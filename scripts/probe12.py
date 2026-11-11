"""Sonda 12: Lidl corso Francia (Torino e Rivoli) su DoveConviene: negozi, volantini, prodotti (JSON-LD + viewer_api)."""
import json, re, os, urllib.request
os.makedirs("../probe_out", exist_ok=True)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
DC = "https://www.doveconviene.it"
def get(u, xhr=False):
    h = {"User-Agent": UA, "Accept-Language": "it-IT"}
    if xhr: h["X-Requested-With"] = "XMLHttpRequest"
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=30)
        return r.status, r.read().decode("utf-8", "replace")
    except Exception as e:
        return getattr(e, "code", 0), str(e)
stores = {}
for city in ["torino", "rivoli", "collegno", "grugliasco"]:
    st, h = get(f"{DC}/{city}/volantino/lidl"); print(f"\n===== {city} {st} {len(h)}")
    for m in re.finditer(r'href="((?:https://www\.doveconviene\.it)?/negozi/lidl/(\d+)/([^"]+))"', h):
        stores[m.group(2)] = m.group(3)
    print("FLYERS", list(dict.fromkeys(re.findall(r"flyerId=(\d+)", h)))[:10])
print("NEGOZI", stores)
fr = {k: v for k, v in stores.items() if "francia" in v.lower()}
print("CORSO FRANCIA", fr)
for sid, slug in fr.items():
    st, h = get(f"{DC}/negozi/lidl/{sid}/{slug}")
    ids = list(dict.fromkeys(re.findall(r"flyerId=(\d+)", h)))
    i = h.lower().find("francia")
    print(f"\n===== negozio {sid} {slug} {st} volantini {ids}\n  ctx", re.sub(r"<[^>]+>|\s+", " ", h[max(0, i-200):i+200]))
fids = []
for sid, slug in fr.items():
    st, h = get(f"{DC}/negozi/lidl/{sid}/{slug}"); fids += re.findall(r"flyerId=(\d+)", h)
for fid in list(dict.fromkeys(fids))[:6]:
    st, page = get(f"{DC}/torino/iper-e-super/lidl/volantino/ultime-offerte-lidl?flyerId={fid}&flyerPage=1")
    lds = []
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', page, re.S):
        try: d = json.loads(m.group(1)); lds += d if isinstance(d, list) else [d]
        except Exception: pass
    art = next((x for x in lds if x.get("@type") == "Article"), {})
    crumbs = next((x for x in lds if x.get("@type") == "BreadcrumbList"), {}).get("itemListElement") or [{}]
    prods = [x for x in lds if x.get("@type") == "Product"]
    print(f"\n===== flyer {fid} {st} '{crumbs[-1].get('name')}' {art.get('datePublished')} -> {art.get('expires')} prodotti {len(prods)}")
    for x in prods[:4]: print("  PROD", x.get("name"), (x.get("offers") or {}).get("price"))
    g = re.search(r"gibCover_([0-9a-f-]{36})", json.dumps(prods))
    if g:
        st, b = get(f"{DC}/viewer_api/flyer_gibs/{g.group(1)}", True)
        try:
            fg = json.loads(b)["data"][0]["FlyerGib"]; s = fg.get("settings", {})
            print("  GIB", fg.get("title"), "|", s.get("brand"), "|", s.get("price"), "| p.", s.get("flyer_page"), "|", (s.get("google_vision_text") or "")[:200])
        except Exception as e: print("  GIB err", st, b[:200])
