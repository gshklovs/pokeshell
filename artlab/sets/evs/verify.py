r"""Checks for every card in the batch.

Sprite (normal and shiny), against the vendor colorscripts sprite:
  - SHAPE exact: every vendor pixel is a full 2x2 block of sprite cells at the placed offset (flip allowed),
    and there are no other sprite cells anywhere
  - OUTLINE exact: every black vendor pixel is black
  - COLOURS exact, with two exceptions that only the high rarities may use:
      gold    (Rare Secret): a pure palette remap -- every vendor colour maps to exactly one colour
      rainbow (Rare Rainbow): each pixel must equal evcards.rainbow_px(vendor colour, body hue at that pixel),
              i.e. the vendor colour blended RAINBOW_BLEND (0.55, <= 0.7) toward its same-luminance rainbow tint; pinned colours (outline, darkest strokes, white,
              the eye) stay exact
Card data: a real swsh7 printing (cached API response), fields verbatim, tier == API rarity (or "Reverse Holo"
for a common / uncommon / rare's reverse print).
Animation: 16 frames, final frame == the static art.

  ..\..\..\.venv\Scripts\python verify.py
"""
import json
import sys

import evcards
import evlib as E
from evlib import L
import sprites

RECOLOUR_OK = {"gold": {"Rare Secret"}, "rainbow": {"Rare Rainbow"}}
assert 0 < evcards.RAINBOW_BLEND <= 0.7, "rainbow blend must let the base colours through (<= 70%)"
fails = 0


def report(ok, msg):
    global fails
    fails += not ok
    print(("ok  " if ok else "BAD ") + msg)


for cid in evcards.ORDER:
    c = evcards.BUILDERS[cid]()
    art = json.load(open(E.ART / f"{cid}.json", encoding="utf-8"))
    var = c.meta["variant"]
    v = art["variants"][var]
    rows = v["rows"]
    A, B = c.off
    name = c.spr.name
    mode = c.meta.get("sprite_recolour")
    if mode:
        report(c.meta["rarity"] in RECOLOUR_OK[mode], f"{cid:10s} {mode} recolour allowed at '{c.meta['rarity']}'")
    for sh in (False, True):
        pal = {**art["palette"], **v.get("palette", {})}
        if sh:
            pal = {**pal, **art["shiny"], **v.get("shiny", {})}
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
                ci = w - 1 - i if flip else i             # column in the placed (possibly flipped) sprite
                X, Y = 2 * (A + ci), 2 * (B + j)
                block = {rows[Y + b][X + a] for a in (0, 1) for b in (0, 1)}
                for a in (0, 1):
                    for b in (0, 1):
                        want_cells.add((X + a, Y + b))
                if len(block) != 1:
                    split += 1
                    continue
                got = L.hexrgb(pal[block.pop()])
                if want == (0, 0, 0):
                    outline_bad += got != (0, 0, 0)
                    continue
                if mode == "gold":
                    remap.setdefault(want, set()).add(got)
                elif mode == "rainbow":
                    hue = evcards.rainbow_hue(ci, j, w, h)
                    exp = L.hexrgb(evcards.rainbow_px(L.rgbhex(want), hue, i=i, j=j, name=name))
                    bad += got != exp
                else:
                    bad += got != want
        if mode == "gold":
            bad = sum(len(s) > 1 for s in remap.values())
        spr_cells = {p for p, (Lr, k) in c.cells.items() if Lr == "sprite"}
        shape_ok = spr_cells == want_cells and split == 0
        ok = shape_ok and outline_bad == 0 and bad == 0
        what = {"gold": "pure gold palette remap", "rainbow": "declared rainbow re-tint",
                None: "exact vendor colours"}[mode]
        report(ok, f"{cid:10s} {name:9s} {'shiny ' if sh else 'normal'} flip={flip!s:5s} {tot} px: shape "
                   f"{'exact' if shape_ok else 'WRONG'}, {outline_bad} outline px off, {bad} colour errors ({what})")
    api = json.load(open(E.CARDS / "api" / f"{cid}.json", encoding="utf-8"))
    card = json.load(open(E.CARDS / f"{cid}.json", encoding="utf-8"))
    # fields the API omits when empty (Dragon types have no weakness, a free retreat has no cost, ...)
    # were written as [] / "" by fetch_cards.py; anything else must match verbatim
    diff = [k for k in card if k not in ("tier", "set", "images")
            and card[k] != api.get(k, card[k] if card[k] in ([], "") else None)]
    tier_ok = card["tier"] == api["rarity"] or (card["tier"] == "Reverse Holo" and api["rarity"] in ("Common", "Uncommon", "Rare"))
    real = api["set"]["id"] == "swsh7" and api["id"] == cid and tier_ok and card["tier"] == c.meta["rarity"]
    report(real and not diff, f"{cid:10s} card data: real swsh7 printing, API rarity '{api['rarity']}', tier '{card['tier']}', "
                              f"fields verbatim{'' if not diff else ' EXCEPT ' + str(diff)}")
    if c.meta.get("anim"):
        for sh in (False, True):
            nm = cid + ("_shiny" if sh else "")
            f = E.DATA / "anim" / nm / f"{nm}.json"
            if not f.exists():
                report(False, f"{nm}: animation missing (run anim.py)")
                continue
            m = json.load(open(f, encoding="utf-8"))
            last = m["frames"][m["final_frame"]]
            got = [[None if ch == "." else L.hexrgb(m["palette"][ch]) for ch in r] for r in last]
            report(got == c.rgb(sh) and len(m["frames"]) == 16,
                   f"{nm:16s} animation: {len(m['frames'])} frames, final frame == static art")
sys.exit(1 if fails else 0)
