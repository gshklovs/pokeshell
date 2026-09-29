"""Shared helpers for animated pixel-art cards (artlab/lib; was style-lab/anim).

Frames are built as RGB grids (lists of rows of (r,g,b) tuples, None = transparent)
from small hand-picked ramps, then quantised with ONE shared palette across all
frames and exported as:
  <card>/<card>.json             {palette, frames:[rows...], frame_ms, final_frame, ...}
  <card>/ans/<card>-NN.ans       one truecolor half-block frame per file
  <card>/<card>.anim             all frames in one file, separated by a form feed (what play.ps1 reads)
  <card>/<card>-x12.gif          12x pixel preview, real frame timing
  <card>/<card>-term.gif         terminal proportions (8x16 cells, 2 px rows per cell, dark bg)
  <card>/<card>-sheet.png        contact sheet of every frame (for review)
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

LIB = Path(__file__).resolve().parent             # artlab/lib
sys.path.insert(0, str(LIB.parent))
import artpaths  # noqa: E402
LAB = artpaths.DATA
ROOT = artpaths.ROOT
ANIM = LAB / "anim"                               # export(): the stand-alone demo cards' frame folders
sys.path.insert(0, str(artpaths.TOOLS))
from build_art import to_ansi, hex_rgb  # noqa: E402

BG = (12, 12, 12)
KEYS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!#$%&*+-/:;<=>?@^_~|{}()[],'\"`\\"


def hexc(h):
    return hex_rgb(h)


def grid(w, h, v=None):
    return [[v] * w for _ in range(h)]


def copy(g):
    return [list(r) for r in g]


def rows_to_rgb(rows, pal):
    return [[None if k == "." else hexc(pal[k]) for k in r] for r in rows]


# ---- 4-point star sparkle ----------------------------------------------------
# stage 0 = off, 1 = dot, 2 = small plus, 3 = big star, (then back down)
STAR_LIFE = [1, 2, 3, 2, 1]


def star(g, x, y, stage, core, mid, tip, allow=None):
    """Draw a 4-point star centred at (x,y). allow(x,y) -> bool gates each pixel
    (e.g. only over background)."""
    H, W = len(g), len(g[0])

    def put(px, py, c):
        if 0 <= px < W and 0 <= py < H and (allow is None or allow(px, py)):
            g[py][px] = c
    if stage <= 0:
        return
    if stage == 1:
        put(x, y, mid)
        return
    if stage == 2:
        put(x, y, core)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            put(x + dx, y + dy, tip)
        return
    # stage 3: long cross, bright core, tapering arms
    put(x, y, core)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        put(x + dx, y + dy, core if dy == 0 and False else mid)
        put(x + 2 * dx, y + 2 * dy, tip)
    # vertical arms one pixel longer: reads as a sharper glint
    put(x, y - 3, tip)
    put(x, y + 3, tip)


def star_stage(frame, start, n_frames):
    k = (frame - start) % n_frames
    return STAR_LIFE[k] if k < len(STAR_LIFE) else 0


# ---- quantise + export --------------------------------------------------------
def quantise(frames_rgb):
    keys, pal = {}, {}
    pool = list(KEYS)
    out = []
    for g in frames_rgb:
        rows = []
        for r in g:
            s = []
            for v in r:
                if v is None:
                    s.append(".")
                    continue
                if v not in keys:
                    k = pool.pop(0)
                    keys[v] = k
                    pal[k] = "#%02x%02x%02x" % v
                s.append(keys[v])
            rows.append("".join(s))
        out.append(rows)
    return out, pal


def frame_img(rows, pal, scale=12):
    w, h = len(rows[0]), len(rows)
    img = Image.new("RGB", (w, h), BG)
    px = img.load()
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch != ".":
                px[x, y] = hexc(pal[ch])
    return img.resize((w * scale, h * scale), Image.NEAREST)


def term_img(rows, pal, cell=(8, 16), pad=(2, 1), prompt=True):
    rows = list(rows) + (["." * len(rows[0])] if len(rows) % 2 else [])
    cw, chh = cell
    cols = len(rows[0]) + pad[0] * 2
    lines = len(rows) // 2 + pad[1] * 2 + (1 if prompt else 0)
    img = Image.new("RGB", (cols * cw, lines * chh), BG)
    px = img.load()
    for ty in range(len(rows) // 2):
        for tx in range(len(rows[0])):
            for half in (0, 1):
                k = rows[ty * 2 + half][tx]
                if k == ".":
                    continue
                c = hexc(pal[k])
                ox = (tx + pad[0]) * cw
                oy = (ty + pad[1]) * chh + half * (chh // 2)
                for yy in range(chh // 2):
                    for xx in range(cw):
                        px[ox + xx, oy + yy] = c
    if prompt:
        d = ImageDraw.Draw(img)
        d.fontmode = "1"  # no antialias -> exact palette colours in the GIF
        font = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 14)
        d.text((pad[0] * cw, (lines - 1) * chh + 1), "PS C:\\Users\\grego> _", font=font, fill=(204, 204, 204))
    return img


def _gif(imgs, durations, path):
    # one global palette for every frame: exact colours, no per-frame dithering
    pal_img = Image.new("P", (1, 1))
    cols = []
    for im in imgs:
        for _, c in im.getcolors(1 << 20):
            if c not in cols:
                cols.append(c)
    assert len(cols) <= 256, len(cols)
    flat = [v for c in cols for v in c] + [0] * (768 - 3 * len(cols))
    pal_img.putpalette(flat)
    ps = [im.quantize(palette=pal_img, dither=Image.Dither.NONE) for im in imgs]
    ps[0].save(path, save_all=True, append_images=ps[1:], duration=durations, loop=0,
               optimize=False, disposal=1)


def gif_durations(n, fps):
    """GIF delays are in 1/100 s; spread the rounding so n frames last exactly n/fps."""
    total = round(n * 100 / fps)
    out, acc = [], 0
    for i in range(n):
        nxt = round((i + 1) * total / n)
        out.append((nxt - acc) * 10)
        acc = nxt
    return out


def contact_sheet(frames, pal, path, scale=5, cols=4, label=True):
    w, h = len(frames[0][0]) * scale, len(frames[0]) * scale
    gap = 6
    rows_n = (len(frames) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (w + gap) + gap, rows_n * (h + gap + 12) + gap), (40, 40, 44))
    d = ImageDraw.Draw(sheet)
    for i, fr in enumerate(frames):
        x = gap + (i % cols) * (w + gap)
        y = gap + (i // cols) * (h + gap + 12)
        sheet.paste(frame_img(fr, pal, scale), (x, y + 12))
        if label:
            d.text((x, y), f"f{i:02d}", fill=(220, 220, 220))
    sheet.save(path)


def export(card, name, frames_rgb, fps, final_frame, notes, frame_ms=None):
    out = ANIM / card
    (out / "ans").mkdir(parents=True, exist_ok=True)
    frames, pal = quantise(frames_rgb)
    w, h = len(frames[0][0]), len(frames[0])
    assert w <= 48 and h <= 32, (w, h)
    n = len(frames)
    frame_ms = frame_ms or [round(1000 / fps)] * n
    meta = {"id": card, "name": name, "width": w, "height": h, "fps": fps, "frame_ms": frame_ms,
            "final_frame": final_frame, "notes": notes, "palette": pal, "frames": frames}
    (out / f"{card}.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    for old in (out / "ans").glob("*.ans"):
        old.unlink()
    ans = []
    for i, fr in enumerate(frames):
        a = to_ansi(fr, pal)
        ans.append(a)
        (out / "ans" / f"{card}-{i:02d}.ans").write_text(a, encoding="utf-8", newline="\n")
    # single-file bundle for the player: header line, then frames separated by \f
    hdr = json.dumps({"lines": (h + 1) // 2, "fps": fps, "frames": n, "final": final_frame})
    (out / f"{card}.anim").write_text(hdr + "\n\f" + "\f".join(ans), encoding="utf-8", newline="\n")
    dur = gif_durations(n, fps)
    _gif([frame_img(f, pal, 12) for f in frames], dur, out / f"{card}-x12.gif")
    _gif([term_img(f, pal) for f in frames], dur, out / f"{card}-term.gif")
    contact_sheet(frames, pal, out / f"{card}-sheet.png")
    frame_img(frames[final_frame], pal, 12).save(out / f"{card}-final.png")
    term_img(frames[final_frame], pal).save(out / f"{card}-final-term.png")
    sizes = [len(a.encode("utf-8")) for a in ans]
    print(f"{card}: {n} frames {w}x{h}px, {len(pal)} colours, .ans {min(sizes)}-{max(sizes)} B/frame, "
          f"{sum(sizes)} B total, gif delays {dur}")
    return frames, pal
