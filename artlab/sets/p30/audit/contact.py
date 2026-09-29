"""contact sheets for the p30 audit: real card | our art, `per` cards per image -> work/audit/sheets/<group>-<n>.png
   usage: contact.py [per] [row_h] [ids-or-groups,comma]"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

CODE = Path(__file__).resolve().parents[1]         # artlab/sets/p30: the set's code
sys.path.insert(0, str(CODE.parents[1]))
import artpaths  # noqa: E402
HERE = artpaths.data("p30")                       # style-lab/p30: the set's data
sys.path.insert(0, str(CODE))
import p30lib as P  # noqa: E402

AUD = HERE / "work/audit"
meta = json.load(open(AUD / "meta.json", encoding="utf-8"))
ORDER = ["ladder", "commons", "rare", "pikachu_rare", "double_rare", "illustration_rare", "sir_futuristic"]
FONT = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 17)


def fit(im, h, wmax):
    k = min(h / im.height, wmax / im.width)
    return im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)


def main():
    per = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    rh = int(sys.argv[2]) if len(sys.argv) > 2 else 420
    only = sys.argv[3].split(",") if len(sys.argv) > 3 else None
    ids = [c for g in ORDER for c in meta if meta[c].get("group") == g and meta[c].get("pokemon")]
    if only:
        ids = [c for c in ids if c in only or meta[c]["group"] in only]
    out = AUD / "sheets"
    out.mkdir(exist_ok=True)
    tw = int(rh * 0.717) + int(rh * 1.25) + 30
    cols = 2
    for n in range(0, len(ids), per):
        chunk = ids[n:n + per]
        rows = (len(chunk) + cols - 1) // cols
        o = Image.new("RGB", (cols * tw + 10, rows * (rh + 44) + 10), (30, 30, 34))
        d = ImageDraw.Draw(o)
        for i, cid in enumerate(chunk):
            m = meta[cid]
            x, y = 10 + (i % cols) * tw, 10 + (i // cols) * (rh + 44)
            real = fit(Image.open(P.ref_path(cid)).convert("RGB"), rh, rh)
            us = fit(Image.open(HERE / "out" / f"{cid}-art.png").convert("RGB"), rh, int(rh * 1.25))
            o.paste(real, (x, y + 40))
            o.paste(us, (x + real.width + 8, y + 40))
            t = f"{cid} {m['name']} [{m['tier']}] spr={m['pokemon']} flip={m['flip']}"
            d.text((x, y), t, font=FONT, fill=(240, 240, 120))
            d.text((x, y + 19), m["finish"][:95], font=FONT, fill=(190, 190, 190))
        pre = (sys.argv[3].replace(",", "_")[:40] + "-") if only else ""
        o.save(out / f"{pre}{n // per:02d}.png")
        print(pre, n // per, o.size, chunk)


if __name__ == "__main__":
    main()
