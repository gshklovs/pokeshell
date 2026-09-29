"""Brilliant Stars group `rare_a` (printed rarity Rare): the ladder Luxray 51 / evs Altaria 106 recipe (build_rare).

Every mask is a hand hull (model=None), traced on work/grid_<n>.png made with
`grid.py brs <n> --crop 40 80 700 510 --step 25` (660 x 430 card px shown at 900 x 586) and written in that grid
image's pixels; D() maps them to card px (as cz batch_rare.py does).

Shared-code workaround (local): every vendor `alcremie*` sprite has one pixel that is set in the regular sprite but
transparent in the shiny one, which evlib.Sprite asserts against. The shiny load is patched here to take the regular
colour at such pixels (cz batch_secret.py's dialga-origin fix); the regular sprite (the one served) stays pixel-exact.
"""
import brsbatch
import sprites  # noqa: E402 (on the path once brsbatch / brslib is imported)

_load = sprites.load


def _load_fixed(name, shiny=False):
    s = _load(name, shiny=shiny)
    if not shiny:
        return s
    n = _load(name)
    return [[(c if c is not None else a) if a is not None else None for a, c in zip(ra, rc)] for ra, rc in zip(n, s)]


sprites.load = _load_fixed

GROUP = "rare_a"
K = 900 / 660                                    # grid image px per card px


def D(*polys):
    return [[(round(40 + x / K), round(80 + y / K)) for x, y in p] for p in polys]


def hand(*polys, keep=1):
    return dict(model=None, add=D(*polys), keep=keep)


TABLE = {
    # faces left like the sprite
    "swsh9-4": dict(kind="rare", sprite="breloom", scene="the mushroom meadow",
                    mask=hand([(340, 130), (380, 85), (440, 80), (495, 115), (525, 180), (515, 250), (500, 300),
                               (510, 330), (530, 360), (540, 415), (570, 435), (640, 415), (700, 385), (730, 335),
                               (775, 322), (830, 335), (840, 385), (795, 410), (745, 425), (700, 465), (640, 495),
                               (560, 515), (470, 535), (380, 535), (295, 530), (240, 495), (240, 445), (275, 435),
                               (305, 405), (325, 360), (335, 330), (335, 300), (340, 260), (330, 220)])),
    # Plant Cloak, hanging frontal: unflipped (ambiguous)
    "swsh9-10": dict(kind="rare", sprite="wormadam", scene="hanging in the sunlit tree",
                     mask=hand([(385, 35), (425, 35), (430, 185), (500, 180), (565, 205), (605, 245), (615, 305),
                                (565, 345), (515, 400), (495, 455), (475, 505), (435, 540), (395, 540), (375, 495),
                                (345, 455), (305, 405), (285, 350), (295, 305), (265, 270), (285, 210), (330, 185),
                                (380, 185)])),
    # frontal: unflipped (ambiguous)
    "swsh9-11": dict(kind="rare", sprite="mothim", scene="the cottage garden",
                     mask=hand([(185, 35), (335, 35), (385, 135), (420, 175), (470, 135), (520, 125), (575, 145),
                                (605, 200), (605, 285), (700, 295), (765, 325), (775, 385), (700, 405), (610, 395),
                                (585, 405), (565, 445), (565, 485), (515, 480), (470, 445), (425, 455), (400, 495),
                                (365, 455), (325, 415), (295, 395), (235, 385), (200, 365), (195, 325), (245, 315),
                                (265, 295), (225, 230), (195, 150)])),
    # frontal: unflipped (ambiguous); Electivire at the left stays as scenery
    "swsh9-20": dict(kind="rare", sprite="magmortar", scene="the clash with Electivire", texture=False,
                     mask=hand([(245, 90), (300, 55), (365, 55), (400, 105), (440, 55), (525, 75), (565, 95),
                                (625, 105), (665, 150), (665, 230), (645, 280), (615, 300), (645, 355), (705, 395),
                                (725, 470), (725, 545), (560, 545), (465, 525), (395, 485), (325, 445), (295, 380),
                                (315, 300), (325, 250), (295, 220), (255, 190), (235, 140)])),
    # head at the left like the sprite
    "swsh9-31": dict(kind="rare", sprite="lapras", scene="the coral reef",
                     mask=hand([(115, 170), (180, 125), (290, 155), (300, 95), (380, 35), (470, 15), (560, 35),
                                (635, 65), (665, 150), (700, 175), (795, 155), (800, 225), (705, 265), (655, 275),
                                (630, 300), (725, 335), (805, 395), (810, 445), (740, 450), (620, 415), (560, 385),
                                (470, 335), (390, 335), (335, 345), (325, 400), (265, 475), (190, 535), (125, 505),
                                (115, 420), (125, 340), (165, 280), (205, 250), (125, 235)])),
    # frontal face; the antenna trails to the viewer's left on the card, to the right in the sprite: flipped
    "swsh9-41": dict(kind="rare", sprite="manaphy", flip=True, scene="the sunset sea",
                     mask=hand([(395, 210), (450, 165), (530, 135), (615, 155), (655, 210), (675, 260), (665, 320),
                                (705, 325), (765, 340), (725, 385), (620, 395), (615, 425), (585, 475), (515, 475),
                                (475, 425), (435, 395), (325, 375), (335, 335), (405, 325), (395, 290)],
                               [(155, 240), (200, 215), (250, 155), (320, 105), (420, 65), (530, 75), (565, 120),
                                (565, 175), (520, 145), (430, 115), (345, 145), (285, 195), (255, 260), (235, 305),
                                (165, 295)], keep=2)),
    # Ice Face (the ice cube head), upside down: unflipped (ambiguous); the Fusion Strike badge boxed out
    "swsh9-44": dict(kind="rare", sprite="eiscue", scene="the shattering ice", texture=False, boxes=[(468, 100, 690, 168)],
                     mask=hand([(239, 55), (300, 20), (382, 14), (436, 68), (450, 136), (546, 136), (641, 150), (689, 218),
                                (696, 341), (682, 436), (641, 518), (587, 559), (505, 559), (450, 532), (396, 505),
                                (327, 464), (286, 436), (259, 355), (232, 273), (218, 164)])),
    # near-frontal: unflipped (ambiguous); Magmortar at the right stays as scenery
    "swsh9-47": dict(kind="rare", sprite="electivire", scene="the clash with Magmortar", texture=False,
                     mask=hand([(295, 160), (380, 95), (475, 105), (565, 155), (615, 215), (645, 275), (705, 325),
                                (765, 355), (765, 425), (705, 445), (645, 475), (560, 475), (500, 485), (420, 485),
                                (355, 455), (305, 405), (275, 330), (245, 250)])),
    # body turned to the viewer's left like the sprite
    "swsh9-54": dict(kind="rare", sprite="clefable", scene="the misty pond",
                     mask=hand([(225, 270), (265, 230), (255, 105), (300, 105), (360, 115), (380, 85), (460, 65),
                                (520, 105), (600, 95), (655, 105), (605, 160), (565, 200), (655, 235), (705, 245),
                                (705, 290), (685, 330), (695, 370), (665, 435), (600, 475), (565, 455), (520, 435),
                                (430, 425), (320, 425), (225, 435), (215, 390), (265, 370), (255, 320), (235, 300)])),
    # faces right: flipped
    "swsh9-56": dict(kind="rare", sprite="mewtwo", flip=True, scene="the psychic storm",
                     mask=hand([(225, 475), (255, 365), (235, 335), (160, 335), (60, 375), (35, 340), (165, 285),
                                (255, 255), (335, 170), (325, 85), (360, 55), (425, 75), (465, 115), (520, 85),
                                (595, 115), (615, 195), (645, 235), (695, 255), (705, 305), (665, 345), (590, 355),
                                (560, 325), (520, 365), (420, 405), (365, 445), (335, 505), (280, 545), (235, 525)],
                               [(560, 190), (650, 180), (730, 230), (745, 320), (700, 385), (610, 385), (545, 340)],
                               keep=2)),
    # Vanilla Cream + Strawberry Sweet (white cream, red strawberries): `alcremie` (= vanilla-cream-strawberry);
    # near-frontal: unflipped (ambiguous); the chef and the cafe sign stay as scenery
    "swsh9-71": dict(kind="rare", sprite="alcremie", scene="the cafe front",
                     mask=hand([(325, 110), (390, 85), (460, 105), (500, 145), (560, 145), (625, 175), (685, 205),
                                (705, 270), (685, 325), (620, 345), (585, 385), (565, 445), (525, 505), (485, 545),
                                (380, 545), (315, 515), (285, 460), (295, 400), (285, 340), (295, 280), (315, 220),
                                (325, 160)])),
    # the tail curls to the viewer's left on the card, to the right in the sprite: flipped (head frontal)
    "swsh9-76": dict(kind="rare", sprite="flygon", flip=True, scene="the stormy sky",
                     mask=hand([(185, 70), (260, 55), (275, 140), (265, 200), (300, 225), (330, 105), (380, 55),
                                (460, 55), (525, 105), (600, 145), (640, 165), (690, 145), (735, 200), (725, 260),
                                (705, 300), (765, 330), (785, 375), (740, 385), (700, 365), (640, 345), (600, 375),
                                (565, 420), (605, 455), (655, 490), (645, 525), (560, 525), (500, 475), (460, 435),
                                (420, 445), (355, 425), (315, 360), (295, 305), (235, 275), (205, 215), (205, 150)])),
    # Sandy Cloak: the head at the viewer's left of the cloak like the sprite, unflipped
    "swsh9-77": dict(kind="rare", sprite="wormadam-sandy", scene="the sandstorm hills",
                     mask=hand([(255, 230), (290, 205), (320, 205), (310, 150), (305, 50), (345, 45), (375, 110),
                                (370, 180), (390, 160), (460, 155), (520, 135), (565, 135), (615, 195), (625, 280),
                                (635, 345), (695, 375), (705, 435), (660, 475), (620, 485), (560, 505), (470, 505),
                                (380, 485), (335, 455), (285, 425), (255, 380), (265, 340), (245, 300), (255, 260)])),
}

if __name__ == "__main__":
    brsbatch.main(GROUP, TABLE)
