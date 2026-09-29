r"""Brilliant Stars group `ultra`: the 13 Rare Ultra cards. The plain full arts get kind `fullart` (Shaymin V 152's
recipe = evs Glaceon V 174: painting, glow + 12 rays, tinted vignette, fingerprint etch); the painted alt arts
(Lumineon V 156, Honchkrow V 162, Arceus V 166) get kind `alt` (Charizard V 154's recipe = evs Umbreon VMAX 215).
Per card: glow / tint / rim_col / star from the card's palette (as evs batch_ultra_a.SPEC), frame / tex_src for the
paintings (as cz batch_gg_v). Hand masks in card px, read off work/grid_<n>.png. Other Pokemon in a painting
(the Murkrow flock on 162) stay as scenery.

  C:\Users\grego\repos\pokeshell\.venv\Scripts\python batch_ultra.py rembg|masks|quick|all [ids]
"""
import brsbatch

GROUP = "ultra"

WARM_STAR = {"L": "#ffffff", "l": "#fff0d8", "j": "#ffc080"}
YELLOW_STAR = {"L": "#ffffff", "l": "#fffbe0", "j": "#ffe98a"}
CYAN_STAR = {"L": "#ffffff", "l": "#e6fbff", "j": "#9fe8ff"}
PINK_STAR = {"L": "#ffffff", "l": "#fff0fa", "j": "#ffc0e0"}
GOLD_STAR = {"L": "#ffffff", "l": "#fff3c4", "j": "#8fd8ff"}
PASTEL_STAR = {"L": "#ffffff", "l": "#fff2fb", "j": "#bfe8ff"}


def hand(*polys, **kw):
    """a pure hand mask: the polygon(s) are the Pokemon"""
    return dict(model=None, add=list(polys), **kw)


TABLE = {
    # ---------------------------------------------------------------- plain full arts (Shaymin V 152)
    "swsh9-153": dict(kind="fullart", sprite="charizard", text_y=688, texture=False,
                      glow=(1.0, 0.9, 0.7), tint=(0.0, 0.12, 0.2), rim_col=(1.0, 0.95, 0.85), star=WARM_STAR,
                      scene="the teal light burst",
                      mask=hand([(30, 260), (60, 200), (130, 92), (210, 95), (235, 175), (255, 195),
                                 (300, 125), (430, 90), (505, 150), (455, 240), (425, 290), (480, 230), (515, 145),
                                 (575, 135), (640, 195), (705, 245), (705, 580), (600, 590), (570, 640), (600, 688),
                                 (120, 688), (140, 560), (100, 525), (30, 500)])),
    "swsh9-155": dict(kind="fullart", sprite="lumineon", flip=True, text_y=596, texture=False,
                      glow=(1.0, 0.95, 0.7), tint=(0.3, 0.05, 0.15), rim_col=(0.85, 0.97, 1.0), star=CYAN_STAR,
                      scene="the sunset glow",
                      mask=hand([(60, 100), (250, 95), (480, 95), (600, 125), (685, 200), (710, 280), (710, 430),
                                 (645, 430), (605, 470), (600, 560), (580, 610), (460, 600), (420, 565), (330, 565),
                                 (250, 545), (200, 485), (160, 455), (80, 445), (30, 445), (30, 360), (80, 355),
                                 (130, 300), (100, 200)])),
    "swsh9-157": dict(kind="fullart", sprite="pikachu", text_y=752, texture=False,
                      glow=(1.0, 0.95, 0.6), tint=(0.3, 0.1, 0.0), rim_col=(1.0, 1.0, 0.8), star=YELLOW_STAR,
                      scene="the orange bokeh",
                      mask=hand([(95, 120), (160, 100), (205, 195), (250, 225), (330, 210), (420, 185), (500, 170),
                                 (545, 195), (510, 255), (600, 230), (705, 270), (705, 345), (600, 455), (525, 495),
                                 (610, 565), (500, 650), (505, 700), (470, 752), (100, 752), (100, 600), (115, 460),
                                 (110, 340), (100, 240)])),
    "swsh9-158": dict(kind="fullart", sprite="raichu", flip=True, text_y=568, texture=False,
                      glow=(1.0, 0.95, 0.6), tint=(0.0, 0.15, 0.05), rim_col=(1.0, 1.0, 0.8), star=YELLOW_STAR,
                      scene="the green lightning rays",
                      mask=hand([(75, 110), (150, 90), (230, 135), (300, 185), (340, 175), (400, 185), (495, 150),
                                 (530, 120), (565, 205), (605, 275), (645, 300), (645, 420), (615, 470), (645, 540),
                                 (645, 568), (160, 568), (165, 515), (100, 470), (60, 430), (150, 390), (90, 260),
                                 (60, 180)],
                                [(30, 395), (155, 385), (165, 425), (85, 445), (75, 500), (140, 568), (95, 568),
                                 (35, 520)])),
    "swsh9-159": dict(kind="fullart", sprite="granbull", text_y=652, texture=False,
                      glow=(1.0, 0.9, 0.85), tint=(0.3, 0.05, 0.05), rim_col=(1.0, 0.94, 0.98), star=PINK_STAR,
                      scene="the red-orange swirl",
                      mask=hand([(125, 125), (200, 100), (300, 115), (400, 105), (525, 120), (615, 145), (630, 265),
                                 (565, 320), (565, 375), (655, 395), (715, 445), (715, 565), (620, 585), (565, 605),
                                 (565, 652), (85, 652), (95, 600), (85, 520), (55, 460), (105, 385), (145, 335),
                                 (125, 230)])),
    "swsh9-160": dict(kind="fullart", sprite="whimsicott", text_y=596, texture=False,
                      glow=(1.0, 0.9, 0.95), tint=(0.2, 0.05, 0.2), rim_col=(1.0, 0.95, 1.0), star=PINK_STAR,
                      scene="the pink cloud sky",
                      mask=hand([(55, 280), (95, 195), (175, 125), (260, 105), (360, 95), (450, 90), (535, 105),
                                 (605, 175), (665, 245), (712, 320), (712, 425), (695, 505), (645, 545), (565, 565),
                                 (505, 596), (85, 596), (75, 500), (55, 400)])),
    "swsh9-161": dict(kind="fullart", sprite="honchkrow", text_y=622, texture=False,
                      glow=(1.0, 0.95, 0.65), tint=(0.15, 0.1, 0.0), rim_col=(1.0, 1.0, 0.85), star=GOLD_STAR,
                      scene="the golden speed lines",
                      mask=hand([(30, 335), (120, 295), (200, 285), (235, 145), (300, 125), (400, 135), (475, 175),
                                 (525, 255), (565, 300), (605, 355), (645, 420), (712, 555), (712, 622), (30, 622)])),
    "swsh9-163": dict(kind="fullart", sprite="zamazenta-crowned", flip=True, text_y=622, texture=False,
                      glow=(0.8, 0.95, 1.0), tint=(0.0, 0.1, 0.25), rim_col=(0.85, 0.97, 1.0), star=CYAN_STAR,
                      scene="the sky blue light",
                      mask=hand([(65, 160), (125, 85), (200, 75), (300, 65), (400, 75), (505, 85), (565, 155),
                                 (565, 245), (645, 275), (695, 325), (710, 420), (690, 560), (700, 622), (85, 622),
                                 (75, 560), (55, 480), (85, 400), (55, 300), (85, 230)])),
    "swsh9-164": dict(kind="fullart", sprite="flygon", flip=True, text_y=652, texture=False,
                      glow=(1.0, 0.9, 0.6), tint=(0.3, 0.08, 0.0), rim_col=(1.0, 0.97, 0.85), star=WARM_STAR,
                      scene="the orange sandstorm",
                      mask=hand([(30, 340), (30, 195), (150, 185), (260, 205), (295, 95), (330, 60), (385, 65),
                                 (430, 190), (480, 95), (525, 175), (515, 300), (545, 330), (535, 430), (585, 455),
                                 (600, 500), (712, 490), (712, 652), (175, 652), (195, 560), (165, 445), (95, 405)])),
    "swsh9-165": dict(kind="fullart", sprite="arceus", flip=True, text_y=658, texture=False,
                      glow=(1.0, 0.92, 0.95), tint=(0.2, 0.05, 0.15), rim_col=(1.0, 0.97, 1.0), star=PINK_STAR,
                      scene="the pink-blue haze",
                      mask=hand([(25, 505), (115, 295), (165, 290), (170, 225), (235, 205), (300, 195), (355, 125), (375, 85),
                                 (470, 110), (525, 155), (505, 210), (545, 325), (605, 445), (705, 465), (712, 560),
                                 (675, 658), (30, 658)])),
    # ---------------------------------------------------------------- alt-art paintings (Charizard V 154)
    "swsh9-156": dict(kind="alt", sprite="lumineon", text_y=596, frame="#4fa8e8", rim_col=(0.8, 0.95, 1.0),
                      vig=(0.02, 0.02, 0.1), star=PASTEL_STAR, tex_src=(300, 460, 470, 590),
                      scene="the reef under the whirlpool",
                      mask=hand([(222, 300), (248, 245), (290, 225), (330, 155), (400, 125), (485, 130), (535, 170),
                                 (545, 235), (505, 255), (470, 250), (440, 300), (478, 330), (468, 385), (405, 375),
                                 (385, 435), (335, 465), (285, 445), (268, 385), (238, 345)])),
    "swsh9-162": dict(kind="alt", sprite="honchkrow", flip=True, text_y=622, frame="#5f7fd0",
                      rim_col=(1.0, 0.95, 0.8), vig=(0.02, 0.06, 0.02), star=GOLD_STAR, tex_src=(560, 360, 690, 500),
                      scene="the forest bough with the Murkrow flock",
                      mask=hand([(225, 75), (300, 60), (420, 115), (485, 165), (505, 220), (475, 262), (482, 325),
                                 (445, 338), (442, 420), (420, 452), (382, 472), (360, 500), (335, 535), (268, 535),
                                 (248, 482), (200, 455), (148, 432), (98, 392), (108, 320), (128, 258), (168, 228),
                                 (218, 218), (255, 178), (235, 120)])),
    "swsh9-166": dict(kind="alt", sprite="arceus", text_y=658, frame="#e0d0a0", rim_col=(1.0, 0.95, 0.8),
                      vig=(0.05, 0.05, 0.1), star=GOLD_STAR, tex_src=(540, 140, 690, 290),
                      scene="the sky over the floating land",
                      mask=hand([(298, 140), (338, 92), (392, 105), (422, 168), (472, 188), (522, 268), (512, 362),
                                 (462, 422), (452, 502), (422, 522), (382, 562), (362, 642), (328, 642), (308, 562),
                                 (278, 522), (268, 462), (218, 472), (206, 420), (176, 340), (198, 306), (258, 298),
                                 (288, 258)])),
}

if __name__ == "__main__":
    brsbatch.main(GROUP, TABLE)
