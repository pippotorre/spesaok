"""Prepara la PWA da caricare su TopHost (cartella /spesaok del sito).

    python scripts/build_pwa.py            -> dist/spesaok/ + dist/spesaok.zip

Copia pwa/ in dist/spesaok/, aggiunge data/offerte.json e mette un numero di
versione nei file (così telefoni e browser scaricano la nuova versione).
Aggiornamento settimanale: basta ricaricare dist/spesaok/offerte.json.
"""
import hashlib, json, pathlib, shutil, zipfile

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
for name in ("index.html", "sw.js"):
    f = OUT / name
    f.write_text(f.read_text().replace("__VER__", ver))

zpath = OUT.parent / "spesaok.zip"
with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
    for f in sorted(OUT.rglob("*")):
        z.write(f, f.relative_to(OUT.parent))
print(f"versione {ver}: {OUT} ({len(offerte['offerte'])} offerte), {zpath}")
