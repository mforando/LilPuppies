"""Write the demo page (index.html) and the key table in README.md from weedogs.json.

Usage (from weedogs/): python -I build/demo.py
"""
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
key = json.load(open(os.path.join(ROOT, "weedogs.json"), encoding="utf8"))
upper = [c for c in key if c.isupper()]
lower = [c for c in key if c.islower()]
e = html.escape


def cells(chars):
    return "\n".join(
        f'      <li><span class="weedogs g" aria-hidden="true">{c}</span><b>{c}</b><small>{e(key[c]["breed"])}</small></li>'
        for c in chars
    )


# A sample unit chart: 100 dogs, a quarter of them highlighted.
pack = "".join(sorted(key))
row = (pack * 4)[:100]
sample = f'<span class="hi">{row[:25]}</span>{row[25:]}'

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>WeeDogs</title>
<link rel="stylesheet" href="weedogs.css">
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
  .try {{ width: 100%; font: inherit; padding: 8px 10px; border: 1px solid var(--line); border-radius: 6px; background: transparent; color: var(--ink); }}
  .tryout {{ font-size: 48px; line-height: 1.1; min-height: 1.2em; overflow-wrap: anywhere; margin-top: 10px; }}
  footer {{ margin-top: 3em; border-top: 1px solid var(--line); padding-top: 1em; font-size: 13.5px; color: var(--ink-2); }}
</style>
</head>
<body>
<main>
  <h1>WeeDogs</h1>
  <p>A font of dog silhouettes for unit charts, in the spirit of ProPublica&rsquo;s
    <a href="https://github.com/propublica/weepeople">WeePeople</a>. Each of the {len(key)} letters is a different breed,
    traced from a photo in the <a href="https://dog.ceo/dog-api/">Dog CEO API</a>. Where a breed&rsquo;s name allows it,
    the letter is its initial: <b>B</b> is a basset hound.</p>
  <div class="hero weedogs" aria-label="A row of dog silhouettes">{e(pack[:12])}</div>

  <h2>In a chart</h2>
  <p>One dog per unit; color some of them. The letters cycle through every breed.</p>
  <div class="chart weedogs" role="img" aria-label="100 dog silhouettes, 25 of them highlighted">{sample}</div>

  <h2>Try it</h2>
  <input class="try" id="try" value="Woof" aria-label="Type letters to see their dogs">
  <div class="tryout weedogs" id="out" aria-hidden="true">Woof</div>

  <h2>Uppercase</h2>
  <ul class="grid">
{cells(upper)}
  </ul>
  <h2>Lowercase</h2>
  <ul class="grid">
{cells(lower)}
  </ul>

  <h2>Use it</h2>
  <pre>&lt;link rel="stylesheet" href="weedogs.css"&gt;
&lt;span class="weedogs"&gt;BbDdGg&lt;/span&gt;</pre>
  <p>The CSS embeds the font, so it is the only file you need. Or load <code>weedogs.woff2</code> /
    <code>weedogs.woff</code> / <code>weedogs.ttf</code> with your own <code>@font-face</code>. Space is a gap the width of a
    dog. Only A&ndash;Z and a&ndash;z have dogs, the same characters as WeePeople.</p>

  <footer>
    Silhouettes traced from photos in the Stanford Dogs Dataset (Khosla et al. 2011, from ImageNet), served by the
    Dog CEO API; licensed for non-commercial research and education, so WeeDogs is for non-commercial use too. The
    source photo for every letter is listed in <code>weedogs.json</code> and README.md. WeeDogs is not affiliated with
    ProPublica and uses none of WeePeople&rsquo;s shapes.
  </footer>
</main>
<script>
  const t = document.getElementById("try"), o = document.getElementById("out");
  t.addEventListener("input", () => {{ o.textContent = t.value; }});
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
readme_path = os.path.join(ROOT, "README.md")
readme = open(readme_path, encoding="utf8").read()
# Between the markers, whether empty or filled by an earlier run.
readme = re.sub(r"<!-- KEY -->.*?<!-- /KEY -->", lambda m: "<!-- KEY -->\n" + "\n".join(rows) + "\n<!-- /KEY -->", readme, flags=re.S)
with open(readme_path, "w", encoding="utf8") as fh:
    fh.write(readme)
print("wrote index.html and README key:", len(rows) - 2, "rows")
