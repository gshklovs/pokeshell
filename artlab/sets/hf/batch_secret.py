r"""Group "secret" of Hidden Fates' Shiny Vault (sma): the gold Tapu GX Rare Secrets (Tapu Bulu SV91, Tapu Fini SV92,
Tapu Lele SV94), built exactly like the approved Tapu Koko-GX SV93 (hfcards.gold_card): the regular sprite with the
evs gold remap, faceted etched gold, glitter, anim `gold`.

Mask: hfmasks.tapu_mask (everything that is not the gold field). Boxes: EDGES, TOP and everything from where the
ability / first attack starts (text_y, read off work/grid_SV<n>.png). Crop: HB.layout_full.

Facing: the three Tapu are drawn near-frontal on the card (as Koko SV93, which the ladder keeps unflipped): not
flipped, listed as ambiguous.

  ..\..\..\.venv\Scripts\python batch_secret.py [masks|build|all|sheet|anim|verify] [ids]
"""
import sys

import hflib as P  # noqa: F401
from hflib import Sprite
import hfcards as C
import hfmasks as HM
import hfbatch as HB

GROUP = "secret"
PLAN = HB.plan(GROUP)

CFG = {
    "sma-SV91": dict(flip=False, text_y=535, scene="Tapu Bulu"),     # Horn Attack row
    "sma-SV92": dict(flip=False, text_y=490, scene="Tapu Fini"),     # Aqua Ring row
    "sma-SV94": dict(flip=False, text_y=440, scene="Tapu Lele"),     # the Ability banner
}

MASKS = {cid: (lambda cid=cid: HM.tapu_mask(cid)) for cid in PLAN}


def make(cid):
    cfg = CFG[cid]
    spr = Sprite(PLAN[cid]["sprite"], cfg["flip"])
    x0, y0, S, W, H = HB.layout_full(cid, spr, top=92, text_y=cfg["text_y"])
    boxes = C.EDGES + (C.TOP, (0, cfg["text_y"], 734, 1024))
    return C.gold_card(cid, spr, x0, y0, S, W, H, boxes, dx=cfg.get("dx", 0), dy=cfg.get("dy", 0))


BUILDERS = {cid: (lambda cid=cid: make(cid)) for cid in PLAN}

if __name__ == "__main__":
    HB.run(GROUP, BUILDERS, MASKS, sys.argv[1:])
