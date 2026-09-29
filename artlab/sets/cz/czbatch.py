r"""The shared pipeline every Crown Zenith group module runs (masks -> build -> anim -> verify -> sheet), so a
batch_<group>.py only holds its per-card table:

    import czbatch
    GROUP = "holo"
    TABLE = {"swsh12pt5-21": dict(kind="holo", sprite="entei", flip=False, mask=dict(...), ...), ...}
    if __name__ == "__main__":
        czbatch.main(GROUP, TABLE)

  ..\..\..\.venv\Scripts\python batch_<group>.py masks [ids]     masks/<id>.png + work/<group>_masks.png
  ..\..\..\.venv\Scripts\python batch_<group>.py rembg [ids]     work/<group>_rembg.png (3 models side by side)
  ..\..\..\.venv\Scripts\python batch_<group>.py quick [ids]     art + text renders only (iteration), work/<group>_pairs.png
  ..\..\..\.venv\Scripts\python batch_<group>.py all [ids]       masks + build + anim + verify + sheets/<group>.png
  ..\..\..\.venv\Scripts\python batch_<group>.py build|anim|verify|sheet [ids]

The rows are registered into czcards.CFG / BUILDERS in memory only (czcards.register); czcards.py is never
edited. Sizes go to sheets/<group>-sizes.json (never the ladder's sizes.json).
"""
import json
import sys

from PIL import Image, ImageDraw

import czlib as P
from czlib import E
import czcards as C
import czmasks as CM


def pairs(ids, path, H=380):
    """quick look: real card | our art, two per row"""
    tiles = []
    for cid in ids:
        r = Image.open(P.ref_path(cid)).convert("RGB")
        r = r.resize((round(r.width * H / r.height), H))
        a = Image.open(E.OUT / f"{cid}-art.png").convert("RGB")
        k = min(H / a.height, 560 / a.width)
        a = a.resize((round(a.width * k), round(a.height * k)))
        t = Image.new("RGB", (r.width + a.width + 30, H + 20), (25, 25, 30))
        t.paste(r, (0, 20))
        t.paste(a, (r.width + 10, 20))
        ImageDraw.Draw(t).text((4, 2), cid, fill=(255, 255, 0))
        tiles.append(t)
    per = 2
    W = max(t.width for t in tiles) * per
    o = Image.new("RGB", (W, (H + 20) * ((len(tiles) + per - 1) // per)), (15, 15, 15))
    for i, t in enumerate(tiles):
        o.paste(t, ((i % per) * (W // per), (i // per) * (H + 20)))
    o.save(path)
    print(path)


def main(group, table, argv=None):
    import czbuild
    import czanim
    import czverify
    import czsheet
    argv = sys.argv[1:] if argv is None else argv
    step = argv[0] if argv else "all"
    ids = [a for a in argv[1:] if a in table] or list(table)
    C.register(table)
    E.WORK.mkdir(exist_ok=True)
    if step == "rembg":
        import subprocess
        subprocess.run([sys.executable, str(P.HERE / "rembg_all.py"), str(E.WORK / f"{group}_rembg.png"), *ids],
                       check=True)
        return
    if step in ("masks", "all"):
        items = [(cid, CM.make(cid, table[cid]["mask"])) for cid in ids if table[cid].get("mask")]
        if items:
            CM.sheet(items, E.WORK / f"{group}_masks.png")
    f = P.DATA / "sheets" / f"{group}-sizes.json"
    f.parent.mkdir(exist_ok=True)
    sizes = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    if step in ("build", "all", "quick"):
        for cid in ids:
            _, sizes[cid] = czbuild.render(cid)
        f.write_text(json.dumps({k: sizes[k] for k in table if k in sizes}, indent=1), encoding="utf-8")
    if step == "quick":
        pairs(ids, E.WORK / f"{group}_pairs.png")
        return
    if step in ("anim", "all"):
        czanim.build(ids)
    rc = 0
    if step in ("verify", "all"):
        for cid in ids:
            czverify.check(cid)
        print(f"{czverify.fails} failures")
        rc = 1 if czverify.fails else 0
    if step in ("sheet", "all"):
        done = [c for c in table if c in sizes]
        czsheet.sheet(done, P.DATA / "sheets" / f"{group}.png", sizes, title=f"Crown Zenith, group {group}")
    if rc:
        sys.exit(rc)
