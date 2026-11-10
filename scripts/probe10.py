"""Sonda 10d: Bennet. Dettaglio prodotto (formato, prezzo pieno, pagina) dalla viewer_api di DoveConviene."""
import json, re, os, urllib.request, asyncio
os.makedirs("../probe_out", exist_ok=True)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
def get(u):
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA, "Accept-Language": "it-IT", "X-Requested-With": "XMLHttpRequest"}), timeout=30)
        return r.status, r.read().decode("utf-8", "replace")
    except Exception as e:
        return getattr(e, "code", 0), str(e)
FID, GIB = "1739865", "6aeb5390-2ba0-4e33-af3b-00ca0ad30146"
PAGE = f"https://www.doveconviene.it/torino/iper-e-super/bennet/volantino/ultime-offerte-bennet?flyerId={FID}&flyerPage=1"
st, h = get(PAGE)
js = list(dict.fromkeys(re.findall(r'src="([^"]+\.js[^"]*)"', h)))
print("JS", js[:30])
for u in js:
    if u.startswith("/"): u = "https://www.doveconviene.it" + u
    if "doveconviene" not in u: continue
    st, b = get(u)
    for m in re.finditer(r"viewer_api|flyer_?gibs?/|/gibs?\b|productInfo", b):
        print("JSHIT", u.split("/")[-1][:40], re.sub(r"\s+", " ", b[max(0, m.start()-200):m.start()+250]))
for path in [f"/viewer_api/flyer_gibs/{GIB}", f"/viewer_api/flyergibs/{GIB}", f"/viewer_api/gibs/{GIB}", f"/viewer_api/flyers/{FID}/flyer_gibs",
             f"/viewer_api/flyers/{FID}/gibs", f"/viewer_api/flyer_gibs?flyer_id={FID}", f"/viewer_api/products/{GIB}"]:
    st, b = get("https://www.doveconviene.it" + path); print(f"\n===== {st} {len(b)} {path}\n{b[:1200]}")
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); ctx = await b.new_context(locale="it-IT", user_agent=UA, viewport={"width": 1366, "height": 900})
        pg = await ctx.new_page(); hits = []
        async def on(r):
            if r.request.resource_type in ("xhr", "fetch") and re.search(r"viewer_api|gib|product|tag-landing", r.url):
                try: t = await r.text()
                except Exception: t = ""
                hits.append((r.status, r.url[:250], t[:2000].replace("\n", " ")))
        pg.on("response", on)
        await pg.goto(PAGE, wait_until="domcontentloaded", timeout=60000); await pg.wait_for_timeout(9000)
        for sel in ["button:has-text('Accetta')", "#iubenda-cs-accept-btn", ".iubenda-cs-accept-btn"]:
            try: await pg.click(sel, timeout=1500); break
            except Exception: pass
        cands = await pg.query_selector_all("[class*=gib], [class*=Gib], [class*=hotspot], [class*=pin], img[src*='plus-white']")
        print("HOTSPOT", len(cands))
        for c in cands[:3]:
            try: await c.click(timeout=3000, force=True); await pg.wait_for_timeout(3000)
            except Exception as e: print("click", e)
        await pg.screenshot(path="../probe_out/bennet_gib.png")
        print("TEXT", re.sub(r"\s+", " ", await pg.inner_text("body"))[:1500])
        for h_ in hits: print("NET", *h_)
        await b.close()
asyncio.run(main())
