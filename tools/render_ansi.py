"""Render truecolor ANSI (as pokeshell prints it) to a PNG at terminal proportions (8x16 px cells, x2).

Box drawing (light / heavy / double, arcs, dashes, diagonals), block elements, quadrants, shades and braille
are drawn as geometry the way Windows Terminal's builtin glyphs are; everything else uses Cascadia Mono,
falling back to Segoe UI Symbol (as WT does).

  python tools/render_ansi.py in.ans out.png

Used by tools/make_media.py for the README images. Needs Pillow; fontTools is optional (without it every
other character is drawn with Cascadia Mono).
"""
import re
import sys
import unicodedata
from PIL import Image, ImageDraw, ImageFont

BG = (12, 12, 12)
FG = (204, 204, 204)
TOKEN = re.compile(r"\x1b\[([0-9;]*)m|\x1b\][^\x1b\x07]*(?:\x1b\\|\x07)|(.)", re.S)
CASCADIA = "C:/Windows/Fonts/CascadiaMono.ttf"
SYMBOL = "C:/Windows/Fonts/seguisym.ttf"
try:
    from fontTools.ttLib import TTFont
    _cmap = TTFont(CASCADIA).getBestCmap()
except Exception:
    _cmap = None


def cells(text):
    rows, fg, bg, bold = [[]], None, None, False
    for m in TOKEN.finditer(text.replace("\r\n", "\n")):
        if m.group(0).startswith("\x1b]"):
            continue
        if m.group(2) is None:
            p = [int(x) if x else 0 for x in (m.group(1) or "0").split(";")]
            i = 0
            while i < len(p):
                if p[i] == 0: fg = bg = None; bold = False; i += 1
                elif p[i] == 1: bold = True; i += 1
                elif p[i] == 22: bold = False; i += 1
                elif p[i] == 39: fg = None; i += 1
                elif p[i] == 49: bg = None; i += 1
                elif p[i] in (38, 48) and i + 4 < len(p) and p[i + 1] == 2:
                    if p[i] == 38: fg = tuple(p[i + 2:i + 5])
                    else: bg = tuple(p[i + 2:i + 5])
                    i += 5
                else: i += 1
            continue
        ch = m.group(2)
        if ch == "\n": rows.append([]); continue
        rows[-1].append((ch, fg, bg, bold))
    while rows and not rows[-1]: rows.pop()
    while rows and not rows[0]: rows.pop(0)
    return rows


# ---- box drawing table from the Unicode names: char -> {dir: weight}, weight 1 light, 2 heavy, 3 double
DIRS = {"UP": "u", "DOWN": "d", "LEFT": "l", "RIGHT": "r", "VERTICAL": "ud", "HORIZONTAL": "lr"}
WEIGHTS = {"LIGHT": 1, "SINGLE": 1, "HEAVY": 2, "DOUBLE": 3}


def _box(c):
    try: n = unicodedata.name(c)
    except ValueError: return None
    if not n.startswith("BOX DRAWINGS ") or any(k in n for k in ("DASH", "ARC", "DIAGONAL")): return None
    words = n[len("BOX DRAWINGS "):].replace(" AND ", " ").split()
    arms, before = {}, words[0] in WEIGHTS
    cur, pending = 1, []
    for w in words:
        if w in WEIGHTS:
            if before: cur = WEIGHTS[w]
            else:
                for d in pending: arms[d] = WEIGHTS[w]
                pending = []
        elif w in DIRS:
            for d in DIRS[w]:
                if before: arms[d] = cur
                else: pending.append(d)
    for d in pending: arms[d] = cur
    return arms


BOX = {}
for cp in range(0x2500, 0x2580):
    a = _box(chr(cp))
    if a: BOX[chr(cp)] = a

DASH = {"\u2504": (1, 3, "h"), "\u2505": (2, 3, "h"), "\u2508": (1, 4, "h"), "\u2509": (2, 4, "h"),
        "\u254c": (1, 2, "h"), "\u254d": (2, 2, "h"), "\u2506": (1, 3, "v"), "\u2507": (2, 3, "v"),
        "\u250a": (1, 4, "v"), "\u250b": (2, 4, "v"), "\u254e": (1, 2, "v"), "\u254f": (2, 2, "v")}
QUAD = {"\u2596": "3", "\u2597": "4", "\u2598": "1", "\u259d": "2", "\u2599": "134", "\u259b": "123",
        "\u259c": "124", "\u259f": "234", "\u259a": "14", "\u259e": "23"}


def blend(a, b, t):
    return tuple(int(a[k] + (b[k] - a[k]) * t) for k in range(3))


def draw_cell(d, img, c, X, Y, cw, ch, fg, bg, fonts):
    t = max(2, cw // 8)            # light stroke
    mx, my = X + cw // 2, Y + ch // 2
    R = lambda x0, y0, x1, y1, col=fg: d.rectangle([x0, y0, x1 - 1, y1 - 1], fill=col)
    if c in BOX:
        arms = BOX[c]
        h = t // 2
        ext = {"u": (Y, None), "d": (None, Y + ch), "l": (X, None), "r": (None, X + cw)}
        def band(dr, half):
            if dr == "u": R(mx - half, Y, mx - half + 2 * half, my + half)
            if dr == "d": R(mx - half, my - half, mx - half + 2 * half, Y + ch)
            if dr == "l": R(X, my - half, mx + half, my - half + 2 * half)
            if dr == "r": R(mx - half, my - half, X + cw, my - half + 2 * half)
        def gap(dr, half):
            if dr == "u": R(mx - half, Y, mx + half, my + half, bg)
            if dr == "d": R(mx - half, my - half, mx + half, Y + ch, bg)
            if dr == "l": R(X, my - half, mx + half, my + half, bg)
            if dr == "r": R(mx - half, my - half, X + cw, my + half, bg)
        for dr, w in arms.items():
            if w == 3: band(dr, int(1.5 * t + 0.5))
        for dr, w in arms.items():
            if w == 3: gap(dr, h if t % 2 == 0 else h + 1)
        for dr, w in arms.items():
            if w == 1: band(dr, (t + 1) // 2)
            if w == 2: band(dr, t)
        return
    if c in DASH:
        w, n, o = DASH[c]; half = (t + 1) // 2 if w == 1 else t
        L = cw if o == "h" else ch
        for k in range(n):
            a0 = int(L * k / n) + 1; a1 = int(L * (k + 0.6) / n) + 1
            if o == "h": R(X + a0, my - half, X + a1, my + half)
            else: R(mx - half, Y + a0, mx + half, Y + a1)
        return
    if c in "\u256d\u256e\u2570\u256f":
        r = cw // 2
        cy = my + r if c in "\u256d\u256e" else my - r
        cx = mx + r if c in "\u256d\u2570" else mx - r
        a0 = {"\u256d": 180, "\u256e": 270, "\u2570": 90, "\u256f": 0}[c]
        d.arc([cx - r, cy - r, cx + r, cy + r], a0, a0 + 90, fill=fg, width=t)
        if c in "\u256d\u256e": R(mx - t // 2, cy, mx - t // 2 + t, Y + ch)
        else: R(mx - t // 2, Y, mx - t // 2 + t, cy)
        return
    if c in "\u2571\u2572\u2573":
        if c in "\u2571\u2573": d.line([X, Y + ch, X + cw, Y], fill=fg, width=t)
        if c in "\u2572\u2573": d.line([X, Y, X + cw, Y + ch], fill=fg, width=t)
        return
    if c == "\u2588": R(X, Y, X + cw, Y + ch); return
    if c == "\u2580": R(X, Y, X + cw, Y + ch // 2); return
    if "\u2581" <= c <= "\u2587":
        k = ord(c) - 0x2580; R(X, Y + ch - ch * k // 8, X + cw, Y + ch); return
    if c == "\u2594": R(X, Y, X + cw, Y + ch // 8); return
    if "\u2589" <= c <= "\u258f":
        k = 0x2590 - ord(c); R(X, Y, X + cw * k // 8, Y + ch); return
    if c == "\u2590": R(X + cw // 2, Y, X + cw, Y + ch); return
    if c == "\u2595": R(X + cw - cw // 8, Y, X + cw, Y + ch); return
    if c in "\u2591\u2592\u2593":
        k = {"\u2591": .25, "\u2592": .5, "\u2593": .75}[c]; R(X, Y, X + cw, Y + ch, blend(bg, fg, k)); return
    if c in QUAD:
        for q in QUAD[c]:
            qx = X if q in "13" else mx; qy = Y if q in "12" else my
            R(qx, qy, qx + cw // 2, qy + ch // 2)
        return
    if "\u2800" <= c <= "\u28ff":
        bits = ord(c) - 0x2800
        pos = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (0, 3), (1, 3)]
        rr = max(2, cw // 6)
        for b, (px, py) in enumerate(pos):
            if bits >> b & 1:
                cx = X + cw * (1 + 2 * px) // 4; cy = Y + ch * (1 + 2 * py) // 8
                d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=fg)
        return
    if c == " ": return
    font, bfont, sym = fonts
    if _cmap is None or ord(c) in _cmap:
        d.text((X, Y + ch * 0.08), c, font=bfont if bold_flag[0] else font, fill=fg)
    else:
        bb = d.textbbox((0, 0), c, font=sym)
        gx = X + (cw - (bb[2] - bb[0])) / 2 - bb[0]
        d.text((gx, Y + ch * 0.13), c, font=sym, fill=fg)


bold_flag = [False]


def render(text, out=None, cw=8, ch=16, scale=2, pad=2):
    rows = cells(text)
    w = max(len(r) for r in rows) + 2 * pad
    h = len(rows) + 2 * pad
    cw, ch = cw * scale, ch * scale
    img = Image.new("RGB", (w * cw, h * ch), BG)
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(CASCADIA, int(ch * 0.74))
    try:
        bfont = ImageFont.truetype(CASCADIA, int(ch * 0.74))
        bfont.set_variation_by_name("Bold")
    except Exception:
        bfont = font
    sym = ImageFont.truetype(SYMBOL, int(ch * 0.7))
    for y, row in enumerate(rows):
        for x, (c, fg, bg, bold) in enumerate(row):
            X, Y = (x + pad) * cw, (y + pad) * ch
            fgc, bgc = fg or FG, bg or BG
            if bg: d.rectangle([X, Y, X + cw - 1, Y + ch - 1], fill=bg)
            bold_flag[0] = bold
            draw_cell(d, img, c, X, Y, cw, ch, fgc, bgc, (font, bfont, sym))
    if out: img.save(out)
    return img


if __name__ == "__main__":
    render(open(sys.argv[1], encoding="utf-8").read(), sys.argv[2])
