"""Prepara la PWA da caricare su TopHost (cartella /spesaok del sito).

    python scripts/build_pwa.py            -> dist/spesaok/ + dist/spesaok.zip
    python scripts/build_pwa.py --dati https://pippotorre.github.io/spesaok/offerte.json
        -> versione per TopHost che legge le offerte da GitHub Pages (niente upload settimanali)

Copia pwa/ in dist/spesaok/, aggiunge data/offerte.json e mette un numero di
versione nei file (così telefoni e browser scaricano la nuova versione).
Aggiornamento settimanale: basta ricaricare dist/spesaok/offerte.json.
"""
import argparse, hashlib, json, pathlib, shutil, zipfile

ap = argparse.ArgumentParser()
ap.add_argument("--dati", default="offerte.json", help="indirizzo da cui la PWA legge le offerte")
ap.add_argument("--zip", default="spesaok.zip")
args = ap.parse_args()

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / "pwa", ROOT / "dist" / "spesaok"

if OUT.exists():
    shutil.rmtree(OUT)
shutil.copytree(SRC, OUT, ignore=shutil.ignore_patterns("*.md"))
offerte = json.loads((ROOT / "data" / "offerte.json").read_text())
(OUT / "offerte.json").write_text(json.dumps(offerte, ensure_ascii=False, separators=(",", ":")))

h = hashlib.sha1()
for f in sorted(SRC.rglob("*")):
    if f.is_file():
        h.update(f.read_bytes())
ver = h.hexdigest()[:8]
ver = hashlib.sha1((ver + args.dati).encode()).hexdigest()[:8]
(OUT / "index.html").write_text((OUT / "index.html").read_text().replace("__VER__", ver)
    .replace('content="offerte.json"', f'content="{args.dati}"'))
(OUT / "sw.js").write_text((OUT / "sw.js").read_text().replace("__VER__", ver).replace("__DATI__", args.dati))

zpath = OUT.parent / args.zip
with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
    for f in sorted(OUT.rglob("*")):
        z.write(f, f.relative_to(OUT.parent))
print(f"versione {ver}: {OUT} ({len(offerte['offerte'])} offerte), {zpath}")
