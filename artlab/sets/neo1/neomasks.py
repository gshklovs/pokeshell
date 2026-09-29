r"""Masks of the real Pokemon on the Neo Genesis ladder cards (white = Pokemon), card px -> masks/<id>.png +
work/masks-ladder.png. The evs / p30 / hf method (docs/ART_METHOD.md section 6): rembg (local ONNX, no API) inside
the card's art window, hand hulls and colour rules read off work/grid_<n>.png. The batch modules reuse the helpers
(poly, rect, largest, rembg, hsv, base_window, fin) and NEO_WIN / STAGE.

  ..\..\..\.venv\Scripts\python neomasks.py [ids]
"""
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from skimage.color import rgb2hsv

import neolib as P
import masks as M                     # evs/masks.py (helpers only; its rembg cache is E.WORK = neo1/work)

E = P.E
L = P.L
poly, rect, largest, rembg = M.poly, M.rect, M.largest, M.rembg

# Neo Genesis card geometry (600 x 825 WotC scans), read off work/grid_{4,18,24,46}.png: the thick yellow border, then
# the art window inside its gold bevel frame (the frame runs x 54..64 / 536..548, y 88..98 / 426..436; the scans
# are registered to +-2 px, so the window is taken 2 px inside it)
NEO_WIN = (68, 99, 532, 420)
STAGE = (10, 18, 114, 138)              # the Stage 1 / 2 badge (starburst + the evolves-from picture) over the
                                        # window's top-left corner


def hsv(cid):
    rgb = E.card_img(cid)
    h = rgb2hsv(rgb)
    return rgb, h[..., 0] * 360, h[..., 1], h[..., 2]


def fin(m, close=3, keep=1):
    m = ndimage.binary_closing(m, iterations=close)
    return ndimage.binary_fill_holes(largest(m, keep))


def base_window(cid, models=("isnet-general-use",), keep=1, close=3, extra=None, cut=None, win=NEO_WIN,
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
def m_quilava():
    """every segmenter takes the volcano fire with it (u2net) or only the head (isnet): Quilava's hull by hand
    (grid_46): the head flame, head and ear, the back flames, the body, the crouched legs"""
    cid = "neo1-46"
    sh = E.card_img(cid).shape[:2]
    hull = poly(sh, [(140, 186), (156, 122), (183, 138), (201, 101), (220, 133), (236, 122), (241, 170), (231, 218),
                     (247, 221), (265, 231), (284, 266), (311, 250), (327, 202), (351, 175), (380, 197), (407, 170),
                     (423, 213), (455, 218), (487, 229), (519, 261), (497, 277), (476, 303), (433, 341), (412, 357),
                     (415, 389), (401, 410), (391, 421), (359, 423), (295, 420), (263, 421), (167, 420), (161, 410),
                     (183, 389), (209, 367), (199, 341), (175, 314), (169, 287), (172, 261), (159, 250), (145, 229)])
    return hull & rect(sh, *NEO_WIN) & ~rect(sh, *STAGE)


def m_murkrow():
    """every segmenter takes the night sky or nothing: Murkrow's hull by hand (grid_24: the hat crest, beak, the
    raised wing, the tail and the feet on the rock; the rock is scene)"""
    cid = "neo1-24"
    sh = E.card_img(cid).shape[:2]
    hull = poly(sh, [(192, 196), (214, 150), (236, 170), (258, 150), (264, 175), (292, 185), (294, 212), (276, 240),
                     (300, 250), (318, 258), (348, 238), (362, 196), (392, 188), (396, 220), (416, 250), (398, 276),
                     (352, 282), (338, 312), (318, 322), (312, 344), (326, 350), (320, 368), (296, 374), (264, 372),
                     (268, 352), (290, 340), (282, 318), (266, 300), (250, 312), (226, 308), (220, 282), (198, 264),
                     (188, 238), (190, 210)])
    return hull & rect(sh, *NEO_WIN)


def m_lugia():
    """rembg takes the starfield: Lugia by colour (the pale white / blue-grey body and its white glow, one blob),
    plus the dark tail plates at the top right and the belly by hand (grid_9)"""
    cid = "neo1-9"
    rgb, h, s, v = hsv(cid)
    sh = rgb.shape[:2]
    w = rect(sh, *NEO_WIN)
    m = ndimage.binary_opening((v > 0.55) & (s < 0.42) & w, iterations=3)
    m = largest(m, 1)
    plates = poly(sh, [(372, 99), (458, 99), (458, 218), (418, 218), (384, 160)])
    belly = poly(sh, [(305, 245), (335, 205), (405, 200), (428, 245), (420, 330), (385, 335), (345, 318), (305, 300)])
    m = ndimage.binary_dilation(m, iterations=5) | plates | belly
    m = ndimage.binary_closing(m, iterations=8)
    return ndimage.binary_fill_holes(m) & w


MASKS = {"neo1-46": m_quilava, "neo1-24": m_murkrow, "neo1-9": m_lugia}


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
