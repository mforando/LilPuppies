"""Cut each candidate dog out of its photo and score how well it would work as a silhouette.

Uses torchvision's Mask R-CNN (COCO weights; class 18 is "dog"). A good glyph source is one
dog, whole (not cut off by the frame), not overlapped by a person, seen from the side and
standing, so its legs show as separate shapes at the bottom of the outline.

Writes .cache/masks/<breed>/<photo>.png (the dog's mask, cropped to the dog) and
.cache/segments.json (one record per photo, with its score). Usage (from LilPuppies/):
    python -I build/segment.py
"""
import json
import os

import cv2
import numpy as np
import torch
from PIL import Image
from torchvision.models.detection import MaskRCNN_ResNet50_FPN_V2_Weights, maskrcnn_resnet50_fpn_v2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, ".cache")
DOG, PERSON = 18, 1


def largest_component(m):
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8), connectivity=8)
    if n <= 1:
        return m
    k = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    return lab == k


def fill_small_holes(m, frac=0.02):
    """Fill enclosed background pockets smaller than `frac` of the dog (leash loops, speckle)."""
    inv = (~m).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(inv, connectivity=4)
    out = m.copy()
    h, w = m.shape
    for k in range(1, n):
        x, y, bw, bh, area = stats[k]
        touches = x == 0 or y == 0 or x + bw == w or y + bh == h
        if not touches and area < frac * m.sum():
            out[lab == k] = True
    return out


def leg_score(m):
    """Share of rows in the bottom quarter of the dog that cross two or more separate runs."""
    ys, xs = np.nonzero(m)
    top, bot = ys.min(), ys.max()
    rows = range(int(bot - 0.25 * (bot - top)), bot + 1)
    multi = 0
    for y in rows:
        r = m[y].astype(np.int8)
        runs = int(((r[1:] - r[:-1]) == 1).sum() + r[0])
        multi += runs >= 2
    return multi / max(1, len(rows))


def main():
    index = json.load(open(os.path.join(CACHE, "index.json")))
    weights = MaskRCNN_ResNet50_FPN_V2_Weights.DEFAULT
    model = maskrcnn_resnet50_fpn_v2(weights=weights, box_score_thresh=0.3)
    model.transform.min_size, model.transform.max_size = (480,), 800
    model.eval()
    torch.set_num_threads(max(1, (os.cpu_count() or 2) - 1))
    tf = weights.transforms()

    out_path = os.path.join(CACHE, "segments.json")
    done = json.load(open(out_path)) if os.path.exists(out_path) else {}
    for breed, photos in index.items():
        for p in photos:
            key = p["file"]
            if key in done:
                continue
            rec = {"breed": breed, "file": key, "url": p["url"], "ok": False}
            done[key] = rec
            try:
                img = Image.open(os.path.join(CACHE, "images", key)).convert("RGB")
            except Exception as e:  # noqa: BLE001
                rec["why"] = f"unreadable: {e}"
                continue
            with torch.no_grad():
                o = model([tf(img)])[0]
            labels, scores = o["labels"].numpy(), o["scores"].numpy()
            masks = o["masks"][:, 0].numpy()
            dogs = [i for i in range(len(labels)) if labels[i] == DOG and scores[i] >= 0.5]
            if not dogs:
                rec["why"] = "no dog"
                continue
            # A photo that fails one of the checks below still keeps its mask (ok stays False, "why" says
            # what failed), as a fallback for breeds with only one or two photos.
            why = "several dogs" if len(dogs) > 1 else None
            i = max(dogs, key=lambda k: scores[k])
            prob = masks[i]
            m = prob > 0.5
            if m.sum() < 500:
                rec["why"] = "tiny"
                continue
            m = fill_small_holes(largest_component(m))
            h, w = m.shape
            ys, xs = np.nonzero(m)
            x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
            if not why and (x0 <= 2 or y0 <= 2 or x1 >= w - 3 or y1 >= h - 3):
                why = "cut off by the frame"
            people = [j for j in range(len(labels)) if labels[j] == PERSON and scores[j] >= 0.5]
            overlap = 0.0
            for j in people:
                pm = masks[j] > 0.5
                overlap = max(overlap, float((pm[y0:y1 + 1, x0:x1 + 1]).sum()) / float(m.sum()))
            if not why and overlap > 0.04:
                why = "person in the way"
            aspect = (x1 - x0 + 1) / (y1 - y0 + 1)
            sharp = float(np.abs(prob[m] - 0.5).mean() * 2)  # 1 = crisp edges, 0 = unsure
            legs = leg_score(m)
            solidity = float(m.sum()) / float(cv2.contourArea(cv2.convexHull(np.column_stack([xs, ys]).astype(np.int32))) or 1)
            side = 1.0 if 1.15 <= aspect <= 2.1 else 0.55
            score = float(scores[i]) * (0.5 + 0.5 * sharp) * (0.25 + legs) * side * (0.6 + 0.4 * min(1.0, solidity / 0.7))
            crop = (m[y0:y1 + 1, x0:x1 + 1] * 255).astype(np.uint8)
            mp = os.path.join(CACHE, "masks", key.rsplit(".", 1)[0] + ".png")
            os.makedirs(os.path.dirname(mp), exist_ok=True)
            Image.fromarray(crop).save(mp)
            if why:
                rec["why"] = why
            rec.update(ok=not why, score=round(score, 4), det=round(float(scores[i]), 3), aspect=round(float(aspect), 2),
                       legs=round(legs, 2), sharp=round(sharp, 2), solidity=round(solidity, 2), box=[int(x0), int(y0), int(x1), int(y1)],
                       size=[w, h], mask=os.path.relpath(mp, CACHE).replace("\\", "/"))
        json.dump(done, open(out_path, "w"), indent=0)
        ok = sum(1 for r in done.values() if r["breed"] == breed and r["ok"])
        print(f"{breed}: {ok} usable", flush=True)
    json.dump(done, open(out_path, "w"), indent=0)


if __name__ == "__main__":
    main()
