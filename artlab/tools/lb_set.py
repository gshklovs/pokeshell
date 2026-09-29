r"""Lookbook sections for a set's build groups: ONE combined image per card, real card | ours | ours + text half
(docs/ART_METHOD.md, "Review"). The user always judges side by side against the real card.

  .venv\Scripts\python artlab\tools\lb_set.py <set folder> <group> [<group> ...] --lookbook <dir>
  .venv\Scripts\python artlab\tools\lb_set.py p30 rare --ids me55-12,me55-14 --lookbook <dir>   (only these cards)

<dir> is the lookbook page's folder (index.html + img/; start one from artlab/lookbook/template.html). Also
$ARTLAB_LOOKBOOK. Per card it writes img/<folder>/<id>.jpg (from <DATA>/<folder>/ref/<prefix>_<n>.png and
out/<id>-art.png, out/<id>-card.png) and replaces or inserts the group's `grid` section in index.html's SECTIONS
(id <section_prefix><group>, placed before/after the set.json lookbook "anchor" section when there is one, else at
the top). A group may also be a label from set.json "labels" that isn't in plan.json (e.g. evs "altart") when --ids
is given. files-last.json lists the images written, for the Artifact publish (`files`: at most 255 per publish,
512 per version: prune old sections' images first).
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import artpaths  # noqa: E402

H = 460
SEC = re.compile(r'\n  \{\n    id: "\w+"')


def num_key(c):
    return (re.sub(r"\d", "", c["number"]), int(re.sub(r"\D", "", c["number"]) or 0))


def combo(d, prefix, cid, n):
    ims = [Image.open(d / "ref" / f"{prefix}_{n}.png").convert("RGB"),
           Image.open(d / "out" / f"{cid}-art.png").convert("RGB"), Image.open(d / "out" / f"{cid}-card.png").convert("RGB")]
    ims = [im.resize((max(1, round(im.width * H / im.height)), H), Image.LANCZOS if i == 0 else Image.NEAREST)
           for i, im in enumerate(ims)]
    c = Image.new("RGB", (sum(i.width for i in ims) + 40, H), (20, 21, 27))
    x = 0
    for im in ims:
        c.paste(im, (x, 0))
        x += im.width + 20
    return c


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder")
    ap.add_argument("groups", nargs="+")
    ap.add_argument("--lookbook", default=os.environ.get("ARTLAB_LOOKBOOK"))
    ap.add_argument("--ids", default="")
    a = ap.parse_args()
    if not a.lookbook:
        ap.error("--lookbook <dir> (or $ARTLAB_LOOKBOOK): the folder holding the lookbook's index.html")
    lb = Path(a.lookbook)
    meta = json.loads((artpaths.code(a.folder) / "set.json").read_text(encoding="utf-8"))
    plan = json.loads((artpaths.code(a.folder) / "plan.json").read_text(encoding="utf-8"))
    d = artpaths.data(a.folder)
    look = meta.get("lookbook", {})
    labels = meta.get("labels", {})
    only = {i for i in a.ids.split(",") if i}
    out = lb / "img" / a.folder
    out.mkdir(parents=True, exist_ok=True)
    html = lb / "index.html"
    s = html.read_text(encoding="utf-8")
    files = {}
    for g in a.groups:
        entries = plan.get(g) or []
        if only:
            every = {c["id"]: c for v in plan.values() if isinstance(v, list) for c in v if isinstance(c, dict)}
            entries = [every[i] if i in every else {"id": i, "name": json.loads((d / "cards" / f"{i}.json").read_text(
                encoding="utf-8"))["name"], "number": i.split("-", 1)[1]} for i in sorted(only)]
        rows = []
        for c in sorted(entries, key=num_key):
            cid, n = c["id"], c["number"]
            if not ((d / "out" / f"{cid}-art.png").exists() and (d / "ref" / f"{meta['prefix']}_{n}.png").exists()):
                print("missing", cid)
                continue
            name = f"{cid}.jpg"
            combo(d, meta["prefix"], cid, n).save(out / name, quality=84)
            files[f"img/{a.folder}/{name}"] = f"img/{a.folder}/{name}"
            rows.append(f'        ["{c["name"]}<br>{n}/{meta["printed_total"]}", ["{name}", "real card | ours | ours + text half"]],')
        label = labels.get(g, g)
        sid = f"{look.get('section_prefix', a.folder + '_')}{g}"
        sec = f'''  {{
    id: "{sid}", eyebrow: "{meta["name"]} · {label}", title: "{label}: {len(rows)} cards",
    blurb: "Each row: the real card, ours, and ours with its text half.",
    grid: {{
      dir: "img/{a.folder}/",
      cols: ["Real card | ours | ours + text half"],
      rows: [
{chr(10).join(rows)}
      ],
    }},
    questions: [
      {{ id: "{sid}_ok", q: "This group", opts: [
        ["ok", "Looks right", "", true],
        ["fix", "Fix some", "Name the cards in the notes."],
      ]}},
    ],
  }},
'''
        m = re.search(r'  \{\n    id: "' + sid + r'"', s)
        if m:                                           # replace the group's old section
            e = SEC.search(s, m.start() + 5)
            s = s[:m.start()] + s[e.start() + 1:] if e else s[:m.start()] + s[s.index("];", m.start()):]
        anchor = look.get("anchor")
        am = re.search(r'  \{\n    id: "' + anchor + r'"', s) if anchor else None
        if am and look.get("place") == "after":
            e = SEC.search(s, am.start() + 5)
            at = e.start() + 1 if e else s.index("];", am.start())
        elif am:
            at = am.start()
        else:
            at = s.index("const SECTIONS = [\n") + len("const SECTIONS = [\n")
        s = s[:at] + sec + s[at:]
        print(g, len(rows), "rows")
    html.write_text(s, encoding="utf-8")
    (lb / "files-last.json").write_text(json.dumps(files), encoding="utf-8")


if __name__ == "__main__":
    main()
