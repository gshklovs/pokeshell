r"""Group "uncommon_a" of Neo Genesis (neo1): the 13 Uncommon cards 26..38, built exactly like the approved ladder
card Quilava 46 (neocards.uncommon_card: window_rgb(texture=False) + evs matte(scale=2), 12 colours, sat .84 /
bright .88, non-foil, no animation, frame #8fc4a8). Stage 1 cards paint out the Stage badge (C.STAGE) and cut it
from the mask.

Facing, read off work/facing-uncA / uncB.png (the art window next to the unflipped vendor sprite, which faces left):
  26 Aipom       -     hangs upside down by its tail hand, face to the viewer (ambiguous)
  27 Ariados     -     head left, as the sprite
  28 Bayleef     -     head left, body right, as the sprite
  29 Bayleef     -     head left
  30 Clefairy    -     frontal (ambiguous)
  31 Croconaw    -     frontal body, snout up-left (ambiguous)
  32 Croconaw    flip  snout right
  33 Electabuzz  -     frontal (ambiguous)
  34 Flaaffy     -     frontal body, tail orb at the right like the sprite
  35 Furret      -     frontal, head turned a little right (ambiguous)
  36 Gloom       -     lying on its back, face to the viewer (ambiguous)
  37 Granbull    -     frontal (ambiguous)
  38 Lanturn     -     head left, tail right, as the sprite

Hand hulls are read off work/grid_<n>.png made with --crop 60 90 540 430 (900 px wide): the points are written in
that image's px and converted with G() (card x = 60 + ix / 1.875, card y = 90 + iy / 1.875).

  ..\..\..\.venv\Scripts\python batch_uncommon_a.py [masks|build|all|sheet] [ids]
"""
import sys

import numpy as np
from scipy import ndimage

import neolib as P
from neolib import E, Sprite
import neocards as C
import neomasks as HM
import neobatch as HB

GROUP = "uncommon_a"
PLAN = HB.plan(GROUP)
LADDER = set(P.META["ladder"])


def sh(cid):
    return E.card_img(cid).shape[:2]


def G(pts):
    """grid_<n> image px (the 60 90 540 430 crop at 1.875x) -> card px"""
    return [(60 + x / 1.875, 90 + y / 1.875) for x, y in pts]


def Z(pts):
    """work/zoom-*.png px (the art window at 1.5x) -> card px"""
    return [(60 + x / 1.5, 90 + y / 1.5) for x, y in pts]


def poly(cid, pts):
    return HM.poly(sh(cid), G(pts))


def disc(cid, cx, cy, r):
    s = sh(cid)
    yy, xx = np.mgrid[0:s[0], 0:s[1]]
    return (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r


def win(cid, stage):
    s = sh(cid)
    w = HM.rect(s, *HM.NEO_WIN)
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
    """(copied from artlab/sets/base/batch_uncommon.py) the cast shadow under the feet: the pixels within `reach`
    px of the mask, in the bottom `band` px of it, darker than k x the median luminance of the scene round them,
    joined to the mask"""
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


def absorb(cid, m, rule, stage, reach=16, grow=2):
    """the Pokemon's own colour (`rule`) within `reach` px of the mask, joined to it (the rims rembg / a hull
    leave behind: they read as ghosts in the fill)"""
    near = ndimage.binary_dilation(m, iterations=reach)
    extra = ndimage.binary_opening(rule & near, iterations=1)
    lbl, _ = ndimage.label(extra | m)
    out = np.isin(lbl, np.unique(lbl[m])) & (extra | m)
    out = ndimage.binary_fill_holes(ndimage.binary_closing(out, iterations=3))
    return ndimage.binary_dilation(out, iterations=grow) & win(cid, stage)


# ---------------------------------------------------------------- masks
def m_26():
    """every segmenter takes nothing or the whole window: Aipom by colour (violet fur, peach skin, the white eyes /
    teeth, the dark outline) inside its hand hull (grid_26: the tail hand at the top, the tail, the upside-down
    head and ears)"""
    cid = "neo1-26"
    _, h, s, v = HM.hsv(cid)
    hull = poly(cid, [(430, 130), (470, 50), (530, 20), (600, 15), (660, 40), (700, 100), (700, 170), (670, 205),
                      (720, 220), (740, 270), (710, 320), (680, 340), (700, 400), (730, 460), (720, 520),
                      (660, 555), (600, 540), (560, 560), (520, 610), (470, 630), (130, 630), (120, 540),
                      (150, 500), (200, 495), (180, 420), (170, 340), (200, 330), (230, 330), (260, 280),
                      (300, 250), (320, 210), (360, 190), (420, 200), (460, 240), (490, 270), (560, 250),
                      (640, 245), (610, 225), (560, 225), (500, 210), (440, 180)])
    purple = (h > 230) & (h < 300) & (s > 0.3)
    peach = (h > 10) & (h < 50) & (s > 0.15) & (s < 0.75) & (v > 0.6)
    m = (purple | peach) & hull
    m = ndimage.binary_opening(m, iterations=1)
    hand = poly(cid, [(430, 130), (460, 40), (500, 10), (705, 10), (722, 100), (710, 175), (660, 210),
                      (600, 230), (520, 225), (450, 190)])
    tail = poly(cid, [(600, 200), (660, 195), (710, 215), (738, 260), (722, 312), (690, 335), (640, 330),
                      (670, 300), (692, 265), (672, 235), (620, 232)])
    return done(cid, m | hand | tail, False, close=5, grow=2)


def m_27():
    """isnet-general-use | u2net take the main Ariados with most of the one behind it; the one behind (left) and
    the big blurred one in the foreground (right, with its raised leg at the right edge) are painted out too by
    hand; the main one's shadow on the deck"""
    cid = "neo1-27"
    main = HM.base_window(cid, ("isnet-general-use", "u2net"), close=4, stage=True)
    main = shadow(cid, main, True)
    behind = poly(cid, [(40, 340), (0, 330), (0, 230), (60, 220), (80, 250), (130, 230), (160, 190), (170, 140), (210, 120), (260, 130),
                        (320, 140), (345, 200), (330, 260), (260, 330), (150, 330)])
    front = poly(cid, [(530, 640), (540, 560), (600, 480), (650, 420), (700, 320), (740, 250), (800, 240),
                       (830, 300), (860, 350), (900, 330), (900, 640)])
    leg = poly(cid, [(840, 40), (880, 20), (900, 20), (900, 400), (860, 400), (850, 300)])
    w = win(cid, True)
    return (main | ndimage.binary_dilation(behind | front | leg, iterations=4)) & w


def m_28():
    """isnet-general-use cuts the head leaf's right half: added by hand (zoom px)"""
    cid = "neo1-28"
    leaf = HM.poly(sh(cid), Z([(310, 40), (400, 18), (480, 28), (528, 50), (512, 82), (470, 102), (440, 92),
                               (400, 62), (340, 72)]))
    m = shadow(cid, HM.base_window(cid, ("isnet-general-use",), close=4, stage=True, extra=leaf), True)
    _, h, s, v = HM.hsv(cid)
    return absorb(cid, m, (h > 35) & (h < 72) & (s > 0.2) & (v > 0.6), True, reach=10)


def m_29():
    """isnet-general-use | the shadow, plus Bayleef's light green rims (a pale-green ghost at the front foot)"""
    cid = "neo1-29"
    m = shadow(cid, HM.base_window(cid, ("isnet-general-use",), close=4, stage=True), True)
    _, h, s, v = HM.hsv(cid)
    return absorb(cid, m, (h > 50) & (h < 95) & (s > 0.25) & (v > 0.45), True, reach=12)


def m_30():
    """rembg takes the swing and the porch: Clefairy by its pink inside a hand hull, plus the black ear tips; the
    swing and the ropes are scene"""
    cid = "neo1-30"
    _, h, s, v = HM.hsv(cid)
    hull = HM.poly(sh(cid), [(250, 194), (270, 200), (290, 205), (330, 212), (362, 212), (358, 238), (352, 262),
                             (378, 274), (390, 300), (378, 324), (345, 328), (300, 328), (250, 328), (212, 324),
                             (206, 300), (218, 280), (233, 260), (243, 230)])
    pink = ((h > 300) | (h < 15)) & (s > 0.12) & (v > 0.55)
    ears = HM.poly(sh(cid), [(253, 196), (272, 199), (272, 216), (256, 216)]) | \
        HM.poly(sh(cid), [(333, 214), (360, 213), (358, 240), (345, 252), (335, 245)])
    m = ndimage.binary_opening(pink & hull, iterations=1) | ears
    return done(cid, m, False, close=5, grow=4)


def m_31():
    """rembg takes the whirlpool: Croconaw's hull by hand (grid_31: the crest, head, back spikes, arms, tail tip,
    feet)"""
    cid = "neo1-31"
    return done(cid, poly(cid, [(400, 70), (525, 30), (510, 95), (555, 105), (525, 140), (540, 200), (590, 230),
                                (600, 295), (565, 300), (600, 340), (665, 355), (660, 395), (620, 400), (590, 420),
                                (610, 470), (640, 540), (630, 575), (655, 595), (640, 612), (540, 612), (500, 585),
                                (410, 590), (380, 612), (300, 607), (305, 580), (330, 560), (330, 520), (240, 505),
                                (275, 440), (300, 480), (345, 440), (380, 380), (330, 400), (300, 410), (285, 365),
                                (300, 350), (330, 340), (380, 310), (320, 260), (310, 200), (320, 170), (360, 150),
                                (400, 160), (405, 120)]), True, grow=2)


def m_32():
    """isnet-general-use misses the tail and the raised arm at the left: added by hand"""
    cid = "neo1-32"
    tail = HM.poly(sh(cid), [(128, 356), (148, 335), (156, 298), (171, 298), (177, 328), (202, 334), (224, 345),
                             (224, 372), (190, 370), (148, 370)]) |         HM.poly(sh(cid), [(175, 364), (226, 364), (226, 396), (175, 396)]) |         HM.poly(sh(cid), [(174, 232), (203, 224), (256, 227), (256, 266), (227, 263), (203, 270), (180, 260)])
    return HM.base_window(cid, ("isnet-general-use",), close=4, stage=True, grow=2, extra=tail)


def m_33():
    """isnet-general-use leaves yellow rims (the fingers) and the shaded right of the belly (by hand, zoom px):
    Electabuzz's yellow joined to it; the cast shadow behind the left arm goes with it"""
    cid = "neo1-33"
    _, h, s, v = HM.hsv(cid)
    belly = HM.poly(sh(cid), Z([(465, 355), (512, 366), (545, 420), (552, 500), (465, 500)]))
    m = HM.base_window(cid, ("isnet-general-use",), close=4, extra=belly)
    return absorb(cid, m, (h > 35) & (h < 75) & (s > 0.4) & (v > 0.35), False, reach=60)


def m_34():
    """isnet-general-use | u2net have Flaaffy with its tail orb; the white electric sparks round the body and the
    orb (over the green mountain, below y 250) are joined to it; its shadow"""
    cid = "neo1-34"
    m = shadow(cid, HM.base_window(cid, ("isnet-general-use", "u2net"), close=4, stage=True), True)
    _, h, s, v = HM.hsv(cid)
    yy = np.arange(m.shape[0])[:, None]
    spark = (v > 0.7) & (s < 0.3) & (yy > 250)
    return absorb(cid, m, spark, True, reach=30, grow=3)


def m_35():
    """isnet-general-use has the big Furret; the tiny one far away at the right stays as scene"""
    return shadow("neo1-35", HM.base_window("neo1-35", ("isnet-general-use",), close=4, stage=True), True)


def m_36():
    """u2net takes the mushrooms: Gloom's hull by hand (grid_36: the dark red flower bulbs, the red petals, the
    violet head and body, arms and foot), plus the dark red petal rims next to it"""
    cid = "neo1-36"
    m = done(cid, poly(cid, [(260, 300), (280, 220), (330, 195), (330, 90), (370, 50), (430, 55), (470, 40),
                             (560, 50), (600, 110), (650, 150), (720, 138), (792, 158), (805, 245), (765, 345),
                             (720, 375), (640, 380), (610, 390), (600, 420), (580, 460), (520, 520), (510, 560),
                             (505, 620), (400, 620), (395, 560), (380, 540), (300, 480), (260, 500), (180, 450),
                             (140, 380), (150, 340), (210, 340), (260, 400), (270, 340)]), True, grow=2)
    _, h, s, v = HM.hsv(cid)
    red = ((h < 15) | (h > 330)) & (s > 0.4) & (v < 0.62)
    return absorb(cid, m, red, True, reach=20)


def m_37():
    """rembg misses the lower body: Granbull by colour (everything that is not the blue sky or the yellow sand)
    inside its hand hull (grid_37)"""
    cid = "neo1-37"
    _, h, s, v = HM.hsv(cid)
    hull = poly(cid, [(60, 160), (200, 135), (300, 155), (480, 55), (520, 35), (640, 15), (695, 65), (705, 125),
                      (645, 145), (625, 200), (645, 280), (630, 340), (645, 435), (685, 475), (705, 535),
                      (745, 595), (760, 630), (285, 630), (295, 520), (305, 470), (255, 455), (185, 400),
                      (195, 330), (155, 305), (65, 315), (55, 260)])
    sky = (h > 190) & (h < 250) & (s > 0.25)
    sand = (h > 25) & (h < 65) & (s > 0.25)
    m = ndimage.binary_opening(hull & ~sky & ~sand, iterations=2)
    m = done(cid, m, True, close=5, grow=2)
    pink = (h > 270) & (h < 350) & (s > 0.12) & (v > 0.4)
    dark = v < 0.3
    return absorb(cid, m, pink | dark, True, reach=18, grow=3)


def m_38():
    """u2net has Lanturn with both lures; the lures' teal glow halos go too"""
    cid = "neo1-38"
    top = disc(cid, 313, 138, 54)
    left = disc(cid, 135, 225, 72)
    m = HM.base_window(cid, ("u2net",), close=4, stage=True, extra=top | left)
    return m


MASKS = {f"neo1-{n}": globals()[f"m_{n}"] for n in range(26, 39)}

# ---------------------------------------------------------------- per card
CFG = {
    "neo1-26": dict(flip=False, stage=False, scene="pastel jungle pods"),
    "neo1-27": dict(flip=False, stage=True, scene="wooden deck under the leaves"),
    "neo1-28": dict(flip=False, stage=True, scene="green leafy whirl"),
    "neo1-29": dict(flip=False, stage=True, scene="CGI orchard"),
    "neo1-30": dict(flip=False, stage=False, scene="porch swing"),
    "neo1-31": dict(flip=False, stage=True, scene="whirlpool"),
    "neo1-32": dict(flip=True, stage=True, scene="rushing water"),
    "neo1-33": dict(flip=False, stage=False, scene="storm clouds"),
    "neo1-34": dict(flip=False, stage=True, scene="green mountain under the sky"),
    "neo1-35": dict(flip=False, stage=True, scene="sandy plain under the clouds"),
    "neo1-36": dict(flip=False, stage=True, scene="mushroom forest"),
    "neo1-37": dict(flip=False, stage=True, scene="lightning over the sand"),
    "neo1-38": dict(flip=False, stage=True, scene="the dark sea"),
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
