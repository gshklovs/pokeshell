r"""Lost Origin Trainer Gallery Rare Holo (TG01-TG11 minus the ladder's Charizard TG03): the gallery painting
(lorcards.build_gallery, the cz Lapras GG05 recipe, as the ladder's Charizard TG03) per card. Only the card's own
Pokemon is painted out; the trainers and other Pokemon in the paintings stay as scenery. Coordinates are card px
read off work/grid_<n>.png.

  ..\..\..\.venv\Scripts\python batch_tg.py rembg|masks|quick|all [ids]
"""
import lorbatch
import lorcards as C

GROUP = "tg"
G = "swsh11tg-"


def row(sprite, text_y, mask, **kw):
    return dict(kind="gallery", sprite=sprite, text_y=text_y, mask=mask, **kw)


def hand(*polys, close=0, **kw):
    """poly_only: the mask is the hand polygon(s)"""
    return dict(model=None, add=list(polys), close=close, keep=len(polys), **kw)


TABLE = {
    G + "TG01": row("parasect", 548,
                    hand([(282, 500), (288, 458), (325, 425), (385, 378), (400, 340), (428, 322), (468, 275), (520, 250),
                          (600, 245), (662, 262), (705, 280), (705, 565), (282, 565)]),
                    texture=False, scene="the mushroom forest with the researcher"),
    G + "TG02": row("roserade", 565,
                    hand([(282, 278), (285, 225), (316, 178), (380, 144), (424, 122), (492, 142), (558, 184),
                          (604, 255), (705, 245), (705, 575), (285, 575), (285, 498), (340, 470), (378, 432),
                          (348, 410), (296, 338)]),
                    texture=False, scene="the forest with Gardenia"),
    G + "TG04": row("chandelure", 548,
                    hand([(270, 214), (306, 160), (380, 130), (455, 138), (505, 100), (570, 90), (705, 90),
                          (705, 560), (400, 560), (395, 530), (388, 433),
                          (388, 338), (356, 312), (300, 282)]),
                    texture=False, scene="the library with Shauntal"),
    G + "TG05": row("pikachu", 548,
                    hand([(30, 176), (50, 172), (122, 216), (163, 220), (236, 154), (260, 172), (270, 234),
                          (312, 276), (312, 338), (345, 345), (368, 380), (368, 440), (322, 458), (302, 434), (285, 472), (214, 486), (200, 556),
                          (30, 556), (30, 468), (90, 460), (110, 449), (98, 400), (114, 327), (94, 280), (30, 224)]),
                    flip=True, dy=-4, texture=False, scene="the forest nap with Akari"),
    G + "TG06": row("gengar", 548,
                    hand([(30, 250), (90, 256), (150, 262), (205, 215), (232, 244), (275, 230), (310, 238), (345, 238),
                          (400, 222), (445, 215), (450, 280), (462, 330), (478, 380), (488, 440), (490, 500),
                          (482, 545), (495, 565), (30, 565)]),
                    flip=True, texture=False, scene="the laundry camp"),
    G + "TG07": row("banette", 575,
                    hand([(30, 318), (82, 318), (104, 348), (200, 320), (265, 300), (350, 276), (372, 255), (455, 285),
                          (520, 288), (570, 238), (605, 280), (640, 296), (705, 296), (705, 590), (250, 590),
                          (258, 530), (318, 500), (308, 470), (212, 470), (112, 464), (75, 428), (40, 404),
                          (30, 392)]),
                    flip=True, strike=True, texture=False, scene="the gym with Phoebe"),
    G + "TG08": row("arcanine-hisui", 578,
                    hand([(30, 184), (128, 150), (245, 110), (326, 130), (359, 100), (505, 100), (535, 165),
                          (578, 235), (669, 256), (705, 290), (705, 590), (348, 590), (306, 547), (314, 492),
                          (290, 452), (268, 437), (204, 428), (128, 424), (70, 404), (30, 350)]),
                    texture=False, scene="the volcano with the young trainer"),
    G + "TG09": row("spiritomb", 548,
                    hand([(45, 118), (110, 90), (460, 90), (526, 134), (542, 202), (576, 276), (584, 362),
                          (524, 380), (460, 388), (428, 436), (404, 500), (386, 535), (269, 552), (160, 535),
                          (94, 502), (53, 444), (30, 368), (30, 208)]),
                    texture=False, scene="the dusk window with the twins"),
    G + "TG10": row("snorlax", 548,
                    hand([(305, 90), (690, 90), (695, 200), (700, 290), (705, 330), (705, 565), (134, 565),
                          (134, 494), (215, 468), (215, 390), (240, 332), (248, 210), (272, 176), (305, 136)]),
                    texture=False, scene="the noodle stall with Grimsley"),
    G + "TG11": row("castform", 548,
                    hand([(118, 90), (462, 90), (454, 150), (428, 184), (412, 253), (420, 320), (386, 363),
                          (328, 380), (272, 396), (252, 470), (196, 496), (140, 480), (102, 436), (60, 386),
                          (68, 334), (68, 276), (102, 242), (110, 170)]),
                    flip=True, texture=False, scene="the chalkboard with the teacher"),
}

# the look per card, from its painting: frame (text-half colour), rim_col (aura), vig (vignette tint), star (palette)
LOOK = {
    "TG01": dict(frame="#e0506a", rim_col=(1.0, 0.95, 0.85), vig=(0.04, 0.06, 0.03), star=C.GOLD_STAR),
    "TG02": dict(frame="#6cc060", rim_col=(0.95, 1.0, 0.9), vig=(0.02, 0.07, 0.03), star=C.GOLD_STAR),
    "TG04": dict(frame="#8c7cd8", rim_col=(0.88, 0.9, 1.0), vig=(0.05, 0.02, 0.1), star=C.WHITE_STAR),
    "TG05": dict(frame="#f6d02c", rim_col=(1.0, 0.97, 0.8), vig=(0.03, 0.06, 0.03), star=C.GOLD_STAR),
    "TG06": dict(frame="#9a78d0", rim_col=(1.0, 0.92, 0.95), vig=(0.06, 0.03, 0.08), star=C.PINK_STAR),
    "TG07": dict(frame="#b070d0", rim_col=(1.0, 0.9, 1.0), vig=(0.06, 0.02, 0.1), star=C.PINK_STAR),
    "TG08": dict(frame="#e05040", rim_col=(1.0, 0.9, 0.8), vig=(0.08, 0.03, 0.02), star=C.GOLD_STAR),
    "TG09": dict(frame="#c060d0", rim_col=(1.0, 0.92, 1.0), vig=(0.06, 0.02, 0.08), star=C.PINK_STAR),
    "TG10": dict(frame="#4a90b0", rim_col=(0.92, 0.97, 1.0), vig=(0.02, 0.05, 0.06), star=C.WHITE_STAR),
    "TG11": dict(frame="#78b090", rim_col=(1.0, 1.0, 1.0), vig=(0.03, 0.06, 0.05), star=C.PASTEL_STAR),
}
for _n, _l in LOOK.items():
    TABLE[G + _n].update(_l)

if __name__ == "__main__":
    lorbatch.main(GROUP, TABLE)
