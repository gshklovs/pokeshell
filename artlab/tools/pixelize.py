"""HD sprite -> pixel sprite: premultiplied-alpha LANCZOS downscale to a target height, a little saturation /
contrast back (downscaling thick black linework greys the colours), hard alpha, median-cut palette built from the
opaque pixels only.
  python artlab/tools/pixelize.py in.png out.png --h 96 --colors 48 --sat 1.25"""
import argparse
import numpy as np
from PIL import Image, ImageEnhance

ap = argparse.ArgumentParser()
ap.add_argument("src"); ap.add_argument("dst")
ap.add_argument("--h", type=int, default=96)
ap.add_argument("--colors", type=int, default=48)
ap.add_argument("--alpha", type=int, default=110)
ap.add_argument("--sat", type=float, default=1.25)
a = ap.parse_args()
im = Image.open(a.src).convert("RGBA")
w = max(1, round(im.width * a.h / im.height))
arr = np.array(im).astype(float)
arr[..., :3] *= arr[..., 3:4] / 255.0
pm = Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGBA").resize((w, a.h), Image.LANCZOS)
s = np.array(pm).astype(float)
al = s[..., 3]
rgb = np.where(al[..., None] > 0, s[..., :3] * 255.0 / np.maximum(al[..., None], 1), 0).clip(0, 255).astype(np.uint8)
img = Image.fromarray(rgb, "RGB")
if a.sat != 1:
    img = ImageEnhance.Contrast(ImageEnhance.Color(img).enhance(a.sat)).enhance(1.1)
mask = al >= a.alpha
strip = Image.fromarray(np.array(img)[mask].reshape(1, -1, 3))
pal = strip.quantize(colors=a.colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
q = img.quantize(palette=pal, dither=Image.Dither.NONE).convert("RGB")
out = np.dstack([np.array(q), np.where(mask, 255, 0).astype(np.uint8)])
Image.fromarray(out, "RGBA").save(a.dst)
print(a.dst, w, "x", a.h)
