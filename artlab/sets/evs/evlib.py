"""Evolving Skies (swsh7) batch: shared helpers on top of artlab/lib/s3lib.py.

The approach is suite3's: the vendor colorscripts sprite, UNMODIFIED (flip / gold remap only), composed on the
art grid (1 grid px = 1 col x half a line; a sprite px is a 2x2 block) over the card's own scene with the
real Pokemon painted out. What is new here:
  - card scans live in evs/ref/swsh7_<n>.png, masks in evs/masks/swsh7-<n>.png (built by masks.py)
  - tex_fill(): the painted-out hole keeps the scene's texture (smooth push-pull membrane for the low
    frequencies + the scene's own high-pass detail reflected across the hole edge), because these SWSH
    Pokemon cover most of the card and a plain membrane leaves a large blurry blob.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent            # artlab/sets/evs: this set's code (plan.json, batch_*.py)
LIB = HERE.parents[1] / "lib"                     # artlab/lib: s3lib, sprites, tiers, s3anim, bottom, maskkit
sys.path.insert(0, str(LIB))
import s3lib as L  # noqa: E402  (also puts artlab/, tools/ on sys.path)
from s3lib import Card  # noqa: E402,F401
import artpaths  # noqa: E402

DATA = artpaths.data("evs")                       # style-lab/evs: scans, masks, card JSON and every output
LAB = artpaths.DATA
REF = DATA / "ref"
MASKS = DATA / "masks"
OUT = DATA / "out"
WORK = DATA / "work"
CARDS = DATA / "cards"
ART = DATA / "art"


def num(cid):
    return cid.split("-")[1]


def ref_path(cid):
    return REF / f"swsh7_{num(cid)}.png"


def card_img(cid):
    return np.asarray(Image.open(ref_path(cid)).convert("RGB")).astype(float) / 255


def mask(cid):
    return np.asarray(Image.open(MASKS / f"{cid}.png")) > 0


def _blur_known(a, known, sigma):
    from scipy import ndimage
    w = ndimage.gaussian_filter(known.astype(float), sigma, mode="nearest")
    out = np.stack([ndimage.gaussian_filter(a[..., c] * known, sigma, mode="nearest") for c in range(3)], -1)
    return out / np.maximum(w, 1e-6)[..., None]


def tex_fill(rgb, known, sigma=14, tex_src=None, detail=1.0):
    """fill the unknown pixels: push-pull membrane (low frequencies) + the scene's own high-pass texture,
    taken from the mirror image across the nearest hole edge; where the mirror lands in the hole too,
    from a wrapped known texture rectangle `tex_src` (x0, y0, x1, y1)"""
    from scipy import ndimage
    base = L.pushpull(rgb, known)
    low = _blur_known(rgb, known, sigma)
    hp = (rgb - low) * known[..., None]
    H, W = known.shape
    _, (iy, ix) = ndimage.distance_transform_edt(~known, return_indices=True)
    yy, xx = np.mgrid[0:H, 0:W]
    sy, sx = 2 * iy - yy, 2 * ix - xx
    ok = (sy >= 0) & (sy < H) & (sx >= 0) & (sx < W)
    sy, sx = np.clip(sy, 0, H - 1), np.clip(sx, 0, W - 1)
    ok &= known[sy, sx]
    det = np.where(ok[..., None], hp[sy, sx], 0.0)
    if tex_src is not None:
        a, b, c, d = tex_src
        tw, th = c - a, d - b
        # mirror-tiling (no seams)
        tx = xx % (2 * tw)
        tx = np.where(tx >= tw, 2 * tw - 1 - tx, tx) + a
        ty = yy % (2 * th)
        ty = np.where(ty >= th, 2 * th - 1 - ty, ty) + b
        det = np.where(ok[..., None], det, hp[ty, tx])
    out = np.where(known[..., None], rgb, np.clip(base + detail * det, 0, 1))
    return out


def clean(cid, grow=4, boxes=(), texture=True, sigma=14, tex_src=None, detail=1.0, extra=None):
    """the card scan with the real Pokemon (mask) and the text/logo boxes painted out"""
    from scipy import ndimage
    rgb = card_img(cid)
    m = mask(cid).copy()
    if extra is not None:
        m |= extra
    if grow:
        m = ndimage.binary_dilation(m, iterations=grow)
    for (a, b, c, d) in boxes:
        m[max(0, b):d, max(0, a):c] = True
    known = ~m
    if texture:
        return tex_fill(rgb, known, sigma, tex_src, detail), m
    return L.pushpull(rgb, known), m


def anchor(cid, x0, y0, S, spr, dx=0, dy=0):
    m = mask(cid)
    ys, xs = np.nonzero(m)
    cx = ((xs.min() + xs.max()) / 2 - x0) / S
    by = (ys.max() - y0) / S
    return round(cx - spr.w / 2) + dx, round(by - spr.h) + dy


def region(cid, x0, y0, x1, y1, height):
    reg = Image.open(ref_path(cid)).convert("RGB").crop((round(x0), round(y0), round(x1), round(y1)))
    return reg.resize((max(1, round(reg.width * height / reg.height)), height), Image.LANCZOS)


# the colorscripts Eeveelutions have more than 24 colour pairs: extra sprite keys come from Hiragana, which
# (+ Katakana, + a Hangul block above the rainbow keys) is outside s3lib.KEY_POOL (no collision with bg keys)
SPRITE_KEYS_EXT = L.SPRITE_KEYS + "".join(chr(c) for c in list(range(0x3041, 0x3097)) + list(range(0x30A1, 0x30FB)) +
                                         list(range(0xC000, 0xC400)))
assert not set(SPRITE_KEYS_EXT) & set(L.KEY_POOL)


class Sprite(L.Sprite):
    """s3lib.Sprite with a longer key alphabet; rows/pal/shiny are the vendor sprite verbatim (flip only)"""

    def __init__(self, name, flip=False):
        import sprites
        n, s = sprites.load(name), sprites.load(name, shiny=True)
        assert len(n) == len(s) and len(n[0]) == len(s[0]), name
        pairs, rows = {}, []
        for rn, rs in zip(n, s):
            row = ""
            for cn, cs in zip(rn, rs):
                assert (cn is None) == (cs is None), name
                if cn is None:
                    row += "."
                    continue
                if (cn, cs) not in pairs:
                    pairs[(cn, cs)] = "k" if cn == L.BLACK and cs == L.BLACK else \
                        SPRITE_KEYS_EXT[len([k for k in pairs.values() if k != "k"])]
                row += pairs[(cn, cs)]
            rows.append(row[::-1] if flip else row)
        self.name, self.flip, self.rows = name, flip, rows
        self.pal = {k: L.rgbhex(cn) for (cn, cs), k in pairs.items()}
        self.shiny = {k: L.rgbhex(cs) for (cn, cs), k in pairs.items()}
        self.w, self.h = len(rows[0]), len(rows)
