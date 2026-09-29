"""contact sheets for the EVS audit: real card | our art, `per` cards per image -> work/audit/sheets/<n>.png
   usage: contact.py [per] [row_h]"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

CODE = Path(__file__).resolve().parents[1]         # artlab/sets/evs: the set's code
sys.path.insert(0, str(CODE.parents[1]))
import artpaths  # noqa: E402
HERE = artpaths.data("evs")                       # style-lab/evs: the set's data
ROOT = artpaths.ROOT                                 # repo
sys.path.insert(0, str(CODE))
import evlib as E  # noqa: E402
from evlib import L  # noqa: E402

AUD = HERE / "work/audit"
meta = json.load(open(AUD / "meta.json", encoding="utf-8"))
ORDER = ["ladder", "commons", "uncommon", "rare", "holo", "v", "vmax", "ultra_a", "ultra_b", "rainbow_secret"]
FONT = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 17)


def ours(cid):
    f = HERE / "out" / f"{cid}-art.png"
    if f.exists():
        return Image.open(f).convert("RGB")
    ch = meta[cid]["pack"]["character"]
    png = AUD / "commons" / f"{cid}.png"
    if not png.exists():
        png.parent.mkdir(exist_ok=True)
        ans = (ROOT / "dist/pokemon" / f"{ch}-{cid}.ans").read_text(encoding="utf-8")
        L.render(ans, str(png))
    return Image.open(png).convert("RGB")


def fit(im, h, wmax):
    k = min(h / im.height, wmax / im.width)
    return im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)


def main():
    per = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    rh = int(sys.argv[2]) if len(sys.argv) > 2 else 420
    only = sys.argv[3].split(",") if len(sys.argv) > 3 else None
    ids = [c for g in ORDER for c in meta if meta[c]["group"] == g]
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
            real = fit(Image.open(E.ref_path(cid)).convert("RGB"), rh, rh)
            us = fit(ours(cid), rh, int(rh * 1.25))
            o.paste(real, (x, y + 40))
            o.paste(us, (x + real.width + 8, y + 40))
            t = f"{cid} {m['name']} [{m['tier']}] spr={m.get('pokemon') or m['pack']['character']} flip={m.get('flip')}"
            d.text((x, y), t, font=FONT, fill=(240, 240, 120))
            d.text((x, y + 19), (m.get("finish") or "plain sprite (pack builder)")[:95], font=FONT, fill=(190, 190, 190))
        pre = (sys.argv[3].replace(",", "_") + "-") if only else ""
        o.save(out / f"{pre}{n // per:02d}.png")
        print(pre, n // per, o.size, chunk)


if __name__ == "__main__":
    main()
