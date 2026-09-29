"""Hidden Fates (sm115) and its Shiny Vault (sma): one real card per printed rarity, built the Evolving Skies way
(evs), each finished like its real print. The tier IS the API rarity. No text or logos in the art.

  sm115-7   Charmander      Common          the plain sprite, no background (user rule)
  sm115-8   Charmeleon      Uncommon        evs Uncommon (Shelgon 108): sprite-scale matte scene, 12 colours
  sm115-32  Mew             Rare            evs Rare (Altaria 106): SM rares are non-foil, grid-scale matte, 16 colours
  sm115-18  Vaporeon        Rare Holo       evs Rare Holo (Salamence 109) in the SM art window
  sm115-9   Charizard-GX    Rare Holo GX    NEW: the SM GX card -- art frame to frame under a silver frame, the GX
                                            "water-web" holo: a fine cracked-web of foil lines over the scene, a
                                            faint rainbow in the cells; anim `gxweb`: a sheen sweeps and the web
                                            lines light up along it
  sma-SV6   Charmander      Rare Shiny      NEW (Shiny Vault): the SHINY sprite, pixel-exact, in the card's art
                                            window. The window's own sparkle-star pattern (painted-out scene)
                                            re-cut as black-and-silver vault foil: brushed gunmetal, the stars
                                            embossed in silver, glitter, 4-point stars; anim `vault`: a silver
                                            specular sweep with thin prismatic fringes, the stars catch it, glitter
  sma-SV49  Charizard-GX    Rare Shiny GX   NEW: the step above -- full-art crop, the same vault foil with an
                                            etched (fingerprint) texture, bigger star flares, a silver bevel frame;
                                            anim `vaultgx`: a silver beam pair over window + frame, the etched
                                            lines flash along it, the flares bloom
  sma-SV93  Tapu Koko-GX    Rare Secret     SM gold GX: evs Rare Secret (Froslass 226) gold remap + faceted gold

The Shiny Vault look has two versions for the user's sign-off (VAULT_TONE): "dark" (black-and-silver vault foil,
as briefed, the default) and "silver" (the scan's white window read as bright silver foil).

BUILDERS[id]() -> evlib Card with card.meta = {card, label, rarity, finish, variant, anim, frame, ...}.
"""
import numpy as np
from scipy import ndimage

import hflib as P
from hflib import E, L, Card, Sprite, ShinySprite
from evcards import SILVER, W_LUM, colour_blend, fingerprint, meta, place, rainbow_rgb, silver_frame
import hfmasks as HM

SM_WIN, ICON, EVOLVES = HM.SM_WIN, HM.ICON, HM.EVOLVES
EDGES = ((0, 0, 28, 1024), (706, 0, 734, 1024))
TOP = (0, 0, 734, 92)                        # name bar, HP, type, the BASIC / STAGE tag

FRAMES = {"Common": "#9aa0aa", "Uncommon": "#8fc4a8", "Rare": "#6ea5ff", "Rare Holo": "#56d0e0",
          "Rare Holo GX": "#6fa8dc", "Rare Shiny": "#b4c0ce", "Rare Shiny GX": "#e6ecf5", "Rare Secret": "#f0c850",
          "Rare Ultra": "#e178e6", "Rare Rainbow": "rainbow"}


def window_rgb(cid, boxes=(), grow=6, texture=True, tex_src=None, win=SM_WIN):
    """evs evcards2.window_rgb for the SM window: the scan with the Pokemon + boxes painted out, and everything
    outside the art window replaced by a membrane of the window"""
    rgb, _ = E.clean(cid, grow=grow, boxes=boxes, texture=texture, tex_src=tex_src)
    a, b, cc, d = win
    m = np.ones(rgb.shape[:2], bool)
    m[b:d, a:cc] = False
    return L.pushpull(rgb, ~m)


def name_of(cid):
    card = P.card_json(cid)
    return f"{card['name']} {card['number']}/{card['set']['printedTotal']}"


# ============================================================ Common: Charmander 7
def charmander():
    cid = "sm115-7"
    spr = Sprite("charmander")
    c = Card(spr.w, spr.h)
    c.put_sprite(spr, 0, 0)
    return meta(c, card=cid, label=f"Common: {name_of(cid)} -- the plain sprite (commons get no background)",
                rarity="Common", finish="plain sprite, no background (commons rule)", variant="common", anim=None,
                ref=(cid, *SM_WIN), S=None, frame=FRAMES["Common"])


# ============================================================ Uncommon: Charmeleon 8 (evs Shelgon recipe)
def charmeleon():
    from evcards2 import matte
    cid = "sm115-8"
    x0, y0, S, W, H = 58, 100, 16, 38, 24
    rgb = window_rgb(cid, boxes=(ICON, EVOLVES), texture=False)
    spr = Sprite("charmeleon", flip=True)
    c = Card(W, H)
    place(c, spr, cid, x0, y0, S, margin=1)
    matte(c, rgb, x0, y0, S, 12, sat=0.84, bright=0.88)
    return meta(c, card=cid, label=f"Uncommon: {name_of(cid)}, mountain crag (non-foil)", rarity="Uncommon",
                finish="non-foil: sprite-scale scene, 12 colours", variant="uncommon", anim=None,
                ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S, frame=FRAMES["Uncommon"])


# ============================================================ Rare: Mew 32 (evs Altaria recipe: SM rares are non-foil)
def mew():
    from evcards2 import matte
    cid = "sm115-32"
    x0, y0, S, W, H = 58, 100, 14, 44, 27
    rgb = window_rgb(cid, grow=8, tex_src=(70, 110, 200, 300))
    spr = Sprite("mew", flip=True)
    c = Card(W, H)
    place(c, spr, cid, x0, y0, S, margin=1)
    matte(c, rgb, x0, y0, S, 16, sat=0.95, bright=0.95, scale=1)
    return meta(c, card=cid, label=f"Rare: {name_of(cid)}, coral sky (non-foil)", rarity="Rare",
                finish="non-foil: grid-scale scene, 16 colours", variant="rare", anim=None,
                ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S, frame=FRAMES["Rare"])


# ============================================================ Rare Holo: Vaporeon 18 (evs Salamence recipe)
def vaporeon():
    import tiers as s3t
    cid = "sm115-18"
    x0, y0, S, W, H = 58, 100, 11.9, 51, 32
    rgb = window_rgb(cid, boxes=(ICON, EVOLVES), grow=5, tex_src=(560, 300, 670, 470))
    spr = Sprite("vaporeon")
    off = E.anchor(cid, x0, y0, S, spr)
    off = (max(1, min(W - spr.w - 1, off[0])), max(1, min(H - spr.h - 1, off[1])))
    c = s3t.holo_scene(spr, cid, None, x0, y0, S, W, H, cid, "", off=off, rgb=rgb, ncol=12, foil=0.22, bright=1.0,
                       sparkles=[(5, 5, 3), (2 * W - 6, 6, 2), (2 * W - 6, 2 * H - 6, 3), (4, 2 * H - 8, 2)], seed=18)
    return meta(c, card=cid, label=f"Rare Holo: {name_of(cid)}, sea spray (holo in the art box)",
                rarity="Rare Holo", finish="SM rare holo: rainbow foil bands + starlight inside the art box (evs Rare Holo)",
                variant="rare-holo", anim="holo", ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S,
                frame=FRAMES["Rare Holo"])


# ============================================================ Rare Holo GX: Charizard-GX 9 (NEW)
def gx_web(FW, FH, seed=0, cell=7.0):
    """the SM GX holo: a cracked web of foil lines (Voronoi cell borders of jittered points, ~`cell` grid px
    apart) -> (line mask, cell id, cell hue 0..1)"""
    rnd = np.random.default_rng(seed)
    pts = []
    for j, y in enumerate(np.arange(-cell, FH + cell, cell * 0.87)):
        for x in np.arange(-cell + (j % 2) * cell / 2, FW + cell, cell):
            pts.append((x + rnd.uniform(-2.2, 2.2), y + rnd.uniform(-2.2, 2.2)))
    pts = np.array(pts)
    yy, xx = np.mgrid[0:FH, 0:FW].astype(float)
    d = np.hypot(xx[..., None] - pts[:, 0], yy[..., None] - pts[:, 1])
    o = np.argsort(d, -1)
    d1 = np.take_along_axis(d, o[..., :1], -1)[..., 0]
    d2 = np.take_along_axis(d, o[..., 1:2], -1)[..., 0]
    line = (d2 - d1) < 0.85
    cid_ = o[..., 0]
    hue = (pts[cid_, 0] * 0.9 + pts[cid_, 1] * 0.5) / 70.0
    return line, cid_, hue


def gx_card(cid, spr, x0, y0, S, W, H, boxes, tex_src=None, sat=1.25, bright=1.0, gamma=1.05, seed=None,
            off=None, dx=0, dy=0, stars=None, scene="", texture=True, label_extra=""):
    """the Rare Holo GX recipe, parameterised for the holo_gx batch"""
    seed = seed if seed is not None else sum(map(ord, cid))
    rgb, _ = E.clean(cid, grow=5, boxes=boxes, tex_src=tex_src, texture=texture)
    c = Card(W, H)
    place(c, spr, cid, x0, y0, S, off=off, dx=dx, dy=dy, margin=1)
    a = L.sample(rgb, x0, y0, S / 2, 2 * W, 2 * H, resample=L.Image.BOX)
    a = L.tone(a, sat=sat, bright=bright, gamma=gamma)
    a = L.focus_halo(c, a, radius=3, dark=0.85, soft=1.0)
    _, lbl, pal = L.kmeans_q(a, 28, 0, ignore=c.fig_mask())
    base = pal[L.orphan_clean(lbl, 1)]
    FH, FW = c.FH, c.FW
    line, _, hue = gx_web(FW, FH, seed)
    lum = base @ W_LUM
    q = colour_blend(base, rainbow_rgb(hue, s=0.55), 0.10 + 0.06 * lum)               # faint rainbow per web cell
    lift = np.where(line, 0.10 + 0.08 * lum, 0.0)
    q = np.clip(q + lift[..., None] * (0.7 + 0.3 * q), 0, 1)
    q = colour_blend(q, rainbow_rgb(hue + 0.25, s=0.5), np.where(line, 0.25, 0.0))     # the lines' own sheen
    q = L.median_q(q, 84)
    d = c.dist()
    rim = (d > 0) & (d <= 1.01)
    q[rim] = q[rim] + (1 - q[rim]) * 0.45
    q = silver_frame(c, q, width=2, ramp_hex=SILVER)
    ring = c.meta["frame_ring"]
    c.bg = q
    c.bgq = L.to8(q)
    stars = stars or [(8, 8, 3), (FW - 10, 8, 2), (FW - 9, FH - 9, 3), (8, FH - 10, 2)]
    stars = [(x, y, st) for (x, y, st) in stars if x < FW and y < FH]
    for x, y, st in stars:
        L.sparkle(c, x, y, st, {"L": "#ffffff", "l": "#e8f2ff", "j": "#9fd0ff"})
    sc = f", {scene}" if scene else ""
    return meta(c, card=cid, label=f"Rare Holo GX: {name_of(cid)}{sc} (silver frame, GX web holo){label_extra}",
                rarity="Rare Holo GX", finish="SM GX holo: art frame to frame, silver frame, cracked-web foil lines + faint rainbow cells",
                variant="rare-holo-gx", anim="gxweb", ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S, stars=stars,
                web=line & ~ring & (d > 1.01), web_hue=hue, frame=FRAMES["Rare Holo GX"])


def charizard_gx():
    cid = "sm115-9"
    x0, y0, S, W, H = 28, 92, 13.6, 49, 42
    boxes = EDGES + (TOP, ICON, EVOLVES, (0, 665, 734, 1024))
    spr = Sprite("charizard")
    return gx_card(cid, spr, x0, y0, S, W, H, boxes, tex_src=(560, 110, 700, 240), scene="flame breath over the crags")


# ============================================================ Shiny Vault: the vault foil (NEW)
VAULT = ["#07080b", "#121419", "#20242b", "#343942", "#4f5661", "#737b87", "#9aa3ae", "#c3cad3", "#e4e9ef", "#ffffff"]
VAULT_TONE = "dark"                          # "dark": black-and-silver (default); "silver": the white window as silver
VAULT_STAR = {"L": "#ffffff", "l": "#eef3fa", "j": "#b9c6d6"}


def ramp(t, hexes=VAULT):
    r = np.array([L.hexrgb(h) for h in hexes], float) / 255
    t = np.clip(t, 0, 1) * (len(r) - 1)
    i = np.minimum(np.floor(t).astype(int), len(r) - 2)
    f = (t - i)[..., None]
    return r[i] + (r[i + 1] - r[i]) * f


def star_map(a):
    """the vault window's printed sparkle-star pattern: pale gold / cream marks on white (or any non-white ink
    left in the painted-out scene) -> 0..1"""
    from skimage.color import rgb2hsv
    h = rgb2hsv(np.clip(a, 0, 1))
    s, v = h[..., 1], h[..., 2]
    m = np.clip((s - 0.035) / 0.16, 0, 1) * np.clip(v * 1.2, 0, 1) + np.clip((0.86 - v) / 0.4, 0, 1) * 0.6
    return np.clip(ndimage.gaussian_filter(m, 0.5), 0, 1)


def hole_map(cid, x0, y0, S, W, H, grow=6, boxes=(), win=None):
    """1 where the grid px lies in the painted-out hole (the real Pokemon grown, the text / logo boxes, and
    outside `win`): there the vault foil is plain metal, no printed stars (they would be the fill's ghosts)"""
    m = E.mask(cid).copy()
    if grow:
        m = ndimage.binary_dilation(m, iterations=grow)
    for (a, b, c_, d) in boxes:
        m[max(0, b):d, max(0, a):c_] = True
    if win is not None:
        k = np.ones_like(m)
        k[win[1]:win[3], win[0]:win[2]] = False
        m |= k
    f = np.repeat(m[..., None].astype(float), 3, -1)
    return L.sample(f, x0, y0, S / 2, 2 * W, 2 * H, resample=L.Image.BOX)[..., 0]


def vault_bg(a, seed=0, tone=None, etch=None, hole=None):
    """the vault foil from the card's own (painted-out) scene: brushed metal, the printed stars embossed in
    silver. dark: gunmetal-black metal, stars bright silver; silver: bright silver metal, stars as a raised
    silver-white relief. etch: an optional line mask (Rare Shiny GX) cut into the metal. -> (rgb, star map)"""
    tone = tone or VAULT_TONE
    FH, FW = a.shape[:2]
    st = star_map(a)
    if hole is not None:
        st = st * np.clip(1 - hole, 0, 1) ** 2
    rnd = np.random.default_rng(seed)
    brush = ndimage.gaussian_filter(rnd.random((FH, FW)), (0.3, 3.0))            # horizontal brushed grain
    brush = (brush - brush.mean()) / max(1e-6, brush.std())
    yy, xx = np.mgrid[0:FH, 0:FW]
    sweep = np.exp(-((((xx + yy) / (FW + FH)) - 0.3) / 0.22) ** 2)               # the static light, top-left
    hgt = ndimage.gaussian_filter(st, 0.8)
    gy, gx = np.gradient(hgt)
    relief = np.clip(-(gx * -1.0 + gy * -1.3) * 3.0, -0.35, 0.35)                 # lit from the top-left
    if tone == "dark":
        t = 0.10 + 0.035 * brush + 0.10 * sweep + 0.78 * st + 0.9 * relief
    else:
        t = 0.66 + 0.03 * brush + 0.14 * sweep - 0.18 * st + 0.9 * relief
    if etch is not None:
        t = t + np.where(etch, 0.16 if tone == "dark" else -0.12, 0.0)
    q = ramp(t)
    q = colour_blend(q, np.array((0.78, 0.84, 1.0)), 0.12)                         # a cool steel cast
    return np.clip(q, 0, 1), st


def glitter(FW, FH, seed, dens=0.025):
    rnd = np.random.default_rng(seed)
    m = rnd.random((FH, FW)) < dens
    ys, xs = np.nonzero(m)
    return [(int(x), int(y), int(rnd.integers(0, 16))) for x, y in zip(xs, ys)]


GLINT_LIFE = [1.0, 0.55, 0.2] + [0.0] * 13     # a glitter px flashes once per loop at its own phase


def vault_stars(c, st, n=6, min_d=14, seed=0, stages=(3, 2)):
    """4-point sparkles on the brightest printed stars, away from the sprite and each other"""
    d = c.dist()
    FH, FW = c.FH, c.FW
    cand = np.argwhere((st > 0.5) & (d > 4))
    rnd = np.random.default_rng(seed)
    rnd.shuffle(cand)
    out = []
    for y, x in cand:
        if 3 <= x < FW - 3 and 3 <= y < FH - 3 and all(abs(x - a) + abs(y - b) >= min_d for a, b, _ in out):
            out.append((int(x), int(y), stages[len(out) % len(stages)]))
        if len(out) >= n:
            break
    # the Pokemon covers most printed stars (full arts): spread the rest over open metal, corners first
    spots = [(0.08, 0.1), (0.92, 0.1), (0.92, 0.88), (0.08, 0.88), (0.5, 0.06), (0.5, 0.94), (0.06, 0.5), (0.94, 0.5)]
    for fx, fy in spots:
        if len(out) >= n:
            break
        x, y = int(fx * (FW - 1)), int(fy * (FH - 1))
        near = np.argwhere(d > 4)
        if not len(near):
            break
        y, x = near[np.argmin(np.abs(near[:, 0] - y) + np.abs(near[:, 1] - x))]
        if 3 <= x < FW - 3 and 3 <= y < FH - 3 and all(abs(x - a) + abs(y - b) >= min_d for a, b, _ in out):
            out.append((int(x), int(y), stages[len(out) % len(stages)]))
    return out


def vault_card(cid, spr, x0, y0, S, W, H, boxes=(), tex_src=None, off=None, dx=0, dy=0, tone=None, seed=None,
               nstars=6, win=SM_WIN, scene="", texture=True, grow=6):
    """the Rare Shiny (Shiny Vault) recipe, parameterised for the shiny batches"""
    seed = seed if seed is not None else sum(map(ord, cid))
    rgb = window_rgb(cid, boxes=boxes, grow=grow, tex_src=tex_src, texture=texture, win=win)
    c = Card(W, H)
    place(c, spr, cid, x0, y0, S, off=off, dx=dx, dy=dy, margin=1)
    a = L.sample(rgb, x0, y0, S / 2, 2 * W, 2 * H, resample=L.Image.LANCZOS)
    q, st = vault_bg(a, seed, tone, hole=hole_map(cid, x0, y0, S, W, H, grow, boxes, win))
    q = L.focus_halo(c, q, radius=3, dark=0.8 if (tone or VAULT_TONE) == "dark" else 0.9, soft=1.0)
    L.finish(c, q, 64, method="median")
    qq = c.bgq.astype(float) / 255
    FH, FW = c.FH, c.FW
    d = c.dist()
    glit = [(x, y, ph) for (x, y, ph) in glitter(FW, FH, seed) if d[y, x] > 2]
    q_pre = qq.copy()
    for x, y, ph in glit:
        qq[y, x] = qq[y, x] + (1 - qq[y, x]) * GLINT_LIFE[(15 - ph) % 16]
    c.bgq = L.to8(qq)
    c.bgq = L.rim(c, c.bgq, colour=(0.92, 0.95, 1.0), amt=0.4)
    q_pre = L.rim(c, L.to8(q_pre), colour=(0.92, 0.95, 1.0), amt=0.4).astype(float) / 255
    stars = vault_stars(c, st, nstars, seed=seed)
    for x, y, s_ in stars:
        L.sparkle(c, x, y, s_, VAULT_STAR)
    sc = f", {scene}" if scene else ""
    return meta(c, card=cid, label=f"Rare Shiny: {name_of(cid)}{sc} (Shiny Vault: shiny sprite, vault foil)",
                rarity="Rare Shiny", finish=f"Shiny Vault: the SHINY sprite; the window's star pattern as {(tone or VAULT_TONE)} vault foil, embossed stars, glitter, 4-point stars",
                variant="rare-shiny", anim="vault", ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S, stars=stars,
                glitter=glit, q_pre=q_pre, star_map=st, frame=FRAMES["Rare Shiny"], vault_tone=tone or VAULT_TONE)


def charmander_sv(tone=None):
    cid = "sma-SV6"
    x0, y0, S, W, H = 58, 100, 15, 41, 25
    spr = ShinySprite("charmander", flip=True)
    return vault_card(cid, spr, x0, y0, S, W, H, tex_src=(560, 110, 670, 470), tone=tone, scene="")


def vault_gx_card(cid, spr, x0, y0, S, W, H, boxes, tex_src=None, off=None, dx=0, dy=0, tone=None, seed=None,
                  nstars=7, scene="", texture=True, grow=6):
    """the Rare Shiny GX recipe: full-art crop, vault foil + fingerprint etch, big flares, silver bevel frame"""
    seed = seed if seed is not None else sum(map(ord, cid))
    rgb, _ = E.clean(cid, grow=grow, boxes=boxes, tex_src=tex_src, texture=texture)
    c = Card(W, H)
    place(c, spr, cid, x0, y0, S, off=off, dx=dx, dy=dy, margin=2)
    a = L.sample(rgb, x0, y0, S / 2, 2 * W, 2 * H, resample=L.Image.LANCZOS)
    FH, FW = c.FH, c.FW
    f, line = fingerprint(FW, FH, [(FW * 0.2, FH * 0.25, 1.0), (FW * 0.8, FH * 0.7, 0.8)], period=3.2, seed=seed % 7)
    q, st = vault_bg(a, seed, tone, etch=line, hole=hole_map(cid, x0, y0, S, W, H, grow, boxes))
    q = L.radial_glow(c, q, (0.75, 0.85, 1.0), max(FW, FH) * 0.5, 0.12)
    q = L.focus_halo(c, q, radius=4, dark=0.78 if (tone or VAULT_TONE) == "dark" else 0.9, soft=1.2)
    q = L.median_q(q, 96)
    d = c.dist()
    rim = (d > 0) & (d <= 1.01)
    q[rim] = q[rim] + (np.array((0.9, 0.95, 1.0)) - q[rim]) * 0.45
    q = silver_frame(c, q, width=2, ramp_hex=SILVER)
    ring = c.meta["frame_ring"]
    glit = [(x, y, ph) for (x, y, ph) in glitter(FW, FH, seed, 0.035) if d[y, x] > 2 and not ring[y, x]]
    q_pre = q.copy()
    for x, y, ph in glit:
        q[y, x] = q[y, x] + (1 - q[y, x]) * GLINT_LIFE[(15 - ph) % 16]
    c.bg = q
    c.bgq = L.to8(q)
    stars = [s for s in vault_stars(c, st, nstars, min_d=16, seed=seed, stages=(3, 3, 2)) if not ring[s[1], s[0]]]
    for x, y, s_ in stars:
        L.sparkle(c, x, y, s_, VAULT_STAR)
    sc = f", {scene}" if scene else ""
    return meta(c, card=cid, label=f"Rare Shiny GX: {name_of(cid)}{sc} (Shiny Vault GX: etched vault foil, silver frame)",
                rarity="Rare Shiny GX", finish=f"Shiny Vault GX: the SHINY sprite, full art; {(tone or VAULT_TONE)} vault foil with an etched texture, silver frame, star flares",
                variant="rare-shiny-gx", anim="vaultgx", ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S, stars=stars,
                glitter=glit, q_pre=q_pre, etch=line & ~ring & (d > 1.01), star_map=st, frame=FRAMES["Rare Shiny GX"],
                vault_tone=tone or VAULT_TONE)


def charizard_svgx(tone=None):
    cid = "sma-SV49"
    x0, y0, S, W, H = 70, 92, 11.4, 52, 41
    boxes = EDGES + (TOP, ICON, EVOLVES, (0, 560, 734, 1024))
    spr = ShinySprite("charizard")
    return vault_gx_card(cid, spr, x0, y0, S, W, H, boxes, texture=False, tone=tone)


# ============================================================ Rare Secret: Tapu Koko-GX SV93 (evs Froslass recipe)
def gold_card(cid, spr, x0, y0, S, W, H, boxes, off=None, dx=0, dy=0, seed=None, scene=""):
    import tiers as s3t
    seed = seed if seed is not None else sum(map(ord, cid))
    rgb, _ = E.clean(cid, grow=5, boxes=boxes, texture=False)
    c = Card(W, H)
    place(c, spr, cid, x0, y0, S, off=off, dx=dx, dy=dy, margin=1)
    gpal, gshiny = L.gold_remap(spr, L.gold_ramp(s3t.RAMP, 24), L.gold_ramp(s3t.RAMP_AMBER, 24))
    c.put_sprite(spr, *c.off, gpal, gshiny)
    a = L.sample(rgb, x0, y0, S / 2, c.FW, c.FH, resample=L.Image.BOX)
    lum = a @ W_LUM
    lum = (lum - lum.min()) / max(1e-6, lum.max() - lum.min())
    h = np.clip((ndimage.gaussian_filter(lum, 0.8) - 0.1) / 0.8, 0, 1)
    fh, seam, _ = s3t.facet_height(c.FW, c.FH, n=70, seed=seed)
    s3t.gold_foil(c, np.zeros_like(h), 1 - h, lo=0.0, hi=0.0, relief=0.0, glow=0.3, glow_r=9, seed=seed,
                  glints=26, facets=0.34 + 0.22 * (h - 0.5) + 0.16 * (fh - 0.5) + 0.5 * s3t.emboss(fh) - 0.05 * seam)
    FW, FH = c.FW, c.FH
    stars = [(6, 8, 3), (FW - 8, 6, 3), (FW - 8, FH - 10, 3), (5, FH - 8, 2), (FW // 2, FH - 5, 2)]
    for x, y, st in stars:
        L.sparkle(c, x, y, st, s3t.GOLD_SPARK)
    sc = f", {scene}" if scene else ""
    return meta(c, card=cid, label=f"Rare Secret: {name_of(cid)} gold{sc} (gold remap, faceted etched gold, glitter)",
                rarity="Rare Secret", finish="gold secret (SM gold GX): gold sprite remap, crystalline etched gold, glitter",
                variant="rare-secret", anim="gold", ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S,
                stars=stars, sprite_recolour="gold", frame=FRAMES["Rare Secret"])


def tapu_koko():
    cid = "sma-SV93"
    x0, y0, S, W, H = 120, 92, 9.8, 50, 40
    boxes = EDGES + (TOP, (0, 485, 734, 1024))
    return gold_card(cid, Sprite("tapu-koko"), x0, y0, S, W, H, boxes)


# rarity order, commonest first (Rare Shiny ~1 in 4.6 packs, Rare Holo GX ~1 in 10, Shiny GX ~1 in 10.6, gold ~1 in 94)
BUILDERS = {"sm115-7": charmander, "sm115-8": charmeleon, "sm115-32": mew, "sm115-18": vaporeon,
            "sm115-9": charizard_gx, "sma-SV6": charmander_sv, "sma-SV49": charizard_svgx, "sma-SV93": tapu_koko}
ORDER = list(BUILDERS)
