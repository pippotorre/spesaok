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
            "fonte": "https://flyer.eurospin.com/it-it/punti-vendita/eurospin-italia/promozioni/" + x.get("_promo", {}).get("alias", ""),
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
        i = int(re.search(r"coop_pdf(\d+)", f).group(1))
        vols = {}
        if os.path.exists(f"{raw}/coop_info.json"):
            vols = {v.get("i"): v for v in json.load(open(f"{raw}/coop_info.json")).get("volantini", [])}
        store = vols.get(i, {}).get("negozio", "")
        label = "Coop Collegno" if "8001120004550" in store else "Ipercoop Torino" if "8001120004796" in store else "Coop"
        rows = parse(f, vf, vt)
        for r in rows:
            r["catena"] = label
            r["fonte"] = vols.get(i, {}).get("final", "").split("?")[0]
        out += rows
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
    rows = parse(d, vf, vt)
    for r in rows: r["fonte"] = "https://www.mymercato.it/mondo-mercato/volantini"
    return rows

def coop_linee(raw):
    """Pagine 'Sconto X% su tutta la linea': le marche sono loghi e l'OCR non le legge bene,
    quindi si segnala la pagina con lo sconto e il link al volantino."""
    info = f"{raw}/coop_info.json"
    if not os.path.exists(info): return []
    vols = {v["i"]: v for v in json.load(open(info)).get("volantini", []) if "i" in v}
    out = []
    for f in sorted(glob.glob(f"{raw}/coop_pdf*.txt")):
        i = int(re.search(r"coop_pdf(\d+)", f).group(1))
        v = vols.get(i, {})
        if "8001120004550" not in v.get("negozio", ""): continue  # solo il negozio di Collegno
        for n, page in enumerate(open(f).read().split("\f"), 1):
            if not re.search(r"tutta\s+la\s+linea", page, re.I): continue
            pct = re.search(r"Sconto\s+(\d{2})\s", re.sub(r"\s+", " ", page))
            if not pct: continue
            out.append({"pct": int(pct.group(1)), "pagina": n, "pdf": (v.get("pdfs") or [""])[0],
                        "volantino": v.get("final", "").split("?")[0]})
    return out

ALDI_FOOD = {"Dispensa", "Farina e prodotti da forno", "Carne fresca, pesce e salumi", "Prodotti refrigerati",
             "Bevande analcoliche", "Bevande alcoliche", "Freezer", "Proteico", "Frutta e verdura", "Colazione",
             "Snack dolci e salati", "Dolci e snack"}

def aldi(raw):
    """Speciali della settimana Aldi (API product-search). Prezzi in centesimi."""
    import datetime as dt
    from parse_coop import NONFOOD
    out = []
    for x in json.load(open(f"{raw}/aldi_products.json")):
        cats = [c["name"] for c in x.get("categories") or []]
        pr = x.get("price") or {}
        cmp_ = pr.get("comparisonDisplay") or ""
        m = re.search(r"/\s*1\s*(kg|l)\b", cmp_)
        if not (cats and cats[0] in ALDI_FOOD) and not m: continue   # Natale, Mondo Baby ecc.: solo se prezzo al kg/l
        name = x.get("name") or ""
        if NONFOOD.search(name) or NON_FOOD_WORDS.search(name): continue
        if re.search(r"Animali|Casa|Igiene|Tempo libero|Abbigliamento|Elettronica", " ".join(cats)): continue
        if not pr.get("amountRelevant"): continue
        was = re.search(r"([0-9]+,[0-9]{2})", pr.get("wasPriceDisplay") or "")
        sc = re.search(r"(\d+)\s*%", pr.get("savingsDisplay") or "")
        k = x["_promo"]["key"]
        out.append({
            "catena": "Aldi", "nome": name, "marca": (x.get("brandName") or "").title(),
            "formato": x.get("sellingSize"), "prezzo": pr["amountRelevant"] / 100,
            "prezzo_pieno": float(was.group(1).replace(",", ".")) if was else None,
            "sconto_pct": int(sc.group(1)) if sc else None,
            "prezzo_unita": pr["comparison"] / 100 if m and pr.get("comparison") else None,
            "unita": m.group(1) if m else None,
            "categoria": cats[0] if cats else "",
            "con_carta": False,
            "valido_dal": k, "valido_al": str(dt.date.fromisoformat(k) + dt.timedelta(days=6)),
            "fonte": x["_promo"]["pagina"],
        })
    return out

def md(raw):
    from parse_md import parse
    info = json.load(open(f"{raw}/md_info.json"))
    vf = vt = None
    m = re.search(r"DAL (\d+)(?: \w+)? AL (\d+) (\w+) (\d{4})", info.get("validita") or "")
    if m:
        mesi = "gennaio febbraio marzo aprile maggio giugno luglio agosto settembre ottobre novembre dicembre".split()
        mm = mesi.index(m.group(3).lower()) + 1
        vf = f"{m.group(4)}-{mm:02d}-{int(m.group(1)):02d}"; vt = f"{m.group(4)}-{mm:02d}-{int(m.group(2)):02d}"
    rows = parse(f"{raw}/md_ocr", vf, vt, (info.get("pdfs") or [info["negozio"]])[0])
    for r in rows: r["catena"] = "MD Torino"
    return rows

GIGANTE_NONFOOD = re.compile(
    r"gioc|lego|bambol|peluche|barbie|macchin|maglie|maglion|plaid|abbigliam|leggings|detersiv|ammorbident|"
    r"cibo per|crocchette|lettiera|animali|assorbent|pannolin|arredo|sgrassat|carta igienica|pulizi|profumator|"
    r"contenitori|basket|\btv\b|ps5|smart|dentifric|spazzolin|detergente|doccia|sapone|shampoo|collutorio|"
    r"schiuma|guanti|anticalcare|lavastoviglie|scopa|swiffer|candeggina|rotoli|tovaglioli|fazzoletti|bicchieri|"
    r"stagnola|sacchett|piatti di plastica|poltron|pouf|grucce|casalinghi|armadi|pattumiera|mobile|padella|"
    r"stendi|stampi|candele|pentol|bici|action|letti|trapunt|drone|magia|divan|aspirapolvere|tappet|make up|"
    r"piante|acquario|asciugatrice|frigorifer|microonde|vaporella|smartphone|cotone|dinosaur|telecomandat|"
    r"didattic|educativ|accessori|bagno|igien|lines|tempo\b", re.I)
GIGANTE_QTY = re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:x\s*(\d+(?:[.,]\d+)?)\s*)?(kg|gr?|ml|cl|lt?|litri|litro)\b", re.I)

def gigante(raw):
    """Il Gigante (corso Marche): prodotti del visualizzatore ShopFully con titolo, marca, prezzo e
    testo letto dall'immagine (google_vision_text), da cui si ricavano formato, prezzo al kg/l e Blucard."""
    info = json.load(open(f"{raw}/gigante_info.json"))
    out = []
    for v in info["volantini"]:
        f = f"{raw}/gigante_{v['id']}.json"
        if not os.path.exists(f): continue
        for x in json.load(open(f)):
            st = x.get("settings") or {}
            cat, title, gv = st.get("shared_category") or "", (x.get("title") or "").strip(), st.get("google_vision_text") or ""
            if GIGANTE_NONFOOD.search(cat) or GIGANTE_NONFOOD.search(title) or NON_FOOD_WORDS.search(title): continue
            m = re.search(r"(\d+[.,]\d{2})", st.get("price") or "")
            if not m: continue
            price = float(m.group(1).replace(",", "."))
            brand = (st.get("brand") or "").strip()
            name = title.split(" - ", 1)[1].strip() if " - " in title else title
            q = GIGANTE_QTY.search(gv)
            formato, qty, unit = None, None, None
            if q:
                n = float(q.group(1).replace(",", ".")) * (float(q.group(2).replace(",", ".")) if q.group(2) else 1)
                u = q.group(3).lower()
                qty, unit = ({"kg": (n, "kg"), "g": (n / 1000, "kg"), "gr": (n / 1000, "kg"), "ml": (n / 1000, "l"),
                              "cl": (n / 100, "l")}.get(u) or (n, "l"))
                formato = q.group(0)
            pu = re.search(r"al\s*(kg|lt?|litro)\.?\s*€?\s*(\d+[.,]\d{2})", gv, re.I)
            prezzo_unita = None
            if pu:
                prezzo_unita = float(pu.group(2).replace(",", ".")); unit = "kg" if pu.group(1).lower() == "kg" else "l"
                if qty and abs(price / qty - prezzo_unita) / prezzo_unita > 0.25: prezzo_unita = round(price / qty, 2)
            elif qty and qty > 0:
                prezzo_unita = round(price / qty, 2)
            sc = re.search(r"-\s?(\d{1,2})\s?%", gv)
            sconto = int(sc.group(1)) if sc and 5 <= int(sc.group(1)) <= 70 else None
            note = "1+1 gratis: 2 pezzi a metà prezzo" if re.search(r"1\s*\+\s*1", gv) else None
            out.append({
                "catena": "Il Gigante", "nome": name, "marca": brand if brand.lower() != "il gigante" else "Il Gigante",
                "formato": ", ".join(p for p in (formato, note) if p) or None, "prezzo": price,
                "prezzo_pieno": round(price / (1 - sconto / 100), 2) if sconto else None, "sconto_pct": sconto,
                "prezzo_unita": prezzo_unita, "unita": unit if prezzo_unita else None,
                "categoria": cat, "con_carta": "BLUCARD" in gv.upper(),
                "valido_dal": v.get("dal"), "valido_al": v.get("al"),
                "pagina": int(st["flyer_page"]) if str(st.get("flyer_page", "")).isdigit() else None,
                "fonte": v["url"],
            })
    return out

def latest(pattern):
    """Ultima cartella data/raw/<data> che contiene i file della catena."""
    ds = [d for d in sorted(glob.glob("data/raw/*")) if glob.glob(f"{d}/{pattern}")]
    return ds[-1] if ds else None

def main():
    sys.path.insert(0, "scripts")
    items, dates = [], []
    for fn, pat in ((eurospin, "eurospin_products.json"), (coop, "coop_pdf*_bbox.html"), (mercato, "mercato_ocr"), (aldi, "aldi_products.json"), (md, "md_ocr"), (gigante, "gigante_info.json")):
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
    d = latest("coop_info.json")
    linee = coop_linee(d) if d else []
    json.dump({"aggiornato": max(dates) if dates else "", "fonti": fonti, "linee_coop": linee, "offerte": items},
              open("data/offerte.json", "w"), ensure_ascii=False, indent=1)
    print("offerte", len(items))

main()
