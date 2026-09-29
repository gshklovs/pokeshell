r"""Group "rare" of Neo Genesis (neo1): the non-holo Rare cards, built exactly like the approved ladder Murkrow 24
(neocards.rare_card, the evs Altaria recipe; WotC rares are NON-foil): window_rgb(grow=8, texture fill with a
per-card tex_src) + evs matte(scale=1), 16 colours, sat .95 / bright .95, no animation, frame #6ea5ff.

rembg takes the scene (or nothing) on every one of these scans, so every mask is a hand hull read off
work/grid_<n>.png (--crop 60 90 540 430 --step 20; the hull points are written in that grid image's px and
converted by g()), sometimes with a colour rule inside it (Elekid) or isnet-general-use near it (Magby, Sneasel).
Fills: texture fill + tex_src, grow 12 (Cleffa, Magby, Sneasel); the smooth membrane for the flat night sky (Elekid,
else the mirror echoes the bolts into the hole) and for Donphan (3/4 of the window), whose hidden sky is rebuilt
by rowfill() (a local fix, see there).

Facing read off the scans vs the vendor sprites (work/facing-rare.png; every sprite here faces left):
  20 Cleffa   flip  the head is turned three-quarter to its left (face features right of the head's centre) and
                    the body leans right into the yarn; the sprite's face is turned the other way
  21 Donphan  -     trunk and tusks to the left, as the sprite
  22 Elekid   -     frontal, arms up (ambiguous)
  23 Magby    -     frontal, beak a touch left (ambiguous)
  25 Sneasel  -     head three-quarter to the left (gem and snout left), as the sprite (the lead listed it ambiguous)

  ..\..\..\.venv\Scripts\python batch_rare.py [masks|build|all|sheet] [ids]
"""
import sys

import numpy as np
from scipy import ndimage

import neolib as P
from neolib import E, Sprite
import neocards as C
import neomasks as HM
import neobatch as HB

GROUP = "rare"
PLAN = HB.plan(GROUP)
LADDER = set(P.META["ladder"])


def g(pts):
    """grid image px (grid.py --crop 60 90 540 430: 1.875 x) -> card px"""
    return [(60 + x / 1.875, 90 + y / 1.875) for x, y in pts]


def win(sh, stage=False):
    w = HM.rect(sh, *HM.NEO_WIN)
    return w & ~HM.rect(sh, *HM.STAGE) if stage else w


def shape(cid):
    return E.card_img(cid).shape[:2]


# ---------------------------------------------------------------- masks
def m_20():
    """Cleffa by hand: both ears, the curl, the body and the hands; the yarn string over her and the yarn balls /
    basket round her are the scene (the string over her is painted out with her)"""
    sh = shape("neo1-20")
    hull = HM.poly(sh, g([(196, 292), (220, 262), (262, 232), (330, 210), (378, 172), (412, 180), (462, 186),
                          (540, 202), (592, 222), (590, 262), (584, 302), (568, 330), (584, 378), (584, 432),
                          (548, 478), (472, 508), (378, 508), (318, 478), (288, 422), (278, 364), (246, 356),
                          (204, 330)]))
    return hull & win(sh)


def m_21():
    """Donphan fills the window: the ear flap, the tusk, the curled trunk, the head, the back and the legs by hand;
    the sky at the left, the ground under him at the bottom left and right and the shadow between the legs stay"""
    sh = shape("neo1-21")
    hull = HM.poly(sh, g([(0, 175), (40, 180), (110, 130), (230, 92), (310, 56), (360, 12), (380, 0), (900, 0),
                          (900, 472), (850, 480), (840, 560), (815, 590), (810, 625), (680, 625), (650, 590),
                          (620, 562), (560, 570), (500, 566), (360, 568), (250, 530), (222, 470), (222, 372),
                          (236, 340), (150, 322), (40, 302), (0, 292)]))
    return hull & win(sh, stage=True)


def m_22():
    """Elekid by colour: his yellow and black stripes inside a hand hull that stops short of the lightning bolts;
    his grey shadow on the cloud by hand (the clouds, bolts and stars are the scene)"""
    cid = "neo1-22"
    rgb, hue, s, v = HM.hsv(cid)
    sh = rgb.shape[:2]
    hull = HM.poly(sh, g([(252, 200), (262, 160), (312, 146), (344, 172), (350, 212), (400, 212), (462, 182),
                          (472, 146), (522, 140), (578, 162), (586, 214), (570, 244), (588, 298), (604, 326),
                          (648, 356), (662, 410), (644, 454), (600, 460), (572, 456), (570, 542), (530, 560),
                          (490, 544), (482, 472), (458, 448), (410, 444), (370, 426), (364, 484), (322, 504),
                          (256, 486), (236, 442), (252, 402), (298, 392), (334, 386), (324, 332), (306, 294),
                          (270, 258)]))
    yellow = (hue > 40) & (hue < 70) & (s > 0.45) & (v > 0.55)
    black = v < 0.22
    m = hull & (yellow | black)
    m = ndimage.binary_closing(m, iterations=6)
    m = ndimage.binary_fill_holes(HM.largest(m, 1))
    m = ndimage.binary_dilation(m, iterations=3) & hull
    yy, xx = np.mgrid[0:sh[0], 0:sh[1]]
    shadow = ((xx - 293) / 118.0) ** 2 + ((yy - 373) / 16.0) ** 2 <= 1
    return (m | shadow) & win(sh)


def m_23():
    """Magby by hand (isnet-general-use has most of him but drops the right arm and the tail): the hair puff, the
    beak, both arms and their claws, the tail, the legs and feet; the white glow behind him is the fire scene"""
    sh = shape("neo1-23")
    hull = HM.poly(sh, g([(372, 22), (452, 14), (494, 40), (544, 56), (576, 108), (590, 160), (580, 204),
                          (546, 214), (506, 222), (510, 262), (494, 298), (562, 296), (606, 312), (646, 316),
                          (652, 348), (636, 386), (600, 390), (566, 380), (560, 416), (618, 436), (656, 414),
                          (676, 440), (646, 484), (584, 502), (566, 526), (566, 558), (614, 566), (646, 598),
                          (632, 626), (578, 626), (550, 614), (500, 594), (488, 562), (476, 530), (456, 544),
                          (456, 584), (424, 612), (364, 600), (370, 566), (398, 536), (410, 510), (398, 470),
                          (400, 424), (406, 392), (362, 418), (330, 430), (300, 414), (294, 366), (336, 346),
                          (388, 330), (390, 302), (376, 272), (354, 252), (326, 218), (296, 194), (280, 140),
                          (286, 98), (316, 66), (346, 50)]))
    near = ndimage.binary_dilation(hull, iterations=10)
    m = hull | (HM.rembg("neo1-23", "isnet-general-use") & near)
    return HM.fin(m, 3) & win(sh)


def m_25():
    """Sneasel by hand: the raised left claw, both arms, the head and the pink ear feather, the right claw, the
    gem, the body and the pink tail feathers at the bottom right; the pink psychic glow at the raised claw and the
    dark forest are the scene"""
    sh = shape("neo1-25")
    hull = HM.poly(sh, g([(116, 214), (150, 186), (200, 236), (232, 300), (244, 370), (300, 404), (340, 412),
                          (352, 374), (344, 300), (346, 248), (380, 200), (392, 146), (418, 156), (440, 124),
                          (474, 160), (540, 170), (560, 186), (598, 124), (678, 64), (760, 10), (796, 22),
                          (766, 112), (704, 194), (644, 244), (636, 300), (604, 382), (620, 426), (740, 396),
                          (784, 390), (754, 300), (752, 228), (800, 214), (856, 256), (886, 320), (876, 404),
                          (822, 434), (760, 468), (824, 534), (866, 590), (800, 616), (700, 596), (636, 566),
                          (610, 572), (604, 638), (428, 638), (436, 560), (414, 528), (378, 534), (296, 514),
                          (226, 456), (186, 404), (156, 334), (126, 282)]))
    near = ndimage.binary_dilation(hull, iterations=8)
    m = hull | (HM.rembg("neo1-25", "isnet-general-use") & near)
    return HM.fin(m, 3) & win(sh)


MASKS = {"neo1-20": m_20, "neo1-21": m_21, "neo1-22": m_22, "neo1-23": m_23, "neo1-25": m_25}

# ---------------------------------------------------------------- per card
CFG = {
    "neo1-20": dict(flip=True, stage=False, tex_src=(356, 300, 412, 356), grow=12, scene="a room with yarn balls"),
    "neo1-21": dict(flip=False, stage=True, tex_src=None, texture=False, grow=10, rowfill=(68, 112),
                    scene="plains under a streaked sky"),
    "neo1-22": dict(flip=False, stage=False, tex_src=None, texture=False, grow=8, scene="on a cloud among lightning"),
    "neo1-23": dict(flip=False, stage=False, tex_src=(72, 143, 192, 356), grow=12, scene="a wall of fire"),
    "neo1-25": dict(flip=False, stage=False, tex_src=(72, 326, 166, 418), grow=12,
                    scene="dark forest, pink psychic glow"),
}


def rowfill(cid, rgb, grow, boxes, strip, ramp=30.0):
    """local fix (not in neocards): Donphan hides ~3/4 of the window, so the membrane pulls the ground's brown up
    over the whole hidden sky. Deep inside the hole, blend towards a per-row profile of the visible left strip
    (sky over the horizon over the hills), keeping the membrane at the hole's edge"""
    sh = rgb.shape[:2]
    hole = ndimage.binary_dilation(E.mask(cid), iterations=grow)
    for bx in boxes:
        hole |= HM.rect(sh, *bx)
    hole &= win(sh)
    a, b, c, d = HM.NEO_WIN
    x0, x1 = strip
    rows = np.arange(b, d)
    prof = np.full((len(rows), 3), np.nan)
    for i, y in enumerate(rows):
        ok = ~hole[y, x0:x1]
        if ok.sum() >= 4:
            prof[i] = np.median(rgb[y, x0:x1][ok], axis=0)
    good = ~np.isnan(prof[:, 0])
    for ch in range(3):
        prof[:, ch] = np.interp(rows, rows[good], prof[good, ch])
    prof = ndimage.gaussian_filter1d(prof, 4, axis=0)
    dist = ndimage.distance_transform_edt(hole | ~win(sh))           # from the visible scene only
    w = np.clip(dist / ramp, 0, 1)[..., None]
    out = rgb.copy()
    out[b:d, a:c] = rgb[b:d, a:c] * (1 - w[b:d, a:c]) + prof[:, None, :] * w[b:d, a:c]
    return out


def make(cid):
    k = CFG[cid]
    spr = Sprite(PLAN[cid]["sprite"], k["flip"])
    boxes = (C.STAGE,) if k["stage"] else ()
    orig = C.window_rgb
    if k.get("rowfill"):
        def patched(cid_, **kw):
            return rowfill(cid_, orig(cid_, **kw), kw.get("grow", 6), kw.get("boxes", ()), k["rowfill"])
        C.window_rgb = patched
    try:
        return C.rare_card(cid, spr, crop=k.get("crop"), boxes=boxes, tex_src=k["tex_src"], grow=k.get("grow", 8),
                           texture=k.get("texture", True), dx=k.get("dx", 0), dy=k.get("dy", 0), scene=k["scene"])
    finally:
        C.window_rgb = orig


BUILDERS = {cid: (lambda cid=cid: make(cid)) for cid in PLAN if cid not in LADDER}
assert set(BUILDERS) == set(CFG) == set(MASKS)

if __name__ == "__main__":
    HB.run(GROUP, BUILDERS, MASKS, sys.argv[1:])
