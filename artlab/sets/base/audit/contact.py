r"""Audit contact sheets: real card | ours, several cards per sheet, grouped by rarity, for the per-card visual
check (docs/ART_METHOD.md section 16). -> <DATA>/base/work/audit/sheets/<n>-<group>.png

  ..\..\..\..\.venv\Scripts\python contact.py [group ...]
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import baselib as P  # noqa: E402
from baselib import E  # noqa: E402

FONT = "C:/Windows/Fonts/consola.ttf"
H = 330
PER = 6


def groups():
    plan = json.loads((P.HERE / "plan.json").read_text(encoding="utf-8"))
    meta = json.loads((P.HERE / "set.json").read_text(encoding="utf-8"))
    out = {"ladder": meta["ladder"]}
    for g, v in plan.items():
        if not g.startswith("_"):
            out[g] = [e["id"] for e in v]
    return out


def tile(cid):
    real = Image.open(P.ref_path(cid)).convert("RGB")
    real = real.resize((round(real.width * H / real.height), H), Image.LANCZOS)
    art = Image.open(E.OUT / f"{cid}-art.png").convert("RGB")
    k = min(H / art.height, 560 / art.width)
    art = art.resize((round(art.width * k), round(art.height * k)), Image.NEAREST)
    t = Image.new("RGB", (real.width + art.width + 30, H + 24), (24, 24, 28))
    t.paste(real, (0, 24))
    t.paste(art, (real.width + 20, 24))
    card = P.card_json(cid)
    ImageDraw.Draw(t).text((4, 2), f"{cid} {card['name']} [{card['tier']}]", font=ImageFont.truetype(FONT, 16),
                           fill=(255, 230, 90))
    return t


def main(which):
    out = E.WORK / "audit" / "sheets"
    out.mkdir(parents=True, exist_ok=True)
    n = 0
    for g, ids in groups().items():
        if which and g not in which:
            continue
        ids = [c for c in ids if (E.OUT / f"{c}-art.png").exists()]
        for i in range(0, len(ids), PER):
            tiles = [tile(c) for c in ids[i:i + PER]]
            W = max(t.width for t in tiles)
            sheet = Image.new("RGB", (2 * W, ((len(tiles) + 1) // 2) * (H + 30)), (12, 12, 14))
            for j, t in enumerate(tiles):
                sheet.paste(t, ((j % 2) * W, (j // 2) * (H + 30)))
            n += 1
            f = out / f"{n:02d}-{g}.png"
            sheet.save(f)
            print(f)


if __name__ == "__main__":
    main(sys.argv[1:])
