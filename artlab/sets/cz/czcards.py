"""Crown Zenith (swsh12pt5 + Galarian Gallery swsh12pt5gg): every builder of the set, one per printed-rarity finish,
driven by a per-card CFG table (so the batch modules add rows, never code). The approved evs / p30 recipes are
reused verbatim; the rarities new in this set get their own effect in the established families:

  kind      printed rarity             approved example / recipe                                   anim
  common    Common                     evs Eevee 125: the plain sprite, no background              -
  uncommon  Uncommon                   evs Shelgon 108: matte, sprite-scale scene, 12 colours       -
  rare      Rare                       evs Altaria 106: matte, grid-scale scene, 16 colours        -
  holo      Rare Holo                  evs Salamence 109: tiers.holo_scene in the SWSH window      holo
  v         Rare Holo V                evs Sylveon V 74 (batch_v.build_v geometry)                 sunpillar
  vmax      Rare Holo VMAX             evs Vaporeon VMAX 30: gunmetal frame, contour grooves       sunpillar
  vstar     Rare Holo VSTAR            NEW, one step above VMAX: the VMAX scene + grooves, a       vstar
                                       platinum-gold grooved frame, a gold star-crest of rays
                                       radiating from the Pokemon (the VSTAR burst)
  radiant   Radiant Rare               NEW, its own shimmer family: a silver radial crosshatch     radiant
                                       (log-spiral diamonds bursting out from the Pokemon) with
                                       star glints at the crossings, a faint angular rainbow,
                                       a thin light frame (matches the tier's `radiant` skin)
  alt       any tier, painted alt art  evs Umbreon VMAX 215 (batch_altart.build_alt)                paint
            (Pikachu 160 Rare Secret, the Galarian Gallery V / VMAX / VSTAR)
  gallery   Trainer Gallery Rare Holo  NEW, the painting family's lighter step: the painting with   gallery
                                       a softer emboss, a fine linen (canvas-weave) texture and a
                                       pastel vertical holo sheen
  gold      Rare Secret (gold)         evs Froslass 226: gold remap, faceted etched gold           gold

BUILDERS[id]() -> evlib Card with card.meta = {card, label, rarity, finish, variant, anim, frame ...}.
"""
import math

import numpy as np
from scipy import ndimage

import czlib as P
from czlib import E, L, Card, Sprite
import czmasks as CM
import evcards2 as B2
from evcards import W_LUM, colour_blend, meta, place, rainbow_rgb, silver_frame

EDGES = ((0, 0, 30, 1024), (700, 0, 734, 1024))
NAME_BAR = (0, 0, 734, 96)
STAGE_BOX = B2.STAGE_BOX                          # stage icon + "Evolves from" over the window's top-left
STAGE_ICON = (20, 130, 125, 168)                  # ... whose plate reaches y ~162 on these scans (audit)
V_CORNER = [(30, 92), (96, 92), (30, 215)]        # the V card's silver corner swoosh (batch_v.CORNER)
V_ARM = [(0, 95), (116, 95), (44, 234), (0, 234)]  # the V logo's arm on full arts (batch_altart.V_ARM)
STRIKE = (440, 84, 712, 170)                      # Single / Rapid Strike badge under the HP
VMAX_LOGO = (0, 28, 112, 152)
EVOLVES = (100, 72, 370, 140)
VSTAR_ICON = (0, 30, 128, 168)                    # the VSTAR stage icon (top-left) + its box
VSTAR_CORNER = (0, 140, 62, 240)                  # the metallic V corner under the icon
RAD_WIN = (58, 98, 680, 482)                      # the Radiant card's art window

FRAMES = {"Common": "#9aa0aa", "Uncommon": "#8fc4a8", "Rare": "#6ea5ff", "Rare Holo": "#56d0e0",
          "Rare Holo V": "#c9d1da", "Rare Holo VMAX": "#8f9cff", "Rare Holo VSTAR": "#e6c86e",
          "Radiant Rare": "#b9c6ff", "Trainer Gallery Rare Holo": "#f4b6d6", "Rare Secret": "#f0c850"}
WHITE_STAR = {"L": "#ffffff", "l": "#e6fbff", "j": "#9fe8ff"}
GOLD_STAR = {"L": "#ffffff", "l": "#fff3c4", "j": "#8fd8ff"}
PINK_STAR = {"L": "#ffffff", "l": "#fff0fa", "j": "#f0b8ff"}
PASTEL_STAR = {"L": "#ffffff", "l": "#fff2fb", "j": "#bfe8ff"}

CFG = {}
BUILDERS = {}
ORDER = []

DEFAULTS = dict(flip=False, off=None, dx=0, dy=0, tex_src=None, boxes=(), polys=(), grow=5, texture=True, stars=None,
                rim_col=(1.0, 1.0, 1.0), rim=0.45, vig=(0.02, 0.04, 0.12), vign=0.4, sat=None, bright=None,
                clarity=0.0, frame=None, star=None, scene="", W=None, H=None, S=None, x0=None, y0=None, ch=None,
                strike=False, text_y=640, gloss=None)


def cfg(cid):
    return {**DEFAULTS, **CFG[cid]}


# ============================================================ shared helpers
def card_name(cid):
    return P.card_json(cid)["name"]


def label(cid, rarity, what):
    k = cfg(cid)
    sc = f", {k['scene']}" if k["scene"] else ""
    return f"{rarity}: {card_name(cid)} {P.num_label(cid)}{sc} ({what})"


def clean(cid, boxes, polys=(), grow=5, texture=True, tex_src=None):
    """the scan with the real Pokemon (masks/<id>.png, grown) and every box / polygon painted out"""
    sh = E.card_img(cid).shape[:2]
    extra = np.zeros(sh, bool)
    for p in polys:
        extra |= CM.poly(sh, p)
    if tex_src is None and texture:
        known = ~ndimage.binary_dilation(E.mask(cid) | extra, iterations=grow + 6)
        for (a, b, c, d) in boxes:
            known[max(0, b):d, max(0, a):c] = False
        tex_src = auto_tex_src(known)
    rgb, _ = E.clean(cid, grow=grow, boxes=boxes, texture=texture, tex_src=tex_src, extra=extra)
    return rgb


def auto_tex_src(known, tw=150, th=150):
    """the rect of the scene with the most known (unmasked, unboxed) pixels (batch_v.auto_tex_src)"""
    H, W = known.shape
    best, bs = (40, 120, 40 + tw, 120 + th), -1
    for y in range(90, H - th, 20):
        for x in range(30, W - 30 - tw, 20):
            s = known[y:y + th, x:x + tw].mean()
            if s > bs:
                best, bs = (x, y, x + tw, y + th), s
    return best


def window_rgb(cid, boxes=(), grow=6, texture=True, tex_src=None, win=B2.SWSH_WIN, polys=()):
    """evs evcards2.window_rgb: everything outside the art window replaced by a membrane of the window. The frame
    and text outside the window are boxed out BEFORE the fill too, so the texture fill never mirrors a name bar or
    stat line into a hole that touches the window edge (the holo batch found "Entei" / "NO. 150" ghosts)"""
    a, b, cc, d = win
    # the scan's silver window border sits ~8 px inside the right edge of SWSH_WIN: box it out with the frame
    # (the audit found a pale strip down the right edge of the uncommon / rare art)
    out = ((0, 0, 734, b), (0, d, 734, 1024), (0, 0, a, 1024), (cc - 12, 0, 734, 1024))
    rgb = clean(cid, tuple(boxes) + out, polys, grow, texture, tex_src)
    m = np.ones(rgb.shape[:2], bool)
    m[b:d, a:cc] = False
    return L.pushpull(rgb, ~m)


def put(c, spr, cid, x0, y0, S, k, margin=1):
    return place(c, spr, cid, x0, y0, S, off=k["off"], dx=k["dx"], dy=k["dy"], margin=margin)


def stars_for(c, n=4, min_d=4, cands=None):
    FW, FH = c.FW, c.FH
    cands = cands or [(6, 6, 3), (FW - 8, 8, 2), (FW - 6, FH - 8, 3), (6, FH - 10, 2), (FW // 2, 3, 1),
                      (FW // 4, FH - 4, 2), (FW - 4, FH // 2, 2), (4, FH // 2, 2), (3 * FW // 4, 4, 2),
                      (FW // 4, 5, 2), (3 * FW // 4, FH - 5, 2)]
    d = c.dist()
    out = []
    for x, y, st in cands:
        x, y = min(max(3, x), FW - 4), min(max(3, y), FH - 4)
        if d[y, x] > min_d and all(abs(x - a) + abs(y - b) > 10 for a, b, _ in out):
            out.append((x, y, st))
    return out[:n]


def window_geo(spr, x0, y0, wspan, hspan, h0, pad_h=2, pad_w=4):
    """a regular-window crop: H follows the sprite (>= h0), S = hspan / H, narrowed when the sprite is wide"""
    H = max(h0, spr.h + pad_h)
    S = hspan / H
    if (spr.w + pad_w) * S > wspan:
        S = wspan / (spr.w + pad_w)
        H = round(hspan / S)
    W = max(round(wspan / S), spr.w + pad_w)
    return x0, y0, S, W, H


def evolves(cid):
    return bool(P.card_json(cid).get("evolvesFrom"))


def geo_override(k, geo):
    x0, y0, S, W, H = geo
    return (k["x0"] if k["x0"] is not None else x0, k["y0"] if k["y0"] is not None else y0,
            k["S"] or S, k["W"] or W, k["H"] or H)


# ============================================================ Common (Eevee 125)
def build_common(cid):
    """commons never get a background (user rule): the plain sprite, mirrored when set.json flip_commons lists it
    (the importer does the same, tools/build_realcards.py)"""
    k = cfg(cid)
    flip = cid in P.META.get("flip_commons", [])
    spr = Sprite(k["sprite"], flip=flip)
    c = Card(spr.w, spr.h)
    c.put_sprite(spr, 0, 0)
    return meta(c, card=cid, label=label(cid, "Common", "the plain sprite, commons get no background"),
                rarity="Common", finish="plain sprite, no background (commons rule)", variant="common", anim=None,
                ref=(cid, 64, 96, 684, 492), S=None, frame=FRAMES["Common"])


# ============================================================ Uncommon (Shelgon 108) / Rare (Altaria 106)
def build_uncommon(cid):
    k = cfg(cid)
    spr = Sprite(k["sprite"], flip=k["flip"])
    x0, y0, S, W, H = geo_override(k, window_geo(spr, 62, 100, 624, 384, 24))
    boxes = ((STAGE_BOX, STAGE_ICON) if evolves(cid) else ()) + tuple(k["boxes"])
    rgb = window_rgb(cid, boxes=boxes, texture=k["texture"] if "texture" in CFG[cid] else False,
                     tex_src=k["tex_src"], polys=k["polys"])
    c = Card(W, H)
    put(c, spr, cid, x0, y0, S, k)
    B2.matte(c, rgb, x0, y0, S, 12, sat=k["sat"] or 0.84, bright=k["bright"] or 0.88)
    return meta(c, card=cid, label=label(cid, "Uncommon", "non-foil"), rarity="Uncommon",
                finish="non-foil: sprite-scale scene, 12 colours", variant="uncommon", anim=None,
                ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S, frame=FRAMES["Uncommon"])


def build_rare(cid):
    k = cfg(cid)
    spr = Sprite(k["sprite"], flip=k["flip"])
    x0, y0, S, W, H = geo_override(k, window_geo(spr, 64, 94, 616, 402, 30))
    boxes = ((STAGE_BOX, STAGE_ICON) if evolves(cid) else ()) + tuple(k["boxes"])
    rgb = window_rgb(cid, boxes=boxes, grow=8, texture=k["texture"], tex_src=k["tex_src"], polys=k["polys"])
    c = Card(W, H)
    put(c, spr, cid, x0, y0, S, k)
    B2.matte(c, rgb, x0, y0, S, 16, sat=k["sat"] or 0.95, bright=k["bright"] or 0.95, scale=1)
    return meta(c, card=cid, label=label(cid, "Rare", "non-foil"), rarity="Rare",
                finish="non-foil: grid-scale scene, 16 colours", variant="rare", anim=None,
                ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S, frame=FRAMES["Rare"])


# ============================================================ Rare Holo (Salamence 109)
def build_holo(cid):
    import tiers as s3t
    k = cfg(cid)
    spr = Sprite(k["sprite"], flip=k["flip"])
    x0, y0, S, W, H = geo_override(k, window_geo(spr, 64, 96, 620, 396, 30))
    boxes = ((STAGE_BOX, STAGE_ICON) if evolves(cid) else ()) + tuple(k["boxes"])
    rgb = window_rgb(cid, boxes=boxes, grow=5, texture=k["texture"], tex_src=k["tex_src"], polys=k["polys"])
    tmp = Card(W, H)
    off = put(tmp, spr, cid, x0, y0, S, k)
    stars = k["stars"] or stars_for(tmp)
    c = s3t.holo_scene(spr, cid, None, x0, y0, S, W, H, cid, "", off=off, rgb=rgb, ncol=12, foil=0.22, bright=1.0,
                       sparkles=stars, seed=int(''.join(ch for ch in E.num(cid) if ch.isdigit())))
    return meta(c, card=cid, label=label(cid, "Rare Holo", "holo in the art box"), rarity="Rare Holo",
                finish="SWSH rare holo: rainbow foil bands + starlight inside the art box", variant="rare-holo",
                anim="holo", ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S, frame=FRAMES["Rare Holo"])


# ============================================================ Rare Holo V (Sylveon V 74, batch_v.build_v)
WX0, WY0, WX1, WY1 = 37, 92, 697, 669


def v_geo(spr, text_y):
    wy1 = min(WY1, text_y + 23)
    ratio = (WX1 - WX0) / (wy1 - WY0)
    W = max(40, int(np.ceil(max(spr.w / 0.75, (spr.h + 4) * ratio) - 1e-6)))
    S = (WX1 - WX0) / W
    H = round((wy1 - WY0) / S)
    return WX0, WY0, S, W, H


def build_v(cid):
    k = cfg(cid)
    spr = Sprite(k["sprite"], flip=k["flip"])
    x0, y0, S, W, H = geo_override(k, v_geo(spr, k["text_y"]))
    boxes = [NAME_BAR, (0, k["text_y"], 734, 1024), *EDGES, *k["boxes"]] + ([STRIKE] if k["strike"] else [])
    rgb = clean(cid, boxes, (V_CORNER, *k["polys"]), k["grow"], k["texture"], k["tex_src"])
    c = Card(W, H)
    put(c, spr, cid, x0, y0, S, k)
    a = L.sample(rgb, x0, y0, S / 2, 2 * W, 2 * H, resample=L.Image.BOX)
    a = L.tone(a, sat=k["sat"] or 1.4, bright=k["bright"] or 1.05, gamma=0.9)
    a = L.focus_halo(c, a, radius=3, dark=0.88, soft=1.0)
    _, lbl, pal = L.kmeans_q(a, 24, 0, ignore=c.fig_mask())
    base = pal[L.orphan_clean(lbl, 1)]
    FH, FW = c.FH, c.FW
    yy, xx = np.mgrid[0:FH, 0:FW]
    q = colour_blend(base, rainbow_rgb((xx * 0.9 + yy * 0.35) / 9.0, s=0.7), 0.10 + 0.10 * (base @ W_LUM))
    q = np.clip(q * 1.02 + 0.02, 0, 1)
    q = L.median_q(q, 72)
    d = c.dist()
    rim = (d > 0) & (d <= 1.01)
    q[rim] = q[rim] + (1 - q[rim]) * k["rim"]
    q = silver_frame(c, q)
    c.bg = q
    c.bgq = L.to8(q)
    stars = k["stars"] or stars_for(c)
    for x, y, st in stars:
        L.sparkle(c, x, y, st, {"L": "#ffffff", "l": "#ffe6f4", "j": "#b9d7ff"})
    return meta(c, card=cid, label=label(cid, "Rare Holo V", "sunpillar foil, silver frame"), rarity="Rare Holo V",
                finish="SWSH V holo: silver frame + sunpillar rainbow stripes", variant="rare-holo-v",
                anim="sunpillar", ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S, stars=stars,
                frame=FRAMES["Rare Holo V"])


# ============================================================ Rare Holo VMAX (Vaporeon VMAX 30)
def full_geo(spr, text_y, x0=6, y0=72, wspan=704, w0=46, smax=15.3):
    W = max(w0, spr.w + 6)
    S = min(smax, wspan / W)
    H = max(spr.h + 3, round((text_y + 25 - y0) / S))
    return x0 + (wspan - W * S) / 2, y0, S, W, H


def vmax_scene(cid, k, boxes, polys, geo, ncol=40):
    spr = Sprite(k["sprite"], flip=k["flip"])
    x0, y0, S, W, H = geo_override(k, geo(spr))
    rgb = clean(cid, boxes, polys, k["grow"], k["texture"], k["tex_src"])
    c = Card(W, H)
    put(c, spr, cid, x0, y0, S, k, margin=2)
    a = L.sample(rgb, x0, y0, S / 2, 2 * W, 2 * H, resample=L.Image.BOX)
    a = L.tone(a, sat=k["sat"] or 1.25, bright=k["bright"] or 1.0)
    a = L.focus_halo(c, a, radius=3, dark=0.85, soft=1.0)
    _, lbl, pal = L.kmeans_q(a, ncol, 0, ignore=c.fig_mask())
    base = pal[L.orphan_clean(lbl, 1)]
    base, groove = B2.vmax_texture(base)
    FH, FW = c.FH, c.FW
    yy, xx = np.mgrid[0:FH, 0:FW]
    q = colour_blend(base, rainbow_rgb((xx * 0.9 + yy * 0.35) / 9.0, s=0.7), 0.14 + 0.1 * (base @ W_LUM))
    return c, q, groove, (x0, y0, S, W, H)


def build_vmax(cid):
    k = cfg(cid)
    boxes = [*EDGES, (0, 0, 734, 74), VMAX_LOGO, EVOLVES, (0, k["text_y"], 734, 1024), *k["boxes"]] + \
        ([STRIKE] if k["strike"] else [])
    c, q, groove, (x0, y0, S, W, H) = vmax_scene(cid, k, boxes, k["polys"], lambda s: full_geo(s, k["text_y"]))
    q = L.median_q(q, 110)
    d = c.dist()
    rim = (d > 0) & (d <= 1.01)
    q[rim] = q[rim] + (1 - q[rim]) * k["rim"]
    q = silver_frame(c, q, width=3, ramp_hex=B2.GUNMETAL, groove=True)
    ring = c.meta["frame_ring"]
    c.bg = q
    c.bgq = L.to8(q)
    stars = k["stars"] or stars_for(c, cands=None)
    for x, y, st in stars:
        L.sparkle(c, x, y, st, {"L": "#ffffff", "l": "#dff6ff", "j": "#8fd8ff"})
    return meta(c, card=cid, label=label(cid, "Rare Holo VMAX", "gunmetal frame, etched holo"),
                rarity="Rare Holo VMAX", finish="SWSH VMAX holo: gunmetal frame, sunpillar stripes, bold etched contours",
                variant="rare-holo-vmax", anim="sunpillar", ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S,
                stars=stars, grooves=groove & ~ring, frame=FRAMES["Rare Holo VMAX"])


# ============================================================ NEW: Rare Holo VSTAR (Leafeon VSTAR 14)
# One step above VMAX: the VMAX scene (40 colours, contour grooves, sunpillar stripes) in a heavier grooved frame
# of platinum shading into gold (the real VSTAR's silver-gold crest), and a gold star-crest: fine rays radiating
# from the Pokemon across the whole foil (the VSTAR burst). Anim `vstar`: the sunpillar beam pair (the grooves
# catch it, as VMAX) + a gold pulse running out along the rays.
PLAT_GOLD = ["#50473a", "#766b55", "#a09576", "#cbbd8a", "#ecdca2", "#fff7da"]
VSTAR_GOLD = (1.0, 0.84, 0.42)


def star_rays(c, n=24, width=0.55, r0=3.0):
    """1-px rays from the figure's centre: a px is on a ray when its distance to the nearest ray line < width"""
    FH, FW = c.FH, c.FW
    cx, cy = L.fig_centre(c)
    yy, xx = np.mgrid[0:FH, 0:FW].astype(float)
    th = np.arctan2(yy - cy, xx - cx)
    r = np.hypot(xx - cx, yy - cy)
    step = 2 * math.pi / n
    dth = np.abs(((th + step / 2) % step) - step / 2)
    long_ = (np.round(th / step).astype(int) % 2) == 0              # alternate long and short rays
    reach = np.where(long_, 1e9, 0.62 * max(FW, FH))
    return (r * np.sin(dth) < width) & (r > r0) & (r < reach), r, (cx, cy)


def build_vstar(cid):
    k = cfg(cid)
    boxes = [*EDGES, (0, 0, 734, 88), VSTAR_ICON, VSTAR_CORNER, EVOLVES, (0, k["text_y"], 734, 1024), *k["boxes"]] + \
        ([STRIKE] if k["strike"] else [])
    c, q, groove, (x0, y0, S, W, H) = vmax_scene(cid, k, boxes, k["polys"],
                                                 lambda s: full_geo(s, k["text_y"], y0=80))
    d = c.dist()
    rays, r, centre = star_rays(c)
    rays &= d > 2
    gold = np.array(VSTAR_GOLD)
    q = np.where(rays[..., None], colour_blend(q, np.broadcast_to(gold, q.shape), 0.55) * 1.0 + 0.07, q)
    q = np.clip(q, 0, 1)
    q = L.median_q(q, 120)
    rim = (d > 0) & (d <= 1.01)
    q[rim] = q[rim] + (1 - q[rim]) * k["rim"]
    q = silver_frame(c, q, width=3, ramp_hex=PLAT_GOLD, groove=True)
    ring = c.meta["frame_ring"]
    c.bg = q
    c.bgq = L.to8(q)
    stars = k["stars"] or stars_for(c)
    for x, y, st in stars:
        L.sparkle(c, x, y, st, {"L": "#ffffff", "l": "#fff3c4", "j": "#f0c850"})
    return meta(c, card=cid, label=label(cid, "Rare Holo VSTAR", "platinum-gold frame, star-crest rays, etched holo"),
                rarity="Rare Holo VSTAR",
                finish="VSTAR holo: VMAX grooves + sunpillar stripes, platinum-gold grooved frame, gold star-crest rays",
                variant="rare-holo-vstar", anim="vstar", ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S,
                stars=stars, grooves=groove & ~ring & ~rays, rays=rays & ~ring, ray_r=r, centre=centre,
                frame=FRAMES["Rare Holo VSTAR"])


# ============================================================ NEW: Radiant Rare (Radiant Charizard 20)
# Its own shimmer family (not a V foil, not a painting): the Radiant card's whole surface is a silver crosshatch
# of diamonds bursting out from the Pokemon, with star glints where the lines cross. Here: the art window's scene
# (grid scale, 32 colours), a log-spiral diamond lattice centred on the sprite (cells grow outward: a burst),
# the lines lifted to silver with a faint rainbow that turns with the angle, white glints at a subset of the
# crossings, a thin (1 px) light silver frame. Anim `radiant`: a ring of light runs outward over the lattice,
# its hue turning around the centre; the crossings glint as it passes.
SILVER_LIGHT = ["#8a93a0", "#aab3bf", "#c8cfd8", "#e2e7ee", "#f6f8fb", "#ffffff"]


def radiant_lattice(c, K=6.5, M=20, w=0.13):
    FH, FW = c.FH, c.FW
    cx, cy = L.fig_centre(c)
    yy, xx = np.mgrid[0:FH, 0:FW].astype(float)
    r = np.hypot(xx - cx, yy - cy)
    th = np.arctan2(yy - cy, xx - cx)
    p = np.log1p(r / 4.0) * K
    m = th / (2 * math.pi) * M
    u, v = (p + m) % 1.0, (p - m) % 1.0
    lu, lv = np.minimum(u, 1 - u) < w, np.minimum(v, 1 - v) < w
    return lu | lv, lu & lv, r, th, (cx, cy)


def build_radiant(cid):
    k = cfg(cid)
    spr = Sprite(k["sprite"], flip=k["flip"])
    x0, y0, S, W, H = geo_override(k, window_geo(spr, RAD_WIN[0], RAD_WIN[1], RAD_WIN[2] - RAD_WIN[0],
                                                 RAD_WIN[3] - RAD_WIN[1], 30))
    rgb = window_rgb(cid, boxes=tuple(k["boxes"]), grow=k["grow"], texture=k["texture"], tex_src=k["tex_src"],
                     win=RAD_WIN, polys=k["polys"])
    c = Card(W, H)
    put(c, spr, cid, x0, y0, S, k)
    a = L.sample(rgb, x0, y0, S / 2, 2 * W, 2 * H, resample=L.Image.BOX)
    a = L.tone(a, sat=k["sat"] or 1.15, bright=k["bright"] or 1.0)
    a = L.focus_halo(c, a, radius=3, dark=0.85, soft=1.0)
    _, lbl, pal = L.kmeans_q(a, 32, 0, ignore=c.fig_mask())
    base = pal[L.orphan_clean(lbl, 1)]
    line, cross, r, th, centre = radiant_lattice(c)
    d = c.dist()
    line &= d > 1.5
    q = colour_blend(base, rainbow_rgb(th / (2 * math.pi) + r / 80.0, s=0.35), 0.10)
    silver = np.array((0.93, 0.95, 1.0))
    q = np.where(line[..., None], q + (silver - q) * 0.30 + 0.04, q * 0.97)
    q = np.clip(q, 0, 1)
    q = L.median_q(q, 100)
    rim = (d > 0) & (d <= 1.01)
    q[rim] = q[rim] + (1 - q[rim]) * k["rim"]
    q = silver_frame(c, q, width=1, ramp_hex=SILVER_LIGHT)
    ring = c.meta["frame_ring"]
    rnd = np.random.default_rng(int(''.join(ch for ch in E.num(cid) if ch.isdigit())))
    ys, xs = np.nonzero(cross & (d > 3) & ~ring)
    pick = rnd.random(len(xs)) < 0.35
    glints = [(int(x), int(y), int(rnd.integers(0, 6))) for x, y in zip(xs[pick], ys[pick])]
    q_pre = q.copy()
    for x, y, ph in glints:                              # static: the glints at their final-frame phase
        q[y, x] = q[y, x] + (1 - q[y, x]) * RAD_GLINT[(15 + ph) % 6]
    c.bg = q
    c.bgq = L.to8(q)
    stars = k["stars"] or stars_for(c)
    for x, y, st in stars:
        L.sparkle(c, x, y, st, {"L": "#ffffff", "l": "#eef2ff", "j": "#c8b8ff"})
    return meta(c, card=cid, label=label(cid, "Radiant Rare", "radial silver crosshatch burst, glints"),
                rarity="Radiant Rare",
                finish="Radiant: silver log-spiral crosshatch bursting from the Pokemon, glints at the crossings, thin light frame",
                variant="radiant-rare", anim="radiant", ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S, stars=stars,
                lattice=line & ~ring, rad_r=r, rad_th=th, centre=centre, glints=glints, q_pre=q_pre,
                frame=FRAMES["Radiant Rare"])


RAD_GLINT = [0.7, 0.4, 0.12, 0.0, 0.12, 0.4]


# ============================================================ alt-art painting (Umbreon VMAX 215)
Y0, SMAX, CW, WMIN, HMIN = 100, 17.0, 714, 42, 32


def alt_geo(spr, k, y0=Y0):
    ch = k["ch"] or min(544, k["text_y"] + 20 - y0)
    H = k["H"] or max(HMIN, spr.h + 3)
    S = k["S"] or min(SMAX, ch / H)
    W = k["W"] or max(WMIN, spr.w + 6, round(CW / S))
    return 367 - W * S / 2, y0, S, W, H


ALT_TOP = {"v": (NAME_BAR, (0, 0, 70, 230)), "vmax": (NAME_BAR, VMAX_LOGO, EVOLVES),
           "vstar": ((0, 0, 734, 92), VSTAR_ICON, VSTAR_CORNER, EVOLVES), "basic": ((0, 0, 734, 92),),
           "stage": ((0, 0, 734, 92), (0, 40, 140, 170), (110, 84, 380, 128))}


def top_boxes(cid, k):
    t = k.get("top")
    if t is None:
        n = card_name(cid)
        t = "vstar" if n.endswith("VSTAR") else "vmax" if n.endswith("VMAX") else "v" if n.endswith(" V") else \
            ("stage" if evolves(cid) else "basic")
    return ALT_TOP[t], [V_ARM] if t == "v" else []


def painting(cid, k, y0=Y0):
    """the painted scene at full grid resolution, vivid, with the Pokemon's focus halo (steps 1-3 of section 11)"""
    spr = Sprite(k["sprite"], flip=k["flip"])
    x0, y0, S, W, H = geo_override(k, alt_geo(spr, k, y0))
    top, tpolys = top_boxes(cid, k)
    boxes = [*EDGES, *top, (0, k["text_y"], 734, 1024), *k["boxes"]] + ([STRIKE] if k["strike"] else [])
    rgb = clean(cid, boxes, (*tpolys, *k["polys"]), k["grow"], k["texture"], k["tex_src"])
    c = Card(W, H)
    put(c, spr, cid, x0, y0, S, k)
    a = L.sample(rgb, x0, y0, S / 2, 2 * W, 2 * H, resample=L.Image.LANCZOS)
    if k["clarity"]:
        low = np.stack([ndimage.gaussian_filter(a[..., i], 3.0) for i in range(3)], -1)
        a = np.clip(a + k["clarity"] * (a - low), 0, 1)
    return c, a, (x0, y0, S, W, H)


def build_alt(cid):
    """Umbreon VMAX 215's recipe (section 11); the tier stays the printed rarity"""
    k = cfg(cid)
    rarity = P.card_json(cid)["tier"]
    c, a, (x0, y0, S, W, H) = painting(cid, k)
    a = L.tone(a, sat=k["sat"] or 1.15, bright=k["bright"] or 1.02)
    a = L.focus_halo(c, a, radius=4, dark=0.8, soft=1.2)
    lum = a @ W_LUM
    h = ndimage.gaussian_filter(lum, 0.6)
    gy, gx = np.gradient(h)
    relief = np.clip(-(gx * -1.0 + gy * -1.3) * 2.4, -0.3, 0.3)
    a = np.clip(a + relief[..., None] * (0.35 + 0.65 * a), 0, 1)
    a = L.vignette(a, k["vign"], tint=k["vig"])
    L.finish(c, a, 200, method="median")
    c.bgq = L.rim(c, c.bgq, colour=k["rim_col"], amt=k["rim"])
    stars = k["stars"] or stars_for(c)
    for x, y, st in stars:
        L.sparkle(c, x, y, st, k["star"] or GOLD_STAR)
    gg = " Galarian Gallery" if P.is_gg(cid) else ""
    return meta(c, card=cid, rarity=rarity,
                label=label(cid, f"{rarity}{gg} (alt art)", "textured painting"),
                finish="alternate art: textured painting (brushwork embossed)",
                variant=rarity.lower().replace(" ", "-") + "-alt", anim="paint",
                ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S, stars=stars, height=h,
                frame=k["frame"] or "#e178e6", alt=True)


# ============================================================ NEW: Trainer Gallery Rare Holo (Lapras GG05)
# The painting family's lighter step (below the alt-art V / VMAX / VSTAR paintings): the Galarian Gallery
# painting, full width, with a softer brushwork emboss (2/3 of Umbreon 215's), a fine linen / canvas-weave
# texture (basket weave, 2-px threads, +-0.03) and a pastel holo sheen standing on the lit left. Anim `gallery`:
# the light swings gently over the brushwork, a vertical pastel band sweeps left -> right and the weave threads
# glint inside it.
def weave(FW, FH):
    """basket-weave threads: 2x2 blocks alternate horizontal / vertical threads (True = a raised thread px)"""
    yy, xx = np.mgrid[0:FH, 0:FW]
    blk = ((xx // 2) + (yy // 2)) % 2
    return np.where(blk == 0, (yy % 2) == 0, (xx % 2) == 0)


def gallery_sheen(FW, FH, ctr, width, t=0.0):
    yy, xx = np.mgrid[0:FH, 0:FW].astype(float)
    band = np.exp(-((xx + 0.25 * yy - ctr) / width) ** 2)
    hue = rainbow_rgb(xx / FW * 0.8 + 0.55 + t * 0.3, s=0.28)
    return band, hue


def build_gallery(cid):
    k = cfg(cid)
    c, a, (x0, y0, S, W, H) = painting(cid, k, y0=k["y0"] or 95)
    a = L.tone(a, sat=k["sat"] or 1.1, bright=k["bright"] or 1.03)
    a = L.focus_halo(c, a, radius=4, dark=0.84, soft=1.2)
    lum = a @ W_LUM
    h = ndimage.gaussian_filter(lum, 0.6)
    gy, gx = np.gradient(h)
    relief = np.clip(-(gx * -1.0 + gy * -1.3) * 1.6, -0.2, 0.2)
    a = np.clip(a + relief[..., None] * (0.35 + 0.65 * a), 0, 1)
    FH, FW = c.FH, c.FW
    wv = weave(FW, FH)
    a = np.clip(a + np.where(wv, 0.03, -0.015)[..., None] * (0.5 + 0.5 * a), 0, 1)
    band, hue = gallery_sheen(FW, FH, 0.22 * FW, 0.14 * FW)
    a = a + (hue - a) * (0.2 * band)[..., None]
    a = L.vignette(a, 0.3, tint=k["vig"])
    L.finish(c, a, 200, method="median")
    c.bgq = L.rim(c, c.bgq, colour=k["rim_col"], amt=0.38 if "rim" not in CFG[cid] else k["rim"])
    stars = k["stars"] or stars_for(c)
    for x, y, st in stars:
        L.sparkle(c, x, y, st, k["star"] or PASTEL_STAR)
    return meta(c, card=cid, rarity="Trainer Gallery Rare Holo",
                label=label(cid, "Trainer Gallery Rare Holo (Galarian Gallery)", "painting, linen weave, pastel sheen"),
                finish="Galarian Gallery: the painting, soft brushwork emboss, linen weave texture, pastel holo sheen",
                variant="trainer-gallery-rare-holo", anim="gallery", ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S,
                stars=stars, height=h, weave=wv, frame=k["frame"] or FRAMES["Trainer Gallery Rare Holo"])


# ============================================================ Rare Secret gold (Froslass 226)
def build_gold(cid):
    import tiers as s3t
    k = cfg(cid)
    spr = Sprite(k["sprite"], flip=k["flip"])
    ch = k["ch"] or min(660, k["text_y"] + 60 - 92)
    H = k["H"] or max(33, spr.h + 3)
    S = k["S"] or min(20.0, ch / H)
    W = k["W"] or max(32, spr.w + 6, round(640 / S))
    x0, y0 = (k["x0"] if k["x0"] is not None else 367 - W * S / 2), (k["y0"] or 92)
    top, tpolys = top_boxes(cid, k)
    boxes = [*EDGES, *top, (0, k["text_y"], 734, 1024), *k["boxes"]]
    rgb = clean(cid, boxes, (*tpolys, *k["polys"]), 5, False)
    c = Card(W, H)
    put(c, spr, cid, x0, y0, S, k)
    near = {v.lower(): "#000000" for v in list(spr.pal.values()) + list(spr.shiny.values()) if max(L.hexrgb(v)) <= 20}
    gpal, gshiny = L.gold_remap(spr, L.gold_ramp(s3t.RAMP, 24), L.gold_ramp(s3t.RAMP_AMBER, 24), special=near or None)
    c.put_sprite(spr, *c.off, gpal, gshiny)
    a = L.sample(rgb, x0, y0, S / 2, c.FW, c.FH, resample=L.Image.BOX)
    lum = a @ W_LUM
    lum = (lum - lum.min()) / max(1e-6, lum.max() - lum.min())
    h = np.clip((ndimage.gaussian_filter(lum, 0.8) - 0.1) / 0.8, 0, 1)
    seed = int(''.join(ch_ for ch_ in E.num(cid) if ch_.isdigit()))
    fh, seam, _ = s3t.facet_height(c.FW, c.FH, n=70, seed=seed)
    s3t.gold_foil(c, np.zeros_like(h), 1 - h, lo=0.0, hi=0.0, relief=0.0, glow=0.3, glow_r=9, seed=seed,
                  glints=26, facets=0.34 + 0.22 * (h - 0.5) + 0.16 * (fh - 0.5) + 0.5 * s3t.emboss(fh) - 0.05 * seam)
    FW, FH = c.FW, c.FH
    stars = k["stars"] or stars_for(c, 6, cands=[(6, 8, 3), (FW - 8, 6, 3), (FW - 6, FH - 26, 3), (5, FH - 20, 2),
                                                 (FW // 2, FH - 4, 2), (FW - 14, FH // 3, 1), (FW // 2, 4, 2),
                                                 (8, FH // 2, 2)])
    for x, y, st in stars:
        L.sparkle(c, x, y, st, s3t.GOLD_SPARK)
    return meta(c, card=cid, rarity="Rare Secret", label=label(cid, "Rare Secret", "gold remap, faceted etched gold"),
                finish="gold secret: gold sprite remap, crystalline etched gold, glitter", variant="rare-secret",
                anim="gold", ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S, stars=stars, sprite_recolour="gold",
                frame=FRAMES["Rare Secret"])


KINDS = {"common": build_common, "uncommon": build_uncommon, "rare": build_rare, "holo": build_holo, "v": build_v,
         "vmax": build_vmax, "vstar": build_vstar, "radiant": build_radiant, "alt": build_alt,
         "gallery": build_gallery, "gold": build_gold}


def register(table):
    """add per-card rows {id: cfg} (each with a `kind`) and their builders -- in memory, as the batches do"""
    for cid, row in table.items():
        CFG[cid] = row
        BUILDERS[cid] = (lambda cid=cid: KINDS[CFG[cid]["kind"]](cid))


# ============================================================ the ladder: one real card per printed rarity
# (masks: czmasks SPEC; coordinates read off work/grid_<n>.png)
LADDER = {
    "swsh12pt5-1": dict(kind="common", sprite="oddish"),
    "swsh12pt5-2": dict(kind="uncommon", sprite="gloom", flip=True,
                        mask=dict(model=None, add=[[(160, 170), (200, 125), (330, 120), (370, 170), (420, 200),
                                                    (470, 230), (500, 300), (490, 360), (460, 420), (360, 445),
                                                    (300, 460), (260, 455), (200, 440), (150, 380), (155, 300),
                                                    (190, 250)]])),
    "swsh12pt5-3": dict(kind="rare", sprite="bellossom",
                        mask=dict(model=None, add=[[(290, 150), (330, 110), (420, 100), (480, 120), (520, 170),
                                                    (515, 240), (480, 280), (520, 340), (545, 420), (560, 482),
                                                    (180, 482), (175, 420), (200, 360), (250, 330), (280, 300),
                                                    (300, 270), (285, 220)]])),
    "swsh12pt5-36": dict(kind="holo", sprite="kyogre", flip=True,
                         mask=dict(model=None, add=[[(55, 340), (120, 330), (200, 300), (240, 210), (330, 180),
                                                     (420, 175), (500, 200), (545, 240), (560, 215), (680, 225),
                                                     (680, 290), (600, 290), (560, 330), (545, 390), (460, 400),
                                                     (360, 380), (300, 400), (200, 440), (120, 470), (55, 470)]])),
    "swsh12pt5-13": dict(kind="v", sprite="leafeon", text_y=545,
                         mask=dict(model="u2net", win=(30, 96, 710, 560), keep=1, close=3)),
    "swsh12pt5-54": dict(kind="vmax", sprite="zeraora", text_y=650, texture=False,
                         mask=dict(model=None, add=[[(30, 300), (80, 250), (170, 300), (250, 320), (290, 270),
                                                     (330, 150), (420, 120), (500, 150), (560, 220), (560, 300),
                                                     (520, 380), (600, 420), (680, 450), (700, 560), (690, 650),
                                                     (30, 650)]])),
    "swsh12pt5-14": dict(kind="vstar", sprite="leafeon", text_y=520,
                         mask=dict(model="u2net", win=(30, 92, 710, 540), keep=1, close=4)),
    "swsh12pt5-20": dict(kind="radiant", sprite="charizard", texture=False, grow=7,
                         mask=dict(model="isnet-general-use", win=RAD_WIN, keep=2, close=4,
                                   add=[[(58, 470), (90, 380), (160, 300), (200, 260), (260, 230), (300, 240),
                                         (320, 180), (330, 130), (420, 105), (560, 98), (680, 115), (680, 235),
                                         (560, 265), (540, 330), (560, 420), (500, 445), (420, 425), (330, 470),
                                         (250, 482), (58, 482)],
                                        [(150, 98), (345, 98), (345, 175), (150, 175)]])),
    "swsh12pt5-160": dict(kind="alt", sprite="pikachu", text_y=600, top="basic", frame="#f0c850",
                          mask=dict(model="isnet-general-use", hull=[(220, 300), (260, 170), (330, 200), (400, 150), (440, 60),
                                                                (530, 90), (520, 190), (545, 300), (500, 420),
                                                                (420, 470), (300, 470), (240, 420)], keep=1, close=4),
                          scene="the Pokemon parade"),
    "swsh12pt5gg-GG05": dict(kind="gallery", sprite="lapras", text_y=628,
                             mask=dict(model="u2net", hull=[(170, 200), (430, 200), (440, 420), (470, 560), (470, 640),
                                                               (150, 640), (200, 450), (250, 400)], keep=1, close=4),
                             scene="under the sea"),
    "swsh12pt5gg-GG36": dict(kind="alt", sprite="entei", text_y=615, frame="#f08040", rim_col=(1.0, 0.85, 0.6),
                             mask=dict(model="isnet-general-use", win=(30, 92, 710, 630), keep=1, close=3),
                             scene="the volcano"),
    "swsh12pt5gg-GG35": dict(kind="alt", sprite="leafeon", text_y=535, frame="#9ad06a", rim_col=(1.0, 1.0, 0.85),
                             mask=dict(model=None, add=[[(90, 230), (200, 215), (300, 280), (360, 320), (470, 330),
                                                            (520, 400), (510, 500), (300, 520), (120, 520), (80, 420)]]),
                             scene="the greenhouse"),
    "swsh12pt5gg-GG70": dict(kind="gold", sprite="arceus", text_y=590,
                             mask=dict(model="isnet-general-use", hull=[(250, 100), (470, 100), (480, 300), (440, 520),
                                                                           (290, 520), (260, 300)], keep=2, close=4)),
}
register(LADDER)
ORDER = list(LADDER)
