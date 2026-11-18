"""Trace the chosen dog silhouettes and build the WeeDogs font.

Reads build/glyphs.json (one photo per character, picked from the contact sheets) and the
masks in .cache/masks/, and writes to weedogs/:
    weedogs.ttf, weedogs.woff, weedogs.woff2   the font
    weedogs.css                                @font-face with the font embedded, plus .weedogs
    weedogs.json                               each character's breed and source photo
    weedogs_all.png                            every glyph with its character
Usage (from weedogs/): python -I build/build_font.py
"""
import base64
import json
import os
import sys

import cv2
import numpy as np
import potrace
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.misc.timeTools import timestampNow
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from breeds import NAMES  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CACHE = os.path.join(ROOT, ".cache")

UPM = 1000
ADVANCE = 1000          # every dog gets the same width, like WeePeople's people
SPACE = 950             # WeePeople's space is a little narrower than a figure
BOX_W, BOX_H = 900, 680  # the largest a dog can be; feet sit on the baseline
ASCENT, DESCENT, CAP, XH = 800, -200, 700, 500
VERSION = "1.000"


def clean(mask):
    """Smooth the mask's edge and drop specks before tracing."""
    m = (mask > 127).astype(np.uint8)
    k = max(3, int(round(min(m.shape) * 0.02)) | 1)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    if n > 1:
        m = (lab == 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))).astype(np.uint8)
    return m


def fit(m):
    """Scale the mask so the dog fills BOX_W x BOX_H (keeping its shape), one pixel = one font unit."""
    h, w = m.shape
    s = min(BOX_W / w, BOX_H / h)
    W, H = max(1, int(round(w * s))), max(1, int(round(h * s)))
    big = cv2.resize(m.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
    big = cv2.GaussianBlur(big, (0, 0), sigmaX=max(1.0, 2.5 * s / 4))
    return big > 0.5


def area(pts):
    a = 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        a += x0 * y1 - x1 * y0
    return a / 2


def inside(pt, poly):
    x, y = pt
    c = False
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
            c = not c
    return c


def trace(bitmap):
    """Potrace the bitmap into contours of ("line"|"curve", points) in font units (y up)."""
    H, W = bitmap.shape
    dx = (ADVANCE - W) / 2
    tf = lambda p: (p.x + dx, H - p.y)  # noqa: E731 (image y runs down, font y runs up)
    out = []
    for curve in potrace.Bitmap(~bitmap).trace(turdsize=60, alphamax=1.0, opticurve=True, opttolerance=0.4):
        segs, poly = [], [tf(curve.start_point)]
        for s in curve.segments:
            if s.is_corner:
                segs += [("line", [tf(s.c)]), ("line", [tf(s.end_point)])]
                poly += [tf(s.c), tf(s.end_point)]
            else:
                segs.append(("curve", [tf(s.c1), tf(s.c2), tf(s.end_point)]))
                poly.append(tf(s.end_point))
        out.append((tf(curve.start_point), segs, poly))
    return out


def draw(contours, pen):
    """TrueType wants outer contours clockwise and holes counter-clockwise (y up)."""
    for i, (start, segs, poly) in enumerate(contours):
        depth = sum(inside(poly[0], other[2]) for j, other in enumerate(contours) if j != i)
        want_cw = depth % 2 == 0
        cw = area(poly) < 0
        if cw != want_cw:  # reverse: walk the segments backwards
            pts = [start]
            for kind, p in segs:
                pts += p
            rev = []
            k = len(pts) - 1
            for kind, p in reversed(segs):
                n = len(p)
                prev = pts[k - n]
                if kind == "curve":
                    rev.append(("curve", [p[1], p[0], prev]))
                else:
                    rev.append(("line", [prev]))
                k -= n
            start, segs = pts[-1], rev
        pen.moveTo(start)
        for kind, p in segs:
            if kind == "curve":
                pen.curveTo(*p)
            else:
                pen.lineTo(p[0])
        pen.closePath()


def main():
    spec = json.load(open(os.path.join(HERE, "glyphs.json"), encoding="utf8"))
    segs = json.load(open(os.path.join(CACHE, "segments.json")))
    by_name = {r["file"].rsplit("/", 1)[1]: r for r in segs.values() if r["ok"]}

    order = [".notdef", "space"] + list(spec)
    glyphs, cmap, key = {}, {32: "space"}, {}

    # .notdef: an empty box, the convention for "no glyph here"
    pen = TTGlyphPen(None)
    for x0, y0, x1, y1, d in [(100, 0, 900, 700, 1), (150, 50, 850, 650, -1)]:
        pts = [(x0, y0), (x0, y1), (x1, y1), (x1, y0)]
        pts = pts if d == 1 else pts[::-1]
        pen.moveTo(pts[0])
        for p in pts[1:]:
            pen.lineTo(p)
        pen.closePath()
    glyphs[".notdef"] = pen.glyph()
    glyphs["space"] = TTGlyphPen(None).glyph()

    for ch, g in spec.items():
        r = by_name[g["photo"]]
        m = clean(np.array(Image.open(os.path.join(CACHE, r["mask"])).convert("L")))
        if g.get("flip"):
            m = m[:, ::-1]
        bitmap = fit(m)
        pen = TTGlyphPen(None)
        draw(trace(bitmap), Cu2QuPen(pen, max_err=1.0, reverse_direction=False))
        glyphs[ch] = pen.glyph()
        cmap[ord(ch)] = ch
        key[ch] = {"breed": NAMES[r["breed"]], "dogCeoBreed": r["breed"], "photo": r["url"]}

    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyphs)
    glyf = fb.font["glyf"]
    metrics = {}
    for n in order:
        g = glyf[n]
        g.recalcBounds(glyf)
        metrics[n] = (SPACE if n == "space" else ADVANCE, getattr(g, "xMin", 0))
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=ASCENT, descent=DESCENT)
    fb.setupNameTable({
        "familyName": "WeeDogs",
        "styleName": "Regular",
        "uniqueFontIdentifier": f"WeeDogs-Regular-{VERSION}",
        "fullName": "WeeDogs Regular",
        "psName": "WeeDogs-Regular",
        "version": f"Version {VERSION}",
        "description": "Dog silhouettes for unit charts, one breed per letter. Inspired by ProPublica's WeePeople; "
                       "traced from Dog CEO API photos (Stanford Dogs Dataset).",
        "licenseDescription": "For non-commercial use. The silhouettes are traced from Stanford Dogs Dataset photos "
                              "(via the Dog CEO API), which are licensed for non-commercial research and education.",
    })
    fb.setupOS2(sTypoAscender=ASCENT, sTypoDescender=DESCENT, sTypoLineGap=0, usWinAscent=ASCENT, usWinDescent=-DESCENT,
                sxHeight=XH, sCapHeight=CAP, achVendID="NONE", fsType=0)
    fb.setupPost()
    stamp = timestampNow()
    fb.setupHead(unitsPerEm=UPM, created=stamp, modified=stamp)

    ttf = os.path.join(ROOT, "weedogs.ttf")
    fb.save(ttf)
    for flavor in ("woff", "woff2"):
        f = TTFont(ttf)
        f.flavor = flavor
        f.save(os.path.join(ROOT, f"weedogs.{flavor}"))

    b64 = {fl: base64.b64encode(open(os.path.join(ROOT, f"weedogs.{fl}"), "rb").read()).decode() for fl in ("woff2", "woff")}
    with open(os.path.join(ROOT, "weedogs.css"), "w", encoding="utf8") as fh:
        fh.write(
            "/* WeeDogs: dog silhouettes for unit charts. See README.md for the key and license. */\n"
            "@font-face {\n  font-family: 'WeeDogs';\n  font-weight: normal;\n  font-style: normal;\n"
            f"  src: url(data:font/woff2;base64,{b64['woff2']}) format('woff2'),\n"
            f"       url(data:font/woff;base64,{b64['woff']}) format('woff');\n}}\n\n"
            ".weedogs {\n  font-family: 'WeeDogs';\n}\n"
        )
    with open(os.path.join(ROOT, "weedogs.json"), "w", encoding="utf8") as fh:
        json.dump(key, fh, indent=1, ensure_ascii=False)

    # Preview sheet: every glyph with its character.
    cols, cell = 13, 110
    chars = list(spec)
    rows = (len(chars) + cols - 1) // cols
    img = Image.new("RGB", (cols * cell, rows * (cell + 20)), "white")
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(ttf, 96)
    label = ImageFont.load_default()
    for i, ch in enumerate(chars):
        x, y = (i % cols) * cell, (i // cols) * (cell + 20)
        d.text((x + cell / 2, y + 88), ch, font=font, fill="black", anchor="ms")
        d.text((x + cell / 2, y + cell + 6), ch, font=label, fill=(120, 120, 120), anchor="mm")
    img.save(os.path.join(ROOT, "weedogs_all.png"))
    print(f"built {len(spec)} glyphs:", " ".join(chars))


if __name__ == "__main__":
    main()
