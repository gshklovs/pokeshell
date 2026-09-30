"""Lost Origin group `rainbow`: the true Rare Rainbows (pastel rainbow wash, not paintings), built like the ladder's
Giratina VSTAR 201 (evs Leafeon VMAX 204: smooth fill, rainbow sprite 0.55, rainbow ground, etch, glitter).
The Pokemon covers most of each art, so the masks are generous hand hulls along the silhouette (card px,
work/grid_<n>.png), leaving the card's own pastel ground wherever it shows.

The smooth-fill fix this batch found (s3lib.pushpull left unknown top-level cells black) now lives in
lorlib.pushpull_1x1 and applies to the whole set."""

import lorbatch



def hand(*polys, close=0):
    return dict(model=None, add=list(polys), close=close)


GROUP = "rainbow"
TABLE = {
    # Kyurem VMAX (Dynamax: plain sprite): head top centre looking right, like the ladder's VMAX 49 -> flip;
    # the VMAX header (logo, Dynamax tag) instead of the VSTAR one; HP circle's lower edge boxed
    "swsh11-197": dict(kind="rainbow", sprite="kyurem", flip=True, top="vmax", text_y=565, scene="the rainbow blizzard",
                       boxes=[(420, 70, 705, 104), (0, 140, 62, 272)],
                       mask=hand([(40, 515), (40, 470), (60, 420), (120, 372), (168, 375), (182, 300), (212, 245),
                                  (125, 240), (118, 150), (230, 108), (300, 92), (460, 92), (470, 145), (570, 145),
                                  (592, 180), (705, 155), (705, 570), (40, 570)])),
    # Magnezone: near-frontal, the big eye and the magnet units lean to the viewer's left like the vendor sprite
    # -> unflipped (ambiguous)
    "swsh11-198": dict(kind="rainbow", sprite="magnezone", text_y=495, scene="the rainbow field",
                       mask=hand([(30, 425), (80, 378), (148, 330), (178, 262), (275, 192), (285, 132), (362, 125),
                                  (372, 185), (448, 165), (520, 132), (600, 122), (682, 142), (705, 185),
                                  (705, 500), (30, 500)])),
    # Aerodactyl: head top right, jaws open toward the right -> flip
    "swsh11-199": dict(kind="rainbow", sprite="aerodactyl", flip=True, text_y=528, scene="the rainbow sky",
                       mask=hand([(30, 262), (60, 228), (132, 218), (138, 188), (198, 115), (242, 120), (238, 212),
                                  (320, 212), (355, 215), (400, 160), (440, 95), (560, 92), (705, 92), (705, 290),
                                  (678, 318), (675, 535), (30, 535)])),
    # Drapion: head on the left, looking left -> unflipped
    "swsh11-200": dict(kind="rainbow", sprite="drapion", text_y=495, scene="the rainbow haze",
                       mask=hand([(30, 300), (80, 268), (118, 245), (200, 245), (228, 198), (300, 205), (348, 178),
                                  (358, 108), (420, 92), (705, 92), (705, 500), (30, 500)])),
    # Hisuian Goodra: shell on the left, head on the right looking right/down -> flip
    "swsh11-202": dict(kind="rainbow", sprite="goodra-hisui", flip=True, text_y=528, scene="the rainbow dew",
                       mask=hand([(30, 425), (30, 92), (705, 92), (705, 535),
                                  (150, 535), (140, 448), (90, 438), (30, 442)])),
    # Hisuian Zoroark: the same illustration as the gold 213; lunging to the left, snout down-left -> unflipped
    "swsh11-203": dict(kind="rainbow", sprite="zoroark-hisui", text_y=555, scene="the rainbow phantom",
                       mask=hand([(30, 425), (30, 252), (80, 212), (160, 172), (260, 130), (360, 108), (460, 92),
                                  (705, 92), (705, 560), (30, 560)])),
}
if __name__ == "__main__":
    lorbatch.main(GROUP, TABLE)
