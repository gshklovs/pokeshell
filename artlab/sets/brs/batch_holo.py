"""Brilliant Stars group `holo`: the 7 Rare Holo cards (ladder Torterra 8; evs Salamence 109: holo_scene in the SWSH
window, anim holo). Every mask is a generous hand hull in card px (read off work/grid_<n>.png)."""
import brsbatch

GROUP = "holo"


def hull(*pts):
    return dict(model=None, add=[list(pts)])


# Everything outside the SWSH art window is painted out too, so the texture fill never mirrors the name bar, the
# "Evolves from" plate or the stat line into the window (cz batch_holo's OUT); window_rgb replaces that area anyway.
OUT = ((0, 0, 734, 97), (0, 488, 734, 1024), (0, 0, 57, 1024), (682, 0, 734, 1024))


TABLE = {
    "swsh9-21": dict(kind="holo", boxes=OUT, sprite="moltres", scene="the fire streak", texture=False, W=56, x0=120, mask=hull(
        (290, 170), (330, 140), (380, 160), (420, 230), (470, 160), (560, 105), (640, 100), (680, 110), (680, 480),
        (430, 480), (380, 470), (300, 460), (215, 450), (225, 410), (300, 400), (295, 340), (275, 280))),
    "swsh9-26": dict(kind="holo", boxes=OUT, sprite="infernape", flip=True, scene="the sky vortex", mask=hull(
        (180, 125), (290, 110), (380, 105), (450, 160), (530, 170), (600, 185), (600, 235), (520, 240), (470, 290),
        (420, 330), (390, 360), (375, 420), (372, 468), (300, 470), (290, 425), (250, 405), (212, 472), (92, 472),
        (92, 398), (140, 358), (160, 300), (210, 280), (230, 230), (200, 200), (170, 160))),
    "swsh9-37": dict(kind="holo", boxes=OUT, sprite="empoleon", scene="the ice floe", mask=hull(
        (300, 100), (440, 100), (430, 190), (470, 230), (540, 270), (620, 295), (688, 330), (688, 415), (590, 395),
        (520, 375), (495, 400), (485, 475), (290, 475), (280, 395), (230, 375), (118, 360), (112, 298), (200, 265),
        (290, 235), (310, 200), (345, 190))),
    "swsh9-62": dict(kind="holo", boxes=OUT, sprite="dusknoir", scene="the dark wood", texture=False, mask=hull(
        (240, 100), (470, 98), (540, 160), (565, 220), (605, 280), (615, 380), (565, 465), (525, 482), (225, 482),
        (200, 425), (150, 425), (95, 385), (95, 300), (140, 255), (200, 245), (245, 225), (235, 160))),
    "swsh9-79": dict(kind="holo", boxes=OUT, sprite="lucario", scene="the aura sphere", mask=hull(
        (250, 120), (290, 105), (345, 120), (345, 190), (390, 215), (440, 195), (510, 200), (555, 225), (545, 280),
        (470, 310), (450, 340), (480, 375), (560, 400), (565, 484), (420, 484), (300, 484), (200, 484), (192, 400),
        (172, 365), (155, 315), (212, 298), (218, 215), (240, 200))),
    "swsh9-109": dict(kind="holo", boxes=OUT, sprite="garchomp", flip=True, scene="the forest stumps", mask=hull(
        (95, 150), (160, 132), (280, 128), (330, 112), (410, 122), (455, 175), (475, 222), (560, 242), (650, 282),
        (668, 390), (645, 435), (600, 465), (540, 475), (470, 484), (160, 484), (158, 420), (200, 370), (250, 345),
        (250, 292), (200, 258), (110, 250), (92, 200))),
    "swsh9-121": dict(kind="holo", boxes=OUT, sprite="bibarel", scene="the dam in the stream", mask=hull(
        (262, 140), (295, 118), (425, 125), (435, 180), (465, 228), (515, 248), (515, 305), (485, 355), (425, 385),
        (295, 385), (255, 335), (215, 315), (195, 270), (205, 218), (265, 198))),
}

if __name__ == "__main__":
    brsbatch.main(GROUP, TABLE)
