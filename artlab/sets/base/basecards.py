"""Base Set (base1, 1999): one real card per printed rarity, built the Evolving Skies way (evs), each finished like
its real print. The tier IS the API rarity. No text or logos in the art. Base Set has four printed rarities, all
already approved tiers:

  base1-46  Charmander  Common     the plain sprite, no background (user rule)
  base1-24  Charmeleon  Uncommon   evs Uncommon (Shelgon 108): sprite-scale matte scene, 12 colours
  base1-18  Dragonair   Rare       evs Rare (Altaria 106): WotC rares are non-foil, grid-scale matte, 16 colours
  base1-4   Charizard   Rare Holo  the approved Rare Holo family (evs Salamence 109, tiers.holo_scene: grid scene,
                                   12 colours, foil blended at the scene's luminance, starlight specks, 1-px rim,
                                   4 sparkles), varied toward the WotC Base Set holo sheet: the SWSH diagonal bands
                                   are replaced by the 1999 "starlight" foil -- a soft rainbow nebula with scattered
                                   starbursts and a faint cosmos swirl, inside the art box only. Anim `wotc`: the
                                   wide rainbow band sweeps the art box as the approved `holo` loop does, and the
                                   starbursts flare as it passes, specks glitter, sparkles twinkle

Scan geometry (600 x 825): the art window BASE_WIN inside its gold bevel frame; the Stage 1 / 2 badge STAGE over
the window's top-left corner; everything outside the window is replaced by a membrane of the window (window_rgb),
so the yellow border, the name / HP line, the 1st Edition stamp and the length / weight bar never bleed in.

BUILDERS[id]() -> evlib Card with card.meta = {card, label, rarity, finish, variant, anim, frame, ...}.
"""
import math

import numpy as np
from scipy import ndimage

import baselib as P
from baselib import E, L, Card, Sprite
from evcards import W_LUM, meta, place, rainbow_rgb
import basemasks as BM

BASE_WIN, STAGE = BM.BASE_WIN, BM.STAGE

# the text-half frame colours: the approved tiers' (evs / hf)
FRAMES = {"Common": "#9aa0aa", "Uncommon": "#8fc4a8", "Rare": "#6ea5ff", "Rare Holo": "#56d0e0"}
SPARK_PAL = {"L": "#ffffff", "l": "#fff4b8", "j": "#9fe8ff"}          # tiers.SPARK_PAL (the Rare Holo sparkles)


def window_rgb(cid, boxes=(), grow=6, texture=True, tex_src=None, win=BASE_WIN):
    """evs evcards2.window_rgb for the Base Set window: the scan with the Pokemon + boxes painted out, and
    everything outside the art window boxed out BEFORE the fill (the cz lesson: else the fill mirrors the yellow
    border / name line into holes touching the window edge), then replaced by a membrane of the window"""
    a, b, cc, d = win
    H, W = E.card_img(cid).shape[:2]
    outside = ((0, 0, W, b), (0, d, W, H), (0, 0, a, H), (cc, 0, W, H))
    rgb, _ = E.clean(cid, grow=grow, boxes=tuple(boxes) + outside, texture=texture, tex_src=tex_src)
    m = np.ones(rgb.shape[:2], bool)
    m[b:d, a:cc] = False
    return L.pushpull(rgb, ~m)


def name_of(cid):
    card = P.card_json(cid)
    return f"{card['name']} {card['number']}/{card['set']['printedTotal']}"


def layout(cid, spr, win=BASE_WIN, maxw=52, pad=1):
    """(x0, y0, S, W, H) in the art window: the largest scale that fits the sprite (+pad all round), a crop of the
    window centred on the real Pokemon when the card would be wider than maxw sprite px (hfbatch.layout_window)"""
    a, b, c, d = win
    ww, wh = c - a, d - b
    S = min(wh / (spr.h + 2 * pad), ww / (spr.w + 2 * pad))
    W = min(int(ww / S), max(maxw, spr.w + 2 * pad))
    H = int(wh / S)
    ys, xs = np.nonzero(E.mask(cid))
    cx = (xs.min() + xs.max()) / 2
    x0 = float(np.clip(cx - W * S / 2, a, c - W * S))
    return round(x0, 1), b, round(S, 2), W, H


# ============================================================ Common: Charmander 46
def common(cid, name):
    spr = Sprite(name, flip=cid in P.META.get("flip_commons", []))
    c = Card(spr.w, spr.h)
    c.put_sprite(spr, 0, 0)
    card = P.card_json(cid)
    assert card["tier"] == "Common", (cid, card["tier"])
    return meta(c, card=cid, label=f"Common: {name_of(cid)} -- the plain sprite (commons get no background)",
                rarity="Common", finish="plain sprite, no background (commons rule)", variant="common", anim=None,
                ref=(cid, *BASE_WIN), S=None, frame=FRAMES["Common"])


def charmander():
    return common("base1-46", "charmander")


# ============================================================ Uncommon: Charmeleon 24 (evs Shelgon recipe)
def uncommon_card(cid, spr, crop=None, boxes=(), dx=0, dy=0, scene=""):
    from evcards2 import matte
    x0, y0, S, W, H = crop or layout(cid, spr)
    rgb = window_rgb(cid, boxes=boxes, texture=False)
    c = Card(W, H)
    place(c, spr, cid, x0, y0, S, dx=dx, dy=dy, margin=1)
    matte(c, rgb, x0, y0, S, 12, sat=0.84, bright=0.88)
    sc = f", {scene}" if scene else ""
    return meta(c, card=cid, label=f"Uncommon: {name_of(cid)}{sc} (non-foil)", rarity="Uncommon",
                finish="non-foil: sprite-scale scene, 12 colours", variant="uncommon", anim=None,
                ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S, frame=FRAMES["Uncommon"])


def charmeleon():
    return uncommon_card("base1-24", Sprite("charmeleon"), boxes=(STAGE,), scene="purple crags, lily pads")


# ============================================================ Rare: Dragonair 18 (evs Altaria recipe: non-foil)
def rare_card(cid, spr, crop=None, boxes=(), tex_src=None, grow=8, texture=True, dx=0, dy=0, scene=""):
    from evcards2 import matte
    x0, y0, S, W, H = crop or layout(cid, spr)
    rgb = window_rgb(cid, boxes=boxes, grow=grow, tex_src=tex_src, texture=texture)
    c = Card(W, H)
    place(c, spr, cid, x0, y0, S, dx=dx, dy=dy, margin=1)
    matte(c, rgb, x0, y0, S, 16, sat=0.95, bright=0.95, scale=1)
    sc = f", {scene}" if scene else ""
    return meta(c, card=cid, label=f"Rare: {name_of(cid)}{sc} (non-foil)", rarity="Rare",
                finish="non-foil: grid-scale scene, 16 colours", variant="rare", anim=None,
                ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S, frame=FRAMES["Rare"])


def dragonair():
    return rare_card("base1-18", Sprite("dragonair", flip=True), boxes=(STAGE,), tex_src=(80, 150, 300, 300),
                     scene="aurora over the night sea")


# ============================================================ Rare Holo: Charizard 4 (the WotC holo)
def starbursts(c, seed, per=420, avoid=3, big=0.3):
    """the Base Set holo sheet's starbursts: scattered 4-point stars (a centre px + arms of 1, or 2 on the big
    ones), away from the sprite. -> [(x, y, arm, phase)], centre mask, arm mask"""
    rnd = np.random.default_rng(seed)
    d = c.dist()
    FH, FW = c.FH, c.FW
    n = max(6, int(FW * FH / per))
    pts = []
    tries = 0
    while len(pts) < n and tries < 20000:
        tries += 1
        x, y = int(rnd.integers(2, FW - 2)), int(rnd.integers(2, FH - 2))
        if d[y, x] <= avoid or any(abs(x - a) + abs(y - b) < 7 for a, b, _, _ in pts):
            continue
        pts.append((x, y, 2 if rnd.random() < big else 1, int(rnd.integers(0, 16))))
    ctr = np.zeros((FH, FW), bool)
    arm = np.zeros((FH, FW), bool)
    for x, y, r, _ in pts:
        ctr[y, x] = True
        for k in range(1, r + 1):
            for ax, ay in ((k, 0), (-k, 0), (0, k), (0, -k)):
                X, Y = x + ax, y + ay
                if 0 <= X < FW and 0 <= Y < FH and d[Y, X] > 1.5:
                    arm[Y, X] = True
    return pts, ctr, arm & ~ctr


def swirl(FW, FH, seed):
    """a faint cosmos swirl: one log-spiral arc through the foil (the holo sheet's spiral), 0..1 strength"""
    rnd = np.random.default_rng(seed + 11)
    cx, cy = rnd.uniform(0.2, 0.8) * FW, rnd.uniform(0.25, 0.75) * FH
    yy, xx = np.mgrid[0:FH, 0:FW].astype(float)
    r = np.hypot(xx - cx, yy - cy) + 1e-6
    th = np.arctan2(yy - cy, xx - cx)
    u = (np.log(r) / 0.32 - th) / (2 * math.pi)                      # log spiral, pitch ~ 0.32
    arm = np.exp(-((u - np.round(u)) / 0.07) ** 2)
    fade = np.clip(r / 6, 0, 1) * np.exp(-(r / (0.55 * max(FW, FH))) ** 2)
    return arm * fade


def wotc_holo(cid, spr, x0, y0, S, W, H, rgb, off=None, ncol=12, foil=0.24, seed=0, sparkles=None, halo=True,
              sat=1.0, bright=1.0, rim_amt=0.5, speck_dens=0.012):
    """the Base Set Rare Holo: tiers.holo_scene's scene (grid, ncol colours, 1-px rim) with the WotC starlight
    foil in place of the SWSH diagonal bands"""
    c = Card(W, H)
    place(c, spr, cid, x0, y0, S, off=off, margin=1)
    a = L.sample(rgb, x0, y0, S / 2, 2 * W, 2 * H, resample=L.Image.BOX)
    a = L.tone(a, sat=sat, bright=bright)
    if halo:
        a = L.focus_halo(c, a, radius=4, dark=0.82, soft=1.0)
    _, lbl, pal = L.kmeans_q(a, ncol, seed, ignore=c.fig_mask())
    lbl = L.orphan_clean(lbl, 1)
    d = c.dist()
    rimm = (d > 0) & (d <= 1.01)
    if rim_amt:
        for y, x in zip(*np.nonzero(rimm)):
            want = pal[lbl[y, x]] + (1 - pal[lbl[y, x]]) * rim_amt
            lbl[y, x] = int(np.argmin(np.linalg.norm(pal - want, axis=1)))
    base = pal[lbl]
    FH, FW = c.FH, c.FW
    yy, xx = np.mgrid[0:FH, 0:FW].astype(float)
    # the foil: a soft rainbow nebula (hue drifting in slow waves), stepped to 8 hues so the palette stays small,
    # re-tinting the scene at its own luminance (holo_scene's 'colour' blend) + a faint swirl arc
    hue = 0.55 + 0.22 * np.sin(xx / 13 + seed) * np.cos(yy / 11 - seed * 0.7) + (xx + 0.6 * yy) / 170
    hue = np.floor(hue * 8) / 8
    hb = rainbow_rgb(hue, s=0.62)
    lb = (base @ W_LUM)[..., None]
    tint = np.clip(hb / np.maximum(hb @ W_LUM, 1e-3)[..., None] * lb * 1.08 + 0.03, 0, 1)
    sw = swirl(FW, FH, seed) * (d > 2)
    amt = foil + 0.16 * sw
    q = base + (tint - base) * amt[..., None]
    q = q + (1 - q) * (0.10 * sw)[..., None]
    q = L.median_q(q, 96)
    q_pre = q.copy()
    # starbursts (pale foil stars, a hue of their own) and starlight specks
    pts, ctr, arm = starbursts(c, seed)
    sh = rainbow_rgb(hue + 0.5, s=0.25)
    q = np.where(ctr[..., None], q + (1 - q) * 0.85, q)
    q = np.where(arm[..., None], q + (sh - q) * 0.5, q)
    rnd = np.random.default_rng(seed + 3)
    specks = (rnd.random((FH, FW)) < speck_dens) & (d > 3) & ~ctr & ~arm
    q = np.where(specks[..., None], np.where((rnd.random((FH, FW)) < 0.3)[..., None], (1.0, 0.99, 0.93),
                                             (0.8, 0.9, 1.0)), q)
    c.bg = q
    c.bgq = L.to8(q)
    sparkles = sparkles if sparkles is not None else [(5, 5, 3), (FW - 6, 6, 2), (FW - 6, FH - 6, 3), (4, FH - 8, 2)]
    for x, y, st in sparkles:
        L.sparkle(c, x, y, st, SPARK_PAL)
    return meta(c, stars=list(sparkles), bursts=pts, burst_ctr=ctr, burst_arm=arm, specks=specks, q_pre=q_pre,
                foil_hue=hue, S=S)


def holo_card(cid, spr, crop=None, boxes=(), tex_src=None, grow=5, texture=True, dx=0, dy=0, seed=None, scene="",
              **kw):
    x0, y0, S, W, H = crop or layout(cid, spr)
    rgb = window_rgb(cid, boxes=boxes, grow=grow, tex_src=tex_src, texture=texture)
    off = E.anchor(cid, x0, y0, S, spr, dx, dy)
    off = (max(1, min(W - spr.w - 1, off[0])), max(1, min(H - spr.h - 1, off[1])))
    seed = seed if seed is not None else int(E.num(cid))
    c = wotc_holo(cid, spr, x0, y0, S, W, H, rgb, off=off, seed=seed, **kw)
    sc = f", {scene}" if scene else ""
    return meta(c, card=cid, label=f"Rare Holo: {name_of(cid)}{sc} (WotC starlight holo in the art box)",
                rarity="Rare Holo", finish="WotC rare holo: starlight foil (rainbow nebula, starbursts, faint cosmos "
                                           "swirl) + specks inside the art box (the Rare Holo family)",
                variant="rare-holo", anim="wotc", ref=(cid, x0, y0, x0 + W * S, y0 + H * S),
                frame=FRAMES["Rare Holo"])


def charizard():
    return holo_card("base1-4", Sprite("charizard"), boxes=(STAGE,), tex_src=(70, 160, 175, 300),
                     scene="flame breath over the holo starfield")


# rarity order, commonest first
BUILDERS = {"base1-46": charmander, "base1-24": charmeleon, "base1-18": dragonair, "base1-4": charizard}
ORDER = list(BUILDERS)
