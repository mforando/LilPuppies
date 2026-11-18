"""The full breed list: every breed in breeds.json, with its candidate photos from breed-images.json.

Each breed is identified by its 4-letter study code (some codes are 3 letters, like LAB and PUG).
In the font, each one gets a character in Unicode's Private Use Area and a ligature: with
discretionary ligatures on, typing the code draws the dog.

Candidate photos come from the Dog CEO API (the Stanford Dogs Dataset) and from Wikimedia
Commons, whose author and license are kept so the README can credit them. A breed with no photo
of its own (the "COO" populations of Tibetan Mastiff, Saluki and Cane Corso) borrows the
silhouette of its twin; see ALIASES.
"""
import hashlib
import json
import os
import random
import re
from urllib.parse import unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUA = 0xE000          # the first breed's character; the rest follow in breeds.json order
PER_BREED = 24        # Dog CEO photos to sample per breed (a stable sample)

# Breeds with no photo of their own, drawn with another breed's silhouette.
ALIASES = {"CHTM": "TIBM", "COOS": "SALU", "ITCC": "CANE"}


def _wm_file(url):
    """A short, safe local file name for a Wikimedia thumbnail URL."""
    name = unquote(url.split("?", 1)[0].rsplit("/", 1)[1])
    name = re.sub(r"^\d+px-", "", name)
    stem, ext = os.path.splitext(name)
    stem = re.sub(r"[^A-Za-z0-9_-]+", "_", stem)[:60].strip("_")
    if not stem:  # e.g. a name entirely in another script
        stem = "photo_" + hashlib.sha1(url.encode()).hexdigest()[:10]
    return f"{stem}{ext.lower() or '.jpg'}"


def load():
    """Return the breeds in breeds.json order, each with code, name, clade, char and candidates."""
    study = json.load(open(os.path.join(ROOT, "breeds.json"), encoding="utf8"))["breeds"]
    images = json.load(open(os.path.join(ROOT, "breed-images.json"), encoding="utf8"))["breeds"]
    records = {}
    for r in images.values():
        if r.get("studyCode"):
            records.setdefault(r["studyCode"], []).append(r)

    out = []
    for i, b in enumerate(study):
        code = b["code"]
        cands, seen = [], set()

        def add(c):
            if c["file"] not in seen:
                seen.add(c["file"])
                cands.append(c)

        for r in records.get(code, []):
            for img in r.get("images") or []:
                url = img.get("url")
                if not url:
                    continue
                if "images.dog.ceo/breeds/" in url:
                    add({"file": url.split("/breeds/", 1)[1], "url": url, "source": "Dog CEO"})
                elif "wikimedia.org" in url:
                    add({"file": f"wikimedia/{code}/{_wm_file(url)}", "url": url, "source": "Wikimedia Commons",
                         "page": img.get("page"), "author": img.get("author"), "license": img.get("license"),
                         "licenseUrl": img.get("licenseUrl")})
            for folder in r.get("dogCeoAllPhotos") or []:
                files = sorted(folder["files"])
                random.Random(code + folder["baseUrl"]).shuffle(files)
                base = folder["baseUrl"]
                sub = base.split("/breeds/", 1)[1]
                for f in files[:PER_BREED]:
                    add({"file": sub + f, "url": base + f, "source": "Dog CEO"})
        out.append({"code": code, "name": re.sub(r"\s+-\s+USA$", "", b["name"]), "fullName": b["name"],
                    "clade": b.get("clade"), "char": chr(PUA + i), "alias": ALIASES.get(code), "candidates": cands})
    return out


def pool(breed, segs):
    """Every segmented photo for a breed: its candidates, plus any other photo from its Dog CEO
    folders that segment.py has already processed (an earlier fetch may have sampled others)."""
    files = [c["file"] for c in breed["candidates"]]
    folders = {f.split("/", 1)[0] + "/" for f in files if not f.startswith("wikimedia/")}
    seen = set(files)
    files += sorted(f for f in segs if f not in seen and any(f.startswith(p) for p in folders))
    return [segs[f] for f in files if f in segs and segs[f].get("mask")]


if __name__ == "__main__":
    breeds = load()
    none = [b["code"] for b in breeds if not b["candidates"] and not b["alias"]]
    print(len(breeds), "breeds;", sum(len(b["candidates"]) for b in breeds), "candidate photos; no photo:", none)
