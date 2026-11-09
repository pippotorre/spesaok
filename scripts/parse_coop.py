"""Estrae le offerte dal PDF Coop (output di pdftotext -bbox-layout)."""
import re, sys
sys.path.insert(0, "scripts")
from coop_blocks import pages

KEY = {"CONVIENE", "SCONTO", "SOCI", "SOLO PER I", "SCONTO SOCI", "OGNI SPESA IL MEGLIO", "SCEGLI TU"}
NONFOOD = re.compile(r"detersiv|shampoo|balsamo|carta igienic|pannolin|ammorbident|dentifric|bagnoschiuma|"
                     r"crocchett|\bcane\b|\bcani\b|gatt[oi]|lettiera|deodorant|assorbent|sapone|"
                     r"rotoli|fazzolett|candeggin|sgrassat|pentol|padell|lavastovigli|lavatrice|"
                     r"concim|\bauto\b|lavavetri|additiv|radiator|pellet|oli motore|adblue|lubrific|svitol|elettric|scarpon|\btv\b|detergent|pavimenti|\bwc\b|bucato|piatti|carta casa|scottex|tovaglioli|panno|spugn|insetticid|profumator|deterg|spazzolin|rasoi|igienizz|pet\b|cosmetic|crema viso|struccant", re.I)
PRICE = re.compile(r"(\d+) ?,(\d\d) €")

def num(m): return float(f"{m.group(1)}.{m.group(2)}")

def is_name(b):
    t = b["lines"][0].strip()
    letters = [c for c in t if c.isalpha()]
    return (len(letters) >= 4 and sum(c.isupper() for c in letters) / len(letters) > 0.85
            and t not in KEY and "€" not in t and not t.startswith("SCONTO") and not t.startswith("SOLO")
            and "%" not in t and not re.search(r"PRENDI|PAGHI|SOTTOCOSTO|OFFERTA", t))

def parse(path, valid_from, valid_to):
    out = []
    for pi, w, h, bl in pages(path):
        names = [b for b in bl if is_name(b)]
        cells = {id(n): {"n": n, "blocks": []} for n in names}
        for b in bl:
            if b in names: continue
            best = None
            for n in names:
                if n["y"] <= b["y"] + 2 and n["x"] - 15 <= b["x"] <= n["x"] + 145:
                    if best is None or n["y"] > best["y"]: best = n
            if best: cells[id(best)]["blocks"].append(b)
        for c in cells.values():
            n = c["n"]; text = [l for b in c["blocks"] for l in b["lines"]]
            name = " ".join(n["lines"]).strip()
            fmt_lines = [l for b in c["blocks"] if abs(b["x"] - n["x"]) < 8 and b["y"] - n["y"] < 45 for l in b["lines"]]
            fmt = " ".join(fmt_lines)
            fmt = re.sub(r"\d+ ?,\d\d €.*|CONVIENE.*|SOLO PER I.*|SCONTO.*", "", fmt).strip(" ,")
            final = unit = old = old_unit = None
            for l in text:
                if "al kg" in l or "al lt" in l or "al l " in l:
                    ps = list(PRICE.finditer(l))
                    if len(ps) == 2: old, old_unit = num(ps[0]), num(ps[1])
                    elif len(ps) == 1: unit = num(ps[0])
                else:
                    for m in PRICE.finditer(l):
                        if " ," in m.group(0): final = num(m)
                        elif final is None: final = num(m)
            if final is None: continue
            if old is not None and old <= final: old = None
            full = f"{name} {fmt}"
            if NONFOOD.search(full): continue
            card = any("SOCI" in l for l in text)
            if unit is None and final > 15: continue
            if unit is None and not re.search(r"\d\s*(kg|g|ml|cl|lt|l)\b|all.etto", fmt, re.I): continue
            m = re.search(r"(\d+(?:,\d+)?)\s*(kg|g|ml|cl|lt|l)\b", fmt, re.I)
            if unit is None:
                q = re.search(r"(?:(\d+) x )?(\d+(?:[.,]\d+)?)\s*(kg|g|ml|cl|lt|l)\b", fmt, re.I)
                if q:
                    qty = float(q.group(2).replace(",", ".")) * (int(q.group(1)) if q.group(1) else 1)
                    qty *= {"kg": 1, "g": .001, "ml": .001, "cl": .01, "lt": 1, "l": 1}[q.group(3).lower()]
                    if qty: unit = round(final / qty, 2)
            out.append({
                "catena": "Coop", "nome": name.title(), "marca": "",
                "formato": fmt, "prezzo": final, "prezzo_pieno": old,
                "sconto_pct": round(100 * (1 - final / old)) if old and old > final else None,
                "prezzo_unita": unit, "unita": ("l" if re.search(r"\d\s*(ml|cl|lt|l)\b", fmt, re.I) else "kg" if re.search(r"\d\s*(kg|g)\b|etto", fmt, re.I)
                          else "l" if re.search(r"birra|acqua|vino|succo|bevanda|spumante", name, re.I) else "kg") if unit else None,
                "categoria": "", "con_carta": card,
                "valido_dal": valid_from, "valido_al": valid_to, "pagina": pi,
            })
    return out

if __name__ == "__main__":
    r = parse(sys.argv[1], "2026-11-05", "2026-11-18")
    print(len(r))
    for x in r[:40]: print(x["pagina"], x["nome"], "|", x["formato"], "|", x["prezzo"], x["prezzo_pieno"], x["prezzo_unita"], x["con_carta"])
