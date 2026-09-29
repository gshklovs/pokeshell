r"""evs/verify.py's checks, for the 30th Celebration ids (evs/verify.py runs on import over evs's own list, so
its logic is repeated here, unchanged):

Sprite (normal and shiny), against the vendor colorscripts sprite:
  - SHAPE exact: every vendor pixel is a full 2x2 block of sprite cells at the placed offset (flip allowed),
    and no other sprite cells anywhere
  - OUTLINE exact: every black vendor pixel is black
  - COLOURS exact, except the Futuristic Rare's allowed tint: each pixel must equal p30cards.fr_colour() of the
    vendor colour (luminance-preserving blend <= FR_BLEND toward the card's tint; outline, near-black, white and
    the eye pinned exact)
Card data: a real me55 printing (cached API record), fields verbatim, tier == API rarity.
Commons: no background at all. Animation: 16 frames, final frame == the static art.

  ..\..\..\.venv\Scripts\python p30verify.py
"""
import json
import sys

import p30lib as P
from p30lib import E, L
import p30cards
import sprites

fails = 0


def report(ok, msg):
    global fails
    fails += not ok
    print(("ok  " if ok else "BAD ") + msg)


def check(cid):
    c = p30cards.BUILDERS[cid]()
    art = json.load(open(E.ART / f"{cid}.json", encoding="utf-8"))
    v = art["variants"][c.meta["variant"]]
    rows = v["rows"]
    A, B = c.off
    name = c.spr.name
    mode = c.meta.get("sprite_recolour")
    report(mode is None or (mode == "futuristic" and c.meta["rarity"] == "Futuristic Rare"),
           f"{cid:9s} sprite recolour '{mode or 'none'}' allowed at '{c.meta['rarity']}'")
    if mode:
        report(0 < p30cards.FR_BLEND <= 0.35, f"{cid:9s} futuristic tint: blend {p30cards.FR_BLEND} <= 0.35 "
                                              f"(cap 0.55), toward {c.meta['fr_tint']}")
    vend = P.Sprite(name)                      # vendor sprite, unflipped (verified exact against sprites.load)
    for sh in (False, True):
        pal = {**art["palette"], **v.get("palette", {})}
        if sh:
            pal = {**pal, **art["shiny"], **v.get("shiny", {})}
        src = sprites.load(name, sh)
        w, h = len(src[0]), len(src)
        flip = v["flip"]
        tot = split = outline_bad = bad = 0
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
                elif mode == "futuristic":        # the vendor colour, blended by the formula (pins exact)
                    exp = p30cards.fr_colour(vend, vend.rows[j][i], i, j, X, Y, 0.0, c.meta["fr_tint"], sh)
                    bad += got != L.hexrgb(exp)
                else:
                    bad += got != want
        spr_cells = {p for p, (Lr, k) in c.cells.items() if Lr == "sprite"}
        shape_ok = spr_cells == want_cells and split == 0
        report(shape_ok and outline_bad == 0 and bad == 0,
               f"{cid:9s} {name:8s} {'shiny ' if sh else 'normal'} flip={flip!s:5s} {tot} px: shape "
               f"{'exact' if shape_ok else 'WRONG'}, {outline_bad} outline px off, {bad} colour errors ({"futuristic tint formula" if mode else "exact vendor colours"})")
    if c.meta["rarity"] == "Common":
        report(c.bg is None and all(ch == "." or ch in c.spr.pal for r in rows for ch in r),
               f"{cid:9s} Common: plain sprite, no background")
    api = json.load(open(E.CARDS / "api" / f"{cid}.json", encoding="utf-8"))
    card = json.load(open(E.CARDS / f"{cid}.json", encoding="utf-8"))
    diff = [k for k in card if k not in ("tier", "set", "images")
            and card[k] != api.get(k, card[k] if card[k] in ([], "") else None)]
    real = api["set"]["id"] == "me55" and api["id"] == cid and card["tier"] == api["rarity"] == c.meta["rarity"]
    report(real and not diff, f"{cid:9s} card data: real me55 printing, API rarity '{api['rarity']}', tier '{card['tier']}', "
                              f"fields verbatim{'' if not diff else ' EXCEPT ' + str(diff)}")
    if c.meta.get("anim"):
        for sh in (False, True):
            nm = cid + ("_shiny" if sh else "")
            f = P.DATA / "anim" / nm / f"{nm}.json"
            if not f.exists():
                report(False, f"{nm}: animation missing (run p30anim.py)")
                continue
            m = json.load(open(f, encoding="utf-8"))
            last = m["frames"][m["final_frame"]]
            got = [[None if ch == "." else L.hexrgb(m["palette"][ch]) for ch in r] for r in last]
            report(got == c.rgb(sh) and len(m["frames"]) == 16,
                   f"{nm:15s} animation: {len(m['frames'])} frames, final frame == static art")


if __name__ == "__main__":
    for cid in [a for a in sys.argv[1:] if a in p30cards.BUILDERS] or p30cards.ORDER:
        check(cid)
    print(f"{fails} failures")
    sys.exit(1 if fails else 0)
