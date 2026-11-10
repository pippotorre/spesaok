"""Sonda 11: Coop di corso Molise (Torino). Esiste? Quale volantino ha? È lo stesso di Collegno o di Ipercoop Dora?"""
import re, os, json, urllib.request, asyncio
from playwright.async_api import async_playwright
os.makedirs("../probe_out", exist_ok=True)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
def get(u):
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA, "Accept-Language": "it-IT"}), timeout=30)
        return r.status, r.read().decode("utf-8", "replace")
    except Exception as e:
        return getattr(e, "code", 0), str(e)
# 1) DoveConviene: negozi Coop a Torino
for u in ["https://www.doveconviene.it/torino/volantino/coop", "https://www.doveconviene.it/torino/catene-e-negozi?r=3630"]:
    st, h = get(u); print(f"\n===== {st} {len(h)} {u}")
    for m in re.finditer(r'href="(/negozi/[^"]+)"', h):
        if re.search(r"molise|coop", m.group(1), re.I): print("NEG", m.group(1))
    i = h.lower().find("molise")
    print("MOLISE ctx", re.sub(r"<[^>]+>|\s+", " ", h[max(0, i-600):i+300]) if i >= 0 else "assente")
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); ctx = await b.new_context(locale="it-IT", user_agent=UA)
        pg = await ctx.new_page()
        # 2) volantinopiu: elenco negozi Nova Coop e confronto volantini
        for u in ["https://negozi.volantinopiu.com/ccno-8001120004550.html", "https://negozi.volantinopiu.com/ccno-8001120004796.html",
                  "https://negozi.volantinopiu.com/", "https://www.volantinopiu.com/negozi/torino/novacoop"]:
            try:
                await pg.goto(u, wait_until="domcontentloaded", timeout=60000); await pg.wait_for_timeout(5000)
            except Exception as e: print("ERR", u, e); continue
            print(f"\n===== VP {u} -> {pg.url}")
            print("TEXT", re.sub(r"\s+", " ", await pg.inner_text("body"))[:1200])
            links = await pg.eval_on_selector_all("a", "els=>els.map(e=>(e.innerText||'').trim().slice(0,70)+' | '+e.href)")
            for l in links:
                if re.search(r"redirect|molise|ccno-|torino", l, re.I): print("LINK", l[:250])
        # 3) Nova Coop: cerca negozio corso Molise
        for u in ["https://www.novacoop.it/negozi", "https://www.novacoop.it/punti-vendita"]:
            try:
                await pg.goto(u, wait_until="domcontentloaded", timeout=60000); await pg.wait_for_timeout(6000)
            except Exception as e: print("ERR", u, e); continue
            t = await pg.inner_text("body"); print(f"\n===== NC {u} -> {pg.url} {len(t)}")
            i = t.lower().find("molise"); print("MOLISE", re.sub(r"\s+", " ", t[max(0, i-400):i+400]) if i >= 0 else "assente")
            links = await pg.eval_on_selector_all("a", "els=>els.map(e=>(e.innerText||'').trim().slice(0,70)+' | '+e.href)")
            for l in links:
                if re.search(r"molise|torino", l, re.I): print("LINK", l[:250])
        await b.close()
asyncio.run(main())
