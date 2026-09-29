"""30th Celebration (me55): one real card per printed rarity, built exactly the Evolving Skies way (evs), each
finished like its real print. The tier IS the API rarity. Every 30th Celebration card is foil (commons too);
every card carries the 30th Pikachu-logo stamp in the art, which is painted out (no logos in the art).

  me55-9   Vulpix         Common            the plain sprite, no background (user rule)
  me55-65  Mew            Rare              ME-era rares are always holo: evs Rare Holo (Salamence 109) recipe
                                            in the art window -- grid scene, rainbow foil bands, starlight
  me55-23  Pikachu        Pikachu Rare      NEW: yellow border + art window, a fireworks-burst holo over BOTH
                                            (the real print foils the art and the border)
  me55-92  Umbreon ex     Double Rare       NEW (ex): evs Rare Holo V (Sylveon V 74) frame + scene, the SV/ME ex
                                            fine sparkle-grain holo instead of the sunpillar stripes, beam pair
  me55-131 Lapras         Illustration Rare NEW: evs Rare Ultra (Glaceon V 174) full-bleed painting, the IR's
                                            lighter, wider-spaced etch that follows the painting, soft glow
  me55-154 Gengar ex      Special Illus.    NEW: evs alt-art (Umbreon VMAX 215) textured painting + the SIR's
                                            pearlescent pink -> cyan lustre
  me55-157 Mewtwo ex      Futuristic Rare   NEW: the card's neon scene in liquid chrome: platinum-mapped
                                            luminance under the scene colour, cyan / magenta reflection bands,
                                            a hard specular line

BUILDERS[id]() -> evlib Card with card.meta = {card, label, rarity, finish, variant, anim, ...}.
"""
import math

import numpy as np
from scipy import ndimage

import p30lib as P
from p30lib import E, L, Card, Sprite
from evcards import W_LUM, colour_blend, meta, place, rainbow_rgb, silver_frame, fingerprint

EDGES = ((0, 0, 14, 914), (638, 0, 652, 914))
ME_WIN = (52, 88, 606, 432)                  # the art window of a regular (non-full-art) ME card, inside its frame


def window_rgb(cid, boxes=(), grow=6, texture=True, tex_src=None, win=ME_WIN):
    """evs evcards2.window_rgb for the ME window: scan with the Pokemon + boxes painted out, and everything
    outside the art window replaced by a membrane of the window"""
    rgb, _ = E.clean(cid, grow=grow, boxes=boxes, texture=texture, tex_src=tex_src)
    a, b, cc, d = win
    m = np.ones(rgb.shape[:2], bool)
    m[b:d, a:cc] = False
    return L.pushpull(rgb, ~m)


# ============================================================ Common: Vulpix 9
def vulpix():
    """commons never get a background (user rule): the plain colorscripts sprite"""
    cid = "me55-9"
    spr = Sprite("vulpix")
    c = Card(spr.w, spr.h)
    c.put_sprite(spr, 0, 0)
    return meta(c, card=cid, label="Common: Vulpix 009/128 -- the plain sprite (commons get no background)",
                rarity="Common", finish="plain sprite, no background (commons rule; the real print is foil)",
                variant="common", anim=None, ref=(cid, 52, 88, 606, 432), S=None)


# ============================================================ Rare: Mew 65 (ME rare = holo in the art box)
STAMP_REG = (484, 334, 652, 468)             # the 30th Pikachu stamp on a regular card (over the window corner)


def mew():
    import tiers as s3t
    cid = "me55-65"
    x0, y0, S, W, H = 52, 88, 12.8, 43, 27
    rgb = window_rgb(cid, boxes=(STAMP_REG,), grow=6, tex_src=(60, 380, 180, 430))
    spr = Sprite("mew", flip=True)
    off = (15, 1)
    c = s3t.holo_scene(spr, cid, None, x0, y0, S, W, H, cid, "", off=off, rgb=rgb, ncol=12, foil=0.22, bright=1.0,
                       sparkles=[(5, 5, 3), (80, 6, 2), (80, 48, 3), (4, 46, 2)], seed=65)
    return meta(c, card=cid, label="Rare: Mew 065/128, sunlit forest (ME rare = holo in the art box)",
                rarity="Rare", finish="ME rare holo: rainbow foil bands + starlight inside the art box (evs Rare Holo)",
                variant="rare", anim="holo", ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S)


# ============================================================ Pikachu Rare: Pikachu 23
YELLOW = ["#8a6a10", "#b88c14", "#dcae22", "#f2cc3a", "#fbe26a", "#fff3b0"]


def fireworks(FW, FH, seed=30, cell=(9, 7)):
    """the 30th Pikachu Rare foil: a staggered lattice of firework bursts (a core, 4 short arms, 4 far
    diagonal / axial sparks), each with its own hue and phase. -> [(x, y, hue, phase)]"""
    rnd = np.random.default_rng(seed)
    cx, cy = cell
    pts = []
    for j, y in enumerate(range(1, FH + cy, cy)):
        for x in range(1 + (j % 2) * (cx // 2), FW + cx, cx):
            pts.append((x + int(rnd.integers(-2, 3)), y + int(rnd.integers(-1, 2)), float(rnd.random()),
                        int(rnd.integers(0, 16))))
    return pts


BURST_LIFE = [0, 1, 2, 3, 3, 2, 1, 0]        # 0 off, 1 spark, 2 small burst, 3 full burst


def burst_cells(stage):
    """(dx, dy, weight) for a burst at a stage: weight 1 = hot core"""
    if stage <= 0:
        return []
    out = [(0, 0, 1.0)]
    if stage >= 2:
        out += [(1, 0, .6), (-1, 0, .6), (0, 1, .6), (0, -1, .6)]
    if stage >= 3:
        out += [(2, 2, .45), (-2, -2, .45), (2, -2, .45), (-2, 2, .45), (3, 0, .45), (-3, 0, .45), (0, 2, .45),
                (0, -2, .45)]
    return out


def fireworks_paint(a, bursts, f, skip, amt=0.8):
    """paint the bursts for frame f onto float image a (0..1), skipping cells where skip[y, x]"""
    H, W = skip.shape
    a = a.copy()
    for (x, y, hue, ph) in bursts:
        st = BURST_LIFE[(f - ph) % len(BURST_LIFE)]
        col = rainbow_rgb(np.array([hue]), s=0.7)[0]
        for dx, dy, w in burst_cells(st):
            X, Y = x + dx, y + dy
            if 0 <= X < W and 0 <= Y < H and not skip[Y, X]:
                a[Y, X] = a[Y, X] + (col - a[Y, X]) * amt * w
                if w == 1.0:
                    a[Y, X] = a[Y, X] + (1 - a[Y, X]) * (0.75 if st >= 2 else 0.4)
    return a


def pikachu():
    cid = "me55-23"
    S, W, H = 15.6, 37, 24
    x0, y0 = 56 - S, 88 - S                          # the window + one sprite px all round (the border ring)
    rgb = window_rgb(cid, grow=6, tex_src=(60, 330, 200, 425))
    spr = Sprite("pikachu")
    c = Card(W, H)
    place(c, spr, cid, x0, y0, S, margin=2)
    a = L.sample(rgb, x0, y0, S / 2, 2 * W, 2 * H, resample=L.Image.BOX)
    a = L.tone(a, sat=1.1, bright=1.0)
    a = L.focus_halo(c, a, radius=4, dark=0.84, soft=1.0)
    _, lbl, pal = L.kmeans_q(a, 14, 23, ignore=c.fig_mask())
    base = pal[L.orphan_clean(lbl, 1)]
    FH, FW = c.FH, c.FW
    yy, xx = np.mgrid[0:FH, 0:FW]
    base = colour_blend(base, rainbow_rgb((xx + yy) / 60.0 + 0.1, s=0.5), 0.12)      # the foil's own sheen
    q = silver_frame(c, base, width=2, ramp_hex=YELLOW)                                # the yellow border
    ring = c.meta["frame_ring"]
    d = c.dist()
    rim = (d > 0) & (d <= 1.01)
    q[rim] = q[rim] + (1 - q[rim]) * 0.4
    bursts = fireworks(FW, FH)
    fig = c.fig_mask()
    q = L.median_q(q, 90)
    q_pre, skip = q.copy(), fig | (d <= 1.01)
    q = fireworks_paint(q, bursts, 15, skip)
    c.bg = q
    c.bgq = L.to8(q)
    return meta(c, card=cid, label="Pikachu Rare: Pikachu 023/128 (01/30), Ken Sugimori (fireworks holo, yellow border)",
                rarity="Pikachu Rare", finish="Pikachu Rare: fireworks-burst holo over the art AND the yellow border",
                variant="pikachu-rare", anim="fireworks", ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S,
                bursts=bursts, q_pre=q_pre, skip=skip, ring=ring, frame="#f6d02c")


# ============================================================ Double Rare: Umbreon ex 92
def ex_grain(FW, FH, seed=0, dens=0.07):
    """SV / ME ex holo: a fine sparkle grain (single glitter px) over a faint diagonal rainbow.
    -> [(x, y, phase)]"""
    rnd = np.random.default_rng(seed)
    m = rnd.random((FH, FW)) < dens
    ys, xs = np.nonzero(m)
    return [(int(x), int(y), int(rnd.integers(0, 6))) for x, y in zip(xs, ys)]


GRAIN_LIFE = [0.65, 0.35, 0.1, 0.0, 0.1, 0.35]


def umbreon():
    cid = "me55-92"
    x0, y0, S, W, H = 20, 90, 15.3, 40, 33
    boxes = EDGES + ((0, 0, 652, 88), (0, 40, 172, 178), (15, 322, 182, 472), (0, 556, 652, 914))
    rgb, _ = E.clean(cid, grow=5, boxes=boxes, tex_src=(20, 470, 330, 552))
    spr = Sprite("umbreon")
    c = Card(W, H)
    place(c, spr, cid, x0, y0, S, off=(12, 3))
    a = L.sample(rgb, x0, y0, S / 2, 2 * W, 2 * H, resample=L.Image.BOX)
    a = L.tone(a, sat=1.25, bright=0.92, gamma=1.15)
    a = L.focus_halo(c, a, radius=3, dark=0.85, soft=1.0)
    _, lbl, pal = L.kmeans_q(a, 24, 0, ignore=c.fig_mask())
    base = pal[L.orphan_clean(lbl, 1)]
    FH, FW = c.FH, c.FW
    yy, xx = np.mgrid[0:FH, 0:FW]
    q = colour_blend(base, rainbow_rgb((xx + yy) / 30.0, s=0.6), 0.16)
    q = np.clip(q * 1.02 + 0.02, 0, 1)
    q = L.median_q(q, 72)
    d = c.dist()
    rim = (d > 0) & (d <= 1.01)
    q[rim] = q[rim] + (1 - q[rim]) * 0.45
    q = silver_frame(c, q)
    ring = c.meta["frame_ring"]
    grain = [(x, y, ph) for (x, y, ph) in ex_grain(FW, FH, 92) if d[y, x] > 1.5 and not ring[y, x]]
    q_pre = q.copy()
    for x, y, ph in grain:                            # static: the grain at its final-frame phase
        q[y, x] = q[y, x] + (1 - q[y, x]) * GRAIN_LIFE[(15 + ph) % 6]
    c.bg = q
    c.bgq = L.to8(q)
    stars = [(8, 8, 3), (70, 8, 2), (72, 58, 3), (7, 56, 2)]
    for x, y, st in stars:
        L.sparkle(c, x, y, st, {"L": "#ffffff", "l": "#fff6c8", "j": "#9fd8ff"})
    return meta(c, card=cid, label="Double Rare: Umbreon ex 092/128, moonlit claw streaks (silver frame, sparkle-grain holo)",
                rarity="Double Rare", finish="ex holo: silver frame, fine sparkle-grain foil, sunpillar beam pair",
                variant="double-rare", anim="ex", ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S, stars=stars,
                grain=grain, q_pre=q_pre, frame="#c9d1da")


# ============================================================ Illustration Rare: Lapras 131
def lapras():
    cid = "me55-131"
    x0, y0, S, W, H = 40, 62, 12, 50, 38
    boxes = ((0, 0, 652, 88), (488, 392, 652, 518), (0, 520, 652, 914), (638, 0, 652, 914))
    rgb, _ = E.clean(cid, grow=5, boxes=boxes, tex_src=(150, 440, 300, 515))
    spr = Sprite("lapras")
    c = Card(W, H)
    place(c, spr, cid, x0, y0, S, dx=0, margin=1)
    a = L.sample(rgb, x0, y0, S / 2, 2 * W, 2 * H, resample=L.Image.LANCZOS)
    a = L.tone(a, sat=1.1, bright=1.0, gamma=0.95)
    a = L.focus_halo(c, a, radius=4, dark=0.82, soft=1.2)
    a = L.radial_glow(c, a, (1.0, 0.95, 0.8), max(c.FW, c.FH) * 0.55, 0.22)
    a = L.vignette(a, 0.3, tint=(0.1, 0.2, 0.3))
    # IR texture: lighter and wider-spaced than the Rare Ultra's fingerprint, following the painting's shading
    lum = ndimage.gaussian_filter(a @ W_LUM, 2.0)
    f, _ = fingerprint(c.FW, c.FH, [(24, 16, 1.0), (80, 60, 0.7)], period=4.0, seed=131)
    f = f + 9.0 * lum
    period = 4.0
    line = ((f / period) % 1.0) < (1.0 / period)
    a = np.clip(a + np.where(line, 0.065, 0.0)[..., None] * (0.6 + 0.4 * a), 0, 1)
    L.finish(c, a, 170, method="median")
    c.bgq = L.rim(c, c.bgq, colour=(1.0, 0.98, 0.9), amt=0.3)
    stars = [(6, 6, 3), (92, 8, 2), (94, 64, 2), (22, 30, 2)]
    for x, y, st in stars:
        L.sparkle(c, x, y, st, {"L": "#ffffff", "l": "#fff6dc", "j": "#9fe8ff"})  # noqa
    return meta(c, card=cid, label="Illustration Rare: Lapras 131/128, ferry at the seaside (light etch, full art)",
                rarity="Illustration Rare", finish="illustration rare: full painting, light etched texture along the art",
                variant="illustration-rare", anim="etch", ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S,
                stars=stars, etch_field=f, etch_period=period, frame="#7fd6e6")


# ============================================================ SIR: Gengar ex 154
PEARL = (0.83, 0.5)                          # pink -> cyan


def gengar():
    cid = "me55-154"
    x0, y0, S, W, H = 20, 58, 11.8, 46, 36
    boxes = ((0, 0, 634, 62), (0, 20, 118, 152), (100, 58, 450, 104), (420, 20, 634, 72), (468, 342, 634, 462),
             (0, 470, 634, 888), (0, 0, 14, 888), (622, 0, 634, 888))
    rgb, _ = E.clean(cid, grow=5, boxes=boxes, tex_src=(470, 110, 600, 330))
    spr = Sprite("gengar", flip=True)
    c = Card(W, H)
    place(c, spr, cid, x0, y0, S, margin=1)
    a = L.sample(rgb, x0, y0, S / 2, 2 * W, 2 * H, resample=L.Image.LANCZOS)
    a = L.tone(a, sat=1.15, bright=1.02)
    a = L.focus_halo(c, a, radius=4, dark=0.8, soft=1.2)
    lum = a @ W_LUM
    h = ndimage.gaussian_filter(lum, 0.6)
    gy, gx = np.gradient(h)
    relief = np.clip(-(gx * -1.0 + gy * -1.3) * 2.4, -0.3, 0.3)
    a = np.clip(a + relief[..., None] * (0.35 + 0.65 * a), 0, 1)
    a = L.vignette(a, 0.4, tint=(0.02, 0.04, 0.12))
    # static pearl lustre on the lit (top-left) side, as the catalogue's sir_special
    FH, FW = c.FH, c.FW
    yy, xx = np.mgrid[0:FH, 0:FW]
    diag, span = xx + yy, FW + FH
    dd = diag - 0.26 * span
    pearl = rainbow_rgb(PEARL[0] + (PEARL[1] - PEARL[0]) * np.clip(dd / 40 + 0.5, 0, 1), s=0.3)
    k = 0.36 * np.exp(-0.5 * (dd / 18) ** 2)
    a = a + (pearl - a) * k[..., None]
    L.finish(c, a, 200, method="median")
    c.bgq = L.rim(c, c.bgq, colour=(1.0, 0.6, 0.9), amt=0.4)
    stars = [(6, 30, 2), (60, 6, 3), (86, 52, 2), (40, 66, 2)]
    for x, y, st in stars:
        L.sparkle(c, x, y, st, {"L": "#ffffff", "l": "#ffe0f4", "j": "#a8f0ff"})
    return meta(c, card=cid, label="Special Illustration Rare: Gengar ex 154/128, haunted lantern town (textured painting, pearl)",
                rarity="Special Illustration Rare", finish="SIR: textured painting (brushwork embossed) + pearlescent pink/cyan lustre",
                variant="special-illustration-rare", anim="sir", ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S,
                stars=stars, height=h, frame="#f0c850")


# ============================================================ Futuristic Rare: Mewtwo ex 157
PLATINUM = ["#1a1624", "#3a3448", "#5e5872", "#8a86a0", "#b8b6ca", "#e2e2ee", "#ffffff"]


def chrome(a, ph=0.0):
    """liquid chrome over the scene: luminance -> a platinum ramp, the scene's own colour laid back over
    it ('colour' blend), rolling reflection bands tinted cyan (crests) / magenta (troughs)"""
    H, W = a.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    l = a @ W_LUM
    l = np.clip((l - np.percentile(l, 2)) / max(1e-6, np.percentile(l, 98) - np.percentile(l, 2)), 0, 1)
    refl = np.sin(yy / 5.0 + 2.2 * np.sin(xx / 13.0) + 2 * math.pi * ph)
    lv = np.clip(0.12 + 0.62 * l + 0.16 * refl, 0, 0.99)
    ramp = np.array([L.hexrgb(h) for h in PLATINUM], float) / 255
    t = lv * (len(ramp) - 1)
    i = np.floor(t).astype(int)
    fr = (t - i)[..., None]
    metal = ramp[i] + (ramp[np.minimum(i + 1, len(ramp) - 1)] - ramp[i]) * fr
    out = colour_blend(metal, np.clip(a * 1.1, 0, 1), 0.72)
    tint = np.where((refl > 0)[..., None], np.array((0.35, 0.95, 1.0)), np.array((1.0, 0.35, 0.9)))
    out = colour_blend(out, tint, 0.22 * np.abs(refl))
    return np.clip(out, 0, 1), refl


# The Futuristic Rare's own style (user decision): the real cards give the Pokemon a slight dark / red cast, so
# the sprite takes a LOW-opacity luminance-preserving tint toward the card's dominant red (or, lacking red, its
# darkest) tone -- the same kind of allowed recolour as the evs rainbow rare, and like it the tint flows and
# pulses over the body in the animation, here in sync with the chrome reflections. Outline, near-black strokes,
# pure white and the eye (EYE_PIN) are untouched. Static = the phase-0 state (the first loop frame).
FR_BLEND = 0.3                               # max blend toward the tint (<= 0.35 asked, 0.55 is the hard cap)
FR_STEPS = 8                                 # tint strength levels (keeps the sprite palette small)
FR_KEYS = "".join(chr(c) for c in range(0xAC00, 0xAC00 + 4000))       # Hangul, as evs RAINBOW_KEYS
# eye, in vendor (unflipped) sprite px: (x0, y0, x1, y1) and the keys inside it that stay as printed
EYE_PIN = {"mewtwo": ((9, 11, 13, 14), "fghj"), "mew": ((8, 12, 12, 14), "ef")}


def futuristic_tint(cid, win=(20, 95, 630, 525)):
    """the card's dominant red tone (median of the saturated mid-dark reds, when they cover >= 1.5% of the art),
    else the mean of its darkest 10%, pushed deep (value 0.25) -> hex"""
    from skimage.color import rgb2hsv, hsv2rgb
    x0, y0, x1, y1 = win
    a = E.card_img(cid)[y0:y1, x0:x1]
    h = rgb2hsv(a)
    H, Sa, V = h[..., 0] * 360, h[..., 1], h[..., 2]
    red = ((H < 30) | (H > 330)) & (Sa > 0.45) & (V > 0.15) & (V < 0.75)
    if red.mean() >= 0.015:
        col = np.median(a[red], 0)
    else:
        lum = a @ W_LUM
        col = a[lum <= np.percentile(lum, 10)].mean(0)
    hh = rgb2hsv(col[None, None])[0, 0]
    return L.rgbhex(np.round(hsv2rgb(np.array([[[hh[0], hh[1], 0.25]]]))[0, 0] * 255))


def fr_amt(X, Y, t=0.0):
    """tint strength at grid px (X, Y), loop phase t: follows chrome()'s reflection wave (same phase), plus a
    slow whole-body pulse; quantised to FR_STEPS levels, max FR_BLEND"""
    refl = math.sin(Y / 5.0 + 2.2 * math.sin(X / 13.0) + 2 * math.pi * t)
    k = (0.5 + 0.5 * refl) * (0.75 + 0.25 * math.cos(2 * math.pi * t))
    return round((0.35 + 0.65 * k) * FR_STEPS) / FR_STEPS * FR_BLEND


def fr_pinned(hexcol, i=None, j=None, name=None, key=None):
    c = L.hexrgb(hexcol)
    if c == (255, 255, 255) or L.lum(c) < 62:          # outline, near-black strokes, white shine
        return True
    box, keys = EYE_PIN.get(name, ((0, 0, -1, -1), ""))
    return bool(i is not None and box[0] <= i <= box[2] and box[1] <= j <= box[3] and key in keys)


def fr_px(hexcol, amt, tint):
    """luminance-preserving blend of one colour toward the tint's hue, by amt"""
    base = np.array(L.hexrgb(hexcol), float)[None, None] / 255
    t = np.array(L.hexrgb(tint), float)[None, None] / 255
    return L.rgbhex(np.clip(np.round(colour_blend(base, t, amt)[0, 0] * 255), 0, 255))


def fr_colour(spr, ch, i, j, X, Y, t, tint, shiny=False):
    """colour of sprite px (i, j) (placed column i; the vendor column follows from the flip) at grid (X, Y),
    phase t. Pinned by the normal colour (so normal and shiny pin the same pixels)"""
    src = spr.shiny if shiny else spr.pal
    vi = spr.w - 1 - i if spr.flip else i
    if ch == "k" or fr_pinned(spr.pal[ch], vi, j, spr.name, ch):
        return src[ch]
    return fr_px(src[ch], fr_amt(X, Y, t), tint)


def futuristic_sprite(c, tint):
    """re-key the sprite cells: (key, tinted normal, tinted shiny) -> a new key"""
    spr = c.spr
    A, B = c.off
    keys = iter(FR_KEYS)
    new, pal, shiny = {}, {}, {}
    for j, r in enumerate(spr.rows):
        for i, ch in enumerate(r):
            if ch == ".":
                continue
            X, Y = 2 * (A + i), 2 * (B + j)
            tok = (ch, fr_colour(spr, ch, i, j, X, Y, 0.0, tint), fr_colour(spr, ch, i, j, X, Y, 0.0, tint, True))
            if tok not in new:
                new[tok] = "k" if ch == "k" else next(keys)
                pal[new[tok]], shiny[new[tok]] = tok[1], tok[2]
            for a in (0, 1):
                for b in (0, 1):
                    c.cells[(X + a, Y + b)] = ("sprite", new[tok])
    c.pals["sprite"], c.shiny["sprite"] = pal, shiny
    c.meta.update(sprite_recolour="futuristic", fr_tint=tint)
    return c


def mewtwo():
    cid = "me55-157"
    x0, y0, S, W, H = 40, 62, 10.8, 48, 43
    boxes = ((0, 0, 652, 92), (470, 388, 652, 530), (0, 528, 652, 914), (0, 0, 16, 914), (636, 0, 652, 914))
    rgb, _ = E.clean(cid, grow=5, boxes=boxes, texture=False)      # the hole is half the card: smooth fill
    spr = Sprite("mewtwo")
    c = Card(W, H)
    place(c, spr, cid, x0, y0, S, margin=1)
    futuristic_sprite(c, futuristic_tint(cid))
    a = L.sample(rgb, x0, y0, S / 2, 2 * W, 2 * H, resample=L.Image.LANCZOS)
    a = L.tone(a, sat=1.2, bright=1.0)
    a = L.focus_halo(c, a, radius=4, dark=0.75, soft=1.2)
    scene = a
    q, refl = chrome(a)
    FH, FW = c.FH, c.FW
    yy, xx = np.mgrid[0:FH, 0:FW]
    spec = np.abs((xx + yy) - 0.3 * (FW + FH)) < 0.8                 # the hard specular line (parked)
    q = np.where(spec[..., None], q + (1 - q) * 0.55, q)
    L.finish(c, q, 180, method="median")
    c.bgq = L.rim(c, c.bgq, colour=(0.8, 1.0, 1.0), amt=0.45)
    stars = [(6, 6, 3), (90, 10, 2), (88, 78, 3), (6, 60, 2)]
    for x, y, st in stars:
        L.sparkle(c, x, y, st, {"L": "#ffffff", "l": "#e0fbff", "j": "#ff9af0"})
    return meta(c, card=cid, label="Futuristic Rare: Mewtwo ex 157/128, YOSHIROTTEN (liquid chrome over the energy burst)",
                rarity="Futuristic Rare", finish="futuristic rare: liquid chrome over the neon scene, specular line; sprite tinted red-black (<=0.3), flowing",
                variant="futuristic-rare", anim="chrome", ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S,
                stars=stars, scene=scene, frame="#c07cff")


# rarity order: pull rate, commonest first (Pikachu Rare is one per pack, Double Rare ~1 in 5)
BUILDERS = {"me55-9": vulpix, "me55-65": mew, "me55-23": pikachu, "me55-92": umbreon, "me55-131": lapras,
            "me55-154": gengar, "me55-157": mewtwo}
ORDER = list(BUILDERS)
