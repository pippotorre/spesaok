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
    """Speciali della settimana Aldi: la pagina chiama asl.api.aldi.it/commerce/v3/product-search
    con promotionKey=<data>. Rileggiamo la stessa API (stessi header della pagina) paginando."""
    pg = await ctx.new_page()
    await pg.goto("https://www.aldi.it/offerte-settimanali/offerte-di-questa-settimana", wait_until="domcontentloaded", timeout=60000)
    await pg.wait_for_timeout(4000)
    links = await pg.eval_on_selector_all("a", "els=>els.map(e=>e.href)")
    oggi = dt.date.today()
    keys = sorted({m.group(1) for l in links if (m := re.search(r"speciali-della-settimana/(\d{4}-\d\d-\d\d)", l))})
    keys = [k for k in keys if -7 < (dt.date.fromisoformat(k) - oggi).days <= 3]
    print("aldi promotionKey", keys)
    out = []
    for k in keys:
        cap = {}
        def on_req(r):
            if "product-search" in r.url and "promotionKey" in r.url and not cap:
                cap["url"] = r.url; cap["h"] = {x: y for x, y in r.headers.items() if x.lower() != "content-length"}
        p2 = await ctx.new_page(); p2.on("request", on_req)
        await p2.goto(f"https://www.aldi.it/speciali-della-settimana/{k}", wait_until="domcontentloaded", timeout=60000)
        for _ in range(20):
            if cap: break
            await p2.wait_for_timeout(500)
        await p2.close()
        if not cap: print("aldi: nessuna chiamata API per", k); continue
        off = 0
        while off < 1000:
            u = re.sub(r"offset=\d+", f"offset={off}", re.sub(r"limit=\d+", "limit=60", cap["url"]))
            r = await ctx.request.get(u, headers=cap["h"])
            if not r.ok: print("aldi stop", k, r.status); break
            d = await r.json()
            items = d.get("data") or []
            for e in items: e["_promo"] = {"key": k, "pagina": f"https://www.aldi.it/speciali-della-settimana/{k}"}
            out += items; off += 60
            if off >= d.get("meta", {}).get("pagination", {}).get("totalCount", 0) or not items: break
    print("aldi products", len(out))
    save("aldi_products.json", out)

COOP_STORES = [
    "https://negozi.volantinopiu.com/ccno-8001120004550.html",  # Coop Collegno (negozio di Pippo)
    "https://negozi.volantinopiu.com/ccno-8001120004796.html",  # Ipercoop Torino Dora
]

async def coop(ctx):
    import shutil
    for f in os.listdir(RAW):  # pulizia dei file Coop di un giro precedente nello stesso giorno
        if f.startswith("coop_"):
            p = f"{RAW}/{f}"; shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    pg = await ctx.new_page()
    flyers = []
    for store in COOP_STORES:
        try:
            await pg.goto(store, wait_until="domcontentloaded", timeout=60000)
            await pg.wait_for_timeout(5000)
        except Exception as e: print("coop store", repr(e)[:150])
        links = await pg.eval_on_selector_all("a", "els => els.map(e => [e.innerText.trim(), e.href])")
        for t, h in links:
            if "redirect" in h and h not in [f[1] for f in flyers]: flyers.append((store, h))
    print("coop volantini", flyers)
    infos = []
    for i, (store, url) in enumerate(flyers):
        try:
            await pg.goto(url, wait_until="domcontentloaded", timeout=60000)
        except Exception as e: print("coop goto", repr(e)[:150])
        await pg.wait_for_timeout(12000)
        html = await pg.content()
        pdfs = sorted(set(re.findall(r'https?://[^"\'\s>]+\.pdf', html)))
        infos.append({"i": i, "negozio": store, "url": url, "final": pg.url, "pdfs": pdfs})
        for u in pdfs[:1]:
            req = urllib.request.Request(u, headers={"User-Agent": UA})
            open(f"/tmp/coop{i}.pdf", "wb").write(urllib.request.urlopen(req, timeout=180).read())
            txt = subprocess.run(["pdftotext", "-layout", f"/tmp/coop{i}.pdf", "-"], capture_output=True, text=True).stdout
            save(f"coop_pdf{i}.txt", txt)
            if len(txt.strip()) > 500:
                subprocess.run(["pdftotext", "-bbox-layout", f"/tmp/coop{i}.pdf", f"{RAW}/coop_pdf{i}_bbox.html"])
                # pagine "sconto su tutta la linea": le marche sono solo loghi, servono all'OCR
                pages_txt = txt.split("\f")
                linea = [n + 1 for n, p in enumerate(pages_txt) if re.search(r"tutta\s+la\s+linea", p, re.I)]
                if linea:
                    d = f"/tmp/cooplinea{i}"; os.makedirs(d, exist_ok=True)
                    os.makedirs(f"{RAW}/coop_linea{i}", exist_ok=True)
                    for n in linea:
                        subprocess.run(["pdftoppm", "-r", "200", "-png", "-f", str(n), "-l", str(n), f"/tmp/coop{i}.pdf", f"{d}/p"], check=True)
                    for f in sorted(os.listdir(d)):
                        subprocess.run(["tesseract", f"{d}/{f}", f"{RAW}/coop_linea{i}/{f[:-4]}", "-l", "ita", "--psm", "11", "tsv"], capture_output=True)
                    subprocess.run(["pdftoppm", "-r", "45", "-jpeg", "-f", str(linea[0]), "-l", str(linea[0]), f"/tmp/coop{i}.pdf", f"{RAW}/coop_linea{i}_prev"])
            else:  # volantino solo immagine: OCR
                d = f"/tmp/coopimg{i}"; os.makedirs(d, exist_ok=True)
                subprocess.run(["pdftoppm", "-r", "200", "-png", f"/tmp/coop{i}.pdf", f"{d}/p"], check=True)
                os.makedirs(f"{RAW}/coop_ocr{i}", exist_ok=True)
                for f in sorted(os.listdir(d)):
                    subprocess.run(["tesseract", f"{d}/{f}", f"{RAW}/coop_ocr{i}/{f[:-4]}", "-l", "ita", "--psm", "11", "tsv"], capture_output=True)
                subprocess.run(["pdftoppm", "-r", "50", "-jpeg", "-f", "2", "-l", "3", f"/tmp/coop{i}.pdf", f"{RAW}/coop_ocr{i}_prev"])
    save("coop_info.json", {"volantini": infos})

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
        open("/tmp/m.pdf", "wb").write(urllib.request.urlopen(req, timeout=180).read())
        os.makedirs("/tmp/mp", exist_ok=True)
        subprocess.run(["pdftoppm", "-r", "200", "-png", "/tmp/m.pdf", "/tmp/mp/p"], check=True)
        os.makedirs(f"{RAW}/mercato_ocr", exist_ok=True)
        for f in sorted(os.listdir("/tmp/mp")):
            base = f[:-4]
            subprocess.run(["tesseract", f"/tmp/mp/{f}", f"{RAW}/mercato_ocr/{base}", "-l", "ita", "--psm", "11", "tsv"],
                           capture_output=True)
        subprocess.run(["pdftoppm", "-r", "50", "-jpeg", "-f", "6", "-l", "7", "/tmp/m.pdf", f"{RAW}/mercato_prev"])
        print("mercato pagine", len(os.listdir("/tmp/mp")))

CHAINS = {"eurospin": eurospin, "aldi": aldi, "coop": coop, "mercato": mercato}

async def main():
    names = sys.argv[1:] or ["eurospin", "coop", "mercato"]  # aldi ancora in sviluppo
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(locale="it-IT", user_agent=UA)
        for n in names:
            try: await CHAINS[n](ctx)
            except Exception as e: print(f"[{n}] ERRORE", repr(e)[:300])
        await b.close()

asyncio.run(main())
