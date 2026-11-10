"""Sonda 10b: Bennet via ShopFully. Cosa c'è dietro i link tag-landing dei prodotti?"""
import json, re, os, urllib.request
os.makedirs("../probe_out", exist_ok=True)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
def get(u):
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA, "Accept-Language": "it-IT"}), timeout=30)
        return r.status, r.geturl(), r.read().decode("utf-8", "replace")
    except Exception as e:
        return getattr(e, "code", 0), u, str(e)
PUB = "972552"   # volantino 1739865 (scade 18/11)
st, _, enr = get(f"https://shopfully-publication-api.global.ssl.fastly.net/publication_pages/it_it/{PUB}/enr/1")
items = [x for v in json.loads(enr).values() for x in v]
print("ITEMS", len(items), "pagine", sorted({x["firstPageNumber"] for x in items}, key=int))
for x in items[2:5]:
    u = x["url"].split("?")[0]
    for v in [u, u + "?store_id=51713", u.replace("tag-landing.shopfully.cloud/it_it/", "tag-landing.shopfully.cloud/api/it_it/")]:
        st, fu, b = get(v)
        print(f"\n===== {st} {len(b)} {v} -> {fu}")
        print(re.sub(r"\s+", " ", b)[:2500])
        for m in re.finditer(r"(https?://[^\"' ]+(?:api|json|gib|product)[^\"' ]*)", b): print("  URL", m.group(1)[:200])
        for m in re.finditer(r"<script[^>]*>(.{0,40}(?:__NEXT_DATA__|window\.__|price|prezzo).{0,1500})", b, re.S): print("  SCRIPT", re.sub(r"\s+", " ", m.group(1))[:1500])
# altre fonti di testo: pagine del volantino ("format=all") e pagina DoveConviene con flyerPage=2
st, _, pages = get(f"https://shopfully-publication-api.global.ssl.fastly.net/publication_pages/it_it/{PUB}/1?format=all")
print("\n===== PAGES", st, len(pages), re.sub(r"\s+", " ", pages)[:1500])
st, _, dc = get("https://www.doveconviene.it/torino/iper-e-super/bennet/volantino/ultime-offerte-bennet?flyerId=1739865&flyerPage=2")
for k in ["gib", "price", "prezzo", "product", "offer"]:
    for m in list(re.finditer(k, dc, re.I))[:3]: print("DC", k, re.sub(r"\s+", " ", dc[max(0, m.start()-150):m.start()+250]))
