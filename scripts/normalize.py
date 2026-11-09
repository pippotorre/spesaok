"""Trasforma i dati grezzi di data/raw/<data>/ in data/offerte.json (lista unica).
Campi: catena, nome, marca, formato, prezzo, prezzo_pieno, sconto_pct,
prezzo_unita, unita, categoria, con_carta, valido_dal, valido_al."""
import glob, json, os, re, sys

FOOD_CAT = {"DISPENSA", "GASTRONOMIA, SALUMI E FORMAGGI", "SURGELATI E GELATI", "BEVANDE",
            "FRUTTA E VERDURA", "LATTICINI E UOVA", "SPECIALITÀ", "CARNE E PESCE"}
NON_FOOD_WORDS = re.compile(r"\b(CROCCHETTE|PER CANI|PER GATTI|PET|LETTIERA|DETERSIV|PANNOLIN)\w*", re.I)

def d8(s):
    return f"{s[:4]}-{s[4:6]}-{s[6:8]}" if s else None

def first(p, k):
    v = p.get(k) or []
    return v[0] if v else None

def eurospin(raw):
    f = f"{raw}/eurospin_products.json"
    if not os.path.exists(f): return []
    family = set()
    ff = f"{raw}/eurospin_family.json"
    if os.path.exists(ff): family = set(json.load(open(ff)))
    out = []
    for x in json.load(open(f)):
        p = {q["code"]: q.get("values") for q in x["properties"]}
        cat = first(p, "CATEGORY")
        unit = first(p, "MEASURE-UNIT")
        name = first(p, "TITLE") or x.get("description")
        if cat not in FOOD_CAT and not (cat is None and unit in ("KG", "L")): continue
        if NON_FOOD_WORDS.search(name or ""): continue
        price = first(p, "END-PRICE")
        if price is None: continue
        out.append({
            "catena": "Eurospin", "nome": name.title(), "marca": (first(p, "MARK") or "").title(),
            "formato": first(p, "DESCRIPTION"), "prezzo": price,
            "prezzo_pieno": first(p, "INITIAL-PRICE"), "sconto_pct": first(p, "DISCOUNT-RATE"),
            "prezzo_unita": first(p, "END-KG-LT-PRICE"),
            "unita": {"KG": "kg", "L": "l"}.get(unit),
            "categoria": (cat or "Altro").capitalize(),
            "con_carta": x["identifier"] in family,
            "valido_dal": d8(first(p, "START-DATE-VALIDITY")), "valido_al": d8(first(p, "END-DATE-VALIDITY")),
        })
    return out

def coop(raw):
    import glob as g
    from parse_coop import parse
    out = []
    for f in sorted(g.glob(f"{raw}/coop_pdf*_bbox.html")):
        m = re.search(r"[Dd]al (\d+) (?:\w+ )?al (\d+) (\w+) (\d{4})", open(f.replace("_bbox.html", ".txt")).read()[:5000])
        mesi = "gennaio febbraio marzo aprile maggio giugno luglio agosto settembre ottobre novembre dicembre".split()
        vf = vt = None
        if m:
            mm = mesi.index(m.group(3).lower()) + 1
            vf = f"{m.group(4)}-{mm:02d}-{int(m.group(1)):02d}"; vt = f"{m.group(4)}-{mm:02d}-{int(m.group(2)):02d}"
        out += parse(f, vf, vt)
    return out

def mercato(raw):
    from parse_mercato import parse
    d = f"{raw}/mercato_ocr"
    if not os.path.isdir(d): return []
    vf = vt = None
    info = f"{raw}/mercato_info.json"
    if os.path.exists(info):
        m = re.search(r"(\d\d)-(\d\d)-(\d{4}) - (\d\d)-(\d\d)-(\d{4})", json.load(open(info))["text"])
        if m: vf = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"; vt = f"{m.group(6)}-{m.group(5)}-{m.group(4)}"
    return parse(d, vf, vt)

def latest(pattern):
    """Ultima cartella data/raw/<data> che contiene i file della catena."""
    ds = [d for d in sorted(glob.glob("data/raw/*")) if glob.glob(f"{d}/{pattern}")]
    return ds[-1] if ds else None

def main():
    sys.path.insert(0, "scripts")
    items, dates = [], []
    for fn, pat in ((eurospin, "eurospin_products.json"), (coop, "coop_pdf*_bbox.html"), (mercato, "mercato_ocr")):
        d = latest(pat)
        if d:
            items += fn(d); dates.append(os.path.basename(d))
    seen, uniq = set(), []
    for r in items:
        for k in ("nome", "formato", "marca"):
            if r.get(k): r[k] = re.sub(r"\s+", " ", r[k]).strip()
        key = (r["catena"], r["nome"].lower(), r["prezzo"])
        if key in seen: continue
        seen.add(key); uniq.append(r)
    items = uniq
    items.sort(key=lambda r: (r["prezzo_unita"] is None, r["prezzo_unita"] or r["prezzo"]))
    fonti = sorted({r["catena"] for r in items})
    json.dump({"aggiornato": max(dates) if dates else "", "fonti": fonti, "offerte": items},
              open("data/offerte.json", "w"), ensure_ascii=False, indent=1)
    print("offerte", len(items))

main()
