r"""Group "uncommon_b" of Neo Genesis (neo1): the 13 Uncommon cards 39..45, 47..52 (the ladder Quilava 46 is done),
built exactly like the approved Quilava 46 (neocards.uncommon_card: window_rgb(texture=False) + evs matte(scale=2),
12 colours, sat .84 / bright .88, non-foil, no animation, frame #8fc4a8). Stage 1 cards paint out the Stage badge
(C.STAGE) and cut it from the mask.

Facing, read off work/facing-unc{B,C}.png (the art window next to the unflipped vendor sprite):
  39 Ledian     -     frontal (ambiguous); two smaller Ledian behind are painted out too
  40 Magmar     -     head / mouth left, as the sprite
  41 Miltank    -     head three-quarter left, reaching arm left, tail right, as the sprite (near-frontal head)
  42 Noctowl    -     frontal (ambiguous)
  43 Phanpy     -     trunk left
  44 Piloswine  -     snout and tusks lower left
  45 Quagsire   -     lying, head left, tail up at the right
  47 Quilava    flip  snout right
  48 Seadra     -     snout left
  49 Skiploom   -     near-frontal, face a little right of centre (ambiguous)
  50 Sunflora   -     frontal (ambiguous)
  51 Togepi     -     frontal (ambiguous), in a tree hollow (the hollow is scene)
  52 Xatu       flip  beak right

  ..\..\..\.venv\Scripts\python batch_uncommon_b.py [masks|build|all|sheet] [ids]
"""
import sys

import numpy as np
from scipy import ndimage

import neolib as P
from neolib import E, Sprite
import neocards as C
import neomasks as HM
import neobatch as HB

GROUP = "uncommon_b"
PLAN = HB.plan(GROUP)
LADDER = set(P.META["ladder"])


def sh(cid):
    return E.card_img(cid).shape[:2]


def g(pts):
    """grid_<n>.png image px (--crop 60 90 540 430, 1.875x) -> card px"""
    return [(60 + x / 1.875, 90 + y / 1.875) for x, y in pts]


def poly(cid, pts, grid=True):
    return HM.poly(sh(cid), g(pts) if grid else pts)


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
    """(copied from base/batch_uncommon.py) the cast shadow under the feet: the pixels within `reach` px of the
    mask, in the bottom `band` px of it, darker than k x the median luminance of the scene round them"""
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


# ---------------------------------------------------------------- masks (hulls read off work/grid_<n>.png)
def m_39():
    """the main Ledian by its hand hull (rembg drops the translucent wings and antenna tips); the two smaller Ledian behind (top left, top
    right) are painted out too, by hand hulls (their wings are translucent: rembg drops them)"""
    cid = "neo1-39"
    main = poly(cid, [(405, 15), (428, 22), (410, 120), (460, 120), (540, 20), (565, 25), (545, 120), (575, 170),
                      (585, 240), (600, 232), (660, 266), (722, 288), (758, 330), (748, 375), (736, 392), (742, 500), (705, 552),
                      (620, 555), (595, 600), (520, 605), (470, 565), (420, 560), (380, 595), (300, 600), (262, 560),
                      (268, 500), (300, 470), (300, 440), (292, 400), (296, 360), (286, 320), (290, 282), (330, 260), (382, 248),
                      (385, 230), (360, 175), (342, 162), (396, 12)])
    body = done(cid, main, True, grow=5)
    left = poly(cid, [(88, 38), (106, 42), (98, 108), (148, 98), (158, 38), (178, 44), (178, 108), (192, 178),
                      (252, 182), (285, 208), (280, 238), (248, 248), (244, 302), (200, 305), (198, 365), (150, 365),
                      (130, 335), (112, 375), (42, 375), (30, 322), (26, 230), (36, 188), (72, 172), (78, 118)])
    right = poly(cid, [(712, 32), (732, 38), (736, 88), (778, 82), (793, 12), (812, 18), (798, 90), (812, 128),
                       (852, 138), (878, 168), (884, 244), (834, 254), (812, 284), (758, 290), (738, 254), (688, 268),
                       (676, 230), (686, 178), (698, 120), (716, 88)])
    small = ndimage.binary_dilation(left | right, iterations=8)
    return body | (small & win(cid, True))


def m_40():
    """rembg takes the lava sky (u2net) or nothing: Magmar's hull by hand (the head flames, the tail flame at the
    top right, both clawed hands, the body down to the window's bottom)"""
    cid = "neo1-40"
    h = poly(cid, [(385, 330), (398, 290), (388, 215), (422, 200), (445, 152), (440, 124), (466, 115), (482, 72), (528, 74),
                   (535, 110), (524, 135), (548, 136), (576, 96), (592, 78), (650, 80), (656, 115), (640, 150),
                   (662, 185), (698, 170), (732, 135), (762, 112), (804, 112), (836, 140), (858, 198), (870, 260),
                   (880, 350), (878, 470), (842, 562), (808, 640), (330, 640), (322, 590), (340, 536), (380, 500),
                   (424, 462), (442, 425), (432, 388), (405, 365)])
    return done(cid, h, False, grow=6)


def m_41():
    """isnet-anime | isnet-general-use have Miltank; the hay bale at the left and the far herd at the right stay
    scene; its shadow on the grass"""
    cid = "neo1-41"
    bale = poly(cid, [(185, 402), (295, 398), (300, 475), (180, 475)])
    m = shadow(cid, HM.base_window(cid, ("isnet-anime", "isnet-general-use"), close=4, cut=bale), False,
               reach=60, k=0.8)
    return m | HM.rect(sh(cid), 422, 358, 462, 392)          # the tail's shadow on the grass


def m_42():
    """isnet-general-use has Noctowl; the tiny Hoothoot in the trees stay scene"""
    cid = "neo1-42"
    return shadow(cid, HM.base_window(cid, ("isnet-general-use", "isnet-anime"), close=4, stage=True, grow=2), True)


def m_43():
    cid = "neo1-43"
    return shadow(cid, HM.base_window(cid, ("isnet-general-use", "u2net"), close=4), False)


def m_44():
    cid = "neo1-44"
    return shadow(cid, HM.base_window(cid, ("u2net",), close=4, stage=True, grow=2), True)


def m_45():
    cid = "neo1-45"
    return shadow(cid, HM.base_window(cid, ("u2net",), close=4, stage=True, grow=2), True)


def m_47():
    """every segmenter takes the smoke and rocks or only parts: Quilava's hull by hand (the back flames, the head
    flames, the crouched legs), grown by a colour rule for the flame tips (warm saturated px joined to it)"""
    cid = "neo1-47"
    h = poly(cid, [(150, 200), (175, 168), (205, 192), (230, 158), (262, 208), (292, 248), (330, 278), (380, 298),
                   (440, 288), (500, 258), (528, 238), (522, 180), (516, 66), (560, 106), (580, 36), (602, 22),
                   (632, 88), (662, 96), (674, 168), (704, 188), (710, 232), (684, 282), (670, 350), (686, 420),
                   (674, 464), (642, 474), (624, 520), (624, 574), (590, 586), (556, 564), (538, 512), (514, 494),
                   (504, 556), (534, 580), (522, 596), (468, 596), (452, 562), (428, 512), (360, 484), (300, 484),
                   (274, 502), (280, 528), (238, 534), (206, 502), (186, 442), (180, 402), (166, 372), (160, 300),
                   (150, 242)])
    _, hh, ss, vv = HM.hsv(cid)
    flame = ((hh < 58) | (hh > 345)) & (ss > 0.4) & (vv > 0.45)
    flame &= ndimage.binary_dilation(h, iterations=40)
    lbl, _ = ndimage.label(flame | h)
    flame &= np.isin(lbl, np.unique(lbl[h]))                  # only the flames joined to the hull
    m = ndimage.binary_closing(h | flame, iterations=3)
    return shadow(cid, done(cid, m, True, grow=7), True)


def m_48():
    """isnet-general-use has only the head and the belly on the mottled sea: Seadra's hull by hand (the snout,
    the fins, the yellow fin, the curled tail)"""
    cid = "neo1-48"
    h = poly(cid, [(114, 108), (160, 116), (215, 126), (250, 96), (320, 72), (380, 74), (440, 54), (510, 36),
                   (592, 28), (640, 70), (682, 44), (694, 90), (656, 128), (710, 146), (792, 150), (744, 222),
                   (694, 246), (686, 262), (766, 298), (776, 394), (704, 386), (668, 392), (706, 420), (726, 470),
                   (730, 522), (694, 564), (620, 574), (566, 564), (522, 616), (496, 606), (462, 530), (452, 476),
                   (430, 494), (358, 484), (306, 444), (296, 392), (300, 360), (326, 330), (316, 302), (246, 244),
                   (206, 214), (166, 184), (120, 168)])
    return done(cid, h, True, grow=4)


def m_49():
    """rembg takes the grass or only the flower: Skiploom's hull by hand (the flower, the leaf, the body and
    feet) and its dark shadow"""
    cid = "neo1-49"
    h = poly(cid, [(182, 280), (198, 198), (268, 116), (360, 70), (440, 56), (532, 80), (602, 126), (640, 144),
                   (702, 134), (764, 156), (786, 210), (764, 274), (722, 304), (694, 322), (694, 382), (662, 424),
                   (604, 504), (562, 524), (502, 566), (420, 586), (328, 590), (306, 556), (248, 556), (156, 524),
                   (130, 472), (136, 400), (172, 366)])
    return shadow(cid, done(cid, h, True, grow=2), True)


def m_50():
    cid = "neo1-50"
    return HM.base_window(cid, ("isnet-general-use",), close=4, stage=True, grow=3)


def m_51():
    """rembg takes the whole tree: Togepi's hull by hand (the spikes, the egg shell, the arms); the hollow and the
    ivy are scene"""
    cid = "neo1-51"
    h = poly(cid, [(298, 244), (344, 232), (364, 202), (396, 212), (420, 196), (446, 192), (472, 218), (490, 222),
                   (526, 202), (548, 232), (598, 248), (590, 296), (598, 388), (624, 418), (620, 454), (588, 460),
                   (562, 502), (512, 524), (400, 528), (348, 508), (328, 478), (296, 462), (286, 430), (300, 404),
                   (302, 372)])
    return done(cid, h, False, grow=2)


def m_52():
    """u2net | isnet-general-use have Xatu with its folded red-white wing at the left"""
    cid = "neo1-52"
    wing = poly(cid, [(335, 160), (368, 155), (374, 200), (334, 244), (268, 352), (208, 322), (246, 266), (298, 206)])
    return shadow(cid, HM.base_window(cid, ("u2net", "isnet-general-use"), close=4, stage=True, grow=2, extra=wing),
                  True)


MASKS = {f"neo1-{n}": globals()[f"m_{n}"] for n in (39, 40, 41, 42, 43, 44, 45, 47, 48, 49, 50, 51, 52)}

# ---------------------------------------------------------------- per card
CFG = {
    "neo1-39": dict(flip=False, stage=True, scene="fireflies in the night"),
    "neo1-40": dict(flip=False, stage=False, scene="volcano and lava sky"),
    "neo1-41": dict(flip=False, stage=False, scene="pasture under a blue sky"),
    "neo1-42": dict(flip=False, stage=True, scene="night forest"),
    "neo1-43": dict(flip=False, stage=False, scene="rocky hills at dusk"),
    "neo1-44": dict(flip=False, stage=True, scene="snowfield"),
    "neo1-45": dict(flip=False, stage=True, scene="deep blue water"),
    "neo1-47": dict(flip=True, stage=True, scene="misty forest rocks"),
    "neo1-48": dict(flip=False, stage=True, scene="mottled deep sea"),
    "neo1-49": dict(flip=False, stage=True, scene="meadow with yellow flowers"),
    "neo1-50": dict(flip=False, stage=True, scene="veranda with sunflowers"),
    "neo1-51": dict(flip=False, stage=False, scene="tree hollow in the ivy"),
    "neo1-52": dict(flip=True, stage=True, scene="red rock wall"),
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
