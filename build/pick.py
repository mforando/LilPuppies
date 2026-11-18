"""Pick one photo per breed in breeds.json, and whether to flip it so the dog faces right.

A breed that already has a letter (glyphs.json) reuses that letter's photo, so a breed always has
one silhouette. Otherwise it takes the best-scoring usable mask, or for breeds whose only photos
failed a check in segment.py, the best fallback mask.

Writes build/breed_glyphs.json. Entries with "auto": false were set by hand and are kept on
re-runs; to override a pick, change its "file" or "flip" and set "auto" to false.
Usage (from LilPuppies/): python -I build/pick.py
"""
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from catalog import load, pool  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CACHE = os.path.join(ROOT, ".cache")
OUT = os.path.join(HERE, "breed_glyphs.json")


def faces_right(mask):
    """Guess the dog's facing from its outline: the head is usually the highest mass, at the front."""
    m = np.asarray(mask) > 127
    ys, xs = np.nonzero(m)
    top, bot = ys.min(), ys.max()
    band = ys < top + 0.4 * (bot - top)
    mid = (xs.min() + xs.max()) / 2
    return float(xs[band].mean()) >= mid


def main():
    segs = json.load(open(os.path.join(CACHE, "segments.json")))
    letters = json.load(open(os.path.join(HERE, "glyphs.json"), encoding="utf8"))
    letter_file = {f"{g['breed'].replace('/', '-')}/{g['photo']}": (ch, g) for ch, g in letters.items()}
    old = json.load(open(OUT, encoding="utf8")) if os.path.exists(OUT) else {}

    out = {}
    for b in load():
        code = b["code"]
        if b["alias"]:
            continue
        if code in old and old[code].get("auto") is False:
            out[code] = old[code]
            continue
        files = [c["file"] for c in b["candidates"]]
        folders = {f.split("/", 1)[0] for f in files}
        reuse = [lf for lf in letter_file if lf.split("/", 1)[0] in folders]
        if reuse:
            ch, g = letter_file[reuse[0]]
            out[code] = {"file": reuse[0], "flip": bool(g.get("flip")), "letter": ch, "auto": True}
            continue
        recs = pool(b, segs)
        good = sorted((r for r in recs if r["ok"]), key=lambda r: -r["score"])
        rest = sorted((r for r in recs if not r["ok"]), key=lambda r: -r["score"])
        pick = (good or rest or [None])[0]
        if pick is None:
            print(f"{code} {b['name']}: no usable photo")
            continue
        mask = Image.open(os.path.join(CACHE, pick["mask"])).convert("L")
        out[code] = {"file": pick["file"], "flip": not faces_right(mask), "auto": True}
        if not pick["ok"]:
            out[code]["fallback"] = pick.get("why")
    with open(OUT, "w", encoding="utf8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
    n_fb = sum(1 for v in out.values() if v.get("fallback"))
    print(f"picked {len(out)} breeds ({sum(1 for v in out.values() if v.get('letter'))} reuse a letter, {n_fb} fallback masks)")


if __name__ == "__main__":
    main()
