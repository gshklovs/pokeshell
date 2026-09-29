"""Mask helpers (white = the real Pokemon, card px), shared by every set's mask recipes (evs masks.py, p30masks.py).

A mask recipe for one card combines, in card pixels read off work/grid_<n>.png (artlab/tools/grid.py):
  rembg_cached()   a local rembg segmentation (ONNX, no API), cached per model and card
  rect() / poly()  hand boxes and polygons: intersect to keep the Pokemon's hull, subtract to cut scenery out
  a colour rule    rgb2hsv thresholds for the Pokemon's own colours, inside a hand hull (when rembg takes the scene)
  largest()        keep the n biggest blobs; then scipy binary_closing / binary_opening / binary_fill_holes
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

# the three segmenters tried on every card; each card keeps the one that caught its Pokemon best
MODELS = ("isnet-general-use", "isnet-anime", "u2net")


def rembg_cached(src, cache, model):
    """rembg's mask of the scan `src` with `model`, cached as the PNG `cache` (computed once). -> bool array"""
    cache = Path(cache)
    if not cache.exists():
        from rembg import new_session, remove
        m = remove(Image.open(src).convert("RGB"), session=new_session(model), only_mask=True)
        m.save(cache)
    return np.asarray(Image.open(cache)) > 128


def poly(shape, pts):
    im = Image.new("L", (shape[1], shape[0]), 0)
    ImageDraw.Draw(im).polygon(pts, fill=255)
    return np.asarray(im) > 0


def rect(shape, a, b, c, d):
    m = np.zeros(shape, bool)
    m[b:d, a:c] = True
    return m


def largest(m, keep=1):
    lbl, n = ndimage.label(m)
    if n <= keep:
        return m
    sz = ndimage.sum(m, lbl, range(1, n + 1))
    return np.isin(lbl, 1 + np.argsort(sz)[::-1][:keep])


def stroke(shape, pts, width):
    """a thick polyline (ribbons, tails) as a mask"""
    im = Image.new("L", (shape[1], shape[0]), 0)
    d = ImageDraw.Draw(im)
    d.line(pts, fill=255, width=width, joint="curve")
    for x, y in (pts[0], pts[-1]):
        d.ellipse((x - width / 2, y - width / 2, x + width / 2, y + width / 2), fill=255)
    return np.asarray(im) > 0


def hsv_planes(rgb):
    """(hue in degrees, saturation, value) planes of a float RGB image, for colour rules"""
    from skimage.color import rgb2hsv
    h = rgb2hsv(rgb)
    return h[..., 0] * 360, h[..., 1], h[..., 2]


def overlay(rgb, m):
    """review tile: the Pokemon in colour, everything else darkened green"""
    return np.where(m[..., None], rgb, rgb * 0.25 + np.array([0, 0.3, 0]))
