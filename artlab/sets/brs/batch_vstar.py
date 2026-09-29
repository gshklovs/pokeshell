"""Brilliant Stars group `vstar`: the 3 Rare Holo VSTAR cards (ladder Charizard VSTAR 18; cz Leafeon VSTAR 14: VMAX
scene + platinum-gold frame + gold star-crest rays, anim vstar). The VSTAR Pokemon fill the card and every segmenter
takes the whole art window, so each mask is a generous whole-window hand hull (read off work/grid_<n>.png), with a
colour rule for the Pokemon's own colours where the hull leaves bits at the edges."""
import brsbatch

GROUP = "vstar"


def fit(h, text_y):
    """the crop ends at the text (text_y + 25): S from the sprite-driven H, W filling the card width"""
    H = h + 3
    S = (text_y + 25 - 80) / H
    Wd = int(704 // S)
    return dict(H=H, S=S, W=Wd, x0=6 + (704 - Wd * S) / 2)


def hull(pts, **kw):
    return dict(model=None, add=[pts], **kw)


TABLE = {
    "swsh9-14": dict(kind="vstar", sprite="shaymin-sky", text_y=555, grow=8, texture=False, **fit(22, 555),
                     scene="the pink flower blaze",
                     mask=hull([(30, 150), (130, 118), (200, 98), (420, 88), (640, 88), (665, 140), (575, 220),
                                (565, 300), (575, 380), (615, 410), (620, 480), (590, 570), (400, 570), (300, 525), (230, 485), (175, 445),
                                (115, 395), (30, 375)], close=3)),
    "swsh9-65": dict(kind="vstar", sprite="whimsicott", text_y=495, grow=8, texture=False,
                     scene="the wind swirl",
                     mask=hull([(150, 160), (250, 118), (380, 88), (625, 88), (645, 200), (665, 330), (625, 455),
                                (555, 495), (300, 510), (195, 480), (145, 385), (115, 300)], close=3)),
    "swsh9-123": dict(kind="vstar", sprite="arceus", flip=True, text_y=530, grow=8, texture=False,
                      scene="the violet star field",
                      mask=hull([(60, 140), (120, 108), (300, 88), (565, 88), (625, 110), (705, 160), (705, 305),
                                 (645, 330), (605, 380), (595, 445), (565, 485), (475, 505), (435, 565), (300, 510),
                                 (200, 485), (90, 445), (55, 300)], close=3)),
}

if __name__ == "__main__":
    brsbatch.main(GROUP, TABLE)
