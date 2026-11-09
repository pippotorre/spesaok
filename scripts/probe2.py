"""Seconda sonda: testo dei PDF (Mercatò, Aldi), API Eurospin, viewer Coop."""
import asyncio, json, re, subprocess, urllib.request
from playwright.async_api import async_playwright
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0 Safari/537.36"}

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()

def pdf_sample(name, url):
    print(f"\n===== PDF {name} {url[:120]}")
    try:
        data = get(url); open(f"/tmp/{name}.pdf", "wb").write(data)
        info = subprocess.run(["pdfinfo", f"/tmp/{name}.pdf"], capture_output=True, text=True).stdout
        print(re.sub(r"\n+", " | ", info)[:400])
        txt = subprocess.run(["pdftotext", "-layout", "-f", "2", "-l", "3", f"/tmp/{name}.pdf", "-"], capture_output=True, text=True).stdout
        print("chars p2-3:", len(txt)); print(txt[:2500])
    except Exception as e:
        print("ERR", e)

def eurospin():
    print("\n===== EUROSPIN API")
    base = "https://flyer.eurospin.com/api/eurospin/eurospin-italia"
    promos = json.loads(get(f"{base}/stores/eurospin-italia/promotions"))
    for p in promos:
        print("PROMO", p.get("alias"), p.get("startDate"), p.get("endDate"), p.get("description"))
    alias = promos[0]["alias"]
    d = json.loads(get(f"{base}/promotions/{alias}/stores/eurospin-italia/products?size=2"))
    print("total", d.get("totalElements"))
    print(json.dumps(d["elements"][0], ensure_ascii=False)[:3500])

async def coop():
    print("\n===== COOP viewer")
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(locale="it-IT")
        hits = []
        async def on(r):
            ct = r.headers.get("content-type", "")
            if "json" in ct or ".pdf" in r.url or "xml" in ct:
                try: body = (await r.text())[:300] if "json" in ct or "xml" in ct else ""
                except Exception: body = ""
                hits.append((r.status, ct[:30], r.url[:250], body))
        pg.on("response", on)
        await pg.goto("https://negozi.volantinopiu.com/ccno-8001120004796.html", wait_until="networkidle", timeout=60000)
        links = await pg.eval_on_selector_all("a", "els => els.map(e => [e.innerText.trim().slice(0,60), e.href])")
        for t, h in links:
            if any(k in h.lower() for k in ("volantin", "flyer", "sfoglia", ".pdf")) or "sfoglia" in t.lower():
                print("LINK", t, h)
        fl = [h for t, h in links if "flyer" in h.lower() or "sfoglia" in t.lower() or "volantino" in t.lower()]
        if fl:
            try:
                await pg.goto(fl[0], wait_until="networkidle", timeout=60000); await pg.wait_for_timeout(4000)
                print("opened", pg.url)
                html = await pg.content()
                print("pdfs", sorted(set(re.findall(r'https?://[^"\'\s>]+\.pdf', html)))[:10])
            except Exception as e: print("ERR open", e)
        for h in hits[-40:]: print("NET", *h)
        await b.close()

for n, u in [("mercato", "https://cdn.dimar.it/volantini/3386/3386_volantino.pdf"),
             ("aldi", "https://volantino.aldi.it/96382/3477404/pdfs/781a23af-f876-44af-bbe7-e3618fc056ab.pdf")]:
    pdf_sample(n, u)
try: eurospin()
except Exception as e: print("EUROSPIN ERR", e)
asyncio.run(coop())
