"""Sonda 11b: Coop Torino Molise (corso Molise 7): pagina volantinopiu del negozio e volantini, confronto con Collegno."""
import re, asyncio
from playwright.async_api import async_playwright
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
async def links(pg, url, pat):
    await pg.goto(url, wait_until="domcontentloaded", timeout=60000); await pg.wait_for_timeout(6000)
    print(f"\n===== {url} -> {pg.url}")
    print("TEXT", re.sub(r"\s+", " ", await pg.inner_text("body"))[:800])
    L = await pg.eval_on_selector_all("a, iframe", "els=>els.map(e=>(e.innerText||'').trim().slice(0,70)+' | '+(e.href||e.src))")
    out = [l for l in dict.fromkeys(L) if re.search(pat, l, re.I)]
    for l in out: print("LINK", l[:250])
    return out
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); ctx = await b.new_context(locale="it-IT", user_agent=UA); pg = await ctx.new_page()
        L = await links(pg, "https://www.novacoop.it/punti-vendita/coop-torino-molise", r"volantin|ccno|offert|redirect")
        vp = [l.split(" | ")[1] for l in L if "volantinopiu" in l]
        for u in vp[:2]: await links(pg, u, r"redirect|ccno")
        await links(pg, "https://www.novacoop.it/punti-vendita/coop-collegno", r"volantin|ccno|offert|redirect")
        await b.close()
asyncio.run(main())
