"""Animated tiers for suite3 (holo / full art / gold-top), in anim_lib's frame format (play.ps1).

Frames are composed at GRID resolution (1 px = 1 col x half a line, the same grid as the static art)
from the same Card as the static render, effects painted on top. The sprite only ever gets a light
sheen (blended toward white, never over its black outline); the FINAL frame (the one play.ps1 rests
on) is asserted identical to the static render.

  ..\\..\\.venv\\Scripts\\python anim.py [pokemon ...]      then:  .\\anim\\play.ps1 holo_pikachu
"""
import json
import math
import random
import shutil
import sys

import numpy as np
from PIL import Image

import s3lib as L
import tiers

sys.path.insert(0, str(L.LIB))
import anim_lib as al  # noqa: E402

ANIM = L.HERE / "anim"
N, FPS = 16, 12
WHITE = (255, 255, 255)


def rainbow(t):
    """continuous foil rainbow, t in 0..1 -> rgb (pastel-bright)"""
    from colorsys import hsv_to_rgb
    r, g, b = hsv_to_rgb(t % 1, 0.55, 1.0)
    return (r * 255, g * 255, b * 255)


def mix(a, b, t):
    return tuple(int(min(255, max(0, round((a[i] + (b[i] - a[i]) * t) / 4) * 4))) for i in range(3))


# ---- export ------------------------------------------------------------------------------------
def quantise(frames_rgb):
    pool = iter([c for c in al.KEYS if c not in "\\\"."] + [c for c in L.KEY_POOL if c not in al.KEYS])
    keys, pal, out = {}, {}, []
    for g in frames_rgb:
        rows = []
        for r in g:
            s = []
            for v in r:
                if v is None:
                    s.append(".")
                    continue
                if v not in keys:
                    keys[v] = next(pool)
                    pal[keys[v]] = "#%02x%02x%02x" % v
                s.append(keys[v])
            rows.append("".join(s))
        out.append(rows)
    return out, pal


def gif(imgs, durations, path):
    strip = Image.new("RGB", (imgs[0].width, imgs[0].height * len(imgs)))
    for i, im in enumerate(imgs):
        strip.paste(im, (0, i * im.height))
    cols = strip.getcolors(1 << 20)
    if len(cols) <= 256:
        pal_img = Image.new("P", (1, 1))
        flat = [v for _, c in cols for v in c]
        pal_img.putpalette(flat + [0] * (768 - len(flat)))
    else:                                  # one shared median-cut palette for all frames
        pal_img = strip.quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    ps = [im.quantize(palette=pal_img, dither=Image.Dither.NONE) for im in imgs]
    ps[0].save(path, save_all=True, append_images=ps[1:], duration=durations, loop=0, optimize=False, disposal=1)


def export(card, name, frames_rgb, final, notes):
    out = ANIM / card
    (out / "ans").mkdir(parents=True, exist_ok=True)
    frames, pal = quantise(frames_rgb)
    w, h = len(frames[0][0]), len(frames[0])
    n = len(frames)
    meta = {"id": card, "name": name, "width": w, "height": h, "fps": FPS, "frame_ms": [round(1000 / FPS)] * n,
            "final_frame": final, "notes": notes, "palette": pal, "frames": frames}
    (out / f"{card}.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
    for old in (out / "ans").glob("*.ans"):
        old.unlink()
    ans = []
    for i, fr in enumerate(frames):
        a = al.to_ansi(fr, pal)
        ans.append(a)
        (out / "ans" / f"{card}-{i:02d}.ans").write_text(a, encoding="utf-8", newline="\n")
    hdr = json.dumps({"lines": (h + 1) // 2, "fps": FPS, "frames": n, "final": final})
    bundle = hdr + "\n\f" + "\f".join(ans)
    (out / f"{card}.anim").write_text(bundle, encoding="utf-8", newline="\n")
    dur = al.gif_durations(n, FPS)
    gif([al.term_img(f, pal) for f in frames], dur, out / f"{card}-term.gif")
    al.contact_sheet(frames, pal, out / f"{card}-sheet.png", scale=4)
    al.term_img(frames[final], pal).save(out / f"{card}-final-term.png")
    size = len(bundle.encode("utf-8"))
    print(f"{card}: {n} frames, {w} cols x {h // 2} lines, {len(pal)} colours, .anim {size // 1024} KB")
    return size


# ---- helpers -----------------------------------------------------------------------------------
def is_outline(c, x, y):
    t = c.cells.get((x, y))
    return t is not None and t[1] == "k" and t[0] in ("sprite", "over", "deco")


def on_char(c, x, y):
    return c.cells.get((x, y), ("bg",))[0] in ("sprite", "over")


def on_bg(c, x, y):
    return 0 <= x < c.FW and 0 <= y < c.FH and (x, y) not in c.cells


def free_spots(c, n, seed, gap=10, avoid=4):
    rnd = random.Random(seed)
    d = c.dist()
    pts, tries = [], 0
    while len(pts) < n and tries < 5000:
        tries += 1
        x, y = rnd.randrange(2, c.FW - 2), rnd.randrange(2, c.FH - 2)
        if d[y, x] < avoid or (x, y) in c.cells or any(abs(x - p[0]) + abs(y - p[1]) < gap for p in pts):
            continue
        pts.append((x, y))
    return pts


def erase_sparkles(g, c):
    """non-final frames: the static sparkles go back to the foil under them, so they can twinkle"""
    for (x, y), (Lr, k) in c.cells.items():
        if Lr == "deco" and k in "Llj":
            g[y][x] = tuple(int(v) for v in c.bgq[y, x])


def sparkle_centres(c):
    """centres of the static sparkles (their 'L' core cells)"""
    return sorted((x, y) for (x, y), (Lr, k) in c.cells.items() if Lr == "deco" and k == "L")


def twinkle(g, c, pts, f, pal, big_every=2):
    """pts: [(x, y, phase)]; sparkles grow 1-2-3-2-1 staggered over the loop, on background only"""
    for i, (x, y, ph) in enumerate(pts):
        k = (f - ph) % N
        seq = [1, 2, 3, 2, 1] if i % big_every == 0 else [1, 2, 1]
        st = seq[k] if k < len(seq) else 0
        al.star(g, x, y, st, L.hexrgb(pal["L"]), L.hexrgb(pal["l"]), L.hexrgb(pal["j"]),
                allow=lambda X, Y: 0 <= X < c.FW and 0 <= Y < c.FH and (
                    (X, Y) not in c.cells or (c.cells[(X, Y)][0] == "deco" and c.cells[(X, Y)][1] in "Llj")))


def sheen_pass(g, c, ctr, fn, sprite_k=0.55):
    """for every non-outline px, d = (x + y) - ctr; fn(d, x, y, colour, on_sprite) -> new colour or None"""
    for y in range(c.FH):
        for x in range(c.FW):
            if g[y][x] is None or is_outline(c, x, y):
                continue
            v = fn((x + y) - ctr, x, y, g[y][x], on_char(c, x, y))
            if v is not None:
                g[y][x] = v


# ---- effects -----------------------------------------------------------------------------------
def anim_holo(c, shiny):
    """a wide rainbow foil band sweeps once per loop (continuous hue across it, brightest in its core),
    the baked starlight specks glitter in waves, sparkles twinkle, the sprite gets a light gloss"""
    g0 = c.rgb(shiny)
    W, H = c.FW, c.FH
    band = 22
    period = W + H + band
    rnd = random.Random(4)
    specks = [(x, y) for y in range(H) for x in range(W) if (x, y) not in c.cells
              and g0[y][x] in ((255, 252, 237), (204, 230, 255))]
    phase = {p: rnd.randrange(N) for p in specks}
    pts = [(x, y, (i * 3) % N) for i, (x, y, st) in enumerate(c.meta.get("stars", []))]
    pts += [(x, y, (i * 5 + 2) % N) for i, (x, y) in enumerate(free_spots(c, 4, 7))]
    frames = []
    for f in range(N):
        g = [r[:] for r in g0]
        if f < N - 1:
            ctr = -band + f * period / (N - 2)

            def fx(d, x, y, col, spr):
                if not (0 <= d < band):
                    return None
                u = d / band
                core = 1 - abs(u - 0.5) * 2
                if spr:
                    return mix(col, WHITE, 0.28 * core ** 2) if core > 0.5 else None
                return mix(col, rainbow(u * 1.2 + (x - y) / 90), 0.18 + 0.4 * core)
            sheen_pass(g, c, ctr, fx)
            for (x, y) in specks:
                k = (f + phase[(x, y)]) % 6
                if k == 0:
                    g[y][x] = WHITE
                elif k == 3:
                    g[y][x] = mix(g0[y][x], (40, 40, 60), 0.4)
            erase_sparkles(g, c)
            twinkle(g, c, pts, f, tiers.VAULT_SPARK if c.meta["card"] == "sma-SV6" else tiers.SPARK_PAL)
        frames.append(g)
    return frames


def anim_glint(c, shiny):
    """full art: the light rays behind the sprite slowly turn and pulse, a narrow white glint (1px hot
    core, soft 4px falloff) crosses the painting, then sparkles ping where it passed"""
    g0 = c.rgb(shiny)
    W, H = c.FW, c.FH
    cx, cy = L.fig_centre(c)
    yy, xx = np.mgrid[0:H, 0:W]
    th = np.arctan2(yy - cy, xx - cx)
    r = np.hypot(xx - cx, yy - cy)
    fall = np.clip(1 - r / (max(W, H) * 0.75), 0, 1)
    pts = [(x, y, (i * 4 + 3) % N) for i, (x, y, st) in enumerate(c.meta.get("stars", []))]
    sweep = 11
    lo, hi = -8, W + H + 8
    frames = []
    for f in range(N):
        g = [r_[:] for r_ in g0]
        if f < N - 1:
            ang = f / (N - 1) * 2 * math.pi / 12
            ray = (0.5 + 0.5 * np.cos(12 * (th - ang))) ** 6 * fall * 0.22
            for y in range(H):
                for x in range(W):
                    if (x, y) not in c.cells and ray[y, x] > 0.02:
                        g[y][x] = mix(g[y][x], (255, 246, 214), ray[y, x])
            if f < sweep:
                ctr = lo + (hi - lo) * f / (sweep - 1)

                def fx(d, x, y, col, spr):
                    k = 0.55 if spr else 1.0
                    ad = abs(d)
                    if ad < 1:
                        return mix(col, WHITE, 0.75 * k)
                    if ad < 2.5:
                        return mix(col, WHITE, 0.4 * k)
                    if ad < 5:
                        return mix(col, WHITE, 0.14 * k)
                    return None
                sheen_pass(g, c, ctr, fx)
            erase_sparkles(g, c)
            twinkle(g, c, pts, f, {"L": "#ffffff", "l": "#fff6d0", "j": "#ffd98a"})
        frames.append(g)
    return frames


def anim_gold(c, shiny):
    """a 45-degree metallic sheen sweeps the fine foil (hot 2px core, stepped falloff, a trailing echo),
    engraved lines catch the light as it passes, glints and sparkles twinkle, crown gems flash"""
    g0 = c.rgb(shiny)
    W, H = c.FW, c.FH
    hi_c = L.hexrgb("#fffbea")
    rnd = random.Random(5)
    bgc = [(x, y) for y in range(H) for x in range(W) if (x, y) not in c.cells]
    glitter = [(*rnd.choice(bgc), rnd.randrange(N)) for _ in range(40)]
    pts = [(x, y, (i * 4) % N) for i, (x, y) in enumerate(free_spots(c, 3, 11, gap=14))]
    pts += [(x, y, (i * 5 + 2) % N) for i, (x, y) in enumerate(sparkle_centres(c))]
    span = W + H + 20
    frames = []
    for f in range(N):
        g = [r[:] for r in g0]
        if f < N - 1:
            ctr = -10 + f * span / (N - 2)

            def fx(d, x, y, col, spr):
                ad = abs(d)
                if ad <= 1:
                    s = 0.7
                elif ad <= 3:
                    s = 0.42
                elif ad <= 6:
                    s = 0.2 if (x % 2 == 0 or ad <= 4) else 0.1
                elif -16 <= d <= -13:
                    s = 0.22
                else:
                    return None
                return mix(col, hi_c, s * (0.55 if spr else 1.0))
            sheen_pass(g, c, ctr, fx)
            for x, y, ph in glitter:
                k = (f - ph) % N
                if k == 0:
                    g[y][x] = WHITE
                elif k == 1:
                    g[y][x] = L.hexrgb("#fde79c")
            erase_sparkles(g, c)
            twinkle(g, c, pts, f, tiers.GOLD_SPARK)
        frames.append(g)
    return frames


def anim_confetti(c, shiny):
    """Dragon 98: every confetti fleck cycles through the foil colours at its own phase, flashing white,
    a soft sheen sweeps across, the rays turn, sparkles twinkle"""
    g0 = c.rgb(shiny)
    W, H = c.FW, c.FH
    cols = [L.hexrgb(v) for v in tiers.CONFETTI]
    conf = c.meta["confetti"]
    rnd = random.Random(3)
    phase = [rnd.randrange(N) for _ in conf]
    pts = [(x, y, (i * 4) % N) for i, (x, y) in enumerate(free_spots(c, 2, 12, gap=14))]
    pts += [(x, y, (i * 5 + 2) % N) for i, (x, y) in enumerate(sparkle_centres(c))]
    frames = []
    for f in range(N):
        g = [r[:] for r in g0]
        if f < N - 1:
            for (x, y, k), ph in zip(conf, phase):
                t = (f + ph) % N
                if t == 0:
                    g[y][x] = WHITE
                elif t < 6:
                    g[y][x] = cols[(k + t) % len(cols)]
                elif t in (9, 10):
                    g[y][x] = mix(g[y][x], (12, 12, 12), 0.55)
            ctr = -6 + f * (W + H + 12) / (N - 2)

            def fx(d, x, y, col, spr):
                ad = abs(d)
                if ad < 2:
                    return mix(col, WHITE, 0.4 * (0.6 if spr else 1.0))
                if ad < 5 and (x + y) % 2:
                    return mix(col, WHITE, 0.14)
                return None
            sheen_pass(g, c, ctr, fx)
            erase_sparkles(g, c)
            twinkle(g, c, pts, f, {"L": "#ffffff", "l": "#e9f6ff", "j": "#6fe3d2"})
        frames.append(g)
    return frames


KINDS = {"holo": anim_holo, "glint": anim_glint, "gold": anim_gold, "confetti": anim_confetti}
NOTES = {"holo": "wide rainbow foil band sweeps once, starlight specks glitter, sparkles twinkle, sprite gloss",
         "glint": "light rays turn + pulse behind the sprite, white glint crosses in 11 frames, sparkles ping",
         "gold": "45-degree metallic sheen with stepped falloff + echo over the fine gold foil, glitter, twinkles",
         "confetti": "confetti flecks cycle the foil colours, soft sheen, sparkles twinkle"}
TIER_NAME = {"holo": "holo", "fullart": "fullart", "gold": "gold", "top": "top"}


def build(pokes):
    ANIM.mkdir(exist_ok=True)
    shutil.copy(L.LIB / "play.ps1", ANIM / "play.ps1")
    sizes = {}
    for p in pokes:
        for t, fn in tiers.TIERS[p].items():
            if t not in TIER_NAME:
                continue
            c = fn()
            kind = c.meta.get("anim")
            if not kind:
                continue
            for shiny in (False, True):
                frames = KINDS[kind](c, shiny)
                final = N - 1
                assert frames[final] == c.rgb(shiny), f"{p}/{t}: final frame differs from the static render"
                card = f"{TIER_NAME[t]}_{p}" + ("_shiny" if shiny else "")
                sizes[card] = export(card, f"{p} {t} ({c.meta['card']})" + (" shiny" if shiny else ""), frames, final,
                                     NOTES[kind])
    return sizes


if __name__ == "__main__":
    build([a for a in sys.argv[1:] if a in tiers.TIERS] or list(tiers.TIERS))
