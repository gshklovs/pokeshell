"""audit/fixed.png: real | before | after for every fixed card"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import artpaths  # noqa: E402
H = artpaths.data("p30")
IDS = ["me55-66", "me55-26", "me55-129"]
F = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 22)
RH = 520
def fit(im):
    return im.resize((round(im.width * RH / im.height), RH), Image.LANCZOS)
rows = []
for cid in IDS:
    n = cid.split("-")[1]
    rows.append((cid, [fit(Image.open(H / "ref" / f"me55_{n}.png").convert("RGB")),
                       fit(Image.open(H / "work/audit/before/out" / f"{cid}-art.png").convert("RGB")),
                       fit(Image.open(H / "out" / f"{cid}-art.png").convert("RGB"))]))
W = max(sum(i.width for i in r) + 20 * 4 for _, r in rows)
o = Image.new("RGB", (W, len(rows) * (RH + 60) + 20), (28, 28, 32))
d = ImageDraw.Draw(o)
y = 10
for cid, ims in rows:
    d.text((20, y), f"{cid}   real | before | after", font=F, fill=(240, 240, 140))
    x = 20
    for i in ims:
        o.paste(i, (x, y + 40)); x += i.width + 20
    y += RH + 60
o.save(H / "audit/fixed.png"); print(o.size)
