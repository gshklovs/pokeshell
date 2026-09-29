r"""Masks of the real Pokemon on the Base Set ladder cards (white = Pokemon), card px -> masks/<id>.png +
work/masks-ladder.png. The evs / p30 / hf method (docs/ART_METHOD.md section 6): rembg (local ONNX, no API) inside
the card's art window, hand hulls and colour rules read off work/grid_<n>.png. The batch modules reuse the helpers
(poly, rect, largest, rembg, hsv, base_window, fin) and BASE_WIN / STAGE.

  ..\..\..\.venv\Scripts\python basemasks.py [ids]
"""
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from skimage.color import rgb2hsv

import baselib as P
import masks as M                     # evs/masks.py (helpers only; its rembg cache is E.WORK = base/work)

E = P.E
L = P.L
poly, rect, largest, rembg = M.poly, M.rect, M.largest, M.rembg

# Base Set card geometry (600 x 825 WotC scans), read off work/grid_{4,18,24,46}.png: the thick yellow border, then
# the art window inside its gold bevel frame (the frame runs x 54..64 / 536..548, y 88..98 / 426..436; the scans
# are registered to +-2 px, so the window is taken 2 px inside it)
BASE_WIN = (66, 100, 534, 424)
STAGE = (18, 18, 150, 148)              # the Stage 1 / 2 badge (starburst + the evolves-from picture) over the
                                        # window's top-left corner


def hsv(cid):
    rgb = E.card_img(cid)
    h = rgb2hsv(rgb)
    return rgb, h[..., 0] * 360, h[..., 1], h[..., 2]


def fin(m, close=3, keep=1):
    m = ndimage.binary_closing(m, iterations=close)
    return ndimage.binary_fill_holes(largest(m, keep))


def base_window(cid, models=("isnet-general-use",), keep=1, close=3, extra=None, cut=None, win=BASE_WIN,
                stage=False, hull=None, grow=0):
    """rembg (union of models) inside the art window (and `hull`), largest parts, minus the stage badge"""
    sh = E.card_img(cid).shape[:2]
    m = np.zeros(sh, bool)
    for mo in models:
        m |= rembg(cid, mo)
    w = rect(sh, *win)
    if stage:
        w &= ~rect(sh, *STAGE)
    if hull is not None:
        m &= hull
    m &= w
    if cut is not None:
        m &= ~cut
    m = ndimage.binary_opening(m, iterations=1)
    if extra is not None:
        m |= extra & w
    m = fin(m, close, keep)
    if grow:
        m = ndimage.binary_dilation(m, iterations=grow) & w
    return m


# ---------------------------------------------------------------- the ladder
def m_charmeleon():
    """isnet-general-use has the body; the tail running back to the left and its flame by hand (grid_24)"""
    cid = "base1-24"
    sh = E.card_img(cid).shape[:2]
    tail = poly(sh, [(98, 332), (108, 290), (132, 256), (150, 222), (166, 246), (192, 262), (250, 256), (300, 260),
                     (338, 284), (348, 332), (300, 342), (240, 347), (190, 342), (150, 338)])
    return base_window(cid, close=4, stage=True, extra=tail)


def m_dragonair():
    """isnet-general-use has the head and neck; the tail tip rising from the sea at the left (and its reflection)
    by hand (grid_18): two parts"""
    cid = "base1-18"
    sh = E.card_img(cid).shape[:2]
    tip = poly(sh, [(138, 298), (152, 298), (170, 336), (184, 342), (198, 360), (196, 392), (190, 424), (160, 424),
                    (166, 396), (168, 380), (156, 366), (156, 344)])
    body = base_window(cid, close=4, stage=True)
    return fin(body | tip, 2, keep=2)


def m_charizard():
    """every segmenter takes the holo starfield (or nothing): Charizard's hull by hand (grid_4): the wings, the
    head and open jaw, the tongue, the tail and its flame, the feet"""
    cid = "base1-4"
    sh = E.card_img(cid).shape[:2]
    hull = poly(sh, [(203, 125), (300, 185), (325, 205), (350, 190), (372, 158), (398, 100), (420, 98), (455, 130),
                     (495, 162), (520, 190), (534, 220), (534, 282), (505, 270), (470, 262), (455, 280), (470, 300),
                     (488, 330), (484, 372), (470, 395), (478, 422), (268, 422), (262, 400), (240, 378), (208, 362),
                     (183, 352), (172, 330), (178, 298), (198, 296), (200, 285), (195, 255), (208, 238), (240, 232),
                     (262, 244)])
    return hull & rect(sh, *BASE_WIN)


MASKS = {"base1-24": m_charmeleon, "base1-18": m_dragonair, "base1-4": m_charizard}


def review(ids, masks, path, per=4):
    """review sheet: the Pokemon in colour, the rest darkened green"""
    tiles = []
    for cid in ids:
        rgb = E.card_img(cid)
        t = Image.fromarray(L.to8(np.where(masks[cid][..., None], rgb, rgb * 0.25 + np.array([0, 0.3, 0]))))
        t = t.resize((400, 550))
        ImageDraw.Draw(t).text((8, 530), cid, fill=(255, 255, 0))
        tiles.append(t)
    sheet = Image.new("RGB", (400 * min(per, len(tiles)), 550 * ((len(tiles) + per - 1) // per)))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % per) * 400, (i // per) * 550))
    sheet.save(path)
    print(path)


def make(ids, table=None, path=None):
    table = table or MASKS
    E.MASKS.mkdir(exist_ok=True)
    E.WORK.mkdir(exist_ok=True)
    out = {}
    for cid in ids:
        m = table[cid]()
        out[cid] = m
        Image.fromarray((m * 255).astype(np.uint8)).save(E.MASKS / f"{cid}.png")
        ys, xs = np.nonzero(m)
        print(cid, "mask bbox", xs.min(), ys.min(), xs.max(), ys.max(), f"{m.mean():.2f}")
    review(ids, out, path or E.WORK / "masks-ladder.png")
    return out


if __name__ == "__main__":
    make([a for a in sys.argv[1:] if a in MASKS] or list(MASKS))
