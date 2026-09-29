r"""Hidden Fates audit fixes (docs/ART_METHOD.md sections 14 and 16): the clear errors the audit found, each fixed by
overriding the one faulty setting of the owning module in memory and re-rendering, verifying and animating the
card. Precedence: this module is the highest for the ids it lists; re-running the owning module alone undoes the fix.

  sm115-8   Charmeleon (ladder, Uncommon)  the Stage 1 icon hexagon runs past hfmasks.ICON (to about x 128, y 176):
                                            its tan Charmander left a ghost in the window's top-left fill
  sm115-18  Vaporeon (ladder, Rare Holo)   the "Evolves from" bar's lower edge (to about y 128) left a dark strip
                                            along the art's top edge
  Both: the paint-out boxes grow to ICON_FIX / EVOLVES_FIX (the masks are unchanged). batch_uncommon / batch_rare /
  batch_holo already box the larger icon locally (their agent found it).

  ..\..\..\.venv\Scripts\python batch_fixes.py [before] [ids]     'before' copies the current renders to work/audit/before/
"""
import json
import shutil
import sys

import hflib as P
from hflib import E
import hfcards as C

ICON_FIX = (0, 60, 128, 176)
EVOLVES_FIX = (100, 86, 446, 128)


def patched(fn):
    """run a ladder builder with the larger paint-out boxes (restored afterwards)"""
    def build(*a, **k):
        old = C.ICON, C.EVOLVES
        C.ICON, C.EVOLVES = ICON_FIX, EVOLVES_FIX
        try:
            return fn(*a, **k)
        finally:
            C.ICON, C.EVOLVES = old
    return build


FIXES = {"sm115-8": patched(C.charmeleon), "sm115-18": patched(C.vaporeon)}
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
    import hfbuild
    import hfanim
    import hfverify
    f = P.DATA / "sizes.json"
    sizes = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    for cid in ids:
        _, sizes[cid] = hfbuild.render(cid)
    f.write_text(json.dumps({k: sizes[k] for k in C.ORDER if k in sizes}, indent=1), encoding="utf-8")
    hfanim.build(ids)
    for cid in ids:
        hfverify.check(cid)
    print(f"{hfverify.fails} failures")
    assert hfverify.fails == 0


if __name__ == "__main__":
    main(sys.argv[1:])
