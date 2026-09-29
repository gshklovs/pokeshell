r"""Masks of the real Pokemon on each 30th Celebration pick (white = Pokemon), card px -> masks/<id>.png +
work/masks.png. Same method as evs/masks.py (whose rembg / poly / rect / largest helpers are reused): rembg
(local ONNX, no API) where a model catches the Pokemon, otherwise a colour rule inside a hand hull (card px,
read off work/grid_<n>.png).

  ..\..\..\.venv\Scripts\python p30masks.py
"""
import numpy as np
from PIL import Image
from scipy import ndimage
from skimage.color import rgb2hsv

import p30lib as P
import masks as M                     # evs/masks.py (helpers only; its rembg cache is E.WORK = p30/work)

E = P.E
poly, rect, largest, rembg = M.poly, M.rect, M.largest, M.rembg


def hsv(cid):
    rgb = E.card_img(cid)
    h = rgb2hsv(rgb)
    return rgb, h[..., 0] * 360, h[..., 1], h[..., 2]


def mew():
    """rembg takes the whole window: Mew is the only soft pink in the forest; tail by a thin hull"""
    cid = "me55-65"
    rgb, h, s, v = hsv(cid)
    sh = rgb.shape[:2]
    pink = ((h > 295) | (h < 25)) & (s > 0.08) & (s < 0.62) & (v > 0.45)
    body = poly(sh, [(282, 125), (330, 120), (395, 128), (440, 130), (470, 170), (455, 225), (420, 240), (398, 272),
                     (372, 318), (345, 380), (318, 385), (300, 360), (282, 300), (270, 245), (290, 190)])
    tail = poly(sh, [(150, 118), (175, 110), (190, 190), (200, 280), (215, 318), (250, 305), (285, 250), (292, 262),
                     (240, 335), (205, 340), (178, 290), (165, 200)])
    m = pink & body
    m = ndimage.binary_closing(m, iterations=4)
    m = largest(ndimage.binary_opening(m, iterations=1))
    t = ndimage.binary_closing(pink & tail, iterations=2)
    t = ndimage.binary_opening(t, iterations=1)
    return cid, ndimage.binary_fill_holes(m | largest(t, 2))


def pikachu():
    """isnet-general-use has the body, u2net adds the tail tip; both only inside the art window"""
    cid = "me55-23"
    sh = E.card_img(cid).shape[:2]
    win = rect(sh, 52, 88, 606, 432)
    m = (rembg(cid, "isnet-general-use") | rembg(cid, "u2net")) & win
    m &= poly(sh, [(180, 95), (250, 100), (290, 175), (390, 100), (560, 100), (560, 170), (470, 250), (440, 380),
                   (360, 425), (220, 425), (180, 300)])
    tail = poly(sh, [(395, 155), (545, 100), (560, 140), (500, 200), (478, 245), (452, 330), (425, 335), (420, 250)])
    yellow = (rgb2hsv(E.card_img(cid))[..., 0] * 360 < 70) & (rgb2hsv(E.card_img(cid))[..., 1] > 0.35)
    m |= tail & ndimage.binary_closing(yellow, iterations=2)
    return cid, ndimage.binary_fill_holes(largest(ndimage.binary_closing(m, iterations=3)))


def umbreon():
    """isnet-general-use has the head; the ear, back and ringed foreleg come from a colour rule (near-black
    fur, yellow rings, red eye) inside Umbreon's whole hull. The light streaks crossing him are cut out by
    the rule and closed back over"""
    cid = "me55-92"
    rgb, h, s_, v = hsv(cid)
    sh = rgb.shape[:2]
    m = rembg(cid, "isnet-general-use") & rect(sh, 0, 80, 652, 560) & ~rect(sh, 0, 55, 160, 175)
    hull = poly(sh, [(40, 110), (160, 88), (560, 88), (610, 200), (652, 320), (652, 530), (520, 548), (330, 505),
                     (200, 470), (60, 360), (28, 250)])
    fur = (v < 0.3) & (s_ < 0.75)
    ring = (h > 35) & (h < 70) & (s_ > 0.45) & (v > 0.45)
    eye = ((h > 330) | (h < 15)) & (s_ > 0.45)
    c = hull & ndimage.binary_opening(fur | ring | eye, iterations=2)
    c = ndimage.binary_closing(c, iterations=7)
    m = (m | c) & ~rect(sh, 20, 330, 175, 465)             # the 30th stamp is a box of its own
    m = ndimage.binary_closing(m, iterations=4)
    return cid, ndimage.binary_fill_holes(largest(m, 2))


def lapras():
    """segmenters miss Lapras on the pastel ground: blue neck/body + purple-grey shell, inside Lapras's hull"""
    cid = "me55-131"
    rgb, h, s, v = hsv(cid)
    sh = rgb.shape[:2]
    blue = (h > 190) & (h < 235) & (s > 0.38) & (v > 0.3)
    shell = (h > 235) & (h < 320) & (s > 0.1) & (s < 0.55) & (v > 0.25) & (v < 0.8)
    hull = poly(sh, [(330, 125), (440, 118), (455, 175), (440, 300), (470, 330), (500, 380), (560, 390), (640, 395),
                     (645, 470), (470, 470), (300, 440), (270, 400), (285, 330), (330, 300), (360, 220)])
    m = (blue | shell) & hull
    m = ndimage.binary_opening(m, iterations=1)
    m = ndimage.binary_closing(m, iterations=6)
    return cid, ndimage.binary_fill_holes(largest(m, 2))


def gengar():
    """isnet takes the pink sky too: Gengar's violet body + white grin + red eyes, inside his hull"""
    cid = "me55-154"
    rgb, h, s, v = hsv(cid)
    sh = rgb.shape[:2]
    violet = (h > 232) & (h < 305) & (s > 0.18) & (v > 0.1)
    grin = (s < 0.2) & (v > 0.8)
    eye = ((h > 340) | (h < 10)) & (s > 0.5) & (v > 0.5)
    hull = poly(sh, [(70, 160), (120, 120), (180, 110), (250, 95), (330, 105), (390, 150), (440, 230), (455, 300),
                     (430, 360), (370, 410), (300, 440), (180, 440), (100, 400), (62, 300)])
    m = (violet | grin | eye) & hull
    m = ndimage.binary_closing(m, iterations=8)
    m = ndimage.binary_opening(m, iterations=2)
    return cid, ndimage.binary_fill_holes(largest(m))


def mewtwo():
    """u2net has Mewtwo (plus the orange orb behind his right shoulder, cut back out where it is not violet)"""
    cid = "me55-157"
    rgb, h, s, v = hsv(cid)
    sh = rgb.shape[:2]
    m = rembg(cid, "u2net") & rect(sh, 0, 90, 652, 914)
    yy, xx = np.mgrid[0:sh[0], 0:sh[1]]
    orb = np.hypot(xx - 505, yy - 365) < 118
    violet = (h > 240) & (h < 320)
    m &= ~(orb & ~violet & ~rect(sh, 380, 250, 470, 500))
    m = ndimage.binary_opening(m, iterations=2)
    return cid, ndimage.binary_fill_holes(largest(m))


FNS = (mew, pikachu, umbreon, lapras, gengar, mewtwo)


def main():
    E.MASKS.mkdir(exist_ok=True)
    tiles = []
    for fn in FNS:
        cid, m = fn()
        Image.fromarray((m * 255).astype(np.uint8)).save(E.MASKS / f"{cid}.png")
        rgb = E.card_img(cid)
        o = np.where(m[..., None], rgb, rgb * 0.25 + np.array([0, 0.3, 0]))
        tiles.append(Image.fromarray(E.L.to8(o)).resize((326, 457)))
        ys, xs = np.nonzero(m)
        print(cid, "bbox", xs.min(), ys.min(), xs.max(), ys.max(), f"{m.mean():.2f}")
    sheet = Image.new("RGB", (326 * 3, 457 * 2))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % 3) * 326, (i // 3) * 457))
    sheet.save(E.WORK / "masks.png")


if __name__ == "__main__":
    main()
