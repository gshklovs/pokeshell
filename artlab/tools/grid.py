r"""A coordinate grid over a card scan, for reading hand polygons / boxes / crops in card pixels (docs/ART_METHOD.md,
"Masks"). Merges p30's work/grid.py (whole card, 50 px) and evs's work/gridov.py (a zoomed crop).

  .venv\Scripts\python artlab\tools\grid.py <set folder> <number> [<number> ...]          whole card, lines every 50 px
  .venv\Scripts\python artlab\tools\grid.py <set folder> <number> --crop x0 y0 x1 y1 [--step 25]   zoomed to 900 px

-> <DATA>/<folder>/work/grid_<number>.png (open it with the Read tool). Green / yellow lines every 100 px.
"""
import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import artpaths  # noqa: E402

FONT = "C:/Windows/Fonts/consola.ttf"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder")
    ap.add_argument("numbers", nargs="+")
    ap.add_argument("--crop", nargs=4, type=int)
    ap.add_argument("--step", type=int, default=50)
    a = ap.parse_args()
    meta = json.loads((artpaths.code(a.folder) / "set.json").read_text(encoding="utf-8"))
    d = artpaths.data(a.folder)
    (d / "work").mkdir(parents=True, exist_ok=True)
    for n in a.numbers:
        im = Image.open(d / "ref" / f"{meta['prefix']}_{n}.png").convert("RGB")
        x0, y0, x1, y1 = a.crop or (0, 0, im.width, im.height)
        im = im.crop((x0, y0, x1, y1))
        k = 900 / max(im.size) if a.crop else 1.0
        im = im.resize((round(im.width * k), round(im.height * k)))
        dr = ImageDraw.Draw(im)
        f = ImageFont.truetype(FONT, 22 if a.crop else 12)
        for x in range((x0 // a.step + 1) * a.step if x0 else 0, x1, a.step):
            X = (x - x0) * k
            dr.line([(X, 0), (X, im.height)], fill=(0, 255, 0) if x % 100 == 0 else (255, 0, 255), width=1)
            dr.text((X + 2, 2), str(x), font=f, fill=(255, 255, 0), stroke_width=2, stroke_fill=(0, 0, 0))
        for y in range((y0 // a.step + 1) * a.step if y0 else 0, y1, a.step):
            Y = (y - y0) * k
            dr.line([(0, Y), (im.width, Y)], fill=(0, 255, 0) if y % 100 == 0 else (255, 0, 255), width=1)
            dr.text((2, Y + 2), str(y), font=f, fill=(255, 255, 0), stroke_width=2, stroke_fill=(0, 0, 0))
        out = d / "work" / f"grid_{n}.png"
        im.save(out)
        print(out)


if __name__ == "__main__":
    main()
