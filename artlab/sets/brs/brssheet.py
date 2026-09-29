r"""Review sheets, one row per card: the real card scan | our art | our art over its text half (p30sheet's layout).
  sheet(ids, path, sizes)   ->  a PNG; the batches pass their own sizes dict
"""
import json

from PIL import Image, ImageDraw, ImageFont

import brslib as P
from brslib import E

ROW_H = 820
GAP = 28
FONT = "C:/Windows/Fonts/consola.ttf"
TITLE = "Brilliant Stars (swsh9 + Trainer Gallery)"


def fit_h(im, h):
    return im.resize((round(im.width * h / im.height), h), Image.LANCZOS)


def sheet(ids, path, sizes=None, title=None):
    sizes = sizes or json.loads((P.DATA / "sizes.json").read_text(encoding="utf-8"))
    rows = []
    for cid in ids:
        card = P.card_json(cid)
        info = sizes[cid]
        real = fit_h(Image.open(P.ref_path(cid)).convert("RGB"), ROW_H)
        st0 = Image.open(E.OUT / f"{cid}-card.png").convert("RGB")
        stacked = fit_h(st0, ROW_H)
        k = stacked.height / st0.height
        art0 = Image.open(E.OUT / f"{cid}-art.png").convert("RGB")
        art = art0.resize((round(art0.width * k), round(art0.height * k)), Image.LANCZOS)
        label = (f"{cid}  {card['name']}  {card['number']}  tier: {card['tier']}  |  sprite {info.get('sprite')} "
                 f"flip={info.get('flip')}  art {info['cols']}x{info['lines']}, card {info['cols']}x{info['card_lines']}\n"
                 f"{info['finish']}")
        rows.append((label, [real, art, stacked]))
    W = max(sum(p.width for p in ps) + GAP * (len(ps) + 1) for _, ps in rows)
    H = sum(ROW_H + 90 + GAP for _ in rows) + 70
    o = Image.new("RGB", (W, H), (24, 24, 28))
    d = ImageDraw.Draw(o)
    d.text((GAP, 14), f"{title or TITLE}: real card | pokeshell art | art + text half",
           font=ImageFont.truetype(FONT, 36), fill=(235, 235, 235))
    y = 70
    f = ImageFont.truetype(FONT, 26)
    for label, ps in rows:
        d.text((GAP, y + 8), label, font=f, fill=(200, 200, 200))
        x = GAP
        for p in ps:
            o.paste(p, (x, y + 80))
            x += p.width + GAP
        y += ROW_H + 90 + GAP
    path.parent.mkdir(parents=True, exist_ok=True)
    o.save(path)
    print(path.name, o.size)
