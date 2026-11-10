"""Sonda 6: MD (cosa apre 'Sfoglia il volantino', API negozi woosmap della pagina) e Conad (ricerca negozio dal campo indirizzo).
Nessun aggiramento di verifiche anti-bot: se compare un captcha ci fermiamo."""
import asyncio, re
from playwright.async_api import async_playwright
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
SKIP = r"cookie|google|demdex|acsb|onetrust|_nuxt|i18n|recaptcha|facebook|tiktok|sprite|tiles|style"
def hook(pg, hits):
    async def on(r):
        ct = r.headers.get("content-type", ""); u = r.url
        if ("json" in ct and not re.search(SKIP, u)) or ".pdf" in u or "volantin" in u or "flyer" in u:
            try: b = await r.text() if "json" in ct else ""
            except Exception: b = ""
            hits.append((len(b), r.status, u[:300], b[:700].replace("\n", " ")))
    pg.on("response", on)
async def consent(pg):
    for t in ["Rifiuta", "Solo Cookies Necessari", "Rifiuta tutti", "Continua senza accettare"]:
        try:
            b = pg.get_by_role("button", name=re.compile(t, re.I)).first
            if await b.count() and await b.is_visible():
                await b.click(timeout=3000); await pg.wait_for_timeout(1500); print("consent:", t); return
        except Exception: pass
async def show(pg, name, hits, pat):
    print(f"\n===== {name} -> {pg.url}")
    print("TEXT", re.sub(r"\s+", " ", await pg.inner_text("body"))[:1200])
    a = await pg.eval_on_selector_all("a", "els=>els.map(e=>[e.innerText.trim().replace(/\\s+/g,' ').slice(0,50), e.href])")
    seen = set()
    for t, h in a:
        if h and h not in seen and re.search(pat, h + t, re.I): seen.add(h); print("A", t, h)
    print("FRAMES", [f.url[:200] for f in pg.frames])
    for h in sorted(hits, reverse=True)[:15]: print("NET", *h)

async def md(ctx):
    pg = await ctx.new_page(); hits = []; hook(pg, hits)
    await pg.goto("https://www.mdspa.it/volantino/", wait_until="domcontentloaded", timeout=60000)
    await pg.wait_for_timeout(3000); await consent(pg)
    el = pg.locator("a.elementor-cta").first
    try:
        await el.scroll_into_view_if_needed(); await el.click(timeout=10000, force=True)
    except Exception as e: print("MD click", str(e)[:150])
    await pg.wait_for_timeout(6000)
    await show(pg, "md-after-click", hits, r"volantin|flyer|negozi/|sfoglia|\.pdf")
    vis = await pg.eval_on_selector_all("input, select", "els=>els.filter(e=>e.offsetParent!==null).map(e=>[e.tagName,e.type,e.name,e.placeholder,e.id])")
    print("MD visible inputs", vis)
    for sel in vis:
        if sel[0] == "INPUT" and sel[1] in ("text", "search"):
            loc = pg.locator(f"#{sel[4]}") if sel[4] else pg.locator(f"input[name='{sel[2]}']")
            try:
                await loc.first.click(); await loc.first.type("Collegno", delay=120); await pg.wait_for_timeout(3000)
                await pg.keyboard.press("ArrowDown"); await pg.keyboard.press("Enter"); await pg.wait_for_timeout(6000)
                await show(pg, "md-after-search", hits, r"volantin|flyer|negozi/|collegno|torino|\.pdf")
            except Exception as e: print("MD type", str(e)[:150])
            break

async def conad(ctx):
    pg = await ctx.new_page(); hits = []; hook(pg, hits)
    await pg.goto("https://www.conad.it/ricerca-negozi", wait_until="domcontentloaded", timeout=60000)
    await pg.wait_for_timeout(3000); await consent(pg)
    try:
        loc = pg.locator("input[name=address]").first
        await loc.scroll_into_view_if_needed(); await loc.click(timeout=10000)
        await loc.type("Collegno", delay=120); await pg.wait_for_timeout(3500)
        sug = await pg.eval_on_selector_all("li, [role=option]", "els=>els.filter(e=>/Collegno/i.test(e.innerText)).map(e=>e.innerText.slice(0,80))")
        print("CONAD sugg", sug[:5])
        await pg.keyboard.press("ArrowDown"); await pg.keyboard.press("Enter"); await pg.wait_for_timeout(9000)
    except Exception as e: print("CONAD", str(e)[:200])
    await show(pg, "conad-after-search", hits, r"volantin|negozi/|collegno|torino|rivoli|grugliasco")

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(locale="it-IT", user_agent=UA, viewport={"width": 1366, "height": 900})
        for f in (md, conad):
            try: await f(ctx)
            except Exception as e: print(f.__name__, "FAILED", e)
        await b.close()
if __name__ == "__main__": asyncio.run(main())
