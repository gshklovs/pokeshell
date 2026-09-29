"""zoom.py out.png id,id,... : real card (top 60%) | our art, big"""
import sys
from pathlib import Path
from PIL import Image
CODE = Path(__file__).resolve().parents[1]         # artlab/sets/evs: the set's code
sys.path.insert(0, str(CODE.parents[1]))
import artpaths  # noqa: E402
HERE = artpaths.data("evs")                       # style-lab/evs: the set's data
ids = sys.argv[2].split(",")
H = int(sys.argv[3]) if len(sys.argv) > 3 else 520
tiles = []
for cid in ids:
    n = cid.split("-")[1]
    real = Image.open(HERE / "ref" / f"swsh7_{n}.png").convert("RGB")
    real = real.crop((0, 0, 734, 720))
    f = HERE / "out" / f"{cid}-art.png"
    if not f.exists():
        f = HERE / "work/audit/commons" / f"{cid}.png"
    us = Image.open(f).convert("RGB")
    r = real.resize((round(real.width * H / real.height), H))
    u = us.resize((round(us.width * H / us.height), H))
    t = Image.new("RGB", (r.width + u.width + 30, H), (30, 30, 34))
    t.paste(r, (0, 0)); t.paste(u, (r.width + 10, 0))
    tiles.append(t)
W = max(t.width for t in tiles)
o = Image.new("RGB", (W, sum(t.height + 10 for t in tiles)), (30, 30, 34))
y = 0
for t in tiles:
    o.paste(t, (0, y)); y += t.height + 10
o.save(sys.argv[1])
