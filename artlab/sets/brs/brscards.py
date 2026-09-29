"""Brilliant Stars (swsh9 + the Trainer Gallery swsh9tg): every builder of the set, one per printed-rarity finish,
driven by a per-card CFG table (so the batch modules add rows, never code). These are the approved recipes, copied
from Crown Zenith (artlab/sets/cz/czcards.py: its VSTAR crest and Trainer Gallery builders exactly as approved) and
from Evolving Skies (the full-art Rare Ultra of batch_ultra_a / Glaceon V 174 and the true Rare Rainbow of
batch_rainbow_secret / Leafeon VMAX 204). No new effect is invented for this set:

  kind      printed rarity              approved example / recipe                                   anim
  common    Common                      evs Eevee 125: the plain sprite, no background              -
  uncommon  Uncommon                    evs Shelgon 108: matte, sprite-scale scene, 12 colours       -
  rare      Rare                        evs Altaria 106: matte, grid-scale scene, 16 colours        -
  holo      Rare Holo                   evs Salamence 109: tiers.holo_scene in the SWSH window      holo
  v         Rare Holo V                 evs Sylveon V 74 (cz build_v)                               sunpillar
  vmax      Rare Holo VMAX              evs Vaporeon VMAX 30: gunmetal frame, contour grooves       sunpillar
  vstar     Rare Holo VSTAR             cz Leafeon VSTAR 14: VMAX scene + grooves, platinum-gold    vstar
                                        grooved frame, gold star-crest rays
  fullart   Rare Ultra (full art)       evs Glaceon V 174 (batch_ultra_a): LANCZOS painting, glow   etch
                                        + 12 rays, tinted vignette, fingerprint etch
  alt       any tier, painted alt art   evs Umbreon VMAX 215 (cz build_alt)                         paint
            (the Rare Ultra alt arts, the Trainer Gallery V / VMAX)
  rainbow   Rare Rainbow (true rainbow) evs Leafeon VMAX 204: smooth fill, rainbow sprite 0.55,     rainbow
                                        pastel rainbow ground, diagonal etch, glitter
  gallery   Trainer Gallery Rare Holo   cz Lapras GG05: painting, soft emboss, linen weave, sheen   gallery
  gold      Rare Secret (gold)          evs Froslass 226: gold remap, faceted etched gold           gold

BUILDERS[id]() -> evlib Card with card.meta = {card, label, rarity, finish, variant, anim, frame ...}.
"""
import math

import numpy as np
from scipy import ndimage

import brslib as P
from brslib import E, L, Card, Sprite
import brsmasks as CM
import evcards2 as B2
from evcards import (W_LUM, colour_blend, fingerprint, meta, place, rainbow_etch, rainbow_rgb, rainbow_sprite,
                     silver_frame)

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

FRAMES = {"Common": "#9aa0aa", "Uncommon": "#8fc4a8", "Rare": "#6ea5ff", "Rare Holo": "#56d0e0",
          "Rare Holo V": "#c9d1da", "Rare Holo VMAX": "#8f9cff", "Rare Holo VSTAR": "#e6c86e",
          "Trainer Gallery Rare Holo": "#f4b6d6", "Rare Secret": "#f0c850",
          "Rare Ultra": "#e178e6", "Rare Rainbow": "rainbow"}
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
                strike=False, text_y=640, gloss=None, glow=(1.0, 0.95, 0.8),
                glow_amt=0.36, tint=(0.1, 0.1, 0.2))


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
                       sparkles=stars, seed=P.seed_of(cid))
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
    tg = " Trainer Gallery" if P.is_tg(cid) else ""
    return meta(c, card=cid, rarity=rarity,
                label=label(cid, f"{rarity}{tg} (alt art)", "textured painting"),
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
                label=label(cid, "Trainer Gallery Rare Holo", "painting, linen weave, pastel sheen"),
                finish="Trainer Gallery: the painting, soft brushwork emboss, linen weave texture, pastel holo sheen",
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
    seed = P.seed_of(cid)
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


# ============================================================ Rare Ultra, full art (Glaceon V 174, batch_ultra_a)
FA_TOP = ((0, 0, 734, 100), (0, 0, 70, 230))      # batch_ultra_a EDGES: the name bar + the V logo's arm corner


def whorls_for(c):
    """off-centre whorls like Glaceon's (top-left, bottom-right, top-right corners) scaled to the grid"""
    FW, FH = c.FW, c.FH
    return [(12 / 84 * FW, 10 / 66 * FH, 1.0), (70 / 84 * FW, 52 / 66 * FH, 0.8), (64 / 84 * FW, 8 / 66 * FH, 0.5)]


def build_fullart(cid):
    """batch_ultra_a.make_builder in substance: W = max(42, sprite w + 6), H = max(33, sprite h + 3), S = 714 / W
    from x0 10, y0 80; the painting (LANCZOS), sat 1.12, focus halo r5, radial glow 0.36 + 12 rays, tinted
    vignette 0.5, fingerprint etch (+0.11 / -0.025), median 170, rim 0.34, four sparkles"""
    k = cfg(cid)
    spr = Sprite(k["sprite"], flip=k["flip"])
    W = k["W"] or max(42, spr.w + 6)
    H = k["H"] or max(33, spr.h + 3)
    x0 = k["x0"] if k["x0"] is not None else 10
    y0 = k["y0"] if k["y0"] is not None else 80
    S = k["S"] or 714 / W
    boxes = [*EDGES, *FA_TOP, (0, k["text_y"], 734, 1024), *k["boxes"]] + ([STRIKE] if k["strike"] else [])
    rgb = clean(cid, boxes, (V_ARM, *k["polys"]), k["grow"], k["texture"], k["tex_src"])
    c = Card(W, H)
    put(c, spr, cid, x0, y0, S, k)
    a = L.sample(rgb, x0, y0, S / 2, 2 * W, 2 * H, resample=L.Image.LANCZOS)
    a = L.tone(a, sat=k["sat"] or 1.12, bright=k["bright"] or 1.0)
    a = L.focus_halo(c, a, radius=5, dark=0.7, soft=1.4)
    a = L.radial_glow(c, a, k["glow"], max(c.FW, c.FH) * 0.55, k["glow_amt"], rays=12, ray_amt=0.5)
    a = L.vignette(a, 0.5 if "vign" not in CFG[cid] else k["vign"], tint=k["tint"])
    f, line = fingerprint(c.FW, c.FH, whorls_for(c), period=2.6, seed=P.seed_of(cid))
    lift = np.where(line, 0.11, -0.025)
    a = np.clip(a + lift[..., None] * (0.6 + 0.4 * a), 0, 1)
    L.finish(c, a, 170, method="median")
    c.bgq = L.rim(c, c.bgq, colour=k["rim_col"], amt=0.34 if "rim" not in CFG[cid] else k["rim"])
    FW, FH = c.FW, c.FH
    stars = k["stars"] or [(6, 6, 3), (FW - 6, 10, 2), (FW - 8, FH - 8, 3), (5, FH - 16, 2)]
    for x, y, st in stars:
        L.sparkle(c, x, y, st, k["star"] or WHITE_STAR)
    return meta(c, card=cid, rarity="Rare Ultra", label=label(cid, "Rare Ultra", "full art, fingerprint etch"),
                finish="full-art V: fingerprint-like etched texture, rainbow on the lines", variant="rare-ultra",
                anim="etch", ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S, stars=stars, etch_field=f,
                etch_period=2.6, frame=FRAMES["Rare Ultra"])


# ============================================================ Rare Rainbow, true rainbow (Leafeon VMAX 204)
RB_GEO = (17, 78, 17.5, 700, 595, 40, 34)         # batch_rainbow_secret.GEO["rainbow"]: 40x34 at S 17.5
RB_TOP = ((0, 0, 734, 80), (0, 30, 112, 150), (95, 78, 345, 145))   # its TOP, VMAX_LOGO, EVOLVES


def build_rainbow(cid):
    """batch_rainbow_secret.build_rainbow + its card() geometry: smooth fill (grow 14), the sprite re-tinted
    RAINBOW_BLEND 0.55 toward its body rainbow, the ground colour_blend(a*0.9+0.12, rainbow, 0.5), the seed-204
    diagonal etch (-0.07 / +0.025), 3 % glitter, median 150, white rim 0.5. `top="vstar"` (default) paints out the
    VSTAR header (icon, metallic corner) instead of the VMAX logo"""
    k = cfg(cid)
    x0f, y0f, smax, cw, ch, wmin, hmin = RB_GEO
    spr = Sprite(k["sprite"], flip=k["flip"])
    H = k["H"] or max(hmin, spr.h + 3)
    S = k["S"] or min(smax, ch / H)
    W = k["W"] or max(wmin, spr.w + 6, round(cw / S))
    x0 = k["x0"] if k["x0"] is not None else 367 - W * S / 2
    y0 = k["y0"] if k["y0"] is not None else y0f
    tb = ((0, 0, 734, 92), VSTAR_ICON, VSTAR_CORNER, EVOLVES) if k.get("top", "vstar") == "vstar" else RB_TOP
    boxes = [*EDGES, *tb, (0, k["text_y"], 734, 1024), *k["boxes"]] + ([STRIKE] if k["strike"] else [])
    rgb = clean(cid, boxes, k["polys"], 14 if "grow" not in CFG[cid] else k["grow"], False)
    c = Card(W, H)
    put(c, spr, cid, x0, y0, S, k)
    rainbow_sprite(c)
    a = L.sample(rgb, x0, y0, S / 2, 2 * W, 2 * H, resample=L.Image.LANCZOS)
    FH, FW = c.FH, c.FW
    yy, xx = np.mgrid[0:FH, 0:FW]
    hue = -0.04 + (xx / FW * 0.5 + yy / FH * 0.42) + k.get("hue_shift", 0.0)
    a = colour_blend(np.clip(a * 0.9 + 0.12, 0, 1), rainbow_rgb(hue, s=0.45), 0.5)
    a = L.tone(a, sat=1.05, bright=1.0)
    a = L.focus_halo(c, a, radius=4, dark=0.82, soft=1.2)
    line, glint = rainbow_etch(FW, FH, seed=204)          # anim_rainbow flashes the seed-204 lines
    a = np.clip(a + np.where(line, -0.07, 0.025)[..., None], 0, 1)
    L.finish(c, a, 150, method="median")
    q = c.bgq.astype(float) / 255
    d = c.dist()
    g = glint & (d > 2)
    q[g] = np.clip(q[g] * 0.3 + 0.75, 0, 1)
    c.bgq = L.to8(q)
    c.bgq = L.rim(c, c.bgq, colour=(1, 1, 1), amt=0.5)
    stars = k["stars"] or stars_for(c, 5, cands=[(6, 6, 3), (FW - 8, 8, 2), (FW - 6, FH - 8, 3), (6, FH - 12, 2),
                                                 (FW // 2, 3, 1), (FW // 4, FH - 4, 2), (FW - 4, FH // 2, 2),
                                                 (4, FH // 2, 2), (3 * FW // 4, 4, 2)])
    for x, y, st in stars:
        L.sparkle(c, x, y, st, {"L": "#ffffff", "l": "#fff0fa", "j": "#b8f0ff"})
    return meta(c, card=cid, rarity="Rare Rainbow", label=label(cid, "Rare Rainbow", "rainbow secret"),
                finish="rainbow secret: pastel rainbow gradient, dense etched texture, glitter", variant="rare-rainbow",
                anim="rainbow", ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S, stars=stars, frame="rainbow",
                glint=[(int(x), int(y)) for y, x in zip(*np.nonzero(g))])


KINDS = {"common": build_common, "uncommon": build_uncommon, "rare": build_rare, "holo": build_holo, "v": build_v,
         "vmax": build_vmax, "vstar": build_vstar, "alt": build_alt,
         "gallery": build_gallery, "gold": build_gold, "fullart": build_fullart,
         "rainbow": build_rainbow}


def register(table):
    """add per-card rows {id: cfg} (each with a `kind`) and their builders -- in memory, as the batches do"""
    for cid, row in table.items():
        CFG[cid] = row
        BUILDERS[cid] = (lambda cid=cid: KINDS[CFG[cid]["kind"]](cid))



# ============================================================ the ladder: one real card per printed rarity
# (masks: brsmasks SPEC; coordinates read off work/grid_<n>.png)
def hand(*polys, close=0):
    """poly_only: the mask is the hand polygon(s), card px read off work/grid_<n>.png"""
    return dict(model=None, add=list(polys), close=close)


LADDER = {
    "swsh9-6": dict(kind="common", sprite="turtwig"),
    "swsh9-7": dict(kind="uncommon", sprite="grotle", flip=True, scene="the forest",
                    mask=hand([(160, 190), (170, 150), (230, 120), (330, 108), (420, 108), (480, 128), (545, 190),
                               (575, 250), (578, 300), (560, 335), (545, 345), (565, 400), (595, 440), (565, 462),
                               (480, 458), (440, 440), (360, 452), (240, 448), (178, 440), (168, 380), (160, 320),
                               (170, 290), (158, 240)])),
    "swsh9-51": dict(kind="rare", sprite="luxray", flip=True, scene="the thunderstorm",
                     mask=hand([(165, 245), (200, 205), (250, 190), (300, 195), (345, 145), (362, 100), (420, 125),
                                (470, 160), (528, 180), (535, 262), (505, 300), (512, 380), (555, 440), (470, 448),
                                (420, 432), (370, 442), (310, 442), (250, 440), (212, 400), (228, 300), (196, 285),
                                (172, 262)])),
    "swsh9-8": dict(kind="holo", sprite="torterra", scene="the herd on the hill", texture=False,
                    mask=hand([(128, 262), (160, 208), (222, 196), (300, 196), (362, 186), (420, 146), (472, 126),
                               (545, 158), (602, 228), (642, 338), (665, 402), (602, 414), (552, 434), (472, 444),
                               (422, 464), (330, 464), (250, 464), (198, 444), (168, 402), (138, 330)])),
    "swsh9-17": dict(kind="v", sprite="charizard", flip=True, text_y=680, texture=False, scene="the firestorm",
                     mask=hand([(30, 669), (30, 420), (70, 330), (120, 240), (200, 190), (270, 148), (300, 175),
                                (340, 210), (380, 110), (430, 108), (440, 210), (510, 225), (580, 240), (630, 270),
                                (645, 335), (600, 372), (565, 400), (630, 440), (695, 490), (705, 560), (705, 669)])),
    "swsh9-29": dict(kind="vmax", sprite="kingler-gmax", text_y=630, texture=False, scene="the bubble vortex",
                     mask=hand([(30, 280), (80, 255), (170, 238), (200, 150), (300, 76), (430, 70), (500, 140),
                                (560, 128), (640, 78), (705, 100), (705, 640), (30, 640)])),
    "swsh9-18": dict(kind="vstar", sprite="charizard", text_y=545, texture=False, scene="the green flame burst",
                     mask=hand([(30, 210), (100, 160), (150, 130), (260, 108), (330, 150), (380, 118), (470, 100),
                                (520, 200), (560, 228), (640, 248), (705, 320), (705, 560), (30, 560)])),
    "swsh9-152": dict(kind="fullart", sprite="shaymin-sky", text_y=680, glow=(1.0, 0.92, 0.85), tint=(0.3, 0.05, 0.1),
                      rim_col=(1.0, 0.97, 0.9), star={"L": "#ffffff", "l": "#fff0f4", "j": "#ffc0d8"},
                      scene="the pink-orange swirl",
                      mask=hand([(40, 420), (80, 330), (180, 158), (262, 208), (300, 282), (340, 258), (400, 178),
                                 (480, 138), (560, 128), (705, 158), (705, 300), (600, 332), (560, 400), (522, 450),
                                 (585, 500), (545, 572), (525, 650), (505, 690), (200, 690), (180, 600), (140, 560),
                                 (90, 480)])),
    "swsh9-154": dict(kind="alt", sprite="charizard", text_y=690, frame="#f08040", rim_col=(1.0, 0.85, 0.6),
                      tex_src=(40, 250, 190, 380), scene="the valley with Venusaur",
                      mask=hand([(140, 100), (230, 90), (420, 95), (560, 180), (705, 190), (705, 700), (560, 700),
                                 (430, 665), (330, 645), (288, 600), (345, 522), (250, 472), (238, 360), (268, 300),
                                 (328, 250), (298, 205), (200, 192), (160, 180)])),
    "swsh9-174": dict(kind="rainbow", sprite="charizard", text_y=555, scene="the rainbow blaze",
                      mask=hand([(30, 180), (90, 150), (170, 128), (280, 108), (420, 98), (520, 160), (640, 228),
                                 (705, 280), (705, 560), (30, 560)])),
    "swsh9-184": dict(kind="gold", sprite="arceus", flip=True, text_y=530,
                      mask=hand([(40, 180), (120, 110), (300, 100), (470, 98), (560, 148), (640, 250), (665, 400),
                                 (640, 540), (40, 540)])),
    "swsh9tg-TG11": dict(kind="gallery", sprite="eevee", text_y=590, scene="the lab desk",
                         mask=hand([(35, 210), (90, 240), (140, 300), (180, 285), (240, 200), (290, 215), (300, 320),
                                    (335, 390), (390, 400), (430, 420), (520, 400), (600, 395), (655, 420), (640, 500),
                                    (560, 560), (520, 600), (90, 600), (60, 520), (50, 420), (60, 330)])),
    "swsh9tg-TG22": dict(kind="alt", sprite="umbreon", text_y=620, strike=True, frame="#f0c850",
                         rim_col=(1.0, 0.9, 0.55), scene="the station at dusk",
                         mask=hand([(235, 185), (260, 200), (300, 280), (360, 300), (390, 200), (420, 150), (470, 80),
                                    (505, 130), (525, 210), (522, 300), (562, 380), (602, 460), (642, 560), (652, 640),
                                    (250, 640), (260, 560), (270, 470), (260, 390), (245, 300)])),
    "swsh9tg-TG23": dict(kind="alt", sprite="umbreon", flip=True, text_y=660, strike=True, texture=False,
                         frame="#f0c850", rim_col=(1.0, 0.55, 0.85), scene="the city night",
                         mask=dict(model=None, add=[[(30, 120), (120, 110), (200, 170), (260, 300), (300, 250),
                                                     (420, 150), (430, 60), (520, 40), (580, 120), (620, 200),
                                                     (640, 300), (680, 420), (705, 500), (705, 670), (30, 670)]],
                                   cut_after=[[(292, 322), (360, 300), (420, 420), (400, 470), (392, 560),
                                               (372, 645), (300, 645), (280, 560), (272, 450)]], fill=False)),
    "swsh9tg-TG29": dict(kind="gold", sprite="urshifu-gmax", text_y=650, boxes=[STRIKE],
                         mask=hand([(30, 150), (200, 140), (300, 90), (420, 90), (500, 160), (600, 180), (705, 230),
                                    (705, 650), (30, 650)])),
}
register(LADDER)
ORDER = list(LADDER)
