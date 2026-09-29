"""Rarity effects for pokeshell's terminal card art: one engine per FAMILY, one parameter set (RECIPE) per
rarity. Works on the half-block art grid (1 grid px = 1 col x half a line; the colorscripts sprite is
2x2 grid px per sprite px) and never edits the sprite: every effect paints the BACKGROUND (scene, foil,
frame, rarity symbol); the sprite, with its black outline, is composited on top unchanged. Animations
may put a light gloss on the sprite's non-outline pixels only.

    import effects
    res = effects.apply("hyper_rare", scene, sprite, off)     # scene: float (FH, FW, 3) grid-scale card scene
    res.frames      # 16 frames, each (FH, FW, 3) uint8; frames[-1] is the static render
    res.static      # == frames[-1]
    res.rows()      # frames as [[(r, g, b), ...], ...] rows (suite3 / anim.py frame format)

`sprite` is an s3lib.Sprite, `off` its offset in sprite px (A, B). Shiny families (shiny, radiant, gold
star, shining) switch to the colorscripts SHINY palette, as the real cards print the shiny Pokemon.
Recipes live in RECIPES (id -> dict with 'fam' + knobs); rarities.json maps every real rarity to one.
"""
import math
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from scipy import ndimage

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "lib"))
import s3lib as L  # noqa: E402

N, FPS = 16, 12
W3 = np.array([0.2126, 0.7152, 0.0722])
WHITE = np.array([1.0, 1.0, 1.0])


# =============================================================== colour helpers
def lumf(a):
    return np.asarray(a) @ W3


def hsv(h, s, v):
    """vectorised HSV -> RGB (h wraps), arrays broadcast; -> (..., 3)"""
    h, s, v = np.broadcast_arrays(np.asarray(h, float) % 1.0, np.asarray(s, float), np.asarray(v, float))
    i = np.floor(h * 6).astype(int) % 6
    f = h * 6 - np.floor(h * 6)
    p, q, t = v * (1 - s), v * (1 - f * s), v * (1 - (1 - f) * s)
    r = np.choose(i, [v, q, p, p, t, v])
    g = np.choose(i, [t, v, v, q, p, p])
    b = np.choose(i, [p, p, t, v, v, q])
    return np.stack([r, g, b], -1)


def bow(h, s=0.55, v=1.0):
    """foil rainbow"""
    return hsv(h, s, v)


def mixc(a, b, t):
    t = np.asarray(t, float)
    if t.ndim == a.ndim - 1:
        t = t[..., None]
    return a + (np.asarray(b, float) - a) * t


def tint(base, col, amt, lift=0.04, gain=1.08):
    """'colour' blend: re-tint base toward col at base's own luminance (+ slight lift) by amt"""
    lb = lumf(base)[..., None]
    lc = np.maximum(lumf(col)[..., None], 0.05)
    t = np.clip(col / lc * lb * gain + lift, 0, 1)
    return mixc(base, t, amt)


def add(base, col, amt):
    amt = np.asarray(amt, float)
    if amt.ndim == base.ndim - 1:
        amt = amt[..., None]
    return np.clip(base + np.asarray(col, float) * amt, 0, 1)


def gauss(d, w):
    return np.exp(-(np.asarray(d, float) / w) ** 2)


AMBER = ["#26100a", "#45200c", "#6a3412", "#94501c", "#bd6f28", "#e08f3a", "#f6b458", "#ffd996", "#fff4e4"]
GOLD = ["#1c0f03", "#3a2308", "#5c3a0e", "#83591a", "#ab7c28", "#d0a23c", "#ecc75e", "#fbe496", "#fffbea"]
ROSE_GOLD = ["#26120e", "#45241a", "#6a3a26", "#945636", "#bd7a4a", "#e0a066", "#f2c48a", "#ffe2bc", "#fff6ec"]
SILVER = ["#5d646c", "#7b838c", "#9aa3ac", "#bcc4cc", "#dde3e8", "#f3f6f8"]      # evs
PLATINUM = ["#101216", "#23272e", "#3a4049", "#555d68", "#737c88", "#949daa", "#b8c0cb", "#dde2ea", "#f8faff"]


def ramp_arr(stops, n=32):
    return np.array([L.hexrgb(h) for h in L.gold_ramp(stops, n)], float) / 255


def ramp_map(level, stops, n=32):
    r = ramp_arr(stops, n)
    return r[np.clip(np.round(np.asarray(level) * (n - 1)), 0, n - 1).astype(int)]


# =============================================================== context
class Ctx:
    """one card: scene + sprite + all the geometry the families share"""

    def __init__(self, scene, spr, off):
        scene = np.asarray(scene, float)
        self.FH, self.FW = scene.shape[:2]
        assert self.FH % 2 == 0 and self.FW % 2 == 0, "grid scene must have even dims"
        self.scene = np.clip(scene, 0, 1)
        self.spr, self.off = spr, off
        c = L.Card(self.FW // 2, self.FH // 2)
        c.put_sprite(spr, *off)
        self.card = c
        self.fig = c.fig_mask()
        self.outl = c.outline_mask()
        self.dist = c.dist()
        self.spr_rgb = {}
        for sh in (False, True):
            a = np.zeros((self.FH, self.FW, 3))
            for (x, y), (Lr, k) in c.cells.items():
                a[y, x] = np.array(L.hexrgb((spr.shiny if sh else spr.pal)[k])) / 255
            self.spr_rgb[sh] = a
        self.yy, self.xx = np.mgrid[0:self.FH, 0:self.FW].astype(float)
        self.cx, self.cy = L.fig_centre(c)
        self.r = np.hypot(self.xx - self.cx, self.yy - self.cy)
        self.th = np.arctan2(self.yy - self.cy, self.xx - self.cx)
        self.diag = self.xx + self.yy
        self.span = self.FW + self.FH
        self._cache = {}

    def ring(self, t):
        m = np.zeros((self.FH, self.FW), bool)
        if t:
            m[:t], m[-t:], m[:, :t], m[:, -t:] = True, True, True, True
        return m

    def edge_dist(self):
        return np.minimum(np.minimum(self.xx, self.FW - 1 - self.xx), np.minimum(self.yy, self.FH - 1 - self.yy))

    # ---- scene at a quality level
    def scene_q(self, kind="grid", n=16, sat=1.0, bright=1.0, gamma=1.0, halo=True):
        key = (kind, n, sat, bright, gamma, halo)
        if key in self._cache:
            return self._cache[key].copy()
        a = L.tone(self.scene, sat=sat, bright=bright, gamma=gamma)
        if halo:
            a = L.focus_halo(self.card, a, radius=4, dark=0.82, soft=1.0)
        if kind == "chunky":                    # sprite-scale blocks, few colours (the common look)
            s = a.reshape(self.FH // 2, 2, self.FW // 2, 2, 3).mean((1, 3))
            q, lbl, pal = L.kmeans_q(s, n)
            lbl = L.orphan_clean(lbl, 1)
            q = np.repeat(np.repeat(pal[lbl], 2, 0), 2, 1)
        elif kind == "grid":
            q, lbl, pal = L.kmeans_q(a, n, ignore=self.fig)
            q = pal[L.orphan_clean(lbl, 1)]
        else:                                   # 'true': near-truecolour painting
            q = L.median_q(a, n)
        self._cache[key] = q
        return q.copy()

    def painting(self, sat=1.12, glow=(1.0, 0.95, 0.75), glow_s=0.35, rays=12, ray_amt=0.5, vig=0.5, n=160, gamma=1.0,
                 bright=1.0):
        """the SIR / full-art painting: near truecolour, focus halo, glow + rays, vignette"""
        key = ("paint", sat, glow, glow_s, rays, ray_amt, vig, n, gamma, bright)
        if key in self._cache:
            return self._cache[key].copy()
        a = L.tone(self.scene, sat=sat, gamma=gamma, bright=bright)
        a = L.focus_halo(self.card, a, radius=5, dark=0.75, soft=1.4)
        a = L.radial_glow(self.card, a, glow, max(self.FW, self.FH) * 0.55, glow_s, rays=rays, ray_amt=ray_amt)
        a = L.vignette(a, vig)
        q = L.median_q(a, n)
        self._cache[key] = q
        return q.copy()

    def rnd(self, seed):
        return random.Random(seed)

    def spots(self, n, seed, gap=8, avoid=4, mask=None):
        """well spread free positions (off the figure)"""
        rnd = random.Random(seed)
        pts, tries = [], 0
        while len(pts) < n and tries < 6000:
            tries += 1
            x, y = rnd.randrange(1, self.FW - 1), rnd.randrange(1, self.FH - 1)
            if self.dist[y, x] < avoid or (mask is not None and not mask[y, x]):
                continue
            if any(abs(x - a) + abs(y - b) < gap for a, b in pts):
                continue
            pts.append((x, y))
        return pts


# =============================================================== shared texture fields
def contour_u(ctx, amp=1.6, wob=0.08, seed=0):
    """fingerprint / etched contour field centred on the sprite (1 unit ~ 1 grid px)"""
    s = seed * 1.7
    return (ctx.r * (1 + wob * np.sin(3 * ctx.th + s)) + amp * np.sin(ctx.xx / 5.5 + ctx.yy / 7.0 + s)
            + 0.75 * amp * np.sin(ctx.yy / 4.2 - ctx.xx / 9.0 + 2 * s))


def voronoi(ctx, n, seed, mask=None):
    rnd = random.Random(seed)
    pts = np.array([(rnd.uniform(-2, ctx.FW + 2), rnd.uniform(-2, ctx.FH + 2)) for _ in range(n)])
    d = np.hypot(ctx.xx[..., None] + 0.5 - pts[:, 0], ctx.yy[..., None] + 0.5 - pts[:, 1])
    o = np.argsort(d, -1)
    ds = np.take_along_axis(d, o[..., :2], -1)
    return o[..., 0], ds[..., 1] - ds[..., 0], pts, rnd


def glitter_pts(ctx, dens, seed, avoid=2, mask=None):
    rnd = random.Random(seed)
    pts = []
    for y in range(ctx.FH):
        for x in range(ctx.FW):
            if ctx.dist[y, x] > avoid and (mask is None or mask[y, x]) and rnd.random() < dens:
                pts.append((x, y, rnd.random(), rnd.randrange(N)))
    return pts


STAR_SEQ_BIG, STAR_SEQ_SMALL = [1, 2, 3, 2, 1], [1, 2, 1]


def star(a, ctx, x, y, stage, core, mid, tip, allow=None):
    """4-point sparkle into the float bg (never over the figure)"""
    if stage <= 0:
        return

    def put(X, Y, c):
        if 0 <= X < ctx.FW and 0 <= Y < ctx.FH and not ctx.fig[Y, X] and (allow is None or allow[Y, X]):
            a[Y, X] = c
    put(x, y, core if stage >= 2 else mid)
    if stage >= 2:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            put(x + dx, y + dy, mid if stage >= 3 else tip)
    if stage >= 3:
        for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
            put(x + dx, y + dy, tip)
        for dx, dy in ((3, 0), (-3, 0)):
            put(x + dx, y + dy, tip)


def twinkle(a, ctx, pts, p, pal, allow=None, static_stage=3):
    """pts [(x, y, phase)]; p None -> every star at static_stage; else grow/shrink staggered"""
    core, mid, tip = (np.array(L.hexrgb(pal[k])) / 255 for k in ("L", "l", "j"))
    for i, (x, y, ph) in enumerate(pts):
        if p is None:
            st = static_stage if i % 2 == 0 else max(1, static_stage - 1)
        else:
            f = round(p * (N - 1))
            k = (f - ph) % N
            seq = STAR_SEQ_BIG if i % 2 == 0 else STAR_SEQ_SMALL
            st = seq[k] if k < len(seq) else 0
        star(a, ctx, x, y, st, core, mid, tip, allow)


SPARK = {"L": "#ffffff", "l": "#fff4b8", "j": "#9fe8ff"}
GOLD_SPARK = {"L": "#ffffff", "l": "#fde79c", "j": "#d8a83e"}
VAULT_SPARK = {"L": "#fffbe0", "l": "#f3dc7a", "j": "#c8a84a"}
PEARL_SPARK = {"L": "#ffffff", "l": "#f6e8ff", "j": "#a8e6ff"}


# =============================================================== frames + symbols
def draw_frame(ctx, a, style, t, p, v):
    """paint the frame ring (outer t px) of style plain / silver / rainbow / gold / glass; returns ring mask"""
    if not style or not t:
        return np.zeros((ctx.FH, ctx.FW), bool)
    ring = ctx.ring(t)
    ed = ctx.edge_dist()
    xx, yy = ctx.xx, ctx.yy
    ph = 0.0 if p is None else p
    if style == "plain":
        col = np.array(v.get("frame_col", (0.80, 0.80, 0.78)), float)
        f = np.broadcast_to(col, a.shape).copy()
        f = f * (1 + 0.05 * (ed == 1))[..., None]                  # a lighter lip
    elif style == "silver":                           # evs Rare Holo V frame
        tt = 1 - ctx.diag / ctx.span
        tt = 0.25 + 0.6 * tt + 0.25 * np.exp(-((ctx.diag / ctx.span - 0.45) / 0.08) ** 2)
        tt = tt - 0.18 * (((xx - yy) % 3) == 0)
        f = ramp_map(np.clip(tt, 0, 1), SILVER, 6)
        if "frame_col" in v:                            # tinted silver (VMAX gunmetal, VSTAR champagne)
            f = f * (np.array(v["frame_col"]) / 0.8)
        if v.get("frame_bow"):
            f = tint(f, bow(ctx.diag / ctx.span * 1.5 + ph), v["frame_bow"])
    elif style == "rainbow":
        f = bow(ctx.diag / ctx.span * 1.4 - ph, 0.42, 0.98)
        f = f * (1 - 0.08 * (((xx - yy) % 3) == 0))[..., None]
    elif style == "gold":
        lv = 0.5 + 0.22 * np.sin(ctx.diag / ctx.span * 2 * math.pi * 1.5 + 0.5) - 0.08 * (((xx + yy) % 3) == 0)
        f = ramp_map(np.clip(lv, 0, 1), v.get("ramp", GOLD))
    elif style == "glass":
        lbl, gap, _, rnd = voronoi(ctx, 70, 5)
        lvl = np.array([rnd.uniform(0.7, 1.0) for _ in range(70)])[lbl]
        f = np.stack([0.72 * lvl, 0.9 * lvl, 0.98 * lvl], -1)
        f = add(f, WHITE, 0.35 * (gap < 0.8))
        f = tint(f, bow(ctx.diag / ctx.span * 2 + ph), 0.25)
    else:
        raise ValueError(style)
    f = np.clip(f, 0, 1)
    if style != "silver":
        f[ed == 0] *= 0.55                                    # outer edge
    a[ring] = f[ring]
    a[ed == t] *= 0.45                                        # dark hairline on the inside edge (evs)
    return ring


SYM = {
    "circle": [".###.", "#####", "#####", "#####", ".###."],
    "diamond": ["..#..", ".###.", "#####", ".###.", "..#.."],
    "star": ["..#..", "..#..", "#####", ".###.", ".#.#."],
    "spark": ["..#..", ".#.#.", "#...#", ".#.#.", "..#.."],   # shiny sparkle-star (hollow)
}
SYM_COL = {"black": (0.05, 0.05, 0.06), "white": (0.96, 0.97, 1.0), "silver": (0.86, 0.88, 0.94),
           "gold": (1.0, 0.82, 0.3), "pink": (1.0, 0.45, 0.72), "mint": (0.55, 0.95, 0.7),
           "cyan": (0.3, 0.9, 1.0), "grey": (0.5, 0.5, 0.52)}


def draw_symbols(ctx, a, syms):
    """rarity symbols bottom-right, 5x5 each, outlined; never over the figure"""
    if not syms:
        return
    n = len(syms)
    x0 = ctx.FW - 3 - 6 * n + 1
    y0 = ctx.FH - 3 - 5
    for i, (shape, colname) in enumerate(syms):
        col = np.array(SYM_COL[colname])
        edge = np.array((0.95, 0.95, 0.92)) if lumf(col) < 0.4 else np.array((0.03, 0.03, 0.04))
        rows = SYM[shape]
        on = {(x0 + 6 * i + ii, y0 + j) for j, r in enumerate(rows) for ii, ch in enumerate(r) if ch == "#"}
        rim = {(X + dx, Y + dy) for X, Y in on for dx in (-1, 0, 1) for dy in (-1, 0, 1)} - on
        for (X, Y), c in [(q, edge) for q in rim] + [(q, col) for q in on]:
            if 0 <= X < ctx.FW and 0 <= Y < ctx.FH and not ctx.fig[Y, X]:
                a[Y, X] = c


def rim_lift(ctx, a, mode="light", amt=0.35):
    """the 1px ring just outside the sprite: lifted (light) so the black outline reads, or a dark hairline"""
    m = (ctx.dist > 0) & (ctx.dist <= 1.01)
    if mode == "light":
        a[m] = a[m] + (1 - a[m]) * amt
    elif mode == "dark":
        a[m] = a[m] * (1 - amt)
    return a


# =============================================================== families
# each: fam_x(ctx, v, p) -> (bg float (FH, FW, 3), sprite gloss map or None)
# p is None for the static (resting) state, else the loop phase in [0, 1) for the animated frames.

def fam_nofoil(ctx, v, p):
    a = ctx.scene_q(*v.get("scene", ("chunky", 8, 0.72, 0.8)))
    if v.get("lamp") and p is not None:                 # a matte card under a passing desk lamp
        x0 = -12 + p * (ctx.FW + 24)
        a = np.clip(a * (1 + 0.16 * gauss(ctx.xx - x0 + 0.3 * ctx.yy, 9))[..., None], 0, 1)
    return a, None


# ---------------- reverse holo: foil OUTSIDE the art only
BALL = {"poke": (["RRR", "KWK", "WWW"], {"R": (0.9, 0.16, 0.18), "K": (0.08, 0.08, 0.1), "W": (0.98, 0.98, 0.98)}),
        "master": (["PmP", "KWK", "WWW"], {"P": (0.46, 0.22, 0.72), "m": (0.98, 0.42, 0.7), "K": (0.08, 0.08, 0.1),
                                          "W": (0.96, 0.95, 1.0)})}


def reverse_foil(ctx, v, p):
    pat = v["pattern"]
    ph = 0.0 if p is None else p
    xx, yy = ctx.xx, ctx.yy
    if pat == "classic":            # modern reverse: bright silver sheen, soft diagonal rainbow, fine grain
        f = np.broadcast_to(np.array((0.84, 0.85, 0.88)), (ctx.FH, ctx.FW, 3)).copy()
        f = tint(f, bow(ctx.diag / 34 + ph, 0.6), 0.55)
        grain = np.array([[hash((x, y)) % 7 for x in range(ctx.FW)] for y in range(ctx.FH)])
        f = f * (1 - 0.06 * (grain == 0))[..., None] + 0.08 * (grain == 3)[..., None]
    elif pat == "fireworks":        # Legendary Collection: dense pale-rainbow spark bursts on dark foil
        f = np.broadcast_to(np.array((0.34, 0.36, 0.46)), (ctx.FH, ctx.FW, 3)).copy()
        f = tint(f, bow(ctx.diag / 50 + ph * 0.5, 0.5), 0.35)
        rnd = random.Random(86)
        ring = ctx.ring(v["t"])
        for j in range(-2, ctx.FH + 2, 4):
            for i in range(-2 + (j // 4 % 2) * 3, ctx.FW + 2, 6):
                x, y = i + rnd.randrange(-1, 2), j + rnd.randrange(-1, 2)
                h, phase, big = rnd.random(), rnd.randrange(N), rnd.random() < 0.5
                if p is None:
                    k = 2 if big else 1
                else:
                    t = (round(p * (N - 1)) - phase) % 6
                    k = [0, 1, 2, 2, 1, 0][t]
                col = bow(h + ph, 0.45, 1.0)
                pts = [(0, 0)]
                if k >= 1:
                    pts += [(1, 0), (-1, 0), (0, 1), (0, -1)]
                if k >= 2:
                    pts += [(2, 0), (-2, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]
                for dx, dy in pts:
                    X, Y = x + dx, y + dy
                    if 0 <= X < ctx.FW and 0 <= Y < ctx.FH and ring[Y, X]:
                        f[Y, X] = WHITE if (dx, dy) == (0, 0) and k else col * (0.8 if abs(dx) + abs(dy) > 1 else 1)
    else:                           # poke / master ball print on silver
        rows, pal = BALL[pat]
        base = (0.86, 0.87, 0.9) if pat == "poke" else (0.74, 0.7, 0.88)
        f = np.broadcast_to(np.array(base), (ctx.FH, ctx.FW, 3)).copy()
        f = tint(f, bow(ctx.diag / 40 + ph, 0.5), 0.3 if pat == "poke" else 0.45)
        sx, sy = 5, 5
        for j in range(0, ctx.FH, sy):
            for i in range((j // sy % 2) * 2 + 1, ctx.FW, sx):
                for jj, r in enumerate(rows):
                    for ii, ch in enumerate(r):
                        X, Y = i + ii - 1, j + jj
                        if 0 <= X < ctx.FW and 0 <= Y < ctx.FH:
                            f[Y, X] = pal[ch]
    if p is not None:                                   # a glint crossing the foil
        g = gauss(ctx.diag - (-10 + p * (ctx.span + 20)), 2.5)
        f = add(f, WHITE, 0.55 * g)
    return np.clip(f, 0, 1)


def fam_reverse(ctx, v, p):
    a = ctx.scene_q("grid", 16, 0.92, 0.9)
    t = v["t"]
    f = reverse_foil(ctx, v, p)
    ring = ctx.ring(t)
    a[ring] = f[ring]
    ed = ctx.edge_dist()
    a[ed == t - 1] *= 0.45                              # the art window's edge
    a[ed == 0] *= 0.6
    return a, None


# ---------------- holo in the art window (frame matte)
def holo_layer(ctx, v, p):
    """-> (hue, amt, white) maps for the art-window foil pattern"""
    pat = v["pattern"]
    ph = 0.0 if p is None else p
    xx, yy, H, W = ctx.xx, ctx.yy, ctx.FH, ctx.FW
    white = np.zeros((H, W))
    rnd = random.Random(v.get("seed", 1))
    if pat == "sheen":              # modern standard holo: soft diagonal rainbow bands + vertical grain
        hue = (xx + 0.5 * yy) / 30 + ph
        amt = 0.26 + 0.12 * np.sin((xx + 0.5 * yy) / 4.5)
        white += 0.05 * (xx % 3 == 0)
    elif pat == "galaxy":           # WotC: starfield over a soft rainbow nebula
        hue = 0.55 + 0.25 * np.sin(xx / 13 + 1) * np.cos(yy / 11) + ph
        amt = 0.2 + 0.08 * np.sin(xx / 7 + yy / 9)
        for (x, y, r, ph0) in glitter_pts(ctx, 0.06, 11, avoid=2):
            tw = 1.0 if p is None else 0.5 + 0.5 * math.cos(2 * math.pi * (p * 2 + ph0 / N))
            white[y, x] = (0.9 if r > 0.8 else 0.5) * tw
    elif pat == "cosmos":           # dots, rings/orbs, a few swirls
        hue = ctx.diag / 60 + ph
        amt = np.full((H, W), 0.12)
        for i in range(20):
            x, y = rnd.uniform(0, W), rnd.uniform(0, H)
            rr = rnd.choice((1.2, 1.6, 2.2, 3.2, 4.4))
            d = np.hypot(xx - x, yy - y)
            h0 = rnd.random()
            if rr < 2.5:
                m = d <= rr
            else:
                m = np.abs(d - rr) < 0.7
            amt = np.where(m, 0.6, amt)
            hue = np.where(m, h0 + ph, hue)
            white += 0.18 * (d < 0.6)
        for s in range(3):          # swirl arcs
            x, y = rnd.uniform(8, W - 8), rnd.uniform(8, H - 8)
            d, t_ = np.hypot(xx - x, yy - y), np.arctan2(yy - y, xx - x)
            m = (np.abs(d - (2 + 1.2 * ((t_ + math.pi) % (2 * math.pi)))) < 0.6) & (d < 9)
            amt = np.where(m, 0.5, amt)
            white += 0.12 * m
    elif pat == "crosshatch":
        on = ((xx + yy) % 4 == 0) | ((xx - yy) % 4 == 0)
        hue = xx / 26 + yy / 60 + ph
        amt = np.where(on, 0.55, 0.12)
        white += 0.1 * (((xx + yy) % 4 == 0) & ((xx - yy) % 4 == 0))
    elif pat == "waterweb":
        s = 2 * math.pi * ph
        f = np.sin(xx / 2.6 + 1.3 * np.sin(yy / 3.7 + s)) + np.sin(yy / 2.9 + 1.1 * np.sin(xx / 4.3 - s))
        web = gauss(f, 0.32)
        hue = 0.5 + yy / 50 + ph * 0.5
        amt = 0.12 + 0.5 * web
        white += 0.12 * web
    elif pat == "crackedice":
        lbl, gap, pts, r2 = voronoi(ctx, 42, v.get("seed", 3))
        hs = np.array([r2.random() for _ in range(42)])
        br = np.array([r2.uniform(-0.12, 0.16) for _ in range(42)])
        hue = hs[lbl] + ph * 0.3
        amt = np.full((H, W), 0.36)
        white += np.clip(br[lbl], 0, 1) + 0.35 * (gap < 0.8)
        if p is not None:           # shards flash as the light passes
            bar = -10 + p * (W + 20)
            white += 0.35 * gauss(pts[lbl, 0] - bar, 5)
    elif pat == "swirl":
        arms = np.cos(4 * ctx.th + ctx.r / 2.4 - 2 * math.pi * ph)
        hue = ctx.th / (2 * math.pi) + ctx.r / 40 + ph
        amt = 0.14 + 0.36 * (arms > 0.55)
        white += 0.08 * (arms > 0.9)
    elif pat == "tinsel":           # BW: fine horizontal lines
        hue = yy / 26 + xx / 90 + ph
        amt = 0.1 + 0.42 * (yy % 2 == 0)
        white += 0.06 * (yy % 4 == 0)
    elif pat == "mirror":           # XY: one smooth diagonal shine, no pattern
        c = 0.4 * ctx.span if p is None else -12 + p * (ctx.span + 24)
        g = gauss(ctx.diag - c, 11)
        hue = ctx.diag / 44 + ph
        amt = 0.1 + 0.42 * g
        white += 0.22 * gauss(ctx.diag - c, 3.5)
    elif pat == "stripes":          # SWSH: vertical-stripe sheen
        hue = xx / 22 + yy / 120 + ph
        amt = 0.14 + 0.3 * ((xx % 4) < 2) + 0.08 * np.sin(yy / 6)
        white += 0.04 * ((xx % 4) == 0)
    elif pat == "wave":             # SV: soft wave sheen
        w = np.sin((yy + 2.5 * np.sin(xx / 6 + 2 * math.pi * ph)) / 2.6)
        hue = (xx + 3 * np.sin(yy / 5)) / 30 + ph
        amt = 0.2 + 0.2 * (w > 0.3)
        white += 0.08 * (w > 0.85)
    elif pat == "fireworks":        # Pikachu Rare: burst fireworks over the whole card
        hue = ctx.diag / 60 + ph * 0.5
        amt = np.full((H, W), 0.14)
        for j in range(-2, H + 2, 6):
            for i in range(-2 + (j // 6 % 2) * 4, W + 2, 8):
                x, y = i + rnd.randrange(-2, 3), j + rnd.randrange(-2, 3)
                h0, phase = rnd.random(), rnd.randrange(N)
                k = 2 if p is None else [0, 1, 2, 2, 1, 0, 0, 0][(round(p * (N - 1)) - phase) % 8]
                if k == 0:
                    continue
                pts = [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)]
                if k >= 2:
                    pts += [(2, 2), (-2, -2), (2, -2), (-2, 2), (3, 0), (-3, 0), (0, 3), (0, -3)]
                for dx, dy in pts:
                    X, Y = x + dx, y + dy
                    if 0 <= X < W and 0 <= Y < H:
                        amt[Y, X] = 0.8
                        hue[Y, X] = h0 + ph
                        white[Y, X] += 0.5 if (dx, dy) == (0, 0) else 0.15
    elif pat == "stars":            # a repeating tiny-star print
        m = np.zeros((H, W), bool)
        for j in range(0, H, 6):
            for i in range((j // 6 % 2) * 4, W, 8):
                for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                    if 0 <= i + dx < W and 0 <= j + dy < H:
                        m[j + dy, i + dx] = True
        hue = 0.12 + 0.1 * np.sin(xx / 9) + ph
        amt = np.where(m, 0.6, 0.16)
        white += 0.25 * m
    else:
        raise ValueError(pat)
    return hue, np.clip(amt * v.get("foil", 1.0), 0, 1), white


def fam_holo(ctx, v, p):
    a = ctx.scene_q(*v.get("scene", ("grid", 16, 1.0, 0.85)))
    whole = v.get("whole")
    if whole:                                        # foil over the frame too (Radiant Collection)
        draw_frame(ctx, a, v.get("frame"), v.get("t", 3), p, v)
    hue, amt, white = holo_layer(ctx, v, p)
    gloss = None
    if p is not None and v["pattern"] not in ("crackedice", "mirror"):     # a soft vertical light bar
        bar = gauss(ctx.xx - (-10 + p * (ctx.FW + 20)), 5)
        amt = np.clip(amt + 0.25 * bar, 0, 1)
        white = white + 0.18 * bar
        gloss = 0.35 * bar
    a = tint(a, bow(hue, v.get("sat", 0.6)), amt)
    a = add(a, WHITE, white)
    if not whole:
        draw_frame(ctx, a, v.get("frame"), v.get("t", 3), p, v)
    return a, gloss


# ---------------- V family: framed, diagonal rainbow beams (sunpillar)
def fam_vbeam(ctx, v, p):
    a = ctx.scene_q("grid", 24, 1.4, 1.05, 0.9)          # evs: saturated, bright
    xx, yy = ctx.xx, ctx.yy
    tex = v.get("tex", "v")
    # static texture in the art
    if tex == "ex":                                    # EX era: horizontal line holo
        a = tint(a, bow(yy / 20 + (0 if p is None else p)), 0.18 + 0.2 * (yy % 3 == 0))
    elif tex == "gx":                                  # SM: water-web holo in the art
        s = 0 if p is None else 2 * math.pi * p
        f = np.sin(xx / 2.6 + 1.3 * np.sin(yy / 3.7 + s)) + np.sin(yy / 2.9 + 1.1 * np.sin(xx / 4.3 - s))
        web = gauss(f, 0.32)
        a = tint(a, bow(0.5 + yy / 50), 0.12 + 0.4 * web)
        a = add(a, WHITE, 0.1 * web)
    elif tex == "ex_bw":                               # BW/XY EX: etched sheen lines over the face
        u = (xx * 0.8 - yy) / 2.0
        line = np.abs(u - np.round(u)) < 0.22
        a = tint(a, bow(ctx.diag / 32), 0.14 + 0.24 * line)
        a = add(a, WHITE, 0.06 * line)
    elif tex == "vmax":                                # bold etched diamond lattice over everything
        u, w = (xx + yy) / 7.0, (xx - yy) / 7.0
        line = (np.abs(u - np.round(u)) < 0.16) | (np.abs(w - np.round(w)) < 0.16)
        a = tint(a, bow(ctx.diag / 40 + (0 if p is None else p)), 0.16 + 0.34 * line)
        a = add(a, WHITE, 0.1 * line)
    elif tex == "vstar":                               # fine horizontal gold streaks
        a = tint(a, np.array((1.0, 0.86, 0.45)), 0.14 + 0.16 * ((yy + (xx // 9)) % 3 == 0))
    elif tex == "ex_sv":                               # SV ex: fine sparkle grain
        a = tint(a, bow(ctx.diag / 30), 0.16)
        for x, y, r, ph0 in glitter_pts(ctx, 0.07, 21):
            k = 0 if p is None else (round(p * (N - 1)) + ph0) % 6
            a[y, x] = mixc(a[y, x], WHITE, [0.65, 0.35, 0.1, 0.0, 0.1, 0.35][k])
    else:                                              # V: evs 'sunpillar' stripes over the whole window
        u = (xx * 0.9 + yy * 0.35) / 9.0
        a = tint(a, bow(u, 0.7), 0.10 + 0.10 * lumf(a)[..., None], lift=0.0, gain=1.0)
        a = np.clip(a * 1.02 + 0.02, 0, 1)
    ring = draw_frame(ctx, a, v.get("frame", "silver"), v.get("t", 3), p, v)
    if v.get("frame_glitter"):                          # EX era: holographic silver border
        for x, y, r, ph0 in glitter_pts(ctx, 0.25, 13, mask=ring):
            k = 0 if p is None else (round(p * (N - 1)) + ph0) % 5
            a[y, x] = mixc(a[y, x], bow(r, 0.5), [0.8, 0.5, 0.2, 0.0, 0.4][k])
    # the beams (evs sunpillar): a 45-degree band with a continuous rainbow across it, sweeping window AND
    # frame, and a fainter counter-beam along x - y; triangular profiles; nothing parked in the static
    band = v.get("beam_w", 9) * 2.0
    gloss = np.zeros((ctx.FH, ctx.FW))
    if p is not None:
        t = p * (N - 1) / (N - 2)
        ctr1 = -band + t * (ctx.span + 2 * band)
        ctr2 = ctx.FW + band - t * (ctx.span + 2 * band) * 0.9
        u1 = (ctx.diag - ctr1) / band
        k1 = np.clip(1 - np.abs(u1 * 2), 0, 1) * v.get("beam", 0.55) / 0.55
        u2 = (xx - yy - ctr2) / (band * 0.7)
        k2 = np.clip(1 - np.abs(u2 * 2), 0, 1) * 0.45 * v.get("second", 1.0)
        c1 = bow(u1 * 0.9 + 0.3 + xx / 160, 0.6)
        c2 = bow(-u2 * 0.9 + 0.7, 0.5)
        if v.get("gold_beam"):
            c1 = mixc(c1, np.array((1.0, 0.84, 0.42)), 0.6)
            c2 = mixc(c2, np.array((1.0, 0.88, 0.5)), 0.6)
        a = mixc(a, c1, np.clip((0.15 + 0.45 * k1) * (k1 > 0), 0, 1))
        a = mixc(a, c2, np.clip(k2, 0, 1))
        gloss = 0.25 * k1 * (k1 > 0.55)
    return a, (gloss if p is not None else None)


# ---------------- etched full art (fingerprint lines + slow rainbow wave)
def duotone(ctx, a, dark, light, sat=1.0):
    l = lumf(a)
    l = (l - np.percentile(l, 2)) / max(1e-6, np.percentile(l, 98) - np.percentile(l, 2))
    return mixc(np.broadcast_to(np.array(dark), a.shape), np.array(light), np.clip(l, 0, 1))


def fingerprint(ctx, period=2.6, seed=0):
    """evs fingerprint field: contours of a sum of whorls (off-centre, scaled to the card), bent by waves"""
    FW, FH = ctx.FW, ctx.FH
    cs = [(12 / 84 * FW, 10 / 66 * FH, 1.0), (70 / 84 * FW, 52 / 66 * FH, 0.8), (64 / 84 * FW, 8 / 66 * FH, 0.5)]
    xx, yy = ctx.xx, ctx.yy
    f = sum(w * np.hypot(xx - cx, (yy - cy) * 1.15) for cx, cy, w in cs) / sum(w for *_, w in cs)
    f = f + 1.6 * np.sin(xx / 7.0 + seed) * np.cos(yy / 9.0) + 0.9 * np.sin((xx + yy) / 5.0)
    return f


def fam_etched(ctx, v, p):
    mode = v.get("mode", "ur")
    if mode == "ur":                                    # evs Rare Ultra
        a = L.tone(ctx.scene, sat=1.12, bright=1.0)
        a = L.focus_halo(ctx.card, a, radius=5, dark=0.7, soft=1.4)
        a = L.radial_glow(ctx.card, a, v.get("glow", (0.75, 0.95, 1.0)), max(ctx.FW, ctx.FH) * 0.55, 0.36, rays=12,
                          ray_amt=0.5)
        a = L.vignette(a, 0.5, tint=v.get("vig_tint", (0.25, 0.0, 0.2)))
        period = v.get("period", 2.6)
        f = fingerprint(ctx, period, v.get("seed", 0))
        amp_on, amp_off = v.get("line", 0.11), -0.025
    elif mode == "ir":                                  # IR: the painting, a lighter and wider-spaced texture
        a = ctx.painting(sat=1.1, glow_s=0.28, rays=10, ray_amt=0.35, vig=0.3, gamma=0.85, bright=1.05)
        period = v.get("period", 4.0)
        f = contour_u(ctx, amp=v.get("amp", 2.2), seed=v.get("seed", 0))
        amp_on, amp_off = v.get("line", 0.06), 0.0
    else:                                               # trainer gallery: pastel, medium texture
        a = ctx.scene_q("grid", 40, 0.85, 1.0)
        a = mixc(a, np.array((1.0, 0.97, 1.0)), 0.25)
        period = v.get("period", 3.0)
        f = contour_u(ctx, amp=v.get("amp", 1.6), seed=v.get("seed", 0))
        amp_on, amp_off = v.get("line", 0.1), 0.0
    line = ((f / period) % 1.0) < (1.0 / period)
    a = np.clip(a + np.where(line, amp_on, amp_off)[..., None] * (0.6 + 0.4 * a), 0, 1)
    if mode == "ur":
        a = L.median_q(a, 170)
    if mode == "tg":
        a = tint(a, bow(np.floor(f / period) / 14), 0.2 * line)
    gloss = None
    if p is not None:                                   # evs: the lines light up in a rainbow wave along the contours
        t = p * (N - 1) / (N - 2)
        idx = np.floor(f / period)
        lo, hi = idx.min(), idx.max()
        front = lo - 4 + t * (hi - lo + 8)
        k = np.exp(-((idx - front) / 2.2) ** 2) * v.get("wave", 1.0)
        hue = bow(idx / 14.0 - t * 0.6, 0.55)
        a = np.where(line[..., None], mixc(a, hue, 0.75 * k), mixc(a, hue, 0.16 * k))
        gloss = 0.12 * k
    if v.get("glitter"):
        for x, y, r, ph0 in glitter_pts(ctx, v["glitter"], 17):
            kk = 0 if p is None else (round(p * (N - 1)) + ph0) % 5
            a[y, x] = mixc(a[y, x], bow(r, 0.3), [0.9, 0.5, 0.0, 0.0, 0.5][kk])
    pts = [(x, y, (i * 4 + 1) % N) for i, (x, y) in enumerate(ctx.spots(v.get("stars", 4), 91, gap=16, avoid=5))]
    twinkle(a, ctx, pts, p, {"L": "#ffffff", "l": "#e6fbff", "j": "#9fe8ff"})
    return a, gloss


# ---------------- special illustration: the painting + pearlescent sweep
def fam_sir(ctx, v, p):
    a = L.tone(ctx.scene, sat=v.get("sat", 1.15), bright=1.02, gamma=v.get("gamma", 0.85))
    a = L.focus_halo(ctx.card, a, radius=4, dark=0.8, soft=1.2)
    if v.get("glow"):
        a = L.radial_glow(ctx.card, a, v["glow"], max(ctx.FW, ctx.FH) * 0.55, 0.3, rays=12, ray_amt=0.45)
    h = ndimage.gaussian_filter(lumf(a), 0.6)
    gy, gx = np.gradient(h)

    def relief(theta):
        return np.clip(-(gx * math.cos(theta) + gy * math.sin(theta)) * v.get("emboss", 2.4), -0.3, 0.3)

    th0 = math.atan2(-1.3, -1.0)                       # lit from the top-left
    a = np.clip(a + relief(th0)[..., None] * (0.35 + 0.65 * a), 0, 1)
    a = L.vignette(a, 0.4, tint=v.get("vig_tint", (0.02, 0.04, 0.12)))
    a = L.median_q(a, 200)
    gloss = None
    pearl = v.get("pearl")
    if p is not None:
        t = p * (N - 1) / (N - 2)
        th = th0 + math.sin(t * 2 * math.pi) * 1.6     # the light swings across the brushwork
        lv = lumf(a)[..., None]
        a = np.clip(a + ((relief(th) - relief(th0))[..., None] * (0.35 + 0.65 * lv) * 2.2), 0, 1)
        ctr = -20 + t * (ctx.span + 40)
        d = ctx.diag - ctr
        k = np.exp(-(d / 12.0) ** 2) * 0.2
        a = mixc(a, np.array((1.0, 0.957, 0.9)), k)
        gloss = k * 0.8
        if pearl:                                       # pearlescent sweep: pink -> cyan across a broad band
            w = 16
            dd = ctx.diag * 0.8 + ctx.yy * 0.2 - (-w * 1.5 + t * (ctx.span + 3 * w))
            band = gauss(dd, w)
            hue = pearl[0] + (pearl[1] - pearl[0]) * np.clip(dd / (2 * w) + 0.5, 0, 1)
            a = mixc(a, hsv(hue, 0.3, 1.0), 0.45 * band)
            gloss = np.maximum(gloss, 0.3 * band)
    elif pearl:                                         # static: a faint pearl lustre on the lit side
        dd = ctx.diag - 0.26 * ctx.span
        a = mixc(a, hsv(pearl[0] + (pearl[1] - pearl[0]) * np.clip(dd / 40 + 0.5, 0, 1), 0.3, 1.0),
                 0.42 * gauss(dd, 18))
    pts = [(x, y, (i * 5 + 2) % N) for i, (x, y) in enumerate(ctx.spots(4, 31, gap=16, avoid=5))]
    twinkle(a, ctx, pts, p, PEARL_SPARK if pearl else {"L": "#ffffff", "l": "#fff3c4", "j": "#8fd8ff"})
    return a, gloss


# ---------------- gold / hyper
def fam_gold(ctx, v, p):
    kind = v.get("kind", "hyper")
    stops = v.get("ramp", GOLD)
    lsc = ndimage.gaussian_filter(lumf(ctx.scene), 0.7)
    lsc = np.clip((lsc - np.percentile(lsc, 3)) / max(1e-6, np.percentile(lsc, 97) - np.percentile(lsc, 3)), 0, 1)
    xx, yy = ctx.xx, ctx.yy
    if kind == "hyper":             # SV: the scene engraved in gold + crystalline facets
        nf = 120
        lbl, gap, _, rnd = voronoi(ctx, nf, 247)
        tilt = np.array([(rnd.uniform(-0.007, 0.007), rnd.uniform(-0.007, 0.007), rnd.uniform(-0.09, 0.09)) for _ in range(nf)])
        fac = tilt[lbl, 2] + tilt[lbl, 0] * (xx - ctx.FW / 2) + tilt[lbl, 1] * (yy - ctx.FH / 2)
        lv = 0.34 + 0.2 * (ndimage.gaussian_filter(lsc, 1.5) - 0.5) + fac - 0.1 * (gap < 0.7)
    elif kind == "mono":            # ME Mega Hyper Rare: all-gold monochrome, dense etched contour lines
        u = contour_u(ctx, amp=2.0, seed=9)
        line = ((u / 2.0) % 1) < 0.5
        lv = 0.3 + 0.3 * lsc - 0.1 * line + 0.05 * np.sin(u / 5)
    elif kind == "studs":           # SM/SWSH gold secret: embossed pyramid studs, faint scene
        P = 8
        u, w = (xx + yy) / P, (xx - yy) / P
        fu, fw = u - np.floor(u) - 0.5, w - np.floor(w) - 0.5
        face = np.where(np.abs(fu) >= np.abs(fw), np.where(fu < 0, 0, 3), np.where(fw > 0, 1, 2))
        lv = np.array([0.62, 0.48, 0.38, 0.28])[face] + 0.14 * (lsc - 0.5)
    else:                           # 'engrave': guilloche rose engraving around the sprite (older gold)
        uu = ctx.r + 1.4 * np.sin(7 * ctx.th + ctx.r / 6)
        lv = 0.42 - 0.13 * ((uu / 3.0) % 1 < 0.34) + 0.2 * (lsc - 0.5)
    sheen = gauss(ctx.diag / ctx.span - 0.34, 0.12) * 0.12
    lv = lv + sheen + 0.28 * gauss(ctx.dist, 7) * (ctx.dist > 0)
    gloss = None
    if p is not None:               # the metallic sheen sweep with an echo
        d = ctx.diag - (-10 + p * (ctx.span + 20))
        lv = lv + 0.36 * (np.abs(d) <= 1) + 0.22 * ((np.abs(d) > 1) & (np.abs(d) <= 3)) + \
            0.1 * ((np.abs(d) > 3) & (np.abs(d) <= 6)) + 0.1 * ((d >= -16) & (d <= -13))
        gloss = 0.35 * gauss(d, 3)
    a = ramp_map(np.clip(lv, 0, 0.97), stops)
    for x, y, r, ph0 in glitter_pts(ctx, v.get("glitter", 0.035), 5, avoid=3):
        k = 0 if p is None else (round(p * (N - 1)) + ph0) % 8
        if p is None and r < 0.6:
            continue
        a[y, x] = [WHITE, ramp_arr(stops)[-4], None, None, None, None, None, None][k] if k < 2 else a[y, x]
    draw_frame(ctx, a, v.get("frame", "gold"), v.get("t", 3), p, {"ramp": stops})
    pts = [(x, y, (i * 4 + 1) % N) for i, (x, y) in enumerate(ctx.spots(v.get("stars", 4), 13, gap=14, avoid=5))]
    twinkle(a, ctx, pts, p, GOLD_SPARK)
    return a, gloss


# ---------------- rainbow rare: pastel rainbow + etched lines
def rainbow_hue(ctx, p):
    """the rainbow rare's hue field (turns), shared by the foil and the rainbow sprite; flows when animated"""
    hue = -0.04 + ctx.xx / ctx.FW * 0.5 + ctx.yy / ctx.FH * 0.42
    if p is not None:
        t = p * (N - 1) / (N - 2)
        hue = hue + 0.10 * np.sin(2 * math.pi * (t - ctx.diag / ctx.span))
    return hue


def fam_rainbow(ctx, v, p):
    a = L.tone(ctx.scene, sat=1.0, bright=1.0)
    a = tint(np.clip(a * 0.8 + 0.22, 0, 1), bow(rainbow_hue(ctx, None), 0.5), 0.68, lift=0.0, gain=1.0)
    a = L.tone(a, sat=1.05, bright=1.0)
    a = L.focus_halo(ctx.card, a, radius=4, dark=0.82, soft=1.2)
    xx, yy = ctx.xx, ctx.yy
    u = (xx - yy * 0.8) + 1.5 * np.sin(yy / 6.0 + 204) + 1.0 * np.sin(xx / 11.0)
    line = (np.floor(u) % 3) == 0
    a = np.clip(a + np.where(line, -0.07, 0.025)[..., None], 0, 1)
    a = L.median_q(a, 150)
    gloss = None
    if p is not None:                                   # the rainbow flows, a sheen flashes the etched lines
        from skimage.color import rgb2hsv, hsv2rgb
        hs = rgb2hsv(a)
        hs[..., 0] = (hs[..., 0] + (rainbow_hue(ctx, p) - rainbow_hue(ctx, None))) % 1.0
        a = hsv2rgb(hs)
        t = p * (N - 1) / (N - 2)
        k = np.exp(-((ctx.diag - (-10 + t * (ctx.span + 20))) / 5.0) ** 2)
        a = np.where(line[..., None], mixc(a, WHITE, 0.55 * k), mixc(a, WHITE, 0.18 * k))
        gloss = 0.2 * k
    rnd = np.random.default_rng(204)
    glint = (rnd.random((ctx.FH, ctx.FW)) < 0.03) & (ctx.dist > 2)
    gph = rnd.integers(0, N, (ctx.FH, ctx.FW))
    if p is None:
        a[glint] = np.clip(a[glint] * 0.3 + 0.75, 0, 1)
    else:
        s_ = (round(p * (N - 1)) - gph) % N
        a[glint & (s_ == 0)] = 1.0
        m = glint & ((s_ == 1) | (s_ == 2))
        a[m] = np.clip(a[m] * 0.3 + 0.75, 0, 1) * 0.5 + 0.5
        m = glint & ((s_ == 6) | (s_ == 7))
        a[m] = a[m] * 0.7
    pts = [(x, y, (i * 4 + 3) % N) for i, (x, y) in enumerate(ctx.spots(4, 71, gap=16, avoid=5))]
    twinkle(a, ctx, pts, p, {"L": "#ffffff", "l": "#fff0fa", "j": "#b8f0ff"})
    return a, gloss


# ---------------- shiny: sparkle foil, shiny sprite
def fam_shiny(ctx, v, p):
    kind = v.get("kind", "vault")
    ph = 0.0 if p is None else p
    if kind == "vault":             # white/silver window, glitter foil
        a = ctx.scene_q("grid", 12, 0.6, 1.0)
        a = mixc(a, np.array((0.97, 0.96, 0.93)), 0.8)
        a = tint(a, bow(ctx.diag / 40 + ph), 0.18)
    elif kind == "gx":              # full-art shiny GX: silver etched + glitter
        a = ctx.scene_q("grid", 16, 0.4, 1.0)
        a = duotone(ctx, a, (0.3, 0.33, 0.4), (0.96, 0.97, 1.0))
        u = contour_u(ctx, seed=2)
        a = add(a, WHITE, 0.12 * (((u / 3) % 1) < 0.34))
        a = tint(a, bow(ctx.diag / 30 + ph), 0.25)
    elif kind == "sv":              # SV Shiny Rare: the scene kept, sparkle-grain foil all over
        a = ctx.scene_q("grid", 24, 0.9, 0.85)
        a = tint(a, bow(ctx.diag / 30 + ph), 0.14)
    elif kind == "sur":             # Shiny Ultra Rare: full-bleed, dark duotone + etch + dense glitter
        a = ctx.scene_q("grid", 24, 1.0, 1.0)
        a = duotone(ctx, a, (0.05, 0.05, 0.12), (0.72, 0.74, 0.9))
        u = contour_u(ctx, seed=5)
        a = add(a, WHITE, 0.1 * (((u / 3) % 1) < 0.34))
    elif kind == "shining":         # Neo Shining: cosmos holo art, big starbursts
        a = ctx.scene_q("grid", 16, 1.0, 0.8)
        hue, amt, white = holo_layer(ctx, {"pattern": "cosmos", "seed": 5}, p)
        a = add(tint(a, bow(hue), amt), WHITE, white)
    dens = v.get("glitter", 0.08)
    gcols = [np.array(L.hexrgb(h)) / 255 for h in ("#fff8d8", "#f3dc7a", "#e8f0ff", "#ffd0f0", "#c8f4ff")]
    for x, y, r, ph0 in glitter_pts(ctx, dens, 9, avoid=2):
        k = 1 if p is None else (round(p * (N - 1)) + ph0) % 6
        amt = [0.95, 0.7, 0.4, 0.15, 0.0, 0.4][k] * (0.6 + 0.4 * r)
        a[y, x] = mixc(a[y, x], gcols[int(r * 5) % 5], amt)
    gloss = None
    if p is not None:
        d = ctx.diag - (-12 + p * (ctx.span + 24))
        a = add(a, WHITE, 0.22 * gauss(d, 4))
        gloss = 0.25 * gauss(d, 3)
    draw_frame(ctx, a, v.get("frame"), v.get("t", 3), p, v)
    n = v.get("stars", 6)
    pts = [(x, y, (i * 3) % N) for i, (x, y) in enumerate(ctx.spots(n, 41, gap=11, avoid=4))]
    twinkle(a, ctx, pts, p, v.get("spark", VAULT_SPARK))
    return a, gloss


# ---------------- radiant: radial crosshatch burst (shiny sprite)
def fam_radiant(ctx, v, p):
    a = ctx.scene_q("grid", 24, 0.95, 0.78)
    ph = 0.0 if p is None else p
    rays = v.get("rays", 20)
    th = ctx.th - ph * 2 * math.pi / rays
    ray = np.cos(rays * th) > 0.25
    hatch = (((ctx.xx + ctx.yy) % 3) == 0) | (((ctx.xx - ctx.yy) % 3) == 0)
    hue = ctx.th / (2 * math.pi) * 2 + ctx.r / 50 + ph
    a = tint(a, bow(hue, 0.65), np.where(ray & hatch, 0.8, np.where(ray, 0.35, 0.08)))
    a = add(a, WHITE, 0.3 * (ray & hatch) * np.clip(1 - ctx.r / (ctx.span * 0.45), 0.25, 1))
    a = np.where((~ray)[..., None], a * 0.82, a)
    if p is not None:               # a light ring pulses outward
        rr = p * ctx.span * 0.55
        a = add(a, WHITE, 0.3 * gauss(ctx.r - rr, 2.2) * ray)
    draw_frame(ctx, a, "silver", v.get("t", 2), p, v)
    return a, None


# ---------------- amazing: a rainbow splash bursting out of the frame
def fam_amazing(ctx, v, p):
    a = ctx.scene_q("grid", 24, 0.95, 0.72)
    a = tint(a, bow(ctx.diag / 40), 0.12)
    ring = draw_frame(ctx, a, "silver", 3, p, v)
    ph = 0.0 if p is None else p
    R = ctx.span * 0.3
    rad = R * (0.62 + 0.25 * np.abs(np.sin(3.5 * ctx.th + 1.0)) + 0.18 * np.abs(np.sin(7 * ctx.th + 0.3))
               + 0.1 * np.sin(13 * ctx.th))
    body = ctx.r < rad
    rnd = random.Random(8)
    drops = np.zeros((ctx.FH, ctx.FW), bool)
    for _ in range(26):
        t = rnd.uniform(-math.pi, math.pi)
        rr = R * rnd.uniform(0.9, 1.9)
        x, y = ctx.cx + rr * math.cos(t), ctx.cy + rr * math.sin(t) * 0.8
        drops |= np.hypot(ctx.xx - x, ctx.yy - y) < rnd.choice((0.8, 1.2, 1.6, 2.2))
    m = body | drops
    hue = ctx.th / (2 * math.pi) + 0.15 * ctx.r / R - ph
    streak = (np.cos(24 * ctx.th) > 0.6)
    col = hsv(hue, 0.78, 0.96)
    col = col * (0.82 + 0.18 * np.clip(ctx.r / R, 0, 1))[..., None]
    col = add(col, WHITE, 0.2 * streak + 0.25 * gauss(ctx.r - rad, 1.2))
    a = np.where(m[..., None], mixc(a, col, 0.82), a)
    if p is not None:
        rr = p * R * 1.8
        a = add(a, WHITE, 0.35 * gauss(ctx.r - rr, 1.8) * m)
    return a, None


# ---------------- prism / crystal / star / ace: crystal facets
def fam_prism(ctx, v, p):
    kind = v.get("kind", "prism")
    a = ctx.scene_q("grid", 24, 1.0, 0.82)
    ring = draw_frame(ctx, a, v.get("frame", "silver"), v.get("t", 3), p, v)
    n = v.get("facets", 55)
    lbl, gap, pts, rnd = voronoi(ctx, n, v.get("seed", 7))
    if kind == "prism":             # Prism Star: kaleidoscope wedges radiating from the Pokemon
        k = 18
        wedge = np.floor((ctx.th + math.pi) / (2 * math.pi) * k).astype(int)
        ringi = np.floor((ctx.r + 3 * ((wedge % 2) == 0)) / 7).astype(int)
        lbl = (wedge + k * ringi) % n
        fa = (ctx.th + math.pi) / (2 * math.pi) * k
        fr = (ctx.r + 3 * ((wedge % 2) == 0)) / 7
        gap = np.minimum(np.minimum(fa % 1, 1 - fa % 1) * ctx.r * 2 * math.pi / k, np.minimum(fr % 1, 1 - fr % 1) * 7) * 2
        cxs = ctx.cx + (np.arange(n) % 7) * 0
        pts = np.stack([np.array([np.mean(ctx.xx[lbl == i]) if (lbl == i).any() else 0 for i in range(n)]),
                        np.array([np.mean(ctx.yy[lbl == i]) if (lbl == i).any() else 0 for i in range(n)])], -1)
    lvl = np.array([rnd.uniform(0.0, 1.0) for _ in range(n)])
    hs = np.array([rnd.random() for _ in range(n)])
    seam = gap < 0.75
    region = np.ones((ctx.FH, ctx.FW), bool) if v.get("whole", True) else ~ring
    if kind == "crystal":
        hs = 0.45 + 0.25 * hs
    elif kind == "ace":
        hs = 0.8 + 0.25 * hs
    flash = 0.0
    if p is not None:
        flash = gauss(pts[lbl, 0] + 0.6 * pts[lbl, 1] - (-12 + p * (ctx.FW * 1.6 + 24)), 6)
    amt = (0.3 + 0.3 * lvl[lbl]) * v.get("foil", 1.0)
    b = tint(a, bow(hs[lbl] + (0 if p is None else 0.3 * p), v.get("sat", 0.6)), np.clip(amt + 0.3 * flash, 0, 1))
    b = add(b, WHITE, 0.22 * lvl[lbl] ** 3 + 0.3 * seam + 0.5 * flash * lvl[lbl])
    if kind == "crystal":            # crystal facets gather round the Pokemon (its crystal body refracting)
        fade = np.clip(1.25 - ctx.dist / 16, 0, 1)[..., None] * (~ring)[..., None]
        a = mixc(a, b, fade)
    else:
        a = np.where(region[..., None], b, a)
    if kind == "ace":                                   # a hot magenta-gold prism gradient on top
        a = tint(a, hsv(0.92 + ctx.diag / ctx.span * 0.25, 0.7, 1.0), 0.3)
    npt = v.get("stars", 6)
    pts2 = [(x, y, (i * 3 + 1) % N) for i, (x, y) in enumerate(ctx.spots(npt, 23, gap=12, avoid=4))]
    twinkle(a, ctx, pts2, p, v.get("spark", SPARK))
    return a, (0.3 * flash if p is not None and isinstance(flash, np.ndarray) else None)


# ---------------- old-era specials
def fam_oldera(ctx, v, p):
    kind = v["kind"]
    ph = 0.0 if p is None else p
    xx, yy = ctx.xx, ctx.yy
    gloss = None
    if kind == "lvx":               # DP LV.X: silver, vertical light streaks across the art
        a = ctx.scene_q("grid", 20, 1.0, 0.85)
        s = (xx + 0.25 * yy - ph * 12) % 6
        a = tint(a, bow(xx / 28 + ph), 0.16 + 0.44 * (s < 1.5))
        a = add(a, WHITE, 0.14 * (s < 0.8))
        draw_frame(ctx, a, "silver", 3, p, {"frame_col": (0.74, 0.76, 0.8)})
    elif kind == "legend":          # HGSS LEGEND: two half-cards, full-card bumpy sparkle holo, a seam
        a = ctx.scene_q("grid", 24, 1.05, 0.85)
        left = xx < ctx.FW / 2
        dots = ((xx % 3 == 1) & (yy % 3 == 1)) | ((xx % 3 == 2) & (yy % 3 == 2) & ((xx // 3 + yy // 3) % 2 == 0))
        hue = np.where(left, 0.0, 0.5) + ctx.diag / 50 + ph
        a = tint(a, bow(hue, 0.65), 0.2 + 0.4 * dots)
        a = add(a, WHITE, 0.12 * dots)
        if p is not None:
            d = ctx.diag - (-10 + p * (ctx.span + 20))
            a = add(a, WHITE, 0.35 * gauss(d, 3))
            gloss = 0.3 * gauss(d, 3)
        mid = ctx.FW // 2
        draw_frame(ctx, a, "silver", 2, p, {"frame_col": (0.7, 0.62, 0.52)})
        a[:, mid - 1] *= 0.35
        a[:, mid] = mixc(a[:, mid], WHITE, 0.4)
    elif kind == "break":           # XY BREAK: trophy-gold 'square prism' foil, the art in gold
        a = ctx.scene_q("grid", 20, 1.0, 1.0)
        l = lumf(a)
        P = 6
        fu, fw = (xx / P) % 1 - 0.5, (yy / P) % 1 - 0.5
        face = np.where(np.abs(fu) >= np.abs(fw), np.where(fu < 0, 0, 2), np.where(fw < 0, 1, 3))
        lv = np.array([0.66, 0.56, 0.4, 0.3])[face] * 0.6 + 0.42 * l
        if p is not None:
            d = ctx.diag - (-10 + p * (ctx.span + 20))
            lv = lv + 0.3 * gauss(d, 3.5)
            gloss = 0.3 * gauss(d, 3)
        a = mixc(a, ramp_map(np.clip(lv, 0, 0.97), GOLD), 0.8)
        a = tint(a, bow(ctx.diag / 30 + ph), 0.12)
        draw_frame(ctx, a, "silver", 3, p, {"frame_col": (0.78, 0.8, 0.84)})
    elif kind == "prime":           # HGSS Prime: foil on BOTH frame and art, spiked art-window edge
        a = ctx.scene_q("grid", 20, 1.0, 0.86)
        band = np.sin(yy / 2.2 + 0.8 * np.sin(xx / 7) - ph * 2 * math.pi)
        a = tint(a, bow(yy / 30 + ph), 0.22 + 0.32 * (band > 0.5))
        a = add(a, WHITE, 0.08 * (band > 0.85))
        t = 3
        b = a.copy()
        draw_frame(ctx, b, "silver", t + 3, p, {"frame_col": (0.84, 0.84, 0.86), "frame_bow": 0.45})
        ed = ctx.edge_dist()
        along = np.where(np.minimum(yy, ctx.FH - 1 - yy) <= np.minimum(xx, ctx.FW - 1 - xx), xx, yy)
        tooth = 2 - np.abs(along % 4 - 2)                     # 0..2 spikes pointing into the art
        m = ed < t + tooth
        edge = m & ~(ed < t + tooth - 1)
        a = np.where(m[..., None], b, a)
        a[edge & (ed >= t)] *= 0.5
        a[ed == 0] *= 0.6
    else:
        raise ValueError(kind)
    return a, gloss


# ---------------- futuristic (chrome + energy-symbol burst)
ENERGY = [(0.3, 0.72, 0.3), (0.92, 0.3, 0.2), (0.25, 0.55, 0.95), (0.98, 0.85, 0.2), (0.7, 0.35, 0.8),
          (0.85, 0.5, 0.25), (0.2, 0.25, 0.3), (0.62, 0.66, 0.72)]


def fam_chrome(ctx, v, p):
    base = ctx.scene_q("grid", 24, 1.0, 1.0)
    l = lumf(base)
    l = np.clip((l - np.percentile(l, 2)) / max(1e-6, np.percentile(l, 98) - np.percentile(l, 2)), 0, 1)
    ph = 0.0 if p is None else p
    xx, yy = ctx.xx, ctx.yy
    refl = np.sin(yy / 3.2 + 2.2 * np.sin(xx / 9) + 2 * math.pi * ph)       # liquid-metal reflections
    lv = 0.18 + 0.55 * l + 0.2 * refl
    a = ramp_map(np.clip(lv, 0, 0.97), PLATINUM)
    a = tint(a, np.where((refl > 0)[..., None], np.array((0.3, 0.95, 1.0)), np.array((1.0, 0.35, 0.85))),
             0.35 * np.abs(refl))
    # a burst of energy-symbol discs flying out from behind the Pokemon
    rnd = random.Random(30)
    R = ctx.span * 0.42
    for i in range(46):
        t = rnd.uniform(-math.pi, math.pi)
        r0 = rnd.uniform(0.25, 1.0)
        r = (r0 + (0 if p is None else p * 0.12)) % 1.0 * R + 6
        x, y = ctx.cx + r * math.cos(t), ctx.cy + r * math.sin(t) * 0.85
        rr = 0.8 + 1.4 * (r / R)
        d = np.hypot(xx - x, yy - y)
        col = np.array(ENERGY[i % len(ENERGY)])
        a = np.where((d < rr + 0.7)[..., None] & ~(d < rr)[..., None], a * 0.3, a)
        a = np.where((d < rr)[..., None], mixc(np.broadcast_to(col, a.shape), WHITE, 0.25 * (d < rr * 0.4)), a)
    gloss = None
    if p is not None:
        dd = ctx.diag - (-10 + p * (ctx.span + 20))
        a = add(a, WHITE, 0.4 * gauss(dd, 2.5))
        gloss = 0.35 * gauss(dd, 3)
    draw_frame(ctx, a, v.get("frame"), v.get("t", 2), p, v)
    return a, gloss


# ---------------- mega attack rare (pop art)
def fam_popart(ctx, v, p):
    a = ctx.scene_q("grid", 6, 1.8, 1.15, halo=False)
    ph = 0.0 if p is None else p
    xx, yy = ctx.xx, ctx.yy
    # ink lines between the flat colour areas
    l = lumf(a)
    edge = (np.abs(np.diff(l, axis=0, prepend=l[:1])) > 0.04) | (np.abs(np.diff(l, axis=1, prepend=l[:, :1])) > 0.04)
    # halftone: dots every 3 px, sized by darkness
    dot = ((xx % 3 == 1) & (yy % 3 == 1)) | (((xx % 3 == 1) ^ (yy % 3 == 1)) & (l < 0.35)
                                             & ((xx % 3 != 0) & (yy % 3 != 0)))
    a = np.where(dot[..., None], mixc(a, np.array((1.0, 0.2, 0.6)), 0.55), a)
    # comic action lines radiating from the Pokemon
    rays = np.cos(28 * ctx.th + 2 * math.pi * ph) > 0.8
    a = np.where((rays & (ctx.dist > 3) & (ctx.r > 10))[..., None], mixc(a, np.array((1.0, 0.98, 0.7)), 0.7), a)
    a = np.where(edge[..., None], np.array((0.06, 0.04, 0.1)), a)
    a = tint(a, bow(ctx.diag / 40 + ph), 0.12)
    gloss = None
    if p is not None:
        dd = ctx.diag - (-10 + p * (ctx.span + 20))
        a = add(a, WHITE, 0.35 * gauss(dd, 3))
        gloss = 0.3 * gauss(dd, 3)
    return a, gloss


# ---------------- black white rare (monochrome, colour only in the holo)
def fam_mono(ctx, v, p):
    base = ctx.scene_q("grid", 24, 1.0, 1.0)
    l = lumf(base)
    l = np.clip((l - np.percentile(l, 2)) / max(1e-6, np.percentile(l, 98) - np.percentile(l, 2)), 0, 1)
    ph = 0.0 if p is None else p
    gy_, gx_ = np.gradient(ndimage.gaussian_filter(l, 1.4))
    emb = np.clip(gx_ + 1.3 * gy_, -0.12, 0.12)
    if v["tone"] == "black":
        g = 0.08 + 0.42 * l + 1.6 * emb
        a = np.repeat(np.clip(g, 0, 1)[..., None], 3, -1)
        holo = gauss(ctx.diag - (0.35 * ctx.span if p is None else -10 + p * (ctx.span + 20)), 9)
        a = tint(a, bow(ctx.diag / 22 + ph), 0.55 * holo * (g > 0.2))
        a = add(a, WHITE, 0.12 * holo * (g > 0.3))
    else:
        g = 0.68 + 0.28 * l + 1.8 * emb
        a = np.repeat(np.clip(g, 0, 1)[..., None], 3, -1)
        holo = gauss(ctx.diag - (0.35 * ctx.span if p is None else -10 + p * (ctx.span + 20)), 9)
        a = tint(a, bow(ctx.diag / 22 + ph, 0.7), 0.04 + 0.28 * holo, lift=-0.02, gain=0.98)
    gloss = None if p is None else 0.25 * holo
    draw_frame(ctx, a, "plain", 2, p, {"frame_col": (0.1, 0.1, 0.11) if v["tone"] == "black" else (0.97, 0.97, 0.98)})
    return a, gloss



FAMILIES = {"nofoil": fam_nofoil, "reverse": fam_reverse, "holo": fam_holo, "vbeam": fam_vbeam,
            "etched": fam_etched, "sir": fam_sir, "gold": fam_gold, "rainbow": fam_rainbow, "shiny": fam_shiny,
            "radiant": fam_radiant, "amazing": fam_amazing, "prism": fam_prism, "oldera": fam_oldera,
            "chrome": fam_chrome, "popart": fam_popart, "mono": fam_mono}

# frames drawn by the wrapper (families that don't draw their own)
WRAP_FRAME = {"nofoil"}

# =============================================================== recipes
YELLOW = (0.95, 0.83, 0.32)
GREY = (0.80, 0.80, 0.78)
S = lambda *xs: [tuple(x.split(":")) for x in xs]  # noqa: E731  "star:black" -> ("star", "black")

RECIPES = {
    "bare_common": dict(fam="bare"),        # user rule: Common never gets a background
    # --- no foil: frame + symbol only
    "nofoil_uncommon": dict(fam="nofoil", scene=("chunky", 12, 0.8, 0.84), frame="plain", t=2, sym=S("diamond:black")),
    "nofoil_rare": dict(fam="nofoil", scene=("grid", 16, 0.9, 0.9), frame="plain", t=3, lamp=True, sym=S("star:black")),
    # --- reverse: foil outside the art
    "reverse_classic": dict(fam="reverse", pattern="classic", t=5, sym=S("circle:black")),
    "reverse_fireworks": dict(fam="reverse", pattern="fireworks", t=5, sym=S("circle:black")),
    "reverse_pokeball": dict(fam="reverse", pattern="poke", t=5, sym=S("circle:black")),
    "reverse_masterball": dict(fam="reverse", pattern="master", t=5, sym=S("circle:black")),
    # --- holo in the art window (matte frame; yellow up to SWSH, grey-silver from SV)
    "holo_starlight": dict(fam="holo", pattern="galaxy", frame="plain", frame_col=YELLOW, t=3, sym=S("star:black")),
    "holo_cosmos": dict(fam="holo", pattern="cosmos", frame="plain", frame_col=YELLOW, t=3, sym=S("star:black")),
    "holo_swirl": dict(fam="holo", pattern="swirl", frame="plain", frame_col=YELLOW, t=3, sym=S("star:black")),
    "holo_tinsel": dict(fam="holo", pattern="tinsel", frame="plain", frame_col=YELLOW, t=3, sym=S("star:black")),
    "holo_mirror": dict(fam="holo", pattern="mirror", frame="plain", frame_col=YELLOW, t=3, sym=S("star:black")),
    "holo_waterweb": dict(fam="holo", pattern="waterweb", frame="plain", frame_col=YELLOW, t=3, sym=S("star:black")),
    "holo_stripes": dict(fam="holo", pattern="stripes", frame="plain", frame_col=YELLOW, t=3, sym=S("star:black")),
    "holo_wave": dict(fam="holo", pattern="wave", frame="plain", frame_col=GREY, t=3, sym=S("star:black")),
    "holo_crackedice": dict(fam="holo", pattern="crackedice", frame="plain", frame_col=YELLOW, t=3, sym=S("star:black")),
    "holo_crosshatch": dict(fam="holo", pattern="crosshatch", frame="plain", frame_col=YELLOW, t=3, sym=S("star:black")),
    "holo_classic_collection": dict(fam="holo", pattern="cosmos", frame="plain", frame_col=(0.98, 0.88, 0.42), t=3,
                                    foil=1.3, sat=0.72, seed=25, scene=("grid", 20, 1.05, 0.9), sym=S("star:black")),
    "holo_promo": dict(fam="holo", pattern="swirl", frame="plain", frame_col=(0.86, 0.86, 0.88), t=3, foil=1.2,
                       sym=S("star:black")),
    "holo_radiant_collection": dict(fam="holo", pattern="cosmos", whole=True, frame="plain", frame_col=YELLOW, t=2,
                                    foil=1.15, seed=40, scene=("grid", 20, 1.05, 0.95), sym=S("star:black")),
    "holo_pikachu_fireworks": dict(fam="holo", pattern="fireworks", frame=None, seed=30,
                                   scene=("grid", 24, 1.05, 0.9), sym=S("star:gold")),
    # --- V family: framed + diagonal rainbow beams
    "vbeam_ex_old": dict(fam="vbeam", tex="ex", beam_w=6, second=0.0, frame_glitter=True, sym=S("star:black")),
    "vbeam_ex_bw": dict(fam="vbeam", tex="ex_bw", beam_w=7, second=0.5, frame="plain", frame_col=YELLOW,
                        sym=S("star:black")),
    "vbeam_gx": dict(fam="vbeam", tex="gx", beam_w=8, second=0.6, frame="plain", frame_col=YELLOW, sym=S("star:black")),
    "vbeam_v": dict(fam="vbeam", tex="v", beam_w=9, sym=S("star:black")),
    "vbeam_vmax": dict(fam="vbeam", tex="vmax", beam_w=13, beam=0.7, frame_col=(0.6, 0.62, 0.68), t=4,
                       sym=S("star:black")),
    "vbeam_vstar": dict(fam="vbeam", tex="vstar", beam_w=10, gold_beam=True, frame_col=(0.9, 0.86, 0.74),
                        sym=S("star:black")),
    "vbeam_ex_sv": dict(fam="vbeam", tex="ex_sv", beam_w=9, sym=S("star:black", "star:black")),
    # --- old-era specials
    "old_lvx": dict(fam="oldera", kind="lvx", sym=S("star:black")),
    "old_prime": dict(fam="oldera", kind="prime", sym=S("star:black")),
    "old_legend": dict(fam="oldera", kind="legend", sym=S("star:black")),
    "old_break": dict(fam="oldera", kind="break", sym=S("star:black")),
    # --- prism / crystal / star / ace
    "shiny_shining": dict(fam="shiny", gloss_col="pearl", kind="shining", frame="plain", frame_col=YELLOW, t=3, glitter=0.02, stars=5,
                          spark=SPARK, sym=S("star:black")),
    "prism_goldstar": dict(fam="holo", pattern="cosmos", frame="plain", frame_col=YELLOW, t=3, seed=77, foil=0.9,
                           sym=S("star:black")),
    "prism_crystal": dict(fam="prism", kind="crystal", frame="plain", frame_col=YELLOW, facets=46, seed=12,
                          stars=3, sat=0.55, sym=S("star:black")),
    "prism_star": dict(fam="prism", kind="prism", frame="plain", frame_col=(0.1, 0.1, 0.12), facets=40, whole=False, foil=1.3, stars=8,
                       sym=S("star:black")),
    "prism_ace_bw": dict(fam="prism", kind="ace", facets=70, seed=9, whole=False, foil=0.7, stars=3,
                         frame_col=(0.82, 0.8, 0.84), sym=S("star:black")),
    "prism_ace_sv": dict(fam="prism", kind="ace", facets=34, seed=31, frame_col=(0.9, 0.8, 0.88), stars=4,
                         spark=PEARL_SPARK, sym=S("star:pink")),
    # --- shiny
    "shiny_vault": dict(fam="shiny", gloss_col="pearl", kind="vault", frame="silver", t=3, glitter=0.09, sym=S("star:black")),
    "shiny_vault_gx": dict(fam="shiny", gloss_col="pearl", kind="gx", frame=None, glitter=0.1, stars=7, sym=S("star:black")),
    "shiny_sv": dict(fam="shiny", gloss_col="pearl", kind="sv", frame="silver", t=3, glitter=0.07, stars=5, spark=GOLD_SPARK,
                     sym=S("spark:gold")),
    "shiny_sv_ultra": dict(fam="shiny", gloss_col="pearl", kind="sur", frame=None, glitter=0.12, stars=8, spark=PEARL_SPARK,
                           sym=S("spark:gold", "spark:gold")),
    # --- specials
    "amazing_splash": dict(fam="amazing", frame_col=YELLOW, sym=S("star:black")),
    "radiant_burst": dict(fam="radiant", t=2, sym=S("star:black")),
    # --- etched full art
    "etched_gallery": dict(fam="etched", mode="tg", line=0.11, period=3.0, glitter=0.03, seed=3, sym=S("star:black")),
    "etched_chr_jp": dict(fam="etched", mode="tg", line=0.14, period=2.6, glitter=0.02, seed=6, amp=2.4,
                          sym=S("star:black")),
    "etched_ultra": dict(fam="etched", mode="ur", line=0.11, period=2.6, sym=S("star:silver", "star:silver")),
    "etched_illustration": dict(fam="etched", mode="ir", line=0.06, period=4.0, amp=2.2, wave=0.6,
                                sym=S("star:gold")),
    # --- special illustration and the new ME / 30th specials
    "sir_altart": dict(fam="sir", sym=S("star:black")),
    "sir_special": dict(fam="sir", pearl=(0.83, 0.5), sat=1.25, glow=(1.0, 0.95, 0.8), gloss_col="pearl", sym=S("star:gold", "star:gold")),
    "sir_csr_jp": dict(fam="sir", pearl=(0.08, 0.95), glow=(1.0, 0.85, 0.7), sat=1.2, gloss_col="pearl",
                       sym=S("star:black")),
    "popart_mega_attack": dict(fam="popart", sym=S("star:pink", "star:mint")),
    "chrome_futuristic": dict(fam="chrome", frame=None, sym=S("star:cyan")),
    # --- rainbow
    "rainbow_rare": dict(fam="rainbow", sprite="rainbow", sym=S("star:black")),
    # --- gold and monochrome secrets
    "gold_engraved": dict(fam="gold", kind="engrave", glitter=0.025, stars=3, sym=S("star:black")),
    "gold_secret": dict(fam="gold", kind="studs", glitter=0.03, stars=3, sym=S("star:black")),
    "gold_hyper": dict(fam="gold", kind="hyper", glitter=0.045, sprite="gold", sym=S("star:gold", "star:gold", "star:gold")),
    "mono_black": dict(fam="mono", tone="black", sprite="grey", sym=S("star:grey")),
    "mono_white": dict(fam="mono", tone="white", sprite="grey", grey_tint=(1.0, 1.0, 1.04), sym=S("star:grey")),
    "gold_mega_hyper": dict(fam="gold", kind="mono", ramp=GOLD, glitter=0.06, stars=5, sprite="gold",
                            sym=S("star:gold", "star:gold", "star:gold")),
}

SHINY_RECIPES = {"shiny_vault", "shiny_vault_gx", "shiny_sv", "shiny_sv_ultra", "shiny_shining", "radiant_burst",
                 "prism_goldstar"}


# =============================================================== apply
@dataclass
class Result:
    rid: str
    recipe: str
    frames: list
    shiny: bool
    notes: str = ""
    meta: dict = field(default_factory=dict)
    alpha: object = None          # bool (H, W): False = transparent (no background at all: Common)

    @property
    def static(self):
        return self.frames[-1]

    def rows(self, i=None):
        fr = self.frames if i is None else [self.frames[i]]
        al = self.alpha
        out = [[[tuple(int(c) for c in px) if al is None or al[y, x] else None for x, px in enumerate(row)]
                for y, row in enumerate(f)] for f in fr]
        return out if i is None else out[0]


_RARITIES = None


def rarities():
    global _RARITIES
    if _RARITIES is None:
        import json
        _RARITIES = {r["id"]: r for r in json.loads((HERE / "rarities.json").read_text(encoding="utf-8"))["rarities"]}
    return _RARITIES


def sprite_rgb(ctx, v, p, shiny):
    """the sprite's colours for this frame. Default: the colorscripts palette untouched. Some top rarities
    recolour it the way the real card does -- always keeping the black outline, the dark eye pixels and
    the whites, so shape and eyes read:
      rainbow  luminance-preserving pastel rainbow flowing across the body, in sync with the foil
      gold     s3lib.gold_remap onto a long gold ramp (amber ramp for the shiny palette)
      grey     monochrome (Black White Rare)"""
    base = ctx.spr_rgb[shiny]
    mode = v.get("sprite")
    if not mode:
        return base
    key = ("spr", mode, shiny, v.get("ramp_name"))
    if mode in ("gold", "grey") and key in ctx._cache:
        return ctx._cache[key]
    lv = lumf(base)
    keep = ctx.outl | (lv < 0.22) | (lv > 0.93)              # outline, eyes / dark strokes, white highlights
    if mode == "rainbow":
        hue = rainbow_hue(ctx, p) + 0.08
        out = tint(base, bow(hue, 0.6), 0.72, lift=0.02, gain=1.05)
    elif mode == "gold":
        g = L.gold_ramp(GOLD, 24)
        pal, sh = L.gold_remap(ctx.spr, g, L.gold_ramp(AMBER, 24))
        src = sh if shiny else pal
        out = np.zeros_like(base)
        for (x, y), (Lr, k) in ctx.card.cells.items():
            out[y, x] = np.array(L.hexrgb(src[k])) / 255
        keep = ctx.outl
    elif mode == "grey":
        g = np.clip((lv - 0.5) * 1.15 + 0.5, 0, 1)
        out = np.repeat(g[..., None], 3, -1) * np.array(v.get("grey_tint", (1.0, 1.0, 1.02)))
    else:
        raise ValueError(mode)
    out = np.where(keep[..., None], base, np.clip(out, 0, 1))
    if mode in ("gold", "grey"):
        ctx._cache[key] = out
    return out


def render_frame(ctx, rc, p, shiny):
    v = RECIPES[rc]
    a, gloss = FAMILIES[v["fam"]](ctx, v, p)
    a = np.array(a, float)
    if v["fam"] in WRAP_FRAME:
        draw_frame(ctx, a, v.get("frame"), v.get("t", 3), p, v)
    if rc == "prism_goldstar":          # the Gold Star emblem (top-left of the art) + gold twinkles
        star7 = ["...#...", "...#...", "#######", ".#####.", "..###..", ".##.##.", "#.....#"]
        gx, gy = 5, 5
        on = {(gx + i, gy + j) for j, r in enumerate(star7) for i, ch in enumerate(r) if ch == "#"}
        rim_ = {(X + dx, Y + dy) for X, Y in on for dx in (-1, 0, 1) for dy in (-1, 0, 1)} - on
        for (X, Y) in rim_:
            if not ctx.fig[Y, X]:
                a[Y, X] = (0.25, 0.15, 0.02)
        for (X, Y) in on:
            if not ctx.fig[Y, X]:
                a[Y, X] = (1.0, 0.95, 0.6) if Y - gy < 3 else (1.0, 0.78, 0.2)
        pts = [(x, y, (i * 3) % N) for i, (x, y) in enumerate(ctx.spots(4, 57, gap=14, avoid=4))]
        twinkle(a, ctx, pts, p, GOLD_SPARK)
    mode = "dark" if v["fam"] == "gold" else "light"
    a = rim_lift(ctx, a, mode, 0.3 if mode == "light" else 0.45)
    draw_symbols(ctx, a, v.get("sym"))
    spr = sprite_rgb(ctx, v, p, shiny)
    if gloss is not None:
        g = np.clip(gloss, 0, 0.45) * (~ctx.outl)
        gc = v.get("gloss_col")
        if gc == "pearl":                                   # pearlescent sheen on the body (SIR, shiny)
            gc = hsv(0.83 - 0.35 * np.clip((ctx.diag % 24) / 24, 0, 1), 0.3, 1.0)
        spr = mixc(spr, WHITE if gc is None else np.asarray(gc, float), g)
    a = np.where(ctx.fig[..., None], spr, a)
    # 4-level steps keep the .anim palette small (as suite3's mix())
    return (np.clip(np.round(np.clip(a, 0, 1) * 255 / 4) * 4, 0, 255)).astype(np.uint8)


def apply(rarity_id, scene, sprite, off, shiny=None, ctx=None):
    """render a rarity (an id from rarities.json, or a recipe name) -> Result with 16 frames; frames[-1] is
    the static render (the frame play.ps1 rests on)"""
    rec = rarities().get(rarity_id, {}).get("recipe", rarity_id)
    if rec not in RECIPES:
        raise KeyError(f"unknown rarity/recipe {rarity_id!r}")
    if shiny is None:
        shiny = rec in SHINY_RECIPES
    if RECIPES[rec]["fam"] == "bare":                   # Common: the colorscripts sprite alone, nothing else
        spr = ctx.spr if ctx is not None else sprite
        H, W = 2 * spr.h, 2 * spr.w
        img = np.zeros((H, W, 3), np.uint8)
        alpha = np.zeros((H, W), bool)
        pal = spr.shiny if shiny else spr.pal
        for j, r in enumerate(spr.rows):
            for i, ch in enumerate(r):
                if ch != ".":
                    img[2 * j:2 * j + 2, 2 * i:2 * i + 2] = L.hexrgb(pal[ch])
                    alpha[2 * j:2 * j + 2, 2 * i:2 * i + 2] = True
        return Result(rarity_id, rec, [img.copy() for _ in range(N)], shiny, alpha=alpha)
    ctx = ctx or Ctx(scene, sprite, off)
    frames = [render_frame(ctx, rec, f / (N - 1), shiny) for f in range(N - 1)]
    frames.append(render_frame(ctx, rec, None, shiny))
    return Result(rarity_id, rec, frames, shiny)
