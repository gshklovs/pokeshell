r"""Brilliant Stars Trainer Gallery Rare Holo (TG01-TG12 minus the ladder's Eevee TG11): the gallery painting
(brscards.build_gallery, the cz Lapras GG05 recipe, as the ladder's Eevee TG11) per card. Only the card's own
Pokemon is painted out; the trainers and other Pokemon in the paintings stay as scenery. Coordinates are card px
read off work/grid_<n>.png.

  ..\..\..\.venv\Scripts\python batch_tg.py rembg|masks|quick|all [ids]
"""
import brsbatch
import brscards as C
import sprites  # noqa: E402 (on the path once brsbatch / brslib is imported)

# Shared-code workaround (local, as cz batch_secret.py): the vendor `alcremie` shiny sprite has one pixel (row 20,
# col 6) set where the regular sprite is transparent, which evlib.Sprite asserts against. The shiny load is patched
# here to drop such pixels; the regular sprite (the one served) stays pixel-exact.
_load = sprites.load


def _load_fixed(name, shiny=False):
    s = _load(name, shiny=shiny)
    if not shiny:
        return s
    n = _load(name)
    return [[None if a is None else (c if c is not None else a) for a, c in zip(ra, rc)] for ra, rc in zip(n, s)]


sprites.load = _load_fixed

GROUP = "tg"
G = "swsh9tg-"


def row(sprite, text_y, mask, **kw):
    return dict(kind="gallery", sprite=sprite, text_y=text_y, mask=mask, **kw)


def hand(*polys, close=0, **kw):
    """poly_only: the mask is the hand polygon(s)"""
    return dict(model=None, add=list(polys), close=close, keep=len(polys), **kw)


TABLE = {
    G + "TG01": row("flareon", 545,
                    hand([(25, 245), (90, 240), (160, 265), (185, 170), (235, 165), (300, 205), (325, 120),
                          (340, 40), (390, 40), (395, 150), (400, 265), (410, 325), (430, 365), (425, 430),
                          (400, 470), (395, 520), (405, 565), (30, 565), (35, 420), (75, 335), (30, 300)]),
                    flip=True, scene="the forest clearing with Blue"),
    G + "TG02": row("vaporeon", 545,
                    hand([(262, 318), (300, 325), (332, 238), (350, 200), (368, 212), (382, 255), (420, 245),
                          (472, 262), (482, 325), (520, 310), (560, 295), (605, 298), (645, 318), (645, 348),
                          (615, 358), (625, 400), (625, 520), (605, 565), (515, 565), (488, 530), (440, 535),
                          (378, 475), (328, 465), (296, 445), (280, 400), (262, 362)]),
                    scene="the forest stream with Gary"),
    G + "TG03": row("octillery", 545,
                    hand([(325, 245), (358, 212), (420, 186), (470, 170), (522, 172), (575, 196), (598, 225),
                          (580, 252), (560, 300), (585, 338), (615, 378), (645, 420), (650, 472), (622, 505),
                          (588, 515), (556, 485), (528, 448), (478, 448), (472, 475), (430, 495), (398, 475),
                          (348, 485), (315, 472), (325, 420), (350, 390), (340, 340), (330, 300)]),
                    strike=True, scene="the harbour pier with the angler"),
    G + "TG04": row("jolteon", 545,
                    hand([(200, 150), (300, 118), (420, 165), (470, 105), (560, 65), (620, 75), (705, 95),
                          (705, 565), (250, 565), (248, 500), (295, 440), (355, 380), (300, 300), (378, 240),
                          (258, 210)]),
                    flip=True, texture=False, scene="the lightning storm with Gary"),
    G + "TG05": row("zekrom", 590,
                    dict(model=None, add=[[(78, 232), (108, 210), (98, 88), (160, 65), (262, 118), (330, 198),
                                           (430, 108), (520, 58), (640, 38), (705, 58), (705, 615), (120, 615),
                                           (128, 520), (175, 420), (108, 332), (78, 292)]],
                         cut_after=[[(298, 242), (330, 212), (382, 226), (470, 256), (482, 298), (425, 312),
                                     (432, 350), (405, 398), (432, 438), (472, 478), (492, 540), (482, 582),
                                     (452, 588), (428, 522), (380, 472), (330, 442), (268, 425), (256, 400),
                                     (296, 370), (306, 300)]], fill=False, keep=4),
                    texture=False, scene="the sunset flight with N"),
    G + "TG06": row("dusknoir", 545,
                    hand([(142, 160), (180, 135), (242, 140), (262, 198), (282, 228), (312, 258), (342, 278),
                          (392, 298), (442, 328), (472, 378), (492, 440), (560, 465), (642, 495), (705, 555),
                          (705, 565), (30, 565), (30, 470), (38, 368), (80, 326), (140, 316), (168, 278),
                          (148, 220)]),
                    texture=False, scene="the ghostly night with Morty"),
    G + "TG07": row("dedenne", 640,
                    hand([(58, 150), (78, 92), (140, 76), (200, 106), (230, 86), (290, 60), (372, 66), (414, 108),
                          (414, 188), (444, 238), (484, 278), (494, 360), (484, 450), (474, 522), (434, 564),
                          (384, 604), (300, 626), (228, 604), (168, 564), (116, 504), (76, 422), (56, 330),
                          (66, 230)]),
                    scene="the pop-art stage with Marnie"),
    G + "TG08": row("alcremie", 545,
                    hand([(380, 228), (408, 196), (440, 166), (480, 146), (540, 126), (602, 136), (644, 178),
                          (664, 228), (674, 300), (664, 350), (674, 420), (656, 470), (646, 540), (566, 565),
                          (360, 565), (368, 500), (358, 440), (398, 412), (388, 372), (408, 330), (378, 290)]),
                    scene="the cafe with the cafe master"),
    G + "TG09": row("ariados", 545,
                    hand([(288, 42), (362, 42), (382, 118), (460, 106), (530, 36), (610, 36), (625, 150), (650, 230),
                          (705, 262), (705, 470), (682, 520), (705, 565), (360, 565),
                          (328, 522), (298, 472), (308, 440), (298, 402), (276, 380), (286, 330), (326, 300),
                          (296, 272), (266, 240), (330, 226), (338, 160), (306, 110)]),
                    scene="the attic web with Janine"),
    G + "TG10": row("houndoom", 545,
                    hand([(38, 300), (88, 198), (108, 138), (148, 106), (158, 56), (202, 66), (262, 96), (330, 46),
                          (422, 46), (504, 78), (512, 122), (472, 142), (422, 182), (372, 232), (352, 300),
                          (342, 350), (302, 382), (312, 450), (332, 500), (332, 565), (30, 565), (30, 380)],
                         [(335, 135), (378, 90), (430, 66), (478, 52), (515, 34), (535, 18), (555, 26), (552, 62),
                          (526, 94), (496, 124), (476, 152), (460, 186), (434, 218), (408, 244), (376, 260),
                          (345, 255)]),
                    strike=True, texture=False, scene="the flames with Grimsley"),
    G + "TG12": row("oranguru", 545,
                    hand([(228, 418), (268, 386), (320, 366), (390, 376), (440, 396), (470, 366), (530, 350),
                          (592, 360), (634, 396), (664, 438), (694, 478), (705, 565), (228, 565), (228, 500),
                          (248, 468)]),
                    scene="the camper van with the hammock"),
}

# the look per card, from its painting: frame (text-half colour), rim_col (aura), vig (vignette tint), star (palette)
LOOK = {
    "TG01": dict(frame="#f08a50", rim_col=(1.0, 0.9, 0.75), vig=(0.04, 0.06, 0.03), star=C.GOLD_STAR),
    "TG02": dict(frame="#5cb8e0", rim_col=(0.85, 0.95, 1.0), vig=(0.02, 0.06, 0.06), star=C.WHITE_STAR),
    "TG03": dict(frame="#e05050", rim_col=(1.0, 0.92, 0.9), vig=(0.02, 0.05, 0.1), star=C.WHITE_STAR),
    "TG04": dict(frame="#f0d040", rim_col=(1.0, 1.0, 0.8), vig=(0.04, 0.05, 0.12), star=C.GOLD_STAR),
    "TG05": dict(frame="#7a78a8", rim_col=(0.9, 0.9, 1.0), vig=(0.06, 0.03, 0.1), star=C.GOLD_STAR),
    "TG06": dict(frame="#8c88c0", rim_col=(0.85, 0.9, 1.0), vig=(0.02, 0.03, 0.1), star=C.WHITE_STAR),
    "TG07": dict(frame="#f0a830", rim_col=(1.0, 0.95, 0.8), vig=(0.1, 0.02, 0.06), star=C.PINK_STAR),
    "TG08": dict(frame="#f0b6c8", rim_col=(1.0, 0.92, 0.95), vig=(0.08, 0.03, 0.03), star=C.PINK_STAR),
    "TG09": dict(frame="#d04858", rim_col=(1.0, 0.9, 0.8), vig=(0.08, 0.04, 0.02), star=C.GOLD_STAR),
    "TG10": dict(frame="#e05040", rim_col=(1.0, 0.85, 0.75), vig=(0.1, 0.02, 0.02), star=C.GOLD_STAR),
    "TG12": dict(frame="#b070d0", rim_col=(1.0, 0.95, 1.0), vig=(0.08, 0.02, 0.08), star=C.PINK_STAR),
}
for _n, _l in LOOK.items():
    TABLE[G + _n].update(_l)

if __name__ == "__main__":
    brsbatch.main(GROUP, TABLE)
