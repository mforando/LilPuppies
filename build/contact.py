"""Contact sheets of the best-scoring silhouettes per breed, for choosing glyphs by eye.

Writes .cache/sheets/sheet-NN.png. Each row is one breed; each tile is labelled
"<rank>" and the photo's file name, which is what glyphs.json refers to.
Usage (from LilPuppies/): python -I build/contact.py [per_breed] [breeds_per_sheet] [breed ...]

    python -I build/contact.py --breeds [code ...]
draws the same sheets for the breeds in breeds.json that have no letter (.cache/sheets/breeds-NN.png),
eight candidates per breed with the current pick (build/breed_glyphs.json) outlined, and writes
.cache/sheets/breeds.json mapping each code to its numbered candidates' files.
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageOps

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from breeds import NAMES  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, ".cache")


def breed_sheets(only):
    from catalog import load, pool
    segs = json.load(open(os.path.join(CACHE, "segments.json")))
    picks = json.load(open(os.path.join(ROOT, "build", "breed_glyphs.json"), encoding="utf8"))
    K, ROWS, TW, TH, LAB = 8, 10, 150, 100, 160
    rows = []
    for b in load():
        if b["alias"] or picks.get(b["code"], {}).get("letter") or (only and b["code"] not in only):
            continue
        recs = pool(b, segs)
        recs.sort(key=lambda r: (not r["ok"], -r["score"]))
        rows.append((b, recs[:K]))
    numbered = {}
    os.makedirs(os.path.join(CACHE, "sheets"), exist_ok=True)
    for s in range(0, len(rows), ROWS):
        chunk = rows[s:s + ROWS]
        sheet = Image.new("RGB", (LAB + K * TW, len(chunk) * (TH + 18)), "white")
        d = ImageDraw.Draw(sheet)
        for row, (b, recs) in enumerate(chunk):
            y = row * (TH + 18)
            d.text((6, y + TH // 2 - 8), b["name"][:26], fill="black")
            d.text((6, y + TH // 2 + 6), b["code"], fill=(120, 120, 120))
            numbered[b["code"]] = [r["file"] for r in recs]
            for col, r in enumerate(recs):
                sil = ImageOps.invert(Image.open(os.path.join(CACHE, r["mask"])).convert("L"))
                sil.thumbnail((TW - 12, TH - 8))
                x = LAB + col * TW
                sheet.paste(sil, (x + (TW - sil.width) // 2, y + TH - sil.height))
                if picks.get(b["code"], {}).get("file") == r["file"]:
                    d.rectangle([x + 1, y + 1, x + TW - 2, y + TH + 14], outline=(220, 60, 40), width=2)
                d.text((x + 4, y + TH + 2), f"{col + 1}{'' if r['ok'] else ' (fallback)'}", fill=(90, 90, 90))
            d.line([(0, y + TH + 16), (sheet.width, y + TH + 16)], fill=(220, 220, 220))
        sheet.save(os.path.join(CACHE, "sheets", f"breeds-{s // ROWS + 1:02d}.png"))
        print("breeds sheet", s // ROWS + 1, " ".join(b["code"] for b, _ in chunk))
    json.dump(numbered, open(os.path.join(CACHE, "sheets", "breeds.json"), "w"), indent=1)


if "--breeds" in sys.argv:
    breed_sheets([a for a in sys.argv[1:] if a != "--breeds"])
    sys.exit()

K = int(sys.argv[1]) if len(sys.argv) > 1 else 6
ROWS = int(sys.argv[2]) if len(sys.argv) > 2 else 12
ONLY = sys.argv[3:]
TW, TH, LAB = 190, 130, 150

segs = json.load(open(os.path.join(CACHE, "segments.json")))
by = {}
for r in segs.values():
    if r["ok"]:
        by.setdefault(r["breed"], []).append(r)
breeds = [b for b in sorted(by) if not ONLY or b in ONLY]

os.makedirs(os.path.join(CACHE, "sheets"), exist_ok=True)
for s in range(0, len(breeds), ROWS):
    chunk = breeds[s:s + ROWS]
    sheet = Image.new("RGB", (LAB + K * TW, len(chunk) * (TH + 18)), "white")
    d = ImageDraw.Draw(sheet)
    for row, b in enumerate(chunk):
        y = row * (TH + 18)
        d.text((6, y + TH // 2), NAMES.get(b, b)[:24], fill="black")
        d.text((6, y + TH // 2 + 14), b, fill=(120, 120, 120))
        for col, r in enumerate(sorted(by[b], key=lambda r: -r["score"])[:K]):
            m = Image.open(os.path.join(CACHE, r["mask"])).convert("L")
            sil = ImageOps.invert(m)  # black dog on white
            sil.thumbnail((TW - 12, TH - 8))
            x = LAB + col * TW
            sheet.paste(sil, (x + (TW - sil.width) // 2, y + TH - sil.height))
            d.text((x + 4, y + TH + 2), f"{col + 1} {r['file'].rsplit('/', 1)[1][:22]} {r['score']:.2f}", fill=(90, 90, 90))
        d.line([(0, y + TH + 16), (sheet.width, y + TH + 16)], fill=(220, 220, 220))
    sheet.save(os.path.join(CACHE, "sheets", f"sheet-{s // ROWS + 1:02d}.png"))
    print("sheet", s // ROWS + 1, ", ".join(chunk))
