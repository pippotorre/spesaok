"""Estrae offerte dal volantino Mercatò a partire dall'OCR Tesseract (TSV, psm 11).
Il prezzo grande (bianco su rosso) l'OCR lo legge male; il prezzo al kg/litro e il
formato invece sono affidabili, quindi il prezzo si ricava da questi e si confronta
con le cifre lette nel riquadro."""
import csv, glob, os, re, sys

def words(path):
    out = []
    for r in csv.DictReader(open(path, encoding="utf-8", errors="ignore"), delimiter="\t", quoting=3):
        t = (r.get("text") or "").strip()
        if not t or float(r["conf"]) < 30: continue
        out.append({"t": t, "x": int(r["left"]), "y": int(r["top"]), "h": int(r["height"]), "w": int(r["width"]),
                    "k": (r["block_num"], r["par_num"], r["line_num"])})
    return out

def lines(ws):
    g = {}
    for w in ws: g.setdefault(w["k"], []).append(w)
    out = []
    for k, ws in g.items():
        ws.sort(key=lambda w: w["x"])
        out.append({"t": " ".join(w["t"] for w in ws), "x": ws[0]["x"], "y": min(w["y"] for w in ws),
                    "x2": max(w["x"] + w["w"] for w in ws), "h": max(w["h"] for w in ws)})
    return out

UNIT = re.compile(r"€\s*/\s*(lt|it|kg|k9|l|1|pz|hg)\.?\s*([0-9]+[,.][0-9]{2})", re.I)
QTY = re.compile(r"(?:(?:x|X)\s*(\d+)|(\d+)\s*x)?", re.I)
FMT = re.compile(r"\b(cl|ml|g|gr|kg|lt|l|it)\.?\s*([0-9]+(?:[,.][0-9]+)?)(?:\s*[xX]\s*(\d+))?|([0-9]+(?:[,.][0-9]+)?)\s*(cl|ml|g|gr|kg|lt|l)\b(?:\s*[xX]\s*(\d+))?", re.I)
FACT = {"cl": .01, "ml": .001, "g": .001, "gr": .001, "kg": 1, "lt": 1, "l": 1, "it": 1}

def qty_of(fmt):
    fmt = re.sub(r"(?<=[cl\.])([0-9oOzZ]{1,4})", lambda m: re.sub("[oO]", "0", m.group(1)).replace("z", "").replace("Z", ""), fmt)
    m = FMT.search(fmt.replace("cl.", "cl ").replace("It.", "lt ").replace("lt.", "lt "))
    if not m: return None
    if m.group(1):
        u, n, mult = m.group(1).lower(), m.group(2), m.group(3)
    else:
        n, u, mult = m.group(4), m.group(5).lower(), m.group(6)
    q = float(n.replace(",", ".")) * FACT[u] * (int(mult) if mult else 1)
    return q or None

def is_upper(t):
    L = [c for c in t if c.isalpha()]
    return len(L) >= 3 and sum(c.isupper() for c in L) / len(L) > .8

def parse(ocr_dir, vf, vt):
    out = []
    for f in sorted(glob.glob(f"{ocr_dir}/p-*.tsv")):
        page = int(re.search(r"p-(\d+)", f).group(1))
        ws = words(f); ls = lines(ws)
        solo = [w for w in ws if w["t"].lower() in ("solo", "soro", "solo.")]
        bigs = [w for w in ws if w["h"] >= 30 and re.search(r"\d", w["t"])]
        for u in ls:
            m = UNIT.search(u["t"])
            if not m: continue
            unit_kind = m.group(1).lower()
            unit = float(m.group(2).replace(",", "."))
            above = sorted([l for l in ls if abs(l["x"] - u["x"]) < 18 and 0 < u["y"] - l["y"] < 140 and l is not u],
                           key=lambda l: l["y"])
            name = " ".join(l["t"] for l in above if is_upper(l["t"]) and not UNIT.search(l["t"]))
            fmt = " ".join(l["t"] for l in above if not is_upper(l["t"]))
            fmt += " " + u["t"][:m.start()]
            name = re.sub(r"\s+", " ", name).strip(" ,.")
            if len(name) < 4: continue
            kind = "l" if unit_kind in ("lt", "it", "l", "1") else "kg" if unit_kind in ("kg", "k9", "hg") else None
            q = qty_of(fmt)
            if not q or not kind: continue
            from parse_coop import NONFOOD
            if NONFOOD.search(name + " " + fmt): continue
            price = round(unit * q, 2)
            box = [b for b in bigs if 0 < b["x"] - u["x"] < 420 and -60 < b["y"] - (above[0]["y"] if above else u["y"]) < 120]
            seen = re.sub(r"[^\d]", "", box[0]["t"]) if box else ""
            if len(seen) >= 3 and abs(int(seen[:3]) / (10 if price >= 10 else 100) - price) < 0.03 and price < 10:
                price = int(seen[:3]) / 100
            dubbio = q > 2 or unit > 150 or price < 0.15 or price > 60
            ny = above[0]["y"] if above else u["y"]
            card = any(0 < s["x"] - u["x"] < 420 and 0 < ny - s["y"] < 330 for s in solo)
            out.append({"catena": "Mercatò", "nome": name.title(), "marca": "", "formato": fmt.strip(),
                        "prezzo": price, "prezzo_pieno": None, "sconto_pct": None,
                        "prezzo_unita": unit, "unita": kind, "categoria": "", "con_carta": card,
                        "valido_dal": vf, "valido_al": vt, "da_verificare": dubbio, "pagina": page})
    return out

if __name__ == "__main__":
    r = parse(sys.argv[1], "2026-11-02", "2026-11-15")
    print(len(r), "sicuri", sum(not x["da_verificare"] for x in r), "carta", sum(x["con_carta"] for x in r))
    for x in r[:45]: print(x["pagina"], x["nome"], "|", x["formato"], "|", x["prezzo"], x["prezzo_unita"], x["unita"], "C" if x["con_carta"] else "", "?" if x["da_verificare"] else "")
