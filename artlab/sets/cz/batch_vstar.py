"""Crown Zenith group `vstar`: the Rare Holo VSTAR cards (ladder: Leafeon VSTAR 14).

The VSTAR Pokemon fill the card and every segmenter takes the whole art window, so each mask is a generous hand
hull of the whole Pokemon (flames, auras, tails, swords included; read off work/grid_<n>.png), grown by 8, and
the hole is filled with the texture fill from a hand-picked patch of the card's own background (`tex_src`)."""
import czbatch

GROUP = "vstar"


def fit(h, text_y):
    """the crop ends at the text (text_y + 25): S from the sprite-driven H, W filling the card width (the builder's
    full_geo runs a tall sprite's crop far down into the painted-out text half)"""
    H = h + 3
    S = (text_y + 25 - 80) / H
    Wd = int(704 // S)
    return dict(H=H, S=S, W=Wd, x0=6 + (704 - Wd * S) / 2)


def hull(pts):
    return dict(model=None, add=[pts])


TABLE = {
    "swsh12pt5-19": dict(kind="vstar", sprite="charizard", flip=True, text_y=560, grow=8, **fit(39, 560),
                         tex_src=(500, 475, 700, 560), scene="the teal flame swirl",
                         mask=dict(model=None, hull=[(30, 88), (720, 88), (720, 570), (30, 570)], close=3,
                                   # the orange wing / flame bits the hull leaves at the top and by the belly
                                   colour=lambda h, s, v: (h > 5) & (h < 50) & (s > 0.45) & (v > 0.5),
                                   add=[[(30, 130), (90, 150), (170, 160), (230, 195), (300, 150), (380, 105), (560, 88),
                                    (705, 88), (720, 200), (720, 470), (640, 472), (570, 500), (510, 500), (482, 470),
                                    (472, 570), (30, 570)]])),
    "swsh12pt5-23": dict(kind="vstar", sprite="simisear", text_y=535, grow=8,
                         tex_src=(40, 100, 150, 260), scene="the blue fire swirl",
                         mask=dict(model=None, hull=[(30, 88), (720, 88), (720, 570), (30, 570)], close=3,
                                   # the pink crest / fur the hull leaves at the top edge
                                   colour=lambda h, s, v: ((h < 45) | (h > 300)) & (s > 0.35) & (v > 0.35),
                                   add=[[(30, 300), (100, 275), (150, 225), (165, 160), (230, 105), (330, 90), (450, 95),
                                    (560, 145), (585, 225), (700, 245), (720, 290), (720, 500), (645, 545),
                                    (30, 550)]])),
    "swsh12pt5-46": dict(kind="vstar", sprite="rotom", text_y=535, grow=8,
                         tex_src=(530, 105, 700, 285), scene="the plasma smoke",
                         mask=hull([(150, 135), (260, 105), (420, 95), (485, 108), (475, 200), (505, 275), (560, 295),
                                    (720, 315), (720, 525), (560, 545), (400, 505), (300, 485), (210, 465),
                                    (140, 545), (30, 545), (30, 415), (145, 415), (195, 375), (165, 300)])),
    "swsh12pt5-55": dict(kind="vstar", sprite="zeraora", text_y=525, grow=8, **fit(32, 525),
                         tex_src=(440, 100, 620, 235), scene="the violet night",
                         mask=dict(model=None, hull=[(30, 88), (720, 88), (720, 570), (30, 570)], close=3,
                                   # the yellow fur the hull leaves at the edges
                                   colour=lambda h, s, v: (h > 42) & (h < 68) & (s > 0.5) & (v > 0.6),
                                   add=[[(30, 235), (80, 185), (145, 155), (155, 105), (250, 112), (310, 155), (360, 195),
                                    (420, 185), (470, 235), (560, 225), (640, 195), (720, 235), (720, 565),
                                    (30, 565)]])),
    "swsh12pt5-96": dict(kind="vstar", sprite="zacian", flip=True, text_y=560, grow=8, **fit(35, 560),
                         tex_src=(35, 445, 165, 560), scene="the starfield",
                         mask=dict(model=None, hull=[(30, 88), (720, 88), (720, 570), (30, 570)], close=3,
                                   # the gold sword / crown, blue mane and red scarf bits the hull leaves at the top edge
                                   colour=lambda h, s, v: (((h > 35) & (h < 65)) | ((h > 190) & (h < 230)) | (h < 15)) & (s > 0.4) & (v > 0.4),
                                   add=[[(30, 225), (120, 195), (200, 145), (300, 125), (430, 115), (480, 88), (625, 88),
                                    (720, 145), (720, 475), (640, 482), (620, 575), (420, 575), (300, 505), (262, 565),
                                    (168, 565), (168, 455), (30, 445)]])),
    # Zamazenta fills the card, its red / gold mane reaching the left edge: the only background left is the green
    # aurora between the mane arcs (cut back out of the hull) and the lightning at the bottom right
    "swsh12pt5-99": dict(kind="vstar", sprite="zamazenta", text_y=525, grow=8, **fit(38, 525),
                         tex_src=(480, 175, 600, 280), scene="the aurora",
                         mask=dict(model=None, hull=[(30, 92), (200, 92), (200, 570), (30, 570)],
                                   colour=lambda h, s, v: ((h < 65) | (h > 320)) & (s > 0.2) & (v > 0.25),
                                   close=3, fill=False,  # keep the green notch open
                                   add=[[(30, 380), (128, 358), (148, 250), (195, 148), (258, 100), (420, 92),
                                         (560, 88), (720, 88), (720, 535), (660, 570), (30, 570)]],
                                   cut_after=[[(465, 170), (600, 165), (625, 280), (480, 288)]])),
    "swsh12pt5-114": dict(kind="vstar", sprite="regigigas", text_y=525, grow=8,
                          tex_src=(40, 100, 240, 240), scene="the thunderhead",
                          mask=hull([(30, 250), (150, 235), (228, 245), (268, 178), (298, 125), (360, 105), (540, 115),
                                     (562, 165), (640, 165), (720, 225), (720, 480), (600, 565), (30, 565)])),
}
if __name__ == "__main__":
    czbatch.main(GROUP, TABLE)
