r"""Contact sheet of the three rembg models per card (the p30 agents' work/rembg_all.py): card | isnet-general-use |
isnet-anime | u2net, the Pokemon in colour, the rest darkened green. Pick the model that caught the Pokemon best.

  ..\..\..\.venv\Scripts\python rembg_all.py <out.png> <id> [<id> ...]
"""
import sys

import numpy as np
from PIL import Image, ImageDraw

import czlib as P
import czmasks as CM

E, L = P.E, P.L


def main():
    out, ids = sys.argv[1], sys.argv[2:]
    rows = []
    for cid in ids:
        rgb = E.card_img(cid)
        tiles = [Image.fromarray(L.to8(rgb)).resize((300, 418))]
        for m in CM.M.MODELS:
            mk = CM.rembg(cid, m)
            o = np.where(mk[..., None], rgb, rgb * 0.25 + np.array([0, 0.3, 0]))
            t = Image.fromarray(L.to8(o)).resize((300, 418))
            ImageDraw.Draw(t).text((4, 4), f"{cid} {m}", fill=(255, 255, 0))
            tiles.append(t)
        rows.append(tiles)
    o = Image.new("RGB", (1200, 418 * len(rows)))
    for j, r in enumerate(rows):
        for i, t in enumerate(r):
            o.paste(t, (300 * i, 418 * j))
    o.save(out)


if __name__ == "__main__":
    main()
