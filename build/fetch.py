"""Download candidate photos from the Dog CEO API into LilPuppies/.cache/images/<breed>/.

Usage (from LilPuppies/): python -I build/fetch.py [photos_per_breed]
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
PER = int(sys.argv[1]) if len(sys.argv) > 1 else 24


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return r.read()


def main():
    index = {}
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
    with open(os.path.join(ROOT, ".cache", "index.json"), "w") as fh:
        json.dump(index, fh, indent=1)


if __name__ == "__main__":
    main()
