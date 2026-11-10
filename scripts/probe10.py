"""Sonda 10: Bennet via ShopFully. Volantini del negozio 51713 (via Giordano Bruno 142) e prodotti."""
import json, re, os, urllib.request
os.makedirs("../probe_out", exist_ok=True)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
GIG = "https://d3k4i39zecu9l5.cloudfront.net/v1/it_it/63f4ba84-d360-4943-b4fb-2d1fac1f52d4"
def get(u):
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA, "Accept-Language": "it-IT"}), timeout=30)
        return r.status, r.read().decode("utf-8", "replace")
    except Exception as e:
        return getattr(e, "code", 0), str(e)
def show(tag, u, n=1500):
    st, b = get(u); print(f"\n===== {tag} {st} {len(b)} {u}\n{b[:n]}"); return st, b

st, h = show("negozio", "https://www.doveconviene.it/negozi/bennet/51713/via-giordano-bruno-142", 300)
ids = list(dict.fromkeys(re.findall(r"flyerId=(\d+)", h)))
print("FLYER IDS NEGOZIO", ids)
for m in re.finditer(r"flyerId=(\d+)[^>]*>(.{0,300})", h): print("CTX", m.group(1), re.sub(r"<[^>]+>|\s+", " ", m.group(2))[:160])
open("../probe_out/negozio.html", "w").write(h)
for fid in (ids or ["1739865", "1731356"])[:4]:
    show(f"gig_api {fid}", f"{GIG}/flyers/{fid}/flyerGibs", 2500)
    show(f"gig_flyer {fid}", f"{GIG}/flyers/{fid}", 800)
    st, page = get(f"https://www.doveconviene.it/torino/iper-e-super/bennet/volantino/ultime-offerte-bennet?flyerId={fid}&flyerPage=1")
    pubs = list(dict.fromkeys(re.findall(r"it_it_(\d{5,})|publication[^\d]{0,40}(\d{6,})", page)))
    print("PUB", fid, st, pubs[:5], "| title:", re.findall(r"<title>(.*?)</title>", page)[:1])
    for m in re.finditer(r"(publication\w*|zmags\w*)[\"']?\s*[:=]\s*[\"']?([\w-]+)", page): print("  PUBCTX", m.group(0)[:120])
    for p in pubs[:1]:
        pid = p[0] or p[1]
        st, enr = show(f"enr {pid}", f"https://shopfully-publication-api.global.ssl.fastly.net/publication_pages/it_it/{pid}/enr/1", 300)
        try:
            d = json.loads(enr); items = [x for v in d.values() for x in v]
            print("ENR items", len(items), "keys", sorted({k for x in items for k in x})[:40])
            for x in items[:6]: print("  ITEM", json.dumps(x, ensure_ascii=False)[:900])
        except Exception as e: print("ENR parse", e)
