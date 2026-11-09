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
    hdrs = {}
    def on_req(r):
        if "/api/eurospin/" in r.url and "products" in r.url and not hdrs:
            hdrs.update({k: v for k, v in r.headers.items() if k.lower() not in ("content-length",)})
    pg.on("request", on_req)
    await pg.goto("https://flyer.eurospin.com/it-it/volantino", wait_until="networkidle", timeout=60000)
    print("eurospin headers keys", list(hdrs))
    base = "https://flyer.eurospin.com/api/eurospin/eurospin-italia"
    r = await ctx.request.get(f"{base}/stores/eurospin-italia/promotions", headers=hdrs)
    promos = await r.json(); save("eurospin_promotions.json", promos)
    out = []
    for p in promos:
        a = p["alias"]; page = 0
        while page < 30:
            r = await ctx.request.get(f"{base}/promotions/{a}/stores/eurospin-italia/products?size=100&page={page}", headers=hdrs)
            if not r.ok: print("eurospin stop", a, r.status); break
            d = await r.json()
            for e in d["elements"]: e["_promo"] = {k: p.get(k) for k in ("alias","description","startDate","endDate")}
            out += d["elements"]; page += 1
            if d.get("last", True): break
    print("eurospin products", len(out))
    save("eurospin_products.json", out)

async def aldi(ctx):
    pg = await ctx.new_page()
    texts = {}
    api = []
    async def on_api(r):
        if "aldi" in r.url and "cookielaw" not in r.url and "json" in r.headers.get("content-type", ""):
            try: api.append({"url": r.url, "data": await r.json()})
            except Exception: pass
    pg.on("response", on_api)
    for path in ["/offerte-settimanali/offerte-di-questa-settimana", "/offerte-settimanali/offerte-della-prossima-settimana"]:
        try:
            await pg.goto("https://www.aldi.it" + path, wait_until="networkidle", timeout=60000)
            for _ in range(12):
                await pg.mouse.wheel(0, 2500); await pg.wait_for_timeout(800)
            await pg.wait_for_timeout(4000)
            texts[path] = {"url": pg.url, "text": await pg.inner_text("body")}
            links = await pg.eval_on_selector_all("a", "els=>els.map(e=>e.href)")
            texts[path]["links"] = sorted({l for l in links if "offert" in l or "speciali" in l})[:80]
        except Exception as e:
            texts[path] = {"err": str(e)[:200]}
    save("aldi_pages.json", texts)
    save("aldi_api.json", api)
    return
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
    try:
        await pg.goto("https://negozi.volantinopiu.com/redirect29401.html?id_pv=24", wait_until="domcontentloaded", timeout=60000)
    except Exception as e: print("coop goto", repr(e)[:150])
    await pg.wait_for_timeout(15000)
    html = await pg.content()
    info = {"final": pg.url, "pdfs": sorted(set(re.findall(r'https?://[^"\'\s>]+\.pdf', html))),
            "text": (await pg.inner_text("body"))[:5000]}
    print("coop final", pg.url, "pdfs", info["pdfs"][:5])
    save("coop_info.json", info)
    for i, u in enumerate(info["pdfs"][:3]):
        req = urllib.request.Request(u, headers={"User-Agent": UA})
        open(f"/tmp/coop{i}.pdf", "wb").write(urllib.request.urlopen(req, timeout=180).read())
        txt = subprocess.run(["pdftotext", "-layout", f"/tmp/coop{i}.pdf", "-"], capture_output=True, text=True).stdout
        save(f"coop_pdf{i}.txt", txt)
        subprocess.run(["pdftotext", "-bbox-layout", f"/tmp/coop{i}.pdf", f"{RAW}/coop_pdf{i}_bbox.html"])
        subprocess.run(["pdftoppm", "-r", "60", "-jpeg", "-f", "3", "-l", "4", f"/tmp/coop{i}.pdf", f"{RAW}/coop_pdf{i}_p"])
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
