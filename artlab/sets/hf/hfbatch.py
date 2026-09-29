r"""The Hidden Fates group-batch runner (shared: batch agents import it, never edit it). A group module
(batch_<group>.py) defines its per-card table, mask recipes and builder, then calls run():

    import hfbatch as HB
    HB.run(GROUP, builders={cid: fn}, masks={cid: fn}, argv=sys.argv[1:])

  ..\..\..\.venv\Scripts\python batch_<group>.py masks [ids]    masks/<id>.png + work/masks-<group>.png (LOOK at it)
  ..\..\..\.venv\Scripts\python batch_<group>.py build [ids]    art/, out/ (static; quick iteration)
  ..\..\..\.venv\Scripts\python batch_<group>.py all [ids]      build + anim + verify + sheets/<group>.png
  ..\..\..\.venv\Scripts\python batch_<group>.py sheet [ids]    sheets/<group>.png from the current out/

Sizes go to sheets/<group>-sizes.json (never the ladder's sizes.json). layout_window / layout_full give the default
crop for a card from its sprite (docs/ART_METHOD.md section 8: sized to the art, within 140 x 110 grid px).
"""
import json

import numpy as np

import hflib as P
from hflib import E
import hfcards
import hfmasks as HM

PLAN = json.loads((P.HERE / "plan.json").read_text(encoding="utf-8"))
MAXW = 52                                   # sprite px (~104 cols): wider sprites get sprite w + 2 (cap 70)


def plan(group):
    return {e["id"]: e for e in PLAN[group]}


def layout_window(cid, spr, win=HM.SM_WIN, maxw=MAXW, pad=1):
    """(x0, y0, S, W, H) in a regular art window: the largest scale that fits the sprite (+pad all round), a crop
    of the window centred on the real Pokemon when the card would be wider than maxw"""
    a, b, c, d = win
    ww, wh = c - a, d - b
    S = min(wh / (spr.h + 2 * pad), ww / (spr.w + 2 * pad))
    W = min(int(ww / S), max(maxw, spr.w + 2 * pad))
    H = int(wh / S)
    ys, xs = np.nonzero(E.mask(cid))
    cx = (xs.min() + xs.max()) / 2
    x0 = float(np.clip(cx - W * S / 2, a, c - W * S))
    return round(x0, 1), b, round(S, 2), W, H


def layout_full(cid, spr, top=92, text_y=560, left=20, right=714, maxw=MAXW, pad=2):
    """(x0, y0, S, W, H) for a full art (GX / Shiny GX / gold): y from `top` to the card text `text_y`, the scale
    that fits the sprite (+pad), centred on the real Pokemon when wider than maxw"""
    wh, ww = text_y - top, right - left
    H = spr.h + 2 * pad
    S = wh / H
    W = min(int(ww / S), max(maxw, spr.w + 2 * pad))
    if W < spr.w + 2 * pad:                   # a very wide sprite: fit the width instead
        W = spr.w + 2 * pad
        S = ww / W
        H = int(wh / S)
    ys, xs = np.nonzero(E.mask(cid))
    cx = (xs.min() + xs.max()) / 2
    x0 = float(np.clip(cx - W * S / 2, left, right - W * S))
    return round(x0, 1), top, round(S, 2), W, H


def run(group, builders, masks=None, argv=()):
    import hfbuild
    import hfanim
    import hfverify
    import hfsheet
    argv = list(argv)
    verb = argv[0] if argv and argv[0] in ("masks", "build", "all", "sheet", "anim", "verify") else "all"
    ids = [a for a in argv if a in builders] or list(builders)
    hfcards.BUILDERS.update(builders)
    if verb == "masks":
        HM.make(ids, masks, E.WORK / f"masks-{group}.png")
        return
    f = P.DATA / "sheets" / f"{group}-sizes.json"
    f.parent.mkdir(exist_ok=True)
    sizes = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    if verb in ("build", "all"):
        for cid in ids:
            _, sizes[cid] = hfbuild.render(cid)
        f.write_text(json.dumps({k: sizes[k] for k in builders if k in sizes}, indent=1), encoding="utf-8")
    if verb in ("anim", "all"):
        hfanim.build(ids)
    if verb in ("verify", "all"):
        for cid in ids:
            hfverify.check(cid)
        print(f"{hfverify.fails} failures")
        assert hfverify.fails == 0, f"{hfverify.fails} verification failures"
    if verb in ("sheet", "all"):
        done = [c for c in builders if c in sizes]
        hfsheet.sheet(done, P.DATA / "sheets" / f"{group}.png", sizes)
