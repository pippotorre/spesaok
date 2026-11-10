"""Sonda 8: Il Gigante, punto vendita di Torino corso Marche -> volantino del negozio (formato?)."""
import asyncio, re
from playwright.async_api import async_playwright
import probe6 as P
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(locale="it-IT", user_agent=P.UA, viewport={"width": 1366, "height": 900})
        pg = await ctx.new_page(); hits = []; P.hook(pg, hits)
        for url in ["https://www.ilgigante.net/", "https://www.ilgigante.net/punti-vendita", "https://www.ilgigante.net/volantini"]:
            try:
                await pg.goto(url, wait_until="domcontentloaded", timeout=60000); await pg.wait_for_timeout(4000); await P.consent(pg)
                await P.show(pg, url, hits, r"volantin|flyer|punti-vendita|negozi|torino|marche|\.pdf|sfoglia")
            except Exception as e: print("ERR", url, str(e)[:150])
        # cerca il negozio di corso Marche tra i link raccolti
        links = await pg.eval_on_selector_all("a", "els=>els.map(e=>[e.innerText.trim().replace(/\\s+/g,' ').slice(0,60), e.href])")
        cand = [h for t, h in links if re.search(r"marche|torino", (t + h), re.I)]
        print("CAND", cand[:20])
        for h in cand[:4]:
            try:
                hits2 = []; P.hook(pg, hits2)
                await pg.goto(h, wait_until="domcontentloaded", timeout=60000); await pg.wait_for_timeout(5000)
                await P.show(pg, "store " + h, hits2, r"volantin|flyer|\.pdf|sfoglia|promo")
            except Exception as e: print("ERR", h, str(e)[:150])
        await b.close()
asyncio.run(main())
