"""Scarica i candidati logo dai siti ufficiali delle catene (una tantum) in logos_raw/<catena>/."""
import asyncio, os, re, json, urllib.parse
from playwright.async_api import async_playwright
SITES = {"aldi": "https://www.aldi.it/", "eurospin": "https://www.eurospin.it/", "coop": "https://www.novacoop.it/",
         "md": "https://www.mdspa.it/", "mercato": "https://www.mymercato.it/", "gigante": "https://ilgigante.net/",
         "bennet": "https://it.wikipedia.org/wiki/Bennet"}
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
JS = """() => {
 const out = [];
 document.querySelectorAll('link[rel*=icon], link[rel=apple-touch-icon], meta[property="og:image"]').forEach(e => out.push(['meta', e.href || e.content]));
 document.querySelectorAll('img, svg, [style*=background]').forEach(e => {
   const s = (e.getAttribute('src')||'') + ' ' + (e.getAttribute('class')||'') + ' ' + (e.getAttribute('alt')||'') + ' ' + (e.id||'') + ' ' + ((e.parentElement&&e.parentElement.className)||'');
   if (/logo/i.test(s)) {
     if (e.tagName.toLowerCase() === 'svg') out.push(['svg', e.outerHTML]);
     else if (e.currentSrc || e.src) out.push(['img', e.currentSrc || e.src]);
   }
 });
 return out.slice(0, 25);
}"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(locale="it-IT", user_agent=UA, viewport={"width": 1366, "height": 900})
        import sys
        for name, url in SITES.items():
            if len(sys.argv) > 1 and name not in sys.argv[1:]: continue
            d = f"logos_raw/{name}"; os.makedirs(d, exist_ok=True); log = []
            try:
                pg = await ctx.new_page()
                await pg.goto(url, wait_until="domcontentloaded", timeout=60000); await pg.wait_for_timeout(4000)
                for i, (kind, val) in enumerate(await pg.evaluate(JS)):
                    try:
                        if kind == "svg":
                            fn = f"{d}/{i:02d}_inline.svg"; open(fn, "w").write(val)
                        else:
                            r = await ctx.request.get(val, timeout=20000)
                            ext = os.path.splitext(urllib.parse.urlparse(val).path)[1][:5] or ".bin"
                            fn = f"{d}/{i:02d}_{kind}{ext}"; open(fn, "wb").write(await r.body())
                        log.append([fn, kind, val if kind != "svg" else "inline"])
                    except Exception as e:
                        log.append(["ERR", kind, str(e)[:120]])
                await pg.screenshot(path=f"{d}/_header.png", clip={"x": 0, "y": 0, "width": 1366, "height": 200})
            except Exception as e:
                log.append(["ERR page", str(e)[:200]])
            json.dump(log, open(f"{d}/_log.json", "w"), indent=1)
        await b.close()
asyncio.run(main())
