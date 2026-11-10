"""Sonda 7: MD, pagina di un punto vendita di Torino -> volantino del negozio."""
import asyncio, re
from playwright.async_api import async_playwright
import probe6 as P  # riusa hook/consent/show
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(locale="it-IT", user_agent=P.UA, viewport={"width": 1366, "height": 900})
        pg = await ctx.new_page(); hits = []; P.hook(pg, hits)
        await pg.goto("https://www.mdspa.it/punti-vendita/Piemonte/TO-Torino/223-TORINO", wait_until="domcontentloaded", timeout=60000)
        await pg.wait_for_timeout(4000); await P.consent(pg)
        await P.show(pg, "md-store", hits, r"volantin|flyer|sfoglia|\.pdf|promo")
        btns = await pg.eval_on_selector_all("a, button", "els=>els.filter(e=>/volantin|sfoglia/i.test(e.innerText+e.className+(e.href||''))).map(e=>[e.innerText.trim().slice(0,40),e.href||'',e.outerHTML.slice(0,300)])")
        for x in btns[:8]: print("BTN", x)
        try:
            async with ctx.expect_page(timeout=12000) as np:
                await pg.get_by_text(re.compile("sfoglia|volantino", re.I)).first.click(timeout=8000)
            v = await np.value
        except Exception as e:
            print("no popup", str(e)[:100]); v = pg
        h2 = []; P.hook(v, h2); await v.wait_for_timeout(10000)
        await P.show(v, "md-flyer", hits + h2, r"\.pdf|flyer|volantin")
        await b.close()
asyncio.run(main())
