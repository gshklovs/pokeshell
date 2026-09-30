r"""Lost Origin group `v`: Rare Holo V (kind `v`, the Giratina V 130 ladder recipe). The only VMAX (Kyurem 49) is in
the ladder. Hand masks in card px read off work/grid_<n>.png (these V arts fill the window; every segmenter takes
the scene), smooth fills (`texture=False`) against ghosts.

  C:\Users\grego\repos\pokeshell\.venv\Scripts\python batch_v.py rembg|masks|quick|all [ids]
"""
import lorbatch

GROUP = "v"


def hand(*polys, **kw):
    """a pure hand mask: the polygon(s) are the Pokemon"""
    return dict(model=None, add=list(polys), **kw)


TABLE = {
    "swsh11-27": dict(kind="v", sprite="delphox", text_y=565, texture=False, scene="the psychic flames",
                      mask=hand([(30, 80), (705, 80), (705, 330), (655, 340), (640, 420), (660, 480), (640, 565), (30, 565),
                                 (30, 480), (80, 420), (65, 330), (30, 300)])),
    "swsh11-48": dict(kind="v", sprite="kyurem", flip=True, text_y=690, dy=-5, texture=False, scene="the ice cavern",
                      mask=hand([(30, 115), (120, 110), (200, 185), (260, 225), (330, 290), (390, 240), (410, 150),
                                 (460, 95), (705, 95), (705, 690), (30, 690)])),
    "swsh11-56": dict(kind="v", sprite="magnezone", text_y=565, texture=False, scene="the plasma sphere",
                      mask=hand([(30, 200), (170, 190), (285, 205), (295, 145), (365, 145), (375, 225), (435, 245),
                                 (485, 185), (550, 195), (550, 280), (600, 325), (705, 335), (705, 565), (30, 565)])),
    "swsh11-58": dict(kind="v", sprite="rotom", text_y=595, texture=False, scene="the neon static",
                      mask=hand([(55, 420), (65, 335), (135, 255), (200, 205), (285, 100), (360, 100), (385, 225),
                                 (400, 265), (530, 250), (540, 300), (440, 360), (425, 470), (395, 560), (340, 600),
                                 (90, 600), (60, 520)])),
    "swsh11-82": dict(kind="v", sprite="enamorus", text_y=597, texture=False, scene="the heart meadow",
                      mask=hand([(115, 290), (165, 235), (195, 135), (260, 95), (335, 115), (305, 200), (325, 270),
                                 (385, 335), (470, 375), (520, 320), (570, 330), (570, 405), (475, 425), (425, 435),
                                 (405, 520), (425, 597), (105, 597), (115, 540), (195, 495), (205, 420), (145, 335)],
                                [(30, 85), (705, 85), (705, 545), (555, 565), (555, 470), (635, 395), (645, 285),
                                 (595, 195), (500, 155), (380, 145), (250, 165), (150, 205), (100, 265), (80, 330),
                                 (30, 345)])),
    "swsh11-92": dict(kind="v", sprite="aerodactyl", text_y=700, dy=-6, texture=False, scene="the volcanic jungle",
                      mask=hand([(55, 150), (130, 115), (205, 105), (365, 145), (440, 225), (560, 205), (705, 175),
                                 (705, 345), (620, 375), (555, 400), (620, 420), (705, 470), (705, 700), (195, 700),
                                 (195, 640), (290, 620), (135, 625), (105, 540), (155, 400), (195, 290), (85, 195)])),
    "swsh11-118": dict(kind="v", sprite="drapion", text_y=597, H=55, dy=-4, texture=False, scene="the dusk vortex",
                       mask=hand([(30, 415), (100, 375), (200, 385), (225, 330), (195, 280), (245, 235), (285, 145),
                                  (330, 105), (400, 115), (420, 150), (440, 95), (560, 95), (610, 150), (625, 255),
                                  (565, 295), (525, 340), (565, 420), (525, 505), (405, 525), (355, 560), (345, 597),
                                  (30, 597)])),
    "swsh11-129": dict(kind="v", sprite="perrserker", text_y=690, texture=False, scene="the scrapyard storm",
                       mask=hand([(30, 395), (85, 375), (95, 300), (55, 165), (130, 185), (220, 135), (305, 135),
                                  (385, 185), (460, 175), (705, 155), (705, 445), (565, 485), (565, 565), (505, 645),
                                  (475, 690), (155, 690), (165, 600), (115, 565), (30, 565)])),
    "swsh11-135": dict(kind="v", sprite="goodra-hisui", flip=True, text_y=595, texture=False, scene="the waterfall",
                       mask=hand([(30, 85), (705, 85), (705, 595), (30, 595), (30, 300), (55, 200)])),
    "swsh11-137": dict(kind="v", sprite="pidgeot", flip=True, text_y=620, texture=False, scene="the forest sky",
                       mask=hand([(30, 225), (100, 205), (160, 145), (250, 105), (420, 115), (495, 150), (530, 185),
                                  (600, 145), (705, 135), (705, 405), (600, 435), (565, 475), (535, 620), (245, 620),
                                  (195, 545), (30, 545)])),
    "swsh11-146": dict(kind="v", sprite="zoroark-hisui", text_y=620, texture=False, scene="the moonlit spirits",
                       mask=hand([(30, 85), (520, 85), (560, 150), (560, 235), (620, 215), (705, 225), (705, 620),
                                  (30, 620)])),
}

if __name__ == "__main__":
    lorbatch.main(GROUP, TABLE)
