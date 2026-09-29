"""Render pack art (packs/<pack>/art/*.json) to ready-to-print ANSI files and PNG previews.

  .venv/Scripts/python tools/build_art.py            # build everything
  .venv/Scripts/python tools/build_art.py pikachu    # only art ids containing "pikachu"
  (real-card packs: tools/build_realcards.py writes the art JSON and calls build_file() for each card)

Outputs
  dist/<pack>/<id>-<variant>.ans         truecolor half-block art (2 pixels per text row)
  dist/<pack>/<id>-<variant>-shiny.ans   same with the shiny palette (if the art defines one)
  previews/<pack>/<id>-<variant>[-shiny].png   12x upscaled PNG, for eyeballing

Art file format: see docs/ART_FORMAT.md.
"""
import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ESC = "\x1b"
UPPER, LOWER = "▀", "▄"  # ▀ ▄
# the largest art a card may have (docs/ART_FORMAT.md): 140 x 110 px = 140 columns x 55 lines. Real-card scenes
# (the colorscripts sprite over the card's scene) go up to that; pixel-art sprites stay far smaller.
MAX_W, MAX_H = 140, 110


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def validate(rows, palette, where):
    w = len(rows[0])
    for i, r in enumerate(rows):
        if len(r) != w:
            raise SystemExit(f"{where}: row {i} is {len(r)} wide, expected {w}")
        for ch in r:
            if ch != "." and ch not in palette:
                raise SystemExit(f"{where}: row {i} uses '{ch}' which is not in the palette")
    if w > MAX_W or len(rows) > MAX_H:
        raise SystemExit(f"{where}: {w}x{len(rows)} exceeds {MAX_W}x{MAX_H}")


def to_ansi(rows, palette):
    rows = list(rows) + (["." * len(rows[0])] if len(rows) % 2 else [])
    out = []
    for y in range(0, len(rows), 2):
        top, bot = rows[y], rows[y + 1]
        line, last = [], None
        for t, b in zip(top, bot):
            if t == "." and b == ".":
                code, ch = f"{ESC}[0m", " "
            elif t == ".":
                code, ch = f"{ESC}[0;38;2;{';'.join(map(str, hex_rgb(palette[b])))}m", LOWER
            elif b == ".":
                code, ch = f"{ESC}[0;38;2;{';'.join(map(str, hex_rgb(palette[t])))}m", UPPER
            else:
                fg, bg = hex_rgb(palette[t]), hex_rgb(palette[b])
                code, ch = f"{ESC}[0;38;2;{fg[0]};{fg[1]};{fg[2]};48;2;{bg[0]};{bg[1]};{bg[2]}m", UPPER
            if code != last:
                line.append(code)
                last = code
            line.append(ch)
        out.append("".join(line).rstrip() + f"{ESC}[0m")
    # trim trailing blank lines
    while out and out[-1].replace(f"{ESC}[0m", "").strip() == "":
        out.pop()
    return "\n".join(out) + "\n"


def to_png(rows, palette, path, scale=12):
    w, h = len(rows[0]), len(rows)
    img = Image.new("RGB", (w, h), (12, 12, 12))  # terminal-ish dark background
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch != ".":
                img.putpixel((x, y), hex_rgb(palette[ch]))
    img.resize((w * scale, h * scale), Image.NEAREST).save(path)


def build_file(art_file, previews=True):
    """render one art JSON to dist/<pack>/<id>-<variant>[-shiny].ans (+ previews); returns the files written"""
    art_file = Path(art_file)
    pack = art_file.parent.parent.name
    art = json.loads(art_file.read_text(encoding="utf-8"))
    art_id = art["id"]
    (ROOT / "dist" / pack).mkdir(parents=True, exist_ok=True)
    if previews:
        (ROOT / "previews" / pack).mkdir(parents=True, exist_ok=True)
    out = []
    for vname, v in art["variants"].items():
        base = {**art["palette"], **v.get("palette", {})}
        palettes = {"": base}
        if "shiny" in art or "shiny" in v:
            palettes["-shiny"] = {**base, **art.get("shiny", {}), **v.get("shiny", {})}
        for suffix, pal in palettes.items():
            validate(v["rows"], pal, f"{art_file.name}:{vname}{suffix}")
            name = f"{art_id}-{vname}{suffix}"
            dst = ROOT / "dist" / pack / f"{name}.ans"
            dst.write_text(to_ansi(v["rows"], pal), encoding="utf-8", newline="\n")
            out.append(dst)
            if previews:
                to_png(v["rows"], pal, ROOT / "previews" / pack / f"{name}.png")
    return out


def build(filter_text=""):
    count = 0
    for art_file in sorted(ROOT.glob("packs/*/art/*.json")):
        art_id = json.loads(art_file.read_text(encoding="utf-8"))["id"]
        if filter_text and filter_text not in art_id and filter_text not in art_file.stem:
            continue
        count += len(build_file(art_file))
    print(f"built {count} art files")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "")
