"""Sonda 8: Il Gigante corso Marche (punto=47) -> pagina dettaglio volantino ShopFully: cosa carica?"""
import asyncio, re, json, os
from playwright.async_api import async_playwright
import probe6 as P
os.makedirs("../probe_out", exist_ok=True)
def hook_all(pg, hits):
    async def on(r):
        u = r.url
        if re.search(r"iubenda|acswapp|google|gstatic|facebook|doubleclick", u): return
        if r.request.resource_type in ("xhr", "fetch", "document", "script") or re.search(r"\.pdf|shopfully|flyer|volantin", u):
            b = ""
            if r.request.resource_type in ("xhr", "fetch"):
                try: b = await r.text()
                except Exception: pass
            hits.append((r.request.resource_type, r.status, u[:300], len(b), b[:1500].replace("\n", " ")))
    pg.on("response", on)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(locale="it-IT", user_agent=P.UA, viewport={"width": 1366, "height": 900})
        pg = await ctx.new_page(); hits = []; hook_all(pg, hits)
        for fid in ["1741507", "1738600"]:
            hits.clear()
            await pg.goto(f"https://ilgigante.net/volantini/dettaglio?flyer-id={fid}&punto=47", wait_until="domcontentloaded", timeout=60000)
            await pg.wait_for_timeout(9000)
            print(f"\n===== FLYER {fid} -> {pg.url}")
            print("TEXT", re.sub(r"\s+", " ", await pg.inner_text("body"))[:1500])
            print("FRAMES", [f.url[:250] for f in pg.frames])
            for f in pg.frames[1:]:
                try: print("FTEXT", f.url[:80], re.sub(r"\s+", " ", await f.inner_text("body"))[:800])
                except Exception: pass
            imgs = await pg.eval_on_selector_all("img", "els=>els.map(e=>e.currentSrc||e.src).filter(s=>/shopfully|volantin|flyer/.test(s))")
            print("IMGS", len(imgs), imgs[:6])
            for h in hits: print("NET", *h)
            await pg.screenshot(path=f"../probe_out/gigante_{fid}.png")
        await b.close()
asyncio.run(main())
