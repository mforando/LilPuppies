"""Download candidate photos into LilPuppies/.cache/images/.

    python -I build/fetch.py [photos_per_breed]   the letter breeds (breeds.py), from the Dog CEO API
    python -I build/fetch.py --breeds             every breed in breeds.json (catalog.py): Dog CEO and
                                                  Wikimedia Commons photos listed in breed-images.json
Both add to .cache/index.json, which build/segment.py reads.
"""
import json
import os
import random
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from breeds import ALL  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, ".cache", "images")
UA = {"User-Agent": "LilPuppies-font-build/1.0 (https://github.com/mforando/DogGenes)"}
PER = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 24
INDEX = os.path.join(ROOT, ".cache", "index.json")


def get(url, headers=UA, timeout=30):
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout) as r:
        return r.read()


def fetch_breeds():
    """Every breed in breeds.json: download its candidates and list them in the index as "study/<code>".

    Breeds that already have a letter (same Dog CEO folder as a glyphs.json pick) reuse that dog,
    so they need no candidates. Others get up to 12 Dog CEO photos plus their Wikimedia photos.
    """
    from catalog import load
    index = json.load(open(INDEX)) if os.path.exists(INDEX) else {}
    # Wikimedia rejects bare library user agents; this one says what the script is.
    wm = {"User-Agent": "LilPuppies-font-build/1.0 (open-source font build script; one-off download of ~50 images) "
                        "python-urllib/3.12"}
    letters = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "glyphs.json"), encoding="utf8"))
    letter_folders = {g["breed"].replace("/", "-") for g in letters.values()}
    for b in load():
        folders = {c["file"].split("/", 1)[0] for c in b["candidates"]}
        if folders & letter_folders:
            print(f"{b['code']} {b['name']}: uses its letter's dog")
            continue
        dogceo = [c for c in b["candidates"] if c["source"] == "Dog CEO"][:12]
        cands = dogceo + [c for c in b["candidates"] if c["source"] != "Dog CEO"]
        got = []
        for c in cands:
            f = os.path.join(CACHE, c["file"])
            if not os.path.exists(f):
                os.makedirs(os.path.dirname(f), exist_ok=True)
                try:
                    data = get(c["url"], wm if c["source"] != "Dog CEO" else UA, timeout=10)
                except Exception as e:  # noqa: BLE001
                    print("  skip", c["url"][:90], e)
                    continue
                with open(f, "wb") as fh:
                    fh.write(data)
                time.sleep(1.0 if c["source"] != "Dog CEO" else 0.05)
            got.append({"file": c["file"], "url": c["url"]})
        index[f"study/{b['code']}"] = got
        print(f"{b['code']} {b['name']}: {len(got)} of {len(cands)}", flush=True)
        with open(INDEX, "w") as fh:
            json.dump(index, fh, indent=1)


def main():
    if "--breeds" in sys.argv:
        return fetch_breeds()
    index = json.load(open(INDEX)) if os.path.exists(INDEX) else {}
    for path in ALL:
        try:
            urls = json.loads(get(f"https://dog.ceo/api/breed/{path}/images"))["message"]
        except Exception as e:  # noqa: BLE001
            print(f"{path}: SKIPPED ({e})")
            continue
        random.Random(path).shuffle(urls)  # a stable sample per breed
        d = os.path.join(CACHE, path.replace("/", "-"))
        os.makedirs(d, exist_ok=True)
        got = []
        for u in urls[:PER]:
            f = os.path.join(d, u.rsplit("/", 1)[1])
            if not os.path.exists(f):
                try:
                    data = get(u)
                except Exception as e:  # noqa: BLE001
                    print("  skip", u, e)
                    continue
                with open(f, "wb") as fh:
                    fh.write(data)
                time.sleep(0.05)
            got.append({"file": os.path.relpath(f, CACHE).replace("\\", "/"), "url": u})
        index[path] = got
        print(f"{path}: {len(got)} of {len(urls)}")
    with open(INDEX, "w") as fh:
        json.dump(index, fh, indent=1)


if __name__ == "__main__":
    main()
