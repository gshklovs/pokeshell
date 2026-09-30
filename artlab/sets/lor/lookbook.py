r"""Lookbook sheets for Lost Origin (ART_METHOD section 15): ALWAYS real card | ours | ours + text half, one row per
card. The lookbook page is near its file limit, so the whole set fits in at most 14 image files, in
<DATA>/lor/sheets/lookbook/:

  ladder.jpg                     ONE tall image: the ladder, one card per printed rarity and finish
  ladder-<id>.gif                two of the 16-frame loops (the terminal gifs from anim/<id>/): Giratina VSTAR 131
                                 and the Giratina V alt art 186
  <nn>-<name>.jpg                at most 11 bundles, each stacking one per-rarity sheet (or several), JPEG, width
                                 <= 1400; every built card, grouped by printed rarity (and finish), in number order
  index.json                     which rarities (and ids) each image holds

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
H = 330                      # row height (px) of each of the three panels
GAP = 14
MAXW = 1400
FONT = "C:/Windows/Fonts/consola.ttf"
GIFS = ["swsh11-131", "swsh11-186"]
# printed rarity (and finish) sections
SECTIONS = [("common", "Common"), ("uncommon", "Uncommon"), ("rare", "Rare"), ("holo", "Rare Holo"),
            ("v", "Rare Holo V"), ("vmax", "Rare Holo VMAX"), ("vstar", "Rare Holo VSTAR"), ("radiant", "Radiant Rare"),
            ("fullart", "Rare Ultra (full art)"), ("alt", "Rare Ultra (alt-art painting)"), ("rainbow", "Rare Rainbow"),
            ("gold", "Rare Secret (gold)"), ("tg", "Trainer Gallery Rare Holo"),
            ("tg_v", "Trainer Gallery Rare Holo V / VMAX (alt-art painting)")]
TITLE = dict(SECTIONS)
# the <= 11 bundles: file stem -> sections it stacks (commons split in two halves)
BUNDLES = [("01-common-1", ["common:0"]), ("02-common-2", ["common:1"]), ("03-uncommon", ["uncommon"]),
           ("04-rare", ["rare"]), ("05-rare-holo", ["holo"]), ("06-v-vmax", ["v", "vmax"]),
           ("07-vstar-radiant", ["vstar", "radiant"]), ("08-rare-ultra-full-art", ["fullart"]),
           ("09-alt-rainbow-gold", ["alt", "rainbow", "gold"]), ("10-trainer-gallery", ["tg"]),
           ("11-tg-v-vmax", ["tg_v"])]


def section(cid):
    t = P.card_json(cid)["tier"]
    tg = P.is_tg(cid)
    kind = C.cfg(cid)["kind"]
    if tg and t in ("Rare Holo V", "Rare Holo VMAX"):
        return "tg_v"
    return {"Common": "common", "Uncommon": "uncommon", "Rare": "rare", "Rare Holo": "holo", "Rare Holo V": "v",
            "Rare Holo VMAX": "vmax", "Rare Holo VSTAR": "vstar", "Radiant Rare": "radiant",
            "Rare Ultra": "alt" if kind == "alt" else "fullart", "Rare Rainbow": "rainbow", "Rare Secret": "gold",
            "Trainer Gallery Rare Holo": "tg"}[t]


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
    w = real.width + art.width + st.width + 4 * GAP
    if w > MAXW:                                  # never wider than the page budget: shrink the three panels
        s = (MAXW - 4 * GAP) / (w - 4 * GAP)
        real, art, st = (im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)
                         for im in (real, art, st))
    t = Image.new("RGB", (min(MAXW, real.width + art.width + st.width + 4 * GAP), H + 50), (24, 24, 28))
    d = ImageDraw.Draw(t)
    flip = cid in P.META.get("flip_commons", []) if k["kind"] == "common" else k["flip"]
    d.text((GAP, 4), f"{card['name']}  {card['number']}  ({cid})  tier: {card['tier']}", font=f, fill=(240, 220, 150))
    d.text((GAP, 24), f"{k['kind']}  sprite {k['sprite']}{' flipped' if flip else ''}  [{AC.OWNER[cid]}]", font=f,
           fill=(170, 170, 170))
    x = GAP
    for im in (real, art, st):
        t.paste(im, (x, 46))
        x += im.width + GAP
    return t


def stack(parts, ft):
    """parts: [(heading, [tiles])] -> one image, width <= MAXW"""
    W = min(MAXW, max(t.width for _, ts in parts for t in ts) + GAP)
    Ht = sum(52 + sum(t.height + GAP for t in ts) for _, ts in parts) + GAP
    o = Image.new("RGB", (W, Ht), (16, 16, 20))
    d = ImageDraw.Draw(o)
    y = GAP
    for head, ts in parts:
        d.text((GAP, y + 8), head, font=ft, fill=(240, 240, 240))
        y += 52
        for t in ts:
            o.paste(t, (GAP // 2, y))
            y += t.height + GAP
    return o


def main():
    f = ImageFont.truetype(FONT, 17)
    ft = ImageFont.truetype(FONT, 24)
    out = P.DATA / "sheets" / "lookbook"
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*"):
        old.unlink()
    lad = list(C.LADDER)
    o = stack([(f"LOR ladder: one card per printed rarity and finish ({len(lad)})  real | ours | ours+text",
                [tile(c, f) for c in lad])], ft)
    o.save(out / "ladder.jpg", quality=86)
    index = {"ladder.jpg": {"holds": "the ladder: " + ", ".join(sorted({P.card_json(c)['tier'] for c in lad})),
                            "ids": lad, "size": list(o.size)}}
    print("ladder.jpg", o.size)
    for cid in GIFS:
        g = P.DATA / "anim" / cid / f"{cid}-term.gif"
        if g.exists():
            shutil.copy(g, out / f"ladder-{cid}.gif")
            index[f"ladder-{cid}.gif"] = {"holds": f"16-frame loop, {P.card_json(cid)['name']} {cid} "
                                                   f"({P.card_json(cid)['tier']}, anim {C.BUILDERS[cid]().meta['anim']})"}
    if "--ladder-only" not in sys.argv:
        groups = {}
        for cid in AC.IDS:
            groups.setdefault(section(cid), []).append(cid)
        key = lambda c: (P.is_tg(c), P.seed_of(c))  # noqa: E731
        for name in groups:
            groups[name] = sorted(groups[name], key=key)
        done = set()
        for stem, secs in BUNDLES:
            parts, held = [], []
            for s in secs:
                name, _, half = s.partition(":")
                ids = groups.get(name, [])
                if half:
                    k = (len(ids) + 1) // 2
                    ids = ids[:k] if half == "0" else ids[k:]
                    head = f"{TITLE[name]} ({int(half) + 1}/2), {len(ids)}"
                else:
                    head = f"{TITLE[name]}, {len(ids)}"
                if not ids:
                    continue
                done |= set(ids)
                parts.append((f"LOR {head}  real | ours | ours+text", [tile(c, f) for c in ids]))
                held.append({"rarity": TITLE[name] + (f" ({int(half) + 1}/2)" if half else ""), "ids": ids})
            if not parts:
                continue
            o = stack(parts, ft)
            o.save(out / f"{stem}.jpg", quality=84)
            index[f"{stem}.jpg"] = {"holds": [h["rarity"] for h in held], "sections": held, "size": list(o.size)}
            print(f"{stem}.jpg", o.size, sum(len(h["ids"]) for h in held))
        missing = [c for c in AC.IDS if c not in done]
        assert not missing, f"cards in no bundle: {missing}"
    files = sorted(p.name for p in out.glob("*") if p.suffix in (".jpg", ".gif"))
    assert len(files) <= 14, f"{len(files)} image files, the budget is 14"
    (out / "index.json").write_text(json.dumps(index, indent=1), encoding="utf-8")
    print(len(files), "image files")


if __name__ == "__main__":
    main()
