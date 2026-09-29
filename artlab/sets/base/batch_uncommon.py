r"""Group "uncommon" of the Base Set (base1): the 19 Uncommon cards 23..42 (the ladder Charmeleon 24 is done),
built exactly like the approved Charmeleon 24 (basecards.uncommon_card, the evs Shelgon recipe):
window_rgb(texture=False) + evs matte(scale=2), 12 colours, sat .84 / bright .88, non-foil, no animation,
frame #8fc4a8. Stage 1 cards paint out the Stage badge (C.STAGE) and cut it from the mask.

Facing, read off work/facing-unc{1,2}.png (the art window next to the unflipped vendor sprite; nearly every vendor
sprite faces left):
  23 Arcanine    -     head left on card and sprite
  25 Dewgong     -     head left of centre, tail rising at the right, as the sprite
  26 Dratini     flip  the head turns toward the viewer / right and the tail curls out to the LEFT; the sprite's
                       head is left, tail right (near-frontal head: flagged)
  27 Farfetch'd  -     beak left on card and sprite
  28 Growlithe   -     head up-left, tail right, as the sprite
  29 Haunter     -     reaching hand left, as the sprite
  30 Ivysaur     -     head left
  31 Jynx        -     frontal (ambiguous)
  32 Kadabra     -     frontal, spoon raised at the left like the sprite (ambiguous)
  33 Kakuna      -     frontal (ambiguous)
  34 Machoke     -     face turned a little right, as the sprite's (three-quarter: ambiguous)
  35 Magikarp    -     mouth left
  36 Magmar      -     three-quarter left
  37 Nidorino    -     head left
  38 Poliwhirl   -     frontal (ambiguous)
  39 Porygon     -     beak left, tail right, as the sprite
  40 Raticate    -     head left
  41 Seel        -     head front-left, tail rising at the right, as the sprite (near-frontal head)
  42 Wartortle   -     frontal, tail right like the sprite (ambiguous)

  ..\..\..\.venv\Scripts\python batch_uncommon.py [masks|build|all|sheet] [ids]
"""
import sys

import numpy as np
from scipy import ndimage

import baselib as P
from baselib import E, Sprite
import basecards as C
import basemasks as HM
import basebatch as HB

GROUP = "uncommon"
PLAN = HB.plan(GROUP)
LADDER = set(P.META["ladder"])


def sh(cid):
    return E.card_img(cid).shape[:2]


def poly(cid, pts):
    return HM.poly(sh(cid), pts)


def win(cid, stage):
    s = sh(cid)
    w = HM.rect(s, *HM.BASE_WIN)
    if stage:
        w &= ~HM.rect(s, *HM.STAGE)
    return w


def rb(cid, *models):
    m = np.zeros(sh(cid), bool)
    for mo in models:
        m |= HM.rembg(cid, mo)
    return m


def done(cid, m, stage, close=3, keep=1, grow=0):
    w = win(cid, stage)
    m = HM.fin(m & w, close, keep)
    if grow:
        m = ndimage.binary_dilation(m, iterations=grow)
    return m & w


def shadow(cid, m, stage, reach=40, band=70, k=0.72, grow=3):
    """the cast shadow under the feet (a ghost if left in the fill): the pixels within `reach` px of the mask, in the
    bottom `band` px of it, darker than k x the median luminance of the scene round them, joined to the mask"""
    rgb = E.card_img(cid)
    lum = rgb @ np.array([0.299, 0.587, 0.114])
    ys = np.nonzero(m)[0]
    yy = np.arange(m.shape[0])[:, None]
    low = yy >= ys.max() - band
    ring = ndimage.binary_dilation(m, iterations=reach) & ~m & low & win(cid, stage)
    wide = ndimage.binary_dilation(m, iterations=reach + 30) & ~m & low & win(cid, stage)
    dark = ring & (lum < k * np.median(lum[wide & ~ring]))
    dark = ndimage.binary_opening(dark, iterations=1)
    lbl, n = ndimage.label(dark | m)
    keep = np.isin(lbl, np.unique(lbl[m]))
    out = m | (keep & dark)
    out = ndimage.binary_closing(out, iterations=3)
    return ndimage.binary_dilation(out, iterations=grow) & win(cid, stage) if grow else out & win(cid, stage)


# ---------------------------------------------------------------- masks (card px, read off work/grid_<n>.png)
def m_23():
    """isnet-general-use | u2net have Arcanine and the dark tree line at the horizon each side (cut); its shadow"""
    cid = "base1-23"
    s = sh(cid)
    cut = HM.rect(s, 66, 240, 128, 340) | HM.rect(s, 488, 250, 534, 330)
    return shadow(cid, HM.base_window(cid, ("isnet-general-use", "u2net"), close=4, stage=True, cut=cut), True)


def m_25():
    """every segmenter misses Dewgong on the bubbly sea: its hull by hand (head, both flippers, the tail and fin)"""
    cid = "base1-25"
    return done(cid, poly(cid, [(251, 210), (262, 224), (283, 234), (306, 246), (329, 219), (317, 196), (288, 190),
                                (343, 107), (362, 155), (369, 193), (387, 224), (410, 265), (422, 300), (421, 340),
                                (408, 325), (398, 380), (363, 378), (352, 404), (288, 410), (231, 394), (213, 377),
                                (179, 354), (141, 331), (170, 318), (205, 300), (202, 279), (212, 252)]), True)


def m_26():
    return shadow("base1-26", HM.base_window("base1-26", close=4), False)


def m_27():
    return shadow("base1-27", HM.base_window("base1-27", ("isnet-anime",), close=4), False)


def m_28():
    return shadow("base1-28", HM.base_window("base1-28", ("isnet-general-use", "u2net"), close=4), False)


def m_29():
    """u2net has Haunter but not the reaching left hand (by hand); the purple smudge of its shadow on the cave
    wall above goes too"""
    cid = "base1-29"
    hand = poly(cid, [(135, 204), (173, 176), (210, 179), (233, 219), (238, 244), (213, 256), (188, 252), (164, 236),
                      (138, 242), (128, 222)])
    smudge = poly(cid, [(350, 100), (395, 100), (398, 150), (352, 152)])
    body = done(cid, rb(cid, "u2net") | hand, True, close=4, grow=2)
    return body | (smudge & win(cid, True))


def m_30():
    return HM.base_window("base1-30", ("u2net",), close=4, stage=True)


def m_31():
    """u2net has Jynx and her aura; the outstretched left hand by hand"""
    cid = "base1-31"
    hand = poly(cid, [(173, 186), (198, 202), (207, 224), (204, 266), (180, 277), (154, 273), (132, 255), (124, 219),
                      (136, 207), (160, 198)])
    return done(cid, rb(cid, "u2net") | hand, False, close=4, grow=4)


def m_32():
    """isnet-general-use takes Kadabra with bits of the red psychic orbs behind it: the orbs' reds cut back out
    (the star and belly stripes come back with the hole fill)"""
    cid = "base1-32"
    _, h, s, v = HM.hsv(cid)
    red = ((h < 18) | (h > 340)) & (s > 0.45) & (v > 0.25)
    return HM.base_window(cid, close=4, stage=True, cut=red)


def m_33():
    """Kakuna inside its glowing white oval: the oval (the glow ring) goes with it"""
    cid = "base1-33"
    s = sh(cid)
    yy, xx = np.mgrid[0:s[0], 0:s[1]]
    oval = ((xx - 304) / 122.0) ** 2 + ((yy - 262) / 170.0) ** 2 <= 1
    return done(cid, oval | rb(cid, "u2net"), True, close=4)


def m_34():
    return shadow("base1-34", HM.base_window("base1-34", ("isnet-anime", "u2net"), close=4, stage=True, grow=4), True)


def m_35():
    """rembg takes the water: Magikarp's hull (body, fins, tail) over u2net | isnet-general-use"""
    cid = "base1-35"
    h = poly(cid, [(242, 198), (275, 194), (310, 203), (350, 205), (372, 194), (390, 181), (412, 196), (440, 220),
                   (472, 226), (478, 240), (466, 262), (476, 290), (494, 336), (470, 340), (445, 328), (422, 332),
                   (412, 362), (402, 408), (360, 398), (330, 384), (316, 408), (290, 420), (248, 420), (238, 396),
                   (228, 372), (213, 358), (168, 347), (172, 328), (212, 302), (220, 272), (236, 240)])
    m = ndimage.binary_dilation(rb(cid, "u2net", "isnet-general-use"), iterations=3) & h
    return done(cid, m, False, close=5)


def m_36():
    return HM.base_window("base1-36", ("isnet-anime",), close=4)


def m_37():
    return shadow("base1-37", HM.base_window("base1-37", ("u2net",), close=4, stage=True), True, k=0.6)


def m_38():
    """u2net takes Poliwhirl with some snow: its hull (the purple aura included)"""
    cid = "base1-38"
    h = poly(cid, [(231, 116), (283, 128), (352, 114), (400, 134), (408, 172), (446, 216), (482, 240), (495, 276),
                   (482, 326), (446, 338), (396, 350), (436, 378), (442, 412), (398, 418), (362, 406), (344, 356),
                   (283, 352), (232, 356), (210, 406), (172, 418), (152, 396), (180, 356), (170, 332), (130, 332),
                   (114, 294), (124, 262), (146, 238), (178, 210), (200, 188), (204, 148)])
    m = ndimage.binary_dilation(rb(cid, "u2net"), iterations=3) & h
    return done(cid, m, True, close=5, grow=5)


def m_39():
    """isnet-general-use takes the mountain and the plant with Porygon: its hull"""
    cid = "base1-39"
    h = poly(cid, [(152, 280), (182, 243), (212, 214), (248, 201), (298, 198), (332, 226), (341, 248), (320, 284),
                   (340, 286), (381, 237), (408, 232), (390, 300), (378, 336), (430, 373), (418, 395), (364, 404),
                   (315, 398), (310, 383), (271, 383), (242, 389), (199, 377), (211, 350), (223, 327), (236, 297),
                   (158, 285)])
    m = ndimage.binary_dilation(rb(cid, "isnet-general-use"), iterations=3) & h
    return done(cid, m, False, close=4)


def m_40():
    return shadow("base1-40", HM.base_window("base1-40", ("u2net",), close=4, stage=True), True)


def m_41():
    """every segmenter misses Seel on the white-blue water: its hull by hand (tail fin, body, flippers, head)"""
    cid = "base1-41"
    return done(cid, poly(cid, [(228, 122), (262, 121), (300, 125), (332, 133), (337, 146), (326, 175), (364, 165),
                                (389, 180), (403, 213), (407, 253), (400, 300), (389, 338), (433, 350), (464, 358),
                                (463, 388), (440, 403), (398, 408), (364, 394), (312, 394), (288, 411), (231, 416),
                                (211, 397), (184, 388), (142, 391), (129, 364), (139, 338), (206, 324), (211, 304),
                                (240, 280), (258, 251), (271, 246), (292, 220), (310, 200), (318, 186), (271, 189),
                                (236, 183), (224, 162)]), False)


def m_42():
    return shadow("base1-42", HM.base_window("base1-42", ("isnet-anime", "u2net"), close=4, stage=True), True)


MASKS = {f"base1-{n}": globals()[f"m_{n}"] for n in (23, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39,
                                                    40, 41, 42)}

# ---------------------------------------------------------------- per card
CFG = {
    "base1-23": dict(flip=False, stage=True, scene="grassland under a blue sky"),
    "base1-25": dict(flip=False, stage=True, scene="bubbles in the icy sea"),
    "base1-26": dict(flip=True, stage=False, scene="sunset over the sea"),
    "base1-27": dict(flip=False, stage=False, scene="green and yellow watercolour"),
    "base1-28": dict(flip=False, stage=False, scene="fields under the clouds"),
    "base1-29": dict(flip=False, stage=True, scene="dark cave"),
    "base1-30": dict(flip=False, stage=True, scene="dark forest"),
    "base1-31": dict(flip=False, stage=False, scene="streaks of light in the dark"),
    "base1-32": dict(flip=False, stage=True, scene="red psychic orbs in the dark"),
    "base1-33": dict(flip=False, stage=True, scene="radial lines over the leaves"),
    "base1-34": dict(flip=False, stage=True, scene="dark rocky hills"),
    "base1-35": dict(flip=False, stage=False, scene="pond water, fishing worm"),
    "base1-36": dict(flip=False, stage=False, scene="fire and lava"),
    "base1-37": dict(flip=False, stage=True, scene="red canyon"),
    "base1-38": dict(flip=False, stage=True, scene="icy water"),
    "base1-39": dict(flip=False, stage=False, scene="CGI hills and pines"),
    "base1-40": dict(flip=False, stage=True, scene="tall grass"),
    "base1-41": dict(flip=False, stage=False, scene="swirling water"),
    "base1-42": dict(flip=False, stage=True, scene="sandy shore"),
}


def make(cid):
    k = CFG[cid]
    spr = Sprite(PLAN[cid]["sprite"], k["flip"])
    return C.uncommon_card(cid, spr, crop=k.get("crop"), boxes=(C.STAGE,) if k["stage"] else (),
                           dx=k.get("dx", 0), dy=k.get("dy", 0), scene=k["scene"])


BUILDERS = {cid: (lambda cid=cid: make(cid)) for cid in PLAN if cid not in LADDER}
assert set(BUILDERS) == set(CFG) == set(MASKS), set(BUILDERS) ^ set(CFG)

if __name__ == "__main__":
    HB.run(GROUP, BUILDERS, MASKS, sys.argv[1:])
