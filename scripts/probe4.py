"""Sonda 4: approfondimento Aldi (API prodotti), MD (viewer volantino), Conad (negozio vicino a Collegno)."""
import asyncio, re
from playwright.async_api import async_playwright
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"

def hook(pg, hits, pat=None):
    async def on(r):
        ct = r.headers.get("content-type", "")
        u = r.url
        if pat and re.search(pat, u):
            try: b = await r.text()
            except Exception: b = ""
            hits.append((len(b), r.status, u[:300], b[:600].replace("\n", " ")))
        elif ("json" in ct and not re.search(r"cookie|google|demdex|acsb|onetrust|_nuxt|i18n", u)) or ".pdf" in u:
            try: b = await r.text() if "json" in ct else ""
            except Exception: b = ""
            hits.append((len(b), r.status, u[:300], b[:600].replace("\n", " ")))
    pg.on("response", on)

async def dump(pg, name, hits, n=15, tlen=3000):
    html = await pg.content(); text = await pg.inner_text("body")
    links = await pg.eval_on_selector_all("a", "els=>els.map(e=>e.href)")
    print(f"\n===== {name} -> {pg.url} title={await pg.title()!r}")
    print("TEXT", re.sub(r"\s+", " ", text)[:tlen])
    print("PDF", sorted(set(re.findall(r'https?://[^"\'\s>]+\.pdf[^"\'\s>]*', html)))[:10])
    print("LINKS", sorted({l for l in links if re.search(r"volantin|flyer|negozi/|negozio|offert|store|sfoglia|promo", l)})[:50])
    print("IFRAMES", [f.url for f in pg.frames][:10])
    for h in sorted(hits, reverse=True)[:n]: print("NET", *h)

async def aldi(ctx):
    pg = await ctx.new_page(); hits = []; hook(pg, hits, r"asl\.api\.aldi\.it")
    await pg.goto("https://www.aldi.it/offerte-settimanali/offerte-di-questa-settimana", wait_until="domcontentloaded", timeout=60000)
    await pg.wait_for_timeout(4000)
    for _ in range(15):
        await pg.mouse.wheel(0, 2500); await pg.wait_for_timeout(900)
    await dump(pg, "aldi", hits, n=25, tlen=5000)
    for h in hits: print("ASL", h[1], h[2])
    tiles = await pg.eval_on_selector_all("[class*=product-tile], [class*=product-teaser], article", "els=>els.slice(0,8).map(e=>e.outerHTML.slice(0,1200))")
    for t in tiles: print("TILE", re.sub(r"\s+", " ", t))

async def md(ctx):
    pg = await ctx.new_page(); hits = []; hook(pg, hits)
    await pg.goto("https://www.mdspa.it/volantino/", wait_until="domcontentloaded", timeout=60000)
    await pg.wait_for_timeout(4000)
    btn = await pg.eval_on_selector_all("a, button", "els=>els.filter(e=>/sfoglia/i.test(e.innerText)).map(e=>[e.tagName,e.href||'',e.outerHTML.slice(0,400)])")
    for b in btn[:6]: print("MDBTN", b)
    try:
        async with ctx.expect_page(timeout=15000) as np:
            await pg.get_by_text(re.compile("sfoglia il volantino", re.I)).first.click()
        v = await np.value
    except Exception as e:
        print("MD no new page", str(e)[:120]); v = pg
    hits2 = []; hook(v, hits2)
    await v.wait_for_timeout(10000)
    await dump(v, "md-viewer", hits + hits2, n=20)

async def conad(ctx):
    pg = await ctx.new_page(); hits = []; hook(pg, hits)
    await pg.goto("https://www.conad.it/ricerca-negozi", wait_until="domcontentloaded", timeout=60000)
    await pg.wait_for_timeout(4000)
    try:
        inp = pg.get_by_placeholder(re.compile("Indirizzo", re.I)).first
        await inp.fill("Collegno TO"); await pg.wait_for_timeout(2500)
        await inp.press("Enter"); await pg.wait_for_timeout(8000)
    except Exception as e: print("CONAD input", str(e)[:200])
    await dump(pg, "conad-search", hits, n=15)
    links = await pg.eval_on_selector_all("a", "els=>els.map(e=>e.href)")
    st = [l for l in links if re.search(r"/negozi/|negozio\.", l)]
    print("CONAD stores", st[:20])
    if st:
        s = await ctx.new_page(); h2 = []; hook(s, h2)
        await s.goto(st[0], wait_until="domcontentloaded", timeout=60000); await s.wait_for_timeout(6000)
        await dump(s, "conad-store", h2, n=15)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(locale="it-IT", user_agent=UA, viewport={"width": 1366, "height": 900})
        for f in (aldi, md, conad):
            try: await f(ctx)
            except Exception as e: print(f.__name__, "FAILED", e)
        await b.close()
asyncio.run(main())
