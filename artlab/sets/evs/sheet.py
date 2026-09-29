r"""sheet.png: one row per card, in rarity order -- the real card scan | our art | our art stacked over its text
half. ladder.png: one art per rarity, Common .. Rare Secret, all at the same scale. Run after build.py.   ..\..\..\.venv\Scripts\python sheet.py
"""
import json

from PIL import Image, ImageDraw, ImageFont

import evcards
import evlib as E

ROW_H = 820
GAP = 28
FONT = "C:/Windows/Fonts/consola.ttf"


def fit_h(im, h):
    return im.resize((round(im.width * h / im.height), h), Image.LANCZOS)


def main():
    rows = []
    for cid in evcards.ORDER:
        card = json.load(open(E.CARDS / f"{cid}.json", encoding="utf-8"))
        info = json.load(open(E.DATA / "sizes.json", encoding="utf-8"))[cid]
        real = fit_h(Image.open(E.ref_path(cid)).convert("RGB"), ROW_H)
        stacked = fit_h(Image.open(E.OUT / f"{cid}-card.png").convert("RGB"), ROW_H)
        art0 = Image.open(E.OUT / f"{cid}-art.png").convert("RGB")
        k = stacked.height / Image.open(E.OUT / f"{cid}-card.png").height        # same scale as the stacked one
        art = art0.resize((round(art0.width * k), round(art0.height * k)), Image.LANCZOS)
        label = (f"{cid}  {card['name']}  {card['number']}/{card['set']['printedTotal']}  tier: {card['tier']}{'' if card['tier'] == card['rarity'] else ' (API rarity: ' + card['rarity'] + ')'}"
                 f"  |  art {info['cols']}x{info['lines']}, card {info['cols']}x{info['card_lines']}\n"
                 f"{info['finish']}")
        rows.append((label, [real, art, stacked]))
    W = max(sum(p.width for p in ps) + GAP * (len(ps) + 1) for _, ps in rows)
    H = sum(ROW_H + 90 + GAP for _ in rows) + 70
    o = Image.new("RGB", (W, H), (24, 24, 28))
    d = ImageDraw.Draw(o)
    d.text((GAP, 14), "Evolving Skies (swsh7): real card | pokeshell art | art + text half",
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
    o.save(E.DATA / "sheet.png")
    print("sheet.png", o.size)
    ladder()


def ladder(per_row=6, k=0.5):
    """every rarity's art in order, at ONE scale (true relative sizes), with its tier + finish"""
    import textwrap
    panels = []
    for cid in evcards.ORDER:
        card = json.load(open(E.CARDS / f"{cid}.json", encoding="utf-8"))
        info = json.load(open(E.DATA / "sizes.json", encoding="utf-8"))[cid]
        im = Image.open(E.OUT / f"{cid}-art.png").convert("RGB")
        im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
        panels.append((card, info, im))
    rows = [panels[i:i + per_row] for i in range(0, len(panels), per_row)]
    f1, f2 = ImageFont.truetype(FONT, 26), ImageFont.truetype(FONT, 18)
    head = 100
    W = max(sum(p[2].width for p in r) + GAP * (len(r) + 1) for r in rows)
    Hs = [max(p[2].height for p in r) + head + GAP for r in rows]
    o = Image.new("RGB", (W, sum(Hs) + 60), (24, 24, 28))
    d = ImageDraw.Draw(o)
    d.text((GAP, 12), "Evolving Skies rarity ladder (one real card per rarity, same scale)", font=ImageFont.truetype(FONT, 32),
           fill=(235, 235, 235))
    y = 60
    n = 0
    for r, h in zip(rows, Hs):
        x = GAP
        for card, info, im in r:
            n += 1
            var = next(iter(json.load(open(E.ART / f"{card['id']}.json", encoding="utf-8"))["variants"]))
            d.text((x, y), f"{n}. {card['tier']}" + (" (alt art)" if var.endswith("-alt") else ""), font=f1,
                   fill=(240, 240, 240))
            d.text((x, y + 32), f"{card['name']} {card['number']}  {info['cols']}x{info['lines']}", font=f2, fill=(170, 170, 170))
            fin = textwrap.shorten(info["finish"], width=max(20, im.width // 10), placeholder="...")
            d.text((x, y + 56), fin, font=f2, fill=(150, 150, 150))
            o.paste(im, (x, y + head))
            x += im.width + GAP
        y += h
    o.save(E.DATA / "ladder.png")
    print("ladder.png", o.size)


if __name__ == "__main__":
    main()
