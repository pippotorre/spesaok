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

def main():
    raw = sys.argv[1] if len(sys.argv) > 1 else sorted(glob.glob("data/raw/*"))[-1]
    items = eurospin(raw)
    items.sort(key=lambda r: (r["prezzo_unita"] is None, r["prezzo_unita"] or r["prezzo"]))
    os.makedirs("data", exist_ok=True)
    fonti = sorted({r["catena"] for r in items})
    json.dump({"aggiornato": os.path.basename(raw), "fonti": fonti, "offerte": items},
              open("data/offerte.json", "w"), ensure_ascii=False, indent=1)
    print("offerte", len(items))

main()
