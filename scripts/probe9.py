"""Sonda 9: Bennet (Torino, via Giordano Bruno): dove sono il punto vendita e il volantino? cosa carica il sito?"""
import asyncio, re, os
from playwright.async_api import async_playwright
import probe6 as P
os.makedirs("../probe_out", exist_ok=True)
SKIP = r"iubenda|onetrust|cookielaw|google|gstatic|facebook|doubleclick|hotjar|clarity|criteo|tiktok|bing|pinterest"
def hook_all(pg, hits):
    async def on(r):
        u = r.url
        if re.search(SKIP, u): return
        if r.request.resource_type in ("xhr", "fetch", "document") or re.search(r"\.pdf|shopfully|flyer|volantin|promo", u, re.I):
            b = ""
            if r.request.resource_type in ("xhr", "fetch"):
                try: b = await r.text()
                except Exception: pass
            hits.append((r.request.resource_type, r.status, u[:300], len(b), b[:1200].replace("\n", " ")))
    pg.on("response", on)
async def visit(pg, hits, url, tag, wait=8000):
    hits.clear()
    try:
        await pg.goto(url, wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        print(f"\n===== {tag} {url} ERRORE {e}"); return
    await pg.wait_for_timeout(wait)
    for sel in ["#onetrust-accept-btn-handler", "button:has-text('Accetta')", "button:has-text('Accetto')"]:
        try: await pg.click(sel, timeout=1500); break
        except Exception: pass
    print(f"\n===== {tag} {url} -> {pg.url}")
    print("TEXT", re.sub(r"\s+", " ", await pg.inner_text("body"))[:2000])
    links = await pg.eval_on_selector_all("a", "els=>els.map(e=>(e.innerText||'').trim().slice(0,60)+' | '+e.href)")
    for l in links:
        if re.search(r"volantin|torino|giordano|punti|negoz|store|promo|offert", l, re.I): print("LINK", l[:250])
    print("FRAMES", [f.url[:250] for f in pg.frames])
    for h in hits: print("NET", *h)
    await pg.screenshot(path=f"../probe_out/bennet_{tag}.png")
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(locale="it-IT", user_agent=P.UA, viewport={"width": 1366, "height": 900})
        pg = await ctx.new_page(); hits = []; hook_all(pg, hits)
        await visit(pg, hits, "https://www.bennet.com/", "home")
        await visit(pg, hits, "https://www.bennet.com/volantini", "volantini")
        await visit(pg, hits, "https://www.bennet.com/punti-vendita", "puntivendita")
        await visit(pg, hits, "https://www.bennet.com/punti-vendita/torino", "torino")
        # link trovati che citano Torino / Giordano Bruno
        links = await pg.eval_on_selector_all("a", "els=>els.map(e=>e.href)")
        cand = [l for l in dict.fromkeys(links) if re.search(r"giordano|torino", l, re.I)][:4]
        for i, l in enumerate(cand): await visit(pg, hits, l, f"cand{i}")
        await b.close()
asyncio.run(main())
