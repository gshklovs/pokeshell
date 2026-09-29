r"""Crown Zenith, group gg_tg_b: the Galarian Gallery Trainer Gallery Rare Holo cards GG19-GG34 (kind `gallery`,
ladder example Lapras GG05). Full-bleed paintings: only the card's own Pokemon is painted out (other Pokemon in
the scene stay). Coordinates are card px read off work/grid_<n>.png.

  ..\..\..\.venv\Scripts\python batch_gg_tg_b.py rembg|masks|quick|all [ids]
"""
import czbatch
import czcards as C

GROUP = "gg_tg_b"
G = "swsh12pt5gg-"
WIN = (30, 92, 710, 700)

TABLE = {
    # Altaria in a pastel doll's bedroom, sitting on the bed; face frontal (ambiguous) -> unflipped
    G + "GG19": dict(kind="gallery", sprite="altaria", text_y=548,
                     mask=dict(model="isnet-general-use", hull=[(255, 245), (420, 245), (548, 295), (548, 380),
                                                                (565, 440), (565, 560), (262, 560), (262, 380),
                                                                (315, 330)], keep=1, close=4,
                               add=[[(330, 250), (410, 250), (420, 330), (330, 330)]]),
                     frame="#f2b8d0", rim_col=(1.0, 0.92, 0.97), vig=(0.1, 0.05, 0.1), star=C.PINK_STAR,
                     scene="the pastel bedroom"),
    # Latias flying through the laundry lines, head right -> flip; Fusion Strike badge under the HP
    G + "GG20": dict(kind="gallery", sprite="latias", flip=True, text_y=548, strike=True,
                     mask=dict(model=None, add=[[(145, 105), (215, 145), (290, 245), (340, 285), (378, 228),
                                                 (400, 196), (450, 180), (495, 192), (505, 240), (482, 275),
                                                 (435, 292), (445, 330), (470, 365), (612, 375), (615, 398),
                                                 (475, 420), (512, 468), (525, 535), (478, 545), (440, 505),
                                                 (400, 475), (330, 485), (290, 505), (245, 505), (225, 472),
                                                 (160, 445), (155, 378), (228, 372), (238, 332), (212, 300),
                                                 (185, 230)]]),
                     frame="#7ab8e8", rim_col=(1.0, 0.92, 0.9), vig=(0.02, 0.05, 0.12),
                     scene="the laundry lines"),
    # Hisuian Goodra with its shell, face to the left -> unflipped; the Murkrow-like birds and the dark bird with
    # the flower are other Pokemon and stay
    G + "GG21": dict(kind="gallery", sprite="goodra-hisui", text_y=548, texture=False, grow=7,
                     mask=dict(model=None, add=[[(135, 135), (260, 175), (350, 285), (400, 275), (415, 60),
                                                    (470, 35), (560, 35), (705, 55), (712, 480), (625, 480),
                                                    (560, 425), (430, 425), (405, 535), (300, 545), (195, 525),
                                                    (115, 505), (118, 440), (140, 380), (130, 250), (120, 160)]],
                               cut_after=[[(418, 425), (470, 408), (505, 440), (525, 470), (612, 468), (625, 565),
                                     (560, 605), (478, 605), (438, 545), (418, 482)],
                                    [(488, 62), (705, 62), (705, 200), (560, 200), (488, 135)]]),
                     frame="#b8a0e0", rim_col=(0.95, 0.93, 1.0), vig=(0.02, 0.06, 0.03),
                     scene="the forest glade"),
    # Ditto transformed into a Numel in a Numel herd: the big one with Ditto's face; frontal -> unflipped
    G + "GG22": dict(kind="gallery", sprite="ditto", text_y=612,
                     mask=dict(model=None, add=[[(412, 470), (438, 408), (500, 382), (560, 378), (592, 388),
                                                 (622, 376), (662, 372), (698, 392), (694, 432), (668, 442),
                                                 (668, 520), (655, 562), (655, 648), (428, 648), (418, 590),
                                                 (408, 530)]]),
                     frame="#8cc850", rim_col=(1.0, 1.0, 0.9), vig=(0.03, 0.08, 0.02),
                     scene="the Numel meadow"),
    # Dunsparce's bedroom: the foreground Dunsparce asleep under the blanket (below the text; the sleeping
    # Dunsparce on the shelves stay as scene); head left -> unflipped
    G + "GG23": dict(kind="gallery", sprite="dunsparce", text_y=552,
                     mask=dict(model=None, add=[[(40, 690), (120, 660), (230, 660), (320, 720), (330, 860),
                                                 (40, 880)]]),
                     frame="#4a78c8", rim_col=(1.0, 0.97, 0.8), vig=(0.02, 0.03, 0.12),
                     scene="the Dunsparce bedroom"),
    # Miltank at the farm table; frontal (ambiguous) -> unflipped
    G + "GG24": dict(kind="gallery", sprite="miltank", text_y=548,
                     mask=dict(model="isnet-general-use", hull=[(205, 300), (238, 250), (285, 150), (425, 145),
                                                                (485, 168), (475, 232), (465, 300), (500, 325),
                                                                (550, 330), (550, 385), (505, 440), (300, 440),
                                                                (296, 340), (255, 340)], keep=1, close=4,
                               add=[[(300, 160), (470, 160), (470, 330), (300, 330)]]),
                     frame="#e89048", rim_col=(1.0, 0.9, 0.7), vig=(0.1, 0.04, 0.02),
                     scene="the autumn farm"),
    # Bibarel in its dam window (the Bidoof around stay), head right -> flip
    G + "GG25": dict(kind="gallery", sprite="bibarel", flip=True, text_y=548,
                     mask=dict(model=None, add=[[(198, 400), (213, 352), (258, 342), (298, 328), (298, 288),
                                                 (328, 262), (422, 262), (448, 300), (442, 338), (482, 342),
                                                 (502, 378), (512, 440), (507, 490), (360, 494), (300, 474),
                                                 (240, 474), (203, 442)]]),
                     frame="#48b0e0", rim_col=(0.9, 0.97, 1.0), vig=(0.02, 0.05, 0.12),
                     scene="the beaver dam"),
    # Riolu lunging to the right -> flip
    G + "GG26": dict(kind="gallery", sprite="riolu", flip=True, text_y=630,
                     mask=dict(model="isnet-general-use", keep=1, close=4,
                               add=[[(35, 110), (200, 60), (340, 100), (360, 200), (430, 190), (520, 250),
                                     (600, 240), (668, 270), (668, 335), (590, 372), (545, 420), (595, 460),
                                     (605, 522), (520, 545), (400, 525), (345, 562), (335, 605), (200, 612),
                                     (168, 540), (128, 452), (108, 382), (35, 262)]],
                               cut_after=[(30, 612, 734, 1024)]),
                     frame="#6aa0d0", rim_col=(0.9, 0.95, 1.0), vig=(0.02, 0.06, 0.06),
                     scene="the pine forest"),
    # Swablu in the sky (the clouds stay), facing right -> flip
    G + "GG27": dict(kind="gallery", sprite="swablu", flip=True, text_y=625,
                     mask=dict(model="isnet-general-use", hull=[(240, 150), (360, 150), (470, 230), (490, 330),
                                                                (440, 430), (330, 440), (250, 360), (245, 250)],
                               keep=1, close=4),
                     frame="#8ccaf0", rim_col=(1.0, 1.0, 1.0), vig=(0.02, 0.05, 0.12),
                     scene="the mountain sky"),
    # Duskull in the dark forest, eye to the left -> unflipped
    G + "GG28": dict(kind="gallery", sprite="duskull", text_y=628, texture=False, grow=7,
                     mask=dict(model="isnet-general-use", keep=1, close=4,
                               hull=[(270, 50), (370, 50), (380, 140), (470, 160), (600, 200), (712, 230),
                                     (712, 610), (560, 610), (470, 620), (380, 590), (320, 565), (250, 535),
                                     (135, 505), (145, 445), (260, 415), (280, 330), (270, 230), (260, 150)],
                               add=[[(270, 50), (370, 50), (380, 140), (470, 160), (560, 190), (560, 540),
                                     (470, 600), (380, 580), (320, 560), (250, 530), (140, 500), (150, 450),
                                     (260, 420), (280, 330), (270, 230), (260, 150)]]),
                     frame="#9070b0", rim_col=(0.95, 0.9, 1.0), vig=(0.06, 0.02, 0.1),
                     scene="the dusky forest"),
    # Bidoof in the sunlit wood, facing right -> flip
    G + "GG29": dict(kind="gallery", sprite="bidoof", flip=True, text_y=545,
                     mask=dict(model="isnet-anime", keep=1, close=4,
                               add=[[(60, 480), (90, 380), (160, 300), (220, 230), (240, 170), (290, 88),
                                     (352, 88), (392, 160), (442, 190), (474, 240), (474, 340), (455, 380),
                                     (475, 452), (442, 485), (400, 472), (382, 560), (60, 560)]]),
                     frame="#c89048", rim_col=(1.0, 0.95, 0.8), vig=(0.05, 0.05, 0.02),
                     scene="the sunlit wood"),
    # Pikachu with a leaf umbrella (the leaf stays), tail right like the sprite -> unflipped
    G + "GG30": dict(kind="gallery", sprite="pikachu", text_y=545,
                     mask=dict(model="isnet-general-use", keep=1, close=4,
                               hull=[(190, 90), (330, 50), (420, 230), (480, 240), (712, 300), (712, 560),
                                     (150, 560), (150, 350), (200, 250)],
                               add=[[(150, 330), (190, 310), (240, 230), (270, 140), (330, 60), (392, 60),
                                     (352, 170), (400, 200), (470, 190), (540, 180), (600, 190), (560, 232),
                                     (500, 262), (520, 300), (540, 360), (640, 300), (712, 300), (712, 522),
                                     (560, 527), (470, 502), (420, 472), (330, 552), (250, 552), (240, 482),
                                     (200, 432), (160, 382)],
                                    [(488, 158), (615, 165), (615, 245), (500, 272)],
                                    [(325, 45), (425, 45), (425, 145), (345, 175)]]),
                     frame="#a8c860", rim_col=(1.0, 1.0, 0.85), vig=(0.03, 0.06, 0.02),
                     scene="the rainy wood"),
    # Turtwig on a mossy rock, facing left -> unflipped
    G + "GG31": dict(kind="gallery", sprite="turtwig", text_y=605,
                     mask=dict(model="isnet-general-use", win=(30, 92, 710, 540), keep=1, close=4,
                               add=[[(270, 250), (330, 210), (420, 215), (480, 280), (512, 330), (512, 440),
                                     (470, 478), (330, 478), (290, 420), (270, 340)]]),
                     frame="#78b060", rim_col=(1.0, 1.0, 0.9), vig=(0.02, 0.06, 0.03),
                     scene="the mossy rock"),
    # Paras among the flowers; frontal (ambiguous) -> unflipped
    G + "GG32": dict(kind="gallery", sprite="paras", text_y=628,
                     mask=dict(model="isnet-general-use", win=(30, 150, 710, 500), keep=1, close=4,
                               add=[[(100, 260), (160, 218), (260, 188), (330, 188), (390, 228), (470, 238),
                                     (532, 278), (548, 340), (522, 422), (420, 442), (330, 452), (250, 442),
                                     (200, 472), (160, 528), (118, 512), (128, 440), (108, 380), (98, 320)]]),
                     frame="#e0c050", rim_col=(1.0, 0.95, 0.85), vig=(0.05, 0.05, 0.02),
                     scene="the flower meadow"),
    # Poochyena running to the left -> unflipped
    G + "GG33": dict(kind="gallery", sprite="poochyena", text_y=605,
                     mask=dict(model="isnet-anime", win=(30, 92, 710, 700), keep=1, close=4),
                     frame="#c8b060", rim_col=(1.0, 0.97, 0.85), vig=(0.04, 0.05, 0.02),
                     scene="the forest path"),
    # Mareep in the bushes, facing left -> unflipped
    G + "GG34": dict(kind="gallery", sprite="mareep", text_y=605,
                     mask=dict(model="isnet-anime", win=(30, 92, 690, 700), keep=1, close=4),
                     frame="#e8c040", rim_col=(1.0, 1.0, 0.85), vig=(0.03, 0.05, 0.02),
                     scene="the leafy thicket"),
}

if __name__ == "__main__":
    czbatch.main(GROUP, TABLE)
