r"""Group "holo" of Neo Genesis (neo1): the 17 Rare Holo cards besides the ladder's Lugia 9, built exactly like it
(neocards.holo_card: the approved Rare Holo scene -- grid, 12 colours, rim, 4 sparkles -- with the WotC starlight
foil in the art box), anim `wotc`, frame #56d0e0.

Facing read off the scans (work/facing-holoA/B.png; every vendor sprite here faces left):
  1  Ampharos    -     body three-quarter left, head up, tail right
  2  Azumarill   -     frontal (ambiguous)
  3  Bellossom   -     frontal (ambiguous); the second Bellossom (top right) is painted out too
  4  Feraligatr  flip  snout right
  5  Feraligatr  -     snout and open jaw left
  6  Heracross   -     horn and head leaning left
  7  Jumpluff    -     near-frontal (ambiguous)
  8  Kingdra     -     snout left, tail curled right
  10 Meganium    -     head bowed left, tail left, like the sprite
  11 Meganium    -     frontal, looking up (ambiguous)
  12 Pichu       -     frontal (ambiguous)
  13 Skarmory    -     head left, wings right
  14 Slowking    -     frontal (ambiguous)
  15 Steelix     -     head left, tail right
  16 Togetic     -     face up-left
  17 Typhlosion  flip  seen from behind, head turned right
  18 Typhlosion  -     head and open mouth left

Masks: rembg where one model holds the Pokemon alone (Ampharos, Azumarill, Heracross, Jumpluff, Meganium 11,
Skarmory, Steelix, the Typhlosions' bodies), hand hulls read off work/grid_<n>.png (grid.py --crop 60 90 540 430
--step 20, written here in that image's px) where every model takes the starfield (Bellossom x2, both Feraligatr,
Meganium 10, Pichu, Slowking, Togetic), a colour rule inside a hull for Kingdra (pale body + yellow belly, as
Lugia 9), and hand patches OR-ed onto rembg for the parts it missed (Ampharos's head orb, ear, tail tip and red tail
orb; Jumpluff's top puff; Meganium 11's antennae and rear body; Steelix's tail tip; the Typhlosions' neck flames,
17's tail fur and snout, 18's jaw). Togetic's scene is soft glow orbs: texture=True kept (the smooth membrane left a
blurred silhouette).

  ..\..\..\.venv\Scripts\python batch_holo.py [masks|build|all|sheet] [ids]
"""
import sys

import numpy as np
from scipy import ndimage

import neolib as P
from neolib import E, Sprite
import neocards as C
import neomasks as HM
import neobatch as HB

GROUP = "holo"
PLAN = HB.plan(GROUP)
LADDER = set(P.META["ladder"])
GRID = (60, 90, 540, 900)               # grid.py --crop 60 90 540 430: image px -> card px


def G(pts):
    x0, y0, x1, w = GRID
    f = (x1 - x0) / w
    return [(x0 + x * f, y0 + y * f) for x, y in pts]


def hull(cid, pts):
    sh = E.card_img(cid).shape[:2]
    return HM.poly(sh, G(pts))


def win(cid, stage):
    sh = E.card_img(cid).shape[:2]
    w = HM.rect(sh, *HM.NEO_WIN)
    if stage:
        w &= ~HM.rect(sh, *HM.STAGE)
    return w


def hand(cid, pts, stage, grow=0, more=()):
    m = hull(cid, pts)
    for p in more:
        m |= hull(cid, p)
    if grow:
        m = ndimage.binary_dilation(m, iterations=grow)
    return m & win(cid, stage)


# ---------------------------------------------------------------- masks
def m_1():
    """isnet-general-use has Ampharos, its tail orb and the head orb; grown over the glow (the light rays are scene)"""
    c = "neo1-1"
    parts = (hull(c, [(625, 410), (690, 410), (695, 475), (625, 480)]) | hull(c, [(545, 465), (640, 470), (640, 540), (545, 545)])
             | hull(c, [(465, 35), (545, 40), (545, 100), (465, 100)]) | hull(c, [(340, 0), (475, 0), (475, 95), (340, 95)]))
    return HM.base_window(c, ("isnet-general-use",), stage=True, extra=parts, keep=4, grow=10)


def m_2():
    """u2net has Azumarill and its white halo, isnet-general-use the tail ball"""
    return HM.base_window("neo1-2", ("u2net", "isnet-general-use"), stage=True, grow=12)


def m_3():
    """every model takes the leafy starfield: both Bellossom by hand (the big one and the one at the top right)"""
    big = [(30, 370), (60, 310), (100, 270), (80, 230), (90, 195), (140, 190), (165, 190), (160, 120), (230, 140),
           (290, 170), (310, 130), (330, 160), (380, 140), (420, 210), (470, 260), (460, 300), (550, 340), (500, 370),
           (530, 400), (500, 430), (510, 470), (440, 470), (430, 540), (450, 560), (400, 560), (330, 510), (320, 560),
           (300, 580), (240, 560), (200, 600), (150, 560), (150, 500), (100, 460), (60, 450), (80, 400)]
    small = [(550, 130), (600, 110), (620, 40), (640, 30), (650, 70), (700, 30), (750, 40), (780, 10), (830, 20),
             (810, 100), (870, 110), (885, 130), (870, 190), (830, 200), (860, 230), (860, 270), (820, 300),
             (760, 290), (720, 300), (700, 330), (680, 310), (660, 350), (620, 330), (600, 300), (590, 240),
             (600, 200), (560, 200), (525, 190), (530, 145)]
    return hand("neo1-3", big, stage=True, grow=9, more=(small,))


def m_4():
    """every model takes the starfield: Feraligatr (crest, snout, raised claws, tail spikes) by hand"""
    return hand("neo1-4", [(50, 638), (60, 530), (100, 470), (115, 430), (140, 480), (170, 470), (180, 540),
                           (215, 520), (250, 470), (255, 390), (260, 300), (255, 275), (270, 245), (255, 195),
                           (290, 195), (275, 110), (270, 45), (320, 55), (345, 95), (400, 120), (435, 80), (470, 165), (490, 170),
                           (540, 90), (600, 100), (605, 25), (650, 90), (700, 100), (710, 190), (750, 215), (790, 240),
                           (790, 280), (770, 305), (745, 330), (710, 350), (700, 390), (750, 420), (780, 460),
                           (800, 520), (790, 540), (760, 540), (725, 510), (715, 545), (690, 545), (665, 470),
                           (640, 460), (620, 520), (640, 600), (640, 638)], stage=True, grow=6)


def m_5():
    """every model takes the starfield: Feraligatr and its white halo by hand"""
    return hand("neo1-5", [(90, 230), (110, 200), (160, 195), (210, 165), (250, 140), (280, 90), (345, 20), (400, 40),
                           (445, 60), (440, 120), (420, 170), (480, 175), (500, 130), (530, 160), (560, 140),
                           (630, 140), (680, 165), (700, 200), (710, 250), (680, 290), (710, 330), (740, 330),
                           (760, 280), (790, 330), (830, 420), (830, 470), (790, 500), (765, 535), (700, 530), (700, 560),
                           (690, 600), (685, 638), (290, 638), (290, 600), (320, 560), (330, 480),
                           (330, 400), (300, 340), (270, 310), (240, 270), (200, 250), (160, 270), (110, 270)],
                stage=True, grow=14)


def m_6():
    """isnet-anime has Heracross alone (the grey rock at the left is scene)"""
    return HM.base_window("neo1-6", ("isnet-anime",), grow=6)


def m_7():
    """u2net has Jumpluff and its three cotton puffs (the tree trunks are scene)"""
    sh = E.card_img("neo1-7").shape[:2]
    puff = HM.poly(sh, [(200, 115), (240, 105), (285, 115), (310, 150), (315, 195), (330, 215), (300, 245),
                        (265, 260), (225, 255), (190, 235), (170, 200), (168, 160), (180, 130)])
    return HM.base_window("neo1-7", ("u2net",), stage=True, extra=puff, grow=6)


def m_8():
    """rembg takes the starfield: Kingdra by colour (the pale blue body, the yellow belly) inside a loose hull"""
    cid = "neo1-8"
    rgb, h, s, v = HM.hsv(cid)
    loose = hand(cid, [(30, 390), (40, 350), (100, 300), (150, 260), (150, 200), (120, 120), (110, 60), (140, 50),
                       (170, 90), (190, 40), (215, 10), (240, 40), (290, 30), (390, 20), (400, 60), (330, 70),
                       (300, 100), (380, 120), (400, 90), (430, 90), (465, 75), (460, 130), (470, 160), (530, 200), (560, 240),
                       (630, 270), (630, 300), (560, 310), (580, 400), (640, 430), (700, 450), (740, 500), (740, 580),
                       (700, 605), (630, 600), (570, 540), (500, 560), (400, 570), (320, 540), (300, 460), (290, 420),
                       (260, 380), (200, 360), (130, 360), (80, 395)], stage=True, grow=6)
    col = ((v > 0.5) & (s < 0.45)) | ((h > 25) & (h < 65) & (s > 0.3) & (v > 0.45))
    m = ndimage.binary_opening(col & loose, iterations=2)
    m = HM.largest(ndimage.binary_closing(m, iterations=5), 1)
    m = ndimage.binary_closing(ndimage.binary_dilation(m, iterations=4), iterations=6)
    return ndimage.binary_dilation(ndimage.binary_fill_holes(m), iterations=4) & win(cid, True)


def m_10():
    """isnet-general-use misses the flower collar: Meganium by hand"""
    return hand("neo1-10", [(310, 120), (305, 60), (330, 20), (345, 0), (365, 0), (370, 20), (350, 40), (380, 100),
                            (440, 110), (450, 150), (470, 200), (540, 180), (610, 190), (700, 215), (735, 265),
                            (730, 320), (710, 360), (690, 390), (700, 460), (690, 520), (670, 560), (640, 600),
                            (600, 590), (560, 550), (520, 500), (490, 560), (480, 600), (470, 638), (340, 638),
                            (310, 600), (320, 560), (310, 500), (300, 470), (250, 470), (195, 470), (200, 450),
                            (260, 420), (320, 370), (370, 340), (380, 300), (400, 260), (420, 230), (350, 220),
                            (320, 190)], stage=True, grow=6) | HM.base_window("neo1-10", ("isnet-general-use",), stage=True, grow=6)


def m_11():
    """u2net has Meganium alone (the fireworks at the top left are scene)"""
    c = "neo1-11"
    more = (hull(c, [(440, 110), (470, 30), (520, 0), (600, 15), (655, 35), (645, 65), (560, 45), (505, 45), (475, 115)])
            | hull(c, [(540, 430), (620, 435), (700, 470), (730, 495), (705, 545), (705, 638), (540, 638)])
            | hull(c, [(320, 540), (560, 540), (560, 638), (320, 638)]))
    return HM.base_window(c, ("u2net",), stage=True, extra=more, grow=8)


def m_12():
    """u2net takes a blue patch of starfield with Pichu: Pichu and its yellow glow by hand"""
    return hand("neo1-12", [(260, 80), (280, 10), (360, 10), (410, 90), (420, 160), (480, 150), (560, 130),
                            (700, 115), (725, 165), (650, 250), (580, 320), (560, 350), (620, 480), (610, 560),
                            (560, 580), (540, 620), (470, 638), (300, 638), (290, 560), (330, 470), (300, 420),
                            (270, 430), (265, 400), (280, 340), (265, 280), (280, 240), (270, 160)], stage=False, grow=9)


def m_13():
    return HM.base_window("neo1-13", ("isnet-general-use",), grow=6)


def m_14():
    """rembg takes the starfield or half of Slowking: Slowking by hand (the rock under it is scene)"""
    return hand("neo1-14", [(575, 120), (630, 80), (660, 50), (700, 65), (740, 60), (760, 110), (800, 110),
                            (790, 145), (830, 140), (810, 190), (790, 200), (790, 250), (810, 290), (810, 340),
                            (810, 400), (800, 440), (790, 480), (790, 490), (760, 495), (560, 495),
                            (570, 450), (540, 440), (490, 420), (490, 395), (510, 390), (550, 395), (575, 370),
                            (570, 330), (560, 290), (560, 240), (590, 220), (600, 200), (610, 180), (590, 150)],
                stage=True, grow=6)


def m_15():
    sh = E.card_img("neo1-15").shape[:2]
    tip = HM.poly(sh, [(440, 360), (475, 360), (470, 395), (452, 415), (440, 400)])
    return HM.base_window("neo1-15", ("isnet-general-use",), stage=True, extra=tip, grow=6)


def m_16():
    """isnet-general-use takes glow orbs of the starfield: Togetic by hand"""
    return hand("neo1-16", [(340, 110), (350, 60), (380, 30), (430, 20), (450, 90), (510, 80), (520, 120), (480, 200),
                            (560, 210), (630, 210), (620, 260), (560, 310), (550, 350), (560, 400), (540, 450),
                            (520, 470), (520, 560), (500, 600), (460, 620), (400, 600), (370, 560), (330, 570),
                            (330, 520), (360, 470), (350, 400), (310, 370), (350, 320), (360, 290), (390, 260),
                            (380, 230), (340, 190)], stage=True, grow=12)


def m_17():
    """u2net has the body and tail; the neck flames by hand"""
    fl = hull("neo1-17", [(190, 140), (260, 100), (290, 40), (330, 0), (470, 0), (560, 0), (620, 0), (680, 40),
                          (690, 120), (680, 180), (630, 210), (600, 170), (560, 130), (430, 140), (360, 200),
                          (300, 200), (250, 180)])
    fl |= hull("neo1-17", [(150, 430), (230, 400), (300, 390), (320, 470), (300, 560), (220, 570), (160, 500)])
    fl |= hull("neo1-17", [(600, 250), (660, 250), (680, 300), (670, 365), (600, 375), (585, 320)])
    return HM.base_window("neo1-17", ("u2net",), stage=True, extra=fl, grow=10)


def m_18():
    """u2net has the body; the neck flames by hand"""
    fl = hull("neo1-18", [(360, 90), (400, 60), (400, 10), (460, 15), (480, 70), (540, 40), (620, 50), (660, 70),
                          (710, 150), (650, 200), (600, 230), (530, 250), (480, 240), (450, 180), (380, 150)])
    fl |= hull("neo1-18", [(290, 240), (360, 235), (395, 280), (380, 325), (320, 320), (290, 290)])
    return HM.base_window("neo1-18", ("u2net",), stage=True, extra=fl, grow=6)


MASKS = {f"neo1-{n}": globals()[f"m_{n}"] for n in (1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15, 16, 17, 18)}

# ---------------------------------------------------------------- per card
SF = "the holo starfield"
CFG = {
    "neo1-1": dict(flip=False, stage=True, tex_src=(420, 300, 520, 400), scene="light rays in the holo starfield"),
    "neo1-2": dict(flip=False, stage=True, tex_src=(75, 290, 150, 410), scene="the green holo starfield"),
    "neo1-3": dict(flip=False, stage=True, tex_src=(400, 320, 520, 415), scene="leaves in the green holo starfield"),
    "neo1-4": dict(flip=True, stage=True, tex_src=(72, 150, 150, 290), scene=SF),
    "neo1-5": dict(flip=False, stage=True, tex_src=(72, 270, 190, 400), scene=SF),
    "neo1-6": dict(flip=False, stage=False, tex_src=(200, 110, 330, 200), scene="a grey rock in the holo starfield"),
    "neo1-7": dict(flip=False, stage=True, tex_src=(400, 250, 525, 400), scene="dark trees in the green holo starfield"),
    "neo1-8": dict(flip=False, stage=True, tex_src=(410, 120, 525, 230), scene="the violet holo starfield"),
    "neo1-10": dict(flip=False, stage=True, tex_src=(75, 120, 190, 300), scene=SF),
    "neo1-11": dict(flip=False, stage=True, tex_src=(430, 250, 525, 400), scene="fireworks in the holo starfield"),
    "neo1-12": dict(flip=False, stage=False, tex_src=(440, 200, 525, 400), scene="the gold-blue holo starfield"),
    "neo1-13": dict(flip=False, stage=False, tex_src=(430, 120, 525, 220), scene="a light band in the holo starfield"),
    "neo1-14": dict(flip=False, stage=True, tex_src=(80, 130, 200, 260), scene="a rock in the holo starfield"),
    "neo1-15": dict(flip=False, stage=True, tex_src=(75, 320, 250, 410), scene=SF),
    "neo1-16": dict(flip=False, stage=True, tex_src=(75, 150, 220, 300), scene="glowing lights in the holo starfield"),
    "neo1-17": dict(flip=True, stage=True, tex_src=(420, 220, 525, 400), scene=SF),
    "neo1-18": dict(flip=False, stage=True, tex_src=(75, 130, 190, 400), scene="the red holo starfield"),
}


def make(cid):
    k = CFG[cid]
    spr = Sprite(PLAN[cid]["sprite"], k["flip"])
    return C.holo_card(cid, spr, crop=k.get("crop"), boxes=(C.STAGE,) if k["stage"] else (), tex_src=k["tex_src"],
                       grow=k.get("grow", 5), texture=k.get("texture", True), dx=k.get("dx", 0), dy=k.get("dy", 0), scene=k["scene"])


BUILDERS = {cid: (lambda cid=cid: make(cid)) for cid in PLAN if cid not in LADDER}
assert set(BUILDERS) == set(CFG) == set(MASKS), (set(BUILDERS) ^ set(CFG), set(BUILDERS) ^ set(MASKS))

if __name__ == "__main__":
    HB.run(GROUP, BUILDERS, MASKS, sys.argv[1:])
