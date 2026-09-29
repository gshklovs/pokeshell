r"""Evolving Skies full set, group "ultra_b" (plan.json): 16 Rare Ultra V cards, built exactly like the approved
Rare Ultra, Glaceon V 174 (evcards.glaceon): the card's own painting (real Pokemon masked out and filled) sampled at
full grid resolution, tone, focus halo, radial glow with rays, tinted vignette, fingerprint etch lines (lit by a
rainbow contour wave in the animation: anim.anim_etch), median-cut ~170 colours, rim, sparkles. The sprite is the
vendor colorscripts sprite, unmodified (flip only).

Full arts (plain V full art) and alternate arts (painted scenes: Medicham 186, Umbreon 189, Dragonite 192,
Rayquaza 194, Noivern 196, Duraludon 198) both get the full-art treatment; the alt arts keep their painted scene
as the background.

Shared files are NOT edited: this module registers its builders into evcards.BUILDERS at runtime and reuses
build.render / anim.build / verify's checks / its own sheet.

  ..\..\..\.venv\Scripts\python batch_ultra_b.py masks [ids]     masks/<id>.png + work/ultra_b-masks.png
  ..\..\..\.venv\Scripts\python batch_ultra_b.py build [ids]     art/ + out/ (+ anim/ for every id)
  ..\..\..\.venv\Scripts\python batch_ultra_b.py verify [ids]
  ..\..\..\.venv\Scripts\python batch_ultra_b.py sheet           sheets/ultra_b.png
  ..\..\..\.venv\Scripts\python batch_ultra_b.py all [ids]
"""
import json
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

import evcards
import evlib as E
from evcards import fingerprint, meta, place
from evlib import L, Card, Sprite
import masks as M

GROUP = "ultra_b"
PLAN = json.load(open(E.HERE / "plan.json", encoding="utf-8"))[GROUP]
IDS = [c["id"] for c in PLAN]
SHEETS = E.DATA / "sheets"
SIZES = SHEETS / f"{GROUP}-sizes.json"

# SWSH full-art layout, card px (734 x 1024): name / HP bar, V corner, side frame
EDGES = ((0, 0, 30, 1024), (700, 0, 734, 1024))
TOP = (0, 0, 734, 100)
VCORNER = (0, 0, 70, 230)
STRIKE = (468, 100, 708, 168)          # Single / Rapid Strike badge under the HP


def bottom(y):
    return (0, y, 734, 1024)


# ------------------------------------------------------------------------------------------ masks
def m_rembg(cid, model="isnet-general-use", hull=None, box=(0, 60, 734, 1024), cut=(), keep=1, close=0, open_=0,
            fill=True, add=()):
    sh = E.card_img(cid).shape[:2]
    m = M.rembg(cid, model) & M.rect(sh, *box)
    if hull is not None:
        m &= M.poly(sh, hull)
    for c in cut:
        m &= ~(M.poly(sh, c) if isinstance(c[0], tuple) else M.rect(sh, *c))
    for p in add:
        m |= M.poly(sh, p)
    if open_:
        m = ndimage.binary_opening(m, iterations=open_)
    if close:
        m = ndimage.binary_closing(m, iterations=close)
    m = M.largest(m, keep)
    return ndimage.binary_fill_holes(m) if fill else m


def m_outline(cid, seeds, region=(28, 60, 706, 700), thr=0.80, sat=0.22, gap=2, grow=3, cut=(), add=(), wall=(), reach=40):
    """SWSH full arts draw a white contour round the Pokemon: the white line (closed with `gap` px of dilation)
    splits the scene into regions; the regions holding a seed point (card px, inside the Pokemon) are the
    Pokemon. `wall` = extra polylines drawn into the line map where the contour is broken."""
    from skimage.color import rgb2hsv
    from PIL import ImageDraw
    rgb = E.card_img(cid)
    sh = rgb.shape[:2]
    hsv = rgb2hsv(rgb)
    white = (rgb.min(-1) > thr) & (hsv[..., 1] < sat)
    if wall:
        im = Image.fromarray((white * 255).astype(np.uint8))
        d = ImageDraw.Draw(im)
        for pl in wall:
            d.line(pl, fill=255, width=3)
        white = np.asarray(im) > 0
    line = ndimage.binary_dilation(white, iterations=gap)
    a, b, c, d = region
    inside = M.rect(sh, a, b, c, d)
    lbl, _ = ndimage.label(~line & inside)
    keep = {lbl[y, x] for x, y in seeds} - {0}
    m = np.isin(lbl, list(keep))
    # the white contour itself + white parts of the Pokemon (claws, horns) touching the seeded regions
    ll, _ = ndimage.label(line & inside)
    touch = set(np.unique(ll[ndimage.binary_dilation(m, iterations=1) & line])) - {0}
    m |= np.isin(ll, list(touch)) & (ndimage.distance_transform_edt(~m) <= reach)
    m = ndimage.binary_dilation(m, iterations=grow) & inside
    for p in add:
        m |= M.poly(sh, p) if isinstance(p[0], tuple) else M.rect(sh, *p)
    for p in cut:
        m &= ~(M.poly(sh, p) if isinstance(p[0], tuple) else M.rect(sh, *p))
    return ndimage.binary_fill_holes(m)


def m_hull(cid, hull, rule=None, open_=2, close=4, keep=1, add=(), cut=(), max_hole=None):
    """hand hull polygon (card px), optionally intersected with a colour rule f(h deg, s, v) -> bool"""
    from skimage.color import rgb2hsv
    rgb = E.card_img(cid)
    sh = rgb.shape[:2]
    m = M.poly(sh, hull)
    if rule is not None:
        hsv = rgb2hsv(rgb)
        m &= rule(hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2])
        if open_:
            m = ndimage.binary_opening(m, iterations=open_)
        if close:
            m = ndimage.binary_closing(m, iterations=close)
        m = M.largest(m, keep)
    for p in add:
        m |= M.poly(sh, p) if isinstance(p[0], tuple) else M.rect(sh, *p)
    for p in cut:
        m &= ~(M.poly(sh, p) if isinstance(p[0], tuple) else M.rect(sh, *p))
    if max_hole is None:
        return ndimage.binary_fill_holes(m)
    lbl, n = ndimage.label(~m)                     # fill only the small holes (a coil can enclose real scene)
    sz = ndimage.sum(np.ones_like(lbl), lbl, range(1, n + 1))
    return m | np.isin(lbl, 1 + np.nonzero(sz <= max_hole)[0])


MASKS = {           # cid -> kwargs for m_outline (seeds), m_hull (hull) or m_rembg
    "swsh7-183": dict(hull=[(60, 180), (90, 140), (150, 150), (195, 80), (265, 90), (330, 200), (390, 110), (445, 80),
                            (455, 180), (590, 180), (625, 230), (580, 320), (640, 340), (655, 400), (590, 430),
                            (560, 470), (620, 490), (700, 500), (700, 600), (620, 640), (560, 720), (40, 720),
                            (40, 560), (75, 420), (90, 300)],
                      rule=lambda h, s, v: (s < 0.2) | (((h > 320) | (h < 8)) & (s > 0.25)) | ((h > 185) & (h < 230)),
                      keep=2, close=6, add=((380, 60, 462, 190), (530, 160, 632, 245), (190, 60, 340, 120))),
    "swsh7-188": dict(seeds=[(200, 250), (160, 150), (300, 500), (600, 420), (570, 350), (400, 160), (230, 650),
                             (440, 680), (260, 420), (190, 290), (640, 300), (620, 480), (560, 470), (600, 540)],
                      add=((140, 88, 270, 150), (430, 88, 610, 160))),
    "swsh7-191": dict(seeds=[(230, 220), (300, 450), (500, 300), (650, 450), (560, 420), (200, 370), (330, 350),
                             (420, 500), (120, 470), (600, 620), (400, 620)]),
    "swsh7-185": dict(model="u2net", box=(30, 60, 704, 580), add=[((360, 420), (470, 410), (620, 440), (695, 520), (695, 600), (360, 600))]),
    "swsh7-187": dict(hull=[(28, 230), (170, 200), (240, 120), (300, 88), (705, 88), (705, 340), (645, 340), (612, 390),
                            (625, 480), (565, 560), (525, 620), (560, 705), (28, 705)]),
    "swsh7-190": dict(hull=[(270, 90), (395, 88), (405, 190), (470, 245), (510, 195), (560, 155), (645, 165),
                            (675, 230), (655, 325), (605, 345), (565, 400), (625, 415), (665, 520), (680, 580),
                            (680, 705), (28, 705), (28, 560), (40, 450), (28, 300), (60, 255), (130, 225), (190, 255),
                            (250, 235), (285, 190), (265, 130)]),
    "swsh7-182": dict(hull=[(360, 300), (420, 240), (470, 222), (520, 248), (600, 248), (645, 225), (668, 300),
                            (635, 380), (705, 415), (705, 565), (600, 585), (530, 565), (482, 595), (462, 645),
                            (398, 655), (378, 600), (408, 560), (418, 470), (378, 420), (356, 370)],
                      add=((268, 176, 348, 234),)),
    "swsh7-186": dict(model="isnet-general-use", box=(60, 90, 470, 570), keep=2, close=3),
    "swsh7-189": dict(model="isnet-general-use", box=(270, 120, 520, 415), close=3, cut=((325, 118, 440, 147),)),
    "swsh7-192": dict(model="isnet-anime", box=(40, 100, 700, 580), keep=2),
    "swsh7-193": dict(hull=[(28, 95), (705, 95), (705, 705), (28, 705)], keep=4, open_=1, close=7, max_hole=3000, add=((655, 150, 705, 205), (675, 290, 705, 400)),
                      rule=lambda h, s, v: ((h > 85) & (h < 190) & (s > 0.2)) | (v < 0.28) | (((h > 320) | (h < 8)) & (s > 0.3))
                      | ((s < 0.12) & (v > 0.85))),
    "swsh7-195": dict(model="isnet-general-use", box=(30, 90, 704, 700),
                      cut=[((610, 95), (705, 95), (705, 285), (650, 295), (615, 200))],
                      add=[((28, 250), (120, 190), (200, 160), (230, 180), (290, 300), (300, 520), (250, 545), (28, 500))]),
    "swsh7-194": dict(hull=[(28, 95), (705, 95), (705, 705), (28, 705)], keep=3, open_=1, close=6, max_hole=3000,
                      rule=lambda h, s, v: ((h > 110) & (h < 196) & (s > 0.22)) | ((v < 0.22) & (s > 0.2))
                      | (((h > 320) | (h < 8)) & (s > 0.35)) | ((h > 40) & (h < 70) & (s > 0.45)),
                      cut=[((470, 380), (560, 370), (650, 480), (705, 560), (705, 705), (460, 705), (430, 560))],
                      add=((370, 110, 470, 205), (505, 250, 570, 370), (455, 355, 500, 420),
                           ((110, 420), (200, 440), (320, 560), (300, 600), (170, 560), (110, 480)))),
    "swsh7-196": dict(model="isnet-general-use", box=(30, 90, 704, 640), close=3),
    "swsh7-197": dict(model="u2net", box=(30, 60, 704, 700),
                      add=[((28, 370), (170, 355), (265, 420), (235, 565), (120, 565), (28, 475)),
                           ((495, 370), (620, 335), (705, 355), (705, 485), (620, 480), (515, 475))]),
    "swsh7-198": dict(hull=[(335, 215), (410, 170), (470, 190), (530, 260), (520, 450), (600, 480), (640, 560),
                            (620, 680), (560, 705), (420, 705), (300, 705), (170, 645), (160, 560), (240, 560),
                            (290, 590), (330, 560), (350, 470), (360, 390), (340, 300)], keep=3, open_=1, close=5,
                      cut=[((270, 470), (450, 455), (455, 600), (280, 600))],
                      rule=lambda h, s, v: (s < 0.2) | ((v < 0.35) & (h > 190) & (h < 260)) | ((h > 190) & (h < 250) & (s < 0.5))),
}


def make_mask(cid):
    kw = dict(MASKS.get(cid, {}))
    if "seeds" in kw:
        return m_outline(cid, **kw)
    if "hull" in kw:
        return m_hull(cid, **kw)
    return m_rembg(cid, **kw)


def build_masks(ids):
    E.MASKS.mkdir(exist_ok=True)
    tiles = []
    for cid in ids:
        if not E.ref_path(cid).exists():
            print(cid, "no scan yet")
            continue
        m = make_mask(cid)
        Image.fromarray((m * 255).astype(np.uint8)).save(E.MASKS / f"{cid}.png")
        rgb = E.card_img(cid)
        o = np.where(m[..., None], rgb, rgb * 0.25 + np.array([0, 0.3, 0]))
        tiles.append(Image.fromarray(L.to8(o)).resize((367, 512)))
        ys, xs = np.nonzero(m)
        print(cid, "bbox", xs.min(), ys.min(), xs.max(), ys.max(), f"{m.mean():.2f}")
    if tiles:
        n = min(6, len(tiles))
        sheet = Image.new("RGB", (367 * n, 512 * ((len(tiles) + n - 1) // n)))
        for i, t in enumerate(tiles):
            sheet.paste(t, ((i % n) * 367, (i // n) * 512))
        sheet.save(E.WORK / f"{GROUP}-masks.png")


# ------------------------------------------------------------------------------------------ the full art
def full_art(cid, sprite, flip, box, boxes, tex_src, label, glow, vtint, rim_c, frame, stars, star_pal,
             centres, sat=1.12, bright=1.0, halo=(5, 0.7, 1.4), glow_amt=0.36, vign=0.5, dx=0, dy=0, off=None,
             margin=0, n=170, alt=False, extra=None, detail=1.0):
    """Glaceon V 174's recipe, parametrised: box = (x0, y0, S, W, H)"""
    x0, y0, S, W, H = box
    rgb, _ = E.clean(cid, grow=5, boxes=EDGES + tuple(boxes), tex_src=tex_src, extra=extra, detail=detail)
    spr = Sprite(sprite, flip=flip)
    c = Card(W, H)
    place(c, spr, cid, x0, y0, S, off=off, dx=dx, dy=dy, margin=margin)
    a = L.sample(rgb, x0, y0, S / 2, 2 * W, 2 * H, resample=L.Image.LANCZOS)
    a = L.tone(a, sat=sat, bright=bright)
    a = L.focus_halo(c, a, radius=halo[0], dark=halo[1], soft=halo[2])
    a = L.radial_glow(c, a, glow, max(c.FW, c.FH) * 0.55, glow_amt, rays=12, ray_amt=0.5)
    a = L.vignette(a, vign, tint=vtint)
    f, line = fingerprint(c.FW, c.FH, centres, period=2.6)
    lift = np.where(line, 0.11, -0.025)
    a = np.clip(a + lift[..., None] * (0.6 + 0.4 * a), 0, 1)
    L.finish(c, a, n, method="median")
    c.bgq = L.rim(c, c.bgq, colour=rim_c, amt=0.34)
    for x, y, st in stars:
        L.sparkle(c, x, y, st, star_pal)
    kind = "alternate-art full art" if alt else "full art"
    return meta(c, card=cid, label=label, rarity="Rare Ultra",
                finish=f"{kind} V: fingerprint-like etched texture, rainbow on the lines",
                variant="rare-ultra", anim="etch", ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S, stars=stars,
                etch_field=f, etch_period=2.6, frame=frame, alt=alt)


def pal_star(core="#ffffff", mid="#fff6e0", tip="#ffd98f"):
    return {"L": core, "l": mid, "j": tip}


WHITE_STAR = pal_star("#ffffff", "#e6fbff", "#9fe8ff")
GOLD_STAR = pal_star()

SPECS = {           # cid -> kwargs for full_art; box = (x0, y0, S, W, H) in card px / sprite px
    "swsh7-188": dict(sprite="umbreon", flip=False, box=(10, 92, 21, 34, 30),
                      boxes=(TOP, VCORNER, STRIKE, bottom(622)), tex_src=(560, 470, 690, 600), sat=1.3,
                      label="Rare Ultra: Umbreon V 188/203 full art, teal-rainbow shimmer (fingerprint etch)",
                      glow=(0.8, 1.0, 0.95), vtint=(0.02, 0.08, 0.22), rim_c=(0.9, 1.0, 0.97), frame="#3fc3c9",
                      stars=[(6, 6, 3), (62, 8, 2), (62, 52, 3), (5, 50, 2)], star_pal=WHITE_STAR,
                      centres=[(10, 8, 1.0), (58, 50, 0.8), (54, 6, 0.5)]),
    "swsh7-183": dict(sprite="sylveon", flip=False, box=(10, 92, 19.8, 36, 32),
                      boxes=(TOP, VCORNER, STRIKE, bottom(655)), tex_src=(600, 420, 700, 560),
                      label="Rare Ultra: Sylveon V 183/203 full art, pastel light streaks (fingerprint etch)",
                      glow=(1.0, 0.92, 0.85), vtint=(0.35, 0.12, 0.25), rim_c=(1.0, 0.95, 0.97), frame="#f39ab8",
                      stars=[(6, 8, 3), (66, 8, 2), (66, 56, 3), (5, 54, 2)], star_pal=pal_star("#ffffff", "#fff0fa", "#b8f0ff"),
                      centres=[(10, 8, 1.0), (62, 54, 0.8), (58, 6, 0.5)], vign=0.35, bright=1.08, sat=1.25,
                      halo=(5, 0.88, 1.4)),
    "swsh7-183": dict(sprite="sylveon", flip=False, box=(10, 92, 19.8, 36, 32),
                      boxes=(TOP, VCORNER, STRIKE, bottom(655)), tex_src=(600, 420, 700, 560),
                      label="Rare Ultra: Sylveon V 183/203 full art, pastel light streaks (fingerprint etch)",
                      glow=(1.0, 0.92, 0.85), vtint=(0.35, 0.12, 0.25), rim_c=(1.0, 0.95, 0.97), frame="#f39ab8",
                      stars=[(6, 8, 3), (66, 8, 2), (66, 56, 3), (5, 54, 2)], star_pal=pal_star("#ffffff", "#fff0fa", "#b8f0ff"),
                      centres=[(10, 8, 1.0), (62, 54, 0.8), (58, 6, 0.5)], vign=0.35, bright=1.08, sat=1.25,
                      halo=(5, 0.88, 1.4)),
    "swsh7-191": dict(sprite="dragonite", flip=False, box=(10, 92, 17, 42, 41),
                      boxes=(TOP, VCORNER, bottom(592)), tex_src=(560, 120, 690, 250),
                      label="Rare Ultra: Dragonite V 191/203 full art, red-orange sunburst (fingerprint etch)",
                      glow=(1.0, 0.85, 0.55), vtint=(0.3, 0.02, 0.02), rim_c=(1.0, 0.95, 0.85), frame="#e8502a",
                      stars=[(6, 8, 3), (76, 8, 2), (76, 70, 3), (5, 66, 2)], star_pal=GOLD_STAR,
                      centres=[(12, 10, 1.0), (70, 64, 0.8), (64, 8, 0.5)]),
    "swsh7-185": dict(sprite="medicham", flip=False, box=(10, 92, 21, 34, 26),
                      boxes=(TOP, VCORNER, STRIKE, bottom(572)), tex_src=(560, 200, 690, 400),
                      label="Rare Ultra: Medicham V 185/203 full art, jade and cream swirls (fingerprint etch)",
                      glow=(1.0, 0.97, 0.8), vtint=(0.02, 0.18, 0.12), rim_c=(1.0, 0.95, 0.95), frame="#e04a78",
                      stars=[(6, 6, 3), (62, 8, 2), (62, 44, 3), (5, 44, 2)], star_pal=GOLD_STAR,
                      centres=[(10, 8, 1.0), (58, 44, 0.8), (54, 6, 0.5)]),
    "swsh7-187": dict(sprite="lycanroc-dusk", flip=True, box=(10, 92, 18.8, 38, 34),
                      boxes=(TOP, VCORNER, bottom(700)), tex_src=(30, 400, 110, 600),
                      label="Rare Ultra: Lycanroc V 187/203 full art (Dusk Form), sunset rings (fingerprint etch)",
                      glow=(1.0, 0.85, 0.6), vtint=(0.3, 0.02, 0.1), rim_c=(1.0, 0.95, 0.9), frame="#e8663a",
                      stars=[(6, 6, 3), (70, 8, 2), (70, 60, 3), (5, 58, 2)], star_pal=GOLD_STAR,
                      centres=[(12, 8, 1.0), (66, 58, 0.8), (62, 6, 0.5)]),
    "swsh7-190": dict(sprite="garbodor", flip=False, box=(10, 92, 15.5, 46, 32),
                      boxes=(TOP, VCORNER, bottom(690)), tex_src=(560, 350, 700, 420),
                      label="Rare Ultra: Garbodor V 190/203 full art, psychedelic swirls (fingerprint etch)",
                      glow=(1.0, 0.9, 0.95), vtint=(0.15, 0.05, 0.3), rim_c=(1.0, 0.97, 0.9), frame="#e0609a",
                      stars=[(6, 6, 3), (84, 8, 2), (84, 56, 3), (5, 56, 2)], star_pal=pal_star("#ffffff", "#fff0fa", "#b8f0ff"),
                      centres=[(12, 8, 1.0), (80, 56, 0.8), (76, 6, 0.5)], sat=1.35),
    "swsh7-182": dict(sprite="golurk", flip=False, box=(10, 92, 19.8, 36, 32),
                      boxes=(TOP, VCORNER, STRIKE, bottom(648)), tex_src=(40, 330, 200, 420), alt=True,
                      label="Rare Ultra (alt art): Golurk V 182/203, village log-carrying scene (fingerprint etch)",
                      glow=(1.0, 0.97, 0.85), vtint=(0.1, 0.15, 0.1), rim_c=(1.0, 0.98, 0.9), frame="#5fb8b0",
                      stars=[(6, 6, 3), (66, 8, 2), (66, 56, 3), (5, 54, 2)], star_pal=GOLD_STAR,
                      centres=[(10, 8, 1.0), (62, 54, 0.8), (58, 6, 0.5)], glow_amt=0.25, vign=0.4),
    "swsh7-186": dict(sprite="medicham", flip=False, box=(10, 92, 18, 40, 29),
                      boxes=(TOP, VCORNER, STRIKE, bottom(575)), tex_src=(150, 400, 260, 500), alt=True,
                      label="Rare Ultra (alt art): Medicham V 186/203, flying kick over the cliffs (fingerprint etch)",
                      glow=(1.0, 0.95, 0.9), vtint=(0.05, 0.1, 0.25), rim_c=(1.0, 0.95, 1.0), frame="#b0306e",
                      stars=[(6, 6, 3), (74, 8, 2), (74, 50, 3), (5, 50, 2)], star_pal=WHITE_STAR,
                      centres=[(10, 8, 1.0), (70, 50, 0.8), (66, 6, 0.5)], glow_amt=0.25, vign=0.4),
    "swsh7-189": dict(sprite="umbreon", flip=False, box=(10, 92, 17, 42, 31),
                      boxes=(TOP, VCORNER, STRIKE, bottom(622)), tex_src=(560, 420, 690, 520), alt=True,
                      label="Rare Ultra (alt art): Umbreon V 189/203, moonlit rooftops (fingerprint etch)",
                      glow=(1.0, 0.95, 0.8), vtint=(0.02, 0.03, 0.15), rim_c=(1.0, 0.95, 0.8), frame="#e8c040",
                      stars=[(6, 6, 3), (78, 8, 2), (78, 54, 3), (5, 54, 2)], star_pal=GOLD_STAR,
                      centres=[(10, 8, 1.0), (74, 54, 0.8), (70, 6, 0.5)], glow_amt=0.3, vign=0.45, off=(10, 4)),
    "swsh7-192": dict(sprite="dragonite", flip=True, box=(10, 92, 17, 42, 41), sat=1.35,
                      boxes=(TOP, VCORNER, bottom(588)), tex_src=(600, 150, 700, 400), alt=True,
                      label="Rare Ultra (alt art): Dragonite V 192/203, napping above the misty peaks (fingerprint etch)",
                      glow=(1.0, 0.97, 0.85), vtint=(0.05, 0.12, 0.2), rim_c=(1.0, 0.97, 0.9), frame="#f0a040",
                      stars=[(6, 8, 3), (76, 8, 2), (76, 70, 3), (5, 66, 2)], star_pal=GOLD_STAR,
                      centres=[(12, 10, 1.0), (70, 64, 0.8), (64, 8, 0.5)], glow_amt=0.25, vign=0.4),
    "swsh7-193": dict(sprite="rayquaza", flip=True, box=(10, 92, 14.28, 50, 50),
                      boxes=(TOP, VCORNER, STRIKE, bottom(628)), tex_src=(200, 100, 380, 200),
                      label="Rare Ultra: Rayquaza V 193/203 full art, blazing speed lines (fingerprint etch)",
                      glow=(1.0, 0.9, 0.6), vtint=(0.3, 0.08, 0.0), rim_c=(1.0, 0.97, 0.85), frame="#2fae6a",
                      stars=[(6, 8, 3), (92, 8, 2), (92, 88, 3), (5, 86, 2)], star_pal=GOLD_STAR,
                      centres=[(14, 12, 1.0), (86, 82, 0.8), (80, 10, 0.5)]),
    "swsh7-194": dict(sprite="rayquaza", flip=False, box=(10, 92, 14.28, 50, 50),
                      boxes=(TOP, VCORNER, STRIKE, bottom(628)), tex_src=(150, 250, 300, 400), alt=True,
                      label="Rare Ultra (alt art): Rayquaza V 194/203, coiling through the sky with a trainer (fingerprint etch)",
                      glow=(0.9, 0.97, 1.0), vtint=(0.02, 0.1, 0.25), rim_c=(0.95, 1.0, 1.0), frame="#2f9e8a",
                      stars=[(6, 8, 3), (92, 8, 2), (92, 88, 3), (5, 86, 2)], star_pal=WHITE_STAR,
                      centres=[(14, 12, 1.0), (86, 82, 0.8), (80, 10, 0.5)], glow_amt=0.25, vign=0.4),
    "swsh7-195": dict(sprite="noivern", flip=False, box=(10, 92, 15.5, 46, 32),
                      boxes=(TOP, VCORNER, bottom(600)), tex_src=(560, 100, 700, 300),
                      label="Rare Ultra: Noivern V 195/203 full art, crimson sound-wave swirl (fingerprint etch)",
                      glow=(1.0, 0.85, 0.9), vtint=(0.25, 0.02, 0.2), rim_c=(1.0, 0.95, 1.0), frame="#7a3fb0",
                      stars=[(6, 6, 3), (84, 8, 2), (84, 56, 3), (5, 56, 2)], star_pal=pal_star("#ffffff", "#fff0fa", "#b8f0ff"),
                      centres=[(12, 8, 1.0), (80, 56, 0.8), (76, 6, 0.5)]),
    "swsh7-196": dict(sprite="noivern", flip=False, box=(10, 92, 15.5, 46, 32), bright=1.15, sat=1.25,
                      boxes=(TOP, VCORNER, bottom(600)), tex_src=(530, 300, 690, 500), alt=True,
                      label="Rare Ultra (alt art): Noivern V 196/203, night flight past the clock tower (fingerprint etch)",
                      glow=(1.0, 0.9, 0.7), vtint=(0.02, 0.02, 0.12), rim_c=(0.9, 0.9, 1.0), frame="#4a3a8a",
                      stars=[(6, 6, 3), (84, 8, 2), (84, 56, 3), (5, 56, 2)], star_pal=GOLD_STAR,
                      centres=[(12, 8, 1.0), (80, 56, 0.8), (76, 6, 0.5)], glow_amt=0.25, vign=0.4),
    "swsh7-197": dict(sprite="duraludon", flip=False, box=(10, 102, 19.8, 36, 36),
                      boxes=(TOP, VCORNER, STRIKE, bottom(655)), tex_src=(520, 170, 690, 330),
                      label="Rare Ultra: Duraludon V 197/203 full art, green-gold speed burst (fingerprint etch)",
                      glow=(1.0, 1.0, 0.75), vtint=(0.02, 0.2, 0.05), rim_c=(1.0, 1.0, 0.95), frame="#5aa83a",
                      stars=[(6, 6, 3), (66, 8, 2), (66, 64, 3), (5, 62, 2)], star_pal=GOLD_STAR,
                      centres=[(10, 8, 1.0), (62, 62, 0.8), (58, 6, 0.5)]),
    "swsh7-198": dict(sprite="duraludon", flip=False, box=(10, 92, 18.8, 38, 36),
                      boxes=(TOP, VCORNER, STRIKE, bottom(655)), tex_src=(40, 560, 150, 650), alt=True,
                      label="Rare Ultra (alt art): Duraludon V 198/203, curry picnic with Raihan (fingerprint etch)",
                      glow=(1.0, 0.97, 0.85), vtint=(0.12, 0.1, 0.02), rim_c=(1.0, 0.98, 0.9), frame="#e0602a",
                      stars=[(6, 6, 3), (70, 8, 2), (70, 64, 3), (5, 62, 2)], star_pal=GOLD_STAR,
                      centres=[(10, 8, 1.0), (66, 62, 0.8), (62, 6, 0.5)], glow_amt=0.25, vign=0.4),
}


def builder(cid):
    return lambda: full_art(cid, **SPECS[cid])


# ------------------------------------------------------------------------------------------ pipeline
def evs_module(name):
    """load evs/<name>.py by path (a plain import can pick up suite3's module of the same name)"""
    import importlib.util
    key = f"evs_{name}"
    if key not in sys.modules:
        spec = importlib.util.spec_from_file_location(key, E.HERE / f"{name}.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return sys.modules[key]


def register():
    for cid in SPECS:
        evcards.BUILDERS[cid] = builder(cid)


def ready(ids):
    out = []
    for cid in ids:
        miss = [p for p in (E.ref_path(cid), E.CARDS / f"{cid}.json", E.CARDS / "api" / f"{cid}.json", E.MASKS / f"{cid}.png")
                if not p.exists()]
        if cid not in SPECS:
            miss.append("spec")
        if miss:
            print(f"{cid}: skipped, missing {[str(getattr(p, 'name', p)) for p in miss]}")
        else:
            out.append(cid)
    return out


def build(ids):
    anim = evs_module("anim")
    B = evs_module("build")
    register()
    ids = ready(ids)
    SHEETS.mkdir(exist_ok=True)
    sizes = json.loads(SIZES.read_text()) if SIZES.exists() else {}
    for cid in ids:
        _, info = B.render(cid)
        sizes[cid] = info
        SIZES.write_text(json.dumps(sizes, indent=1), encoding="utf-8")
    anim.build(ids)
    return ids


def verify(ids):
    """verify.py's checks, on our ids (verify.py iterates evcards.ORDER at import time)"""
    register()
    ids = ready(ids)
    order = evcards.ORDER
    evcards.ORDER = ids
    sys.modules.pop("evs_verify", None)
    try:
        evs_module("verify")
        code = 0
    except SystemExit as e:
        code = e.code
    finally:
        evcards.ORDER = order
    print("verify:", "ALL PASS" if not code else "FAILURES")
    return code


def sheet(ids=None):
    """sheets/ultra_b.png: real card | ours | ours + text half, one row per card (sheet.py's layout)"""
    from PIL import ImageDraw, ImageFont
    SH = evs_module("sheet")
    sizes = json.loads(SIZES.read_text())
    ids = [c for c in (ids or IDS) if c in sizes and (E.OUT / f"{c}-card.png").exists()]
    rows = []
    for cid in ids:
        card = json.load(open(E.CARDS / f"{cid}.json", encoding="utf-8"))
        info = sizes[cid]
        real = SH.fit_h(Image.open(E.ref_path(cid)).convert("RGB"), SH.ROW_H)
        st0 = Image.open(E.OUT / f"{cid}-card.png").convert("RGB")
        stacked = SH.fit_h(st0, SH.ROW_H)
        art0 = Image.open(E.OUT / f"{cid}-art.png").convert("RGB")
        k = stacked.height / st0.height
        art = art0.resize((round(art0.width * k), round(art0.height * k)), Image.LANCZOS)
        alt = " (alt art)" if SPECS[cid].get("alt") else ""
        label = (f"{cid}  {card['name']}  {card['number']}/{card['set']['printedTotal']}  tier: {card['tier']}{alt}"
                 f"  |  art {info['cols']}x{info['lines']}, card {info['cols']}x{info['card_lines']}\n{info['finish']}")
        rows.append((label, [real, art, stacked]))
    G = SH.GAP
    W = max(sum(p.width for p in ps) + G * (len(ps) + 1) for _, ps in rows)
    H = sum(SH.ROW_H + 90 + G for _ in rows) + 70
    o = Image.new("RGB", (W, H), (24, 24, 28))
    d = ImageDraw.Draw(o)
    d.text((G, 14), "Evolving Skies ultra_b (Rare Ultra): real card | pokeshell art | art + text half",
           font=ImageFont.truetype(SH.FONT, 36), fill=(235, 235, 235))
    y = 70
    f = ImageFont.truetype(SH.FONT, 26)
    for label, ps in rows:
        d.text((G, y + 8), label, font=f, fill=(200, 200, 200))
        x = G
        for p in ps:
            o.paste(p, (x, y + 80))
            x += p.width + G
        y += SH.ROW_H + 90 + G
    o.save(SHEETS / f"{GROUP}.png")
    print(f"sheets/{GROUP}.png", o.size, len(rows), "rows")


def preview(cid):
    """quick look while tuning: real card (scaled) | our art, to work/ub-<id>.png"""
    register()
    c = evcards.BUILDERS[cid]()
    rows, pal, _ = L.keyed(c)
    art = L.term_png(rows, pal, E.WORK / f"ub-art-{cid}.png")
    real = Image.open(E.ref_path(cid)).convert("RGB")
    real = real.resize((round(real.width * art.height / real.height * 1.4), round(art.height * 1.4)))
    o = Image.new("RGB", (real.width + art.width + 20, max(real.height, art.height)), (24, 24, 28))
    o.paste(real, (0, 0))
    o.paste(art, (real.width + 20, 0))
    o.save(E.WORK / f"ub-{cid}.png")
    print(cid, "sprite at", c.off, "grid", c.FW, "x", c.FH // 2)


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    ids = [a for a in sys.argv[2:] if a in IDS] or IDS
    if cmd == "masks":
        build_masks(ids)
    elif cmd == "preview":
        for cid in ids:
            preview(cid)
    elif cmd == "build":
        build(ids)
    elif cmd == "verify":
        sys.exit(verify(ids))
    elif cmd == "sheet":
        sheet()
    elif cmd == "all":
        done = build(ids)
        code = verify(done)
        sheet()
        sys.exit(code)


if __name__ == "__main__":
    main()
