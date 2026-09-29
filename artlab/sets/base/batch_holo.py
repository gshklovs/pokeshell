r"""Group "holo" of the Base Set (base1): the 15 Rare Holo cards besides the ladder's Charizard 4, built exactly like
it (basecards.holo_card: the approved Rare Holo scene -- grid, 12 colours, 1-px rim, 4 sparkles -- with the WotC
starlight foil in the art box), anim `wotc`, frame #56d0e0.

Facing read off the scans (work/facing-holoA/B.png; every vendor sprite here faces left):
  1  Alakazam    -     near-frontal, head a touch left (ambiguous)
  2  Blastoise   -     head turned left, cannon right, like the sprite
  3  Chansey     -     frontal (ambiguous)
  5  Clefairy    -     face on the left of the body, like the sprite
  6  Gyarados    -     head and open jaw left
  7  Hitmonchan  -     frontal guard (ambiguous)
  8  Machamp     -     frontal (ambiguous)
  9  Magneton    -     frontal (ambiguous)
  10 Mewtwo      -     body turned left, tail right
  11 Nidoking    -     head and horn left
  12 Ninetales   flip  head at the right, looking up to the right; the tails fan out left
  13 Poliwrath   -     frontal (ambiguous)
  14 Raichu      -     head left, tail right, like the sprite
  15 Venusaur    -     head left of the body, like the sprite
  16 Zapdos      -     near-frontal, beak down-left (ambiguous)

Masks: rembg where it holds the Pokemon alone on these scans (isnet-general-use / u2net), grown over the glow halo;
hand hulls read off work/grid_<n>.png (grid.py --crop 40 80 560 445 --step 25, written here in that image's px)
where every segmenter takes the starfield (Gyarados, Machamp, Magneton, Ninetales, Poliwrath, Zapdos), and hand
patches OR-ed onto rembg for the parts it missed (Blastoise's feet, Chansey's / Clefairy's ears and feet, Mewtwo's
hand, Nidoking's ear and back spikes, Raichu's lightning tail). tex_src: the starfield patch farthest from the grown
mask inside BASE_WIN, clear of the Stage badge.

  ..\..\..\.venv\Scripts\python batch_holo.py [masks|build|all|sheet] [ids]
"""
import sys

from scipy import ndimage

import baselib as P
from baselib import E, Sprite
import basecards as C
import basemasks as HM
import basebatch as HB

GROUP = "holo"
PLAN = HB.plan(GROUP)
LADDER = set(P.META["ladder"])
GRID = (40, 80, 560, 900)               # grid.py --crop 40 80 560 445: image px -> card px


def G(pts):
    x0, y0, x1, w = GRID
    f = (x1 - x0) / w
    return [(x0 + x * f, y0 + y * f) for x, y in pts]


def hull(cid, pts):
    sh = E.card_img(cid).shape[:2]
    return HM.poly(sh, G(pts))


def win(cid, stage):
    sh = E.card_img(cid).shape[:2]
    w = HM.rect(sh, *HM.BASE_WIN)
    if stage:
        w &= ~HM.rect(sh, *HM.STAGE)
    return w


def hand(cid, pts, stage, grow=0):
    m = hull(cid, pts)
    if grow:
        m = ndimage.binary_dilation(m, iterations=grow)
    return m & win(cid, stage)


# ---------------------------------------------------------------- masks
def m_1():
    """isnet-general-use + isnet-anime have Alakazam and both spoons; grown over the purple glow round him"""
    return HM.base_window("base1-1", ("isnet-general-use", "isnet-anime"), stage=True, grow=18)


def m_2():
    feet = hull("base1-2", [(255, 515), (345, 515), (350, 590), (255, 590)]) | hull("base1-2", [(475, 525), (655, 525), (655, 585), (475, 585)])
    return HM.base_window("base1-2", ("isnet-general-use",), stage=True, extra=feet, grow=7)


def m_3():
    body = hull("base1-3", [(320, 70), (450, 38), (580, 70), (640, 130), (765, 170), (770, 280), (775, 320),
                            (730, 420), (650, 530), (630, 595), (520, 595), (330, 585), (225, 580), (245, 530), (205, 450),
                            (190, 300), (160, 250), (160, 150), (300, 130)])
    return HM.base_window("base1-3", ("u2net",), extra=body, grow=6)


def m_5():
    body = hull("base1-5", [(180, 120), (240, 105), (290, 108), (330, 68), (420, 58), (530, 78), (645, 70), (645, 120),
                            (620, 200), (675, 210), (705, 260), (750, 320), (745, 395), (690, 465), (640, 505),
                            (595, 570), (505, 572), (420, 545), (340, 550), (255, 550), (240, 470), (248, 420),
                            (222, 370), (228, 300), (248, 250), (215, 200)])
    return HM.base_window("base1-5", ("u2net",), extra=body, grow=6)


def m_6():
    """every segmenter takes the starfield: the coil, crest fins, jaw, tongue and whiskers by hand"""
    return hand("base1-6", [(225, 160), (290, 88), (330, 60), (395, 28), (705, 28), (725, 110), (690, 150), (665, 165), (710, 235), (718, 320), (700, 390), (650, 430),
                            (620, 470), (640, 560), (650, 595), (520, 600), (440, 590), (380, 600), (355, 560),
                            (340, 540), (290, 490), (285, 420), (265, 440), (225, 500),
                            (195, 505), (200, 470), (215, 440), (215, 400), (200, 330), (190, 270), (195, 240),
                            (210, 215), (220, 185)], stage=True, grow=5)


def m_7():
    return HM.base_window("base1-7", ("isnet-general-use",), grow=8)


def m_8():
    """rembg takes the whole nebula: Machamp's four arms, head and legs by hand"""
    return hand("base1-8", [(160, 175), (175, 130), (215, 115), (265, 130), (290, 175), (330, 200), (370, 170),
                            (420, 155), (490, 170), (500, 120), (495, 70), (520, 45), (600, 45), (615, 80), (600, 120),
                            (650, 160), (700, 220), (710, 290), (705, 350), (680, 420), (640, 450),
                            (615, 520), (630, 580), (560, 590), (480, 585), (450, 560), (420, 585), (360, 590),
                            (330, 570), (345, 520), (355, 470), (330, 430), (290, 410), (255, 390), (235, 340),
                            (225, 290), (220, 260), (185, 235), (160, 210)], stage=True, grow=6)


def m_9():
    """isnet-general-use misses the top unit: the three units and their magnets by hand"""
    return hand("base1-9", [(285, 120), (345, 50), (420, 95), (440, 120), (480, 110), (555, 50), (620, 120),
                            (595, 160), (630, 220), (760, 205), (765, 230), (660, 300), (700, 370), (690, 400),
                            (630, 410), (640, 460), (675, 550), (560, 580), (530, 470), (460, 420), (415, 420),
                            (360, 470), (345, 585), (290, 575), (250, 555), (220, 550), (265, 440), (250, 420),
                            (190, 400), (195, 370), (245, 310), (240, 275), (130, 230), (145, 205), (270, 230),
                            (365, 200), (330, 190), (290, 160)], stage=True, grow=6)


def m_10():
    hand_ = hull("base1-10", [(270, 250), (370, 280), (400, 330), (330, 350), (270, 320)])
    return HM.base_window("base1-10", ("isnet-general-use",), extra=hand_, grow=10)


def m_11():
    spikes = (hull("base1-11", [(600, 225), (710, 230), (730, 310), (660, 330), (610, 300)])
              | hull("base1-11", [(230, 45), (315, 45), (325, 125), (240, 135)])
              | hull("base1-11", [(640, 375), (725, 375), (725, 455), (640, 455)]))
    return HM.base_window("base1-11", ("isnet-general-use",), stage=True, extra=spikes, grow=8)


def m_12():
    """rembg takes the starfield with the tails: the tails, body and head fur by hand"""
    return hand("base1-12", [(150, 300), (165, 200), (210, 150), (285, 66), (380, 56), (460, 104), (520, 90),
                             (580, 55), (730, 58), (745, 130), (735, 220), (660, 240),
                             (620, 260), (640, 300), (610, 410), (660, 440), (710, 480), (700, 510), (660, 560),
                             (640, 590), (560, 585), (480, 590), (400, 560), (330, 590), (240, 590), (180, 560),
                             (160, 520), (165, 460), (150, 420), (170, 380)], stage=True, grow=10)


def m_13():
    """the blue body on the blue starfield: Poliwrath by hand"""
    return hand("base1-13", [(300, 80), (340, 60), (400, 70), (450, 90), (500, 60), (560, 70), (580, 110),
                             (620, 160), (700, 200), (740, 250), (720, 320), (680, 360), (640, 370), (610, 420),
                             (680, 470), (700, 540), (680, 590), (560, 595), (500, 580), (470, 500), (450, 450),
                             (385, 450), (365, 500), (335, 580), (260, 595), (180, 580), (200, 510), (250, 470),
                             (310, 420), (285, 375), (230, 380), (165, 350), (150, 290), (175, 240), (200, 200),
                             (270, 160), (290, 120)], stage=True, grow=8)


def m_14():
    bolt = hull("base1-14", [(110, 385), (330, 360), (385, 430), (335, 565), (285, 565)])
    return HM.base_window("base1-14", ("isnet-general-use",), stage=True, extra=bolt, grow=8)


def m_15():
    return HM.base_window("base1-15", ("isnet-anime", "u2net"), stage=True, grow=6)


def m_16():
    """rembg takes the starfield and the light rays: Zapdos and its yellow glow by hand"""
    return hand("base1-16", [(40, 105), (240, 70), (320, 130), (355, 80), (385, 160), (430, 130), (470, 70),
                             (520, 90), (600, 80), (700, 60), (850, 50), (850, 130), (800, 200), (740, 260),
                             (705, 300), (650, 380), (610, 370), (590, 420), (570, 470), (520, 500), (490, 560), (440, 520),
                             (400, 560), (380, 500), (330, 500), (310, 450), (290, 420), (200, 330)], stage=False, grow=6)


MASKS = {f"base1-{n}": globals()[f"m_{n}"] for n in (1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16)}

# ---------------------------------------------------------------- per card
CFG = {
    "base1-1": dict(flip=False, stage=True, tex_src=(416, 145, 516, 245), scene="psychic glow over the holo starfield"),
    "base1-2": dict(flip=False, stage=True, tex_src=(71, 310, 171, 410), scene="the holo starfield"),
    "base1-3": dict(flip=False, stage=False, tex_src=(71, 340, 151, 420), scene="the holo starfield"),
    "base1-5": dict(flip=False, stage=False, tex_src=(66, 310, 166, 410), scene="the pink holo starfield"),
    "base1-6": dict(flip=False, stage=True, tex_src=(441, 330, 521, 410), scene="the holo starfield"),
    "base1-7": dict(flip=False, stage=False, tex_src=(421, 310, 521, 410), scene="the green holo starfield"),
    "base1-8": dict(flip=False, stage=True, tex_src=(76, 315, 176, 415), scene="rainbow ring in the holo starfield"),
    "base1-9": dict(flip=False, stage=True, tex_src=(446, 325, 526, 405), scene="the amber holo starfield"),
    "base1-10": dict(flip=False, stage=False, tex_src=(91, 295, 191, 395), scene="the holo starfield"),
    "base1-11": dict(flip=False, stage=True, tex_src=(406, 100, 506, 200), scene="red-green holo starfield"),
    "base1-12": dict(flip=True, stage=True, tex_src=(431, 230, 531, 330), scene="the holo starfield"),
    "base1-13": dict(flip=False, stage=True, tex_src=(451, 105, 531, 185), scene="the holo starfield"),
    "base1-14": dict(flip=False, stage=True, tex_src=(86, 175, 186, 275), scene="the holo starfield"),
    "base1-15": dict(flip=False, stage=True, tex_src=(76, 160, 136, 220), scene="the green holo starfield"),
    "base1-16": dict(flip=False, stage=False, tex_src=(76, 315, 176, 415), scene="lightning rays in the holo starfield"),
}


def make(cid):
    k = CFG[cid]
    spr = Sprite(PLAN[cid]["sprite"], k["flip"])
    return C.holo_card(cid, spr, crop=k.get("crop"), boxes=(C.STAGE,) if k["stage"] else (), tex_src=k["tex_src"],
                       grow=k.get("grow", 5), dx=k.get("dx", 0), dy=k.get("dy", 0), scene=k["scene"])


BUILDERS = {cid: (lambda cid=cid: make(cid)) for cid in PLAN if cid not in LADDER}
assert set(BUILDERS) == set(CFG) == set(MASKS), (set(BUILDERS) ^ set(CFG), set(BUILDERS) ^ set(MASKS))

if __name__ == "__main__":
    HB.run(GROUP, BUILDERS, MASKS, sys.argv[1:])
