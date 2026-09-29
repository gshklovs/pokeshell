r"""Lookbook sheets for Brilliant Stars (ART_METHOD section 15): ALWAYS real card | ours | ours + text half, one row per
card, about 5 cards per image (the lookbook page has a file limit), -> <DATA>/brs/sheets/lookbook/:

  ladder_<k>.jpg                 the ladder, one card per printed rarity and finish
  ladder-<id>.gif                a few of the ladder's 16-frame loops (the terminal gifs from anim/<id>/)
  <nn>-<rarity>_<k>.jpg          every built card, grouped by printed rarity (and finish), in number order
  index.json                     what each file holds

Builders come in precedence order (audit/allcards.py: ladder < group batches < batch_fixes), so the sheets show the
art that would ship. Run after the batches (and the audit fixes):

  ..\..\..\.venv\Scripts\python lookbook.py [--ladder-only]
"""
import json
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent / "audit"))
import allcards as AC  # noqa: E402

P, C, E = AC.P, AC.C, AC.P.E
H = 440
GAP = 18
PER = 5
FONT = "C:/Windows/Fonts/consola.ttf"
GIFS = ["swsh9-17", "swsh9-18", "swsh9-152", "swsh9-154", "swsh9-174", "swsh9-184", "swsh9tg-TG11", "swsh9tg-TG23"]
ORDER = [("01-common", "Common"), ("02-uncommon", "Uncommon"), ("03-rare", "Rare"), ("04-rare-holo", "Rare Holo"),
         ("05-rare-holo-v", "Rare Holo V"), ("06-rare-holo-vmax", "Rare Holo VMAX"),
         ("07-rare-holo-vstar", "Rare Holo VSTAR"), ("08-rare-ultra-full-art", "Rare Ultra (full art)"),
         ("09-rare-ultra-alt-art", "Rare Ultra (alt-art painting)"), ("10-rare-rainbow", "Rare Rainbow"),
         ("11-rare-secret", "Rare Secret (gold)"), ("12-trainer-gallery", "Trainer Gallery Rare Holo"),
         ("13-tg-v-vmax", "Trainer Gallery Rare Holo V / VMAX (alt-art painting)")]


def bucket(cid):
    t = P.card_json(cid)["tier"]
    tg = P.is_tg(cid)
    kind = C.cfg(cid)["kind"]
    return {"Common": "01-common", "Uncommon": "02-uncommon", "Rare": "03-rare", "Rare Holo": "04-rare-holo",
            "Rare Holo V": "13-tg-v-vmax" if tg else "05-rare-holo-v",
            "Rare Holo VMAX": "13-tg-v-vmax" if tg else "06-rare-holo-vmax",
            "Rare Holo VSTAR": "07-rare-holo-vstar",
            "Rare Ultra": "09-rare-ultra-alt-art" if kind == "alt" else "08-rare-ultra-full-art",
            "Rare Rainbow": "10-rare-rainbow", "Rare Secret": "11-rare-secret",
            "Trainer Gallery Rare Holo": "12-trainer-gallery"}[t]


def fit(im, h):
    return im.resize((max(1, round(im.width * h / im.height)), h), Image.LANCZOS)


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
    d.text((GAP, 6), f"{card['name']}  {card['number']}  ({cid})  tier: {card['tier']}", font=f, fill=(240, 220, 150))
    d.text((GAP, 28), f"{k['kind']}  sprite {k['sprite']}{' flipped' if flip else ''}  [{AC.OWNER[cid]}]", font=f,
           fill=(170, 170, 170))
    x = GAP
    for im in (real, art, st):
        t.paste(im, (x, 52))
        x += im.width + GAP
    return t


def sheets(ids, title, stem, out, f, ft):
    files = []
    for k in range(0, len(ids), PER):
        part = ids[k:k + PER]
        tiles = [tile(c, f) for c in part]
        W = max(t.width for t in tiles) + GAP
        n = (len(ids) + PER - 1) // PER
        o = Image.new("RGB", (W, 64 + sum(t.height + GAP for t in tiles)), (16, 16, 20))
        ImageDraw.Draw(o).text((GAP, 14), f"BRS {title} ({k // PER + 1}/{n})  real | ours | ours+text",
                               font=ft, fill=(240, 240, 240))
        y = 64
        for t in tiles:
            o.paste(t, (GAP // 2, y))
            y += t.height + GAP
        p = out / f"{stem}_{k // PER + 1}.jpg"
        o.save(p, quality=88)
        files.append({"png": p.name, "ids": part})
        print(p.name, len(part), o.size)
    return files


def main():
    f = ImageFont.truetype(FONT, 19)
    ft = ImageFont.truetype(FONT, 26)
    out = P.DATA / "sheets" / "lookbook"
    out.mkdir(parents=True, exist_ok=True)
    index = {"ladder": sheets(list(C.LADDER), "ladder", "ladder", out, f, ft)}
    for cid in GIFS:
        g = P.DATA / "anim" / cid / f"{cid}-term.gif"
        if g.exists():
            shutil.copy(g, out / f"ladder-{cid}.gif")
            index.setdefault("gifs", []).append(f"ladder-{cid}.gif")
    if "--ladder-only" not in sys.argv:
        groups = {}
        for cid in AC.IDS:
            groups.setdefault(bucket(cid), []).append(cid)
        key = lambda c: (P.is_tg(c), P.seed_of(c))  # noqa: E731
        for name, title in ORDER:
            ids = sorted(groups.get(name, []), key=key)
            if ids:
                index[name] = {"title": title, "files": sheets(ids, f"{title}, {len(ids)}", name, out, f, ft)}
    (out / "index.json").write_text(json.dumps(index, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
