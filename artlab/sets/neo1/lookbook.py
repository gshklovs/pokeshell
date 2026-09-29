r"""The Neo Genesis lookbook sheets (docs/ART_METHOD.md section 15), ALWAYS real card | ours | ours + text half per
card, as a few bundled images: the lookbook artifact is near its file limit, so the whole set is at most 10 files
-> <DATA>/neo1/sheets/lookbook/:

  00-ladder.jpg               the ladder: one card per printed rarity, one tall image
  00-ladder-holo.gif          the ladder's Rare Holo (Lugia 9), animated: its 16-frame loop at 12 fps
  <n>-<rarity>-<k>.jpg        every card of a printed rarity in number order, packed two cards to a row where they
                              fit (JPEG, width <= 1400): 2 Common, 2 Uncommon, 1 Rare, 3 Rare Holo = 8 images
  index.json                  what each image holds

The renders are the current out/ and anim/ files (whatever ran last: ladder < group batch < batch_fixes).

  ..\..\..\.venv\Scripts\python lookbook.py [ladder|groups|all]
"""
import json
import math
import sys

from PIL import Image, ImageDraw, ImageFont

import neolib as P
from neolib import E, bottom
import neocards as C

sys.path.insert(0, str(P.HERE.parents[2] / "tools"))
from render_ansi import render  # noqa: E402

OUT = P.DATA / "sheets" / "lookbook"
FONT = "C:/Windows/Fonts/consola.ttf"
GAP = 16
BGC = (22, 22, 27)
MAXW = 1400
RARITIES = [("01-common", "Common", 2), ("02-uncommon", "Uncommon", 2), ("03-rare", "Rare", 1),
            ("04-rare-holo", "Rare Holo", 3)]


def fit_h(im, h):
    return im.resize((max(1, round(im.width * h / im.height)), h), Image.LANCZOS)


def label(cid):
    card = P.card_json(cid)
    art = json.loads((E.ART / f"{cid}.json").read_text(encoding="utf-8"))
    v = next(iter(art["variants"].values()))
    rows = v["rows"]
    flip = ", flipped" if v.get("flip") else ""
    return (f"{card['name']} {card['number']}/{card['set']['printedTotal']}  {card['tier']}",
            f"{cid}, sprite {art.get('pokemon', '')}{flip}, {len(rows[0])} x {len(rows) // 2}")


def panels(cid, H):
    """real | ours | ours + text half at row height H (ours at the scale of ours + text)"""
    real = fit_h(Image.open(P.ref_path(cid)).convert("RGB"), H)
    st0 = Image.open(E.OUT / f"{cid}-card.png").convert("RGB")
    k = H / st0.height
    art0 = Image.open(E.OUT / f"{cid}-art.png").convert("RGB")
    art = art0.resize((max(1, round(art0.width * k)), max(1, round(art0.height * k))), Image.LANCZOS)
    return [real, art, fit_h(st0, H)]


def anim_panels(cid, H):
    """per frame [real, ours, ours + text] at row height H, from the loop's own frames (anim/<id>/ans/)"""
    card = P.card_json(cid)
    ans = sorted((P.DATA / "anim" / cid / "ans").glob(f"{cid}-*.ans"))
    real = fit_h(Image.open(P.ref_path(cid)).convert("RGB"), H)
    art = json.loads((E.ART / f"{cid}.json").read_text(encoding="utf-8"))
    width = len(next(iter(art["variants"].values()))["rows"][0])
    bot = bottom.render_text(card, width, frame=C.FRAMES[card["tier"]])
    out = []
    for f in ans:
        top = f.read_text(encoding="utf-8")
        if not top.endswith("\n"):
            top += "\n"
        st0 = render(top + bot, scale=1)
        k = H / st0.height
        a0 = render(top, scale=1)
        out.append([real, a0.resize((round(a0.width * k), round(a0.height * k)), Image.LANCZOS), fit_h(st0, H)])
    return out


def fonts():
    return ImageFont.truetype(FONT, 24), ImageFont.truetype(FONT, 15), ImageFont.truetype(FONT, 12)


def cell_w(ps):
    return sum(p.width for p in ps) + GAP * (len(ps) - 1)


def compose(title, cards, H, maxw=MAXW):
    """cards: [(label, sub, [real, ours, ours + text])] -> one image, packed left to right into rows <= maxw wide
    (each card keeps its three panels together, real | ours | ours + text)"""
    ft, fl, ff = fonts()
    fitted = []
    for lab, sub, ps in cards:                  # a card wider than the page on its own: scale its panels down
        k = (maxw - 3 * GAP) / cell_w(ps)
        if k < 1:
            ps = [p.resize((max(1, round(p.width * k)), max(1, round(p.height * k))), Image.LANCZOS) for p in ps]
        fitted.append((lab, sub, ps))
    cards = fitted
    rows, cur, w = [], [], GAP
    for c in cards:
        cw = cell_w(c[2]) + 2 * GAP
        if cur and w + cw > maxw:
            rows.append(cur)
            cur, w = [], GAP
        cur.append(c)
        w += cw
    rows.append(cur)
    width = min(maxw, max(GAP + sum(cell_w(c[2]) + 2 * GAP for c in r) for r in rows))
    RH = H + 50
    o = Image.new("RGB", (width, 48 + RH * len(rows)), BGC)
    d = ImageDraw.Draw(o)
    d.text((GAP, 12), title, font=ft, fill=(240, 240, 240))
    y = 48
    for r in rows:
        x = GAP
        for lab, sub, ps in r:
            d.text((x, y + 2), lab, font=fl, fill=(240, 220, 150))
            d.text((x, y + 21), sub, font=ff, fill=(165, 165, 170))
            px = x
            for p in ps:
                o.paste(p, (px, y + 42))
                px += p.width + GAP
            x = px + GAP
        y += RH
    return o


def save_jpg(im, path):
    if im.width > MAXW:
        im = im.resize((MAXW, round(im.height * MAXW / im.width)), Image.LANCZOS)
    im.save(path, quality=86, optimize=True, progressive=True)


def save_gif(frames, path, fps=12):
    pal = [f.convert("P", palette=Image.ADAPTIVE, colors=255) for f in frames]
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=round(1000 / fps), loop=0, optimize=True,
                disposal=1)


def by_rarity():
    ids = sorted((p.stem for p in E.ART.glob("neo1-*.json")), key=lambda c: int(E.num(c)))
    out = {}
    for c in ids:
        out.setdefault(P.card_json(c)["tier"], []).append(c)
    return out


def main(what):
    OUT.mkdir(parents=True, exist_ok=True)
    f = OUT / "index.json"
    index = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    head = "real card | ours | ours + text half"
    if what in ("ladder", "all"):
        lad = P.META["ladder"]
        im = compose(f"Neo Genesis rarity ladder, one real card per printed rarity  --  {head}",
                     [(*label(c), panels(c, 520)) for c in lad], 520, maxw=1300)
        save_jpg(im, OUT / "00-ladder.jpg")
        index["00-ladder.jpg"] = {"title": "Neo Genesis rarity ladder (Common, Uncommon, Rare, Rare Holo)", "ids": lad}
        holos = [c for c in lad if P.card_json(c)["tier"] == "Rare Holo"]
        per = {c: anim_panels(c, 420) for c in holos}
        frames = [compose("Neo Genesis Rare Holo: the WotC starlight loop, 16 frames at 12 fps  --  " + head,
                          [(*label(c), per[c][i]) for c in holos], 420) for i in range(16)]
        save_gif(frames, OUT / "00-ladder-holo.gif")
        index["00-ladder-holo.gif"] = {"title": "the ladder's Rare Holo, animated (16 frames at 12 fps)", "ids": holos}
        print("00-ladder.jpg, 00-ladder-holo.gif")
    if what in ("groups", "all"):
        for stale in OUT.glob("0[1-4]-*.jpg"):
            stale.unlink()
            index.pop(stale.name, None)
        groups = by_rarity()
        for pre, tier, n in RARITIES:
            ids = groups.get(tier, [])
            k = math.ceil(len(ids) / n)
            parts = [ids[i:i + k] for i in range(0, len(ids), k)]
            for j, part in enumerate(parts, 1):
                name = f"{pre}-{j}.jpg"
                im = compose(f"Neo Genesis {tier} {j}/{len(parts)} ({len(ids)} cards)  --  {head}",
                             [(*label(c), panels(c, 300)) for c in part], 300)
                save_jpg(im, OUT / name)
                index[name] = {"title": f"Neo Genesis {tier} {j}/{len(parts)}", "ids": part}
                print(name, len(part), im.size)
    f.write_text(json.dumps(index, indent=1), encoding="utf-8")
    files = sorted(p.name for p in OUT.iterdir() if p.suffix in (".jpg", ".gif"))
    print(f"{len(files)} image files: {', '.join(files)}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "all")
