r"""Crown Zenith group `v`: the Rare Holo V cards (kind `v`, Leafeon V 13's recipe) and the Rare Holo VMAX cards
(kind `vmax`, Zeraora VMAX 54's recipe). Masks in card px, read off work/grid_<n>.png.

  ..\..\..\.venv\Scripts\python batch_v.py rembg|masks|quick|all [ids]
"""
import czbatch

GROUP = "v"


def hand(*polys, **kw):
    """a pure hand mask: the polygon(s) are the Pokemon (every segmenter takes the scene)"""
    return dict(model=None, add=list(polys), **kw)


def model(name, y1, hull=None, **kw):
    """a rembg model inside the art window down to the text (and a hand hull when given)"""
    d = dict(model=name, win=(30, 92, 710, y1), keep=kw.pop("keep", 1), close=kw.pop("close", 3), **kw)
    if hull:
        d["hull"] = hull
    return d


TABLE = {
    "swsh12pt5-18": dict(kind="v", sprite="charizard", flip=True, text_y=680, texture=False, scene="the firestorm",
                         mask=hand([(30, 669), (30, 420), (90, 320), (170, 220), (240, 130), (250, 90),
                                    (590, 90), (600, 190),
                                    (640, 220), (645, 285), (615, 315), (625, 400), (605, 450), (665, 460),
                                    (705, 520), (705, 669)])),
    "swsh12pt5-22": dict(kind="v", sprite="simisear", text_y=628, scene="the fire swirl",
                         mask=hand([(40, 300), (50, 200), (90, 160), (115, 200), (170, 190), (160, 130), (200, 90),
                                    (270, 100), (330, 110), (390, 90), (445, 118), (475, 130), (525, 150),
                                    (545, 210), (505, 270), (515, 315), (565, 330), (645, 350), (700, 400),
                                    (705, 640), (145, 640), (135, 560), (155, 450), (175, 400), (165, 330),
                                    (110, 345), (60, 335)])),
    "swsh12pt5-37": dict(kind="v", sprite="kyogre", text_y=598, W=66, S=10.0, H=53, dy=-8, texture=False, scene="the open sea",
                         mask=model("isnet-general-use", 610, close=5,
                                    hull=[(30, 440), (125, 360), (145, 230), (195, 145), (280, 115), (360, 90),
                                          (565, 90), (605, 150), (625, 200), (605, 260), (655, 330), (690, 420),
                                          (625, 485), (605, 610), (30, 610)])),
    "swsh12pt5-38": dict(kind="v", sprite="glaceon", flip=True, text_y=682, texture=False, scene="the ice field",
                         mask=hand([(30, 300), (100, 250), (250, 200), (330, 150), (420, 110), (480, 90), (640, 90),
                                    (695, 160), (685, 300), (645, 350), (705, 380), (705, 475), (625, 485),
                                    (625, 600), (605, 669), (475, 669), (455, 600), (300, 640), (150, 669),
                                    (30, 669)])),
    "swsh12pt5-45": dict(kind="v", sprite="rotom", text_y=598, scene="the static haze",
                         mask=model("isnet-general-use", 610, close=5)),
    "swsh12pt5-53": dict(kind="v", sprite="zeraora", text_y=698, texture=False, scene="the lightning",
                         mask=hand([(30, 300), (150, 225), (170, 155), (260, 195), (300, 105), (385, 95),
                                    (470, 155), (540, 115), (600, 90), (705, 90), (705, 265), (565, 300),
                                    (525, 420), (565, 480), (625, 450), (705, 470), (705, 669), (30, 669)])),
    "swsh12pt5-60": dict(kind="v", sprite="mew", flip=True, text_y=645, strike=True, scene="the neon city",
                         mask=dict(model="u2net", win=(30, 165, 710, 650), keep=1, close=4)),
    "swsh12pt5-65": dict(kind="v", sprite="hatterene", text_y=645, texture=False, scene="the dark forest",
                         mask=hand([(40, 250), (60, 160), (150, 105), (260, 105), (330, 145), (420, 105),
                                    (560, 90), (665, 125), (705, 200), (705, 305), (625, 385), (525, 425),
                                    (475, 500), (485, 645), (245, 645), (225, 565), (95, 535), (35, 430)])),
    "swsh12pt5-66": dict(kind="vmax", sprite="hatterene-gmax", text_y=640, texture=False, scene="the psychic storm",
                         mask=dict(model="u2net", win=(0, 74, 734, 650), keep=2, close=5)),
    "swsh12pt5-95": dict(kind="v", sprite="zacian-crowned", flip=True, text_y=615, texture=False,
                         scene="the sword light",
                         mask=hand([(30, 130), (80, 90), (260, 90), (330, 115), (430, 125), (485, 175),
                                    (565, 195), (625, 255), (685, 325), (705, 400), (705, 485), (655, 525),
                                    (625, 615), (495, 615), (415, 525), (375, 485), (300, 485), (200, 425),
                                    (100, 425), (30, 385)])),
    "swsh12pt5-98": dict(kind="v", sprite="zamazenta-crowned", text_y=632, scene="the shield light", texture=False,
                         mask=hand([(30, 180), (150, 160), (180, 90), (560, 90), (580, 160), (660, 160),
                                    (705, 250), (705, 640), (120, 640), (80, 570), (30, 530)])),
    "swsh12pt5-100": dict(kind="v", sprite="rayquaza", text_y=640, strike=True, scene="the sky",
                          mask=model("isnet-general-use", 650, close=5,
                                     hull=[(30, 300), (60, 195), (120, 145), (150, 95), (250, 115), (330, 135),
                                           (425, 155), (475, 215), (560, 255), (640, 285), (710, 315), (710, 650),
                                           (555, 650), (465, 560), (395, 485), (300, 505), (150, 505),
                                           (30, 525)])),
    "swsh12pt5-101": dict(kind="vmax", sprite="rayquaza", text_y=570, strike=True, texture=False,
                          scene="the dynamax storm",
                          mask=hand([(20, 420), (60, 330), (130, 300), (170, 230), (160, 160), (250, 135),
                                     (350, 90), (420, 105), (470, 145), (560, 145), (640, 115), (705, 150),
                                     (705, 305), (645, 335), (625, 420), (625, 580), (395, 580), (345, 540),
                                     (300, 500), (200, 485), (130, 475), (80, 525), (20, 505)])),
    "swsh12pt5-102": dict(kind="vmax", sprite="rayquaza", text_y=570, strike=True, texture=False,
                          scene="the dynamax storm",
                          mask=hand([(295, 300), (325, 200), (415, 140), (415, 90), (710, 90), (710, 475),
                                     (625, 425), (565, 505), (465, 585), (325, 585), (295, 450)],
                                    [(15, 200), (60, 135), (150, 105), (250, 90), (305, 140), (285, 235),
                                     (205, 245), (205, 585), (15, 585)], keep=2)),
    "swsh12pt5-103": dict(kind="v", sprite="duraludon", text_y=668, strike=True, texture=False,
                          scene="the rock blast",
                          mask=hand([(30, 500), (120, 355), (220, 295), (295, 275), (315, 175), (355, 115),
                                     (420, 95), (485, 125), (505, 195), (560, 225), (705, 185), (705, 335),
                                     (605, 345), (565, 380), (605, 520), (565, 668), (30, 668)])),
    "swsh12pt5-104": dict(kind="vmax", sprite="duraludon-gmax", text_y=612, strike=True, texture=False,
                          scene="the rainbow storm",
                          mask=hand([(355, 150), (375, 90), (425, 90), (455, 125), (475, 185), (535, 195),
                                     (565, 240), (475, 262), (485, 325), (565, 315), (575, 390), (525, 410),
                                     (535, 435), (600, 395), (705, 415), (705, 612), (245, 612), (235, 565),
                                     (150, 545), (55, 505), (35, 400), (120, 375), (200, 415), (245, 395),
                                     (265, 325), (305, 315), (325, 255), (295, 235), (315, 165)])),
    "swsh12pt5-108": dict(kind="v", sprite="eevee", text_y=695, texture=False, grow=8, scene="the gust",
                          mask=model("u2net", 700, close=4,
                                     hull=[(30, 195), (100, 165), (230, 195), (360, 95), (435, 90), (455, 150),
                                           (475, 265), (500, 255), (600, 105), (710, 145), (710, 425),
                                           (605, 445), (525, 475), (505, 565), (485, 700), (375, 700),
                                           (295, 605), (200, 565), (75, 545), (35, 480), (95, 435), (195, 305),
                                           (120, 265), (35, 245)])),
    "swsh12pt5-113": dict(kind="v", sprite="regigigas", text_y=695, W=62, S=10.645, H=54, texture=False, scene="the hilltop",
                          mask=hand([(30, 260), (150, 180), (180, 105), (300, 90), (360, 105), (420, 95),
                                     (470, 125), (540, 155), (600, 165), (705, 275), (705, 475), (620, 455),
                                     (500, 475), (400, 525), (330, 565), (250, 668), (30, 668)])),
    "swsh12pt5-116": dict(kind="v", sprite="stoutland", flip=True, text_y=672, texture=False, scene="the flower garden",
                          mask=model("isnet-general-use", 680, close=5)),
    "swsh12pt5-120": dict(kind="v", sprite="greedent", flip=True, text_y=672, texture=False, scene="the berry nest",
                          mask=hand([(140, 500), (200, 420), (280, 330), (290, 240), (320, 195), (420, 145),
                                     (455, 160), (475, 240), (560, 225), (595, 300), (645, 350), (685, 500),
                                     (645, 565), (500, 545), (300, 545), (200, 565)],
                                    [(30, 120), (100, 90), (565, 90), (565, 205), (420, 150), (300, 200),
                                     (260, 300), (200, 400), (120, 425), (30, 405)], keep=2)),
}

if __name__ == "__main__":
    czbatch.main(GROUP, TABLE)
