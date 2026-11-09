"""Esplora le pagine volantino delle catene con un browser headless e
stampa nel log le risposte JSON/PDF intercettate e i link PDF nella pagina.
Serve solo a capire da dove leggere i dati, non salva offerte."""
import asyncio, json, os, re, sys
from playwright.async_api import async_playwright

TARGETS = {
    "coop_home": "https://www.novacoop.it/",
    "coop_flyer": "https://negozi.volantinopiu.com/ccno-8001120004796.html",
    "mercato_home": "https://www.mymercato.it/",
    "mercato_volantini": "https://www.mymercato.it/volantini",
    "aldi": "https://www.aldi.it/volantino-online",
    "aldi_viewer": "https://volantino.aldi.it/aldi_offerte_da_lunedi_9_novembre/page/1",
    "carrefour": "https://www.carrefour.it/promozioni/",
    "eurospin": "https://flyer.eurospin.com/it-it/volantino",
    "md": "https://www.mdspa.it/volantino/",
    "conad": "https://www.conad.it/ricerca-negozi",
}
OUT = "probe_out"
os.makedirs(OUT, exist_ok=True)

async def probe(browser, name, url):
    ctx = await browser.new_context(locale="it-IT", user_agent=(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"))
    page = await ctx.new_page()
    hits = []
    async def on_resp(r):
        ct = r.headers.get("content-type", "")
        if any(k in ct for k in ("json", "pdf", "svg")) or r.url.lower().endswith(".pdf"):
            entry = {"url": r.url[:300], "status": r.status, "ct": ct[:40]}
            if "json" in ct:
                try:
                    body = await r.text()
                    entry["len"] = len(body)
                    entry["head"] = body[:400]
                except Exception as e:
                    entry["err"] = str(e)[:80]
            hits.append(entry)
    page.on("response", on_resp)
    try:
        await page.goto(url, wait_until="networkidle", timeout=45000)
    except Exception as e:
        print(f"[{name}] goto error: {str(e)[:150]}")
    await page.wait_for_timeout(3000)
    html = await page.content()
    text = await page.inner_text("body") if await page.query_selector("body") else ""
    pdfs = sorted(set(re.findall(r'https?://[^"\'\s>]+\.pdf', html)))
    print(f"\n===== {name} {url} -> {page.url}")
    print(f"title={await page.title()!r} html={len(html)} text={len(text)}")
    print("text sample:", re.sub(r"\s+", " ", text)[:600])
    print("pdf links:", pdfs[:15])
    big = sorted([h for h in hits if h.get("len", 0) > 2000], key=lambda h: -h["len"])
    for h in big[:12]:
        print("JSON", h["status"], h["len"], h["url"])
        print("   ", h["head"].replace("\n", " ")[:300])
    for h in [h for h in hits if "json" not in h["ct"]][:10]:
        print("FILE", h["status"], h["ct"], h["url"])
    with open(f"{OUT}/{name}.json", "w") as f:
        json.dump({"url": url, "final": page.url, "pdfs": pdfs, "hits": hits}, f, indent=1)
    with open(f"{OUT}/{name}.txt", "w") as f:
        f.write(text)
    await ctx.close()

async def main():
    names = sys.argv[1:] or list(TARGETS)
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        for n in names:
            try:
                await probe(browser, n, TARGETS[n])
            except Exception as e:
                print(f"[{n}] failed: {e}")
        await browser.close()

asyncio.run(main())
