"""Sonda 3: Aldi, MD, Conad. Stampa JSON grandi, PDF e link utili.
Carrefour escluso: il sito usa una verifica anti-bot (Cloudflare) che non aggiriamo."""
import asyncio, re
from playwright.async_api import async_playwright
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
T = {
 "aldi": ["https://www.aldi.it/offerte-settimanali/offerte-di-questa-settimana"],
 "md": ["https://www.mdspa.it/volantino/"],
 "conad": ["https://www.conad.it/ricerca-negozi?query=Collegno"],
}
async def run(ctx, name, url):
    pg = await ctx.new_page(); hits = []
    async def on(r):
        ct = r.headers.get("content-type", "")
        if ("json" in ct and "cookie" not in r.url and "google" not in r.url) or ".pdf" in r.url:
            try: b = await r.text() if "json" in ct else ""
            except Exception: b = ""
            hits.append((len(b), r.status, r.url[:220], b[:350].replace("\n", " ")))
    pg.on("response", on)
    try: await pg.goto(url, wait_until="domcontentloaded", timeout=60000)
    except Exception as e: print("ERR", e)
    for _ in range(8):
        await pg.mouse.wheel(0, 2000); await pg.wait_for_timeout(1200)
    await pg.wait_for_timeout(5000)
    html = await pg.content(); text = await pg.inner_text("body")
    links = await pg.eval_on_selector_all("a", "els=>els.map(e=>e.href)")
    print(f"\n===== {name} {url} -> {pg.url} title={await pg.title()!r}")
    print("TEXT", re.sub(r"\s+", " ", text)[:700])
    print("PDF", sorted(set(re.findall(r'https?://[^"\'\s>]+\.pdf', html)))[:10])
    print("LINKS", sorted({l for l in links if re.search(r"volantin|flyer|punti-vendita|negozi/|offert|store", l)})[:40])
    for h in sorted(hits, reverse=True)[:12]: print("NET", *h)
    await pg.close()
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(locale="it-IT", user_agent=UA)
        for n, us in T.items():
            for u in us:
                try: await run(ctx, n, u)
                except Exception as e: print(n, "FAILED", e)
        await b.close()
asyncio.run(main())
