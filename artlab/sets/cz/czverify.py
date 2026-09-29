r"""evs/verify.py's checks for the Crown Zenith ids (evs/verify.py runs on import over evs's own list, so its logic
is repeated here, unchanged in substance):

Sprite (normal and shiny), against the vendor colorscripts sprite:
  - SHAPE exact: every vendor pixel is a full 2x2 block of sprite cells at the placed offset (flip allowed),
    and no other sprite cells anywhere
  - OUTLINE exact: every black vendor pixel is black
  - COLOURS exact, except the gold remap at Rare Secret (a pure palette remap: one vendor colour -> one colour)
Card data: a real swsh12pt5 / swsh12pt5gg printing (cached API record), fields verbatim, tier == API rarity.
Commons: no background at all, flipped exactly when set.json flip_commons lists them.
Size: <= 140 x 110 grid px. Animation (foil tiers): 16 frames, final frame == the static art.

  ..\..\..\.venv\Scripts\python czverify.py [ids]
"""
import json
import sys

import czlib as P
from czlib import E, L
import czcards
import sprites

RECOLOUR_OK = {"gold": {"Rare Secret"}}
fails = 0


def report(ok, msg):
    global fails
    fails += not ok
    print(("ok  " if ok else "BAD ") + msg)


def check(cid):
    c = czcards.BUILDERS[cid]()
    art = json.load(open(E.ART / f"{cid}.json", encoding="utf-8"))
    v = art["variants"][c.meta["variant"]]
    rows = v["rows"]
    A, B = c.off
    name = c.spr.name
    mode = c.meta.get("sprite_recolour")
    if mode:
        report(c.meta["rarity"] in RECOLOUR_OK.get(mode, ()), f"{cid:17s} {mode} recolour allowed at '{c.meta['rarity']}'")
    for sh in (False, True):
        pal = {**art["palette"], **v.get("palette", {})}
        if sh:
            pal = {**pal, **art.get("shiny", {}), **v.get("shiny", {})}
        src = sprites.load(name, sh)
        w, h = len(src[0]), len(src)
        flip = v["flip"]
        tot = split = outline_bad = bad = 0
        remap = {}
        want_cells = set()
        for j in range(h):
            for i in range(w):
                want = src[j][i]
                if want is None:
                    continue
                tot += 1
                ci = w - 1 - i if flip else i
                X, Y = 2 * (A + ci), 2 * (B + j)
                block = {rows[Y + b][X + a] for a in (0, 1) for b in (0, 1)}
                want_cells |= {(X + a, Y + b) for a in (0, 1) for b in (0, 1)}
                if len(block) != 1:
                    split += 1
                    continue
                got = L.hexrgb(pal[block.pop()])
                if want == (0, 0, 0):
                    outline_bad += got != (0, 0, 0)
                elif mode == "gold":
                    remap.setdefault(want, set()).add(got)
                else:
                    bad += got != want
        if mode == "gold":
            bad = sum(len(s) > 1 for s in remap.values())
        spr_cells = {p for p, (Lr, k) in c.cells.items() if Lr == "sprite"}
        shape_ok = spr_cells == want_cells and split == 0
        report(shape_ok and outline_bad == 0 and bad == 0,
               f"{cid:17s} {name:12s} {'shiny ' if sh else 'normal'} flip={flip!s:5s} {tot} px: shape "
               f"{'exact' if shape_ok else 'WRONG'}, {outline_bad} outline px off, {bad} colour errors "
               f"({'pure gold palette remap' if mode == 'gold' else 'exact vendor colours'})")
    if c.meta["rarity"] == "Common":
        want_flip = cid in P.META.get("flip_commons", [])
        report(c.bg is None and all(ch == "." or ch in c.spr.pal for r in rows for ch in r) and c.spr.flip == want_flip,
               f"{cid:17s} Common: plain sprite, no background, flip={c.spr.flip} (flip_commons: {want_flip})")
    report(c.FW <= 140 and c.FH <= 110, f"{cid:17s} size {c.FW} x {c.FH} grid px (cap 140 x 110)")
    api = json.load(open(E.CARDS / "api" / f"{cid}.json", encoding="utf-8"))
    card = json.load(open(E.CARDS / f"{cid}.json", encoding="utf-8"))
    diff = [k for k in card if k not in ("tier", "set", "images")
            and card[k] != api.get(k, card[k] if card[k] in ([], "") else None)]
    real = api["set"]["id"] in P.SETS and api["id"] == cid and card["tier"] == api["rarity"] == c.meta["rarity"]
    report(real and not diff, f"{cid:17s} card data: real {api['set']['id']} printing, API rarity '{api['rarity']}', "
                              f"tier '{card['tier']}', fields verbatim{'' if not diff else ' EXCEPT ' + str(diff)}")
    if c.meta.get("anim"):
        for sh in (False, True):
            nm = cid + ("_shiny" if sh else "")
            f = P.DATA / "anim" / nm / f"{nm}.json"
            if not f.exists():
                report(False, f"{nm}: animation missing (run czanim.build)")
                continue
            m = json.load(open(f, encoding="utf-8"))
            last = m["frames"][m["final_frame"]]
            got = [[None if ch == "." else L.hexrgb(m["palette"][ch]) for ch in r] for r in last]
            report(got == c.rgb(sh) and len(m["frames"]) == 16,
                   f"{nm:20s} animation: {len(m['frames'])} frames, final frame == static art")


if __name__ == "__main__":
    for cid in [a for a in sys.argv[1:] if a in czcards.BUILDERS] or czcards.ORDER:
        check(cid)
    print(f"{fails} failures")
    sys.exit(1 if fails else 0)
