#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Bforartists Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
BFA - Build the shared Bforartists icon library (Server 2.0, issue #6935).

Bforartists-only tool: it publishes the UI icons so the websites
(www.bforartists.com, trinumedia.com) can link to them directly instead of
hand-uploading copies into each site.

    python tools/utils/bforartists_icons_publish.py --out build_icons

writes:

    build_icons/icons/<name>.svg   every icon from release/datafiles/icons_svg,
                                   with Inkscape editor metadata removed
    build_icons/icons/index.json   machine-readable list of all icons
    build_icons/icons/index.html   searchable gallery with copy-link buttons

The GitHub Action `.github/workflows/icons.yml` runs this on every icon change
on master and uploads the result to https://assets.bforartists.com/icons/.
Only the standard library is used, so it runs anywhere Python 3.9+ runs.
"""

import argparse
import datetime
import html
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ICONS_SRC = REPO_ROOT / "release" / "datafiles" / "icons_svg"
BASE_URL = "https://assets.bforartists.com/icons"

# ---------------------------------------------------------------------------
# SVG clean-up
#
# Only editor data is removed (Inkscape/Sodipodi elements and attributes, RDF
# metadata, comments). Shapes, styles, ids, viewBox and size stay untouched, so
# the icons look exactly as in Bforartists.
# ---------------------------------------------------------------------------

RE_XML_DECL = re.compile(r"<\?xml[^>]*\?>\s*")
RE_COMMENT = re.compile(r"<!--.*?-->\s*", re.S)
RE_METADATA = re.compile(r"<metadata\b.*?</metadata>\s*|<metadata\b[^>]*/>\s*", re.S)
RE_EDITOR_ELEMENT = re.compile(
    r"<(sodipodi|inkscape):(\w[\w-]*)\b[^>]*?/>\s*"         # self-closing
    r"|<(sodipodi|inkscape):(\w[\w-]*)\b.*?</\3:\4>\s*",    # with children
    re.S)
RE_EDITOR_ATTR = re.compile(r"\s+(?:sodipodi|inkscape):[\w-]+=\"[^\"]*\"")
RE_UNUSED_NS = re.compile(r"\s+xmlns:(?:sodipodi|inkscape|rdf|cc|dc)=\"[^\"]*\"")
RE_EMPTY_DEFS = re.compile(r"<defs\b[^>]*/>\s*|<defs\b[^>]*>\s*</defs>\s*")
RE_BETWEEN_TAGS = re.compile(r">\s+<")


def clean_svg(text):
    text = RE_XML_DECL.sub("", text)
    text = RE_COMMENT.sub("", text)
    text = RE_METADATA.sub("", text)
    text = RE_EDITOR_ELEMENT.sub("", text)
    text = RE_EDITOR_ATTR.sub("", text)
    text = RE_UNUSED_NS.sub("", text)
    text = RE_EMPTY_DEFS.sub("", text)
    text = RE_BETWEEN_TAGS.sub("><", text)
    text = re.sub(r"\s*\n\s*", " ", text).strip()
    if not text.startswith("<svg") or "</svg>" not in text:
        raise ValueError("not a plain SVG after clean-up")
    return text + "\n"


# ---------------------------------------------------------------------------
# Gallery page (same look as downloads.bforartists.com)
# ---------------------------------------------------------------------------

PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bforartists Icons</title>
<link rel="icon" type="image/svg+xml" href="{base}/blender.svg">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Titillium+Web:wght@600&display=swap" rel="stylesheet">
<style>
:root{{--bg:#1f1f1f;--panel:#2a2a2a;--panel-2:#333;--line:#464646;--text:#ececec;--muted:#a3a3a3;
--blue:#394c66;--blue-hi:#5680c2;--blue-light:#a0cff7;--orange:#ff9b32}}
*{{box-sizing:border-box}}html{{color-scheme:dark}}
body{{margin:0;background:var(--bg);color:var(--text);font:16px/1.5 Inter,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}}
main{{max-width:1200px;margin:0 auto;padding:40px 16px 64px}}
.eyebrow{{color:var(--blue-light);font-size:12px;letter-spacing:2px;text-transform:uppercase;margin:0 0 6px}}
h1,h2{{font-family:"Titillium Web",Verdana,sans-serif;font-weight:600;line-height:1.1}}
h1{{font-size:40px;margin:0 0 8px}}h2{{font-size:22px;margin:32px 0 10px}}
.lead{{color:var(--muted);margin:0 0 20px}}
.banner{{background:var(--blue);border:1px solid var(--blue-hi);border-radius:.4em;padding:12px 16px;margin:0 0 20px}}
code,pre{{font:13px/1.5 ui-monospace,Consolas,monospace}}
pre{{background:var(--panel);border:1px solid var(--line);border-radius:.4em;padding:10px 12px;overflow:auto;margin:6px 0 14px}}
.tools{{position:sticky;top:0;background:var(--bg);padding:10px 0;z-index:1;display:flex;gap:10px;align-items:center}}
input{{flex:1;padding:11px 12px;border-radius:.4em;border:1px solid var(--line);background:var(--panel);color:var(--text);font:inherit}}
input:focus{{outline:2px solid var(--blue-hi);border-color:var(--blue-hi)}}
#count{{color:var(--muted);font-size:14px;white-space:nowrap}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(112px,1fr));gap:8px}}
button.icon{{background:var(--panel);border:1px solid var(--line);border-radius:.4em;padding:12px 6px 8px;color:var(--text);cursor:pointer;font:12px/1.3 Inter,sans-serif;text-align:center}}
button.icon:hover{{background:var(--panel-2);border-color:var(--blue-hi)}}
button.icon img{{width:32px;height:32px;display:block;margin:0 auto 8px}}
button.icon span{{display:block;overflow-wrap:anywhere;color:var(--muted)}}
button.icon.copied{{border-color:var(--orange)}}button.icon.copied span{{color:var(--orange)}}
footer{{margin-top:48px;padding-top:16px;border-top:1px solid var(--line);color:var(--muted);font-size:13px}}
a{{color:var(--blue-light)}}
</style></head><body><main>
<p class="eyebrow">Shared library</p><h1>Bforartists Icons</h1>
<p class="lead">All {count} interface icons of Bforartists, always in sync with the latest code.</p>
<div class="banner">🖱️ Click an icon to copy its link. Links never change, so websites can use them directly.</div>
<h2>How to use</h2>
<pre>&lt;img src="{base}/particles.svg" alt="" width="20" height="20"&gt;</pre>
<p class="lead">Single-colour tint (CSS mask, keeps the shape and paints it in any colour):</p>
<pre>.bfa-icon{{width:20px;height:20px;background:currentColor;
  -webkit-mask:var(--icon) center/contain no-repeat;mask:var(--icon) center/contain no-repeat}}
&lt;span class="bfa-icon" style="--icon:url({base}/particles.svg)"&gt;&lt;/span&gt;</pre>
<div class="tools"><input id="q" placeholder="Search icons, e.g. mesh, view, modifier" autocomplete="off"><span id="count"></span></div>
<div class="grid" id="grid">
{items}
</div>
<footer>Updated {stamp} from <a href="https://github.com/Bforartists/Bforartists/tree/master/release/datafiles/icons_svg">release/datafiles/icons_svg</a> ·
<a href="{base}/index.json">index.json</a> · <a href="https://github.com/Bforartists/Bforartists">Bforartists on GitHub</a></footer>
</main><script>
const q=document.getElementById('q'),items=[...document.querySelectorAll('#grid button')],count=document.getElementById('count');
function filter(){{const t=q.value.trim().toLowerCase();let n=0;items.forEach(b=>{{const hit=!t||b.dataset.n.includes(t);b.hidden=!hit;if(hit)n++}});count.textContent=n+' icons'}}
q.addEventListener('input',filter);filter();
document.getElementById('grid').addEventListener('click',e=>{{const b=e.target.closest('button');if(!b)return;
const url='{base}/'+b.dataset.n+'.svg';const done=()=>{{b.classList.add('copied');const s=b.querySelector('span'),o=s.textContent;s.textContent='Link copied';
setTimeout(()=>{{b.classList.remove('copied');s.textContent=o}},1200)}};
navigator.clipboard?navigator.clipboard.writeText(url).then(done,()=>prompt('Icon link:',url)):prompt('Icon link:',url)}});
</script></body></html>
"""


def gallery(names):
    items = "\n".join(
        f'<button class="icon" data-n="{html.escape(n)}" title="{html.escape(n)}.svg">'
        f'<img src="{BASE_URL}/{html.escape(n)}.svg" alt="" loading="lazy" width="32" height="32">'
        f'<span>{html.escape(n)}</span></button>' for n in names)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return PAGE.format(base=BASE_URL, count=len(names), items=items, stamp=stamp)


# ---------------------------------------------------------------------------

def build(src, out):
    dest = out / "icons"
    dest.mkdir(parents=True, exist_ok=True)
    entries, before, after, failed = [], 0, 0, []
    for f in sorted(src.glob("*.svg"), key=lambda p: p.name.lower()):
        raw = f.read_text(encoding="utf-8")
        try:
            svg = clean_svg(raw)
        except ValueError as e:
            failed.append(f"{f.name}: {e}")
            svg = raw  # publish untouched rather than drop it
        (dest / f.name).write_text(svg, encoding="utf-8")
        before += len(raw.encode())
        after += len(svg.encode())
        entries.append({"name": f.stem, "url": f"{BASE_URL}/{f.name}", "bytes": len(svg.encode())})

    (dest / "index.json").write_text(json.dumps({
        "generated": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "source": "https://github.com/Bforartists/Bforartists/tree/master/release/datafiles/icons_svg",
        "count": len(entries),
        "icons": entries,
    }, indent=1) + "\n", encoding="utf-8")
    (dest / "index.html").write_text(gallery([e["name"] for e in entries]), encoding="utf-8")

    print(f"  ✓ {len(entries)} icons → {dest}")
    print(f"  ✓ size {before / 1e6:.1f} MB → {after / 1e6:.1f} MB")
    for msg in failed:
        print(f"  ! kept as-is: {msg}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", type=Path, default=ICONS_SRC, help="Folder with the icon SVGs")
    ap.add_argument("--out", type=Path, required=True, help="Output folder (icons/ is created inside)")
    args = ap.parse_args(argv)
    if not args.src.is_dir():
        sys.exit(f"Icon folder not found: {args.src}")
    return build(args.src, args.out)


if __name__ == "__main__":
    sys.exit(main())
