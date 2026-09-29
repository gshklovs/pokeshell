r"""evs/verify.py's checks for the Hidden Fates ids (evs/verify.py runs on import over evs's own list, so its
logic is repeated here, unchanged), plus the Shiny Vault rule.

Sprite (normal and shiny palette), against the vendor colorscripts sprite:
  - SHAPE exact: every vendor pixel is a full 2x2 block of sprite cells at the placed offset (flip allowed),
    and no other sprite cells anywhere
  - OUTLINE exact: every black vendor pixel is black
  - COLOURS exact:
      regular cards        normal = vendor regular colours, shiny roll = vendor shiny colours
      Shiny Vault (Rare Shiny / Rare Shiny GX): BOTH = the vendor SHINY colours (the card prints the shiny Pokemon)
      Rare Secret (gold)   a pure palette remap: every vendor colour maps to exactly one colour (evs verify)
Card data: a real sm115 / sma printing (cached API record), fields verbatim, tier == API rarity.
Commons: no background at all. Animation: 16 frames, final frame == the static art. Size <= 140 x 110 grid px.

  ..\..\..\.venv\Scripts\python hfverify.py [ids]
"""
import json
import sys

import hflib as P
from hflib import E, L
import hfcards
import sprites

RECOLOUR_OK = {"gold": {"Rare Secret"}}
MAX_W, MAX_H = 140, 110
fails = 0


def report(ok, msg):
    global fails
    fails += not ok
    print(("ok  " if ok else "BAD ") + msg)


def check(cid):
    c = hfcards.BUILDERS[cid]()
    art = json.load(open(E.ART / f"{cid}.json", encoding="utf-8"))
    v = art["variants"][c.meta["variant"]]
    rows = v["rows"]
    A, B = c.off
    name = c.spr.name
    mode = c.meta.get("sprite_recolour")
    vault = P.is_vault(cid)
    report(vault == bool(getattr(c.spr, "vault", False)),
           f"{cid:10s} Shiny Vault printing: {vault}, sprite is the shiny sprite: {getattr(c.spr, 'vault', False)}")
    if mode:
        report(c.meta["rarity"] in RECOLOUR_OK.get(mode, ()), f"{cid:10s} {mode} recolour allowed at '{c.meta['rarity']}'")
    for sh in (False, True):
        pal = {**art["palette"], **v.get("palette", {})}
        if sh:
            pal = {**pal, **art.get("shiny", {}), **v.get("shiny", {})}
        src = sprites.load(name, sh or vault)            # Shiny Vault: the shiny sprite on both rolls
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
        what = "pure gold palette remap" if mode == "gold" else (
            "exact vendor SHINY colours" if vault else "exact vendor colours")
        report(shape_ok and outline_bad == 0 and bad == 0,
               f"{cid:10s} {name:10s} {'shiny ' if sh else 'normal'} flip={flip!s:5s} {tot} px: shape "
               f"{'exact' if shape_ok else 'WRONG'}, {outline_bad} outline px off, {bad} colour errors ({what})")
    report(len(rows[0]) <= MAX_W and len(rows) <= MAX_H, f"{cid:10s} size {len(rows[0])}x{len(rows)} grid px "
                                                         f"(cap {MAX_W}x{MAX_H})")
    if c.meta["rarity"] == "Common":
        report(c.bg is None and all(ch == "." or ch in c.spr.pal for r in rows for ch in r),
               f"{cid:10s} Common: plain sprite, no background")
    api = json.load(open(E.CARDS / "api" / f"{cid}.json", encoding="utf-8"))
    card = json.load(open(E.CARDS / f"{cid}.json", encoding="utf-8"))
    diff = [k for k in card if k not in ("tier", "set", "images")
            and card[k] != api.get(k, card[k] if card[k] in ([], "") else None)]
    real = api["set"]["id"] in P.SETS and api["id"] == cid and card["tier"] == api["rarity"] == c.meta["rarity"]
    report(real and not diff, f"{cid:10s} card data: real {api['set']['id']} printing, API rarity '{api['rarity']}', "
                              f"tier '{card['tier']}', fields verbatim{'' if not diff else ' EXCEPT ' + str(diff)}")
    if c.meta.get("anim"):
        for sh in (False, True):
            nm = cid + ("_shiny" if sh else "")
            f = P.DATA / "anim" / nm / f"{nm}.json"
            if not f.exists():
                report(False, f"{nm}: animation missing (run hfanim.py)")
                continue
            m = json.load(open(f, encoding="utf-8"))
            last = m["frames"][m["final_frame"]]
            got = [[None if ch == "." else L.hexrgb(m["palette"][ch]) for ch in r] for r in last]
            report(got == c.rgb(sh) and len(m["frames"]) == 16,
                   f"{nm:15s} animation: {len(m['frames'])} frames, final frame == static art")


if __name__ == "__main__":
    for cid in [a for a in sys.argv[1:] if a in hfcards.BUILDERS] or hfcards.ORDER:
        check(cid)
    print(f"{fails} failures")
    sys.exit(1 if fails else 0)
