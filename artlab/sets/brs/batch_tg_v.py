r"""Brilliant Stars, group tg_v: the Trainer Gallery Rare Holo V / VMAX cards (swsh9tg), kind `alt` -- Umbreon VMAX
215's painting treatment at the printed tier (ladder: Umbreon V TG22, Umbreon VMAX TG23). Only the card's own
Pokemon is painted out; the trainers (Sonia, Acerola and the others) and other Pokemon (Acerola's Gengar)
stay as scenery. Coordinates are card px read off work/grid_TG<n>.png. TG20 (Rapid Strike Urshifu V) is skipped by
the lead: there is no non-Gigantamax Rapid Strike sprite.

  ..\..\..\.venv\Scripts\python batch_tg_v.py rembg|masks|quick|all [ids]
"""
import brsbatch
from brscards import WHITE_STAR, GOLD_STAR, PINK_STAR, PASTEL_STAR

GROUP = "tg_v"
EVO = (100, 95, 425, 158)       # "Evolves from ..." + the Dynamax / Gigantamax pill (runs past brscards.EVOLVES)

TABLE = {
    # Boltund bounds in with Sonia, muzzle to the right (vendor faces left: flip)
    "swsh9tg-TG13": dict(
        kind="alt", texture=False, sprite="boltund", flip=True, text_y=590,
        mask=dict(model=None, add=[[(30, 380), (60, 300), (100, 220), (125, 150), (145, 105), (210, 100),
                                    (290, 95), (375, 95), (385, 125), (360, 140), (425, 175), (478, 225),
                                    (478, 285), (435, 318), (385, 325), (345, 345), (318, 365), (335, 450),
                                    (355, 515), (430, 530), (565, 550), (600, 590), (30, 590)]]),
        rim_col=(1.0, 0.92, 0.6), vig=(0.1, 0.04, 0.08), star=GOLD_STAR,
        frame="#f0c850", scene="Sonia's room"),
    # Sylveon with its trainer behind it; head turned left (vendor faces left)
    "swsh9tg-TG14": dict(
        kind="alt", texture=False, sprite="sylveon", text_y=650, strike=True,
        mask=dict(model=None, add=[[(318, 380), (345, 300), (378, 228), (430, 190), (520, 175), (620, 185),
                                    (700, 195), (700, 650), (335, 650), (318, 560), (288, 480), (298, 420)]]),
        rim_col=(1.0, 0.85, 0.95), vig=(0.08, 0.03, 0.1), star=PINK_STAR,
        frame="#f090c8", scene="the petal garden"),
    # the Dynamax Sylveon's face fills the card; its trainer floats on the right (kept). Frontal: unflipped
    "swsh9tg-TG15": dict(
        kind="alt", texture=False, boxes=[EVO], sprite="sylveon", text_y=600, strike=True,
        mask=dict(model=None, add=[(30, 96, 700, 600)],
                  cut_after=[[(440, 96), (500, 96), (530, 200), (560, 238), (622, 238), (662, 300), (652, 390),
                              (618, 402), (700, 420), (700, 600), (505, 600), (480, 540), (460, 500),
                              (445, 440), (455, 370), (470, 330), (490, 300), (468, 200)]], fill=False),
        rim_col=(1.0, 0.88, 0.96), vig=(0.06, 0.04, 0.12), star=PASTEL_STAR,
        frame="#f090c8", scene="the petal storm"),
    # Mimikyu sprawled upside-down on Acerola's couch (Gengar by the lamp stays); frontal: unflipped
    "swsh9tg-TG16": dict(
        kind="alt", texture=False, sprite="mimikyu", text_y=560,
        mask=dict(model=None, add=[[(222, 398), (232, 330), (270, 292), (292, 290), (318, 268), (318, 205), (348, 195),
                                    (365, 258), (425, 275), (475, 298), (525, 340), (535, 420), (505, 470),
                                    (492, 540), (472, 560), (250, 560), (240, 520), (188, 470), (178, 420)]]),
        rim_col=(1.0, 0.95, 0.7), vig=(0.04, 0.04, 0.1), star=GOLD_STAR,
        frame="#c8a0e8", scene="Acerola's haunted parlour"),
    # the Dynamax Mimikyu's disguise fills the left; Acerola lies on it (kept). Frontal: unflipped
    "swsh9tg-TG17": dict(
        kind="alt", texture=False, boxes=[EVO], sprite="mimikyu", text_y=615, dx=-5,
        mask=dict(model=None, add=[[(30, 140), (430, 140), (465, 260), (475, 400), (400, 470), (360, 560),
                                    (430, 565), (520, 545), (600, 600), (640, 615), (30, 615)]],
                  cut_after=[[(368, 480), (390, 420), (440, 388), (500, 398), (565, 440), (625, 520),
                              (615, 600), (560, 615), (480, 600), (420, 560), (378, 530)]], fill=False),
        rim_col=(1.0, 0.95, 0.7), vig=(0.06, 0.03, 0.08), star=GOLD_STAR,
        frame="#c8a0e8", scene="the confetti sky"),
    # Single Strike Urshifu punches right beside its trainer (vendor faces left: flip)
    "swsh9tg-TG18": dict(
        kind="alt", texture=False, sprite="urshifu", flip=True, text_y=625, strike=True, dx=-4,
        mask=dict(model=None, add=[[(30, 420), (65, 300), (55, 160), (110, 125), (170, 155), (210, 135),
                                    (260, 105), (305, 125), (365, 145), (405, 205), (405, 280), (385, 322),
                                    (395, 368), (455, 385), (458, 452), (415, 462), (425, 500), (520, 535),
                                    (580, 535), (660, 552), (705, 575), (705, 625), (30, 625)]]),
        rim_col=(1.0, 0.8, 0.6), vig=(0.1, 0.03, 0.04), star=GOLD_STAR,
        frame="#e05040", scene="the dojo hills"),
    # Gigantamax Single Strike Urshifu fills the sky behind the trainer (kept); face and fist to the right: flip
    "swsh9tg-TG19": dict(
        kind="alt", texture=False, boxes=[EVO], sprite="urshifu-gmax", flip=True, text_y=648, strike=True, dx=-7,
        mask=dict(model=None, add=[(30, 96, 700, 648)],
                  cut_after=[[(170, 470), (200, 420), (270, 412), (335, 420), (400, 458), (440, 465),
                              (470, 445), (530, 445), (568, 488), (562, 580), (522, 602), (512, 648),
                              (170, 648)],
                             [(30, 140), (50, 140), (65, 300), (70, 450), (30, 480)],        # the blue sky, left
                             [(340, 96), (450, 96), (420, 170), (370, 175)],                  # ... between head and fist
                             [(655, 420), (700, 400), (700, 648), (640, 648), (645, 540)]],   # ... sparkles, right
                  fill=False),
        rim_col=(1.0, 0.8, 0.6), vig=(0.1, 0.03, 0.06), star=GOLD_STAR,
        frame="#e05040", scene="the one-blow sky"),
    # Gigantamax Rapid Strike Urshifu, head turned left toward the trainer on the left (kept); vendor faces left
    "swsh9tg-TG21": dict(
        kind="alt", texture=False, boxes=[EVO], sprite="urshifu-rapid-strike-gmax", text_y=600, strike=True, dx=10,
        mask=dict(model=None, add=[[(318, 260), (350, 200), (410, 150), (500, 128), (600, 148), (705, 200),
                                    (705, 600), (30, 600), (40, 570), (90, 540), (130, 510), (200, 470),
                                    (262, 452), (298, 470), (300, 390), (318, 330)]]),
        rim_col=(0.7, 0.85, 1.0), vig=(0.06, 0.03, 0.1), star=WHITE_STAR,
        frame="#4f80e0", scene="the sunset river"),
}

if __name__ == "__main__":
    brsbatch.main(GROUP, TABLE)
