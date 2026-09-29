"""The five Evolving Skies cards. Each builder returns an s3lib.Card: the UNMODIFIED colorscripts sprite (flip
only) over the card's own scene with the real Pokemon painted out, finished with the foil of that card's real
printed rarity (the tier IS the printed rarity):

  swsh7-125 Eevee          Common       non-foil and NO background (user rule): the plain sprite
  swsh7-74  Sylveon V      Rare Holo V  SWSH regular V: grid-scale scene in a silver etched frame, the whole art
                                        window foiled with the V "sunpillar" rainbow stripes
  swsh7-174 Glaceon V      Rare Ultra   full-art V: full-bleed painting, near-truecolour, glow / rays / vignette,
                                        fingerprint-like etched line texture everywhere
  swsh7-215 Umbreon VMAX   Rare Rainbow (API field; the print is the alternate-art secret) textured painting:
                                        the illustration at full resolution, embossed along its own brushwork
  swsh7-204 Leafeon VMAX   Rare Rainbow rainbow secret: pastel rainbow gradient + dense etched line texture +
                                        glitter

No text or logos are drawn in the art. BUILDERS[id]() -> Card with card.meta = {card, label, rarity, finish,
anim, ...}.
"""
import math
import random

import numpy as np
from scipy import ndimage

import evlib as E
from evlib import L, Card, Sprite

W_LUM = np.array([0.2126, 0.7152, 0.0722])


def meta(c, **kw):
    c.meta.update(kw)
    return c


def place(c, spr, cid, x0, y0, S, off=None, dx=0, dy=0, margin=0):
    A, B = off if off else E.anchor(cid, x0, y0, S, spr, dx, dy)
    A = max(margin, min(c.W - spr.w - margin, A))
    B = max(margin, min(c.H - spr.h - margin, B))
    c.put_sprite(spr, A, B)
    return A, B


def rainbow_rgb(t, s=0.55, v=1.0):
    """continuous pastel rainbow, t array in turns -> (..., 3)"""
    from skimage.color import hsv2rgb
    t = np.asarray(t, float) % 1.0
    hsv = np.stack([t, np.full_like(t, s), np.full_like(t, v)], -1)
    return hsv2rgb(hsv)


def colour_blend(base, tint, amt):
    """re-tint `base` toward `tint`'s hue at base's own luminance ('color' blend), by amt"""
    lb = (base @ W_LUM)[..., None]
    lt = np.maximum((tint @ W_LUM)[..., None], 1e-3)
    t = np.clip(tint / lt * lb, 0, 1)
    amt = np.asarray(amt, float)
    if amt.ndim == 2:
        amt = amt[..., None]
    return base + (t - base) * amt


# ============================================================ Common: Eevee 125
def eevee():
    """Commons never get a background (user rule): the plain colorscripts sprite, as the pack builder does"""
    cid = "swsh7-125"
    spr = Sprite("eevee")
    c = Card(spr.w, spr.h)
    c.put_sprite(spr, 0, 0)
    return meta(c, card=cid, label="Common: Eevee 125/203 -- the plain sprite (commons get no background)",
                rarity="Common", finish="non-foil, no background: the plain sprite", variant="common", anim=None,
                ref=(cid, 60, 100, 686, 482), S=None)


# ============================================================ Rare Holo V: Sylveon V 74
SILVER = ["#5d646c", "#7b838c", "#9aa3ac", "#bcc4cc", "#dde3e8", "#f3f6f8"]


def silver_frame(c, q, width=2, ramp_hex=None, groove=False):
    """the V card's metal frame in the outer `width` grid px of the bg: a brushed gradient lit from the
    top-left, a bright bevel on the outer top/left edge and a shadow on the bottom/right, sparse diagonal
    etch lines (every 5 px, so a thin frame never reads as a checkerboard); `groove` cuts a dark channel
    down the middle of a >= 3 px frame (the heavier VMAX frame). A dark hairline on the inside edge."""
    FH, FW = c.FH, c.FW
    yy, xx = np.mgrid[0:FH, 0:FW]
    ring = (xx < width) | (yy < width) | (xx >= FW - width) | (yy >= FH - width)
    inner = ~ring & ((xx == width) | (yy == width) | (xx == FW - width - 1) | (yy == FH - width - 1))
    depth = np.minimum(np.minimum(xx, yy), np.minimum(FW - 1 - xx, FH - 1 - yy))     # 0 = outermost
    t = 1 - (xx + yy) / (FW + FH)
    t = 0.3 + 0.5 * t + 0.2 * np.exp(-(((xx + yy) / (FW + FH) - 0.45) / 0.08) ** 2)
    outer = depth == 0
    t = t + 0.18 * (outer & ((xx == 0) | (yy == 0))) - 0.22 * (outer & ((xx == FW - 1) | (yy == FH - 1)))
    t = t - 0.12 * (((xx - yy) % 5) == 0)
    if groove and width >= 3:
        t = t - 0.3 * (depth == width // 2)
    ramp = np.array([L.hexrgb(h) for h in (ramp_hex or SILVER)], float) / 255
    idx = np.clip(np.round(t * (len(ramp) - 1)), 0, len(ramp) - 1).astype(int)
    q = q.copy()
    q[ring] = ramp[idx][ring]
    q[inner] = q[inner] * 0.45
    c.meta["frame_ring"] = ring
    return q


def sylveon():
    cid = "swsh7-74"
    x0, y0, S, W, H = 37, 92, 16.5, 40, 35
    rgb, _ = E.clean(cid, grow=5, boxes=((0, 0, 734, 96), (440, 90, 734, 168), (0, 646, 734, 1024), (0, 0, 30, 1024), (700, 0, 734, 1024)),
                     tex_src=(130, 110, 330, 300))
    spr = Sprite("sylveon", flip=True)
    c = Card(W, H)
    place(c, spr, cid, x0, y0, S, dx=1, margin=1)
    a = L.sample(rgb, x0, y0, S / 2, 2 * W, 2 * H, resample=L.Image.BOX)
    a = L.tone(a, sat=1.4, bright=1.05, gamma=0.9)
    a = L.focus_halo(c, a, radius=3, dark=0.88, soft=1.0)
    _, lbl, pal = L.kmeans_q(a, 24, 0, ignore=c.fig_mask())
    lbl = L.orphan_clean(lbl, 1)
    base = pal[lbl]
    # SWSH V "sunpillar" foil: narrow continuous rainbow stripes running steeply diagonal, over the whole
    # art window, strongest in the brighter areas
    FH, FW = c.FH, c.FW
    yy, xx = np.mgrid[0:FH, 0:FW]
    u = (xx * 0.9 + yy * 0.35) / 9.0
    stripe = rainbow_rgb(u, s=0.7)
    q = colour_blend(base, stripe, 0.10 + 0.10 * (base @ W_LUM))
    q = np.clip(q * 1.02 + 0.02, 0, 1)
    q = L.median_q(q, 72)
    d = c.dist()
    rim = (d > 0) & (d <= 1.01)
    q[rim] = q[rim] + (1 - q[rim]) * 0.45
    q = silver_frame(c, q)
    c.bg = q
    c.bgq = L.to8(q)
    stars = [(8, 10, 3), (70, 8, 2), (72, 50, 3), (7, 58, 2)]
    for x, y, st in stars:
        L.sparkle(c, x, y, st, {"L": "#ffffff", "l": "#ffe6f4", "j": "#b9d7ff"})
    return meta(c, card=cid, label="Rare Holo V: Sylveon V 074/203, flower bubble (sunpillar foil, silver frame)",
                rarity="Rare Holo V", finish="SWSH V holo: silver frame + sunpillar rainbow stripes",
                variant="rare-holo-v", anim="sunpillar", ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S,
                stars=stars, frame="#c9d1da")


# ============================================================ Rare Ultra: Glaceon V 174 (full art)
def fingerprint(FW, FH, centres, period=2.6, seed=0):
    """fingerprint-like etch field: contours of a sum of whorls (distance to a few centres, bent by a slow
    wave). Returns (field value, 1-px line mask)"""
    yy, xx = np.mgrid[0:FH, 0:FW].astype(float)
    f = np.zeros((FH, FW))
    for (cx, cy, wgt) in centres:
        r = np.hypot(xx - cx, (yy - cy) * 1.15)
        f = f + wgt * r
    f = f / sum(w for _, _, w in centres)
    f = f + 1.6 * np.sin(xx / 7.0 + seed) * np.cos(yy / 9.0) + 0.9 * np.sin((xx + yy) / 5.0)
    ph = (f / period) % 1.0
    line = ph < (1.0 / period)
    return f, line


def glaceon():
    cid = "swsh7-174"
    x0, y0, S, W, H = 10, 80, 17, 42, 33
    rgb, _ = E.clean(cid, grow=5, boxes=((0, 0, 734, 100), (0, 585, 734, 1024), (0, 0, 70, 230), (0, 0, 30, 1024), (700, 0, 734, 1024)),
                     tex_src=(470, 400, 700, 580))
    spr = Sprite("glaceon", flip=True)
    c = Card(W, H)
    place(c, spr, cid, x0, y0, S, dx=0)
    a = L.sample(rgb, x0, y0, S / 2, 2 * W, 2 * H, resample=L.Image.LANCZOS)
    a = L.tone(a, sat=1.12, bright=1.0)
    a = L.focus_halo(c, a, radius=5, dark=0.7, soft=1.4)
    a = L.radial_glow(c, a, (0.75, 0.95, 1.0), max(c.FW, c.FH) * 0.55, 0.36, rays=12, ray_amt=0.5)
    a = L.vignette(a, 0.5, tint=(0.25, 0.0, 0.2))
    # etched fingerprint lines: raised lines catch a little light (low contrast), whorls off-centre
    f, line = fingerprint(c.FW, c.FH, [(12, 10, 1.0), (70, 52, 0.8), (64, 8, 0.5)], period=2.6)
    lift = np.where(line, 0.11, -0.025)
    a = np.clip(a + lift[..., None] * (0.6 + 0.4 * a), 0, 1)
    L.finish(c, a, 170, method="median")
    c.bgq = L.rim(c, c.bgq, colour=(0.85, 0.97, 1.0), amt=0.34)
    stars = [(6, 6, 3), (78, 10, 2), (76, 58, 3), (5, 50, 2)]
    for x, y, st in stars:
        L.sparkle(c, x, y, st, {"L": "#ffffff", "l": "#e6fbff", "j": "#9fe8ff"})
    return meta(c, card=cid, label="Rare Ultra: Glaceon V 174/203 full art, magenta ice shards (fingerprint etch)",
                rarity="Rare Ultra", finish="full-art V: fingerprint-like etched texture, rainbow on the lines",
                variant="rare-ultra", anim="etch", ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S, stars=stars,
                etch_field=f, etch_period=2.6, frame="#e178e6")


# ============================================================ Alt art: Umbreon VMAX 215
def umbreon():
    cid = "swsh7-215"
    x0, y0, S, W, H = 10, 100, 17, 42, 32
    boxes = ((0, 0, 30, 1024), (700, 0, 734, 1024), (0, 0, 734, 88), (0, 30, 112, 150), (95, 84, 345, 160), (430, 92, 708, 168), (0, 645, 734, 1024))
    rgb, _ = E.clean(cid, grow=5, boxes=boxes, tex_src=(20, 250, 240, 420))
    spr = Sprite("umbreon")
    c = Card(W, H)
    place(c, spr, cid, x0, y0, S, dx=0)
    a = L.sample(rgb, x0, y0, S / 2, 2 * W, 2 * H, resample=L.Image.LANCZOS)
    a = L.tone(a, sat=1.15, bright=1.02)
    a = L.focus_halo(c, a, radius=4, dark=0.8, soft=1.2)
    # textured painting: the illustration's own brushwork embossed (height = its luminance), lit from top-left
    lum = a @ W_LUM
    h = ndimage.gaussian_filter(lum, 0.6)
    gy, gx = np.gradient(h)
    relief = np.clip(-(gx * -1.0 + gy * -1.3) * 2.4, -0.3, 0.3)
    a = np.clip(a + relief[..., None] * (0.35 + 0.65 * a), 0, 1)
    a = L.vignette(a, 0.4, tint=(0.02, 0.04, 0.12))
    L.finish(c, a, 200, method="median")
    c.bgq = L.rim(c, c.bgq, colour=(1.0, 0.55, 0.85), amt=0.45)          # the card's pink aura around Umbreon
    stars = [(24, 30, 2), (40, 6, 3), (4, 26, 1), (78, 30, 2)]
    for x, y, st in stars:
        L.sparkle(c, x, y, st, {"L": "#ffffff", "l": "#fff3c4", "j": "#8fd8ff"})
    return meta(c, card=cid, label="Rare Rainbow (alt art): Umbreon VMAX 215/203, moonlit rooftops (textured painting)",
                rarity="Rare Rainbow", finish="alternate-art secret: textured painting (brushwork embossed)",
                variant="rare-rainbow-alt", anim="paint", ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S, stars=stars,
                height=h, frame="#f0c850")


# ============================================================ Rare Rainbow: Leafeon VMAX 204
# The rainbow rare recolours the Pokemon itself. Allowed at rainbow / gold rarities (like the gold remap):
# every sprite colour keeps its LUMINANCE (so the shading structure survives) and takes a pastel rainbow hue
# that depends on where the pixel sits on the body, like the card: warm ears, green/teal face, blue/violet
# body, pink-red legs. Black outline, the darkest strokes (eyes) and pure white (eye shine) are untouched.
RAINBOW_STOPS = [(0.0, -0.02), (0.22, 0.08), (0.42, 0.30), (0.58, 0.47), (0.74, 0.63), (0.88, 0.76), (1.0, 0.93)]
RAINBOW_KEYS = "".join(chr(c) for c in range(0xAC00, 0xAC00 + 4000))       # Hangul: outside every other key set
HUE_STEPS = 48
# how far each colour moves toward its rainbow tint (both are the same luminance, so any blend keeps the
# shading): 0.55 lets Leafeon's own cream / green / brown read under the rainbow (user: at most ~70%)
RAINBOW_BLEND = 0.55


def rainbow_hue(i, j, w, h, shift=0.0):
    """body hue for sprite px (i, j) of a w x h sprite, quantised to HUE_STEPS"""
    u = j / max(1, h - 1)
    ts, hs = zip(*RAINBOW_STOPS)
    hue = float(np.interp(u, ts, hs)) + 0.08 * (i / max(1, w - 1) - 0.5) + shift
    return round(hue * HUE_STEPS) / HUE_STEPS


# the eye, in sprite px of the vendor (unflipped) sprite: its dark iris / pupil pixels keep their colour
EYE_BOX = {"leafeon": (7, 14, 12, 19)}


def rainbow_pinned(hexcol, i=None, j=None, name=None):
    c = L.hexrgb(hexcol)
    if c == (0, 0, 0) or c == (255, 255, 255) or L.lum(c) < 62:
        return True
    box = EYE_BOX.get(name)
    return bool(box and i is not None and box[0] <= i <= box[2] and box[1] <= j <= box[3] and L.lum(c) < 130)


def rainbow_px(hexcol, hue, s=0.5, i=None, j=None, name=None):
    """luminance-preserving pastel re-tint of one sprite colour; pinned colours pass through.
    (i, j) are vendor-sprite px (before any flip), used for the eye pin"""
    if rainbow_pinned(hexcol, i, j, name):
        return hexcol
    base = np.array(L.hexrgb(hexcol), float)[None, None] / 255
    tint = rainbow_rgb(np.array([[hue]]), s=s)
    out = colour_blend(base, tint, RAINBOW_BLEND)[0, 0]
    return L.rgbhex(np.clip(np.round(out * 255), 0, 255))


def rainbow_sprite(c):
    """re-key the sprite cells: (original key, body hue) -> a new key with the rainbow colour (normal and
    shiny palettes both re-tinted from their own colours)"""
    spr = c.spr
    A, B = c.off
    keys = iter(RAINBOW_KEYS)
    new, pal, shiny = {}, {}, {}
    for j, r in enumerate(spr.rows):
        for i, ch in enumerate(r):
            if ch == ".":
                continue
            if ch == "k":
                nk = "k"
                pal["k"], shiny["k"] = spr.pal["k"], spr.shiny["k"]
            else:
                hue = rainbow_hue(i, j, spr.w, spr.h)
                vi = spr.w - 1 - i if spr.flip else i
                eye = rainbow_pinned(spr.pal[ch], vi, j, spr.name) and not rainbow_pinned(spr.pal[ch])
                tok = (ch, hue, eye)
                if tok not in new:
                    new[tok] = next(keys)
                    pal[new[tok]] = rainbow_px(spr.pal[ch], hue, i=vi, j=j, name=spr.name)
                    shiny[new[tok]] = rainbow_px(spr.shiny[ch], hue, i=vi, j=j, name=spr.name)
                nk = new[tok]
            for a in (0, 1):
                for b in (0, 1):
                    c.cells[(2 * (A + i) + a, 2 * (B + j) + b)] = ("sprite", nk)
    c.pals["sprite"] = pal
    c.shiny["sprite"] = shiny
    c.meta["sprite_recolour"] = "rainbow"
    return c


def rainbow_etch(FW, FH, seed=0):
    """rainbow-rare texture: dense diagonal etched lines with a slow wave (1 px every 2-3), plus faceted
    sparkle cells. Returns (line mask, glint mask)"""
    yy, xx = np.mgrid[0:FH, 0:FW].astype(float)
    u = (xx - yy * 0.8) + 1.5 * np.sin(yy / 6.0 + seed) + 1.0 * np.sin(xx / 11.0)
    line = (np.floor(u) % 3) == 0
    rnd = np.random.default_rng(seed)
    glint = rnd.random((FH, FW)) < 0.03
    return line, glint


def leafeon():
    cid = "swsh7-204"
    x0, y0, S, W, H = 17, 78, 17.5, 40, 34
    boxes = ((0, 0, 30, 1024), (700, 0, 734, 1024), (0, 0, 734, 80), (0, 30, 108, 145), (95, 78, 345, 142), (0, 640, 734, 1024))
    rgb, _ = E.clean(cid, grow=14, boxes=boxes, texture=False)          # the rainbow ground is a smooth gradient
    spr = Sprite("leafeon")
    c = Card(W, H)
    place(c, spr, cid, x0, y0, S, dx=0)
    rainbow_sprite(c)
    a = L.sample(rgb, x0, y0, S / 2, 2 * W, 2 * H, resample=L.Image.LANCZOS)
    # the card's own pastel gradient, pushed further into a full rainbow sweep (diagonal hue ramp)
    FH, FW = c.FH, c.FW
    yy, xx = np.mgrid[0:FH, 0:FW]
    hue = -0.04 + (xx / FW * 0.5 + yy / FH * 0.42)
    a = colour_blend(np.clip(a * 0.9 + 0.12, 0, 1), rainbow_rgb(hue, s=0.45), 0.5)
    a = L.tone(a, sat=1.05, bright=1.0)
    a = L.focus_halo(c, a, radius=4, dark=0.82, soft=1.2)
    line, glint = rainbow_etch(FW, FH, seed=204)
    a = np.clip(a + np.where(line, -0.07, 0.025)[..., None], 0, 1)
    L.finish(c, a, 150, method="median")
    q = c.bgq.astype(float) / 255
    d = c.dist()
    g = glint & (d > 2)
    q[g] = np.clip(q[g] * 0.3 + 0.75, 0, 1)
    c.bgq = L.to8(q)
    c.bgq = L.rim(c, c.bgq, colour=(1, 1, 1), amt=0.5)
    stars = [(6, 6, 3), (72, 8, 2), (74, 60, 3), (6, 56, 2), (40, 3, 1)]
    for x, y, st in stars:
        L.sparkle(c, x, y, st, {"L": "#ffffff", "l": "#fff0fa", "j": "#b8f0ff"})
    return meta(c, card=cid, label="Rare Rainbow: Leafeon VMAX 204/203, rainbow secret (gradient + etched lines + glitter)",
                rarity="Rare Rainbow", finish="rainbow secret: pastel rainbow gradient, dense etched texture, glitter",
                variant="rare-rainbow", anim="rainbow", ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S, stars=stars,
                frame="rainbow", glint=[(int(x), int(y)) for y, x in zip(*np.nonzero(g))])


import evcards2 as B2  # noqa: E402  (batch 2; imports the helpers above)

# rarity order, Common .. Rare Secret (the two Rare Rainbows by card number)
BUILDERS = {"swsh7-125": eevee, "swsh7-108": B2.shelgon, "swsh7-106": B2.altaria, "swsh7-49": B2.pikachu,
            "swsh7-109": B2.salamence, "swsh7-74": sylveon, "swsh7-30": B2.vaporeon, "swsh7-174": glaceon,
            "swsh7-204": leafeon, "swsh7-215": umbreon, "swsh7-226": B2.froslass}
ORDER = list(BUILDERS)
