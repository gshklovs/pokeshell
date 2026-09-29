"""Render the binder's headless frames to PNG.

  target/release/binder --snapshot snapshots        # TestBackend frames -> snapshots/*.ans + *.txt
  ../.venv/Scripts/python snap.py snapshots         # -> snapshots/*.png (via tools/render_ansi.py)
  ../.venv/Scripts/python snap.py snapshots --scale 1 --only foil

Uses the repo's ANSI renderer (Cascadia Mono + Windows Terminal-style box/block/braille geometry).
The shimmer-*.ans frames are also stitched into shimmer-strip.png.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))
import render_ansi  # noqa: E402
from PIL import Image  # noqa: E402


def main():
    args = sys.argv[1:]
    d = Path(args[0]) if args else HERE / "snapshots"
    scale = int(args[args.index("--scale") + 1]) if "--scale" in args else 1
    only = args[args.index("--only") + 1] if "--only" in args else ""
    for f in sorted(d.glob("*.ans")):
        if only and only not in f.stem:
            continue
        text = f.read_text(encoding="utf-8")
        img = render_ansi.render(text, None, scale=scale, pad=1)
        img.save(f.with_suffix(".png"))
        print(f.with_suffix(".png").name, img.size)
    frames = sorted(d.glob("shimmer-*.png"))
    if frames and not only:
        # crop each to the card panel region (right column, top half) and stack side by side
        ims = [Image.open(p) for p in frames if "strip" not in p.name]
        w, h = ims[0].size
        box = (int(w * 0.5), 0, w, int(h * 0.56))
        crops = [im.crop(box) for im in ims]
        cw, ch = crops[0].size
        strip = Image.new("RGB", (cw * len(crops), ch))
        for i, c in enumerate(crops):
            strip.paste(c, (i * cw, 0))
        strip.save(d / "shimmer-strip.png")
        print("shimmer-strip.png", strip.size)


if __name__ == "__main__":
    main()
