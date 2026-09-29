r"""Crown Zenith, group gg_vstar: the Galarian Gallery Rare Holo VSTAR paintings (kind `alt`, the Umbreon VMAX 215
treatment via czcards.build_alt, ladder example Leafeon VSTAR GG35). The tier stays Rare Holo VSTAR.

Masks paint out only the card's own Pokemon (hand hulls in card px, read off work/grid_GG<n>.png); every other
character stays in the scene (Mewtwo GG44's Charizard / Blastoise / Machamp, Samurott GG52's Snorunt, the
background Simisear wallpaper on GG37, Regigigas GG55's floating island).
"""
import czbatch
from czcards import GOLD_STAR, WHITE_STAR, PINK_STAR

GROUP = "gg_vstar"


def not_cream(h, s, v):
    """Simisear GG37: everything that is not the flat cream ground (red body, black outline, yellow face)"""
    return ~((h > 35) & (h < 75) & (s < 0.3) & (v > 0.85))


def orange_blue(h, s, v):
    """Deoxys (Normal Forme): orange-red arms / body and the cyan arm stripes"""
    return (((h < 28) | (h > 352)) & (s > 0.42) & (v > 0.4)) | ((h > 180) & (h < 215) & (s > 0.35) & (v > 0.6))


TABLE = {
    "swsh12pt5gg-GG37": dict(
        kind="alt", sprite="simisear", text_y=522, texture=False, grow=8,
        mask=dict(model=None, colour=not_cream, colour_open=2, keep=1, close=4,
                  hull=[(112, 262), (140, 226), (270, 180), (318, 136), (368, 146), (440, 170), (446, 222),
                        (490, 214), (566, 232), (600, 282), (590, 322), (560, 348), (542, 384), (542, 452),
                        (500, 480), (462, 476), (462, 540), (240, 540), (248, 470), (228, 424), (186, 384),
                        (180, 330), (116, 316)]),
        frame="#f07068", rim_col=(1.0, 0.9, 0.85), vig=(0.1, 0.05, 0.02), star=GOLD_STAR,
        scene="the Simisear wallpaper"),
    "swsh12pt5gg-GG40": dict(
        kind="alt", sprite="glaceon", text_y=550, tex_src=(470, 430, 650, 540), grow=7,
        mask=dict(model="isnet-general-use", win=(200, 130, 560, 515), keep=1, close=3,
                  add=[[(390, 340), (440, 318), (500, 288), (565, 280), (560, 318), (512, 348), (452, 368),
                        (400, 380)]]),
        frame="#8fb8e8", rim_col=(0.85, 0.97, 1.0), vig=(0.02, 0.05, 0.12), star=WHITE_STAR,
        scene="the snowy wood"),
    "swsh12pt5gg-GG43": dict(
        kind="alt", sprite="zeraora", text_y=525, tex_src=(500, 280, 690, 420), grow=7,
        mask=dict(model="u2net", win=(200, 96, 490, 560), keep=1, close=3,
                  add=[[(262, 96), (475, 96), (492, 262), (440, 270), (300, 270), (258, 180)]]),
        frame="#f0c040", rim_col=(1.0, 0.95, 0.7), vig=(0.05, 0.02, 0.12), star=GOLD_STAR,
        scene="the storm-struck ruins"),
    "swsh12pt5gg-GG44": dict(
        kind="alt", sprite="mewtwo", text_y=552, tex_src=(430, 280, 560, 360), grow=7,
        mask=dict(model=None, add=[[(85, 202), (135, 206), (170, 218), (200, 236), (240, 232), (262, 290),
                                    (302, 318), (352, 338), (382, 388), (440, 418), (518, 405), (560, 365),
                                    (612, 365), (645, 400), (622, 445), (582, 472), (540, 482), (480, 472),
                                    (442, 500), (425, 525), (500, 535), (600, 522), (705, 512), (705, 560),
                                    (58, 560), (58, 462), (140, 458), (200, 448), (232, 400), (232, 350),
                                    (150, 338), (92, 336), (92, 298), (128, 288), (88, 255)]]),
        frame="#b48ce0", rim_col=(1.0, 0.92, 1.0), vig=(0.08, 0.04, 0.1), star=GOLD_STAR,
        scene="the psychic clash"),
    "swsh12pt5gg-GG46": dict(
        kind="alt", sprite="deoxys", flip=True, text_y=525, tex_src=(40, 120, 200, 280), grow=7,
        mask=dict(model=None, colour=orange_blue, keep=6, close=3,
                  hull=[(430, 200), (535, 195), (595, 212), (615, 258), (655, 300), (665, 400), (650, 485),
                        (560, 485), (500, 485), (370, 485), (295, 465), (285, 380), (285, 325), (318, 295),
                        (420, 265), (438, 235)],
                  add=[[(470, 200), (560, 205), (600, 250), (570, 290), (560, 330), (520, 345), (480, 375),
                        (440, 335), (470, 285)]]),
        frame="#f06040", rim_col=(1.0, 0.9, 0.85), vig=(0.08, 0.02, 0.12), star=PINK_STAR,
        scene="the psychic vortex"),
    "swsh12pt5gg-GG50": dict(
        kind="alt", sprite="darkrai", text_y=550, tex_src=(450, 410, 650, 500), grow=7,
        mask=dict(model="u2net", win=(190, 135, 560, 500), keep=1, close=3,
                  add=[[(420, 148), (512, 136), (525, 200), (472, 242), (432, 272), (398, 232)]]),
        frame="#5a6ab0", rim_col=(0.9, 0.9, 1.0), vig=(0.02, 0.02, 0.1), star=WHITE_STAR,
        scene="the moonlit shore"),
    "swsh12pt5gg-GG52": dict(
        kind="alt", sprite="samurott-hisui", text_y=555, tex_src=(40, 150, 210, 330), grow=7,
        mask=dict(model=None, add=[[(340, 94), (386, 94), (402, 148), (452, 162), (482, 198), (492, 244),
                                    (508, 300), (502, 340), (512, 442), (470, 448), (430, 422), (395, 400),
                                    (360, 400), (320, 422), (275, 448), (232, 442), (238, 340), (230, 300),
                                    (244, 244), (258, 198), (298, 162), (330, 148)]]),
        frame="#e0405a", rim_col=(1.0, 0.85, 0.9), vig=(0.12, 0.0, 0.04), star=PINK_STAR,
        scene="the crimson thicket"),
    "swsh12pt5gg-GG55": dict(
        kind="alt", sprite="regigigas", text_y=525, tex_src=(550, 440, 690, 520), grow=7,
        mask=dict(model=None, add=[[(240, 298), (290, 292), (330, 278), (402, 272), (432, 298), (472, 298),
                                    (502, 318), (542, 338), (568, 380), (562, 432), (512, 442), (472, 442),
                                    (482, 500), (472, 528), (260, 528), (240, 502), (222, 506), (202, 530),
                                    (144, 530), (144, 468), (174, 418), (200, 378), (238, 358)]]),
        frame="#d8a070", rim_col=(1.0, 0.95, 0.85), vig=(0.1, 0.06, 0.03), star=GOLD_STAR,
        scene="the floating island"),
    "swsh12pt5gg-GG56": dict(
        kind="alt", sprite="zoroark-hisui", text_y=555, tex_src=(560, 150, 695, 450), grow=7,
        mask=dict(model=None, add=[[(80, 190), (150, 118), (250, 106), (380, 106), (470, 126), (522, 198),
                                    (562, 278), (562, 378), (582, 450), (566, 560), (150, 560), (130, 470),
                                    (70, 400), (62, 300)]]),
        frame="#c8a060", rim_col=(1.0, 0.95, 0.85), vig=(0.06, 0.04, 0.02), star=GOLD_STAR,
        scene="the ghostly gale"),
}

if __name__ == "__main__":
    czbatch.main(GROUP, TABLE)
