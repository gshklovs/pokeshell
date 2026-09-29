r"""sheet.png: one row per card, rarity order -- the real card scan | our art | our art over its text half.
ladder.png: one art per rarity at ONE scale. (evs/sheet.py's layout, p30 paths.) Run after p30build.py.
  ..\..\..\.venv\Scripts\python p30sheet.py [me55-23 ...]     (ids: a partial sheet -> work/sheet-part.png)
"""
import json
import sys
import textwrap

from PIL import Image, ImageDraw, ImageFont

import p30lib as P
from p30lib import E
import p30cards

ROW_H = 820
GAP = 28
FONT = "C:/Windows/Fonts/consola.ttf"
TITLE = "30th Celebration (me55)"


def fit_h(im, h):
    return im.resize((round(im.width * h / im.height), h), Image.LANCZOS)


def sheet(ids, path, sizes=None):
    """sizes: {id: p30build.render info}; default the ladder's sizes.json (batch agents pass their own, so
    parallel agents never share a file)"""
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
        label = (f"{cid}  {card['name']}  {card['number']}/{card['set']['printedTotal']}  tier: {card['tier']}"
                 f"  |  art {info['cols']}x{info['lines']}, card {info['cols']}x{info['card_lines']}\n{info['finish']}")
        rows.append((label, [real, art, stacked]))
    W = max(sum(p.width for p in ps) + GAP * (len(ps) + 1) for _, ps in rows)
    H = sum(ROW_H + 90 + GAP for _ in rows) + 70
    o = Image.new("RGB", (W, H), (24, 24, 28))
    d = ImageDraw.Draw(o)
    d.text((GAP, 14), f"{TITLE}: real card | pokeshell art | art + text half", font=ImageFont.truetype(FONT, 36),
           fill=(235, 235, 235))
    y = 70
    f = ImageFont.truetype(FONT, 26)
    for label, ps in rows:
        d.text((GAP, y + 8), label, font=f, fill=(200, 200, 200))
        x = GAP
        for p in ps:
            o.paste(p, (x, y + 80))
            x += p.width + GAP
        y += ROW_H + 90 + GAP
    o.save(path)
    print(path.name, o.size)


def ladder(per_row=4, k=0.5):
    sizes = json.loads((P.DATA / "sizes.json").read_text(encoding="utf-8"))
    panels = []
    for cid in p30cards.ORDER:
        im = Image.open(E.OUT / f"{cid}-art.png").convert("RGB")
        panels.append((P.card_json(cid), sizes[cid], im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)))
    rows = [panels[i:i + per_row] for i in range(0, len(panels), per_row)]
    f1, f2 = ImageFont.truetype(FONT, 26), ImageFont.truetype(FONT, 18)
    head = 100
    W = max(sum(p[2].width for p in r) + GAP * (len(r) + 1) for r in rows)
    Hs = [max(p[2].height for p in r) + head + GAP for r in rows]
    o = Image.new("RGB", (W, sum(Hs) + 60), (24, 24, 28))
    d = ImageDraw.Draw(o)
    d.text((GAP, 12), f"{TITLE} rarity ladder (one real card per rarity, same scale)",
           font=ImageFont.truetype(FONT, 32), fill=(235, 235, 235))
    y = 60
    n = 0
    for r, h in zip(rows, Hs):
        x = GAP
        for card, info, im in r:
            n += 1
            d.text((x, y), f"{n}. {card['tier']}", font=f1, fill=(240, 240, 240))
            d.text((x, y + 32), f"{card['name']} {card['number']}  {info['cols']}x{info['lines']}", font=f2, fill=(170, 170, 170))
            d.text((x, y + 56), textwrap.shorten(info["finish"], width=max(20, im.width // 10), placeholder="..."),
                   font=f2, fill=(150, 150, 150))
            o.paste(im, (x, y + head))
            x += im.width + GAP
        y += h
    o.save(P.DATA / "ladder.png")
    print("ladder.png", o.size)


if __name__ == "__main__":
    ids = [a for a in sys.argv[1:] if a in p30cards.BUILDERS]
    if ids:
        sheet(ids, E.WORK / "sheet-part.png")
    else:
        sheet(p30cards.ORDER, P.DATA / "sheet.png")
        ladder()
