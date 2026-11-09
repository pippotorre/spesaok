"""Raccoglitore offerte. Salva dati grezzi in data/raw/<data>/<catena>.* per
analisi e normalizzazione successiva. Uso: python scripts/collect.py [catene...]"""
import asyncio, datetime as dt, json, os, re, subprocess, sys, urllib.request
from playwright.async_api import async_playwright

TODAY = dt.date.today().isoformat()
RAW = f"data/raw/{TODAY}"
os.makedirs(RAW, exist_ok=True)
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")

def save(name, obj):
    with open(f"{RAW}/{name}", "w") as f:
        if isinstance(obj, str): f.write(obj)
        else: json.dump(obj, f, ensure_ascii=False, indent=1)
    print("saved", name)

async def eurospin(ctx):
    pg = await ctx.new_page()
    await pg.goto("https://flyer.eurospin.com/it-it/volantino", wait_until="networkidle", timeout=60000)
    alias = pg.url.rstrip("/").split("/")[-1]
    base = "/api/eurospin/eurospin-italia"
    promos = await pg.evaluate(f"fetch('{base}/stores/eurospin-italia/promotions').then(r=>r.json())")
    save("eurospin_promotions.json", promos)
    out = []
    for p in promos:
        a = p["alias"]; page = 0
        while True:
            d = await pg.evaluate(f"fetch('{base}/promotions/{a}/stores/eurospin-italia/products?size=100&page={page}').then(r=>r.ok?r.json():{{status:r.status}})")
            if "elements" not in d:
                print("eurospin stop", a, d); break
            for e in d["elements"]: e["_promo"] = {k: p.get(k) for k in ("alias","description","startDate","endDate")}
            out += d["elements"]; page += 1
            if d.get("last", True): break
    print("eurospin products", len(out), "current alias", alias)
    save("eurospin_products.json", out)

async def aldi(ctx):
    pg = await ctx.new_page()
    texts = {}
    for path in ["/offerte-settimanali", "/offerte-della-settimana", "/volantino-online"]:
        try:
            await pg.goto("https://www.aldi.it" + path, wait_until="networkidle", timeout=60000)
            await pg.wait_for_timeout(2000)
            texts[path] = {"url": pg.url, "text": await pg.inner_text("body")}
            links = await pg.eval_on_selector_all("a", "els=>els.map(e=>e.href)")
            texts[path]["links"] = sorted({l for l in links if "offert" in l or "speciali" in l})[:80]
        except Exception as e:
            texts[path] = {"err": str(e)[:200]}
    save("aldi_pages.json", texts)
    # viewer publitas: hotspots con eventuali dati prodotto
    hs = []
    async def on(r):
        if "hotspots_data.json" in r.url:
            try: hs.append({"url": r.url, "data": await r.json()})
            except Exception: pass
    v = await ctx.new_page(); v.on("response", on)
    await v.goto("https://www.aldi.it/volantino-online", wait_until="networkidle", timeout=60000)
    vl = await v.eval_on_selector_all("a", "els=>els.map(e=>e.href)")
    vl = [l for l in vl if "volantino.aldi.it" in l]
    print("aldi viewer links", vl[:4])
    if vl:
        await v.goto(vl[0], wait_until="networkidle", timeout=60000)
        for i in range(20):
            await v.keyboard.press("ArrowRight"); await v.wait_for_timeout(700)
    save("aldi_hotspots.json", hs)

async def coop(ctx):
    pg = await ctx.new_page()
    net = []
    async def on(r):
        ct = r.headers.get("content-type", "")
        if "json" in ct or "xml" in ct or ".pdf" in r.url:
            try: body = await r.text() if ("json" in ct or "xml" in ct) else ""
            except Exception: body = ""
            net.append({"url": r.url, "ct": ct, "len": len(body), "body": body[:200000]})
    pg.on("response", on)
    await pg.goto("https://negozi.volantinopiu.com/redirect29401.html?id_pv=24", wait_until="networkidle", timeout=60000)
    await pg.wait_for_timeout(4000)
    html = await pg.content()
    info = {"final": pg.url, "pdfs": sorted(set(re.findall(r'https?://[^"\'\s>]+\.pdf', html))),
            "text": (await pg.inner_text("body"))[:5000]}
    print("coop final", pg.url, "pdfs", info["pdfs"][:5])
    save("coop_info.json", info)
    save("coop_net.json", [n for n in net if n["len"] > 500 or ".pdf" in n["url"]])

async def mercato(ctx):
    pg = await ctx.new_page()
    await pg.goto("https://www.mymercato.it/mondo-mercato/volantini", wait_until="domcontentloaded", timeout=60000)
    await pg.wait_for_timeout(8000)
    html = await pg.content()
    pdfs = sorted(set(re.findall(r'https://cdn\.dimar\.it/volantini/\d+/\d+_volantino\.pdf', html)))
    blocks = await pg.inner_text("body")
    save("mercato_info.json", {"pdfs": pdfs, "text": blocks[:6000]})
    if pdfs:
        req = urllib.request.Request(pdfs[0], headers={"User-Agent": UA})
        open("/tmp/m.pdf", "wb").write(urllib.request.urlopen(req, timeout=120).read())
        subprocess.run(["pdftoppm", "-r", "150", "-f", "4", "-l", "5", "-png", "/tmp/m.pdf", "/tmp/mp"], check=True)
        txt = ""
        for f in sorted(os.listdir("/tmp")):
            if f.startswith("mp") and f.endswith(".png"):
                txt += f"\n--- {f}\n" + subprocess.run(["tesseract", f"/tmp/{f}", "-", "-l", "ita", "--psm", "11"], capture_output=True, text=True).stdout
        save("mercato_ocr_sample.txt", txt)

CHAINS = {"eurospin": eurospin, "aldi": aldi, "coop": coop, "mercato": mercato}

async def main():
    names = sys.argv[1:] or list(CHAINS)
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(locale="it-IT", user_agent=UA)
        for n in names:
            try: await CHAINS[n](ctx)
            except Exception as e: print(f"[{n}] ERRORE", repr(e)[:300])
        await b.close()

asyncio.run(main())
