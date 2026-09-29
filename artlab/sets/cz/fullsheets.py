r"""The full-set review sheets, grouped by printed rarity (and finish): every built Crown Zenith card as
real card | ours | ours + text half, two cards per row, one PNG per rarity group -> <DATA>/cz/sheets/full/.
Builders come in precedence order (audit/allcards.py: ladder < group batches < batch_fixes), so the sheet shows the
art that would ship.

  ..\..\..\.venv\Scripts\python fullsheets.py
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent / "audit"))
import allcards as AC  # noqa: E402

P, C, E = AC.P, AC.C, AC.P.E
H = 440
GAP = 18
FONT = "C:/Windows/Fonts/consola.ttf"
ORDER = [("01-common", "Common"), ("02-uncommon", "Uncommon"), ("03-rare", "Rare"), ("04-rare-holo", "Rare Holo"),
         ("05-rare-holo-v", "Rare Holo V"), ("06-rare-holo-vmax", "Rare Holo VMAX"),
         ("07-rare-holo-vstar", "Rare Holo VSTAR (NEW)"), ("08-radiant-rare", "Radiant Rare (NEW)"),
         ("09-trainer-gallery", "Trainer Gallery Rare Holo (NEW), Galarian Gallery"),
         ("10-gg-v-vmax", "Galarian Gallery Rare Holo V / VMAX (alt-art painting)"),
         ("11-gg-vstar", "Galarian Gallery Rare Holo VSTAR (alt-art painting)"),
         ("12-rare-secret", "Rare Secret (gold, and the painted Pikachu 160)")]


def bucket(cid):
    t = P.card_json(cid)["tier"]
    gg = P.is_gg(cid)
    return {"Common": "01-common", "Uncommon": "02-uncommon", "Rare": "03-rare", "Rare Holo": "04-rare-holo",
            "Rare Holo V": "10-gg-v-vmax" if gg else "05-rare-holo-v",
            "Rare Holo VMAX": "10-gg-v-vmax" if gg else "06-rare-holo-vmax",
            "Rare Holo VSTAR": "11-gg-vstar" if gg else "07-rare-holo-vstar", "Radiant Rare": "08-radiant-rare",
            "Trainer Gallery Rare Holo": "09-trainer-gallery", "Rare Secret": "12-rare-secret"}[t]


def fit(im, h, nearest=False):
    return im.resize((max(1, round(im.width * h / im.height)), h), Image.NEAREST if nearest else Image.LANCZOS)


def tile(cid, f):
    card = P.card_json(cid)
    k = C.cfg(cid)
    real = fit(Image.open(P.ref_path(cid)).convert("RGB"), H)
    st0 = Image.open(E.OUT / f"{cid}-card.png").convert("RGB")
    st = fit(st0, H)
    art0 = Image.open(E.OUT / f"{cid}-art.png").convert("RGB")
    art = art0.resize((round(art0.width * H / st0.height), round(art0.height * H / st0.height)), Image.LANCZOS)
    t = Image.new("RGB", (real.width + art.width + st.width + 4 * GAP, H + 56), (24, 24, 28))
    d = ImageDraw.Draw(t)
    flip = cid in P.META.get("flip_commons", []) if k["kind"] == "common" else k["flip"]
    d.text((GAP, 6), f"{card['name']}  {card['number']}  ({cid})", font=f, fill=(240, 220, 150))
    d.text((GAP, 28), f"{k['kind']}  sprite {k['sprite']}{' flipped' if flip else ''}  [{AC.OWNER[cid]}]", font=f,
           fill=(170, 170, 170))
    x = GAP
    for im in (real, art, st):
        t.paste(im, (x, 52))
        x += im.width + GAP
    return t


def main():
    f = ImageFont.truetype(FONT, 19)
    ft = ImageFont.truetype(FONT, 34)
    out = P.DATA / "sheets" / "full"
    out.mkdir(parents=True, exist_ok=True)
    groups = {}
    for cid in AC.IDS:
        groups.setdefault(bucket(cid), []).append(cid)
    key = lambda c: (P.is_gg(c), int("".join(ch for ch in P.E.num(c) if ch.isdigit())))  # noqa: E731
    index = {}
    for name, title in ORDER:
        ids = sorted(groups.get(name, []), key=key)
        if not ids:
            continue
        tiles = [tile(c, f) for c in ids]
        per = 2
        W = max(t.width for t in tiles)
        o = Image.new("RGB", (W * per + GAP, 70 + (H + 56 + GAP) * ((len(tiles) + per - 1) // per)), (16, 16, 20))
        ImageDraw.Draw(o).text((GAP, 16), f"Crown Zenith: {title}, {len(ids)} cards -- real | ours | ours + text half",
                               font=ft, fill=(240, 240, 240))
        for i, t in enumerate(tiles):
            o.paste(t, ((i % per) * W + GAP // 2, 70 + (i // per) * (H + 56 + GAP)))
        p = out / f"{name}.png"
        o.save(p)
        index[name] = {"title": title, "ids": ids, "png": str(p)}
        print(p.name, len(ids), o.size)
    (out / "index.json").write_text(json.dumps(index, indent=1), encoding="utf-8")
    print(sum(len(v["ids"]) for v in index.values()), "cards")


if __name__ == "__main__":
    main()
