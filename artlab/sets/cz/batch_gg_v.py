r"""Crown Zenith, group gg_v: the Galarian Gallery Rare Holo V / VMAX cards (swsh12pt5gg), kind `alt` -- Umbreon VMAX
215's painting treatment (ladder: Entei V GG36). The tier stays the printed rarity. Only the card's own Pokemon is
painted out; the other Pokemon / people in each scene stay (Lumineon's reef Pokemon, Zeraora's Pachirisu /
Dedenne, Deoxys's saucer, Drapion's two Skorupi). Coordinates are card px read off work/grid_GG<n>.png.

  ..\..\..\.venv\Scripts\python batch_gg_v.py rembg|masks|quick|all [ids]
"""
import czbatch
from czcards import WHITE_STAR, GOLD_STAR, PINK_STAR, PASTEL_STAR

GROUP = "gg_v"
ISNET = "isnet-general-use"

TABLE = {
    # Suicune stands on the snowfield under the meteor sky, head to the right (vendor faces left: flip)
    "swsh12pt5gg-GG38": dict(
        kind="alt", sprite="suicune", flip=True, text_y=620,
        mask=dict(model=ISNET, hull=[(130, 420), (160, 370), (240, 300), (255, 250), (250, 200), (330, 220),
                                     (400, 260), (430, 330), (430, 380), (575, 415), (575, 480), (430, 450),
                                     (390, 480), (375, 540), (390, 620), (320, 620), (300, 570), (270, 570),
                                     (260, 620), (190, 610), (190, 510), (150, 490), (120, 470)], keep=2, close=4),
        tex_src=(450, 110, 690, 260), rim_col=(0.85, 0.95, 1.0), vig=(0.02, 0.04, 0.14), star=WHITE_STAR,
        frame="#7fb8e8", scene="the meteor shower over the snowfield"),
    # Lumineon, a dark silhouette in the glowing bubble among the reef (Chinchou, Finneon ... stay)
    "swsh12pt5gg-GG39": dict(
        kind="alt", sprite="lumineon", text_y=600, texture=False, grow=7,
        mask=dict(model=None, add=[[(300, 270), (330, 240), (400, 245), (455, 280), (465, 335), (430, 375),
                                    (390, 410), (330, 420), (290, 400), (290, 340)]]),
        rim_col=(0.8, 0.95, 1.0), vig=(0.02, 0.02, 0.1), star=PASTEL_STAR,
        frame="#4fa8e8", scene="the glowing bubble in the reef"),
    # Raikou leaps left through the lightning sunset (vendor faces left)
    "swsh12pt5gg-GG41": dict(
        kind="alt", sprite="raikou", text_y=620,
        mask=dict(model=ISNET, hull=[(140, 390), (150, 320), (200, 290), (260, 220), (330, 185), (410, 195),
                                     (440, 255), (480, 280), (540, 275), (555, 335), (520, 365), (525, 425),
                                     (490, 475), (480, 550), (430, 555), (390, 505), (340, 475), (280, 450),
                                     (220, 430), (170, 440)], keep=1, close=4),
        tex_src=(440, 500, 690, 600), rim_col=(1.0, 0.9, 0.6), vig=(0.1, 0.03, 0.08), star=GOLD_STAR,
        frame="#f0c040", scene="the lightning sunset"),
    # the Dynamax Zeraora fills the card (as the ladder's Zeraora VMAX 54): everything but Pachirisu on its head,
    # Dedenne on the left and the red orbs top right goes; frontal close-up (kept unflipped)
    "swsh12pt5gg-GG42": dict(
        kind="alt", sprite="zeraora", text_y=650, texture=False,
        mask=dict(model=None, add=[(30, 96, 700, 650)],
                  cut_after=[[(305, 205), (350, 175), (425, 170), (460, 225), (450, 300), (405, 345), (335, 345),
                              (300, 295)],
                             [(90, 565), (150, 560), (165, 625), (105, 635)],
                             [(530, 96), (700, 96), (700, 190), (620, 175), (550, 140)],
                             [(640, 225), (700, 215), (700, 385), (645, 365)]], keep=1, fill=False),
        rim_col=(1.0, 0.95, 0.6), vig=(0.08, 0.06, 0.0), star=GOLD_STAR,
        frame="#f0d040", scene="Pachirisu riding the storm"),
    # Deoxys Normal Forme standing in the saucer's tractor beam (the Deoxys-faced saucer stays); frontal
    "swsh12pt5gg-GG45": dict(
        kind="alt", sprite="deoxys", text_y=625, texture=False, grow=7,
        mask=dict(model=None, add=[[(330, 355), (370, 350), (410, 365), (430, 415), (470, 435), (505, 515),
                                    (515, 625), (225, 625), (235, 515), (255, 445), (305, 415), (315, 375)]]),
        rim_col=(1.0, 0.8, 0.85), vig=(0.08, 0.02, 0.1), star=PINK_STAR,
        frame="#e05050", scene="the saucer's tractor beam"),
    # Gigantamax Hatterene (G-Max Smite: the -gmax sprite), a translucent giant over the night forest; its
    # face turns right and the hair trails down the left (vendor mirrored: flip)
    "swsh12pt5gg-GG47": dict(
        kind="alt", sprite="hatterene-gmax", flip=True, text_y=625, texture=False, grow=8,
        mask=dict(model=None, add=[[(30, 96), (700, 96), (700, 205), (610, 230), (530, 260), (490, 330),
                                    (420, 355), (365, 365), (355, 430), (345, 510), (340, 575), (250, 605),
                                    (150, 595), (100, 565), (60, 565), (30, 530)]]),
        rim_col=(1.0, 0.9, 1.0), vig=(0.04, 0.03, 0.12), star=PINK_STAR,
        frame="#f08ad0", scene="the enchanted night forest"),
    # Zacian Hero of Many Battles (the sword in its mouth), in the sketched ruins; frontal (kept unflipped)
    "swsh12pt5gg-GG48": dict(
        kind="alt", sprite="zacian", text_y=592, grow=6,
        mask=dict(model=None, add=[[(175, 345), (250, 330), (250, 205), (335, 295), (420, 295), (500, 210),
                                    (470, 330), (545, 340), (530, 445), (480, 460), (425, 445), (410, 575),
                                    (335, 575), (325, 450), (260, 465), (180, 445)]]),
        tex_src=(545, 290, 690, 480), rim_col=(0.85, 1.0, 1.0), vig=(0.02, 0.08, 0.1), star=WHITE_STAR,
        frame="#5fb0b0", scene="the sketched ruins"),
    # the clay-figure diorama (a photograph, not a painting): Drapion only, the two Skorupi stay; head on the
    # right (vendor has it left of centre: flip)
    "swsh12pt5gg-GG49": dict(
        kind="alt", sprite="drapion", flip=True, text_y=600,
        mask=dict(model=ISNET, hull=[(175, 285), (235, 250), (300, 210), (380, 195), (420, 185), (485, 210),
                                     (515, 255), (525, 335), (470, 345), (430, 360), (425, 415), (330, 430),
                                     (265, 415), (245, 370), (210, 345), (175, 335)], keep=1, close=4),
        tex_src=(440, 480, 690, 600), rim_col=(1.0, 0.9, 0.75), vig=(0.1, 0.05, 0.02), star=GOLD_STAR,
        frame="#e0608c", scene="the clay diorama on the sand bluff"),
    # Hisuian Samurott wading at the autumn lake, head to the left (vendor faces left)
    "swsh12pt5gg-GG51": dict(
        kind="alt", sprite="samurott-hisui", text_y=650,
        mask=dict(model=ISNET, hull=[(285, 270), (360, 275), (400, 225), (445, 255), (480, 285), (535, 285),
                                     (570, 330), (525, 355), (505, 400), (545, 450), (600, 520), (565, 545),
                                     (515, 545), (485, 600), (415, 600), (360, 575), (300, 605), (215, 575),
                                     (215, 495), (300, 475), (325, 430), (335, 380), (325, 320), (290, 310)],
                  keep=1, close=4),
        tex_src=(40, 470, 200, 630), rim_col=(0.9, 1.0, 1.0), vig=(0.02, 0.06, 0.1), star=WHITE_STAR,
        frame="#f08c3c", scene="the autumn lake"),
    # Hoopa Unbound (the card shows the Unbound form: horns, six floating arms) in the treasure hoard; the
    # arms float free and go with it; frontal (kept unflipped)
    "swsh12pt5gg-GG53": dict(
        kind="alt", sprite="hoopa-unbound", text_y=680, top="v", boxes=((455, 98, 705, 172),),
        mask=dict(model=None, add=[[(295, 330), (400, 295), (470, 285), (565, 305), (570, 360), (605, 420),
                                    (565, 480), (555, 535), (625, 555), (685, 600), (675, 675), (620, 625),
                                    (550, 595), (500, 605), (450, 615), (375, 605), (315, 575), (295, 500),
                                    (325, 440), (325, 380)],
                                   [(115, 120), (200, 95), (275, 105), (265, 165), (200, 180), (125, 175)],
                                   [(75, 225), (135, 215), (175, 285), (175, 335), (105, 335), (85, 285)],
                                   [(590, 375), (650, 355), (705, 365), (705, 475), (615, 475), (590, 440)]],
                  keep=4),
        tex_src=(40, 350, 200, 500), rim_col=(1.0, 0.9, 0.7), vig=(0.08, 0.04, 0.0), star=GOLD_STAR,
        frame="#e05aa0", scene="the treasure hoard"),
    # Zamazenta Hero of Many Battles in the pop-art forest, head to the right (vendor faces left: flip)
    "swsh12pt5gg-GG54": dict(
        kind="alt", sprite="zamazenta", flip=True, text_y=620,
        mask=dict(model=None, add=[[(145, 380), (200, 335), (275, 290), (300, 235), (375, 195), (395, 155),
                                    (465, 165), (505, 215), (545, 205), (570, 260), (570, 345), (515, 355),
                                    (485, 425), (455, 475), (435, 510), (380, 490), (300, 475), (265, 465),
                                    (230, 510), (195, 465), (145, 445)]]),
        tex_src=(560, 400, 690, 600), rim_col=(1.0, 0.85, 0.9), vig=(0.08, 0.02, 0.08), star=PINK_STAR,
        frame="#e04a8c", scene="the pop-art forest"),
}

if __name__ == "__main__":
    czbatch.main(GROUP, TABLE)
