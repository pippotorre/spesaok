"""Estrae offerte dal volantino MD (PDF a immagini) dall'OCR Tesseract (TSV, psm 11).
Schema della cella: NOME in maiuscolo, marca (maiuscolo più piccolo), formato ("g 100"),
poi più in basso il prezzo grande (letto male dall'OCR), il prezzo barrato e "€ 10,82 al kg".
Come per Mercatò il prezzo si ricava da prezzo al kg/l × formato."""
import glob, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from parse_mercato import words, lines, qty_of
from parse_coop import NONFOOD

UP = re.compile(r"^[A-ZÀ-Ý0-9'’!&.,()\- ]+$")
UNITP = re.compile(r"€?\s*([0-9]+(?:[,.][0-9]{1,2})?)\s*(0?l?kg|al\s*kg|alkg|al\s*l|al\s*lt|all|ollt|lkg|llt)\b", re.I)

def unit_val(t):
    m = re.search(r"€?\s*([0-9]+)(?:[,.]([0-9]{1,2}))?\s*(a?l+\s*k[g9]|a?l+\s*l?t?|olkg|0lkg|lkg)", t.replace(" ", ""), re.I)
    if not m: return None, None
    a, b, u = m.group(1), m.group(2), m.group(3).lower()
    un = "kg" if "k" in u else "l"
    if b is not None: return float(f"{a}.{b}"), un
    glued = not re.search(r"al", u)          # la "a" di "al" letta come cifra
    if glued and len(a) >= 4: a = a[:-1]
    if len(a) < 3: return None, None
    return float(f"{a[:-2]}.{a[-2:]}"), un

def parse(ocr_dir, vf, vt, fonte):
    out = []
    for f in sorted(glob.glob(f"{ocr_dir}/p-*.tsv")):
        pagina = int(re.search(r"p-(\d+)", f).group(1))
        pw = int(open(f).readlines()[1].split("\t")[8])
        k = pw / 1734                              # coordinate tarate a 200 dpi
        L = sorted(({**l, "x": l["x"] / k, "y": l["y"] / k, "h": l["h"] / k} for l in lines(words(f))), key=lambda l: (l["y"], l["x"]))
        used = set()
        for i, l in enumerate(L):
            if i in used or not UP.match(l["t"]) or len(re.sub(r"[^A-Z]", "", l["t"])) < 3: continue
            blk = [l]; used.add(i); last = l
            for j in range(i + 1, len(L)):
                m = L[j]
                if m["y"] - last["y"] > 48: break
                if abs(m["x"] - l["x"]) < 30 and j not in used:
                    blk.append(m); used.add(j); last = m
            ups = [b for b in blk if UP.match(b["t"]) and not re.match(r"^(g|kg|ml|cl|l|lt)\b", b["t"], re.I)]
            if not ups: continue
            hmax = max(b["h"] for b in ups)
            name = [b["t"] for b in ups if b["h"] >= hmax - 1.5]
            brand = [b["t"] for b in ups if b["h"] < hmax - 1.5]
            if len(name) == len(ups) and len(ups) >= 3: brand = [name.pop()]
            desc = [b["t"] for b in blk if not UP.match(b["t"])]
            fmt = next((d for d in desc[::-1] if re.match(r"^\s*(g|gr|kg|ml|cl|l|lt|9g|9)\s*[0-9]", d, re.I)), None)
            if fmt: fmt = re.sub(r"^9g?\s", "g ", fmt)
            q = qty_of(fmt) if fmt else None
            # prezzo al kg/l: nella stessa colonna, 300-700 px sotto il nome
            cand = [m for m in L if l["x"] - 90 <= m["x"] <= l["x"] + 320 and 300 < m["y"] - l["y"] < 700
                    and re.search(r"k[g9]|al\s*l|alkg|lkg", m["t"], re.I)]
            unit = un = None
            for c in sorted(cand, key=lambda c: c["y"]):
                unit, un = unit_val(c["t"])
                if unit: break
            nome = " ".join(name).title()
            if not unit or not q or NONFOOD.search(nome): continue
            prezzo = round(unit * q, 2)
            out.append({"catena": "MD", "nome": nome, "marca": " ".join(brand).title(), "formato": fmt,
                        "prezzo": prezzo, "prezzo_pieno": None, "sconto_pct": None, "prezzo_unita": unit, "unita": un,
                        "categoria": "", "con_carta": False, "valido_dal": vf, "valido_al": vt, "fonte": fonte,
                        "pagina": pagina, "da_verificare": q > 2.5 or unit > 120 or prezzo < 0.4 or prezzo > 50 or len(nome) < 4})
    return out

if __name__ == "__main__":
    for r in parse(sys.argv[1], None, None, ""):
        print(r["pagina"], r["nome"], "|", r["marca"], "|", r["formato"], r["prezzo"], r["prezzo_unita"], r["unita"], "!" if r["da_verificare"] else "")
