"""Check that every tier's sprite pixels in <poke>-suite3.json are the vendor colorscripts sprite, pixel for
pixel (normal and shiny), allowing only the flip, the gold palette remap, and cells hidden by an overlay.

Grid rows are at half-block resolution: one sprite pixel = a 2x2 block of grid cells, which must all
carry the same key. Gold tiers must be a pure palette remap: every vendor colour maps to exactly one
gold colour (so the sprite's structure is untouched)."""
import json
import sys

from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))
import s3lib as L  # noqa: E402
import sprites
import tiers

fails = 0
for p, T in tiers.TIERS.items():
    art = json.load(open(L.HERE / f"{p}-suite3.json", encoding="utf-8"))
    for t, fn in T.items():
        c = fn()
        A, B = c.off
        v = art["variants"][t]
        rows = v["rows"]
        gold = t == "gold"
        for sh in (False, True):
            pal = {**art["palette"], **v.get("palette", {})}
            if sh:
                pal = {**pal, **art["shiny"], **v.get("shiny", {})}
            src = sprites.load(p, sh)
            w, h = len(src[0]), len(src)
            flip = c.spr.flip
            tot = hidden = bad = split = 0
            remap = {}
            for j in range(h):
                for i in range(w):
                    want = src[j][w - 1 - i] if flip else src[j][i]
                    if want is None:
                        continue
                    tot += 1
                    X, Y = 2 * (A + i), 2 * (B + j)
                    block = {rows[Y + b][X + a] for a in (0, 1) for b in (0, 1)}
                    cells = [c.cells.get((X + a, Y + b)) for a in (0, 1) for b in (0, 1)]
                    if any(cl is None or cl[0] != "sprite" for cl in cells):
                        hidden += 1
                        continue
                    if len(block) != 1:
                        split += 1
                        continue
                    got = L.hexrgb(pal[block.pop()])
                    if gold:
                        remap.setdefault(want, set()).add(got)
                    else:
                        bad += got != want
            if gold:
                bad = sum(len(s) > 1 for s in remap.values())
            ok = bad == 0 and split == 0
            fails += not ok
            print(f"{'ok ' if ok else 'BAD'} {p:10s} {t:9s} {'shiny ' if sh else 'normal'} flip={flip!s:5s} "
                  f"{tot} sprite px, {hidden} under overlay, {split} split blocks, "
                  + (f"{len(remap)} colours -> gold, {bad} ambiguous (pure palette remap)" if gold else f"{bad} recoloured"))
sys.exit(1 if fails else 0)
