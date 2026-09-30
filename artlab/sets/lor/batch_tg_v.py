r"""Lost Origin, group tg_v: the Trainer Gallery Rare Holo V / VMAX cards (swsh11tg), kind `alt` -- Umbreon VMAX
215's painting treatment at the printed tier (ladder: Pikachu V TG16, Pikachu VMAX TG17). Only the card's own
Pokemon is painted out; the trainers stay as scenery (`cut_after` keeps a trainer who overlaps the mask).
Coordinates are card px read off work/grid_TG<n>.png. TG22 (Eternatus VMAX) is skipped: the Eternamax sprite
`eternatus-eternamax` is 67 x 56 sprite px, and 56 rows = 112 grid px exceeds the 110 cap (FH = 2 H), so it
cannot be placed pixel-exact whatever W / H / S are.

  ..\..\..\.venv\Scripts\python batch_tg_v.py rembg|masks|quick|all [ids]
"""
import lorbatch
from lorcards import WHITE_STAR, GOLD_STAR, PINK_STAR, PASTEL_STAR  # noqa: F401

GROUP = "tg_v"
ART = (30, 96, 705, 720)

TABLE = {
    # Orbeetle springs out of the jungle beside its trainer: shell on the left, face to the right (vendor: face
    # left of the shell -> flip)
    "swsh11tg-TG12": dict(
        kind="alt", sprite="orbeetle", flip=True, text_y=620, tex_src=(560, 150, 700, 300),
        mask=dict(model=None, add=[[(30, 250), (45, 175), (100, 125), (180, 105), (265, 115), (335, 150), (390, 205),
                                    (425, 260), (440, 320), (432, 380), (412, 440), (388, 472), (345, 482),
                                    (350, 520), (380, 580), (400, 640), (180, 640), (190, 560), (160, 520),
                                    (120, 505), (60, 515), (38, 480), (30, 420)]]),
        rim_col=(1.0, 0.85, 0.8), vig=(0.02, 0.08, 0.04), star=GOLD_STAR,
        frame="#d8403c", scene="the jungle trail"),
    # Gigantamax Orbeetle's shell (the red ring and its saucer lights) fills the card, its body hangs top right;
    # the trainer tumbles through the light in the middle (kept). Face right of the dome: flip
    "swsh11tg-TG13": dict(
        kind="alt", texture=False, sprite="orbeetle-gmax", flip=True, text_y=595,
        mask=dict(model=None, add=[(30, 96, 705, 600)],
                  cut_after=[[(200, 390), (262, 378), (292, 420), (300, 448), (340, 440), (392, 448), (425, 470),
                              (412, 502), (362, 502), (332, 540), (302, 560), (292, 600), (200, 600), (188, 560),
                              (160, 540), (188, 500), (198, 450)],
                             [(30, 480), (120, 470), (200, 500), (200, 600), (30, 600)],      # pink glitter, low left
                             [(290, 340), (400, 315), (500, 330), (545, 380), (555, 470), (540, 560), (470, 600),
                              (300, 600), (260, 540), (250, 450)],                             # the white light
                             [(140, 330), (170, 280), (230, 245), (300, 228), (370, 225), (430, 240), (445, 275),
                              (420, 285), (360, 270), (300, 270), (240, 285), (195, 320), (180, 360), (145, 360)],
                             [(550, 400), (590, 390), (610, 440), (615, 520), (600, 575), (565, 570), (560, 500),
                              (545, 450)]],                                                    # the pink G-Max beams
                  fill=False),
        rim_col=(1.0, 0.8, 0.9), vig=(0.08, 0.03, 0.1), star=PINK_STAR,
        frame="#e0508a", scene="the G-Max light show"),
    # Centiskorch's head blazes on the right, its body coiling down-left toward the shouting trainer (kept).
    # Head upper right, body trailing left (vendor: head upper left) -> flip
    "swsh11tg-TG14": dict(
        kind="alt", texture=False, sprite="centiskorch", flip=True, text_y=685,
        mask=dict(model=None, add=[[(262, 330), (275, 220), (300, 150), (340, 128), (390, 96), (705, 96),
                                    (705, 690), (120, 690), (130, 620), (160, 580), (230, 560), (272, 520),
                                    (300, 480), (300, 420)]]),
        rim_col=(1.0, 0.8, 0.5), vig=(0.1, 0.03, 0.02), star=GOLD_STAR,
        frame="#f07a28", scene="the stadium fire"),
    # Gigantamax Centiskorch arcs across the sky, head up-left (vendor: head up-left); the trainer runs along
    # its back (kept)
    "swsh11tg-TG15": dict(
        kind="alt", sprite="centiskorch-gmax", text_y=690, tex_src=(420, 110, 700, 330),
        mask=dict(model=None, add=[[(170, 180), (230, 150), (300, 150), (330, 200), (380, 260), (420, 330),
                                    (420, 420), (400, 520), (430, 540), (500, 520), (560, 540), (640, 510),
                                    (705, 500), (705, 690), (30, 690), (30, 500), (60, 420), (120, 350),
                                    (200, 300), (280, 260), (250, 230), (180, 230)]],
                  cut_after=[[(530, 400), (570, 385), (600, 400), (610, 450), (640, 500), (620, 555),
                              (560, 560), (530, 520), (525, 450)]], fill=False),
        rim_col=(1.0, 0.85, 0.6), vig=(0.02, 0.06, 0.14), star=WHITE_STAR,
        frame="#f07a28", scene="the sky above the stadium"),
    # Enamorus coils over its trainer (the lady in the great hat, kept): arm raised up-left, head top right looking
    # down-left, the heart-bulb tail bottom right. Vendor is near-frontal with the fist on the right: flip
    "swsh11tg-TG18": dict(
        kind="alt", texture=False, sprite="enamorus", flip=True, text_y=595, dx=20,
        mask=dict(model=None, keep=4, close=4, hull=[(30, 96), (705, 96), (705, 600), (30, 600)],
                  colour=lambda h, s, v: ((h > 318) | (h < 16)) & (s > 0.42) & (v > 0.28),   # pink body, red tail
                  add=[[(350, 100), (420, 90), (480, 110), (560, 150), (580, 230), (600, 300), (620, 330),
                        (690, 340), (695, 420), (640, 440), (620, 470), (690, 500), (700, 600), (440, 600),
                        (460, 520), (500, 470), (480, 380), (440, 300), (420, 250), (380, 240), (270, 230),
                        (250, 270), (170, 270), (100, 230), (90, 150), (140, 100), (250, 110), (300, 170),
                        (380, 170)],
                       [(30, 130), (90, 110), (160, 110), (130, 170), (95, 240), (110, 300), (70, 360),
                        (60, 440), (40, 520), (30, 560)]],
                  cut_after=[[(100, 290), (150, 245), (230, 240), (330, 270), (420, 310), (485, 365), (490, 430),
                              (455, 470), (465, 560), (455, 600), (70, 600), (50, 520), (60, 450), (110, 400),
                              (120, 330)]],
                  fill=False),
        rim_col=(1.0, 0.8, 0.92), vig=(0.08, 0.02, 0.1), star=PINK_STAR,
        frame="#e8508c", scene="the blossom storm"),
    # Gallade slashes across the card in front of its trainer (kept), head right, facing left (vendor faces left)
    "swsh11tg-TG19": dict(
        kind="alt", sprite="gallade", text_y=650, dx=20, tex_src=(620, 440, 700, 640),
        mask=dict(model=None, keep=3, close=4, hull=[(30, 96), (705, 96), (705, 660), (30, 660)],
                  colour=lambda h, s, v: (h > 95) & (h < 178) & (s > 0.35) & (v > 0.2),     # the green blades
                  add=[[(40, 130), (80, 110), (140, 150), (200, 250), (260, 380), (300, 480), (340, 600),
                        (360, 660), (250, 660), (180, 560), (110, 440), (60, 330), (40, 230)],
                       [(300, 420), (350, 370), (420, 330), (440, 250), (470, 180), (560, 140), (630, 160),
                        (660, 220), (650, 300), (615, 380), (620, 450), (660, 500), (705, 560), (705, 660),
                        (400, 660), (420, 560), (440, 480), (400, 450)]]),
        rim_col=(0.8, 1.0, 0.9), vig=(0.02, 0.06, 0.1), star=WHITE_STAR,
        frame="#3cb878", scene="the moonlit sparring ground"),
    # Crobat's wings fill the card; its trainer stands at the left (kept). Near-frontal: unflipped
    "swsh11tg-TG20": dict(
        kind="alt", texture=False, sprite="crobat", text_y=595,
        mask=dict(model=None, add=[(30, 96, 705, 600)],
                  cut_after=[[(30, 265), (60, 232), (120, 230), (170, 258), (200, 300), (250, 330), (282, 380),
                              (272, 480), (242, 530), (232, 600), (30, 600)],
                             [(240, 100), (420, 100), (400, 160), (260, 200)],                # sky, top
                             [(570, 200), (640, 200), (650, 320), (580, 330)]], fill=False),  # mountain, right
        rim_col=(0.9, 0.8, 1.0), vig=(0.06, 0.03, 0.12), star=WHITE_STAR,
        frame="#9a6ae0", scene="the mountain wind"),
    # Eternatus looms over its trainer (kept, lower left), head glowing on the right, spikes spread up-left
    # (vendor: head left, body right) -> flip
    "swsh11tg-TG21": dict(
        kind="alt", texture=False, sprite="eternatus", flip=True, text_y=625,
        mask=dict(model=None, add=[(30, 96, 705, 625)],
                  cut_after=[[(30, 560), (90, 520), (160, 470), (210, 420), (260, 395), (320, 400), (360, 440),
                              (370, 500), (400, 560), (470, 600), (470, 625), (30, 625)]], fill=False),
        rim_col=(1.0, 0.6, 0.7), vig=(0.08, 0.02, 0.06), star=PINK_STAR,
        frame="#d0304a", scene="the darkest night"),
}

if __name__ == "__main__":
    lorbatch.main(GROUP, TABLE)
