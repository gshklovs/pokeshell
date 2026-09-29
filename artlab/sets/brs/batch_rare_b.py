"""Brilliant Stars group `rare_b` (printed rarity Rare, second half): the ladder Luxray 51 recipe (build_rare,
evs Altaria 106: matte, grid-scale scene, 16 colours), modelled on cz batch_rare.py.

Every mask is a hand hull (model=None). Most hulls were traced on a 1:1 overlay of the scan's art crop
(card px 50..700 x 80..510, the mask outline drawn in red) and are written in that crop's pixels; O() maps them to
card px (+50, +80). Rows using hand() are in card px (read off work/grid_<n>.png).
"""
import brsbatch

GROUP = "rare_b"


def O(*polys):
    return [[(x + 50, y + 80) for x, y in p] for p in polys]


def hand(*polys, keep=1, **kw):
    return dict(model=None, add=list(polys), keep=keep, **kw)


def handO(*polys, keep=1, **kw):
    kw = {k: (O(*v) if k in ("cut_after", "cut") else v) for k, v in kw.items()}
    return dict(model=None, add=O(*polys), keep=keep, **kw)


TABLE = {
    # frontal, arms spread (sprite frontal too): unflipped (ambiguous)
    "swsh9-83": dict(kind="rare", sprite="golurk", scene="the rocky dusk", texture=False,
                     mask=handO([(38, 140), (50, 100), (90, 82), (150, 88), (200, 102), (215, 78), (260, 62),
                                 (330, 52), (362, 58), (400, 82), (440, 92), (500, 76), (535, 118), (550, 178),
                                 (585, 228), (618, 270), (618, 335), (560, 350), (480, 345), (445, 335), (425, 382),
                                 (385, 405), (85, 405), (80, 330), (105, 298), (145, 265), (125, 238), (58, 232),
                                 (38, 190)])),
    # face on the left, the goo arm arcing up and over to the right, as the sprite: unflipped
    "swsh9-85": dict(kind="rare", sprite="muk", scene="the junkyard", texture=False,
                     mask=handO([(78, 300), (98, 238), (148, 186), (200, 162), (262, 166), (312, 192), (352, 212),
                                 (420, 212), (478, 192), (515, 158), (535, 110), (505, 62), (465, 42), (445, 12),
                                 (562, 6), (635, 38), (645, 232), (602, 284), (522, 314), (455, 334), (422, 364),
                                 (352, 408), (150, 408), (98, 372)],
                                [(168, 40), (200, 12), (342, 12), (364, 60), (354, 122), (302, 144), (220, 140),
                                 (178, 102)], keep=2)),
    # head right, tail left (cz Liepard 78 is flipped too)
    "swsh9-91": dict(kind="rare", sprite="liepard", flip=True, scene="the city rooftop at night",
                     mask=handO([(238, 240), (258, 208), (298, 188), (326, 158), (326, 58), (348, 16), (422, 12),
                                 (444, 58), (464, 98), (474, 158), (504, 228), (544, 256), (594, 276), (596, 324),
                                 (522, 334), (462, 334), (404, 354), (344, 412), (266, 412), (246, 332)],
                                [(76, 222), (98, 182), (148, 132), (195, 114), (242, 121), (274, 158), (284, 220),
                                 (284, 264), (242, 256), (226, 194), (190, 176), (152, 192), (112, 230)], keep=2)),
    # the claw reaching to the viewer's left, as the sprite's: unflipped; fills the window
    "swsh9-94": dict(kind="rare", sprite="grimmsnarl", scene="the moonlit wisps", texture=False,
                     mask=hand([(60, 200), (100, 175), (150, 185), (200, 195), (250, 190), (295, 155), (325, 125),
                                (365, 115), (385, 94), (445, 94), (475, 115), (525, 104), (540, 140), (565, 170),
                                (570, 235), (610, 275), (630, 345), (650, 415), (685, 465), (685, 496), (60, 496),
                                (60, 420), (88, 400), (95, 370), (60, 330)],
                               [(585, 262), (690, 248), (690, 392), (605, 392)])),     # the green hair tip
    # pink Trash Cloak (verified on the scan); head near-frontal: unflipped (ambiguous)
    "swsh9-98": dict(kind="rare", sprite="wormadam-trash", scene="hanging in the park trees",
                     mask=hand([(245, 240), (285, 198), (325, 178), (345, 155), (372, 165), (400, 185), (450, 165),
                                (525, 162), (560, 172), (552, 220), (512, 235), (478, 222), (488, 262), (478, 325),
                                (448, 365), (430, 420), (438, 460), (400, 478), (355, 478), (325, 445), (295, 395),
                                (275, 352), (265, 318), (285, 300), (262, 282), (245, 262)],
                               [(222, 226), (250, 168), (310, 168), (302, 334), (230, 340)],   # the left streamer
                               [(328, 94), (352, 94), (352, 190), (328, 190)], keep=2)),
    # head on the right, body sprawled to the left: flipped (the sprite's head is on its left)
    "swsh9-100": dict(kind="rare", sprite="heatran", flip=True, scene="the volcano storm", texture=False,
                      mask=handO([(35, 280), (68, 238), (160, 212), (248, 212), (288, 188), (316, 158), (316, 58),
                                  (338, 12), (422, 2), (505, 28), (525, 90), (535, 158), (563, 198), (612, 218),
                                  (645, 238), (645, 420), (35, 420)])),
    # shield left, lance thrusting right, as the sprite: unflipped
    "swsh9-101": dict(kind="rare", sprite="escavalier", scene="the rock-shattering charge", texture=False,
                      mask=handO([(15, 82), (42, 80), (98, 115), (92, 58), (128, 16), (200, 6), (292, 12), (354, 38),
                                  (384, 88), (394, 128), (434, 158), (484, 188), (524, 228), (564, 308), (618, 392),
                                  (560, 400), (468, 374), (400, 364), (332, 404), (300, 416), (76, 416), (56, 340),
                                  (66, 258), (96, 220), (56, 160)])),
    # a machine at a diagonal, no clear facing: unflipped (ambiguous)
    "swsh9-104": dict(kind="rare", sprite="klinklang", scene="the sparking night city", texture=False,
                      mask=handO([(136, 120), (198, 66), (258, 46), (292, 40), (334, 56), (384, 76), (424, 96),
                                  (482, 106), (564, 106), (586, 140), (524, 182), (484, 208), (456, 234), (560, 186),
                                  (576, 232), (484, 304), (404, 344), (362, 336), (322, 354), (282, 384), (200, 404),
                                  (66, 410), (54, 380), (98, 348), (178, 318), (226, 290), (176, 252), (146, 202)])),
    # head on the right, facing right: flipped
    "swsh9-112": dict(kind="rare", sprite="haxorus", flip=True, scene="the cliff under a blue sky", texture=False,
                      mask=handO([(6, 190), (26, 148), (78, 106), (128, 86), (200, 66), (260, 76), (298, 36),
                                  (318, 10), (402, 10), (452, 26), (502, 36), (562, 46), (614, 88), (616, 162),
                                  (584, 194), (564, 242), (524, 304), (472, 324), (444, 342), (454, 382), (434, 416),
                                  (86, 416), (76, 352), (56, 292), (26, 252)])),
    # head on the left, facing left, as the sprite: unflipped
    "swsh9-113": dict(kind="rare", sprite="druddigon", scene="the sunlit cave", texture=False,
                      mask=handO([(40, 342), (78, 298), (136, 268), (126, 188), (146, 136), (188, 106), (238, 100),
                                  (276, 76), (296, 26), (328, 10), (462, 16), (562, 86), (606, 118), (574, 180),
                                  (564, 250), (574, 300), (564, 372), (522, 400), (280, 404), (178, 400), (118, 374),
                                  (46, 374)])),
    # diving, beak down-left, as the sprite faces left: unflipped
    "swsh9-119": dict(kind="rare", sprite="staraptor", scene="the sky over the green valley",
                      mask=handO([(2, 200), (38, 176), (150, 166), (228, 156), (266, 106), (296, 46), (338, 20),
                                  (400, 10), (470, 16), (560, 20), (640, 26), (640, 94), (560, 94), (482, 90),
                                  (446, 122), (426, 202), (394, 244), (334, 274), (304, 322), (296, 362), (276, 406),
                                  (226, 406), (196, 342), (184, 272), (148, 246), (18, 250)])),
    # Incarnate Forme (the genie cloud, verified on the scan); frontal, arm flexed on the right: unflipped
    # (ambiguous). The hole of the tail ring is scene, so fill=False keeps it open
    "swsh9-126": dict(kind="rare", sprite="tornadus", scene="the whirlwind over the volcano", texture=False,
                      mask=handO([(196, 60), (258, 36), (308, 6), (402, 0), (442, 26), (482, 56), (540, 46),
                                  (592, 36), (626, 68), (626, 394), (562, 414), (218, 414), (196, 342), (206, 280),
                                  (186, 200), (176, 120)],
                                 [(2, 120), (16, 46), (68, 10), (152, 6), (214, 38), (246, 100), (246, 160),
                                  (220, 222), (206, 290), (216, 362), (184, 406), (36, 406), (4, 332), (2, 250)],
                                 cut_after=[[(78, 92), (130, 64), (172, 82), (184, 148), (180, 228), (166, 286),
                                             (130, 314), (84, 306), (72, 200)]], fill=False)),
}

if __name__ == "__main__":
    brsbatch.main(GROUP, TABLE)
