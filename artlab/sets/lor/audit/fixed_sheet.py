r"""Before / after of the audit fixes (ART_METHOD section 16): real card | before | after, one row per fixed card
-> <DATA>/lor/work/audit/fixed_<k>.png. The "before" renders are copies of out/<id>-art.png taken into
work/audit/before/ just before batch_fixes.py ran.

  ..\..\..\..\.venv\Scripts\python audit\fixed_sheet.py
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import lorlib as P  # noqa: E402
import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location("lor_batch_fixes", P.HERE / "batch_fixes.py")
F = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(F)

E = P.E
H = 300


def fit(im, h):
    return im.resize((max(1, round(im.width * h / im.height)), h), Image.LANCZOS)


def main():
    out = E.WORK / "audit"
    f = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 18)
    ids = list(F.TABLE)
    for k in range(0, len(ids), 6):
        rows = []
        for cid in ids[k:k + 6]:
            b = out / "before" / f"{cid}-art.png"
            ims = [fit(Image.open(P.ref_path(cid)).convert("RGB"), H)]
            ims += [fit(Image.open(p).convert("RGB"), H) for p in (b, E.OUT / f"{cid}-art.png") if p.exists()]
            t = Image.new("RGB", (sum(i.width + 10 for i in ims), H + 26), (24, 24, 28))
            ImageDraw.Draw(t).text((4, 2), f"{cid}  real | before | after", font=f, fill=(255, 220, 120))
            x = 0
            for i in ims:
                t.paste(i, (x, 26))
                x += i.width + 10
            rows.append(t)
        o = Image.new("RGB", (max(r.width for r in rows), sum(r.height + 8 for r in rows)), (12, 12, 12))
        y = 0
        for r in rows:
            o.paste(r, (0, y))
            y += r.height + 8
        p = out / f"fixed_{k // 6}.png"
        o.save(p)
        print(p)


if __name__ == "__main__":
    main()
