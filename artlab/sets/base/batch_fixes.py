r"""Base Set audit fixes (docs/ART_METHOD.md sections 14 and 16): the clear errors the audit found, each fixed by
overriding the one faulty setting of the owning module in memory and re-rendering and verifying the card.
Precedence: this module is the highest for the ids it lists; re-running the owning module alone undoes the fix.

  base1-32  Kadabra (batch_uncommon, Uncommon)  the Uncommon matte's light rim (evcards2.matte: dark scenery cells
                                                touching the outline take the darkest palette colour with luminance
                                                >= 70) picked the red of the psychic orbs on this black scene, so a
                                                RED outline ran round the whole sprite. Fix: the rim takes a neutral
                                                light grey instead (the rim's purpose: keep the black outline readable
                                                on dark scenery); every other cell is unchanged.

  ..\..\..\.venv\Scripts\python batch_fixes.py [before] [ids]     'before' copies the current renders to work/audit/before/
"""
import importlib.util
import json
import shutil
import sys

import numpy as np

import baselib as P
from baselib import E, L
import basecards as C

RIM_GREY = (0.44, 0.43, 0.48)


def owner(name):
    f = P.HERE / f"batch_{name}.py"
    spec = importlib.util.spec_from_file_location(f"base_batch_{name}", f)
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


def neutral_rim(fn):
    """run a matte builder, then give the rim cells (bg cells at sprite scale touching the outline whose colour is
    the rim colour the matte chose) a neutral grey"""
    def build():
        c = fn()
        q = c.bg.copy()
        outl = c.outline_mask()
        fig = c.fig_mask()
        near = np.zeros_like(outl)
        for ax, ay in ((2, 0), (-2, 0), (0, 2), (0, -2), (1, 0), (-1, 0), (0, 1), (0, -1)):
            near |= np.roll(np.roll(outl, ay, 0), ax, 1)
        cand = near & ~fig
        # the rim colour: the most common bg colour next to the outline that is saturated red
        cols = q[cand]
        sat = cols.max(1) - cols.min(1)
        red = (cols[:, 0] > 0.5) & (sat > 0.35)
        if red.any():
            vals, n = np.unique(np.round(cols[red], 4), axis=0, return_counts=True)
            rim = vals[n.argmax()]
            hit = cand & np.all(np.abs(np.round(q, 4) - rim) < 1e-3, -1)
            q[hit] = RIM_GREY
            c.bg = q
            c.bgq = L.to8(q)
        return c
    return build


FIXES = {"base1-32": neutral_rim(owner("uncommon").BUILDERS["base1-32"])}
BUILDERS = FIXES


def main(argv):
    ids = [a for a in argv if a in FIXES] or list(FIXES)
    before = E.WORK / "audit" / "before"
    if "before" in argv:
        before.mkdir(parents=True, exist_ok=True)
        for cid in ids:
            shutil.copy(E.OUT / f"{cid}-art.png", before / f"{cid}-art.png")
        return
    C.BUILDERS.update({cid: FIXES[cid] for cid in ids})
    import basebuild
    import baseanim
    import baseverify
    f = P.DATA / "sheets" / "fixes-sizes.json"
    sizes = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    for cid in ids:
        _, sizes[cid] = basebuild.render(cid)
    f.write_text(json.dumps(sizes, indent=1), encoding="utf-8")
    baseanim.build(ids)
    for cid in ids:
        baseverify.check(cid)
    print(f"{baseverify.fails} failures")
    assert baseverify.fails == 0


if __name__ == "__main__":
    main(sys.argv[1:])
