r"""The Base Set lookbook sheets (docs/ART_METHOD.md section 15), ALWAYS real card | ours | ours + text half, one row
per card, as combined images (the lookbook page has a file limit) -> <DATA>/base/sheets/lookbook/:

  00-ladder.png                the ladder: one card per printed rarity
  00-ladder-holo.gif           the ladder's Rare Holo, animated (its 16-frame loop at 12 fps, art and art + text)
  <n>-<rarity>-<k>.png         every card of a printed rarity, about 5 per image, in number order
  04-rare-holo-<k>.gif         the Rare Holo sheets animated (the foil loop in both "ours" panels)
  index.json                   what each image holds

The renders are the current out/ and anim/ files (whatever ran last: ladder < group batch < batch_fixes).

  ..\..\..\.venv\Scripts\python lookbook.py [ladder|groups|all]
"""
import json
import math
import sys

from PIL import Image, ImageDraw, ImageFont

import baselib as P
from baselib import E, bottom
import basecards as C

sys.path.insert(0, str(P.HERE.parents[2] / "tools"))
from render_ansi import render  # noqa: E402

OUT = P.DATA / "sheets" / "lookbook"
FONT = "C:/Windows/Fonts/consola.ttf"
GAP = 24
BGC = (22, 22, 27)
RARITIES = [("01-common", "Common"), ("02-uncommon", "Uncommon"), ("03-rare", "Rare"), ("04-rare-holo", "Rare Holo")]
PER = 5


def fit_h(im, h, nearest=False):
    return im.resize((max(1, round(im.width * h / im.height)), h), Image.NEAREST if nearest else Image.LANCZOS)


def label(cid):
    card = P.card_json(cid)
    art = json.loads((E.ART / f"{cid}.json").read_text(encoding="utf-8"))
    v = next(iter(art["variants"].values()))
    rows = v["rows"]
    flip = " flipped" if v.get("flip") else ""
    return (f"{card['name']}  {card['number']}/102  {card['tier']}   ({cid}, sprite {art.get('pokemon', '')}{flip}, "
            f"{len(rows[0])} cols x {len(rows) // 2} lines)"), v.get("finish", "")


def panels(cid, H):
    """real | ours | ours + text half at row height H (ours at the scale of ours + text)"""
    real = fit_h(Image.open(P.ref_path(cid)).convert("RGB"), H)
    st0 = Image.open(E.OUT / f"{cid}-card.png").convert("RGB")
    k = H / st0.height
    art0 = Image.open(E.OUT / f"{cid}-art.png").convert("RGB")
    art = art0.resize((round(art0.width * k), round(art0.height * k)), Image.LANCZOS)
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


def compose(title, rows, H, fonts):
    """rows: [(label, finish, [panel, panel, panel])] -> one image"""
    ft, fl, ff = fonts
    W = max([sum(p.width for p in ps) + GAP * (len(ps) + 1) for _, _, ps in rows]
            + [int(ft.getlength(title)) + 2 * GAP] + [int(ff.getlength(fin)) + 2 * GAP for _, fin, _ in rows])
    RH = H + 70
    o = Image.new("RGB", (W, 64 + RH * len(rows)), BGC)
    d = ImageDraw.Draw(o)
    d.text((GAP, 14), title, font=ft, fill=(240, 240, 240))
    y = 64
    for lab, fin, ps in rows:
        d.text((GAP, y + 4), lab, font=fl, fill=(240, 220, 150))
        d.text((GAP, y + 30), fin, font=ff, fill=(165, 165, 170))
        x = GAP
        for p in ps:
            o.paste(p, (x, y + 58))
            x += p.width + GAP
        y += RH
    return o


def save_gif(frames, path, fps=12):
    pal = [f.convert("P", palette=Image.ADAPTIVE, colors=255) for f in frames]
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=round(1000 / fps), loop=0, optimize=True,
                disposal=1)


def fonts():
    return (ImageFont.truetype(FONT, 30), ImageFont.truetype(FONT, 20), ImageFont.truetype(FONT, 16))


def chunks(ids):
    n = max(1, math.ceil(len(ids) / PER))
    k = math.ceil(len(ids) / n)
    return [ids[i:i + k] for i in range(0, len(ids), k)]


def sheet(name, title, ids, index, H=440, gif=False, gif_h=300):
    fs = fonts()
    rows = [(*label(c), panels(c, H)) for c in ids]
    p = OUT / f"{name}.png"
    compose(title + "  --  real card | ours | ours + text half", rows, H, fs).save(p, optimize=True)
    index[p.name] = {"title": title, "ids": ids}
    print(p.name, len(ids))
    if gif:
        per = {c: anim_panels(c, gif_h) for c in ids}
        frames = [compose(title + "  --  real card | ours (loop) | ours + text half (loop)",
                          [(*label(c), per[c][f]) for c in ids], gif_h, fs) for f in range(16)]
        g = OUT / f"{name}.gif"
        save_gif(frames, g)
        index[g.name] = {"title": title + " (animated, 16 frames at 12 fps)", "ids": ids}
        print(g.name, f"{g.stat().st_size / 1e6:.1f} MB")


def by_rarity():
    ids = sorted((p.stem for p in E.ART.glob("base1-*.json")), key=lambda c: int(E.num(c)))
    out = {}
    for c in ids:
        out.setdefault(P.card_json(c)["tier"], []).append(c)
    return out


def main(what):
    OUT.mkdir(parents=True, exist_ok=True)
    f = OUT / "index.json"
    index = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    if what in ("ladder", "all"):
        lad = P.META["ladder"]
        sheet("00-ladder", "Base Set rarity ladder (one real card per printed rarity)", lad, index)
        holos = [c for c in lad if P.card_json(c)["tier"] == "Rare Holo"]
        fs = fonts()
        per = {c: anim_panels(c, 440) for c in holos}
        frames = [compose("Base Set ladder: Rare Holo, the 16-frame loop at 12 fps  --  real | ours | ours + text half",
                          [(*label(c), per[c][i]) for c in holos], 440, fs) for i in range(16)]
        save_gif(frames, OUT / "00-ladder-holo.gif")
        index["00-ladder-holo.gif"] = {"title": "ladder Rare Holo, animated", "ids": holos}
        print("00-ladder-holo.gif")
    if what in ("groups", "all"):
        groups = by_rarity()
        for pre, tier in RARITIES:
            ids = groups.get(tier, [])
            parts = chunks(ids)
            for k, part in enumerate(parts, 1):
                sheet(f"{pre}-{k}", f"Base Set {tier} {k}/{len(parts)} ({len(ids)} cards)", part, index,
                      gif=tier == "Rare Holo")
    f.write_text(json.dumps(index, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "all")
