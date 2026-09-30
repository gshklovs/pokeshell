"""Render the binder's headless frames to PNG.

  target/release/binder --snapshot snapshots        # TestBackend frames -> snapshots/*.ans + *.txt
  ../.venv/Scripts/python snap.py snapshots         # -> snapshots/*.png (via tools/render_ansi.py)
  ../.venv/Scripts/python snap.py snapshots --scale 1 --only foil

Uses the repo's ANSI renderer (Cascadia Mono + Windows Terminal-style box/block/braille geometry).
The shimmer-*.ans frames are also stitched into shimmer-strip.png. A frame with a <name>.six next to it (the printed
card's sixel image, `p`: "x y w h" then the sixel data the terminal would get) has the image decoded and painted
over its cells, as Windows Terminal would show it.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))
import render_ansi  # noqa: E402
from PIL import Image  # noqa: E402


def decode_sixel(data):
    """a sixel image (DCS ... q ... ST) -> an RGBA PIL image; unset pixels stay transparent"""
    body = data[data.index("q") + 1:].rstrip(chr(27) + chr(92))
    i, n = 0, len(body)
    w = h = 0
    if body.startswith('"'):
        j = i + 1
        while j < n and (body[j].isdigit() or body[j] == ";"):
            j += 1
        pa = [int(x) for x in body[1:j].split(";") if x]
        if len(pa) >= 4:
            w, h = pa[2], pa[3]
        i = j
    img = Image.new("RGBA", (max(w, 1), max(h, 1)), (0, 0, 0, 0))
    px = img.load()
    pal, cur, x, y = {}, 0, 0, 0

    def num(j):
        k = j
        while k < n and body[k].isdigit():
            k += 1
        return int(body[j:k] or 0), k
    while i < n:
        c = body[i]
        if c == "#":
            v, i = num(i + 1)
            if i < n and body[i] == ";":
                parts = [v]
                while i < n and body[i] == ";":
                    p, i = num(i + 1)
                    parts.append(p)
                if len(parts) >= 5 and parts[1] == 2:
                    pal[parts[0]] = tuple(round(q * 255 / 100) for q in parts[2:5])
            cur = v
            continue
        rep = 1
        if c == "!":
            rep, i = num(i + 1)
            c = body[i]
        if c == "$":
            x = 0
        elif c == "-":
            x, y = 0, y + 6
        elif "?" <= c <= "~":
            bits = ord(c) - 63
            col = pal.get(cur, (0, 0, 0)) + (255,)
            for _ in range(rep):
                for b in range(6):
                    if bits >> b & 1 and x < img.width and y + b < img.height:
                        px[x, y + b] = col
                x += 1
        i += 1
    return img


def paint_sixel(img, six, cw, ch, pad=1):
    """paint a .six (the printed card's sixel image) over the frame's cells: its virtual 10x20 cells scaled to ours"""
    head, data = six.split(chr(10), 1)
    x, y, w, h = (int(v) for v in head.split())
    im = decode_sixel(data).resize((w * cw, h * ch), Image.LANCZOS)
    img.paste(im, ((x + pad) * cw, (y + pad) * ch), im)


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
        six = f.with_suffix(".six")
        if six.exists():
            paint_sixel(img, six.read_text(encoding="ascii"), 8 * scale, 16 * scale, pad=1)
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
