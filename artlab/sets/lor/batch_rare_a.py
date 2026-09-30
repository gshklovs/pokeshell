"""Lost Origin group `rare_a` (printed rarity Rare): the ladder Raichu 53 / evs Altaria 106 recipe (build_rare).

Every mask starts from a hand polygon traced on work/grid_<n>.png made with
`grid.py lor <n> --crop 40 80 700 510 --step 25` (660 x 430 card px shown at 900 x 586) and written in that grid
image's pixels; D() maps them to card px (as brs batch_rare_a.py does). Where a rembg model caught the Pokemon
(work/rare_a_rembg.png), its cut is OR-ed in, but only inside the hand polygon grown by `reach` px (so props far
away never come along). The union is then dilated by `dil` px: the rare builder's own grow is a fixed 8 px, and
the texture fill mirrors whatever sits just outside the hole, so any sliver of the real Pokemon left at the
edge came back as a ghost (the brs audit's lesson: mask the whole Pokemon generously).
"""
import numpy as np
from scipy import ndimage

import lorbatch
import lormasks as CM

GROUP = "rare_a"
K = 900 / 660                                    # grid image px per card px


def D(*polys):
    return [[(round(40 + x / K), round(80 + y / K)) for x, y in p] for p in polys]


def mk(model, *polys, card=(), reach=30, dil=10):
    """hand polygons (grid image px, plus `card` polygons in card px) | rembg(model) within reach, dilated"""
    shapes = D(*polys) + [list(p) for p in card]

    def fn(cid):
        rgb = CM.E.card_img(cid)
        sh = rgb.shape[:2]
        h = np.zeros(sh, bool)
        for p in shapes:
            h |= CM.poly(sh, p)
        m = h.copy()
        if model:
            near = ndimage.distance_transform_edt(~h) <= reach
            m |= CM.rembg(cid, model) & near
            m = CM.largest(m, 1) | h
        m = ndimage.binary_fill_holes(m)
        return ndimage.distance_transform_edt(~m) <= dil if dil else m
    return dict(fn=fn)


def hand(*polys, **kw):
    return mk(None, *polys, **kw)


GEN, ANI = "isnet-general-use", "isnet-anime"


TABLE = {
    # frontal (the mushroom and claws spread): unflipped (ambiguous)
    "swsh11-5": dict(kind="rare", sprite="parasect", scene="the misty mushroom wood",
                     mask=mk(GEN, [(380, 100), (450, 95), (560, 135), (640, 185), (740, 190), (795, 245), (820, 330),
                                (810, 425), (775, 480), (715, 480), (690, 445), (645, 455), (605, 520), (500, 550),
                                (400, 550), (325, 540), (285, 510), (235, 450), (210, 350), (230, 260), (285, 200),
                                (355, 165), (360, 120)])),
    # frontal, wings spread: unflipped (ambiguous)
    "swsh11-10": dict(kind="rare", sprite="dustox", scene="the forest canopy",
                      mask=mk(GEN, [(110, 200), (250, 200), (315, 195), (295, 140), (275, 95), (295, 72), (340, 110),
                                 (370, 140), (410, 110), (435, 52), (475, 58), (465, 130), (485, 145), (620, 100),
                                 (752, 70), (772, 92), (748, 262), (695, 335), (625, 375), (565, 400), (515, 430),
                                 (450, 445), (375, 435), (325, 410), (275, 375), (205, 325), (145, 265)])),
    # head at the viewer's right: flipped
    "swsh11-22": dict(kind="rare", sprite="magcargo", flip=True, scene="the misty green wood",
                      mask=mk(GEN, [(330, 135), (340, 90), (405, 48), (420, 125), (440, 115), (470, 88), (545, 85),
                                 (582, 118), (606, 190), (582, 240), (606, 290), (596, 332), (578, 360), (582, 398),
                                 (618, 438), (622, 490), (532, 522), (400, 536), (278, 522), (180, 500), (180, 438),
                                 (235, 400), (198, 342), (194, 258), (225, 190), (272, 150)])),
    # faces the viewer's right: flipped
    "swsh11-32": dict(kind="rare", sprite="politoed", flip=True, texture=False, scene="the rainy night pond",
                      mask=mk(GEN, [(340, 125), (388, 88), (462, 88), (512, 128), (502, 172), (545, 198), (572, 238),
                                 (582, 262), (636, 270), (642, 314), (586, 336), (572, 372), (576, 418), (626, 430),
                                 (632, 470), (562, 492), (500, 496), (452, 486), (422, 476), (402, 506), (328, 506),
                                 (296, 474), (268, 446), (205, 446), (194, 408), (245, 366), (276, 336), (325, 296),
                                 (334, 248), (340, 208), (380, 178), (362, 150)])),
    # faces the viewer's right, the tail fin up at the right: flipped
    "swsh11-34": dict(kind="rare", sprite="dewgong", flip=True, texture=False, scene="the icy splash",
                      mask=hand(card=[[(313, 137), (337, 207), (333, 240), (353, 267), (413, 260), (453, 223),
                                       (440, 160), (460, 104), (550, 104), (590, 180), (610, 280), (610, 370),
                                       (576, 436), (476, 484), (360, 476), (260, 456), (193, 476), (98, 464),
                                       (84, 380), (170, 330), (184, 273), (197, 213), (237, 158), (287, 140)]])),
    # plain Cramorant (no Arrokuda / Pikachu in the gullet); the beak points right: flipped
    "swsh11-50": dict(kind="rare", sprite="cramorant", flip=True, scene="the sunlit forest",
                      mask=mk(GEN, [(335, 30), (425, 34), (475, 84), (528, 94), (505, 124), (478, 150), (515, 196),
                                 (576, 244), (604, 296), (560, 278), (500, 248), (455, 238), (446, 278), (466, 304),
                                 (565, 352), (665, 394), (740, 442), (645, 458), (560, 438), (500, 466), (420, 476),
                                 (362, 476), (332, 506), (248, 516), (226, 486), (168, 476), (84, 466), (72, 408),
                                 (95, 390), (135, 375), (145, 340), (112, 308), (165, 264), (248, 214), (320, 198),
                                 (374, 212), (374, 158), (384, 118), (354, 80)])),
    # head frontal, the body and tail spikes trail to the viewer's left: flipped (ambiguous)
    "swsh11-55": dict(kind="rare", sprite="manectric", flip=True, scene="the discharge",
                      mask=hand([(195, 160), (245, 125), (288, 88), (335, 94), (355, 145), (385, 134), (412, 100),
                                 (435, 185), (468, 85), (498, 24), (565, 24), (606, 96), (626, 166), (656, 228),
                                 (646, 300), (618, 330), (646, 374), (705, 395), (726, 415), (746, 466), (768, 506),
                                 (700, 516), (620, 496), (550, 486), (500, 506), (400, 516), (350, 536), (286, 536),
                                 (262, 472), (300, 420), (258, 446), (196, 476), (164, 452), (185, 378), (225, 326),
                                 (245, 276), (245, 226)])),
    # the mouth at the viewer's left like the sprite; the Tynamo in the scene stay as scenery
    "swsh11-61": dict(kind="rare", sprite="eelektross", texture=False, scene="the electric deep",
                      mask=mk(ANI, [(55, 170), (88, 115), (150, 88), (205, 104), (262, 162), (330, 134), (400, 134),
                                 (470, 124), (520, 104), (580, 84), (640, 74), (700, 34), (765, 54), (798, 116),
                                 (838, 196), (848, 302), (826, 366), (762, 388), (700, 396), (640, 386), (594, 386),
                                 (565, 426), (502, 468), (420, 458), (380, 476), (330, 488), (250, 516), (175, 506),
                                 (152, 474), (112, 404), (102, 334), (62, 294), (44, 230)])),
    # frontal: unflipped (ambiguous)
    "swsh11-63": dict(kind="rare", sprite="clefable", scene="the cherry blossoms",
                      mask=mk(GEN, [(236, 104), (284, 94), (334, 144), (360, 158), (398, 104), (450, 72), (532, 72),
                                 (580, 94), (612, 62), (648, 52), (628, 120), (606, 160), (648, 160), (658, 200),
                                 (628, 238), (616, 262), (636, 312), (646, 372), (626, 424), (566, 476), (516, 506),
                                 (506, 542), (456, 542), (434, 486), (356, 476), (294, 436), (254, 384), (250, 332),
                                 (230, 300), (240, 264), (224, 230), (214, 196), (262, 176), (244, 150)])),
    # Kantonian Mr. Mime, frontal: unflipped (ambiguous); the barrier wall stays as scenery
    "swsh11-67": dict(kind="rare", sprite="mr-mime", scene="the barrier in the alley",
                      mask=mk(ANI, [(92, 160), (135, 94), (232, 104), (262, 150), (252, 104), (318, 42), (366, 72),
                                 (366, 112), (400, 98), (450, 94), (500, 62), (545, 48), (608, 76), (566, 100),
                                 (526, 130), (516, 170), (526, 206), (560, 232), (600, 222), (672, 212), (728, 236),
                                 (718, 300), (738, 342), (706, 396), (646, 402), (628, 420), (638, 446), (698, 446),
                                 (708, 506), (640, 518), (596, 496), (584, 464), (556, 408), (530, 406), (470, 396),
                                 (436, 416), (406, 462), (396, 506), (330, 528), (292, 494), (312, 434), (292, 404),
                                 (322, 370), (332, 344), (296, 308), (240, 308), (196, 306), (164, 288), (112, 266),
                                 (108, 224), (88, 192)])),
    # close-up, the face at the viewer's right: flipped; it fills most of the window
    "swsh11-73": dict(kind="rare", sprite="banette", flip=True, texture=False, scene="the haunted wood",
                      mask=hand([(62, 62), (132, 52), (262, 144), (330, 134), (388, 84), (450, 52), (562, 52),
                                 (606, 94), (656, 154), (706, 194), (716, 300), (686, 384), (656, 454), (626, 546),
                                 (244, 546), (234, 476), (132, 446), (122, 314), (212, 294), (252, 250), (196, 196),
                                 (112, 176), (72, 134)])),
    # the tentacles sweep to the viewer's right, the body at the left
    "swsh11-78": dict(kind="rare", sprite="malamar", scene="the sunset reeds",
                      mask=mk(GEN, [(152, 96), (230, 62), (290, 84), (320, 62), (362, 94), (392, 74), (444, 84),
                                 (476, 124), (506, 104), (478, 158), (440, 172), (500, 194), (600, 174), (700, 132),
                                 (762, 122), (798, 170), (745, 206), (645, 216), (566, 236), (566, 254), (662, 244),
                                 (690, 282), (636, 326), (560, 342), (496, 326), (436, 286), (366, 268), (358, 314),
                                 (348, 396), (318, 456), (286, 496), (238, 508), (202, 474), (182, 400), (182, 320),
                                 (192, 250), (202, 194), (172, 156), (142, 134)])),
    # the head and its body vine; the lei's flowers around stay as scenery (the ones on its body go with it)
    "swsh11-79": dict(kind="rare", sprite="comfey", texture=False, scene="the flower lei",
                      mask=hand([(312, 180), (332, 124), (386, 82), (442, 72), (476, 102), (522, 122), (584, 132),
                                 (626, 164), (626, 262), (584, 296), (520, 296), (480, 286), (426, 306), (392, 338),
                                 (344, 328), (322, 286), (312, 232)])),
    # plain Mimikyu (disguise intact), the head at the viewer's left, the tail at the right
    "swsh11-80": dict(kind="rare", sprite="mimikyu", scene="the vending machine",
                      mask=mk(GEN, [(436, 42), (474, 32), (506, 86), (526, 144), (564, 184), (646, 184), (686, 210),
                                 (706, 234), (764, 234), (782, 262), (762, 304), (706, 344), (686, 400), (640, 424), (606, 440),
                                 (596, 440), (606, 496), (562, 516), (500, 506), (460, 526), (398, 516), (352, 496),
                                 (342, 440), (372, 400), (362, 350), (352, 300), (362, 240), (374, 184), (414, 144),
                                 (434, 104)])),
}

if __name__ == "__main__":
    lorbatch.main(GROUP, TABLE)
