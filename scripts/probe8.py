"""Sonda 8: Il Gigante -> pagina volantini, scelta del punto vendita di Torino corso Marche, formato del volantino."""
import asyncio, re
from playwright.async_api import async_playwright
import probe6 as P
def hook_all(pg, hits):
    async def on(r):
        if r.request.resource_type in ("xhr", "fetch", "document") or re.search(r"\.pdf|volantin|flyer|publitas|issuu|ipaper", r.url):
            try: b = await r.text() if r.request.resource_type in ("xhr", "fetch") else ""
            except Exception: b = ""
            hits.append((r.request.resource_type, r.status, r.request.method, r.url[:250], (r.request.post_data or "")[:200], b[:600].replace("\n", " ")))
    pg.on("response", on)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(locale="it-IT", user_agent=P.UA, viewport={"width": 1366, "height": 900})
        pg = await ctx.new_page(); hits = []; hook_all(pg, hits)
        await pg.goto("https://ilgigante.net/volantini/", wait_until="domcontentloaded", timeout=60000); await pg.wait_for_timeout(4000)
        for t in ["Chiudi", "Rifiuta"]:
            try: await pg.get_by_role("button", name=re.compile(t, re.I)).first.click(timeout=2000)
            except Exception: pass
        print("INPUTS", await pg.eval_on_selector_all("input, select, button", "els=>els.filter(e=>e.offsetParent!==null).map(e=>[e.tagName,e.type,e.name,e.id,e.placeholder,(e.innerText||'').slice(0,30)])"))
        sels = await pg.eval_on_selector_all("select", "els=>els.map(s=>[s.name,s.id,[...s.options].map(o=>o.value+'|'+o.text).slice(0,400)])")
        for s in sels: print("SELECT", s[0], s[1], [o for o in s[2] if re.search(r'torino|marche', o, re.I)], len(s[2]))
        try:
            inp = pg.locator("input[type=text], input[type=search]").filter(has_not_text="").first
            await inp.click(timeout=5000); await inp.type("Torino", delay=100); await pg.wait_for_timeout(2500)
            print("SUGG", re.sub(r"\s+", " ", await pg.inner_text("body"))[-1500:])
            await pg.keyboard.press("Enter"); await pg.wait_for_timeout(1500)
            try: await pg.get_by_text(re.compile("^CERCA$", re.I)).first.click(timeout=3000)
            except Exception as e: print("no CERCA", str(e)[:80])
            await pg.wait_for_timeout(5000)
        except Exception as e: print("ERR search", str(e)[:200])
        print("AFTER", pg.url, re.sub(r"\s+", " ", await pg.inner_text("body"))[:3000])
        links = await pg.eval_on_selector_all("a", "els=>els.map(e=>[e.innerText.trim().replace(/\\s+/g,' ').slice(0,80), e.href])")
        for t, h in links:
            if re.search(r"marche|torino|volantin|punto-vendita|\.pdf", t + h, re.I): print("A", t, h)
        cand = [h for t, h in links if re.search(r"marche", t + h, re.I)]
        if not cand:
            try:
                el = pg.get_by_text(re.compile("marche", re.I)).first
                await el.click(timeout=5000); await pg.wait_for_timeout(6000)
            except Exception as e: print("no marche click", str(e)[:100])
        else:
            await pg.goto(cand[0], wait_until="domcontentloaded", timeout=60000); await pg.wait_for_timeout(6000)
        print("STORE", pg.url, re.sub(r"\s+", " ", await pg.inner_text("body"))[:2500])
        links = await pg.eval_on_selector_all("a, iframe", "els=>els.map(e=>[ (e.innerText||'').trim().replace(/\\s+/g,' ').slice(0,60), e.href||e.src])")
        for t, h in links:
            if h and re.search(r"volantin|sfoglia|\.pdf|flyer|publitas|issuu|ipaper|promo", t + h, re.I): print("SA", t, h)
        print("FRAMES", [f.url[:200] for f in pg.frames])
        for h in hits[-60:]: print("NET", *h)
        await b.close()
asyncio.run(main())
