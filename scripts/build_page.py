"""Genera la pagina con i dati incorporati: python scripts/build_page.py <output.html>"""
import json, sys
d = json.load(open("data/offerte.json"))
html = open("app/template.html").read().replace("/*DATA*/", json.dumps(d, ensure_ascii=False))
open(sys.argv[1] if len(sys.argv) > 1 else "app/index.html", "w").write(html)
