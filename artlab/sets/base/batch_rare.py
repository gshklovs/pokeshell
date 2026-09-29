r"""Group "rare" of the Base Set (base1): the non-holo Rare cards, built exactly like the approved ladder Dragonair 18
(basecards.rare_card, the evs Altaria recipe; WotC rares are NON-foil): window_rgb(grow=8, texture fill with a
per-card tex_src) + evs matte(scale=1), 16 colours, sat .95 / bright .95, no animation, frame #6ea5ff.

Facing read off the scans vs the vendor sprites (work/facing-rare.png; every sprite here faces left):
  17 Beedrill    -      near-frontal, head a little left of the body (ambiguous)
  19 Dugtrio     -      three near-frontal heads, the noses a touch left of centre (ambiguous)
  20 Electabuzz  -      frontal, fists raised (ambiguous)
  21 Electrode   -      frontal face (ambiguous)
  22 Pidgeotto   -      head and beak to the left, as the sprite

  ..\..\..\.venv\Scripts\python batch_rare.py [masks|build|all|sheet] [ids]
"""
import sys

import numpy as np
from scipy import ndimage

import baselib as P
from baselib import E, Sprite
import basecards as C
import basemasks as HM
import basebatch as HB

GROUP = "rare"
PLAN = HB.plan(GROUP)
LADDER = set(P.META["ladder"])


def win(sh, stage=True):
    w = HM.rect(sh, *HM.BASE_WIN)
    return w & ~HM.rect(sh, *HM.STAGE) if stage else w


# ---------------------------------------------------------------- masks (card px, read off work/grid_<n>.png)
def m_17():
    """isnet-anime has Beedrill whole (wings, antennae, legs, stinger); the yellow-green glow round him is his:
    a colour rule near the body takes it"""
    cid = "base1-17"
    m = HM.base_window(cid, ("isnet-anime",), close=3, stage=True)
    rgb, hue, s, v = HM.hsv(cid)
    near = ndimage.binary_dilation(m, iterations=14)
    glow = near & (hue > 55) & (hue < 95) & (s > 0.35) & (v > 0.72)
    return HM.fin(m | glow, 2) & win(m.shape)


def m_19():
    """only the three heads are Dugtrio: their orange inside a hand hull; the mound, the rocks and the flowers
    are the scene"""
    cid = "base1-19"
    sh = E.card_img(cid).shape[:2]
    hull = HM.poly(sh, [(158, 362), (158, 200), (172, 168), (200, 154), (240, 154), (250, 134), (270, 120),
                        (312, 120), (342, 132), (362, 158), (370, 204), (398, 210), (422, 236), (434, 278),
                        (434, 368), (392, 372), (330, 382), (240, 378), (190, 370)])
    rgb, hue, s, v = HM.hsv(cid)
    orange = (hue > 12) & (hue < 50) & (s > 0.45) & (v > 0.45)
    m = ndimage.binary_opening(orange & hull, iterations=1)
    m = ndimage.binary_closing(m, iterations=4)
    return ndimage.binary_fill_holes(HM.largest(m, 1)) & win(sh)


def m_20():
    """Electabuzz and the yellow glow halo round him (his figure): everything bright inside his hand hull; the
    lightning bolts running out left and right stay (the hull stops at his hands)"""
    cid = "base1-20"
    sh = E.card_img(cid).shape[:2]
    hull = HM.poly(sh, [(162, 380), (160, 414), (252, 418), (300, 402), (330, 412), (440, 414), (442, 374),
                        (428, 362), (460, 362), (468, 330), (448, 314), (404, 314), (392, 290), (400, 280),
                        (470, 280), (470, 232), (464, 206), (442, 172), (414, 138), (384, 108), (348, 106),
                        (338, 92), (316, 94), (300, 106), (262, 104), (226, 108), (198, 124), (170, 158),
                        (150, 198), (146, 250), (160, 266), (196, 266), (204, 292), (206, 330), (212, 356),
                        (180, 366)])
    rgb, hue, s, v = HM.hsv(cid)
    bright = hull & (v > 0.14)
    m = ndimage.binary_closing(bright, iterations=4)
    m = ndimage.binary_fill_holes(HM.largest(m, 1))
    return ndimage.binary_dilation(m, iterations=4) & hull & win(sh, stage=False)


def m_21():
    """Electrode is a ball: an ellipse a little over its rim; the white-pink centre of the rainbow burst round it
    is the scene"""
    cid = "base1-21"
    sh = E.card_img(cid).shape[:2]
    yy, xx = np.mgrid[0:sh[0], 0:sh[1]]
    ball = ((xx - 297) / 110.0) ** 2 + ((yy - 259) / 111.0) ** 2 <= 1
    return ball & win(sh)


def m_22():
    """u2net has Pidgeotto whole (crest, tail feathers, claws); his shadow under the feet by hand"""
    cid = "base1-22"
    sh = E.card_img(cid).shape[:2]
    shadow = HM.poly(sh, [(205, 390), (250, 380), (330, 382), (380, 392), (372, 420), (300, 424), (215, 418)])
    return HM.base_window(cid, ("u2net",), close=3, stage=True, extra=shadow)


MASKS = {"base1-17": m_17, "base1-19": m_19, "base1-20": m_20, "base1-21": m_21, "base1-22": m_22}

# ---------------------------------------------------------------- per card
CFG = {
    "base1-17": dict(flip=False, stage=True, tex_src=(455, 300, 530, 400), scene="forest canopy"),
    "base1-19": dict(flip=False, stage=True, tex_src=(420, 105, 530, 230), scene="mound under a cloudy sky"),
    "base1-20": dict(flip=False, stage=False, tex_src=None, texture=False, grow=10, scene="lightning in the dark"),
    "base1-21": dict(flip=False, stage=True, tex_src=None, texture=False, scene="radial rainbow burst"),
    "base1-22": dict(flip=False, stage=True, tex_src=(70, 190, 170, 330), scene="sky over the plains"),
}


def make(cid):
    k = CFG[cid]
    spr = Sprite(PLAN[cid]["sprite"], k["flip"])
    return C.rare_card(cid, spr, crop=k.get("crop"), boxes=(C.STAGE,) if k["stage"] else (), tex_src=k["tex_src"],
                       grow=k.get("grow", 8), texture=k.get("texture", True), dx=k.get("dx", 0), dy=k.get("dy", 0),
                       scene=k["scene"])


BUILDERS = {cid: (lambda cid=cid: make(cid)) for cid in PLAN if cid not in LADDER}
assert set(BUILDERS) == set(CFG) == set(MASKS)

if __name__ == "__main__":
    HB.run(GROUP, BUILDERS, MASKS, sys.argv[1:])
