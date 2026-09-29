r"""Evolving Skies alternate-art Rare Ultra V cards, rebuilt with the approved alt-art treatment of Umbreon VMAX 215
(evcards.umbreon; batch_rainbow_secret.build_alt applied it to 205, 209, 212, 218, 220):

  the card's own painting (real Pokemon masked out, tex_fill) sampled at FULL grid resolution (LANCZOS), kept
  vivid (sat 1.15), soft focus halo, the painting's own brushwork embossed (height = its luminance, lit from the
  top-left), a light tinted vignette, median-cut 200 colours, rim light, four sparkles; animation = anim.py's
  "paint" (the light swings across the embossed brushwork, soft sheen, stars twinkle). The sprite is the vendor
  colorscripts sprite, unmodified (flip only).

These 11 cards were first built by batch_ultra_a / batch_ultra_b with Glaceon V 174's full-art recipe (radial glow,
rays, fingerprint etch) which drowned their paintings. Tier stays the API rarity "Rare Ultra"; only the finish
changes (finish = alternate art, textured painting). The art json keeps the variant key "rare-ultra".

Geometry follows batch_rainbow_secret's alt cards: the crop spans the card's width and its art height (y 100 down
to the attack text) and the sprite is placed at true size, so the canvas grows when the sprite is big and more of
the painting shows round it. Masks: the ultra batches' masks/<id>.png, reused unless a tighter one is listed in
MASK_FIX (written to masks/altart/<id>.png, the shared masks/ file is left alone).

Shared files are not edited: builders are registered into evcards.BUILDERS at runtime and build / anim / verify are
loaded by file path (suite3 has modules of the same names).

  ..\..\..\.venv\Scripts\python batch_altart.py backup            out/<id>-art.png -> work/altart/before/ (no overwrite)
  ..\..\..\.venv\Scripts\python batch_altart.py masks [ids]       masks/altart/<id>.png + work/altart/masks.png
  ..\..\..\.venv\Scripts\python batch_altart.py preview [ids]     work/altart/<id>-cmp.png (real | before | after)
  ..\..\..\.venv\Scripts\python batch_altart.py build [ids]       art/ + out/ + anim/
  ..\..\..\.venv\Scripts\python batch_altart.py verify [ids]
  ..\..\..\.venv\Scripts\python batch_altart.py sheet             sheets/altart.png
  ..\..\..\.venv\Scripts\python batch_altart.py all
"""
import importlib.util
import json
import shutil
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

import evcards
import evlib as E
from evcards import W_LUM, meta, place
from evlib import L, Card, Sprite

GROUP = "altart"
WORK = E.WORK / "altart"
BEFORE = WORK / "before"
MASK_DIR = E.MASKS / "altart"
SIZES = E.DATA / "sheets" / f"{GROUP}-sizes.json"

# SWSH V card layout, card px (734 x 1024)
EDGES = ((0, 0, 30, 1024), (700, 0, 734, 1024))
TOP = (0, 0, 734, 100)
VCORNER = (0, 0, 70, 230)
# the V logo's right arm reaches x ~105 at the top of the art (the ultra batches' rect left its tip in the scene)
V_ARM = ((0, 95), (116, 95), (44, 234), (0, 234))
STRIKE = (468, 100, 708, 168)          # Single / Rapid Strike badge under the HP

# alt-art geometry (batch_rainbow_secret GEO["alt"], Umbreon 215): crop from y 100, max S 17, full card width
Y0, SMAX, CW, WMIN, HMIN = 100, 17.0, 714, 42, 32

WHITE_STAR = {"L": "#ffffff", "l": "#e6fbff", "j": "#9fe8ff"}
GOLD_STAR = {"L": "#ffffff", "l": "#fff3c4", "j": "#8fd8ff"}           # Umbreon 215's
PINK_STAR = {"L": "#ffffff", "l": "#fff0fa", "j": "#f0b8ff"}

# per card (read off each scan): sprite + flip as the ultra batches had them, text_y = where the attack text starts
# (everything below is painted out), extra boxes, tex_src (a textured scene rectangle for tex_fill), rim light,
# vignette tint, sparkle palette, text-half frame colour, scene description
SPEC = {
    "swsh7-167": dict(name="Leafeon V", sprite="leafeon", text_y=620, src="ultra_a", tex_src=(560, 330, 690, 520),
                      rim=(1.0, 1.0, 0.85), vig=(0.1, 0.06, 0.0), star=GOLD_STAR, frame="#e178e6",
                      scene="autumn leaf pile under the trees"),
    "swsh7-175": dict(name="Glaceon V", sprite="glaceon", text_y=625, src="ultra_a", tex_src=(40, 380, 200, 560),
                      rim=(0.85, 0.97, 1.0), vig=(0.02, 0.05, 0.12), star=WHITE_STAR, frame="#e178e6",
                      scene="snowy park bench"),
    "swsh7-180": dict(name="Espeon V", sprite="espeon", text_y=660, src="ultra_a", tex_src=(40, 240, 200, 420),
                      rim=(1.0, 0.92, 1.0), vig=(0.12, 0.03, 0.12), star=PINK_STAR, frame="#e178e6",
                      scene="library of flying books"),
    "swsh7-184": dict(name="Sylveon V", sprite="sylveon", dx=2, text_y=655, src="ultra_a", tex_src=(470, 360, 690, 560),
                      extra_boxes=((480, 100, 700, 172),),
                      rim=(1.0, 0.94, 0.98), vig=(0.15, 0.03, 0.03), star=PINK_STAR, frame="#e178e6",
                      scene="bakery shelves"),
    "swsh7-182": dict(name="Golurk V", sprite="golurk", text_y=648, src="ultra_b", tex_src=(40, 330, 200, 420),
                      extra_boxes=(STRIKE,), rim=(1.0, 0.98, 0.9), vig=(0.05, 0.08, 0.05), star=GOLD_STAR,
                      frame="#5fb8b0", scene="village log-carrying"),
    "swsh7-186": dict(name="Medicham V", sprite="medicham", text_y=575, src="ultra_b", tex_src=(150, 400, 260, 500),
                      extra_boxes=(STRIKE,), rim=(1.0, 0.95, 1.0), vig=(0.02, 0.05, 0.15), star=WHITE_STAR,
                      frame="#b0306e", scene="flying kick over the cliffs"),
    "swsh7-189": dict(name="Umbreon V", sprite="umbreon", text_y=622, src="ultra_b", tex_src=(560, 420, 690, 520),
                      extra_boxes=(STRIKE,), rim=(1.0, 0.95, 0.8), vig=(0.02, 0.04, 0.12), star=GOLD_STAR,
                      frame="#e8c040", scene="moonlit rooftops"),
    "swsh7-192": dict(name="Dragonite V", sprite="dragonite", flip=True, text_y=588, src="ultra_b",
                      tex_src=(600, 150, 700, 400), dy=-1, sat=1.35, clarity=0.6, bright=0.98, rim=(1.0, 0.97, 0.9), vig=(0.02, 0.05, 0.1), star=GOLD_STAR,
                      frame="#f0a040", scene="napping above the misty peaks"),
    "swsh7-194": dict(name="Rayquaza V", sprite="rayquaza", text_y=628, src="ultra_b", tex_src=(150, 250, 300, 400),
                      extra_boxes=(STRIKE,), rim=(0.95, 1.0, 1.0), vig=(0.02, 0.06, 0.15), star=WHITE_STAR,
                      frame="#2f9e8a", scene="coiling through the sky with a trainer"),
    "swsh7-196": dict(name="Noivern V", sprite="noivern", text_y=600, src="ultra_b", tex_src=(530, 300, 690, 500),
                      rim=(0.9, 0.9, 1.0), vig=(0.02, 0.02, 0.1), star=GOLD_STAR, frame="#4a3a8a", bright=1.1, sat=1.3, clarity=0.5,
                      scene="night flight past the clock tower"),
    "swsh7-198": dict(name="Duraludon V", sprite="duraludon", text_y=655, src="ultra_b", tex_src=(40, 560, 150, 650),
                      extra_boxes=(STRIKE,), rim=(1.0, 0.98, 0.9), vig=(0.08, 0.06, 0.0), star=GOLD_STAR,
                      frame="#e0602a", scene="curry picnic with Raihan"),
}
IDS = list(SPEC)
DEFAULTS = dict(flip=False, extra_boxes=(), bright=1.02, sat=1.15, vign=0.4, dx=0, dy=0, off=None, S=None, W=None,
                H=None, ch=None, clarity=0.0)

# tighter masks where the ultra batches' mask swallowed parts of the painting (card px). Each entry is
# (base, ops): base "old" = masks/<id>.png, or a rembg model name; ops = ("cut", poly|rect) / ("add", ...) /
# ("hull", poly) (intersect) / ("close", n) / ("keep", n)
MASK_FIX = {
    # the orange underside of the tail (y 560-592) was left out: it showed as a red-brown blob under the sprite
    "swsh7-192": ("old", [("add", ((110, 548), (300, 560), (300, 594), (110, 590)))]),
    # a 15-px strip down the left frame edge (the tower's lit edge) was swallowed: give the tower back
    "swsh7-196": ("old", [("cut", (28, 170, 50, 640))]),
    # Sylveon's blue ribbon end (top left) was left in the scene as a stray teal blob
    "swsh7-184": ("old", [("add", (60, 128, 122, 222))]),
}


def spec(cid):
    return {**DEFAULTS, **SPEC[cid]}


# ---------------------------------------------------------------------------------------------- masks
def _shape(sh, p):
    import masks as M
    return M.poly(sh, p) if isinstance(p[0], tuple) else M.rect(sh, *p)


def make_mask(cid):
    import masks as M
    base, ops = MASK_FIX[cid]
    sh = E.card_img(cid).shape[:2]
    m = E.mask(cid).copy() if base == "old" else M.rembg(cid, base)
    for op, arg in ops:
        if op == "cut":
            m &= ~_shape(sh, arg)
        elif op == "add":
            m |= _shape(sh, arg)
        elif op == "hull":
            m &= _shape(sh, arg)
        elif op == "close":
            m = ndimage.binary_closing(m, iterations=arg)
        elif op == "open":
            m = ndimage.binary_opening(m, iterations=arg)
        elif op == "keep":
            m = M.largest(m, arg)
        elif op == "fill":
            m = ndimage.binary_fill_holes(m)
    return m


def get_mask(cid):
    f = MASK_DIR / f"{cid}.png"
    if cid in MASK_FIX and f.exists():
        return np.asarray(Image.open(f)) > 0
    return E.mask(cid)


def build_masks(ids):
    MASK_DIR.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    tiles = []
    for cid in ids:
        rgb = E.card_img(cid)
        old = E.mask(cid)
        if cid in MASK_FIX:
            m = make_mask(cid)
            Image.fromarray((m * 255).astype(np.uint8)).save(MASK_DIR / f"{cid}.png")
        else:
            m = old
        # green = masked (painted out), red = was masked by the ultra batch, now kept
        o = np.where(m[..., None], rgb * 0.3 + np.array([0, 0.45, 0]), rgb)
        o = np.where((old & ~m)[..., None], rgb * 0.4 + np.array([0.5, 0, 0]), o)
        tiles.append(Image.fromarray(L.to8(o)).resize((367, 512)))
        print(cid, "mask", "FIXED" if cid in MASK_FIX else "reused", f"{m.mean():.3f} (old {old.mean():.3f})")
    n = min(6, len(tiles))
    sheet = Image.new("RGB", (367 * n, 512 * ((len(tiles) + n - 1) // n)))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % n) * 367, (i // n) * 512))
    sheet.save(WORK / "masks.png")


# ---------------------------------------------------------------------------------------------- the alt art
def clean(cid, m, boxes, tex_src, grow=5):
    """evlib.clean with an explicit mask (the real Pokemon + text boxes painted out, scene texture kept)"""
    hole = ndimage.binary_dilation(m, iterations=grow)
    for bx in boxes:
        if isinstance(bx[0], tuple):
            hole |= _shape(hole.shape, bx)
        else:
            a, b, c, d = bx
            hole[max(0, b):d, max(0, a):c] = True
    return E.tex_fill(E.card_img(cid), ~hole, 14, tex_src, 1.0)


def anchor(m, x0, y0, S, spr, dx=0, dy=0):
    """evlib.anchor on an explicit mask: sprite centred on the mask's bbox, feet on its bottom"""
    ys, xs = np.nonzero(m)
    cx = ((xs.min() + xs.max()) / 2 - x0) / S
    by = (ys.max() - y0) / S
    return round(cx - spr.w / 2) + dx, round(by - spr.h) + dy


def geometry(cid, spr):
    """(x0, y0, S, W, H): the crop spans the card width and y 100 .. the attack text; the sprite at true size"""
    s = spec(cid)
    ch = s["ch"] or min(544, s["text_y"] + 20 - Y0)
    H = s["H"] or max(HMIN, spr.h + 3)
    S = s["S"] or min(SMAX, ch / H)
    W = s["W"] or max(WMIN, spr.w + 6, round(CW / S))
    return 367 - W * S / 2, Y0, S, W, H


def stars_for(c, min_d=4):
    FW, FH = c.FW, c.FH
    cands = [(6, 6, 3), (FW - 8, 8, 2), (FW - 6, FH - 8, 3), (6, FH - 12, 2), (FW // 2, 3, 1),
             (FW // 4, FH - 4, 2), (FW - 4, FH // 2, 2), (4, FH // 2, 2), (3 * FW // 4, 4, 2)]
    d = c.dist()
    out = []
    for x, y, st in cands:
        x, y = min(max(3, x), FW - 4), min(max(3, y), FH - 4)
        if d[y, x] > min_d:
            out.append((x, y, st))
    return out[:4]


def build_alt(cid):
    """Umbreon VMAX 215's recipe (evcards.umbreon / batch_rainbow_secret.build_alt), tier Rare Ultra"""
    s = spec(cid)
    spr = Sprite(s["sprite"], flip=s["flip"])
    x0, y0, S, W, H = geometry(cid, spr)
    m = get_mask(cid)
    boxes = EDGES + (TOP, VCORNER, V_ARM) + tuple(s["extra_boxes"]) + ((0, s["text_y"], 734, 1024),)
    rgb = clean(cid, m, boxes, s["tex_src"])
    c = Card(W, H)
    place(c, spr, cid, x0, y0, S, off=s["off"] or anchor(m, x0, y0, S, spr, s["dx"], s["dy"]), margin=1)
    a = L.sample(rgb, x0, y0, S / 2, 2 * W, 2 * H, resample=L.Image.LANCZOS)
    if s["clarity"]:              # local contrast for a hazy painting (Dragonite's mist): unsharp on a wide radius
        low = np.stack([ndimage.gaussian_filter(a[..., i], 3.0) for i in range(3)], -1)
        a = np.clip(a + s["clarity"] * (a - low), 0, 1)
    a = L.tone(a, sat=s["sat"], bright=s["bright"])
    a = L.focus_halo(c, a, radius=4, dark=0.8, soft=1.2)
    # textured painting: the illustration's own brushwork embossed (height = its luminance), lit from top-left
    lum = a @ W_LUM
    h = ndimage.gaussian_filter(lum, 0.6)
    gy, gx = np.gradient(h)
    relief = np.clip(-(gx * -1.0 + gy * -1.3) * 2.4, -0.3, 0.3)
    a = np.clip(a + relief[..., None] * (0.35 + 0.65 * a), 0, 1)
    a = L.vignette(a, s["vign"], tint=s["vig"])
    L.finish(c, a, 200, method="median")
    c.bgq = L.rim(c, c.bgq, colour=s["rim"], amt=0.45)
    stars = stars_for(c)
    for x, y, st in stars:
        L.sparkle(c, x, y, st, s["star"])
    num = E.num(cid)
    return meta(c, card=cid, rarity="Rare Ultra",
                label=f"Rare Ultra (alt art): {s['name']} {num}/203, {s['scene']} (textured painting)",
                finish="alternate art: textured painting (brushwork embossed)",
                variant="rare-ultra", anim="paint", ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S, stars=stars,
                height=h, frame=s["frame"], alt=True)


def builder(cid):
    fn = lambda: build_alt(cid)  # noqa: E731
    fn.__name__ = f"altart_{E.num(cid)}"
    return fn


def register(ids):
    for cid in ids:
        evcards.BUILDERS[cid] = builder(cid)


# ---------------------------------------------------------------------------------------------- pipeline
def evs_module(name):
    """load evs/<name>.py by path (a plain import can pick up suite3's module of the same name)"""
    key = f"evs_{name}"
    if key not in sys.modules:
        sp = importlib.util.spec_from_file_location(key, E.HERE / f"{name}.py")
        mod = importlib.util.module_from_spec(sp)
        sys.modules[key] = mod
        sp.loader.exec_module(mod)
    return sys.modules[key]


def backup(ids):
    """keep the etch renders: out/<id>-art.png (+ -card.png) -> work/altart/before/, never overwritten"""
    BEFORE.mkdir(parents=True, exist_ok=True)
    for cid in ids:
        for sfx in ("art", "card"):
            src, dst = E.OUT / f"{cid}-{sfx}.png", BEFORE / f"{cid}-{sfx}.png"
            if src.exists() and not dst.exists():
                shutil.copy2(src, dst)
                print("backed up", dst.name)


def build(ids):
    backup(ids)
    anim = evs_module("anim")
    B = evs_module("build")
    register(ids)
    SIZES.parent.mkdir(exist_ok=True)
    sizes = json.loads(SIZES.read_text(encoding="utf-8")) if SIZES.exists() else {}
    for cid in ids:
        _, info = B.render(cid)
        c = evcards.BUILDERS[cid]()
        info.update(sprite=c.spr.name, sprite_px=[c.spr.w, c.spr.h], S=round(c.meta["S"], 2),
                    mask="altart" if cid in MASK_FIX else "ultra batch")
        sizes[cid] = info
        SIZES.write_text(json.dumps(sizes, indent=1), encoding="utf-8")
    anim.build(ids)


def verify(ids):
    """verify.py's checks on our ids (it iterates evcards.ORDER at import): sprite exact, card data verbatim,
    16 frames, final frame == static"""
    register(ids)
    order = list(evcards.ORDER)
    evcards.ORDER[:] = ids
    sys.modules.pop("evs_verify", None)
    try:
        evs_module("verify")
        code = 0
    except SystemExit as e:
        code = e.code
    finally:
        evcards.ORDER[:] = order
    print("verify:", "ALL PASS" if not code else "FAILURES")
    return code


def fit_h(im, h):
    return im.resize((round(im.width * h / im.height), h), Image.LANCZOS)


def preview(ids):
    """work/altart/<id>-cmp.png: real card | before (etch) | after, art-only (no card data / anim needed)"""
    register(ids)
    WORK.mkdir(parents=True, exist_ok=True)
    for cid in ids:
        c = evcards.BUILDERS[cid]()
        rows, pal, _ = L.keyed(c)
        after = L.term_png(rows, pal, WORK / f"{cid}-after.png").convert("RGB")
        real = fit_h(Image.open(E.ref_path(cid)).convert("RGB"), 760)
        bef = Image.open(BEFORE / f"{cid}-art.png").convert("RGB")
        k = 560 / max(bef.height, after.height)
        ims = [real] + [i.resize((round(i.width * k), round(i.height * k)), Image.LANCZOS) for i in (bef, after)]
        o = Image.new("RGB", (sum(i.width for i in ims) + 20 * len(ims), 760), (24, 24, 28))
        x = 0
        for i in ims:
            o.paste(i, (x, 0))
            x += i.width + 20
        o.save(WORK / f"{cid}-cmp.png")
        print(cid, f"{c.FW} cols x {c.FH // 2} lines", "sprite", c.spr.w, "x", c.spr.h, "at", c.off,
              "S", round(c.meta["S"], 2))


def sheet(ids):
    """sheets/altart.png: real card | before (etch) | after (alt-art treatment) | after + text half"""
    ROW_H, GAP, FONT = 820, 28, "C:/Windows/Fonts/consola.ttf"
    sizes = json.loads(SIZES.read_text(encoding="utf-8"))
    rows = []
    for cid in ids:
        card = json.load(open(E.CARDS / f"{cid}.json", encoding="utf-8"))
        info = sizes[cid]
        real = fit_h(Image.open(E.ref_path(cid)).convert("RGB"), ROW_H)
        st0 = Image.open(E.OUT / f"{cid}-card.png").convert("RGB")
        stacked = fit_h(st0, ROW_H)
        k = stacked.height / st0.height                       # art at the same scale as the stacked card
        art0 = Image.open(E.OUT / f"{cid}-art.png").convert("RGB")
        after = art0.resize((round(art0.width * k), round(art0.height * k)), Image.LANCZOS)
        b0 = Image.open(BEFORE / f"{cid}-art.png").convert("RGB")
        bst = Image.open(BEFORE / f"{cid}-card.png")
        kb = ROW_H / bst.height                               # the etch art at its own stacked-card scale
        before = b0.resize((round(b0.width * kb), round(b0.height * kb)), Image.LANCZOS)
        label = (f"{cid}  {card['name']}  {card['number']}/{card['set']['printedTotal']}  tier: {card['tier']}"
                 f"  [alt art]  sprite {info['sprite']} {info['sprite_px'][0]}x{info['sprite_px'][1]}"
                 f"{' flipped' if info['flip'] else ''}  |  art {info['cols']}x{info['lines']}, card "
                 f"{info['cols']}x{info['card_lines']}\nbefore: fingerprint etch (Glaceon 174)   ->   after: "
                 f"{info['finish']}  (mask: {info['mask']})")
        rows.append((label, [real, before, after, stacked]))
    W = max(sum(p.width for p in ps) + GAP * (len(ps) + 1) for _, ps in rows)
    H = sum(ROW_H + 90 + GAP for _ in rows) + 70
    o = Image.new("RGB", (W, H), (24, 24, 28))
    d = ImageDraw.Draw(o)
    d.text((GAP, 14), "Evolving Skies alt-art Rare Ultras: real card | before (etch) | after (alt-art treatment) | "
                      "after + text half", font=ImageFont.truetype(FONT, 36), fill=(235, 235, 235))
    y = 70
    f = ImageFont.truetype(FONT, 24)
    for label, ps in rows:
        d.text((GAP, y + 8), label, font=f, fill=(200, 200, 200))
        x = GAP
        for p in ps:
            o.paste(p, (x, y + 80))
            x += p.width + GAP
        y += ROW_H + 90 + GAP
    out = E.DATA / "sheets" / f"{GROUP}.png"
    o.save(out)
    print(out, o.size)


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    ids = [a for a in sys.argv[2:] if a in SPEC] or IDS
    if cmd == "backup":
        backup(ids)
    elif cmd == "masks":
        build_masks(ids)
    elif cmd == "preview":
        preview(ids)
    elif cmd == "build":
        build(ids)
    elif cmd == "verify":
        sys.exit(verify(ids))
    elif cmd == "sheet":
        sheet(ids)
    elif cmd == "all":
        build(ids)
        code = verify(ids)
        sheet(ids)
        sys.exit(code)


if __name__ == "__main__":
    main()
