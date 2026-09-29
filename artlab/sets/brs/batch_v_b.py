r"""Brilliant Stars group `v_b`: Rare Holo V (kind `v`, Charizard V 17's recipe) and Rare Holo VMAX (kind `vmax`,
Kingler VMAX 29's recipe). Hand masks in card px, read off work/grid_<n>.png.

  C:\Users\grego\repos\pokeshell\.venv\Scripts\python batch_v_b.py rembg|masks|quick|all [ids]
"""
import brsbatch

GROUP = "v_b"


def hand(*polys, **kw):
    """a pure hand mask: the polygon(s) are the Pokemon"""
    return dict(model=None, add=list(polys), **kw)


TABLE = {
    "swsh9-69": dict(kind="vmax", sprite="mimikyu", flip=True, text_y=615, texture=False, scene="the ghostly vortex",
                     mask=hand([(30, 615), (30, 95), (260, 95),
                                (330, 150), (380, 220), (430, 190), (450, 150), (440, 75), (520, 70), (600, 110),
                                (620, 200), (600, 290), (705, 320), (705, 615)])),
    "swsh9-88": dict(kind="v", sprite="honchkrow", flip=True, text_y=622, texture=False, scene="the moonlit feathers",
                     mask=hand([(30, 300), (60, 225), (110, 200), (175, 235), (240, 195), (300, 170), (420, 165),
                                (520, 200), (560, 270), (620, 290), (700, 250), (705, 560), (640, 590), (560, 622),
                                (30, 622)])),
    "swsh9-95": dict(kind="v", sprite="morpeko-hangry", text_y=620, texture=False, scene="the stadium lightning",
                     mask=hand([(150, 470), (135, 380), (160, 300), (205, 250), (255, 215), (285, 105), (355, 95),
                                (375, 195), (420, 225), (490, 195), (560, 185), (655, 225), (645, 285), (585, 320),
                                (625, 360), (605, 470), (565, 505), (525, 560), (505, 620), (165, 620), (115, 560),
                                (105, 480)])),
    "swsh9-96": dict(kind="v", sprite="aggron", flip=True, text_y=595, texture=False, scene="the rock slide",
                     mask=hand([(30, 285), (120, 275), (160, 155), (230, 125), (270, 90), (400, 95), (430, 155),
                                (490, 115), (605, 105), (625, 180), (700, 215), (695, 285), (640, 295), (615, 380),
                                (665, 445), (705, 465), (705, 595), (95, 595), (75, 500), (30, 470)])),
    "swsh9-97": dict(kind="vmax", sprite="aggron", flip=True, text_y=660, texture=False, scene="the dynamax swirl",
                     mask=hand([(30, 320), (30, 95), (330, 90), (440, 35), (500, 90), (520, 135), (565, 190), (545, 300), (565, 375),
                                (615, 425), (705, 465), (705, 660), (30, 660)])),
    "swsh9-105": dict(kind="v", sprite="zamazenta-crowned", flip=True, text_y=622, texture=False,
                      scene="the shield light",
                      mask=hand([(30, 175), (150, 105), (230, 105), (330, 145), (400, 145), (430, 95), (470, 155),
                                 (520, 95), (565, 150), (585, 250), (645, 320), (695, 380), (705, 480), (705, 622),
                                 (30, 622)])),
    "swsh9-106": dict(kind="v", sprite="flygon", text_y=652, texture=False, scene="the desert sky",
                      mask=hand([(40, 145), (120, 185), (250, 210), (330, 175), (375, 95), (455, 105), (455, 160),
                                 (505, 145), (565, 245), (705, 305), (705, 475), (620, 475), (565, 520), (565, 652),
                                 (465, 652), (400, 600), (250, 600), (120, 652), (75, 560), (15, 420)])),
    "swsh9-114": dict(kind="v", sprite="dracovish", text_y=568, texture=False, scene="the sunlit cliffs",
                      mask=hand([(45, 330), (85, 195), (150, 115), (230, 95), (295, 135), (380, 165), (460, 185),
                                 (565, 205), (575, 280), (505, 330), (545, 420), (565, 520), (525, 568), (155, 568),
                                 (145, 500), (55, 425)])),
    "swsh9-122": dict(kind="v", sprite="arceus", flip=True, text_y=655, texture=False, scene="the starburst",
                      mask=hand([(10, 610), (40, 375), (100, 275), (170, 245), (245, 275), (320, 295), (365, 275),
                                 (395, 185), (415, 105), (475, 115), (505, 195), (545, 235), (565, 330), (555, 425),
                                 (645, 495), (695, 600), (705, 655), (20, 655)])),
    "swsh9-128": dict(kind="v", sprite="drampa", text_y=680, dy=-6, texture=False, scene="the rocky ledge",
                      mask=hand([(40, 300), (70, 195), (150, 105), (260, 95), (475, 105), (535, 165), (585, 255),
                                 (655, 275), (705, 300), (705, 680), (255, 680), (215, 600), (125, 580), (85, 460),
                                 (40, 380)])),
}

if __name__ == "__main__":
    brsbatch.main(GROUP, TABLE)
