"""The four Pokemon x five tiers. Each builder returns an s3lib.Card: the UNMODIFIED colorscripts sprite
(flip only; gold tiers remap its palette) over a background whose resolution and colour budget
escalate with rarity:

  common      the bare sprite
  common_bg   the card's scene at SPRITE scale (1 bg px = 2x2 grid px), 8 muted colours
  holo        the scene at GRID scale (2x finer), ~8 scene colours x 3 foil bands + starlight + rim + sparkles
  fullart     the card painting at grid scale, near-truecolour (median cut ~160), smooth inpaint,
              focus halo, light rays / radial glow, vignette, rim
  gold / top  a fine etched gold foil at grid scale (engraved hatching, embossed facets, glints), glow;
              Charmander's top tier is the Dragon 98 confetti foil over its forest at full-art quality

No text or logos (V, ex, 25th stamp, energy, rarity star) are drawn: rarity is the frame + background.
TIERS[poke][tier]() -> Card, with card.meta = {card, label, ref, anim, ...}
"""
import math
import random

import numpy as np

import s3lib as L
from s3lib import Card, Sprite

RAMP = ["#1c0f03", "#3a2308", "#5c3a0e", "#83591a", "#ab7c28", "#d0a23c", "#ecc75e", "#fbe496", "#fffbea"]
RAMP_AMBER = ["#26100a", "#45200c", "#6a3412", "#94501c", "#bd6f28", "#e08f3a", "#f6b458", "#ffd996", "#fff4e4"]
RAMP_ELECTRUM = ["#1c1a04", "#35340a", "#535212", "#77781c", "#9fa42a", "#c3c83c", "#dfe462", "#f1f59c", "#fdffe8"]
RAMP_ROSE = ["#26120e", "#45241a", "#6a3a26", "#945636", "#bd7a4a", "#e0a066", "#f2c48a", "#ffe2bc", "#fff6ec"]
GOLD24 = L.gold_ramp(RAMP, 24)

SPARK_PAL = {"L": "#ffffff", "l": "#fff4b8", "j": "#9fe8ff"}
GOLD_SPARK = {"L": "#ffffff", "l": "#fde79c", "j": "#d8a83e"}
VAULT_SPARK = {"L": "#fffbe0", "l": "#f3dc7a", "j": "#c8a84a"}
FOIL_HUES = [(1.0, 0.45, 0.8), (1.0, 0.85, 0.3), (0.3, 0.9, 1.0)]


def meta(c, **kw):
    c.meta.update(kw)
    return c


def place(c, spr, maskname, x0, y0, S, off=None, dx=0, dy=0):
    A, B = off if off else L.anchor(maskname, x0, y0, S, spr, dx, dy)
    A = max(0, min(c.W - spr.w, A))
    B = max(0, min(c.H - spr.h, B))
    c.put_sprite(spr, A, B)
    return A, B


# ============================================================ tier recipes
def plain(spr, cardid, label, ref):
    c = Card(spr.w, spr.h)
    c.put_sprite(spr, 0, 0)
    return meta(c, card=cardid, label=label, ref=ref, anim=None, tier="common")


def common_scene(spr, ref, maskname, x0, y0, S, W, H, cardid, label, win=None, boxes=(), dx=0, dy=0, off=None,
                 ncol=8, sat=0.72, bright=0.8, cgrow=None, grow=6, seed=0):
    """sprite-scale (chunky) scene, 8 colours, desaturated + darkened into a plain backdrop"""
    rgb, _ = L.clean_card(ref, maskname, grow=grow, boxes=boxes, win=win,
                          cgrow=cgrow if cgrow is not None else dict(reach=30, tol=18))
    c = Card(W, H)
    place(c, spr, maskname, x0, y0, S, off, dx, dy)
    # area-average to sprite px, k-means, per-cell mode, orphan cleanup
    a = L.sample(rgb, x0, y0, S / 3, W * 3, H * 3, resample=L.Image.BOX)
    a = L.tone(a, sat=sat, bright=bright)
    _, lbl3, pal = L.kmeans_q(a, ncol, seed)
    lbl = np.zeros((H, W), int)
    for y in range(H):
        for x in range(W):
            v, n = np.unique(lbl3[y * 3:(y + 1) * 3, x * 3:(x + 1) * 3], return_counts=True)
            lbl[y, x] = v[n.argmax()]
    lbl = L.orphan_clean(lbl)
    # rim lift at sprite scale: bg px 4-touching the sprite outline that are too dark -> the nearest
    # lighter palette colour
    fig = c.fig_mask()[::2, ::2]
    outl = c.outline_mask()[::2, ::2]
    lums = np.array([L.lum(p * 255) for p in pal])
    light = [i for i in np.argsort(lums) if lums[i] >= 70]
    for y in range(H):
        for x in range(W):
            if fig[y, x] or lums[lbl[y, x]] >= 70 or not light:
                continue
            if any(0 <= x + ax < W and 0 <= y + ay < H and outl[y + ay, x + ax] for ax, ay in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                lbl[y, x] = light[0]
    q = pal[lbl]
    q = np.repeat(np.repeat(q, 2, 0), 2, 1)
    c.bg = q
    c.bgq = L.to8(q)
    return meta(c, card=cardid, label=label, ref=(ref, x0, y0, x0 + W * S, y0 + H * S), anim=None, tier="common_bg",
                S=S)


def holo_bands(FW, FH, period=7, slope=0.55, wave=1.2, seed=0):
    """static holo foil: diagonal rainbow bands (index 0..len(FOIL_HUES)-1) with a slight wave"""
    yy, xx = np.mgrid[0:FH, 0:FW]
    u = xx + yy / slope * 0.5 + wave * np.sin(yy / 3.1 + seed) + 0.7 * np.sin(xx / 5.3)
    return (np.floor(u / period).astype(int)) % len(FOIL_HUES)


def starlight(c, dens=0.035, seed=1, avoid=3):
    """cosmos / starlight specks: scattered grid px, away from the sprite"""
    rnd = random.Random(seed)
    d = c.dist()
    pts = []
    for y in range(c.FH):
        for x in range(c.FW):
            if d[y, x] > avoid and rnd.random() < dens:
                pts.append((x, y, rnd.random()))
    return pts


def holo_scene(spr, ref, maskname, x0, y0, S, W, H, cardid, label, win=None, boxes=(), dx=0, dy=0, off=None,
               ncol=8, sat=1.0, bright=0.86, foil=0.34, rim_amt=0.5, sparkles=(), cgrow=None, grow=5, seed=0,
               period=7, rgb=None, halo=True, star_dens=0.03, star_amt=0.55):
    """grid-scale scene, ncol colours, with a static rainbow foil (ncol x 4 band colours), starlight
    specks, a 1px light rim around the sprite, sparkles"""
    if rgb is None:
        rgb, _ = L.clean_card(ref, maskname, grow=grow, boxes=boxes, win=win,
                              cgrow=cgrow if cgrow is not None else dict(reach=24, tol=16))
    c = Card(W, H)
    place(c, spr, maskname, x0, y0, S, off, dx, dy)
    a = L.sample(rgb, x0, y0, S / 2, 2 * W, 2 * H, resample=L.Image.BOX)
    a = L.tone(a, sat=sat, bright=bright)
    if halo:
        a = L.focus_halo(c, a, radius=4, dark=0.82, soft=1.0)
    _, lbl, pal = L.kmeans_q(a, ncol, seed, ignore=c.fig_mask())
    lbl = L.orphan_clean(lbl, 1)
    # rim: bg cells touching the silhouette -> the palette colour closest to a lifted version of it
    d = c.dist()
    rimm = (d > 0) & (d <= 1.01)
    if rim_amt:
        for y, x in zip(*np.nonzero(rimm)):
            want = pal[lbl[y, x]] + (1 - pal[lbl[y, x]]) * rim_amt
            lbl[y, x] = int(np.argmin(np.linalg.norm(pal - want, axis=1)))
    band = holo_bands(c.FW, c.FH, period=period, seed=seed)
    hues = np.array(FOIL_HUES)
    base = pal[lbl]
    # 'colour' blend: each band re-tints the scene toward its hue at the scene's own luminance, plus a
    # slight lift -- the rainbow reads as foil without washing the scene out
    w = np.array([0.2126, 0.7152, 0.0722])
    lb = (base @ w)[..., None]
    hb = hues[band]
    tint = np.clip(hb / (hb @ w)[..., None] * lb * 1.08 + 0.03, 0, 1)
    q = base + (tint - base) * foil
    for x, y, r in starlight(c, star_dens, seed + 3):
        q[y, x] = (1.0, 0.99, 0.93) if r >= 0.75 else (0.8, 0.9, 1.0)
    c.bg = q
    c.bgq = L.to8(q)
    for x, y, st in sparkles:
        L.sparkle(c, x, y, st, SPARK_PAL)
    return meta(c, card=cardid, label=label, ref=(ref, x0, y0, x0 + W * S, y0 + H * S), anim="holo", tier="holo",
                S=S, stars=list(sparkles), foil=foil)


def fullart_scene(spr, rgb, x0, y0, S, W, H, cardid, label, ref, maskname=None, off=None, dx=0, dy=0,
                  sat=1.12, bright=1.0, glow=(1.0, 0.92, 0.7), glow_r=None, glow_s=0.42, rays=12, ray_amt=0.55,
                  vig=0.55, halo_dark=0.72, ncol=160, rim_amt=0.32, sparkles=(), gamma=1.0, spark_pal=None,
                  vig_tint=None):
    """grid-scale painting, near-truecolour, focus halo + glow/rays behind the sprite + vignette + rim"""
    c = Card(W, H)
    place(c, spr, maskname, x0, y0, S, off, dx, dy)
    a = L.sample(rgb, x0, y0, S / 2, 2 * W, 2 * H, resample=L.Image.LANCZOS)
    a = L.tone(a, sat=sat, bright=bright, gamma=gamma)
    a = L.focus_halo(c, a, radius=5, dark=halo_dark, soft=1.4)
    a = L.radial_glow(c, a, glow, glow_r or max(c.FW, c.FH) * 0.55, glow_s, rays=rays, ray_amt=ray_amt)
    a = L.vignette(a, vig, tint=vig_tint)
    L.finish(c, a, ncol, method="median")
    if rim_amt:
        c.bgq = L.rim(c, c.bgq, colour=tuple(0.55 + 0.45 * np.asarray(glow)), amt=rim_amt)
    for x, y, st in sparkles:
        L.sparkle(c, x, y, st, spark_pal or {"L": "#ffffff", "l": "#fff6d0", "j": "#ffd98a"})
    return meta(c, card=cardid, label=label, ref=(ref, x0, y0, x0 + W * S, y0 + H * S), anim="glint", tier="fullart",
                S=S, stars=list(sparkles))


# ---- gold foil ----------------------------------------------------------------------------------
def voronoi(FW, FH, n, seed):
    rnd = random.Random(seed)
    pts = np.array([(rnd.uniform(-2, FW + 2), rnd.uniform(-2, FH + 2)) for _ in range(n)])
    yy, xx = np.mgrid[0:FH, 0:FW]
    d = np.hypot(xx[..., None] + 0.5 - pts[:, 0], yy[..., None] + 0.5 - pts[:, 1])
    o = np.argsort(d, -1)
    ds = np.take_along_axis(d, o[..., :2], -1)
    return o[..., 0], ds[..., 1] - ds[..., 0], rnd


def emboss(h, light=(-1.0, -1.3)):
    """relief shading of a height map: + on slopes facing the light (top-left), - facing away"""
    gy, gx = np.gradient(h)
    return -(gx * light[0] + gy * light[1])


def gold_foil(c, height, hatch_src, ramp=GOLD24, lo=0.18, hi=0.62, relief=0.9, glow=0.45, glow_r=9,
              facets=None, seed=0, glints=40, glint_top=None):
    """fine etched gold, at grid resolution:
      height     float map 0..1 (the engraved relief: facets or the scene's luminance)
      hatch_src  0..1 'darkness' driving engraved hatching (denser/darker lines where darker)
    level = lo..hi from height, + emboss relief, - hatching, + a glow around the sprite, + glints;
    mapped onto the gold ramp (<= len(ramp) colours)."""
    FH, FW = height.shape
    yy, xx = np.mgrid[0:FH, 0:FW]
    lv = lo + (hi - lo) * height
    lv = lv + relief * emboss(height)
    # engraved hatching: 45-degree lines every 3 px where darker, cross-hatch where darkest
    h1 = ((xx - yy) % 3 == 0) & (hatch_src > 0.35)
    h2 = ((xx + yy) % 3 == 0) & (hatch_src > 0.68)
    h0 = ((xx - yy) % 4 == 0) & (hatch_src <= 0.35) & (hatch_src > 0.12)
    lv = lv - 0.07 * h1 - 0.07 * h2 - 0.04 * h0
    if facets is not None:
        lv = lv + facets
    d = c.dist()
    g = np.clip(1 - (d - 1) / glow_r, 0, 1) ** 1.5
    lv = lv + glow * g
    lv = lv - 0.16 * ((d > 0) & (d <= 1.01))        # a dark hairline just outside the outline: the sprite sits in
    rnd = random.Random(seed + 7)
    n = len(ramp)
    idx = np.clip(np.round(lv * (n - 1)), 0, n - 3).astype(int)
    top = glint_top or n - 1
    placed = []
    for _ in range(glints * 4):                      # glints: a bright px + dimmer arms, on the foil
        if len(placed) >= glints:
            break
        x, y = rnd.randrange(FW), rnd.randrange(FH)
        if d[y, x] < 3 or any(abs(x - a) + abs(y - b) < 8 for a, b in placed):
            continue
        placed.append((x, y))
        idx[y, x] = top
        for ax, ay in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if 0 <= x + ax < FW and 0 <= y + ay < FH:
                idx[y + ay, x + ax] = max(idx[y + ay, x + ax], top - 4)
    pal = np.array([L.hexrgb(h) for h in ramp], float) / 255
    q = pal[idx]
    c.bg = q
    c.bgq = L.to8(q)
    c.meta["gold_idx"] = idx
    return c


def pyramid_foil(FW, FH, P=7, sheen=0.12, seed=0):
    """embossed pyramid-stud lattice (diamonds, 45 degrees): each stud's four faces take four flat light
    levels (lit from the top-left), fine hatching engraved into the shadow faces, ridge highlights, and
    a broad diagonal sheen across the foil. -> (level map 0..1, hatch-free mask of lit faces)"""
    yy, xx = np.mgrid[0:FH, 0:FW].astype(float)
    u, v = (xx + yy) / P, (xx - yy) / P
    fu, fv = u - np.floor(u) - 0.5, v - np.floor(v) - 0.5
    face = np.where(np.abs(fu) >= np.abs(fv), np.where(fu < 0, 0, 3), np.where(fv > 0, 1, 2))
    lv = np.array([0.60, 0.47, 0.38, 0.28])[face]
    ridge = np.abs(np.abs(fu) - np.abs(fv)) < 0.5 / P
    lv = np.where(ridge & (face <= 1), lv + 0.08, lv)
    xi, yi = xx.astype(int), yy.astype(int)
    lv = lv - 0.05 * ((face == 3) & ((xi - yi) % 2 == 0)) - 0.04 * ((face == 2) & ((xi - yi) % 3 == 0))
    d = (xx + yy) / (FW + FH)
    lv = lv + sheen * np.exp(-((d - 0.38) / 0.12) ** 2) + 0.5 * sheen * np.exp(-((d - 0.72) / 0.06) ** 2)
    return lv, face


def guilloche_foil(c, period=3.0, lobes=9, amp=1.6, mode="rose", sheen=0.1):
    """engraved guilloche: fine concentric (rose) or wave lines cut into the gold, 1 grid px wide every
    `period` px, centred on the sprite so the engraving radiates from it; a broad sheen across"""
    FH, FW = c.FH, c.FW
    yy, xx = np.mgrid[0:FH, 0:FW].astype(float)
    cx, cy = L.fig_centre(c)
    r = np.hypot(xx - cx, yy - cy)
    th = np.arctan2(yy - cy, xx - cx)
    if mode == "rose":
        u = r + amp * np.sin(lobes * th + r / 6.0)
    else:                                   # waves
        u = yy + amp * np.sin(xx / 4.0 + yy / 9.0) + 0.6 * amp * np.sin(xx / 1.9 - yy / 5.0)
    f = (u / period) % 1.0
    lv = 0.44 - 0.12 * (f < 1 / period) + 0.05 * ((f > 0.45) & (f < 0.45 + 1 / period))
    d = (xx + yy) / (FW + FH)
    lv = lv + sheen * np.exp(-((d - 0.3) / 0.1) ** 2) + sheen * 0.7 * np.exp(-((d - 0.75) / 0.07) ** 2) - 0.06
    return lv


def facet_height(FW, FH, n=60, seed=11, groove=0.9):
    """crystal facets: each Voronoi cell a tilted plane (lit by its normal), grooved seams"""
    lbl, gap, rnd = voronoi(FW, FH, n, seed)
    yy, xx = np.mgrid[0:FH, 0:FW]
    tilt = np.array([(rnd.uniform(-0.012, 0.012), rnd.uniform(-0.012, 0.012), rnd.uniform(0.15, 0.85)) for _ in range(n)])
    h = tilt[lbl, 2] + tilt[lbl, 0] * (xx - FW / 2) + tilt[lbl, 1] * (yy - FH / 2)
    seam = gap < groove
    h = np.where(seam, h - 0.25, h)
    return np.clip(h, 0, 1), seam, lbl


# ============================================================ Pikachu
PIKA = lambda flip=False: Sprite("pikachu", flip)  # noqa: E731
BASE1_WIN = (66, 100, 534, 418)       # Base Set art window (card px)


def pika_common():
    return plain(PIKA(), "base1-58", "common: Base Set 58/102", ("pikachu/ref/base1_58",) + BASE1_WIN)


def pika_common_bg():
    return common_scene(PIKA(), "pikachu/ref/base1_58", "pikachu_common", 66, 100, 13, 36, 24, "base1-58",
                        "common+scene: Base Set 58/102 forest", win=BASE1_WIN)


def pika_holo():
    return holo_scene(PIKA(), "pikachu/ref/cel25_5", "pikachu_holo", 26, 96, 22, 32, 27, "cel25-5",
                      "holo: Celebrations 005/025 forest",
                      boxes=((10, 440, 200, 580), (230, 620, 380, 700), (530, 620, 640, 700)),
                      win=(30, 0, 704, 1024), dx=3, bright=0.9,
                      sparkles=[(6, 6, 3), (9, 30, 2), (54, 10, 3), (58, 44, 2), (22, 49, 2)])


# Pikachu V fills the whole card: there is no scene around a sprite-sized Pikachu. The full art is a
# tight crop of the card's own pink lightning field -- the clean patch between the ears, at 2 card px per grid px --
# around the sprite, so nothing is inpainted at all.
PV_PATCH = (204, 100, 372, 206)


def lightning_field():
    rgb = L.card_img("pikachu/ref/swsh4_170")
    a, b, cc, d = PV_PATCH
    p = rgb[b:d, a:cc]
    # the bolts are thick pale-cream bands: warm them to electric yellow
    mn = p.min(-1)
    from scipy import ndimage
    hot = np.clip((mn - 0.6) / 0.2, 0, 1)
    edge = np.clip(ndimage.gaussian_filter(hot, 2.5) * 1.8 - hot, 0, 1)
    p = L.tone(p, sat=1.25, bright=1.0)
    p = L.lerp(p, (1.0, 0.72, 0.25), edge * 0.5)
    p = L.lerp(p, (1.0, 0.96, 0.5), hot * 0.85)
    return p


def pika_fullart():
    spr = PIKA()
    W, H = 32, 26
    f = lightning_field()
    return fullart_scene(spr, f, 20, 0, 4.0, W, H, "swsh4-170", "full art: Pikachu V swsh4 170 (lightning field)",
                         "pikachu/ref/swsh4_170", off=((W - spr.w) // 2, H - spr.h - 2), sat=1.05, glow=(1, 0.95, 0.7),
                         glow_s=0.3, rays=14, vig=0.5, halo_dark=0.8, vig_tint=(0.35, 0.0, 0.15),
                         sparkles=[(5, 5, 3), (58, 8, 2), (8, 42, 2), (57, 40, 3)])


# ---- gold: Pikachu ex sv8/247, sprite flipped (tail left like the card) + crown overlay
GW, GH = 33, 27
G_OFF = (6, 6)
GOLD_SPECIAL = {"#f66252": "#e8894a"}         # cheeks: rose-copper so the face still reads
STAR4 = ["..k..", ".kRk.", "kRRQk", ".kQk.", "..k.."]
STAR_BIG = ["..k..", ".kLk.", "kLLLk", ".kLk.", "..k.."]
STAR_PAL = {"R": "#e8283a", "Q": "#8e1420", "T": "#2a8a9a", "t": "#16505a", "L": "#fff4b0", "l": "#e8b83c",
            "k": "#000000"}
G_STARS = [(STAR4, 28, 14), ([r.replace("R", "T").replace("Q", "t") for r in STAR4], 28, 21)]
G_SPARKS = [(6, 8, 3), (58, 6, 3), (5, 44, 3), (14, 26, 2), (46, 50, 2), (62, 26, 1)]


def pika_gold(crown="rainbow"):
    import crowns
    spr = PIKA(flip=True)
    c = Card(GW, GH)
    gpal, gshiny = L.gold_remap(spr, L.gold_ramp(RAMP, 24), L.gold_ramp(RAMP_AMBER, 24), GOLD_SPECIAL)
    c.put_sprite(spr, *G_OFF, gpal, gshiny)
    if crown:
        rows, pal = crowns.CROWNS[crown]
        cx, cy = crowns.anchor(crown)
        c.put("over", rows, G_OFF[0] + cx, G_OFF[1] + cy, pal)
    for shape, x, y in G_STARS:
        c.put("deco", shape, x, y, STAR_PAL)
    for x, y, st in G_SPARKS:
        L.sparkle(c, x, y, st, GOLD_SPARK)
    lv, face = pyramid_foil(c.FW, c.FH, P=10)
    gold_foil(c, np.zeros_like(lv), np.zeros_like(lv), lo=0.0, hi=0.0, relief=0.0, glow=0.24, glow_r=8, seed=247,
              facets=lv - 0.1, glints=14)
    return meta(c, card="sv8-247", label="gold: Pikachu ex sv8 247 (+Tera crown)", tier="gold",
                ref=("pikachu/ref/sv8_247", 20, 160, 20 + GW * 21, 160 + GH * 21), anim="gold", crown=crown)


# ============================================================ Charmander
CHAR = lambda flip=False: Sprite("charmander", flip)  # noqa: E731


def char_common():
    return plain(CHAR(), "base1-46", "common: Base Set 46/102", ("charmander/ref/base1_46",) + BASE1_WIN)


def char_common_bg():
    return common_scene(CHAR(flip=True), "charmander/ref/base1_46", "charmander_common", 66, 100, 14, 33, 22,
                        "base1-46", "common+scene: Base Set 46/102 meadow", win=BASE1_WIN, boxes=((452, 150, 534, 418),),
                        cgrow=dict(reach=40, tol=22), grow=8)


# Shiny Vault: Charmander on white with pale-gold vault stars; holo = that white field at grid scale with
# the rainbow foil and the vault stars redrawn as sparkles at the card's positions
SV6_X0, SV6_Y0, SV6_S, SV6_W, SV6_H = 62, 100, 18, 34, 21
SV6_STARS_CARD = [(118, 222, 3), (228, 428, 2), (590, 160, 3), (612, 252, 2), (598, 385, 3),
                  (350, 125, 1), (470, 440, 1), (95, 140, 1)]


def char_holo():
    spr = CHAR(flip=True)
    W, H = SV6_W, SV6_H
    stars = [(round((x - SV6_X0) / SV6_S * 2), round((y - SV6_Y0) / SV6_S * 2), st) for x, y, st in SV6_STARS_CARD]
    white = np.ones((1024, 734, 3)) * np.array([0.985, 0.972, 0.93])
    c = holo_scene(spr, "charmander/ref/sma_SV6", "charmander_holo", SV6_X0, SV6_Y0, SV6_S, W, H, "sma-SV6",
                   "holo: Hidden Fates SV6 (shiny vault)", rgb=white, ncol=2, foil=0.3, rim_amt=0, halo=False,
                   period=6, star_dens=0.05, star_amt=0.9, bright=1.0)
    c.bgq = L.rim(c, c.bgq, colour=(0.95, 0.8, 0.45), amt=0.35)
    for x, y, st in stars:
        L.sparkle(c, x, y, st, VAULT_SPARK)
    c.meta["stars"] = stars
    return c


def char_fullart():
    spr = CHAR(flip=True)
    rgb, _ = L.clean_card("charmander/ref/sv3pt5_168", "charmander_fullart", grow=4)
    return fullart_scene(spr, rgb, 34, 95, 16, 36, 28, "sv3pt5-168", "full art: 151 IR 168/165 canyon",
                         "charmander/ref/sv3pt5_168", maskname="charmander_fullart", dy=1, sat=1.2,
                         glow=(1.0, 0.75, 0.45), rays=10, sparkles=[(64, 6, 2), (6, 10, 2)])


CONFETTI = ["#6fe3d2", "#f4d35e", "#f59ab0", "#e9f6ff", "#9be07a", "#b69cff", "#ffb86b"]


def char_top():
    """Dragon 98/97: confetti-foil secret rare, not gold -> unmodified sprite over its forest at full-art
    quality, with a fine multi-colour confetti foil + cosmos swirl over it"""
    spr = CHAR()
    W, H = 39, 24
    rgb, _ = L.clean_card("charmander/ref/ex3_98", "charmander_top", grow=5, win=(70, 106, 664, 466),
                          cgrow=dict(reach=20, tol=14))
    c = fullart_scene(spr, rgb, 70, 106, 15.2, W, H, "ex3-98", "top: EX Dragon 98/97 confetti secret rare",
                      "charmander/ref/ex3_98", maskname="charmander_top", sat=1.35, bright=1.0,
                      glow=(1.0, 0.72, 0.42), glow_s=0.55, rays=16, ray_amt=0.6, vig=0.5, ncol=140, rim_amt=0.35,
                      vig_tint=(0.02, 0.05, 0.14))
    # big soft confetti discs (the card's 2x2 / 3x3 translucent dots), blended into the scene
    rnd = random.Random(980)
    d = c.dist()
    q = c.bgq.astype(float) / 255
    for _ in range(26):
        x, y = rnd.randrange(c.FW), rnd.randrange(c.FH)
        if d[y, x] < 4:
            continue
        col = np.array(L.hexrgb(rnd.choice(CONFETTI))) / 255
        rr = rnd.choice((1.0, 1.0, 1.5))
        for yy in range(max(0, int(y - rr)), min(c.FH, int(y + rr) + 1)):
            for xx in range(max(0, int(x - rr)), min(c.FW, int(x + rr) + 1)):
                if (xx - x) ** 2 + (yy - y) ** 2 <= rr * rr and d[yy, xx] >= 2:
                    q[yy, xx] = q[yy, xx] + (col - q[yy, xx]) * 0.6
    c.bgq = L.to8(L.median_q(q, 170))
    # confetti: 1px dots and 2x1 flakes in the foil colours
    rnd = random.Random(98)
    d = c.dist()
    conf = []
    for y in range(c.FH):
        for x in range(c.FW):
            if d[y, x] < 2 or rnd.random() > 0.035:
                continue
            k = rnd.randrange(len(CONFETTI))
            cells = [(x, y)] + ([(x + 1, y)] if rnd.random() < 0.35 and x + 1 < c.FW and d[y, x + 1] >= 2 else [])
            for X, Y in cells:
                c.cells[(X, Y)] = ("deco", f"c{k}")
                conf.append((X, Y, k))
    c.pals.setdefault("deco", {}).update({f"c{i}": v for i, v in enumerate(CONFETTI)})
    for x, y, st in [(4, 4, 3), (73, 42, 3), (72, 5, 2), (5, 42, 2), (40, 3, 1)]:
        L.sparkle(c, x, y, st, {"L": "#ffffff", "l": "#e9f6ff", "j": "#6fe3d2"})
    c.meta.update(anim="confetti", tier="top", confetti=[p for p in conf if c.cells.get(p[:2], ("",))[0] == "deco"])
    return c


# ============================================================ Bulbasaur
BULB = lambda flip=False: Sprite("bulbasaur", flip)  # noqa: E731


def bulb_common():
    return plain(BULB(), "base1-44", "common: Base Set 44/102", ("bulbasaur/ref/base1_44",) + BASE1_WIN)


def bulb_common_bg():
    return common_scene(BULB(), "bulbasaur/ref/base1_44", "bulbasaur_common", 66, 100, 15, 31, 21, "base1-44",
                        "common+scene: Base Set 44/102 garden", win=BASE1_WIN)


def bulb_holo():
    """the Base Set garden as a holo: grid scale + foil (Base Set 44 has no holo print)"""
    return holo_scene(BULB(), "bulbasaur/ref/base1_44", "bulbasaur_common", 66, 100, 15, 31, 21, "base1-44*",
                      "holo (invented): Base Set 44/102 garden, holo foil", win=BASE1_WIN,
                      sparkles=[(4, 4, 3), (58, 6, 2), (56, 36, 3), (4, 34, 2)])


def bulb_fullart_rgb():
    rgb, _ = L.clean_card("bulbasaur/ref/sv3pt5_166", "bulbasaur_fullart", grow=5, cgrow=dict(reach=16, tol=12))
    return rgb


def bulb_fullart():
    return fullart_scene(BULB(), bulb_fullart_rgb(), 40, 92, 12, 38, 28, "sv3pt5-166", "full art: 151 IR 166/165 jungle",
                         "bulbasaur/ref/sv3pt5_166", maskname="bulbasaur_fullart", sat=1.1, glow=(1.0, 0.98, 0.72),
                         rays=12, sparkles=[(70, 6, 3), (6, 48, 2)])


def scene_gold(c, rgb, x0, y0, S, shiny_ramp, special=None, seed=0, guilloche=None):
    """invented gold: the full-art scene ENGRAVED into gold -- its luminance becomes the relief (embossed)
    and drives the hatching density, like the etched texture of a gold secret rare"""
    a = L.sample(rgb, x0, y0, S / 2, c.FW, c.FH, resample=L.Image.BOX)
    lum = (a @ np.array([0.2126, 0.7152, 0.0722]))
    lum = (lum - lum.min()) / max(1e-6, lum.max() - lum.min())
    from scipy import ndimage
    h = ndimage.gaussian_filter(lum, 0.7)
    h = np.clip((h - 0.15) / 0.75, 0, 1)
    spr = c.spr
    gpal, gshiny = L.gold_remap(spr, L.gold_ramp(RAMP, 24), L.gold_ramp(shiny_ramp, 24), special)
    c.put_sprite(spr, *c.off, gpal, gshiny)
    lv = guilloche_foil(c, **(guilloche or {}))
    # the scene shows through the engraving as a soft tone (etched artwork under the lines)
    gold_foil(c, np.zeros_like(h), np.zeros_like(h), lo=0.0, hi=0.0, relief=0.0, glow=0.34, glow_r=10, seed=seed,
              glints=8, facets=lv + 0.22 * (h - 0.5) - 0.04)
    return c


def bulb_gold():
    spr = BULB()
    c = Card(38, 28)
    place(c, spr, "bulbasaur_fullart", 40, 92, 12)
    scene_gold(c, bulb_fullart_rgb(), 40, 92, 12, RAMP_ELECTRUM, seed=44)
    return meta(c, card="invented", label="gold (invented): the jungle engraved in gold", anim="gold", tier="gold",
                ref=("bulbasaur/ref/sv3pt5_166", 40, 92, 40 + 38 * 12, 92 + 28 * 12))


# ============================================================ Squirtle
SQUI = lambda flip=False: Sprite("squirtle", flip)  # noqa: E731


def squi_common():
    return plain(SQUI(), "base1-63", "common: Base Set 63/102", ("squirtle/ref/base1_63",) + BASE1_WIN)


def squi_common_bg():
    return common_scene(SQUI(flip=True), "squirtle/ref/base1_63", "squirtle_common", 66, 100, 15, 31, 21, "base1-63",
                        "common+scene: Base Set 63/102 boulder", win=BASE1_WIN, dy=-1)


def squi_holo():
    return holo_scene(SQUI(flip=True), "squirtle/ref/base1_63", "squirtle_common", 66, 100, 15, 31, 21, "base1-63*",
                      "holo (invented): Base Set 63/102 boulder, holo foil", win=BASE1_WIN, dy=-1,
                      sparkles=[(4, 5, 3), (57, 36, 3), (6, 36, 2)])


SQ_X0, SQ_Y0, SQ_S, SQ_W, SQ_H = 40, 112, 16, 40, 30


def squi_fullart_rgb():
    rgb, _ = L.clean_card("squirtle/ref/sv3pt5_170", "squirtle_fullart", grow=5)
    return rgb


def squi_fullart():
    return fullart_scene(SQUI(), squi_fullart_rgb(), SQ_X0, SQ_Y0, SQ_S, SQ_W, SQ_H, "sv3pt5-170",
                         "full art: 151 IR 170/165 surf", "squirtle/ref/sv3pt5_170", maskname="squirtle_fullart",
                         dy=-2, sat=1.1, glow=(0.85, 1.0, 1.0), glow_s=0.35, rays=12, halo_dark=0.62,
                         sparkles=[(72, 6, 3), (6, 8, 2), (74, 50, 2)])


def squi_gold():
    spr = SQUI()
    c = Card(SQ_W, SQ_H)
    place(c, spr, "squirtle_fullart", SQ_X0, SQ_Y0, SQ_S, dy=-2)
    scene_gold(c, squi_fullart_rgb(), SQ_X0, SQ_Y0, SQ_S, RAMP_ROSE, seed=63, guilloche=dict(lobes=5, amp=0.7, period=3.4))
    return meta(c, card="invented", label="gold (invented): the surf engraved in gold", anim="gold", tier="gold",
                ref=("squirtle/ref/sv3pt5_170", SQ_X0, SQ_Y0, SQ_X0 + SQ_W * SQ_S, SQ_Y0 + SQ_H * SQ_S))


TIERS = {
    "pikachu": {"common": pika_common, "common_bg": pika_common_bg, "holo": pika_holo, "fullart": pika_fullart,
                "gold": pika_gold},
    "charmander": {"common": char_common, "common_bg": char_common_bg, "holo": char_holo, "fullart": char_fullart,
                   "top": char_top},
    "bulbasaur": {"common": bulb_common, "common_bg": bulb_common_bg, "holo": bulb_holo, "fullart": bulb_fullart,
                  "gold": bulb_gold},
    "squirtle": {"common": squi_common, "common_bg": squi_common_bg, "holo": squi_holo, "fullart": squi_fullart,
                 "gold": squi_gold},
}
