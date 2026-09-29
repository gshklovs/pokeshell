r"""Facing review: per card the real art window | the vendor sprite as it is (unflipped), to read which way the
card's Pokemon faces vs the sprite (docs/ART_METHOD.md section 8). -> <DATA>/neo1/work/facing-<name>.png

  ..\..\..\.venv\Scripts\python facing.py <name> <id> [<id> ...]
"""
import json
import sys

from PIL import Image, ImageDraw

import neolib as P
import sprites

E, L = P.E, P.L
X0, Y0, X1, Y1 = 60, 94, 540, 430
TW, TH = 300, 210


def sprite_img(name, h=TH):
    g = sprites.load(name, False)
    im = Image.new("RGB", (len(g[0]), len(g)), (40, 40, 48))
    for y, r in enumerate(g):
        for x, c in enumerate(r):
            if c:
                im.putpixel((x, y), c)
    k = min(h / im.height, TW / im.width)
    return im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.NEAREST)


def main():
    name, ids = sys.argv[1], sys.argv[2:]
    plan = json.loads((P.HERE / "plan.json").read_text(encoding="utf-8"))
    spr = {e["id"]: e["sprite"] for g, v in plan.items() if not g.startswith("_") for e in v}
    per = 3
    rows = (len(ids) + per - 1) // per
    o = Image.new("RGB", (per * (2 * TW + 30), rows * (TH + 24)), (20, 20, 24))
    d = ImageDraw.Draw(o)
    for i, cid in enumerate(ids):
        X, Y = (i % per) * (2 * TW + 30), (i // per) * (TH + 24)
        win = Image.open(P.ref_path(cid)).convert("RGB").crop((X0, Y0, X1, Y1)).resize((TW, TH))
        o.paste(win, (X, Y + 20))
        o.paste(sprite_img(spr[cid]), (X + TW + 10, Y + 20))
        d.text((X + 4, Y + 3), f"{cid} {P.card_json(cid)['name']}  | sprite {spr[cid]} (unflipped)", fill=(255, 230, 90))
    f = E.WORK / f"facing-{name}.png"
    o.save(f)
    print(f)


if __name__ == "__main__":
    main()
