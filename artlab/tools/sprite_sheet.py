"""Sprite-sheet helpers (from the op-sprites research): find the sprites on a ripped sheet and cut one out.

  python artlab/tools/sprite_sheet.py label <sheet.png> [--bg auto|none|#rrggbb] [--max 60]   # annotated preview: every blob numbered
  python artlab/tools/sprite_sheet.py cut <sheet.png> <index> <out.png> [--bg ...] [--pad 0]   # cut blob <index> to a transparent PNG
"""
import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage


def load_mask(path, bg="auto", tol=12):
    im = Image.open(path)
    if im.mode == "P" and "transparency" in im.info or im.mode in ("RGBA", "LA", "PA"):
        rgba = np.array(im.convert("RGBA"))
        alpha = rgba[..., 3] > 16
        if bg == "auto" and alpha.mean() < 0.98:
            return rgba, alpha
    rgba = np.array(im.convert("RGBA"))
    if bg in ("auto", None):
        c = rgba[0, 0, :3].astype(int)
    elif bg == "none":
        return rgba, rgba[..., 3] > 16
    else:
        c = np.array([int(bg[i:i + 2], 16) for i in (1, 3, 5)])
    diff = np.abs(rgba[..., :3].astype(int) - c).max(axis=2)
    mask = (diff > tol) & (rgba[..., 3] > 16)
    rgba[..., 3] = np.where(mask, 255, 0)
    return rgba, mask


def blobs(mask, merge=2, min_px=200):
    grown = ndimage.binary_dilation(mask, iterations=merge) if merge else mask
    lab, n = ndimage.label(grown)
    out = []
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        if sl is None:
            continue
        area = int((mask[sl] & (lab[sl] == i)).sum())
        if area >= min_px:
            out.append((sl[0].start, sl[1].start, sl[0].stop, sl[1].stop, area, i))
    # reading order: rows of ~40px bands, then x
    out.sort(key=lambda b: (b[0] // 40, b[1]))
    return out, lab


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["label", "cut"])
    ap.add_argument("sheet")
    ap.add_argument("rest", nargs="*")
    ap.add_argument("--bg", default="auto")
    ap.add_argument("--tol", type=int, default=12)
    ap.add_argument("--merge", type=int, default=2)
    ap.add_argument("--min", type=int, default=200)
    ap.add_argument("--max", type=int, default=80)
    ap.add_argument("--crop", default="", help="x0,y0,x1,y1 region of the sheet to look at")
    a = ap.parse_args()
    rgba, mask = load_mask(a.sheet, a.bg, a.tol)
    ox = oy = 0
    if a.crop:
        x0, y0, x1, y1 = map(int, a.crop.split(","))
        rgba, mask, ox, oy = rgba[y0:y1, x0:x1], mask[y0:y1, x0:x1], x0, y0
    bl, lab = blobs(mask, a.merge, a.min)
    if a.cmd == "label":
        out = a.rest[0] if a.rest else str(Path(a.sheet).with_suffix("")) + "_labels.png"
        im = Image.fromarray(rgba).convert("RGBA")
        bgim = Image.new("RGBA", im.size, (40, 40, 48, 255))
        bgim.alpha_composite(im)
        d = ImageDraw.Draw(bgim)
        for k, (y0, x0, y1, x1, area, _) in enumerate(bl[: a.max]):
            d.rectangle([x0, y0, x1, y1], outline=(255, 0, 0, 255))
            d.text((x0 + 1, y0 + 1), str(k), fill=(255, 255, 0, 255))
            print(k, f"x={x0 + ox} y={y0 + oy} w={x1 - x0} h={y1 - y0} area={area}")
        bgim.convert("RGB").save(out)
        print("wrote", out)
    else:
        k, out = int(a.rest[0]), a.rest[1]
        y0, x0, y1, x1, _, li = bl[k]
        sub = rgba[y0:y1, x0:x1].copy()
        keep = (lab[y0:y1, x0:x1] == li) & mask[y0:y1, x0:x1]
        sub[..., 3] = np.where(keep, sub[..., 3], 0)
        Image.fromarray(sub).save(out)
        print("wrote", out, sub.shape[1], "x", sub.shape[0])


if __name__ == "__main__":
    main()
