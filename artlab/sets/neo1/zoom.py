r"""Zoomed mask check: the art window with the mask's Pokemon bright and the rest dimmed, several cards per image ->
<DATA>/neo1/work/zoom-<name>.png

  ..\..\..\.venv\Scripts\python zoom.py <name> <id> [<id> ...]
"""
import sys

import numpy as np
from PIL import Image, ImageDraw

import neolib as P

E, L = P.E, P.L


def main():
    name, ids = sys.argv[1], sys.argv[2:]
    tiles = []
    for cid in ids:
        rgb = E.card_img(cid)
        m = E.mask(cid)
        o = np.where(m[..., None], rgb, rgb * 0.3 + np.array([0, 0.25, 0]))
        t = Image.fromarray(L.to8(o)).crop((60, 90, 540, 430)).resize((720, 510))
        ImageDraw.Draw(t).text((6, 4), cid, fill=(255, 255, 0))
        tiles.append(t)
    per = 2
    o = Image.new("RGB", (720 * per, 510 * ((len(tiles) + per - 1) // per)))
    for i, t in enumerate(tiles):
        o.paste(t, ((i % per) * 720, (i // per) * 510))
    f = E.WORK / f"zoom-{name}.png"
    o.save(f)
    print(f)


if __name__ == "__main__":
    main()
