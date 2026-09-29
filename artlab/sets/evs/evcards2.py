"""Batch 2: one card for every Evolving Skies rarity not in batch 1 (evcards.py), each with the effect of its
real printed finish:

  swsh7-108 Shelgon         Uncommon        non-foil: sprite-scale scene, 12 colours (a notch finer than Common)
  swsh7-106 Altaria         Rare            non-foil: scene at grid scale (2x finer), 16 colours
  swsh7-49  Pikachu         Reverse Holo    (a Common's reverse-holo parallel print) the Common's art -- the plain
                                            sprite, commons get no background -- with rainbow foil ONLY outside it
  swsh7-109 Salamence       Rare Holo       holo INSIDE the art box: grid scene, rainbow foil bands, starlight
  swsh7-30  Vaporeon VMAX   Rare Holo VMAX  framed like the V but gunmetal and heavier, sunpillar stripes and a
                                            bold etched texture along the painting's own contours
  swsh7-226 Froslass        Rare Secret     gold: gold sprite remap, the scene engraved in faceted gold, glitter
"""
import numpy as np
from scipy import ndimage

import evlib as E
from evlib import L, Card, Sprite
from evcards import W_LUM, colour_blend, meta, place, rainbow_rgb, silver_frame

SWSH_WIN = (66, 106, 680, 476)              # the art window (inset past its frame line) of a SWSH common / uncommon / rare / holo
STAGE_BOX = (0, 58, 312, 136)               # stage icon + "Evolves from" bar overlapping the window's top-left
EDGES = ((0, 0, 30, 1024), (700, 0, 734, 1024))


def window_rgb(cid, boxes=(), grow=6, texture=True, tex_src=None):
    """the scan with the Pokemon + boxes painted out, and everything outside the art window replaced by a
    membrane of the window (the card's frame must not bleed in when the crop runs past the window)"""
    rgb, _ = E.clean(cid, grow=grow, boxes=boxes, texture=texture, tex_src=tex_src)
    a, b, cc, d = SWSH_WIN
    m = np.ones(rgb.shape[:2], bool)
    m[b:d, a:cc] = False
    return L.pushpull(rgb, ~m)


def matte(c, rgb, x0, y0, S, ncol, sat, bright, scale=2, seed=0):
    """non-foil scene: scale 2 = sprite scale (chunky, per-sprite-px mode of 3x3 samples), scale 1 = grid
    scale. k-means to ncol, orphan cleanup, a light rim where dark scenery touches the outline"""
    W, H = c.W, c.H
    if scale == 2:
        a = L.sample(rgb, x0, y0, S / 3, W * 3, H * 3, resample=L.Image.BOX)
        a = L.tone(a, sat=sat, bright=bright)
        _, lbl3, pal = L.kmeans_q(a, ncol, seed)
        lbl = np.zeros((H, W), int)
        for y in range(H):
            for x in range(W):
                v, n = np.unique(lbl3[y * 3:(y + 1) * 3, x * 3:(x + 1) * 3], return_counts=True)
                lbl[y, x] = v[n.argmax()]
        lbl = L.orphan_clean(lbl)
        fig = c.fig_mask()[::2, ::2]
        outl = c.outline_mask()[::2, ::2]
        GW, GH = W, H
    else:
        a = L.sample(rgb, x0, y0, S / 2, 2 * W, 2 * H, resample=L.Image.BOX)
        a = L.tone(a, sat=sat, bright=bright)
        _, lbl, pal = L.kmeans_q(a, ncol, seed, ignore=c.fig_mask())
        lbl = L.orphan_clean(lbl, 1)
        fig, outl = c.fig_mask(), c.outline_mask()
        GW, GH = 2 * W, 2 * H
    lums = np.array([L.lum(p * 255) for p in pal])
    light = [i for i in np.argsort(lums) if lums[i] >= 70]
    for y in range(GH):
        for x in range(GW):
            if fig[y, x] or lums[lbl[y, x]] >= 70 or not light:
                continue
            if any(0 <= x + ax < GW and 0 <= y + ay < GH and outl[y + ay, x + ax]
                   for ax, ay in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                lbl[y, x] = light[0]
    q = pal[lbl]
    if scale == 2:
        q = np.repeat(np.repeat(q, 2, 0), 2, 1)
    c.bg = q
    c.bgq = L.to8(q)
    return c


# ---- Uncommon: Shelgon 108
def shelgon():
    cid = "swsh7-108"
    x0, y0, S, W, H = 62, 100, 16, 39, 24
    rgb = window_rgb(cid, boxes=(STAGE_BOX,), texture=False)
    spr = Sprite("shelgon")
    c = Card(W, H)
    place(c, spr, cid, x0, y0, S, off=(4, H - spr.h - 1))
    matte(c, rgb, x0, y0, S, 12, sat=0.84, bright=0.88)
    return meta(c, card=cid, label="Uncommon: Shelgon 108/203, sky islands (non-foil)", rarity="Uncommon",
                finish="non-foil: sprite-scale scene, 12 colours", variant="uncommon", anim=None,
                ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S)


# ---- Rare: Altaria 106
def altaria():
    cid = "swsh7-106"
    x0, y0, S, W, H = 64, 94, 13.4, 46, 30
    rgb = window_rgb(cid, boxes=(STAGE_BOX,), grow=8, tex_src=(380, 300, 660, 470))
    spr = Sprite("altaria", flip=True)
    c = Card(W, H)
    place(c, spr, cid, x0, y0, S, off=(6, 0))
    matte(c, rgb, x0, y0, S, 16, sat=0.95, bright=0.95, scale=1)
    return meta(c, card=cid, label="Rare: Altaria 106/203, cloud sea (non-foil)", rarity="Rare",
                finish="non-foil: grid-scale scene, 16 colours", variant="rare", anim=None,
                ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S)


# ---- Reverse Holo: Pikachu 049 -- a Common's parallel print: the Common's art (the plain sprite, no background,
# per the commons rule) with the reverse-holo foil ONLY outside it, as a ring around the art
def reverse_ring(FW, FH, width=3, seed=0):
    """SWSH reverse holo foil: a smooth pastel rainbow sweep with a fine sparkle grain, `width` grid px wide.
    -> {(x, y): rgb 0..1} for the ring cells"""
    yy, xx = np.mgrid[0:FH, 0:FW]
    ring = (xx < width) | (yy < width) | (xx >= FW - width) | (yy >= FH - width)
    foil = rainbow_rgb((xx + yy) / 60.0 + 0.1, s=0.32, v=0.97)
    grain = np.random.default_rng(seed).random((FH, FW))
    foil = np.where((grain < 0.18)[..., None], np.clip(foil * 0.82, 0, 1), foil)
    foil = np.where((grain > 0.94)[..., None], 1.0, foil)
    return ring, foil


def pikachu():
    cid = "swsh7-49"
    spr = Sprite("pikachu")
    m = 2                                               # sprite-px gap between the art and the foil ring
    c = Card(spr.w + 2 * m, spr.h + 2 * m)
    c.put_sprite(spr, m, m)
    ring, foil = reverse_ring(c.FW, c.FH, width=3, seed=49)
    pal = {}
    for y, x in zip(*np.nonzero(ring)):
        k = L.rgbhex(np.round(foil[y, x] * 255))
        pal[k] = k
        c.cells[(int(x), int(y))] = ("frame", k)
    c.pals["frame"] = pal
    c.meta["ring"] = ring
    return meta(c, card=cid, label="Reverse Holo: Pikachu 049/203 (a Common's reverse-holo print): plain sprite, foil ring",
                rarity="Reverse Holo", finish="reverse holo: the Common's plain art, rainbow foil only outside it",
                variant="reverse-holo", anim="reverse", ref=(cid, 60, 100, 686, 482), S=None)


# ---- Rare Holo: Salamence 109 (suite3's holo recipe, inside the art box)
def salamence():
    import tiers as s3t
    cid = "swsh7-109"
    x0, y0, S, W, H = 64, 96, 13.2, 47, 30
    rgb = window_rgb(cid, boxes=(STAGE_BOX,), grow=5, tex_src=(596, 250, 676, 430))
    spr = Sprite("salamence", flip=True)
    off = (3, H - spr.h - 1)
    c = s3t.holo_scene(spr, cid, None, x0, y0, S, W, H, cid, "", off=off, rgb=rgb, ncol=12, foil=0.22, bright=1.0,
                       sparkles=[(5, 5, 3), (88, 6, 2), (86, 52, 3), (4, 50, 2)], seed=109)
    return meta(c, card=cid, label="Rare Holo: Salamence 109/203, crag in the clouds (holo in the art box)",
                rarity="Rare Holo", finish="SWSH rare holo: rainbow foil bands + starlight inside the art box",
                variant="rare-holo", anim="holo", ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S)


# ---- Rare Holo VMAX: Vaporeon VMAX 30
def vmax_texture(a, levels=7):
    """VMAX etched texture: grooves along the painting's own iso-luminance contours (1 px dark cut with a
    1 px highlight on its top-left side). Returns (textured image, groove mask)"""
    lum = ndimage.gaussian_filter(a @ W_LUM, 1.0)
    band = np.floor(lum * levels)
    groove = np.zeros(lum.shape, bool)
    groove[:, 1:] |= band[:, 1:] != band[:, :-1]
    groove[1:, :] |= band[1:, :] != band[:-1, :]
    hi = np.zeros_like(groove)
    hi[:-1, :-1] = groove[1:, 1:] & ~groove[:-1, :-1]
    out = a * np.where(groove, 0.78, 1.0)[..., None] + np.where(hi, 0.07, 0.0)[..., None]
    return np.clip(out, 0, 1), groove


GUNMETAL = ["#3a4048", "#566069", "#76818c", "#9ea8b2", "#c6ced6", "#eef2f5"]


def vaporeon():
    cid = "swsh7-30"
    x0, y0, S, W, H = 6, 72, 15.3, 46, 33
    boxes = EDGES + ((0, 0, 734, 74), (0, 28, 112, 152), (100, 72, 350, 140), (440, 84, 708, 164),
                     (0, 552, 734, 1024))
    rgb, _ = E.clean(cid, grow=5, boxes=boxes, tex_src=(20, 330, 180, 540))
    spr = Sprite("vaporeon", flip=True)
    c = Card(W, H)
    place(c, spr, cid, x0, y0, S, margin=2)
    a = L.sample(rgb, x0, y0, S / 2, 2 * W, 2 * H, resample=L.Image.BOX)
    a = L.tone(a, sat=1.25, bright=1.0)
    a = L.focus_halo(c, a, radius=3, dark=0.85, soft=1.0)
    _, lbl, pal = L.kmeans_q(a, 40, 0, ignore=c.fig_mask())
    base = pal[L.orphan_clean(lbl, 1)]
    base, groove = vmax_texture(base)
    FH, FW = c.FH, c.FW
    yy, xx = np.mgrid[0:FH, 0:FW]
    q = colour_blend(base, rainbow_rgb((xx * 0.9 + yy * 0.35) / 9.0, s=0.7), 0.14 + 0.1 * (base @ W_LUM))
    q = L.median_q(q, 110)
    d = c.dist()
    rim = (d > 0) & (d <= 1.01)
    q[rim] = q[rim] + (1 - q[rim]) * 0.45
    q = silver_frame(c, q, width=3, ramp_hex=GUNMETAL, groove=True)   # VMAX: gunmetal, grooved, heavier
    ring = c.meta["frame_ring"]
    c.bg = q
    c.bgq = L.to8(q)
    stars = [(9, 9, 3), (82, 8, 2), (84, 56, 3), (8, 58, 2)]
    for x, y, st in stars:
        L.sparkle(c, x, y, st, {"L": "#ffffff", "l": "#dff6ff", "j": "#8fd8ff"})
    return meta(c, card=cid, label="Rare Holo VMAX: Vaporeon VMAX 030/203, tidal swirl (gunmetal frame, etched holo)",
                rarity="Rare Holo VMAX", finish="SWSH VMAX holo: gunmetal frame, sunpillar stripes, bold etched contours",
                variant="rare-holo-vmax", anim="sunpillar", ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S,
                stars=stars, grooves=groove & ~ring)


# ---- Rare Secret (gold): Froslass 226
def froslass():
    import tiers as s3t
    cid = "swsh7-226"
    x0, y0, S, W, H = 47, 92, 20, 32, 33
    boxes = EDGES + ((0, 0, 734, 96), (0, 58, 330, 140), (0, 552, 734, 1024))
    rgb, _ = E.clean(cid, grow=5, boxes=boxes, texture=False)
    spr = Sprite("froslass")
    c = Card(W, H)
    place(c, spr, cid, x0, y0, S, margin=1)
    gpal, gshiny = L.gold_remap(spr, L.gold_ramp(s3t.RAMP, 24), L.gold_ramp(s3t.RAMP_AMBER, 24))
    c.put_sprite(spr, *c.off, gpal, gshiny)
    a = L.sample(rgb, x0, y0, S / 2, c.FW, c.FH, resample=L.Image.BOX)
    lum = a @ W_LUM
    lum = (lum - lum.min()) / max(1e-6, lum.max() - lum.min())
    h = np.clip((ndimage.gaussian_filter(lum, 0.8) - 0.1) / 0.8, 0, 1)
    fh, seam, _ = s3t.facet_height(c.FW, c.FH, n=70, seed=226)
    s3t.gold_foil(c, np.zeros_like(h), 1 - h, lo=0.0, hi=0.0, relief=0.0, glow=0.3, glow_r=9, seed=226,
                  glints=26, facets=0.34 + 0.22 * (h - 0.5) + 0.16 * (fh - 0.5) + 0.5 * s3t.emboss(fh) - 0.05 * seam)
    stars = [(6, 8, 3), (56, 6, 3), (58, 40, 3), (5, 46, 2), (30, 62, 2), (50, 22, 1)]
    for x, y, st in stars:
        L.sparkle(c, x, y, st, s3t.GOLD_SPARK)
    return meta(c, card=cid, label="Rare Secret: Froslass 226/203 gold (gold remap, faceted etched gold, glitter)",
                rarity="Rare Secret", finish="gold secret: gold sprite remap, crystalline etched gold, glitter",
                variant="rare-secret", anim="gold", ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S,
                stars=stars, sprite_recolour="gold")
