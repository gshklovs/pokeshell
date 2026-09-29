r"""Group "ultra_a" of the Evolving Skies full set: 16 Rare Ultra cards (full-art V and alternate-art V), each
built exactly like the approved Rare Ultra, Glaceon V 174 (evcards.glaceon):

  the card's own painting at full grid resolution (LANCZOS, S ~17 card px per sprite px), the real Pokemon
  painted out (tex_fill), sat 1.12, focus halo, radial glow + 12 rays behind the sprite, tinted vignette,
  fingerprint etch (low-contrast raised lines, off-centre whorls), median-cut 170 colours, a 1-px rim light,
  four sparkles; animation = anim.py's "etch" (the lines light up in a rainbow wave along the contours).

Alternate-art V cards (painted scenes) get the same full-art treatment (none of them is the embossed textured
painting of Umbreon 215). Per card only the framing, the painted-out boxes, the flip and the glow / vignette /
rim / sparkle colours change (read off each scan).

  ..\..\..\.venv\Scripts\python batch_ultra_a.py masks            -> masks/<id>.png + work/ua/masks.png
  ..\..\..\.venv\Scripts\python batch_ultra_a.py build [ids]      -> art/, out/, anim/
  ..\..\..\.venv\Scripts\python batch_ultra_a.py verify [ids]
  ..\..\..\.venv\Scripts\python batch_ultra_a.py sheet            -> sheets/ultra_a.png
  ..\..\..\.venv\Scripts\python batch_ultra_a.py all
"""
import json
import runpy
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

import evcards
import evlib as E
from evlib import L, Card, Sprite
from evcards import fingerprint, meta, place

GROUP = "ultra_a"
PLAN = json.loads((E.HERE / "plan.json").read_text(encoding="utf-8"))[GROUP]
IDS = [c["id"] for c in PLAN]
SPRITE = {c["id"]: c["sprite"] for c in PLAN}
UA = E.WORK / "ua"

EDGES = ((0, 0, 734, 100), (0, 0, 70, 230), (0, 0, 30, 1024), (700, 0, 734, 1024))

# per card: text_y = where the attack / ability text starts (everything below is painted out, as Glaceon's 585),
# flip = face the way the card does, glow = the light behind the Pokemon, tint = the vignette's deep colour,
# rim = rim light, star = sparkle (mid, tip) colours, frame = text-half frame colour, alt = alternate art,
# model / hull / cut / keep / close: the mask (rembg model constrained to a card-px polygon)
SPEC = {
    "swsh7-166": dict(name="Leafeon V", text_y=620, flip=False, glow=(1.0, 0.93, 0.62), tint=(0.35, 0.08, 0.0),
                      rim=(1.0, 0.97, 0.8), star=("#fff6d8", "#ffe08a"), models=("isnet-general-use",), close=10,
                      hull=[(80, 250), (120, 110), (260, 120), (300, 140), (420, 120), (470, 190), (560, 200),
                            (700, 280), (690, 420), (630, 580), (560, 640), (40, 640), (40, 450), (70, 330)]),
    "swsh7-167": dict(name="Leafeon V", text_y=620, flip=False, glow=(1.0, 0.95, 0.75), tint=(0.1, 0.12, 0.02),
                      rim=(1.0, 1.0, 0.85), star=("#fffbe0", "#c8f5a0"), alt=True, models=(),
                      hull=[(130, 300), (160, 230), (230, 170), (280, 190), (300, 170), (380, 190), (430, 180),
                            (500, 160), (560, 190), (540, 260), (500, 310), (510, 450), (560, 560), (480, 590),
                            (400, 570), (280, 570), (250, 500), (170, 440)]),
    "swsh7-168": dict(name="Trevenant V", text_y=680, glow_amt=0.22, flip=False, glow=(0.85, 1.0, 0.75), tint=(0.02, 0.15, 0.05),
                      rim=(0.9, 1.0, 0.85), star=("#f0ffe6", "#b8ff9f"), models=(),
                      hull=[(40, 240), (40, 105), (160, 105), (230, 150), (290, 160), (380, 100), (460, 110), (520, 230),
                            (640, 250), (705, 300), (705, 470), (600, 470), (560, 500), (705, 700), (40, 700),
                            (40, 560)]),
    "swsh7-169": dict(name="Flareon V", text_y=655, flip=False, glow=(1.0, 0.85, 0.55), tint=(0.02, 0.15, 0.2),
                      rim=(1.0, 0.95, 0.8), star=("#fff0d8", "#ffc080"), models=("u2net",),
                      extra_boxes=((500, 100, 700, 172),),
                      hull=[(40, 190), (250, 230), (330, 190), (420, 100), (560, 120), (705, 220), (705, 520),
                            (640, 560), (640, 700), (40, 700), (40, 600), (150, 450)]),
    "swsh7-173": dict(name="Suicune V", text_y=620, flip=False, glow=(0.75, 0.95, 1.0), tint=(0.0, 0.12, 0.2),
                      rim=(0.85, 0.97, 1.0), star=("#e6fbff", "#9fe8ff"), models=("u2net",),
                      hull=[(30, 110), (560, 105), (620, 250), (720, 480), (705, 640), (30, 640)]),
    "swsh7-170": dict(name="Volcarona V", text_y=625, flip=False, glow=(1.0, 0.85, 0.55), tint=(0.3, 0.02, 0.1),
                      rim=(1.0, 0.95, 0.8), star=("#fff0d8", "#ffc080"), models=(),
                      hull=[(20, 255), (95, 230), (110, 130), (200, 105), (300, 110), (360, 160), (400, 230),
                            (440, 260), (520, 230), (620, 215), (705, 210), (705, 420), (640, 450), (705, 560),
                            (705, 650), (40, 650), (60, 460), (20, 420)]),
    "swsh7-171": dict(name="Gyarados V", text_y=690, flip=False, glow=(0.75, 0.95, 1.0), tint=(0.1, 0.02, 0.25),
                      rim=(0.85, 0.97, 1.0), star=("#e6fbff", "#9fe8ff"), models=(),
                      hull=[(60, 380), (130, 380), (200, 240), (300, 160), (400, 100), (610, 100), (720, 200),
                            (705, 350), (660, 440), (660, 640), (560, 660), (560, 700), (40, 700), (40, 560)]),
    "swsh7-172": dict(name="Vaporeon V", text_y=690, flip=False, glow=(0.8, 0.95, 1.0), tint=(0.15, 0.1, 0.3),
                      rim=(0.85, 0.97, 1.0), star=("#e6fbff", "#9fe8ff"), models=("isnet-general-use",),
                      extra_boxes=((480, 100, 700, 172),),
                      hull=[(30, 420), (90, 420), (150, 280), (180, 140), (250, 200), (320, 180), (410, 90),
                            (450, 150), (420, 250), (520, 300), (705, 260), (705, 700), (30, 700)]),
    "swsh7-178": dict(name="Dracozolt V", text_y=625, flip=True, glow=(1.0, 0.95, 0.6), tint=(0.0, 0.12, 0.2),
                      rim=(1.0, 1.0, 0.8), star=("#fffbe0", "#ffe98a"), models=(),
                      hull=[(30, 320), (80, 100), (300, 110), (420, 190), (560, 95), (640, 95), (640, 280), (720, 300),
                            (720, 440), (680, 480), (680, 640), (30, 640)]),
    "swsh7-177": dict(name="Jolteon V", text_y=655, flip=False, glow=(1.0, 0.95, 0.6), tint=(0.02, 0.05, 0.25),
                      rim=(1.0, 1.0, 0.8), star=("#fffbe0", "#ffe98a"), models=(),
                      hull=[(50, 95), (290, 95), (340, 250), (420, 100), (600, 95), (560, 300), (705, 330),
                            (705, 500), (640, 540), (640, 670), (80, 670), (90, 420)]),
    "swsh7-175": dict(name="Glaceon V", text_y=625, flip=False, glow=(0.8, 0.95, 1.0), tint=(0.1, 0.12, 0.2),
                      rim=(0.85, 0.97, 1.0), star=("#e6fbff", "#9fe8ff"), alt=True, models=("u2net",),
                      hull=[(190, 300), (260, 220), (330, 260), (400, 210), (500, 240), (520, 350), (460, 500),
                            (390, 500), (250, 440), (200, 400)]),
    "swsh7-176": dict(name="Arctovish V", text_y=655, flip=False, glow=(0.8, 0.95, 1.0), tint=(0.0, 0.12, 0.2),
                      rim=(0.85, 0.97, 1.0), star=("#e6fbff", "#9fe8ff"), models=(),
                      hull=[(30, 280), (70, 220), (200, 160), (400, 140), (470, 250), (520, 340), (705, 230),
                            (705, 660), (30, 660)]),
    "swsh7-180": dict(name="Espeon V", text_y=660, flip=False, glow=(1.0, 0.88, 0.95), tint=(0.2, 0.05, 0.2),
                      rim=(1.0, 0.92, 1.0), star=("#fff0fa", "#f0b8ff"), alt=True, models=(),
                      hull=[(300, 300), (360, 140), (400, 230), (460, 160), (480, 290), (560, 280), (620, 270),
                            (680, 340), (640, 450), (570, 420), (560, 600), (420, 600), (360, 520), (330, 380)]),
    "swsh7-181": dict(name="Golurk V", text_y=655, flip=False, glow=(1.0, 0.95, 0.7), tint=(0.25, 0.08, 0.0),
                      rim=(1.0, 0.97, 0.9), star=("#fff8e6", "#ffe0a0"), models=("isnet-anime",),
                      extra_boxes=((500, 100, 700, 172),),
                      hull=[(30, 240), (120, 210), (290, 180), (330, 110), (400, 130), (450, 210), (620, 200),
                            (705, 240), (705, 480), (600, 500), (620, 670), (160, 670), (150, 480), (30, 450)]),
    "swsh7-179": dict(name="Espeon V", text_y=660, flip=True, glow=(1.0, 0.97, 0.75), tint=(0.25, 0.1, 0.0),
                      rim=(1.0, 0.95, 1.0), star=("#fff0fa", "#fff0a0"), models=("isnet-general-use",),
                      hull=[(20, 300), (90, 200), (160, 160), (260, 160), (420, 230), (560, 100), (620, 110),
                            (640, 340), (620, 440), (560, 470), (560, 580), (640, 620), (640, 680), (20, 680)]),
    "swsh7-184": dict(name="Sylveon V", text_y=655, flip=False, glow=(1.0, 0.9, 0.85), tint=(0.3, 0.05, 0.05),
                      rim=(1.0, 0.94, 0.98), star=("#fff0fa", "#ffc0e0"), alt=True, models=("isnet-general-use",),
                      extra_boxes=((480, 100, 700, 172),),
                      hull=[(100, 160), (160, 110), (260, 150), (300, 100), (360, 140), (380, 230), (460, 300),
                            (560, 220), (640, 220), (660, 300), (560, 320), (460, 330), (430, 500), (360, 510),
                            (260, 470), (200, 420), (170, 330), (160, 230)]),
}
DEFAULTS = dict(models=(), hull=None, cut=(), keep=1, close=4, grow=5, tex_src=None, dx=0, dy=0,
                W=None, H=None, x0=10, y0=80, whorls=None, extra_boxes=(), alt=False, scene="", sat=1.12,
                glow_amt=0.36, vig=0.5)


def spec(cid):
    return {**DEFAULTS, **SPEC[cid]}


# ============================================================ masks (as masks.py: rembg constrained by a hull)
def build_mask(cid):
    """rembg (union of the listed models) inside a hand hull (card px); no models = the hull itself (the
    segmenters fail on that painting). Cut at the text line: everything below is painted out anyway."""
    import masks as M
    s = spec(cid)
    sh = E.card_img(cid).shape[:2]
    hull = M.poly(sh, s["hull"]) & M.rect(sh, 30, 95, 704, s["text_y"] + 20)
    if s["models"]:
        m = np.zeros(sh, bool)
        for mdl in s["models"]:
            m |= M.rembg(cid, mdl)
        m &= hull
        if s["close"]:
            m = ndimage.binary_closing(m, iterations=s["close"])
        m = ndimage.binary_fill_holes(M.largest(m, s["keep"])) & hull
    else:
        m = hull
    return m


def masks(ids):
    E.MASKS.mkdir(exist_ok=True)
    UA.mkdir(parents=True, exist_ok=True)
    tiles = []
    for cid in ids:
        m = build_mask(cid)
        Image.fromarray((m * 255).astype(np.uint8)).save(E.MASKS / f"{cid}.png")
        rgb = E.card_img(cid)
        o = np.where(m[..., None], rgb, rgb * 0.25 + np.array([0, 0.3, 0]))
        tiles.append(Image.fromarray(L.to8(o)).resize((367, 512)))
        ys, xs = np.nonzero(m)
        print(cid, "bbox", xs.min(), ys.min(), xs.max(), ys.max(), f"{m.mean():.2f}")
    n = 4
    sheet = Image.new("RGB", (367 * n, 512 * ((len(tiles) + n - 1) // n)))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % n) * 367, (i // n) * 512))
    sheet.save(UA / "masks.png")


# ============================================================ the Rare Ultra builder (Glaceon V 174's recipe)
def auto_tex_src(cid, m, text_y, w=200, h=160):
    """a fully-known scene rectangle for tex_fill's wrapped texture: the most textured one not touching the
    mask / boxes"""
    rgb = E.card_img(cid)
    best, bs = None, -1
    for y in range(110, max(111, text_y - h), 20):
        for x in range(40, 700 - w, 20):
            if m[y:y + h, x:x + w].any():
                continue
            v = rgb[y:y + h, x:x + w].std()
            if v > bs:
                best, bs = (x, y, x + w, y + h), v
    return best


def whorls_for(c):
    """off-centre whorls like Glaceon's (top-left, bottom-right, top-right corners) scaled to the grid"""
    FW, FH = c.FW, c.FH
    return [(12 / 84 * FW, 10 / 66 * FH, 1.0), (70 / 84 * FW, 52 / 66 * FH, 0.8), (64 / 84 * FW, 8 / 66 * FH, 0.5)]


def stars_for(c):
    FW, FH = c.FW, c.FH
    return [(6, 6, 3), (FW - 6, 10, 2), (FW - 8, FH - 8, 3), (5, FH - 16, 2)]


def make_builder(cid):
    def build():
        s = spec(cid)
        spr = Sprite(SPRITE[cid], flip=s["flip"])
        W = s["W"] or max(42, spr.w + 6)
        H = s["H"] or max(33, spr.h + 3)
        x0, y0 = s["x0"], s["y0"]
        S = s.get("S") or 714 / W
        boxes = EDGES + ((0, s["text_y"], 734, 1024),) + tuple(s["extra_boxes"])
        from scipy import ndimage as nd
        hole = nd.binary_dilation(E.mask(cid), iterations=s["grow"])
        for (a, b, cc, d) in boxes:
            hole[max(0, b):d, max(0, a):cc] = True
        tex = s["tex_src"] or auto_tex_src(cid, hole, s["text_y"])
        rgb, _ = E.clean(cid, grow=s["grow"], boxes=boxes, tex_src=tex)
        c = Card(W, H)
        place(c, spr, cid, x0, y0, S, dx=s["dx"], dy=s["dy"])
        a = L.sample(rgb, x0, y0, S / 2, 2 * W, 2 * H, resample=L.Image.LANCZOS)
        a = L.tone(a, sat=s["sat"], bright=1.0)
        a = L.focus_halo(c, a, radius=5, dark=0.7, soft=1.4)
        a = L.radial_glow(c, a, s["glow"], max(c.FW, c.FH) * 0.55, s["glow_amt"], rays=12, ray_amt=0.5)
        a = L.vignette(a, s["vig"], tint=s["tint"])
        f, line = fingerprint(c.FW, c.FH, s["whorls"] or whorls_for(c), period=2.6, seed=int(E.num(cid)))
        lift = np.where(line, 0.11, -0.025)
        a = np.clip(a + lift[..., None] * (0.6 + 0.4 * a), 0, 1)
        L.finish(c, a, 170, method="median")
        c.bgq = L.rim(c, c.bgq, colour=s["rim"], amt=0.34)
        stars = stars_for(c)
        for x, y, st in stars:
            L.sparkle(c, x, y, st, {"L": "#ffffff", "l": s["star"][0], "j": s["star"][1]})
        num = E.num(cid)
        kind = "alternate-art V, painted scene" if s["alt"] else "full art"
        return meta(c, card=cid, label=f"Rare Ultra: {s['name']} {num}/203 {kind} (fingerprint etch)",
                    rarity="Rare Ultra",
                    finish="full-art V: fingerprint-like etched texture, rainbow on the lines" +
                           (" (alternate art)" if s["alt"] else ""),
                    variant="rare-ultra", anim="etch", ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S, stars=stars,
                    etch_field=f, etch_period=2.6, frame="#e178e6", alt=s["alt"], tex_src=tex)
    build.__name__ = f"ua_{E.num(cid)}"
    return build


def register(ids):
    """put this group's builders into evcards.BUILDERS / ORDER in-process (the shared files stay untouched), so
    build.render / anim.build / verify.py run on them unchanged"""
    for cid in ids:
        evcards.BUILDERS[cid] = make_builder(cid)
    evcards.ORDER[:] = list(ids)


# ============================================================ build / verify / sheet
def _load(name):
    """an evs module by path (a plain `import build` / `import anim` can pick up suite3's)"""
    import importlib.util
    key = f"evs_{name}"
    if key not in sys.modules:
        spec = importlib.util.spec_from_file_location(key, E.HERE / f"{name}.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return sys.modules[key]


def build_ids(ids):
    anim = _load("anim")
    B = _load("build")
    register(ids)
    sizes_f = UA / "sizes.json"
    sizes = json.loads(sizes_f.read_text(encoding="utf-8")) if sizes_f.exists() else {}
    for cid in ids:
        _, info = B.render(cid)
        sizes[cid] = info
        sizes_f.write_text(json.dumps(sizes, indent=1), encoding="utf-8")
    anim.build(ids)


def verify(ids):
    register(ids)
    try:
        runpy.run_path(str(E.HERE / "verify.py"), run_name="__main__")
    except SystemExit as e:
        return e.code or 0
    return 0


def fit_h(im, h):
    return im.resize((round(im.width * h / im.height), h), Image.LANCZOS)


def sheet(ids):
    ROW_H, GAP, FONT = 820, 28, "C:/Windows/Fonts/consola.ttf"
    sizes = json.loads((UA / "sizes.json").read_text(encoding="utf-8"))
    rows = []
    for cid in ids:
        card = json.load(open(E.CARDS / f"{cid}.json", encoding="utf-8"))
        info = sizes[cid]
        real = fit_h(Image.open(E.ref_path(cid)).convert("RGB"), ROW_H)
        st0 = Image.open(E.OUT / f"{cid}-card.png").convert("RGB")
        stacked = fit_h(st0, ROW_H)
        art0 = Image.open(E.OUT / f"{cid}-art.png").convert("RGB")
        k = stacked.height / st0.height
        art = art0.resize((round(art0.width * k), round(art0.height * k)), Image.LANCZOS)
        alt = " [alt art]" if spec(cid)["alt"] else ""
        label = (f"{cid}  {card['name']}  {card['number']}/{card['set']['printedTotal']}  tier: {card['tier']}{alt}"
                 f"  |  art {info['cols']}x{info['lines']}, card {info['cols']}x{info['card_lines']}\n{info['finish']}")
        rows.append((label, [real, art, stacked]))
    W = max(sum(p.width for p in ps) + GAP * (len(ps) + 1) for _, ps in rows)
    H = sum(ROW_H + 90 + GAP for _ in rows) + 70
    o = Image.new("RGB", (W, H), (24, 24, 28))
    d = ImageDraw.Draw(o)
    d.text((GAP, 14), "Evolving Skies ultra_a (Rare Ultra): real card | pokeshell art | art + text half",
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
    o.save(E.DATA / "sheets" / f"{GROUP}.png")
    print(f"sheets/{GROUP}.png", o.size)


def preview(ids):
    """work/ua/<id>-cmp.png: real scan | our art, for quick iteration"""
    UA.mkdir(parents=True, exist_ok=True)
    for cid in ids:
        real = fit_h(Image.open(E.ref_path(cid)).convert("RGB"), 600)
        art = fit_h(Image.open(E.OUT / f"{cid}-art.png").convert("RGB"), 480)
        o = Image.new("RGB", (real.width + art.width + 30, 600), (24, 24, 28))
        o.paste(real, (0, 0))
        o.paste(art, (real.width + 30, 0))
        o.save(UA / f"{cid}-cmp.png")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    ids = [a for a in sys.argv[2:] if a in IDS] or IDS
    if cmd == "masks":
        masks(ids)
    elif cmd == "build":
        build_ids(ids)
        preview(ids)
    elif cmd == "preview":
        preview(ids)
    elif cmd == "art":            # art only (no card data needed): work/ua/<id>-cmp.png for iteration
        UA.mkdir(parents=True, exist_ok=True)
        for cid in ids:
            c = make_builder(cid)()
            rows, pal, _ = L.keyed(c)
            art = L.term_png(rows, pal, UA / f"{cid}-art.png")
            real = fit_h(Image.open(E.ref_path(cid)).convert("RGB"), 600)
            art = fit_h(art.convert("RGB"), 480)
            o = Image.new("RGB", (real.width + art.width + 30, 600), (24, 24, 28))
            o.paste(real, (0, 0))
            o.paste(art, (real.width + 30, 0))
            o.save(UA / f"{cid}-cmp.png")
            print(cid, c.FW, "x", c.FH // 2, "sprite at", c.off)
    elif cmd == "verify":
        sys.exit(verify(ids))
    elif cmd == "sheet":
        sheet(ids)
    elif cmd == "all":
        masks(ids)
        build_ids(ids)
        preview(ids)
        rc = verify(ids)
        sheet(ids)
        sys.exit(rc)
