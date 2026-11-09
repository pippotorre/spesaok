import re, sys, html
from xml.etree import ElementTree as ET
def pages(path):
    src = open(path, encoding="utf-8").read()
    src = re.sub(r"<!DOCTYPE[^>]*>", "", src).replace("&nbsp;", " ")
    src = re.sub(r'xmlns="[^"]+"', "", src)
    src = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", src)
    root = ET.fromstring(src)
    for pi, pg in enumerate(root.iter("page"), 1):
        blocks = []
        for b in pg.iter("block"):
            lines = [" ".join(w.text or "" for w in l.iter("word")) for l in b.iter("line")]
            blocks.append({"x": float(b.get("xMin")), "y": float(b.get("yMin")), "x2": float(b.get("xMax")), "y2": float(b.get("yMax")), "lines": lines})
        yield pi, float(pg.get("width")), float(pg.get("height")), blocks
if __name__ == "__main__":
    want = int(sys.argv[2])
    for pi, w, h, bl in pages(sys.argv[1]):
        if pi == want:
            print(w, h)
            for b in sorted(bl, key=lambda b: (round(b["y"]/20), b["x"])):
                print(f'{b["x"]:6.0f}{b["y"]:6.0f} | ' + " / ".join(b["lines"])[:150])
