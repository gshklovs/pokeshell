r"""Brilliant Stars group `v_a`: Rare Holo V cards (kind `v`, the Charizard V 17 ladder recipe). Masks are hand hulls
in card px read off work/grid_<n>.png (every segmenter takes the scene on these card-filling V arts).

  ..\..\..\.venv\Scripts\python batch_v_a.py rembg|masks|quick|all [ids]
"""
import brsbatch

GROUP = "v_a"


def hand(*polys, **kw):
    """a pure hand mask: the polygon(s) are the Pokemon"""
    return dict(model=None, add=list(polys), **kw)


TABLE = {
    "swsh9-13": dict(kind="v", sprite="shaymin-sky", flip=True, text_y=680, texture=False, scene="the petal rush",
                     mask=hand([(30, 180), (110, 140), (230, 110), (340, 100), (480, 100), (520, 170), (600, 190),
                                (680, 220), (705, 290), (705, 460), (660, 540), (600, 600), (560, 680), (130, 680),
                                (60, 630), (30, 580)])),
    "swsh9-16": dict(kind="v", sprite="zarude", flip=True, text_y=598, texture=False, scene="the jungle vines",
                     mask=hand([(40, 150), (150, 95), (345, 95), (490, 95), (560, 150), (705, 160),
                                (715, 330), (650, 420), (600, 520), (570, 598), (30, 598), (30, 370), (110, 300),
                                (60, 240)])),
    "swsh9-22": dict(kind="v", sprite="entei", flip=True, text_y=622, texture=False, scene="the flame gale",
                     mask=hand([(30, 300), (90, 240), (150, 150), (250, 105), (420, 110), (500, 140), (560, 125),
                                (690, 150), (705, 250), (705, 500), (650, 622), (70, 622), (30, 560)])),
    "swsh9-27": dict(kind="v", sprite="simisear", text_y=628, texture=False, scene="the fire swirl",
                     mask=hand([(40, 215), (80, 160), (140, 185), (170, 150), (210, 105), (330, 105), (400, 125),
                                (470, 135), (570, 175), (550, 260), (620, 360), (705, 410), (705, 628), (290, 628),
                                (150, 570), (165, 420), (140, 335), (55, 305)])),
    "swsh9-28": dict(kind="v", sprite="kingler", flip=True, text_y=625, texture=False, scene="the beach whirlpool",
                     mask=hand([(30, 370), (100, 360), (125, 325), (95, 300), (105, 245), (155, 200), (135, 120),
                                (200, 95), (310, 95), (335, 150), (385, 105), (475, 150), (525, 175), (600, 295),
                                (565, 380), (615, 425), (705, 435), (705, 560), (565, 525), (400, 565), (250, 610),
                                (30, 610)])),
    "swsh9-40": dict(kind="v", sprite="lumineon", flip=True, text_y=600, texture=False, scene="the coral reef",
                     mask=hand([(30, 190), (160, 180), (250, 150), (330, 165), (345, 95), (425, 95), (445, 195),
                                (560, 215), (650, 185), (705, 220), (705, 340), (610, 365), (620, 500), (510, 595),
                                (360, 570), (270, 475), (240, 370), (190, 310), (30, 310)])),
    "swsh9-45": dict(kind="v", sprite="raichu", text_y=568, texture=False, scene="the lightning lab",
                     mask=hand([(30, 100), (235, 100), (280, 150), (330, 125), (430, 95), (550, 110), (570, 250),
                                (525, 330), (570, 380), (590, 460), (635, 530), (645, 568), (140, 568), (110, 470), (150, 380),
                                (140, 310), (30, 290)])),
    "swsh9-48": dict(kind="v", sprite="raikou", flip=True, text_y=625, texture=False, scene="the thunder storm",
                     mask=hand([(30, 380), (80, 335), (110, 290), (250, 265), (265, 195), (295, 105), (430, 105),
                                (530, 125), (590, 220), (610, 300), (705, 345), (705, 625), (80, 625), (30, 565)])),
    "swsh9-57": dict(kind="v", sprite="granbull", text_y=650, texture=False, scene="the rock burst",
                     mask=hand([(30, 240), (55, 195), (120, 195), (150, 140), (265, 155), (300, 185), (420, 185),
                                (480, 200), (625, 205), (705, 225), (705, 330), (650, 340), (705, 415), (705, 650), (30, 650)])),
    "swsh9-64": dict(kind="v", sprite="whimsicott", flip=True, text_y=598, texture=False, scene="the cotton wind",
                     mask=hand([(85, 200), (145, 115), (250, 95), (455, 95), (570, 135), (650, 230), (690, 300),
                                (690, 360), (650, 470), (570, 525), (510, 598), (290, 598), (190, 505), (115, 435), (85, 330)])),
    "swsh9-68": dict(kind="v", sprite="mimikyu", text_y=565, texture=False, scene="the shadowed garden",
                     mask=hand([(285, 300), (325, 245), (395, 105), (455, 95), (545, 105), (565, 160), (530, 205),
                                (565, 255), (645, 295), (710, 335), (710, 520), (665, 565), (285, 565), (275, 420)],
                               ),
                     polys=[[(30, 200), (150, 185), (220, 290), (245, 450), (225, 565), (30, 565)]]),
}

if __name__ == "__main__":
    brsbatch.main(GROUP, TABLE)
