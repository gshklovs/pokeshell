r"""Animated Evolving Skies cards, 16 frames at 12 fps in suite3's frame format (play.ps1 plays them). Each
effect imitates what that printed finish does when the card is tilted; the Common is non-foil and has none.

  sunpillar  Rare Holo V   (Sylveon V 74)    a 45-degree rainbow beam sweeps the window AND the silver frame, a
                                             fainter beam crosses the other way (the V "sunpillar" pair), sparkles
  etch       Rare Ultra    (Glaceon V 174)   the fingerprint lines light up in a slow rainbow wave that runs
                                             along the contours (raking light on an etched surface); no beam
  paint      alt art       (Umbreon VMAX 215) the light direction swings across the embossed brushwork so the
                                             paint texture catches and loses the light, the stars twinkle
  rainbow    Rare Rainbow  (Leafeon VMAX 204) the rainbow flows along the diagonal, the etched lines flash as a
                                             sheen crosses, the glitter sparks

Composed at grid resolution from the same Card as the static art; the sprite only gets a light gloss (never its
black outline, never a recolour); the FINAL frame is asserted identical to the static render.

  ..\..\..\.venv\Scripts\python anim.py [swsh7-74 ...]        then:  .\anim\play.ps1 swsh7-215
"""
import importlib.util
import math
import shutil
import sys

import numpy as np

import evcards
import evlib as E
from evlib import L

_spec = importlib.util.spec_from_file_location("s3anim", E.LIB / "s3anim.py")
s3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(s3)
s3.ANIM = E.DATA / "anim"
N = s3.N
W_LUM = evcards.W_LUM


def layers(c):
    """masks: bg (no keyed cell or a static sparkle), sprite body (not outline), outline"""
    FH, FW = c.FH, c.FW
    bg = np.ones((FH, FW), bool)
    body = np.zeros((FH, FW), bool)
    for (x, y), (Lr, k) in c.cells.items():
        if Lr == "deco":
            continue
        bg[y, x] = False
        if Lr in ("sprite", "over") and k != "k":
            body[y, x] = True
    return bg, body


def base_arrays(c, shiny):
    g = c.rgb(shiny)
    a = np.array([[v if v is not None else (0, 0, 0) for v in r] for r in g], float)
    # static sparkles erased back to the bg under them (they twinkle instead)
    for (x, y), (Lr, k) in c.cells.items():
        if Lr == "deco":
            a[y, x] = c.bgq[y, x]
    return g, a


def to_frame(a):
    q = np.clip(np.round(a / 4) * 4, 0, 255).astype(int)       # 4-level steps keep the palette small
    return [[tuple(int(v) for v in q[y, x]) for x in range(q.shape[1])] for y in range(q.shape[0])]


def finish_frame(c, a, f, pts, pal):
    g = to_frame(a)
    s3.twinkle(g, c, pts, f, pal)
    return g


def lerp(a, b, t):
    t = np.asarray(t, float)
    if t.ndim == 2:
        t = t[..., None]
    return a + (np.asarray(b, float) - a) * t


def spark_pts(c, n_free=3, seed=7):
    pts = [(x, y, (i * 4 + 1) % N) for i, (x, y, st) in enumerate(c.meta.get("stars", []))]
    pts += [(x, y, (i * 5 + 3) % N) for i, (x, y) in enumerate(s3.free_spots(c, n_free, seed, gap=14))]
    return pts


# ---- effects -----------------------------------------------------------------------------------
def anim_sunpillar(c, shiny):
    grooves = c.meta.get("grooves")
    g0, a0 = base_arrays(c, shiny)
    bg, body = layers(c)
    FH, FW = c.FH, c.FW
    yy, xx = np.mgrid[0:FH, 0:FW].astype(float)
    d1 = xx + yy                 # main beam runs along x + y = const (45 degrees)
    d2 = xx - yy                 # counter beam
    band = 18
    span = FW + FH + 2 * band
    pts = spark_pts(c)
    frames = []
    for f in range(N):
        if f == N - 1:
            frames.append(g0)
            continue
        t = f / (N - 2)
        ctr1 = -band + t * span
        ctr2 = FW + band - t * (FW + FH + 2 * band) * 0.9
        u1 = (d1 - ctr1) / band
        k1 = np.clip(1 - np.abs(u1 * 2), 0, 1)
        u2 = (d2 - ctr2) / (band * 0.7)
        k2 = np.clip(1 - np.abs(u2 * 2), 0, 1) * 0.45
        hue = evcards.rainbow_rgb(u1 * 0.9 + 0.3 + xx / 160, s=0.6) * 255
        hue2 = evcards.rainbow_rgb(-u2 * 0.9 + 0.7, s=0.5) * 255
        a = a0.copy()
        amt = 0.15 + 0.45 * k1
        a = np.where((bg & (k1 > 0))[..., None], lerp(a, hue, amt * (k1 > 0)), a)
        a = np.where((bg & (k2 > 0))[..., None], lerp(a, hue2, k2), a)
        a = np.where((body & (k1 > 0.55))[..., None], lerp(a, (255, 255, 255), 0.25 * k1), a)
        if grooves is not None:                   # VMAX: the etched contours catch the beam
            a = np.where((grooves & bg & (k1 > 0.2))[..., None], lerp(a, np.clip(hue * 1.15, 0, 255), 0.85 * k1), a)
        frames.append(finish_frame(c, a, f, pts, {"L": "#ffffff", "l": "#ffe6f4", "j": "#b9d7ff"}))
    return frames


def anim_etch(c, shiny):
    g0, a0 = base_arrays(c, shiny)
    bg, body = layers(c)
    FH, FW = c.FH, c.FW
    field = c.meta["etch_field"]
    per = c.meta["etch_period"]
    line = ((field / per) % 1.0) < (1.0 / per)
    idx = np.floor(field / per)                       # contour index: the wave runs outward over the whorls
    lo, hi = idx.min(), idx.max()
    pts = spark_pts(c, 2, 9)
    frames = []
    for f in range(N):
        if f == N - 1:
            frames.append(g0)
            continue
        t = f / (N - 2)
        front = lo - 4 + t * (hi - lo + 8)
        dd = idx - front
        k = np.exp(-(dd / 2.2) ** 2)                   # lines near the front lit, a soft trailing glow
        hue = evcards.rainbow_rgb(idx / 14.0 - t * 0.6, s=0.55) * 255
        a = a0.copy()
        lit = bg & line
        a = np.where(lit[..., None], lerp(a, hue, 0.75 * k), a)
        a = np.where((bg & ~line)[..., None], lerp(a, hue, 0.16 * k), a)
        a = np.where(body[..., None], lerp(a, (255, 255, 255), 0.12 * k), a)
        frames.append(finish_frame(c, a, f, pts, {"L": "#ffffff", "l": "#e6fbff", "j": "#9fe8ff"}))
    return frames


def anim_paint(c, shiny):
    g0, a0 = base_arrays(c, shiny)
    bg, body = layers(c)
    FH, FW = c.FH, c.FW
    h = c.meta["height"]
    gy, gx = np.gradient(h)

    def relief(theta):
        lx, ly = math.cos(theta), math.sin(theta)
        return np.clip(-(gx * lx + gy * ly) * 2.4, -0.3, 0.3)

    r0 = relief(math.atan2(-1.3, -1.0))               # the static emboss (lit from the top-left)
    lumv = a0 @ W_LUM / 255
    yy, xx = np.mgrid[0:FH, 0:FW].astype(float)
    pts = spark_pts(c, 4, 15)
    frames = []
    for f in range(N):
        if f == N - 1:
            frames.append(g0)
            continue
        t = f / (N - 2)
        th = math.atan2(-1.3, -1.0) + math.sin(t * 2 * math.pi) * 1.6   # light swings left -> right -> back
        dr = relief(th) - r0
        a = a0 + (dr * (0.35 + 0.65 * lumv) * 255 * 2.2)[..., None]
        # a broad soft sheen (the light source) drifting diagonally, very gentle
        ctr = -20 + t * (FW + FH + 40)
        k = np.exp(-(((xx + yy) - ctr) / 12.0) ** 2) * 0.2
        a = np.where(bg[..., None], lerp(a, (255, 244, 230), k), a0)
        a = np.where(body[..., None], lerp(a0, (255, 255, 255), k * 0.8), a)
        frames.append(finish_frame(c, a, f, pts, {"L": "#ffffff", "l": "#fff3c4", "j": "#8fd8ff"}))
    return frames


def rainbow_sprite_frame(c, a, shiny, t, k):
    """re-tint every recoloured sprite px with its body hue + the same flowing shift as the background
    (sampled at the px block's top-left grid cell), then the passing sheen; outline / pinned px untouched"""
    spr = c.spr
    A, B = c.off
    src = spr.shiny if shiny else spr.pal
    FW, FH = c.FW, c.FH
    for j, r in enumerate(spr.rows):
        for i, ch in enumerate(r):
            if ch in ".k":
                continue
            X, Y = 2 * (A + i), 2 * (B + j)
            shift = 0.10 * math.sin(2 * math.pi * (t - (X + Y) / (FW + FH)))
            vi = spr.w - 1 - i if spr.flip else i
            hue = evcards.rainbow_hue(i, j, spr.w, spr.h, shift)
            col = np.array(L.hexrgb(evcards.rainbow_px(src[ch], hue, i=vi, j=j, name=spr.name)), float)
            for dx in (0, 1):
                for dy in (0, 1):
                    a[Y + dy, X + dx] = lerp(col, (255, 255, 255), 0.2 * k[Y + dy, X + dx])
    return a


def anim_reverse(c, shiny):
    """reverse holo: only the foil ring moves -- a rainbow hue shift travels around it, its grain glints;
    the art inside (the plain sprite) stays exactly as printed"""
    g0 = c.rgb(shiny)
    FH, FW = c.FH, c.FW
    ring = c.meta["ring"]
    cells = [(int(x), int(y)) for y, x in zip(*np.nonzero(ring))]
    per = 2 * (FW + FH)

    def pos(x, y):
        if y == min(y, x, FH - 1 - y, FW - 1 - x):
            return x
        if FW - 1 - x == min(y, x, FH - 1 - y, FW - 1 - x):
            return FW + y
        if FH - 1 - y == min(y, x, FH - 1 - y, FW - 1 - x):
            return FW + FH + (FW - 1 - x)
        return 2 * FW + FH + (FH - 1 - y)

    rnd = np.random.default_rng(49)
    ph = {p: int(rnd.integers(0, N)) for p in cells if rnd.random() < 0.12}
    frames = []
    for f in range(N):
        if f == N - 1:
            frames.append(g0)
            continue
        t = f / (N - 2)
        g = [r[:] for r in g0]
        for (x, y) in cells:
            base = np.array(g0[y][x], float)
            u = pos(x, y) / per
            band = math.exp(-(((u - t + 0.5) % 1.0 - 0.5) / 0.09) ** 2)         # a bright arc runs round the ring
            hue = evcards.rainbow_rgb(np.array([[u * 2 - t]]), s=0.45)[0, 0] * 255
            col = lerp(base, hue, 0.35 + 0.4 * band)
            col = lerp(col, (255, 255, 255), 0.35 * band)
            if (x, y) in ph:
                s_ = (f - ph[(x, y)]) % N
                if s_ == 0:
                    col = np.array((255, 255, 255), float)
                elif s_ == 1:
                    col = lerp(col, (255, 255, 255), 0.5)
            q = np.clip(np.round(col / 4) * 4, 0, 255).astype(int)
            g[y][x] = tuple(int(v) for v in q)
        frames.append(g)
    return frames


def anim_rainbow(c, shiny):
    from skimage.color import rgb2hsv, hsv2rgb
    g0, a0 = base_arrays(c, shiny)
    bg, body = layers(c)
    FH, FW = c.FH, c.FW
    yy, xx = np.mgrid[0:FH, 0:FW].astype(float)
    line, _ = evcards.rainbow_etch(FW, FH, seed=204)
    hsv0 = rgb2hsv(a0 / 255)
    glint = [(x, y) for x, y in c.meta.get("glint", [])]
    rnd = np.random.default_rng(3)
    gph = rnd.integers(0, N, len(glint))
    pts = spark_pts(c, 3, 21)
    frames = []
    for f in range(N):
        if f == N - 1:
            frames.append(g0)
            continue
        t = f / (N - 2)
        hsv = hsv0.copy()
        hsv[..., 0] = (hsv[..., 0] + 0.10 * np.sin(2 * math.pi * (t - (xx + yy) / (FW + FH)))) % 1.0
        a = hsv2rgb(hsv) * 255
        ctr = -10 + t * (FW + FH + 20)
        dd = (xx + yy) - ctr
        k = np.exp(-(dd / 5.0) ** 2)
        a = np.where((line & bg)[..., None], lerp(a, (255, 255, 255), 0.55 * k), lerp(a, (255, 255, 255), 0.18 * k))
        a = np.where(bg[..., None], a, a0)
        a = np.where(body[..., None], lerp(a0, (255, 255, 255), 0.2 * k), a)
        if c.meta.get("sprite_recolour") == "rainbow":         # the sprite's rainbow flows with the ground's
            a = rainbow_sprite_frame(c, a, shiny, t, k)
        for (x, y), ph in zip(glint, gph):
            s = (f - ph) % N
            if s == 0:
                a[y, x] = (255, 255, 255)
            elif s in (1, 2):
                a[y, x] = lerp(a0[y, x], (255, 255, 255), 0.5)
            elif s in (6, 7):
                a[y, x] = a0[y, x] * 0.7
        frames.append(finish_frame(c, a, f, pts, {"L": "#ffffff", "l": "#fff0fa", "j": "#b8f0ff"}))
    return frames


KINDS = {"sunpillar": anim_sunpillar, "etch": anim_etch, "paint": anim_paint, "rainbow": anim_rainbow,
         "reverse": anim_reverse, "holo": lambda c, sh: s3.anim_holo(c, sh), "gold": lambda c, sh: s3.anim_gold(c, sh)}
NOTES = {"sunpillar": "Rare Holo V: 45-degree rainbow beam sweeps window + silver frame, fainter counter-beam, sparkles",
         "etch": "Rare Ultra full art: fingerprint etch lines light up in a rainbow wave along the contours, no beam",
         "paint": "alt art: light swings across the embossed brushwork (texture catches the light), soft sheen, stars",
         "rainbow": "Rare Rainbow: rainbow flows along the diagonal AND over the rainbow sprite, etched lines flash, glitter",
         "reverse": "Reverse Holo: only the foil ring moves -- a bright rainbow arc runs round it, grain glints; art untouched",
         "holo": "Rare Holo: a wide rainbow foil band sweeps the art box, starlight specks glitter, sparkles twinkle",
         "gold": "Rare Secret gold: 45-degree metallic sheen over the faceted gold, glitter, star flares"}


def build(ids):
    s3.ANIM.mkdir(exist_ok=True)
    shutil.copy(E.LIB / "play.ps1", s3.ANIM / "play.ps1")
    sizes = {}
    for cid in ids:
        c = evcards.BUILDERS[cid]()
        kind = c.meta.get("anim")
        if not kind:
            print(f"{cid}: {c.meta['rarity']} is non-foil, no animation")
            continue
        for shiny in (False, True):
            frames = KINDS[kind](c, shiny)
            assert len(frames) == N
            assert frames[N - 1] == c.rgb(shiny), f"{cid}: final frame differs from the static render"
            name = cid + ("_shiny" if shiny else "")
            sizes[name] = s3.export(name, f"{c.meta['label']}" + (" (shiny)" if shiny else ""), frames, N - 1,
                                    NOTES[kind])
    return sizes


if __name__ == "__main__":
    build([a for a in sys.argv[1:] if a in evcards.BUILDERS] or evcards.ORDER)
