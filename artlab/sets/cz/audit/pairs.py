r"""Audit contact sheets: real card | ours (art), 3 per row, for a list of ids -> one PNG per 12 cards.
  ..\..\..\..\.venv\Scripts\python audit\pairs.py <name> <id> [<id> ...]    -> work/audit/<name>_<k>.png
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import czlib as P  # noqa: E402

E = P.E
H = 330


def tile(cid):
    r = Image.open(P.ref_path(cid)).convert("RGB")
    r = r.resize((round(r.width * H / r.height), H), Image.LANCZOS)
    a = Image.open(E.OUT / f"{cid}-art.png").convert("RGB")
    k = min(H / a.height, 430 / a.width)
    a = a.resize((max(1, round(a.width * k)), max(1, round(a.height * k))), Image.LANCZOS)
    t = Image.new("RGB", (r.width + 440, H + 22), (25, 25, 30))
    t.paste(r, (0, 22))
    t.paste(a, (r.width + 8, 22 + (H - a.height) // 2))
    ImageDraw.Draw(t).text((4, 2), cid, font=ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 17), fill=(255, 255, 0))
    return t


def main():
    name, ids = sys.argv[1], sys.argv[2:]
    out = E.WORK / "audit"
    out.mkdir(parents=True, exist_ok=True)
    per, rows = 3, 4
    for k in range(0, len(ids), per * rows):
        ts = [tile(c) for c in ids[k:k + per * rows]]
        W = max(t.width for t in ts)
        o = Image.new("RGB", (W * per, (H + 22) * ((len(ts) + per - 1) // per)), (12, 12, 12))
        for i, t in enumerate(ts):
            o.paste(t, ((i % per) * W, (i // per) * (H + 22)))
        f = out / f"{name}_{k // (per * rows)}.png"
        o.save(f)
        print(f)


if __name__ == "__main__":
    main()
