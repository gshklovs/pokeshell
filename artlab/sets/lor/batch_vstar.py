"""Lost Origin group `vstar`: the 5 Rare Holo VSTAR cards (ladder Giratina VSTAR 131; cz Leafeon VSTAR 14: VMAX
scene + platinum-gold frame + gold star-crest rays, anim vstar). The VSTAR Pokemon fill the art, so each mask is a
generous hand hull (card px read off work/grid_<n>.png) and the fill is smooth (texture=False) against ghosts, as
the ladder's Giratina VSTAR. text_y = the top of the first attack's cost icons.

The smooth-fill fix this batch found (s3lib.pushpull left unknown top-level cells black) now lives in
lorlib.pushpull_1x1 and applies to the whole set."""

import lorbatch



GROUP = "vstar"


def hull(*pts, **kw):
    return dict(model=None, add=list(pts), **kw)


TABLE = {
    # the eye-and-magnet body seen three-quarter; the sprite's eye side kept on the left (ambiguous pose)
    "swsh11-57": dict(kind="vstar", sprite="magnezone", text_y=490, texture=False, grow=8,
                      scene="the electric shards",
                      mask=hull([(150, 470), (150, 400), (175, 340), (230, 290), (280, 250), (282, 150), (300, 128),
                                 (330, 135), (340, 205), (400, 195), (470, 165), (530, 140), (610, 130), (660, 170),
                                 (670, 230), (705, 290), (705, 500), (150, 500)],
                                [(30, 455), (160, 455), (160, 500), (30, 500)], keep=2, close=3)),
    # head top right, the open jaw pointing right: flipped
    "swsh11-93": dict(kind="vstar", sprite="aerodactyl", flip=True, text_y=522, texture=False, grow=8,
                      scene="the neon aurora",
                      mask=hull([(30, 290), (50, 200), (120, 150), (200, 160), (290, 190), (340, 150), (390, 105),
                                 (450, 92), (705, 92), (705, 530), (30, 530)], close=3)),
    # head centre-left, facing the viewer's left, the big arms on the right: as the sprite
    "swsh11-119": dict(kind="vstar", sprite="drapion", text_y=492, texture=False, grow=8,
                       boxes=[(0, 80, 734, 102)],  # the dark name bar's lower edge (a dark smudge in the fill)
                       scene="the toxic lightning",
                       mask=hull([(30, 290), (100, 262), (160, 245), (240, 195), (300, 150), (350, 105), (420, 92),
                                  (705, 92), (705, 500), (30, 500)], close=3)),
    # head on the right, facing right: flipped. The shell fills the left edge too; a 18-px strip at the frame
    # (shell edge under the yellow sparks) is kept as the smooth fill's seed, else the left fills black
    "swsh11-136": dict(kind="vstar", sprite="goodra-hisui", flip=True, text_y=525, texture=False, grow=8,
                       scene="the starry iron shell",
                       mask=hull([(48, 130), (130, 95), (705, 92), (705, 380), (660, 420), (645, 530), (48, 530)],
                                 close=3)),
    # near-frontal: the head centre-left, turned to the viewer's left (as the sprite; ambiguous)
    "swsh11-147": dict(kind="vstar", sprite="zoroark-hisui", text_y=555, texture=False, grow=8,
                       scene="the phantom night",
                       mask=hull([(30, 150), (80, 100), (560, 95), (690, 125), (705, 330), (610, 345), (570, 430),
                                  (610, 500), (650, 560), (30, 560)], close=3)),
}

if __name__ == "__main__":
    lorbatch.main(GROUP, TABLE)
