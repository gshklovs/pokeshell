r"""Evolving Skies full set, group "v": the 17 regular Pokemon V cards (Rare Holo V), built exactly like the
approved Sylveon V 74 (evcards.sylveon): the card's own scene in the art window (x 37..697, y 92..669 card px),
the real Pokemon and the text / logos painted out (evlib.clean, texture fill), the UNMODIFIED colorscripts
sprite (flip only), 24-colour k-means on the scene, the V "sunpillar" rainbow stripes blended over the whole
window (0.10 + 0.10 x luminance), 72-colour median cut, a lifted 1-px rim, the silver etched frame, four
sparkles; animation = anim.anim_sunpillar (45-degree rainbow beam + counter beam), last frame == static art.

Size (fit to the card): the window is always the same card region; the grid scale S follows the sprite with
Sylveon's proportions (sprite width <= 0.75 W, height + 4 <= H), so every art is Sylveon-sized or larger as
its sprite needs.

Shared files are not edited: this module registers its builders in evcards.BUILDERS at import (in-process
only) and drives build.render / anim.build / verify.py's checks / a sheet from here.

  ..\..\..\.venv\Scripts\python batch_v.py masks|build|anim|verify|sheet|all [swsh7-13 ...]
"""
import json
import runpy
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

import evcards
import evlib as E
import masks as M
from evcards import L, Card, Sprite, W_LUM, colour_blend, meta, place, rainbow_rgb, silver_frame

PLAN = json.load(open(E.HERE / "plan.json", encoding="utf-8"))["v"]
IDS = [p["id"] for p in PLAN]

# the approved Sylveon V window, in card px
WX0, WY0, WX1, WY1 = 37, 92, 697, 669
# the V card's silver corner swoosh (top-left, under the name bar): painted out with the scene
CORNER = [(30, 92), (96, 92), (30, 215)]
RAPID = (440, 90, 734, 168)            # the Rapid Strike / Single Strike logo, top-right under the HP

# per card: sprite, flip (face the way the card does), text_y (top of the first text row: the Ability label or
# the first attack), logo (a strike logo box or None), mask recipe (model, keep, close, cut boxes, polys),
# dx / dy nudges of the sprite anchor (sprite px)
CFG = {
    "swsh7-13": dict(sprite="trevenant", flip=False, text_y=660),
    "swsh7-7": dict(sprite="leafeon", flip=False, text_y=620, model=None, keep=1,
                    add=([(210, 420), (235, 380), (280, 290), (360, 300), (360, 210), (440, 190), (470, 220), (430, 300),
                          (530, 290), (560, 380), (585, 460), (565, 520), (560, 600), (470, 640), (380, 640), (330, 560),
                          (300, 480), (210, 470)],)),
    # Dracozolt / Duraludon fill the window and no segmenter finds them: hand hulls
    "swsh7-58": dict(sprite="dracozolt", flip=False, text_y=615, model=None, keep=1,
                     add=([(40, 300), (90, 160), (150, 110), (200, 150), (260, 170), (300, 110), (420, 100), (560, 110),
                           (640, 200), (700, 280), (700, 500), (640, 560), (600, 640), (300, 660), (200, 640), (170, 520),
                           (130, 450), (60, 360)],)),
    "swsh7-28": dict(sprite="gyarados", flip=False, text_y=665),
    "swsh7-31": dict(sprite="suicune", flip=False, text_y=615, model="isnet-general-use", keep=1),
    "swsh7-40": dict(sprite="glaceon", flip=False, text_y=625, model="isnet-anime", keep=3),
    "swsh7-21": dict(sprite="volcarona", flip=False, text_y=615),
    "swsh7-48": dict(sprite="arctovish", flip=True, text_y=650, keep=1),
    "swsh7-64": dict(sprite="espeon", flip=False, text_y=655, model="isnet-anime", keep=1),
    "swsh7-70": dict(sprite="golurk", flip=False, text_y=650, logo=RAPID, keep=1),
    "swsh7-83": dict(sprite="medicham", flip=False, text_y=570, model="isnet-general-use", logo=RAPID, keep=1,
                     add=([(40, 330), (120, 230), (200, 200), (280, 240), (330, 300), (390, 420), (420, 560), (380, 620),
                           (250, 620), (120, 560), (40, 480)],)),          # the kicking leg (motion-blurred)
    # the card is Dusk Form Lycanroc (orange mane, green eyes): the vendor's lycanroc-dusk sprite
    "swsh7-91": dict(sprite="lycanroc-dusk", flip=False, text_y=705, keep=3,
                     add=([(30, 160), (80, 110), (250, 100), (420, 100), (470, 110), (580, 210), (640, 240), (700, 230),
                           (700, 520), (560, 450), (400, 400), (200, 450), (30, 450)],)),     # the white mane,
    "swsh7-94": dict(sprite="umbreon", flip=False, text_y=625, model="isnet-general-use", keep=1, logo=RAPID),
    "swsh7-100": dict(sprite="garbodor", flip=False, text_y=685, keep=1, off=(7, 11)),
    "swsh7-110": dict(sprite="rayquaza", flip=False, text_y=625, model="isnet-general-use", keep=1, logo=RAPID),
    "swsh7-117": dict(sprite="noivern", flip=False, text_y=600, model="isnet-general-use", keep=1),
    "swsh7-122": dict(sprite="duraludon", flip=False, text_y=655, model=None, keep=1, logo=RAPID,
                      add=([(60, 100), (230, 100), (280, 230), (600, 210), (700, 230), (700, 660), (80, 660), (60, 560),
                            (30, 430), (30, 330), (80, 250)],)),
}
MIN_W = 40          # never smaller than the approved Sylveon V (80 cols)


def cfg(cid):
    k = dict(model="u2net", keep=2, close=0, cut=(), polys=(), add=(), logo=None, dx=0, dy=0, stars=None,
             tex_src=None, grow=5, rim=0.45)
    k.update(CFG[cid])
    return k


# ------------------------------------------------------------------------------------------ masks
def make_mask(cid):
    """rembg first cut inside the art window, as masks.sylveon; cut = boxes removed (logos, scenery the model
    grabbed), polys = hand polygons ANDed in (a hull), add = polygons ORed in (parts the model missed)"""
    k = cfg(cid)
    sh = E.card_img(cid).shape[:2]
    m = M.rembg(cid, k["model"]) if k["model"] else np.zeros(sh, bool)
    m &= M.rect(sh, 30, 96, 710, 900)
    if k["logo"]:
        m &= ~M.rect(sh, *k["logo"])
    for c in k["cut"]:
        m &= ~M.rect(sh, *c)
    for p in k["polys"]:
        m &= M.poly(sh, p)
    if k["close"]:
        m = ndimage.binary_closing(m, iterations=k["close"])
    for p in k["add"]:
        m |= M.poly(sh, p)
    m = ndimage.binary_fill_holes(M.largest(m, k["keep"]))
    E.MASKS.mkdir(exist_ok=True)
    Image.fromarray((m * 255).astype(np.uint8)).save(E.MASKS / f"{cid}.png")
    return m


def masks_sheet(ids):
    tiles = []
    for cid in ids:
        m = make_mask(cid)
        rgb = E.card_img(cid)
        o = np.where(m[..., None], rgb, rgb * 0.25 + np.array([0, 0.3, 0]))
        t = Image.fromarray(E.L.to8(o)).resize((367, 512))
        ImageDraw.Draw(t).text((4, 4), cid, fill=(255, 255, 0))
        tiles.append(t)
        ys, xs = np.nonzero(m)
        print(cid, "bbox", xs.min(), ys.min(), xs.max(), ys.max(), f"{m.mean():.2f}")
    n = 6
    sheet = Image.new("RGB", (367 * n, 512 * ((len(tiles) + n - 1) // n)))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % n) * 367, (i // n) * 512))
    sheet.save(E.WORK / "v_masks.png")


# ------------------------------------------------------------------------------------------ builder
def win_bottom(cid):
    """Sylveon's window ends 23 px below its first text row (and never lower than 669)"""
    return min(WY1, cfg(cid)["text_y"] + 23)


def grid_size(spr, wy1=WY1):
    """Sylveon's proportions: sprite <= 0.75 of the window width, sprite + 4 px <= window height"""
    ratio = (WX1 - WX0) / (wy1 - WY0)
    W = max(MIN_W, int(np.ceil(max(spr.w / 0.75, (spr.h + 4) * ratio) - 1e-6)))
    S = (WX1 - WX0) / W
    H = round((wy1 - WY0) / S)
    return W, H, S


def auto_tex_src(known, x0, y0, x1, y1, tw=200, th=190):
    """the window rect of the scene with the most known (unmasked, unboxed) pixels"""
    best, bs = None, -1
    for y in range(y0, y1 - th + 1, 20):
        for x in range(x0, x1 - tw + 1, 20):
            s = known[y:y + th, x:x + tw].mean()
            if s > bs:
                best, bs = (x, y, x + tw, y + th), s
    return best


SYL_STARS = [(8 / 80, 10 / 70, 3), (70 / 80, 8 / 70, 2), (72 / 80, 50 / 70, 3), (7 / 80, 58 / 70, 2)]


def pick_stars(c):
    """Sylveon's four sparkle spots scaled to this window; a spot that lands within 4 px of the sprite (or on
    the frame) moves to the nearest free spot in its quadrant"""
    d = c.dist()
    FW, FH = c.FW, c.FH
    out = []
    for fx, fy, st in SYL_STARS:
        x, y = round(fx * FW), round(fy * FH)
        if d[y, x] > 4:
            out.append((x, y, st))
            continue
        qx = slice(5, FW // 2) if fx < 0.5 else slice(FW // 2, FW - 5)
        qy = slice(5, FH // 2) if fy < 0.5 else slice(FH // 2, FH - 5)
        sub = d[qy, qx]
        ys, xs = np.nonzero(sub > 4)
        if not len(ys):
            continue
        yy, xx = ys + qy.start, xs + qx.start
        i = np.argmin((yy - y) ** 2 + (xx - x) ** 2)
        if any(abs(xx[i] - a) + abs(yy[i] - b) < 10 for a, b, _ in out):
            continue
        out.append((int(xx[i]), int(yy[i]), st))
    return out


def build_v(cid):
    k = cfg(cid)
    spr = Sprite(k["sprite"], flip=k["flip"])
    wy1 = win_bottom(cid)
    W, H, S = grid_size(spr, wy1)
    x0, y0 = WX0, WY0
    sh = E.card_img(cid).shape[:2]
    boxes = [(0, 0, 734, 96), (0, k["text_y"], 734, 1024), (0, 0, 30, 1024), (700, 0, 734, 1024)]
    if k["logo"]:
        boxes.append(k["logo"])
    extra = M.poly(sh, CORNER)
    tex = k["tex_src"]
    if tex is None:
        known = ~E.mask(cid) & ~extra
        for (a, b, cc, dd) in boxes:
            known[b:dd, a:cc] = False
        tex = auto_tex_src(ndimage.binary_erosion(known, iterations=6), x0, y0, WX1, min(wy1, k["text_y"]))
    rgb, _ = E.clean(cid, grow=k["grow"], boxes=boxes, tex_src=tex, extra=extra)
    c = Card(W, H)
    place(c, spr, cid, x0, y0, S, off=k.get("off"), dx=k["dx"], dy=k["dy"], margin=1)
    # --- from here on: evcards.sylveon verbatim
    a = L.sample(rgb, x0, y0, S / 2, 2 * W, 2 * H, resample=L.Image.BOX)
    a = L.tone(a, sat=1.4, bright=1.05, gamma=0.9)
    a = L.focus_halo(c, a, radius=3, dark=0.88, soft=1.0)
    _, lbl, pal = L.kmeans_q(a, 24, 0, ignore=c.fig_mask())
    lbl = L.orphan_clean(lbl, 1)
    base = pal[lbl]
    FH, FW = c.FH, c.FW
    yy, xx = np.mgrid[0:FH, 0:FW]
    u = (xx * 0.9 + yy * 0.35) / 9.0
    stripe = rainbow_rgb(u, s=0.7)
    q = colour_blend(base, stripe, 0.10 + 0.10 * (base @ W_LUM))
    q = np.clip(q * 1.02 + 0.02, 0, 1)
    q = L.median_q(q, 72)
    d = c.dist()
    rim = (d > 0) & (d <= 1.01)
    q[rim] = q[rim] + (1 - q[rim]) * k["rim"]
    q = silver_frame(c, q)
    c.bg = q
    c.bgq = L.to8(q)
    stars = k["stars"] or pick_stars(c)
    for x, y, st in stars:
        L.sparkle(c, x, y, st, {"L": "#ffffff", "l": "#ffe6f4", "j": "#b9d7ff"})
    card = next(p for p in PLAN if p["id"] == cid)
    return meta(c, card=cid, label=f"Rare Holo V: {card['name']} {int(card['number']):03d}/203 (sunpillar foil, silver frame)",
                rarity="Rare Holo V", finish="SWSH V holo: silver frame + sunpillar rainbow stripes",
                variant="rare-holo-v", anim="sunpillar", ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S,
                stars=stars, frame="#c9d1da")


def _mk(cid):
    return lambda: build_v(cid)


# register in-process only (evcards.py is shared and not edited)
for _cid in IDS:
    evcards.BUILDERS[_cid] = _mk(_cid)


# ------------------------------------------------------------------------------------------ steps
def _load(name):
    """an evs module by path (a same-named module elsewhere on sys.path, e.g. suite3's build, would shadow it)"""
    import importlib.util
    spec = importlib.util.spec_from_file_location(f"evs_{name}", E.HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def do_build(ids):
    build = _load("build")
    infos = {}
    for cid in ids:
        _, infos[cid] = build.render(cid)
    f = E.WORK / "sizes_v.json"
    old = json.load(open(f, encoding="utf-8")) if f.exists() else {}
    old.update(infos)
    f.write_text(json.dumps(old, indent=1), encoding="utf-8")


def do_anim(ids):
    anim = _load("anim")
    anim.build(ids)


def do_verify(ids):
    """verify.py's checks, verbatim, run over our ids (it loops evcards.ORDER at import time)"""
    saved = list(evcards.ORDER)
    evcards.ORDER[:] = ids
    try:
        runpy.run_path(str(E.HERE / "verify.py"), run_name="verify_v")
        rc = 0
    except SystemExit as e:
        rc = e.code or 0
    finally:
        evcards.ORDER[:] = saved
    print("VERIFY", "ALL PASS" if rc == 0 else "FAILURES")
    return rc


ROW_H = 820
GAP = 28
FONT = "C:/Windows/Fonts/consola.ttf"


def fit_h(im, h):
    return im.resize((round(im.width * h / im.height), h), Image.LANCZOS)


def do_sheet(ids, name="v.png"):
    """sheet.py's layout: real card | ours | ours + text half, one row per card"""
    sizes = json.load(open(E.WORK / "sizes_v.json", encoding="utf-8"))
    rows = []
    for cid in ids:
        card = json.load(open(E.CARDS / f"{cid}.json", encoding="utf-8"))
        info = sizes[cid]
        real = fit_h(Image.open(E.ref_path(cid)).convert("RGB"), ROW_H)
        st0 = Image.open(E.OUT / f"{cid}-card.png").convert("RGB")
        stacked = fit_h(st0, ROW_H)
        art0 = Image.open(E.OUT / f"{cid}-art.png").convert("RGB")
        kk = stacked.height / st0.height
        art = art0.resize((round(art0.width * kk), round(art0.height * kk)), Image.LANCZOS)
        label = (f"{cid}  {card['name']}  {card['number']}/{card['set']['printedTotal']}  tier: {card['tier']}"
                 f"  |  sprite {cfg(cid)['sprite']} flip={info['flip']}  art {info['cols']}x{info['lines']}, card {info['cols']}x{info['card_lines']}\n"
                 f"{info['finish']}")
        rows.append((label, [real, art, stacked]))
    W = max(sum(p.width for p in ps) + GAP * (len(ps) + 1) for _, ps in rows)
    H = sum(ROW_H + 90 + GAP for _ in rows) + 70
    o = Image.new("RGB", (W, H), (24, 24, 28))
    d = ImageDraw.Draw(o)
    d.text((GAP, 14), "Evolving Skies (swsh7) group v, Rare Holo V: real card | pokeshell art | art + text half",
           font=ImageFont.truetype(FONT, 36), fill=(235, 235, 235))
    y = 70
    f = ImageFont.truetype(FONT, 26)
    for label, ps in rows:
        d.text((GAP, y + 8), label, font=f, fill=(200, 200, 200))
        x = GAP
        for p in ps:
            o.paste(p, (x, y + 80))
            x += p.width + GAP
        y += ROW_H + 90 + GAP
    (E.DATA / "sheets").mkdir(exist_ok=True)
    out = E.DATA / "sheets" / name
    o.save(out)
    print(out, o.size)


def quick(ids):
    """art only (no card json needed): work/v_q_<id>.png + preview"""
    for cid in ids:
        c = evcards.BUILDERS[cid]()
        rows, pal, _ = L.keyed(c)
        L.term_png(rows, pal, E.WORK / f"v_q_{cid}.png")
        real = fit_h(Image.open(E.ref_path(cid)).convert("RGB"), 700)
        art = Image.open(E.WORK / f"v_q_{cid}.png").convert("RGB")
        art = fit_h(art, 600)
        o = Image.new("RGB", (real.width + art.width + 30, 700), (24, 24, 28))
        o.paste(real, (0, 0))
        o.paste(art, (real.width + 30, 0))
        o.save(E.WORK / f"v_prev_{cid}.png")
        print(cid, c.FW, c.FH, c.off)


def do_preview(ids):
    """work/v_prev_<id>.png: real card beside our art (quick iteration)"""
    for cid in ids:
        real = fit_h(Image.open(E.ref_path(cid)).convert("RGB"), 700)
        art = Image.open(E.OUT / f"{cid}-art.png").convert("RGB")
        art = art.resize((round(art.width * 700 / art.height * 0.85), round(700 * 0.85)), Image.LANCZOS)
        o = Image.new("RGB", (real.width + art.width + 30, 700), (24, 24, 28))
        o.paste(real, (0, 0))
        o.paste(art, (real.width + 30, 0))
        o.save(E.WORK / f"v_prev_{cid}.png")


def main():
    step = sys.argv[1] if len(sys.argv) > 1 else "all"
    ids = [a for a in sys.argv[2:] if a in IDS] or IDS
    E.WORK.mkdir(exist_ok=True)
    if step in ("masks", "all"):
        masks_sheet(ids)
    if step in ("build", "all", "bp"):
        do_build(ids)
    if step == "quick":
        quick(ids)
    if step in ("preview", "bp"):
        do_preview(ids)
    if step in ("anim", "all"):
        do_anim(ids)
    if step in ("verify", "all"):
        rc = do_verify(ids)
    if step in ("sheet", "all"):
        do_sheet(IDS if step == "all" else ids)
    if step in ("verify", "all"):
        sys.exit(rc)


if __name__ == "__main__":
    main()
