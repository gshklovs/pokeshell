r"""Group "rare" of Hidden Fates (sm115): the Rare cards, built exactly like the approved Mew 32 (hfcards.mew, the
evs Altaria recipe; SM rares are NON-foil): window_rgb(grow=8, texture fill with a per-card tex_src) + evs
matte(scale=1), 16 colours, sat .95 / bright .95, no animation, frame #6ea5ff.

Facing read off the scans (most vendor sprites face left):
  3  Butterfree  -      frontal on the card (ambiguous)
  17 Lapras      flip   the body swims right (shell left, neck and head right, looking down at the ball)
  22 Electrode   -      face toward the left on card and sprite
  23 Jolteon     -      head / snout left, body and tail right, as the sprite
  27 Arbok       -      open mouth left
  29 Weezing     -      big head left, small head right, as the sprite
  35 Golem       -      head left
  40 Clefable    -      head turned left
  43 Mr. Mime    -      face turned slightly left
  47 Kangaskhan  flip   snout and punching arm to the right
  50 Snorlax     -      frontal (ambiguous), head right of centre like the sprite

  ..\..\..\.venv\Scripts\python batch_rare.py [masks|build|all|sheet] [ids]
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

GROUP = "rare"
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


# everything outside the art window is boxed out too: window_rgb replaces it with a membrane anyway, and so the
# texture fill never mirrors the card frame / name / "Evolves from" / NO. line text into the holes
# (5 px into the window: its thin silver border line would be mirrored in as well)
OUTSIDE = ((0, 0, 734, HM.SM_WIN[1] + 5), (0, HM.SM_WIN[3] - 5, 734, 1024), (0, 0, HM.SM_WIN[0] + 5, 1024),
           (HM.SM_WIN[2] - 5, 0, 734, 1024))


def window_rgb(cid, boxes, grow, tex_src, protect=None):
    """hfcards.window_rgb (local variant): with `protect` (scene figures next to the hole, e.g. Jessie by Arbok)
    those pixels are kept but never used as the fill's mirror source, so no echo of them lands in the hole"""
    if protect is None:
        return C.window_rgb(cid, boxes=boxes, grow=grow, tex_src=tex_src)
    rgb = E.card_img(cid)
    m = ndimage.binary_dilation(E.mask(cid), iterations=grow)
    for (a, b, c_, d) in boxes:
        m[max(0, b):d, max(0, a):c_] = True
    known = ~m
    out = E.tex_fill(rgb, known & ~protect, 14, tex_src)
    out = np.where((known & protect)[..., None], rgb, out)
    a, b, c_, d = HM.SM_WIN
    w = np.zeros(m.shape, bool)
    w[b:d, a:c_] = True
    return E.L.pushpull(out, w)


def cut_stage(m):
    return m & ~HM.rect(m.shape, *HM.ICON) & ~HM.rect(m.shape, *HM.EVOLVES)


# ---------------------------------------------------------------- masks (read off work/grid_<n>.png)
def m_3():
    """isnet-anime has the body and wings but not the dark wing borders or the antennae (they stayed as an
    outline ghost): its union with Butterfree's hand hull"""
    cid = "sm115-3"
    h = hull(cid, [(158, 112), (210, 78), (300, 76), (362, 116), (410, 196), (438, 196), (448, 128), (470, 100),
                   (504, 112), (500, 170), (478, 228), (540, 206), (598, 176), (640, 160), (700, 116), (754, 126),
                   (774, 180), (764, 262), (724, 322), (686, 332), (704, 380), (724, 442), (704, 524), (642, 554),
                   (588, 544), (522, 514), (474, 564), (440, 584), (356, 574), (346, 524), (298, 514), (246, 484),
                   (226, 420), (254, 372), (196, 342), (166, 282), (146, 200)])
    return cut_stage(HM.sm_window(cid, ("isnet-anime",), close=4, stage=True, extra=h))


def m_17():
    """rembg misses the neck and the flippers under water: Lapras by hand. The beach ball under its chin goes
    with it (left in, the grown mask cut it in half and it read as a red blob next to the sprite)"""
    cid = "sm115-17"
    return hull(cid, [(360, 82), (410, 87), (470, 117), (500, 105), (560, 92), (625, 97), (690, 109), (767, 127),
                      (808, 180), (798, 242), (762, 264), (740, 330), (730, 400), (705, 462), (668, 500),
                      (650, 596), (472, 596), (360, 595), (248, 567), (87, 447), (75, 400), (107, 350),
                      (97, 280), (147, 207), (218, 157), (298, 107)])


def m_22():
    """Electrode is a ball: an ellipse, plus its red motion trail; the lightning stays"""
    cid = "sm115-22"
    sh = E.card_img(cid).shape[:2]
    yy, xx = np.mgrid[0:sh[0], 0:sh[1]]
    ball = ((xx - 495) / 180.0) ** 2 + ((yy - 265) / 162.0) ** 2 <= 1
    trail = hull(cid, [(330, 185), (430, 145), (455, 475), (340, 445), (295, 330)])
    # the red motion blur under the ball: its saturated reds next to the ball and trail
    rgb, hue, s, v = HM.hsv(cid)
    red = ((hue < 22) | (hue > 335)) & (s > 0.4) & (v > 0.25)
    near = ndimage.binary_dilation(ball | trail, iterations=40) & hull(cid, [(250, 150), (620, 150), (620, 600),
                                                                               (250, 600)])
    red = ndimage.binary_closing(red & near, iterations=3)
    return cut_stage(HM.fin((ball & HM.rect(sh, *HM.SM_WIN)) | trail | red, 3))


def m_23():
    """rembg has only the head: Jolteon (ears, white ruff, legs, tail) by hand"""
    cid = "sm115-23"
    return cut_stage(hull(cid, [(28, 326), (198, 296), (238, 248), (226, 74), (304, 80), (355, 150), (452, 80),
                                (522, 66), (604, 118), (594, 200), (546, 262), (602, 326), (702, 326), (804, 376),
                                (826, 424), (764, 470), (724, 590), (418, 590), (418, 472), (358, 450), (298, 410),
                                (198, 370), (28, 358)]))


JESSIE = [(58, 300), (100, 253), (135, 233), (187, 238), (237, 266), (267, 330), (247, 360), (257, 420), (280, 477),
          (223, 480), (196, 442), (180, 392), (172, 477), (133, 477), (146, 387), (106, 354), (83, 322)]


def jessie():
    return HM.poly(E.card_img("sm115-27").shape[:2], G(JESSIE))


def m_27():
    """isnet-anime takes Arbok and Jessie: Jessie is cut back out (she is the scene); the tail around her is kept.
    The fill must not mirror her into the hole (CFG protect)"""
    cid = "sm115-27"
    m = HM.sm_window(cid, ("isnet-anime",), close=4, stage=True, cut=jessie(), keep=3)
    return cut_stage(ndimage.binary_dilation(m, iterations=3) & ~jessie() & HM.rect(m.shape, *HM.SM_WIN))


def m_29():
    return HM.sm_window("sm115-29", close=4, stage=True)


def m_35():
    """isnet-general-use leaves holes in the shell and misses the right leg: Golem's hull (wide enough to take
    the orange glow around him, else it stays as an outline ghost) with the model, grown a little"""
    cid = "sm115-35"
    h = hull(cid, [(278, 145), (340, 104), (430, 89), (532, 94), (614, 134), (666, 198), (676, 300), (648, 380),
                   (668, 468), (678, 566), (496, 580), (502, 488), (470, 450), (404, 478), (342, 518), (236, 527),
                   (222, 480), (270, 438), (252, 384), (224, 326), (152, 316), (140, 262), (164, 214), (238, 202),
                   (256, 184)])
    m = HM.sm_window(cid, ("isnet-general-use", "isnet-anime"), close=8, stage=True, extra=h)
    return cut_stage(ndimage.binary_dilation(m, iterations=4) & HM.rect(m.shape, *HM.SM_WIN))


def m_40():
    return HM.sm_window("sm115-40", ("u2net",), close=4, stage=True)


def m_43():
    """rembg misses the lower hand and legs in the glow: Mr. Mime by hand"""
    cid = "sm115-43"
    return hull(cid, [(320, 100), (390, 40), (480, 28), (640, 30), (660, 70), (560, 125), (540, 200), (625, 222),
                      (710, 282), (732, 360), (712, 420), (772, 496), (786, 570), (700, 582), (650, 557), (560, 552),
                      (496, 490), (470, 452), (428, 480), (398, 548), (300, 594), (206, 584), (218, 506), (292, 456),
                      (330, 424), (296, 400), (140, 396), (100, 300), (102, 214), (150, 120), (262, 114), (306, 146)])


def m_47():
    """rembg takes the explosion: Kangaskhan (punching arm, joey pouch, tail) by hand"""
    cid = "sm115-47"
    return hull(cid, [(184, 76), (260, 62), (384, 66), (444, 128), (462, 204), (556, 150), (598, 86), (646, 48),
                      (806, 44), (836, 120), (806, 236), (736, 266), (656, 280), (590, 334), (648, 356), (718, 424),
                      (772, 518), (752, 596), (540, 596), (60, 596), (54, 480), (66, 400), (76, 330), (70, 232),
                      (140, 170)])


def m_50():
    """rembg takes the foliage: Snorlax by hand (the leaves over its arm go with it)"""
    cid = "sm115-50"
    return hull(cid, [(388, 88), (430, 52), (562, 68), (617, 118), (612, 200), (622, 258), (702, 288), (777, 298),
                      (792, 345), (742, 382), (652, 382), (622, 430), (582, 500), (572, 592), (298, 592), (288, 522),
                      (250, 562), (168, 502), (128, 440), (138, 398), (198, 368), (183, 300), (228, 250), (238, 188),
                      (318, 163), (388, 148)])


MASKS = {"sm115-3": m_3, "sm115-17": m_17, "sm115-22": m_22, "sm115-23": m_23, "sm115-27": m_27, "sm115-29": m_29,
         "sm115-35": m_35, "sm115-40": m_40, "sm115-43": m_43, "sm115-47": m_47, "sm115-50": m_50}

# ---------------------------------------------------------------- per card
CFG = {
    "sm115-3": dict(flip=False, stage=True, tex_src=(66, 330, 170, 470), scene="storm of leaves"),
    "sm115-17": dict(flip=True, stage=False, tex_src=(600, 350, 670, 470), scene="open sea"),
    "sm115-22": dict(flip=False, stage=True, tex_src=(66, 380, 220, 470), scene="lightning"),
    "sm115-23": dict(flip=False, stage=True, tex_src=(580, 110, 670, 300), scene="thunder in the woods"),
    "sm115-27": dict(flip=False, stage=True, tex_src=(560, 380, 670, 470), protect=jessie, dx=4,
                     scene="Jessie on the shore"),  # dx: clear of Jessie
    "sm115-29": dict(flip=False, stage=True, tex_src=None, scene="blue aura, James"),
    "sm115-35": dict(flip=False, stage=True, tex_src=(70, 330, 190, 470), scene="mountain pass"),
    "sm115-40": dict(flip=False, stage=True, tex_src=(450, 130, 670, 230), scene="lake at night"),
    "sm115-43": dict(flip=False, stage=False, tex_src=None, scene="stage hearts"),
    "sm115-47": dict(flip=True, stage=False, tex_src=None, scene="explosion"),
    "sm115-50": dict(flip=False, stage=False, tex_src=(62, 110, 240, 180), scene="jungle canopy"),
}


def make(cid):
    from evcards2 import matte
    cfg = CFG[cid]
    spr = Sprite(PLAN[cid]["sprite"], flip=cfg["flip"])
    x0, y0, S, W, H = cfg.get("crop") or HB.layout_window(cid, spr)
    boxes = OUTSIDE + ((ICON, HM.EVOLVES) if cfg["stage"] else ())
    rgb = window_rgb(cid, boxes, 8, cfg["tex_src"], cfg["protect"]() if cfg.get("protect") else None)
    c = C.Card(W, H)
    place(c, spr, cid, x0, y0, S, dx=cfg.get("dx", 0), dy=cfg.get("dy", 0), margin=1)
    matte(c, rgb, x0, y0, S, 16, sat=0.95, bright=0.95, scale=1)
    return meta(c, card=cid, label=f"Rare: {C.name_of(cid)}, {cfg['scene']} (non-foil)", rarity="Rare",
                finish="non-foil: grid-scale scene, 16 colours", variant="rare", anim=None,
                ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S, frame=C.FRAMES["Rare"])


BUILDERS = {cid: (lambda cid=cid: make(cid)) for cid in PLAN}
assert set(BUILDERS) == set(CFG) == set(MASKS)

if __name__ == "__main__":
    HB.run(GROUP, BUILDERS, MASKS, sys.argv[1:])
