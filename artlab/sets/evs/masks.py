"""Masks of the real Pokemon on each card (white = Pokemon), card-px, -> masks/<id>.png + work/masks.png.

rembg (local ONNX models, no API) gives a first cut per card; each card then gets the model that caught its
Pokemon best, constrained by hand polygons (card px, read off work/grid_<n>.png), or a colour rule.

  ..\\..\\..\\.venv\\Scripts\\python masks.py
"""
import numpy as np
from PIL import Image
from scipy import ndimage

import evlib as E
import maskkit as K
from maskkit import MODELS, largest, poly, rect  # noqa: F401  (the helpers every set's recipes use, via this module)


def rembg(cid, model):
    """rembg mask of the current set's scan (E.ref_path), cached as E.WORK/rembg-<model>-<id>.png"""
    return K.rembg_cached(E.ref_path(cid), E.WORK / f"rembg-{model}-{cid}.png", model)


def eevee():
    cid = "swsh7-125"
    sh = E.card_img(cid).shape[:2]
    m = rembg(cid, "isnet-general-use") & rect(sh, 58, 96, 430, 468) & ~rect(sh, 370, 90, 600, 195)
    return cid, ndimage.binary_fill_holes(largest(m))


def sylveon():
    cid = "swsh7-74"
    sh = E.card_img(cid).shape[:2]
    m = rembg(cid, "u2net") & rect(sh, 30, 96, 710, 900) & ~rect(sh, 440, 96, 700, 165)
    return cid, ndimage.binary_fill_holes(largest(m, 2))


def glaceon():
    """Glaceon is cyan / white on a magenta shard field: a hue rule, inside Glaceon's hull"""
    from skimage.color import rgb2hsv
    cid = "swsh7-174"
    rgb = E.card_img(cid)
    sh = rgb.shape[:2]
    hsv = rgb2hsv(rgb)
    h, s, v = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
    col = ((h > 150) & (h < 250) & (s > 0.12)) | ((s < 0.16) & (v > 0.78)) | ((h > 170) & (h < 240) & (v < 0.5))
    hull = poly(sh, [(35, 60), (250, 60), (330, 190), (470, 185), (640, 110), (700, 90), (715, 300), (690, 560),
                     (640, 700), (600, 900), (450, 900), (120, 880), (100, 700), (40, 520)])
    m = col & hull
    m = ndimage.binary_opening(m, iterations=2)
    m = ndimage.binary_closing(m, iterations=4)
    return cid, largest(m)


def umbreon():
    """u2net takes Umbreon AND the tower it wraps around: cut the tower (spire + cone) back out"""
    cid = "swsh7-215"
    sh = E.card_img(cid).shape[:2]
    m = rembg(cid, "u2net") & poly(sh, [(240, 150), (560, 150), (700, 280), (700, 690), (330, 690), (240, 430)])
    tower = poly(sh, [(482, 118), (506, 118), (508, 318), (540, 380), (600, 520), (655, 700), (330, 700), (390, 520),
                      (452, 380), (480, 318)])
    body_front = poly(sh, [(500, 400), (560, 410), (650, 520), (660, 660), (560, 660), (520, 560)])  # hind leg + rings
    m = m & ~(tower & ~body_front)
    m = ndimage.binary_opening(m, iterations=2)
    return cid, largest(m, 3)


def leafeon():
    cid = "swsh7-204"
    sh = E.card_img(cid).shape[:2]
    m = rembg(cid, "isnet-general-use") & rect(sh, 0, 60, 734, 900)
    m = ndimage.binary_closing(m, iterations=8)
    return cid, ndimage.binary_fill_holes(largest(m, 3))


def windowed(cid, model="isnet-general-use", win=(58, 98, 688, 488), cut=(), keep=1, close=0):
    """a Pokemon inside the standard SWSH art window (common / uncommon / rare / holo layout)"""
    sh = E.card_img(cid).shape[:2]
    m = rembg(cid, model) & rect(sh, *win)
    for c in cut:
        m &= ~rect(sh, *c)
    if close:
        m = ndimage.binary_closing(m, iterations=close)
    return cid, ndimage.binary_fill_holes(largest(m, keep))


def pikachu():
    return windowed("swsh7-49")


def shelgon():
    return windowed("swsh7-108", cut=((0, 60, 310, 135),))


def altaria():
    """only Altaria's blue body is segmented; its cloud wings stay in the scene as clouds (the sprite brings
    its own cloud wings)"""
    return windowed("swsh7-106", cut=((0, 60, 310, 135),), keep=4, close=6)


def salamence():
    """the segmenters take the whole window here: a colour rule instead -- cyan-blue body, crimson wings,
    orange flame breath -- inside Salamence's hull"""
    from skimage.color import rgb2hsv
    cid = "swsh7-109"
    rgb = E.card_img(cid)
    sh = rgb.shape[:2]
    hsv = rgb2hsv(rgb)
    h, s_, v = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
    body = (h > 180) & (h < 225) & (s_ > 0.5) & (v > 0.3)
    wing = ((h > 320) | (h < 12)) & (s_ > 0.45) & (v > 0.25)
    fire = (h >= 12) & (h < 50) & (s_ > 0.55) & (v > 0.6)
    hull = poly(sh, [(60, 150), (330, 110), (560, 110), (640, 170), (640, 300), (600, 470), (240, 480), (60, 420)])
    m = (body | wing | fire) & hull & ~rect(sh, 0, 60, 310, 135)
    m = ndimage.binary_opening(m, iterations=1)
    m = ndimage.binary_closing(m, iterations=5)
    return cid, ndimage.binary_fill_holes(largest(m, 3))


def vaporeon():
    cid = "swsh7-30"
    sh = E.card_img(cid).shape[:2]
    m = rembg(cid, "isnet-anime") & rect(sh, 0, 60, 734, 900)
    return cid, ndimage.binary_fill_holes(largest(m))


def froslass():
    cid = "swsh7-226"
    sh = E.card_img(cid).shape[:2]
    m = rembg(cid, "u2net") & rect(sh, 30, 80, 704, 900)
    return cid, ndimage.binary_fill_holes(largest(m))


FNS = (eevee, sylveon, glaceon, umbreon, leafeon, pikachu, shelgon, altaria, salamence, vaporeon, froslass)


def main():
    E.MASKS.mkdir(exist_ok=True)
    E.WORK.mkdir(exist_ok=True)
    tiles = []
    for fn in FNS:
        cid, m = fn()
        Image.fromarray((m * 255).astype(np.uint8)).save(E.MASKS / f"{cid}.png")
        rgb = E.card_img(cid)
        o = np.where(m[..., None], rgb, rgb * 0.25 + np.array([0, 0.3, 0]))
        tiles.append(Image.fromarray(E.L.to8(o)).resize((367, 512)))
        ys, xs = np.nonzero(m)
        print(cid, "bbox", xs.min(), ys.min(), xs.max(), ys.max(), f"{m.mean():.2f}")
    sheet = Image.new("RGB", (367 * 6, 512 * 2))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % 6) * 367, (i // 6) * 512))
    sheet.save(E.WORK / "masks.png")


if __name__ == "__main__":
    main()
