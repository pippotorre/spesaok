"""Sonda 5: come la 4 ma prima chiude il banner cookie (solo necessari) e stampa tutti i link con testo."""
import asyncio, re
from playwright.async_api import async_playwright
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
SKIP = r"cookie|google|demdex|acsb|onetrust|_nuxt|i18n|recaptcha|facebook|tiktok"

def hook(pg, hits):
    async def on(r):
        ct = r.headers.get("content-type", ""); u = r.url
        if ("json" in ct and not re.search(SKIP, u)) or ".pdf" in u:
            try: b = await r.text() if "json" in ct else ""
            except Exception: b = ""
            hits.append((len(b), r.status, u[:300], b[:500].replace("\n", " ")))
    pg.on("response", on)

async def consent(pg):
    for t in ["Solo Cookies Necessari", "Rifiuta", "Rifiuta tutti", "Continua senza accettare", "Accetta solo i necessari", "Solo necessari"]:
        try:
            b = pg.get_by_role("button", name=re.compile(t, re.I)).first
            if await b.count():
                await b.click(timeout=3000); await pg.wait_for_timeout(1500); print("consent:", t); return
        except Exception: pass
    print("consent: none")

async def anchors(pg, pat=None, n=80):
    a = await pg.eval_on_selector_all("a", "els=>els.map(e=>[e.innerText.trim().replace(/\\s+/g,' ').slice(0,60), e.href])")
    a = [x for x in a if x[1] and (not pat or re.search(pat, x[1] + x[0], re.I))]
    seen = set(); out = []
    for t, h in a:
        if h not in seen: seen.add(h); out.append((t, h))
    for x in out[:n]: print("A", x)

async def dump(pg, name, hits, n=15, tlen=1500):
    print(f"\n===== {name} -> {pg.url} title={await pg.title()!r}")
    print("TEXT", re.sub(r"\s+", " ", await pg.inner_text("body"))[:tlen])
    html = await pg.content()
    print("PDF", sorted(set(re.findall(r'https?://[^"\'\s>]+\.pdf[^"\'\s>]*', html)))[:10])
    for h in sorted(hits, reverse=True)[:n]: print("NET", *h)

async def aldi(ctx):
    pg = await ctx.new_page(); hits = []; hook(pg, hits)
    await pg.goto("https://www.aldi.it/offerte-settimanali/offerte-di-questa-settimana", wait_until="domcontentloaded", timeout=60000)
    await pg.wait_for_timeout(3000); await consent(pg)
    for _ in range(10):
        await pg.mouse.wheel(0, 2000); await pg.wait_for_timeout(800)
    await dump(pg, "aldi", hits, tlen=2500)
    await anchors(pg, r"offert|speciali|prodott")
    # prova la pagina "speciali" con data
    p2 = await ctx.new_page(); h2 = []; hook(p2, h2)
    await p2.goto("https://www.aldi.it/speciali-della-settimana/2026-11-09", wait_until="domcontentloaded", timeout=60000)
    await p2.wait_for_timeout(4000)
    for _ in range(10):
        await p2.mouse.wheel(0, 2000); await p2.wait_for_timeout(800)
    await dump(p2, "aldi-speciali", h2, n=20, tlen=2500)

async def md(ctx):
    pg = await ctx.new_page(); hits = []; hook(pg, hits)
    await pg.goto("https://www.mdspa.it/negozi/", wait_until="domcontentloaded", timeout=60000)
    await pg.wait_for_timeout(3000); await consent(pg)
    await dump(pg, "md-negozi", hits, tlen=1200)
    await anchors(pg, r"torino|collegno|piemonte|negozi/|punto-vendita|volantino")
    inputs = await pg.eval_on_selector_all("input", "els=>els.map(e=>[e.type,e.name,e.placeholder,e.id])")
    print("INPUTS", inputs)

async def conad(ctx):
    pg = await ctx.new_page(); hits = []; hook(pg, hits)
    await pg.goto("https://www.conad.it/ricerca-negozi", wait_until="domcontentloaded", timeout=60000)
    await pg.wait_for_timeout(3000); await consent(pg)
    inputs = await pg.eval_on_selector_all("input", "els=>els.map(e=>[e.type,e.name,e.placeholder,e.id,e.offsetParent!==null])")
    print("INPUTS", inputs)
    try:
        inp = pg.locator("input[type=text]:visible, input[type=search]:visible").first
        await inp.click(); await inp.type("Collegno", delay=120); await pg.wait_for_timeout(3000)
        await pg.keyboard.press("ArrowDown"); await pg.keyboard.press("Enter"); await pg.wait_for_timeout(8000)
    except Exception as e: print("CONAD input", str(e)[:200])
    await dump(pg, "conad-search", hits, tlen=1500)
    await anchors(pg, r"negozi/|volantin|collegno|torino")

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(locale="it-IT", user_agent=UA, viewport={"width": 1366, "height": 900})
        for f in (aldi, md, conad):
            try: await f(ctx)
            except Exception as e: print(f.__name__, "FAILED", e)
        await b.close()
asyncio.run(main())
