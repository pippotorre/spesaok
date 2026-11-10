"""Sonda 10c: Bennet. Prodotti nel JSON-LD delle pagine volantino DoveConviene (ShopFully)."""
import json, re, os, urllib.request
os.makedirs("../probe_out", exist_ok=True)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
def get(u):
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA, "Accept-Language": "it-IT"}), timeout=30)
        return r.status, r.read().decode("utf-8", "replace")
    except Exception as e:
        return getattr(e, "code", 0), str(e)
def ld(html):
    out = []
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        try: d = json.loads(m.group(1))
        except Exception as e: out.append({"_err": str(e), "_raw": m.group(1)[:200]}); continue
        out += d if isinstance(d, list) else [d]
    return out
U = "https://www.doveconviene.it/torino/iper-e-super/bennet/volantino/ultime-offerte-bennet?flyerId={}&flyerPage={}"
for fid in ["1739865", "1731356"]:
    seen = {}
    for pg in [1, 2, 5]:
        st, h = get(U.format(fid, pg))
        L = ld(h); types = {}
        for x in L: types[x.get("@type")] = types.get(x.get("@type"), 0) + 1
        prods = [x for x in L if x.get("@type") == "Product"]
        print(f"\n===== flyer {fid} pagina {pg}: {st} {len(h)} tipi {types}")
        for x in L:
            if x.get("@type") not in ("Product",): print("  ALTRO", json.dumps(x, ensure_ascii=False)[:600])
        for x in prods[:5]: print("  PROD", json.dumps(x, ensure_ascii=False)[:700])
        for x in prods: seen[x.get("name"), (x.get("offers") or {}).get("price")] = x
        open(f"../probe_out/dc_{fid}_{pg}.html", "w").write(h)
    print("TOTALE prodotti distinti", fid, len(seen))
    # cerca altre strutture con i prodotti (es. JSON in pagina con flyer_gibs)
    for k in ["flyerGibs", "flyer_gibs", "\"gibs\"", "productInfo", "\"title\":"]:
        i = h.find(k)
        if i >= 0: print("KEY", k, re.sub(r"\s+", " ", h[max(0, i-100):i+600]))
