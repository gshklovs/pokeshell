r"""Masks of the real Pokemon on the Hidden Fates ladder cards (white = Pokemon), card px -> masks/<id>.png +
work/masks-ladder.png. The evs / p30 method (docs/ART_METHOD.md section 6): rembg (local ONNX, no API) inside the
card's art region, hand hulls and colour rules read off work/grid_<n>.png. The batch modules reuse the helpers
(poly, rect, largest, rembg, hsv, sm_window, fin) and SM_WIN / ICON / EVOLVES.

  ..\..\..\.venv\Scripts\python hfmasks.py [ids]
"""
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from skimage.color import rgb2hsv

import hflib as P
import masks as M                     # evs/masks.py (helpers only; its rembg cache is E.WORK = hf/work)

E = P.E
L = P.L
poly, rect, largest, rembg = M.poly, M.rect, M.largest, M.rembg

# Sun & Moon card geometry (734 x 1024 scans), read off work/grid_{7,8,18,32}.png
SM_WIN = (58, 100, 676, 482)            # the art window of a regular SM card (Common .. Rare Holo, Shiny Vault)
ICON = (0, 60, 124, 164)                # the Stage 1 / 2 evolution icon over the window's top-left corner
EVOLVES = (100, 86, 440, 122)           # the "Evolves from" bar across the window's top edge
GX_ART = (28, 92, 706, 880)             # a GX / full-art card: the art runs frame to frame (text on top of it)


def hsv(cid):
    rgb = E.card_img(cid)
    h = rgb2hsv(rgb)
    return rgb, h[..., 0] * 360, h[..., 1], h[..., 2]


def fin(m, close=3, keep=1):
    m = ndimage.binary_closing(m, iterations=close)
    return ndimage.binary_fill_holes(largest(m, keep))


def sm_window(cid, models=("isnet-general-use",), keep=1, close=3, extra=None, cut=None, win=SM_WIN, stage=False):
    """rembg (union of models) inside the art window, largest parts, minus the stage icon / evolves bar"""
    sh = E.card_img(cid).shape[:2]
    m = np.zeros(sh, bool)
    for mo in models:
        m |= rembg(cid, mo)
    w = rect(sh, *win)
    if stage:
        w &= ~rect(sh, *ICON) & ~rect(sh, *EVOLVES)
    m &= w
    if cut is not None:
        m &= ~cut
    m = ndimage.binary_opening(m, iterations=1)
    if extra is not None:
        m |= extra & w
    return fin(m, close, keep)


def outline_halo(cid, m, reach=10):
    """Shiny Vault GX: the Pokemon is drawn with a thick cyan / coloured outline on the white card; grow the mask
    over every non-white (saturated or dark) pixel within `reach` px of it, so no outline ghost is left"""
    rgb, h, s, v = hsv(cid)
    ink = (s > 0.22) | (v < 0.55)
    near = ndimage.binary_dilation(m, iterations=reach)
    return m | (near & ink)


# ---------------------------------------------------------------- the ladder
def m_charmeleon():
    return sm_window("sm115-8", close=4, stage=True)


def m_mew():
    return sm_window("sm115-32", ("isnet-general-use", "isnet-anime"), close=5)


def m_vaporeon():
    return sm_window("sm115-18", close=4, stage=True)


def m_charizard_gx():
    """rembg has only the head and belly: Charizard fills the art (both arms, the wing at the right), so his hull
    (read off grid_9); the flame breath top-left is the scene"""
    cid = "sm115-9"
    sh = E.card_img(cid).shape[:2]
    hull = poly(sh, [(330, 135), (420, 112), (470, 150), (520, 250), (580, 300), (600, 250), (650, 240), (706, 250),
                     (706, 670), (30, 670), (30, 470), (70, 400), (95, 330), (160, 300), (220, 330), (270, 380),
                     (300, 300), (320, 200)])
    return sm_window(cid, ("isnet-general-use", "u2net"), close=5, win=(28, 92, 706, 670),
                     cut=rect(sh, *ICON) | rect(sh, *EVOLVES), extra=hull)


def m_charmander_sv():
    return sm_window("sma-SV6", ("isnet-general-use",), close=3)


def m_charizard_svgx():
    cid = "sma-SV49"
    sh = E.card_img(cid).shape[:2]
    m = sm_window(cid, ("isnet-general-use", "u2net"), close=5, win=(0, 92, 734, 890),
                  cut=rect(sh, *ICON) | rect(sh, *EVOLVES))
    return outline_halo(cid, m)


def tapu_mask(cid, win=(20, 92, 714, 880)):
    """gold Tapu GX: the Pokemon is flat coloured line art on the gold field. Everything that is not gold is it
    (plus the card text, boxed out later), closed and filled into one silhouette"""
    rgb, h, s, v = hsv(cid)
    sh = rgb.shape[:2]
    gold = (h > 32) & (h < 60) & (s > 0.55) & (v > 0.6)
    m = ~gold & rect(sh, *win)
    m = ndimage.binary_opening(m, iterations=2)
    m = ndimage.binary_closing(m, iterations=10)
    return ndimage.binary_fill_holes(largest(m, 1))


def m_tapu_koko():
    return tapu_mask("sma-SV93")


MASKS = {"sm115-8": m_charmeleon, "sm115-32": m_mew, "sm115-18": m_vaporeon, "sm115-9": m_charizard_gx,
         "sma-SV6": m_charmander_sv, "sma-SV49": m_charizard_svgx, "sma-SV93": m_tapu_koko}


def review(ids, masks, path, per=4):
    """review sheet: the Pokemon in colour, the rest darkened green"""
    tiles = []
    for cid in ids:
        rgb = E.card_img(cid)
        t = Image.fromarray(L.to8(M.K.overlay(rgb, masks[cid]) if hasattr(M, "K") else
                                  np.where(masks[cid][..., None], rgb, rgb * 0.25 + np.array([0, 0.3, 0]))))
        t = t.resize((367, 512))
        ImageDraw.Draw(t).text((8, 494), cid, fill=(255, 255, 0))
        tiles.append(t)
    sheet = Image.new("RGB", (367 * min(per, len(tiles)), 512 * ((len(tiles) + per - 1) // per)))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % per) * 367, (i // per) * 512))
    sheet.save(path)
    print(path)


def make(ids, table=None, path=None):
    table = table or MASKS
    E.MASKS.mkdir(exist_ok=True)
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
