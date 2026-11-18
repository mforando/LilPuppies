"""Write the demo page (index.html) and the key tables in README.md from lilpuppies.json and
lilpuppies_breeds.json.

Usage (from LilPuppies/): python -I build/demo.py
"""
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
key = json.load(open(os.path.join(ROOT, "lilpuppies.json"), encoding="utf8"))
bkey = json.load(open(os.path.join(ROOT, "lilpuppies_breeds.json"), encoding="utf8"))
upper = [c for c in key if c.isupper()]
lower = [c for c in key if c.islower()]
e = html.escape


def cells(chars):
    return "\n".join(
        f'      <li><span class="lilpuppies g" aria-hidden="true">{c}</span><b>{c}</b><small>{e(key[c]["breed"])}</small></li>'
        for c in chars
    )


def clade_name(c):
    """"AsianSpitz" -> "Asian Spitz", "UKRural" -> "UK Rural"; breeds without a clade go last."""
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", c) if c else "No clade assigned"


# Every breed, grouped by clade in breeds.json order.
clades = {}
for code, b in bkey.items():
    clades.setdefault(b["clade"], []).append(code)
clade_order = [c for c in clades if c] + ([None] if None in clades else [])
breed_sections = "\n".join(
    f'  <h3>{e(clade_name(c))} <span class="count">{len(clades[c])}</span></h3>\n  <ul class="grid">\n'
    + "\n".join(
        f'      <li><span class="lilpuppies g" aria-hidden="true">{bkey[code]["char"]}</span><b>{code}</b>'
        f'<small>{e(bkey[code]["name"])}</small></li>'
        for code in clades[c]
    )
    + "\n  </ul>"
    for c in clade_order
)
husky_cp = bkey["HUSK"]["codepoint"][2:]


# A sample unit chart: 100 dogs, a quarter of them highlighted.
pack = "".join(sorted(key))
row = (pack * 4)[:100]
sample = f'<span class="hi">{row[:25]}</span>{row[25:]}'

# Example-chart data: AKC group (Kelpie, which the AKC doesn't register, is listed as Herding), and typical adult
# weight (kg) and lifespan (years), midpoints of commonly cited ranges. Approximate; for demonstrating the font.
FACTS = {
    "A": ("Hound", 25, 13), "B": ("Hound", 27, 12), "C": ("Toy", 2, 16), "D": ("Hound", 10, 14),
    "E": ("Non-Sporting", 11, 14), "F": ("Non-Sporting", 11, 11), "G": ("Working", 63, 8.5), "H": ("Working", 23, 13),
    "I": ("Hound", 60, 7.5), "J": ("Toy", 3.5, 11), "K": ("Herding", 17, 12.5), "L": ("Working", 55, 8),
    "M": ("Working", 36, 11), "N": ("Working", 60, 9), "O": ("Hound", 47, 11), "P": ("Toy", 4, 15),
    "Q": ("Hound", 10, 13), "R": ("Hound", 35, 11), "S": ("Hound", 23, 13), "T": ("Working", 60, 11),
    "U": ("Herding", 18, 13.5), "V": ("Sporting", 23, 13), "W": ("Sporting", 32, 12), "X": ("Non-Sporting", 14, 14),
    "Y": ("Toy", 3, 13.5), "Z": ("Hound", 41, 9), "a": ("Working", 45, 11), "b": ("Working", 30, 11),
    "c": ("Sporting", 12, 13.5), "d": ("Working", 38, 11), "e": ("Sporting", 22, 13), "f": ("Terrier", 8, 13.5),
    "g": ("Herding", 32, 11), "h": ("Hound", 45, 11), "i": ("Hound", 22, 13), "j": ("Terrier", 6, 13),
    "k": ("Working", 45, 11), "l": ("Non-Sporting", 6, 13.5), "m": ("Toy", 4.5, 13.5), "n": ("Hound", 22, 13.5),
    "o": ("Herding", 34, 11), "p": ("Non-Sporting", 25, 13.5), "q": ("Hound", 38, 10.5), "r": ("Hound", 29, 13.5),
    "s": ("Terrier", 9, 12), "t": ("Toy", 3.5, 13), "u": ("Working", 25, 13), "v": ("Herding", 12, 13.5),
    "w": ("Hound", 13, 13.5), "x": ("Hound", 10, 14), "y": ("Terrier", 25, 11.5), "z": ("Working", 70, 9),
}
assert set(FACTS) == set(key), "every letter needs chart facts"
breeds = [{"c": c, "breed": key[c]["breed"], "group": FACTS[c][0], "kg": FACTS[c][1], "yrs": FACTS[c][2]}
          for c in upper + lower]
breeds_json = json.dumps(breeds, separators=(",", ":"), ensure_ascii=False)
charts_js = open(os.path.join(ROOT, "build", "charts.js"), encoding="utf8").read()

# Unit bar chart: one bar per AKC group, one dog per breed, each drawn with its own letter.
by_group = {}
for b in breeds:
    by_group.setdefault(b["group"], []).append(b)
groups = sorted(by_group.items(), key=lambda kv: (-len(kv[1]), kv[0]))
bar_label = "Bar chart of the 52 breeds by AKC group: " + ", ".join(f"{g} {len(bs)}" for g, bs in groups)
bar_rows = "\n".join(
    f'    <div class="ubar"><div class="ulab">{e(g)} <span>{len(bs)}</span></div><div class="umarks lilpuppies">'
    + "".join(f'<span data-tip="{e(b["breed"])}">{b["c"]}</span>' for b in bs)
    + "</div></div>"
    for g, bs in groups
)
table_rows = "\n".join(
    f'      <tr><td><span class="lilpuppies" aria-hidden="true">{b["c"]}</span> {b["c"]}</td><td>{e(b["breed"])}</td>'
    f'<td>{e(b["group"])}</td><td>{b["kg"]:g}</td><td>{b["yrs"]:g}</td></tr>'
    for b in sorted(breeds, key=lambda b: b["breed"])
)

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LilPuppies</title>
<link rel="stylesheet" href="lilpuppies.css">
<style>
  :root {{ --bg: #faf8f4; --ink: #1d1b18; --ink-2: #5d5850; --line: #e3ded4; --accent: #b4552d; }}
  @media (prefers-color-scheme: dark) {{ :root {{ --bg: #17161a; --ink: #eeebe5; --ink-2: #a39d93; --line: #34313a; --accent: #e08a5f; }} }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: var(--bg); color: var(--ink); font: 16px/1.55 system-ui, -apple-system, "Segoe UI", sans-serif; }}
  main {{ max-width: 1040px; margin: 0 auto; padding: 48px 16px 64px; }}
  h1 {{ font-size: 2.6rem; line-height: 1.1; margin: 0 0 .2em; letter-spacing: -.01em; }}
  h2 {{ font-size: 1.15rem; margin: 2.4em 0 .6em; }}
  p {{ max-width: 44rem; color: var(--ink-2); }}
  a {{ color: var(--accent); }}
  code, pre {{ font: 13.5px/1.5 ui-monospace, SFMono-Regular, Consolas, monospace; }}
  pre {{ background: color-mix(in srgb, var(--ink) 6%, transparent); padding: 12px 14px; border-radius: 6px; overflow-x: auto; }}
  .hero {{ font-size: 64px; line-height: 1; margin: 18px 0 8px; overflow-wrap: anywhere; }}
  .chart {{ font-size: 34px; line-height: 1.05; max-width: 34em; overflow-wrap: anywhere; color: color-mix(in srgb, var(--ink) 35%, transparent); }}
  .chart .hi {{ color: var(--accent); }}
  .grid {{ list-style: none; padding: 0; margin: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(112px, 1fr)); border-top: 1px solid var(--line); border-left: 1px solid var(--line); }}
  .grid li {{ border-right: 1px solid var(--line); border-bottom: 1px solid var(--line); padding: 10px 8px 9px; display: flex; flex-direction: column; align-items: center; text-align: center; }}
  .grid .g {{ font-size: 64px; line-height: 1; height: 60px; }}
  .grid b {{ font: 600 13px ui-monospace, SFMono-Regular, Consolas, monospace; margin-top: 6px; }}
  .grid small {{ color: var(--ink-2); font-size: 11.5px; line-height: 1.3; }}
  h3 .count {{ color: var(--ink-2); font-weight: 400; font-variant-numeric: tabular-nums; margin-left: .2em; }}
  main > h3 {{ font-size: 1rem; margin: 1.8em 0 .6em; }}
  .sub {{ font-size: 14.5px; margin: 1.2em 0 .5em; }}
  .try {{ width: 100%; font: inherit; padding: 8px 10px; border: 1px solid var(--line); border-radius: 6px; background: transparent; color: var(--ink); }}
  .tryout {{ font-size: 48px; line-height: 1.1; min-height: 1.2em; overflow-wrap: anywhere; margin-top: 10px; }}
  .credit {{ font-size: 14px; color: var(--ink-2); margin-top: -0.4em; }}
  .viz {{ --s1: #2a78d6; --s2: #eb6834; --s3: #1baf7a; --other: color-mix(in srgb, var(--ink) 28%, transparent); }}
  @media (prefers-color-scheme: dark) {{ .viz {{ --s1: #3987e5; --s2: #d95926; --s3: #199e70; }} }}
  .viz h3 {{ font-size: 1rem; margin: 2.2em 0 .2em; }}
  .viz .sub {{ margin: 0 0 .8em; font-size: 14.5px; }}
  .ubar {{ display: grid; grid-template-columns: 9em 1fr; align-items: end; gap: 10px; padding: 3px 0; }}
  .ulab {{ font-size: 14px; text-align: right; padding-bottom: 5px; }}
  .ulab span {{ color: var(--ink-2); font-variant-numeric: tabular-nums; margin-left: .25em; }}
  .umarks {{ font-size: min(34px, 5.4vw); line-height: 1; border-left: 1px solid var(--line); padding-left: 4px; }}
  .umarks span {{ cursor: default; }}
  .umarks span:hover {{ color: var(--accent); }}
  @media (max-width: 560px) {{ .ubar {{ grid-template-columns: 1fr; gap: 0; }} .ulab {{ text-align: left; padding: 6px 0 0; }} .umarks {{ font-size: 5.6vw; }} }}
  .vbtns {{ display: flex; gap: 6px; flex-wrap: wrap; margin: 0 0 10px; }}
  .vbtns button {{ font: inherit; font-size: 14px; padding: 5px 12px; border-radius: 999px; border: 1px solid var(--line); background: transparent; color: var(--ink); cursor: pointer; }}
  .vbtns button[aria-pressed="true"] {{ background: var(--ink); color: var(--bg); border-color: var(--ink); }}
  .legend {{ display: flex; flex-wrap: wrap; gap: 4px 16px; font-size: 14px; margin: 0 0 6px; padding: 0; list-style: none; }}
  .legend li {{ display: flex; align-items: center; gap: 6px; }}
  .legend .lilpuppies {{ font-size: 22px; line-height: 1; }}
  .viz svg {{ display: block; width: 100%; height: auto; overflow: visible; }}
  .viz svg text.dog {{ font-family: 'LilPuppies'; paint-order: stroke; stroke: var(--bg); stroke-width: 2px; stroke-linejoin: round; cursor: default; }}
  .viz svg .axis text {{ fill: var(--ink-2); font-size: 13px; }}
  .viz svg .axis line, .viz svg .axis path {{ stroke: var(--line); }}
  .viz svg .grid line {{ stroke: var(--line); stroke-dasharray: 2 3; }}
  .viz svg .note {{ fill: var(--ink-2); font-size: 12.5px; }}
  .viz svg .clabel {{ fill: var(--ink); font-size: 14px; font-weight: 600; }}
  .viz svg .clabel tspan {{ fill: var(--ink-2); font-weight: 400; }}
  .viz details {{ margin-top: 10px; font-size: 14px; }}
  .viz details > div, .viz table {{ display: block; overflow-x: auto; }}
  .viz table {{ border-collapse: collapse; margin-top: 8px; font-size: 13.5px; }}
  .viz th, .viz td {{ text-align: left; padding: 3px 14px 3px 0; border-bottom: 1px solid var(--line); white-space: nowrap; }}
  .viz td:nth-child(n+4), .viz th:nth-child(n+4) {{ text-align: right; font-variant-numeric: tabular-nums; }}
  .viz td .lilpuppies {{ font-size: 20px; }}
  .tip {{ position: fixed; left: 0; top: 0; pointer-events: none; z-index: 10; background: var(--ink); color: var(--bg); font-size: 13px; line-height: 1.35; padding: 5px 8px; border-radius: 5px; opacity: 0; transition: opacity .1s; max-width: 240px; }}
  footer {{ margin-top: 3em; border-top: 1px solid var(--line); padding-top: 1em; font-size: 13.5px; color: var(--ink-2); }}
</style>
</head>
<body>
<main>
  <h1>LilPuppies</h1>
  <p class="credit">Inspired by ProPublica&rsquo;s <a href="https://github.com/propublica/weepeople">WeePeople</a> font
    (<a href="https://github.com/propublica/weepeople">github.com/propublica/weepeople</a>).</p>
  <p>A font of dog silhouettes for unit charts, following WeePeople&rsquo;s idea of one figure per letter. Each of the {len(key)} letters is a different breed,
    traced from a photo in the <a href="https://dog.ceo/dog-api/">Dog CEO API</a>. Where a breed&rsquo;s name allows it,
    the letter is its initial: <b>B</b> is a basset hound.</p>
  <div class="hero lilpuppies" aria-label="A row of dog silhouettes">{e(pack[:12])}</div>

  <h2>In a chart</h2>
  <p>One dog per unit; color some of them. The letters cycle through every breed.</p>
  <div class="chart lilpuppies" role="img" aria-label="100 dog silhouettes, 25 of them highlighted">{sample}</div>

  <h2>Try it</h2>
  <input class="try" id="try" value="Woof" aria-label="Type letters to see their dogs">
  <div class="tryout lilpuppies" id="out" aria-hidden="true">Woof</div>
  <p class="sub">Or type breed codes, such as <code>HUSK</code> for a Siberian Husky. Every code is listed under
    <a href="#every-breed">Every breed</a>.</p>
  <input class="try" id="try2" value="HUSK BSJI AKIT DACH" aria-label="Type breed codes to see their dogs">
  <div class="tryout lilpuppies-codes" id="out2" aria-hidden="true">HUSK BSJI AKIT DACH</div>

  <h2>Uppercase</h2>
  <ul class="grid">
{cells(upper)}
  </ul>
  <h2>Lowercase</h2>
  <ul class="grid">
{cells(lower)}
  </ul>

  <h2 id="every-breed">Every breed</h2>
  <p>Beyond the 52 letters, the font has all {len(bkey)} breeds of the genetics study in <code>breeds.json</code>,
    grouped here by clade. Each one has a code, which draws the dog in the <code>lilpuppies-codes</code> class, and
    its own character in Unicode&rsquo;s Private Use Area, listed in <code>lilpuppies_breeds.json</code>. A breed that
    also has a letter draws the same dog.</p>
{breed_sections}

  <h2>Use it</h2>
  <pre>&lt;link rel="stylesheet" href="lilpuppies.css"&gt;
&lt;span class="lilpuppies"&gt;BbDdGg&lt;/span&gt;
&lt;span class="lilpuppies-codes"&gt;HUSK BSJI AKIT&lt;/span&gt;</pre>
  <p>The CSS embeds the font, so it is the only file you need. Or load <code>lilpuppies.woff2</code> /
    <code>lilpuppies.woff</code> / <code>lilpuppies.ttf</code> with your own <code>@font-face</code>. Space is a gap the width of a
    dog. In the <code>lilpuppies</code> class, A&ndash;Z and a&ndash;z are the dogs, the same characters as WeePeople.
    The <code>lilpuppies-codes</code> class turns on discretionary ligatures
    (<code>font-variant-ligatures: discretionary-ligatures</code>), so breed codes become dogs. In code you can also
    write a breed&rsquo;s character directly, such as <code>"\\u{husky_cp}"</code> for the Siberian Husky.</p>

  <section class="viz" aria-labelledby="viz-h">
  <h2 id="viz-h">Example charts</h2>
  <p>Every mark below is a LilPuppies character, sized and colored like any other text. The breed groups, weights
    and lifespans are approximate typical values, used here only to show the font.</p>

  <h3>Unit bar chart</h3>
  <p class="sub">The {len(breeds)} breeds in the font by AKC group. Each breed is drawn with its own letter.</p>
  <div class="ubars" role="img" aria-label="{e(bar_label)}">
{bar_rows}
  </div>

  <h3>100 dogs in a force layout</h3>
  <p class="sub">An imaginary shelter&rsquo;s 100 dogs, first as one pack and then split by outcome.</p>
  <div class="vbtns" role="group" aria-label="Layout">
    <button type="button" aria-pressed="true" data-mode="pack">One pack</button>
    <button type="button" aria-pressed="false" data-mode="split">By outcome</button>
  </div>
  <ul class="legend" id="force-legend"></ul>
  <svg id="force" viewBox="0 0 960 400" role="img" aria-label="100 dog silhouettes: 58 adopted, 27 in foster care, 15 waiting"></svg>

  <h3>Scatter plot</h3>
  <p class="sub">Typical adult weight and lifespan for each breed. Three AKC groups are colored and the rest are gray.
    Dogs that would overlap are nudged apart.</p>
  <ul class="legend" id="scatter-legend"></ul>
  <svg id="scatter" viewBox="0 0 960 540" role="img" aria-label="Scatter plot of weight against lifespan for {len(breeds)} breeds: bigger breeds tend to live shorter lives"></svg>
  <details>
    <summary>Show the data as a table</summary>
    <table>
      <thead><tr><th>Letter</th><th>Breed</th><th>AKC group</th><th>Weight (kg)</th><th>Lifespan (yrs)</th></tr></thead>
      <tbody>
{table_rows}
      </tbody>
    </table>
  </details>
  </section>
  <div class="tip" id="tip" role="tooltip"></div>

  <footer>
    Silhouettes traced from photos in the Stanford Dogs Dataset (Khosla et al. 2011, from ImageNet), served by the
    Dog CEO API; licensed for non-commercial research and education, so LilPuppies is for non-commercial use too.
    Breeds that Dog CEO lacks are traced from Wikimedia Commons photos, credited with their authors and licenses in
    README.md and <code>lilpuppies_breeds.json</code>. The source photo for every letter is listed in
    <code>lilpuppies.json</code> and README.md. LilPuppies is not affiliated with
    ProPublica and uses none of WeePeople&rsquo;s shapes. Inspired by
    <a href="https://github.com/propublica/weepeople">WeePeople</a>.
  </footer>
</main>
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"></script>
<script>
const BREEDS = {breeds_json};
{charts_js}</script>
<script>
  const t = document.getElementById("try"), o = document.getElementById("out");
  t.addEventListener("input", () => {{ o.textContent = t.value; }});
  const t2 = document.getElementById("try2"), o2 = document.getElementById("out2");
  t2.addEventListener("input", () => {{ o2.textContent = t2.value.toUpperCase(); }});
</script>
</body>
</html>
"""
with open(os.path.join(ROOT, "index.html"), "w", encoding="utf8") as fh:
    fh.write(page)

# README key table, between the KEY markers.
rows = ["| Letter | Breed | Source photo |", "|---|---|---|"]
for c in upper + lower:
    u = key[c]["photo"]
    rows.append(f"| `{c}` | {key[c]['breed']} | [{u.rsplit('/', 1)[1]}]({u}) |")

# README breed table, between the BREEDS markers: every breed, with credit for Wikimedia photos.
brows = ["| Code | Character | Breed | Clade | Source photo |", "|---|---|---|---|---|"]
for code, b in bkey.items():
    if b.get("sameDogAs"):
        src = f"same dog as `{b['sameDogAs']}`"
    elif b.get("letter"):
        src = f"same dog as letter `{b['letter']}`"
    elif b["source"] == "Wikimedia Commons":
        lic = f"[{b['license']}]({b['licenseUrl']})" if b.get("licenseUrl") else (b.get("license") or "see page")
        src = f"[Wikimedia Commons]({b['page']}), {b.get('author') or 'unknown author'}, {lic}"
    else:
        src = f"[{b['photo'].rsplit('/', 1)[1]}]({b['photo']})"
    src = src.replace("|", "\\|").replace("\n", " ")
    brows.append(f"| `{code}` | {b['codepoint']} | {b['name']} | {clade_name(b['clade']) if b['clade'] else ''} | {src} |")

readme_path = os.path.join(ROOT, "README.md")
readme = open(readme_path, encoding="utf8").read()
# Between the markers, whether empty or filled by an earlier run.
for tag, lines in (("KEY", rows), ("BREEDS", brows)):
    readme = re.sub(rf"<!-- {tag} -->.*?<!-- /{tag} -->", lambda m, t=tag, ls=lines: f"<!-- {t} -->\n" + "\n".join(ls) + f"\n<!-- /{t} -->",
                    readme, flags=re.S)
with open(readme_path, "w", encoding="utf8") as fh:
    fh.write(readme)
print("wrote index.html and README keys:", len(rows) - 2, "letters,", len(brows) - 2, "breeds")
