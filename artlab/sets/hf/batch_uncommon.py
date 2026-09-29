r"""Group "uncommon" of Hidden Fates (sm115): the Uncommon cards, built exactly like the approved Charmeleon 8
(hfcards.charmeleon, the evs Shelgon recipe): window_rgb(texture=False) + evs matte(scale=2), 12 colours,
sat .84 / bright .88, non-foil, no animation, frame #8fc4a8.

Facing read off the scans (most vendor sprites face left):
  2  Metapod     flip   the vendor sprite's face is on its right; the card's Metapod looks left
  5  Scyther     -      head left on card and sprite
  10 Magmar      -      beak left on card and sprite
  30 Jynx        -      near-frontal (ambiguous)
  34 Graveler    -      near-frontal (ambiguous)
  45 Farfetch'd  -      beak left on card and sprite
  46 Chansey     -      three-quarter, face turned left like the sprite

  ..\..\..\.venv\Scripts\python batch_uncommon.py [masks|build|all|sheet] [ids]
"""
import sys

import numpy as np
from scipy import ndimage

import hflib as P  # noqa: F401
from hflib import E, Sprite
import hfcards as C
import hfmasks as HM
import hfbatch as HB
from evcards import meta, place

GROUP = "uncommon"
PLAN = HB.plan(GROUP)
GRID = (40, 60, 700, 500, 900)          # grid.py --crop 40 60 700 500: image px -> card px
# the Stage 1 / 2 icon hexagon runs a few px below and right of HM.ICON on these scans (a dark sliver of it was
# mirrored into the fill): a slightly larger box for the painting-out (masks still cut the shared HM.ICON)
ICON = (0, 60, 128, 176)


def G(pts):
    x0, y0, x1, _, w = GRID
    f = (x1 - x0) / w
    return [(x0 + x * f, y0 + y * f) for x, y in pts]


def hull(cid, pts):
    sh = E.card_img(cid).shape[:2]
    return HM.poly(sh, G(pts)) & HM.rect(sh, *HM.SM_WIN)


def cut_stage(cid, m):
    sh = m.shape
    return m & ~HM.rect(sh, *HM.ICON) & ~HM.rect(sh, *HM.EVOLVES)


# ---------------------------------------------------------------- masks (read off work/grid_<n>.png)
def m_2():
    """every segmenter takes the whole painted scene: Metapod's crescent by hand"""
    cid = "sm115-2"
    m = hull(cid, [(520, 55), (612, 55), (662, 118), (742, 198), (778, 260), (783, 330), (768, 402), (728, 462),
                   (652, 517), (560, 552), (440, 567), (332, 557), (312, 510), (332, 463), (418, 452), (476, 418),
                   (495, 340), (512, 260), (512, 180), (497, 110)])
    return cut_stage(cid, m)


def m_5():
    """rembg takes the whole scene: Scyther (wings, both scythes, legs) by hand; the white slash streaks stay"""
    cid = "sm115-5"
    return hull(cid, [(228, 48), (340, 42), (455, 58), (520, 92), (600, 48), (635, 68), (568, 145), (528, 208),
                      (562, 238), (628, 298), (648, 335), (628, 420), (568, 485), (568, 548), (480, 568),
                      (338, 568), (322, 520), (298, 470), (288, 440), (298, 388), (250, 388), (198, 338),
                      (168, 278), (120, 258), (52, 278), (82, 198), (178, 142), (238, 138)])


def m_10():
    """u2net inside Magmar's hull (it also takes the dark cave wall top right), plus the raised flaming hand it
    misses"""
    cid = "sm115-10"
    h = hull(cid, [(340, 120), (380, 82), (470, 78), (532, 118), (562, 200), (602, 248), (642, 288), (720, 298),
                   (758, 248), (778, 128), (872, 148), (872, 272), (802, 332), (832, 442), (760, 452), (720, 382),
                   (622, 392), (602, 480), (562, 562), (420, 582), (248, 562), (238, 520), (318, 480), (298, 420),
                   (318, 380), (358, 330), (298, 302), (248, 272), (218, 158), (280, 148), (330, 178)])
    arm = hull(cid, [(218, 148), (292, 146), (342, 198), (372, 258), (362, 302), (298, 302), (248, 272)])
    m = (ndimage.binary_dilation(HM.rembg(cid, "u2net"), iterations=3) & h) | arm
    return HM.fin(m, 4)


def m_30():
    """rembg takes the moon and trees: Jynx (hair, hands, dress) by hand, the pink hearts stay"""
    cid = "sm115-30"
    return hull(cid, [(330, 58), (400, 46), (482, 56), (522, 108), (600, 168), (666, 198), (714, 258), (727, 330),
                      (747, 400), (767, 455), (737, 527), (702, 570), (298, 570), (248, 522), (268, 455),
                      (238, 420), (182, 335), (192, 262), (252, 238), (262, 212), (268, 140)])


def m_34():
    return HM.sm_window("sm115-34", close=4, stage=True)


def m_45():
    return HM.sm_window("sm115-45", ("u2net",), close=4)


def m_46():
    """u2net takes Chansey with the garden path: its hull"""
    cid = "sm115-46"
    h = hull(cid, [(352, 118), (400, 92), (470, 86), (560, 102), (640, 116), (712, 116), (734, 170), (724, 240),
                   (794, 288), (779, 342), (742, 392), (702, 442), (642, 488), (550, 503), (448, 488), (368, 452),
                   (322, 402), (302, 330), (327, 288), (347, 200)])
    m = ndimage.binary_dilation(HM.rembg(cid, "u2net"), iterations=4) & h
    return HM.fin(m, 5)


MASKS = {"sm115-2": m_2, "sm115-5": m_5, "sm115-10": m_10, "sm115-30": m_30, "sm115-34": m_34, "sm115-45": m_45,
         "sm115-46": m_46}

# ---------------------------------------------------------------- per card
CFG = {
    "sm115-2": dict(flip=True, stage=True, scene="flower meadow"),
    "sm115-5": dict(flip=False, stage=False, scene="slash streaks over the canyon"),
    "sm115-10": dict(flip=False, stage=False, scene="volcanic cave"),
    "sm115-30": dict(flip=False, stage=False, scene="moonlit forest, hearts"),
    "sm115-34": dict(flip=False, stage=True, scene="rocky slope"),
    "sm115-45": dict(flip=False, stage=False, scene="grass field"),
    "sm115-46": dict(flip=False, stage=False, scene="cottage garden"),
}


def make(cid):
    from evcards2 import matte
    cfg = CFG[cid]
    spr = Sprite(PLAN[cid]["sprite"], flip=cfg["flip"])
    x0, y0, S, W, H = cfg.get("crop") or HB.layout_window(cid, spr)
    boxes = (ICON, HM.EVOLVES) if cfg["stage"] else ()
    rgb = C.window_rgb(cid, boxes=boxes, texture=False)
    c = C.Card(W, H)
    place(c, spr, cid, x0, y0, S, dx=cfg.get("dx", 0), dy=cfg.get("dy", 0), margin=1)
    matte(c, rgb, x0, y0, S, 12, sat=0.84, bright=0.88)
    return meta(c, card=cid, label=f"Uncommon: {C.name_of(cid)}, {cfg['scene']} (non-foil)", rarity="Uncommon",
                finish="non-foil: sprite-scale scene, 12 colours", variant="uncommon", anim=None,
                ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S, frame=C.FRAMES["Uncommon"])


BUILDERS = {cid: (lambda cid=cid: make(cid)) for cid in PLAN}
assert set(BUILDERS) == set(CFG) == set(MASKS)

if __name__ == "__main__":
    HB.run(GROUP, BUILDERS, MASKS, sys.argv[1:])
