r"""Masks of the real Pokemon on each Brilliant Stars card (white = Pokemon), card px -> masks/<id>.png, the method of
evs/masks.py and p30masks.py (docs/ART_METHOD.md section 6), driven by a per-card SPEC so every batch writes
its recipes as data:

  spec = dict(
    model="isnet-general-use" | "isnet-anime" | "u2net" | None,   rembg first cut (None: start empty)
    win=(x0, y0, x1, y1),            intersect with this rect (default: the whole card above the text)
    hull=[(x, y), ...],              intersect with this hand polygon (card px, read off work/grid_<n>.png)
    colour=fn(h, s, v) -> bool map,  OR a colour rule (hue 0..360, sat, val 0..1), taken inside `hull` only
    cut=[rect | poly, ...],          subtract (logos, scenery the model grabbed)
    add=[rect | poly, ...],          OR in (parts the model missed; a poly alone = poly_only)
    open=n, close=n, keep=n, fill=True
    fn=callable(cid) -> bool map     a custom recipe instead of all of the above
  )

  ..\..\..\.venv\Scripts\python brsmasks.py <id> ...     (the ladder's specs; batches call make/sheet themselves)
"""
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from skimage.color import rgb2hsv

import brslib as P
import masks as M                     # evs/masks.py (helpers; its rembg cache is E.WORK = cz/work)

E, L = P.E, P.L
poly, rect, largest, rembg = M.poly, M.rect, M.largest, M.rembg


def shape(sh, p):
    return poly(sh, p) if isinstance(p[0], (tuple, list)) else rect(sh, *p)


def hsv(cid):
    rgb = E.card_img(cid)
    h = rgb2hsv(rgb)
    return rgb, h[..., 0] * 360, h[..., 1], h[..., 2]


def make(cid, spec):
    if spec.get("fn"):
        m = spec["fn"](cid)
    else:
        rgb, h, s, v = hsv(cid)
        sh = rgb.shape[:2]
        m = rembg(cid, spec["model"]) if spec.get("model") else np.zeros(sh, bool)
        if spec.get("win"):
            m &= rect(sh, *spec["win"])
        hull = poly(sh, spec["hull"]) if spec.get("hull") else None
        if spec.get("colour") is not None:
            col = spec["colour"](h, s, v)
            if spec.get("colour_open", 1):
                col = ndimage.binary_opening(col, iterations=spec.get("colour_open", 1))
            m |= col & (hull if hull is not None else True)
        if hull is not None:
            m &= hull
        for c in spec.get("cut", ()):
            m &= ~shape(sh, c)
        if spec.get("open"):
            m = ndimage.binary_opening(m, iterations=spec["open"])
        if spec.get("close"):
            m = ndimage.binary_closing(m, iterations=spec["close"])
        for a in spec.get("add", ()):
            m |= shape(sh, a)
        for c in spec.get("cut_after", ()):
            m &= ~shape(sh, c)
        m = largest(m, spec.get("keep", 1)) if m.any() else m
        if spec.get("fill", True):
            m = ndimage.binary_fill_holes(m)
    E.MASKS.mkdir(exist_ok=True)
    Image.fromarray((m * 255).astype(np.uint8)).save(E.MASKS / f"{cid}.png")
    return m


def sheet(items, path):
    """items: [(cid, mask)] -> a review sheet: the Pokemon in colour, the rest darkened green"""
    tiles = []
    for cid, m in items:
        rgb = E.card_img(cid)
        o = np.where(m[..., None], rgb, rgb * 0.25 + np.array([0, 0.3, 0]))
        t = Image.fromarray(L.to8(o)).resize((367, 512))
        ImageDraw.Draw(t).text((4, 4), cid, fill=(255, 255, 0))
        tiles.append(t)
        ys, xs = np.nonzero(m)
        if len(xs):
            print(cid, "mask bbox", xs.min(), ys.min(), xs.max(), ys.max(), f"{m.mean():.3f}")
        else:
            print(cid, "EMPTY MASK")
    n = min(6, len(tiles))
    o = Image.new("RGB", (367 * n, 512 * ((len(tiles) + n - 1) // n)))
    for i, t in enumerate(tiles):
        o.paste(t, ((i % n) * 367, (i // n) * 512))
    o.save(path)


if __name__ == "__main__":
    import brscards as C
    ids = [a for a in sys.argv[1:] if a in C.CFG] or C.ORDER
    items = [(cid, make(cid, C.CFG[cid]["mask"])) for cid in ids if C.CFG[cid].get("mask")]
    sheet(items, E.WORK / "masks_ladder.png")
