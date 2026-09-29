r"""Contact sheet of the three rembg models per card, cropped to the art window: window | isnet-general-use |
isnet-anime | u2net, the Pokemon in colour, the rest darkened green. Pick the model that caught the Pokemon best.

  ..\..\..\.venv\Scripts\python rembg_all.py <out.png> <id> [<id> ...]
"""
import sys

import numpy as np
from PIL import Image, ImageDraw

import baselib as P
import basemasks as BM

E, L = P.E, P.L
X0, Y0, X1, Y1 = 40, 80, 560, 445
TW, TH = 390, 274


def main():
    out, ids = sys.argv[1], sys.argv[2:]
    rows = []
    for cid in ids:
        rgb = E.card_img(cid)
        tiles = [Image.fromarray(L.to8(rgb[Y0:Y1, X0:X1])).resize((TW, TH))]
        for m in BM.M.MODELS:
            mk = BM.rembg(cid, m)
            o = np.where(mk[..., None], rgb, rgb * 0.25 + np.array([0, 0.3, 0]))[Y0:Y1, X0:X1]
            t = Image.fromarray(L.to8(o)).resize((TW, TH))
            ImageDraw.Draw(t).text((4, 4), f"{cid} {m}", fill=(255, 255, 0))
            tiles.append(t)
        rows.append(tiles)
    o = Image.new("RGB", (TW * 4, TH * len(rows)))
    for j, r in enumerate(rows):
        for i, t in enumerate(r):
            o.paste(t, (TW * i, TH * j))
    o.save(out)
    print(out)


if __name__ == "__main__":
    main()
