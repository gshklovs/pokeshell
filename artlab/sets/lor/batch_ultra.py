r"""Lost Origin group `ultra`: the 15 Rare Ultra cards. The plain full arts get kind `fullart` (Giratina V 185's
recipe = evs Glaceon V 174: painting, glow + 12 rays, tinted vignette, fingerprint etch); the painted alt arts
(Rotom V 177, Aerodactyl V 180, Galarian Perrserker V 184) get kind `alt` (Giratina V 186's recipe = evs Umbreon
VMAX 215). Per card: glow / tint / rim_col / star from the card's palette, frame / tex_src for the paintings.
Hand masks in card px, read off work/grid_<n>.png. Other Pokemon in a painting (the Tropius / Bonsly / Archeops
flock on 180) stay as scenery.

  C:\Users\grego\repos\pokeshell\.venv\Scripts\python batch_ultra.py rembg|masks|quick|all [ids]
"""
import math

import lorbatch

GROUP = "ultra"

WARM_STAR = {"L": "#ffffff", "l": "#fff0d8", "j": "#ffc080"}
YELLOW_STAR = {"L": "#ffffff", "l": "#fffbe0", "j": "#ffe98a"}
CYAN_STAR = {"L": "#ffffff", "l": "#e6fbff", "j": "#9fe8ff"}
PINK_STAR = {"L": "#ffffff", "l": "#fff0fa", "j": "#ffc0e0"}
GREEN_STAR = {"L": "#ffffff", "l": "#efffe6", "j": "#aef0a0"}
GOLD_STAR = {"L": "#ffffff", "l": "#fff3c4", "j": "#ffd070"}
PASTEL_STAR = {"L": "#ffffff", "l": "#fff2fb", "j": "#bfe8ff"}


def hand(*polys, **kw):
    """a pure hand mask: the polygon(s) are the Pokemon"""
    return dict(model=None, add=list(polys), **kw)


def circle(cx, cy, r, n=48):
    return [(round(cx + r * math.cos(2 * math.pi * i / n)), round(cy + r * math.sin(2 * math.pi * i / n)))
            for i in range(n)]


TABLE = {
    # ---------------------------------------------------------------- plain full arts (Giratina V 185)
    "swsh11-172": dict(kind="fullart", sprite="electrode-hisui", text_y=645, texture=False,
                       glow=(0.85, 0.95, 1.0), tint=(0.0, 0.08, 0.22), rim_col=(0.9, 0.97, 1.0), star=CYAN_STAR,
                       scene="the blue lightning",
                       mask=hand(circle(370, 415, 305))),
    "swsh11-173": dict(kind="fullart", sprite="delphox", text_y=560, texture=False,
                       glow=(1.0, 0.85, 0.7), tint=(0.02, 0.05, 0.25), rim_col=(1.0, 0.95, 0.85), star=WARM_STAR,
                       scene="the blue burst with pink rays",
                       mask=hand([(30, 150), (75, 118), (170, 110), (250, 86), (370, 86), (430, 98), (520, 96),
                                  (630, 96), (635, 170), (565, 245), (475, 265), (445, 300), (500, 318), (540, 298),
                                  (555, 268), (605, 288), (615, 350), (655, 372), (705, 405), (705, 560), (130, 560),
                                  (130, 530), (105, 510), (88, 450), (52, 370), (30, 280)])),    "swsh11-174": dict(kind="fullart", sprite="kyurem", text_y=690, texture=False,
                       glow=(0.85, 0.95, 1.0), tint=(0.2, 0.02, 0.2), rim_col=(0.9, 0.97, 1.0), star=CYAN_STAR,
                       scene="the violet crystal field",
                       mask=hand([(30, 225), (80, 215), (180, 165), (250, 145), (290, 95), (400, 95), (425, 245),
                                  (470, 225), (560, 245), (640, 245), (705, 265), (705, 565), (640, 595), (560, 625),
                                  (500, 690), (255, 690), (245, 605), (150, 545), (70, 505), (30, 475)])),
    "swsh11-175": dict(kind="fullart", sprite="magnezone", text_y=565, texture=False,
                       glow=(1.0, 0.95, 0.6), tint=(0.3, 0.05, 0.0), rim_col=(1.0, 1.0, 0.8), star=YELLOW_STAR,
                       scene="the orange lightning storm",
                       mask=hand([(210, 125), (270, 125), (275, 215), (390, 195), (395, 155), (475, 155),
                                  (475, 220), (565, 238), (605, 280), (605, 325), (705, 315), (705, 515), (600, 515),
                                  (565, 545), (430, 565), (75, 565), (30, 520), (30, 335), (80, 295), (150, 275),
                                  (205, 235)])),
    "swsh11-176": dict(kind="fullart", sprite="rotom", text_y=595, texture=False,
                       glow=(0.9, 1.0, 0.8), tint=(0.0, 0.15, 0.08), rim_col=(0.9, 1.0, 0.95), star=GREEN_STAR,
                       scene="the green radar rings",
                       mask=hand([(30, 435), (100, 345), (160, 395), (235, 385), (270, 325), (330, 295), (400, 195),
                                  (465, 65), (510, 85), (505, 300), (545, 365), (565, 455), (565, 515), (695, 515),
                                  (705, 595), (30, 595)])),
    "swsh11-178": dict(kind="fullart", sprite="enamorus", text_y=595, texture=False,
                       glow=(1.0, 0.9, 0.95), tint=(0.2, 0.05, 0.2), rim_col=(1.0, 0.95, 1.0), star=PINK_STAR,
                       scene="the violet ink swirl",
                       mask=hand([(185, 95), (300, 92), (435, 95), (445, 160), (405, 200), (470, 195), (500, 225),
                                  (510, 190), (565, 180), (645, 205), (665, 260), (625, 305), (520, 305), (475, 360),
                                  (520, 440), (565, 495), (645, 515), (655, 560), (560, 595), (165, 595), (105, 510),
                                  (115, 465), (225, 435), (275, 380), (255, 300), (215, 240), (245, 200),
                                  (195, 160)])),
    "swsh11-179": dict(kind="fullart", sprite="aerodactyl", flip=True, text_y=700, texture=False,
                       glow=(1.0, 0.9, 0.6), tint=(0.3, 0.08, 0.0), rim_col=(1.0, 0.95, 0.9), star=WARM_STAR,
                       scene="the orange whirlwind",
                       mask=hand([(30, 105), (125, 105), (250, 195), (360, 275), (430, 245), (500, 175), (560, 195),
                                  (620, 115), (705, 95), (705, 425), (665, 505), (605, 565), (565, 700), (325, 700),
                                  (305, 605), (200, 575), (90, 565), (30, 545)])),
    "swsh11-181": dict(kind="fullart", sprite="gallade", flip=True, text_y=650, texture=False,
                       glow=(1.0, 0.92, 0.95), tint=(0.3, 0.0, 0.15), rim_col=(1.0, 0.95, 1.0), star=PINK_STAR,
                       scene="the pink speed rays",
                       mask=hand([(195, 195), (260, 190), (330, 145), (410, 90), (485, 90), (505, 200), (525, 320),
                                  (475, 385), (465, 440), (485, 495), (565, 505), (705, 535), (705, 650), (35, 650),
                                  (55, 575), (145, 465), (255, 350), (195, 240)])),
    "swsh11-182": dict(kind="fullart", sprite="drapion", flip=True, text_y=595, texture=False,
                       glow=(0.85, 0.95, 1.0), tint=(0.0, 0.1, 0.25), rim_col=(1.0, 0.95, 1.0), star=CYAN_STAR,
                       scene="the blue sky and clouds",
                       mask=hand([(30, 160), (160, 125), (230, 95), (325, 115), (335, 245), (460, 245), (520, 205),
                                  (560, 190), (645, 235), (705, 295), (705, 595), (30, 595)])),
    "swsh11-183": dict(kind="fullart", sprite="perrserker", text_y=680, texture=False,
                       glow=(1.0, 1.0, 0.75), tint=(0.0, 0.15, 0.05), rim_col=(1.0, 1.0, 0.9), star=YELLOW_STAR,
                       scene="the green-yellow swirl",
                       mask=hand([(110, 150), (110, 88), (240, 88), (360, 90), (450, 115), (520, 105), (565, 150),
                                  (585, 290), (635, 375), (675, 415), (705, 435), (705, 605), (600, 595), (565, 640),
                                  (565, 680), (145, 680), (150, 615), (80, 590), (30, 510), (30, 320), (85, 298),
                                  (150, 290), (140, 220)])),
    "swsh11-187": dict(kind="fullart", sprite="goodra-hisui", text_y=600, texture=False,
                       glow=(0.9, 0.95, 1.0), tint=(0.0, 0.12, 0.2), rim_col=(0.95, 0.95, 1.0), star=CYAN_STAR,
                       scene="the teal bubble spray",
                       mask=hand([(30, 185), (100, 185), (250, 205), (300, 145), (400, 92), (705, 92), (705, 600),
                                  (30, 600)])),
    "swsh11-188": dict(kind="fullart", sprite="pidgeot", text_y=600, texture=False,
                       glow=(1.0, 0.9, 0.8), tint=(0.25, 0.05, 0.2), rim_col=(1.0, 0.97, 0.9), star=WARM_STAR,
                       scene="the pink sunset glow",
                       mask=hand([(30, 245), (150, 245), (215, 175), (255, 115), (385, 115), (505, 165), (605, 255),
                                  (685, 375), (705, 480), (705, 600), (30, 600)])),
    # ---------------------------------------------------------------- alt-art paintings (Giratina V 186)
    "swsh11-177": dict(kind="alt", sprite="rotom", text_y=595, frame="#f0a040", rim_col=(1.0, 0.9, 0.6),
                       star=GOLD_STAR, scene="the junk pile of old appliances",
                       mask=hand([(185, 88), (252, 122), (322, 182), (302, 200), (335, 228), (360, 212), (390, 186),
                                  (402, 214), (397, 250), (440, 238), (512, 212), (518, 236), (477, 265), (472, 287),
                                  (420, 302), (385, 322), (340, 327), (300, 362), (272, 362), (278, 315), (253, 292),
                                  (198, 257), (138, 210), (213, 193), (228, 165)])),
    "swsh11-180": dict(kind="alt", sprite="aerodactyl", flip=True, text_y=700, frame="#4fb0d8",
                       rim_col=(1.0, 0.97, 0.9), star=PASTEL_STAR, scene="the prehistoric island coast",
                       mask=hand([(30, 285), (110, 245), (200, 205), (260, 195), (330, 215), (440, 185), (480, 145),
                                  (560, 120), (630, 95), (665, 108), (645, 152), (565, 202), (485, 252), (522, 330),
                                  (562, 388), (622, 448), (655, 520), (635, 565), (560, 565), (508, 512), (430, 445),
                                  (380, 425), (300, 445), (268, 385), (200, 375), (150, 395), (90, 400), (35, 385)])),
    "swsh11-184": dict(kind="alt", sprite="perrserker", text_y=685, frame="#e0b040", rim_col=(1.0, 0.95, 0.8),
                       star=GOLD_STAR, scene="the desk by the window with the gold coins",
                       mask=hand([(130, 160), (185, 122), (290, 92), (350, 90), (420, 112), (490, 100), (540, 98),
                                  (550, 148), (565, 250), (560, 300), (575, 360), (580, 440), (530, 490), (490, 560),
                                  (480, 612), (445, 690), (245, 690), (240, 600), (205, 525), (175, 495), (135, 445),
                                  (140, 390), (125, 320), (160, 300), (175, 270), (140, 230)])),}

if __name__ == "__main__":
    lorbatch.main(GROUP, TABLE)
