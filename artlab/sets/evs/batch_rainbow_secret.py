r"""Evolving Skies full set, group "rainbow_secret": the Rare Rainbow (true rainbow + alternate-art secrets) and
the Rare Secret (gold) cards, built exactly like the approved examples:

  true rainbow   Leafeon VMAX 204 (evcards.leafeon)   pastel rainbow gradient, dense etch, glitter, the sprite
                                                      re-tinted RAINBOW_BLEND (0.55) toward its body rainbow
  alt art        Umbreon VMAX 215 (evcards.umbreon)   the painting, embossed along its own brushwork; sprite as is
  gold secret    Froslass 226 (evcards2.froslass)     gold sprite remap, faceted etched gold, glitter, star flares

Which API "Rare Rainbow" cards are really alt-art secrets was decided from each scan (KIND below).
Shared files are not edited: this module registers its builders into evcards.BUILDERS at runtime so
build.render / anim.build / verify.py's checks run unchanged on these ids.

  ..\..\..\.venv\Scripts\python batch_rainbow_secret.py masks [ids]     rembg masks -> masks/<id>.png + work/rs/masks.png
  ..\..\..\.venv\Scripts\python batch_rainbow_secret.py build [ids]     art json + static renders + animations
  ..\..\..\.venv\Scripts\python batch_rainbow_secret.py verify          verify.py's checks on this group
  ..\..\..\.venv\Scripts\python batch_rainbow_secret.py sheet           sheets/rainbow_secret.png
"""
import json
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

import evcards
import evcards2 as B2
import evlib as E
from evcards import (W_LUM, colour_blend, meta, place, rainbow_etch, rainbow_rgb, rainbow_sprite)
from evlib import L, Card, Sprite

GROUP = "rainbow_secret"
PLAN = json.load(open(E.HERE / "plan.json", encoding="utf-8"))[GROUP]
EDGES = ((0, 0, 30, 1024), (700, 0, 734, 1024))

# ---------------------------------------------------------------------------------------------------------
# per card: kind (rainbow / alt / gold, from the scan), sprite, flip (face the way the card does), the crop
# (x0, y0, S, W, H in sprite px), sprite offset, text / logo boxes to paint out, mask recipe, and extras.
# Filled in per card after looking at its scan.
CFG = {}


def cfg(cid, **kw):
    CFG[cid] = kw


# ---- helpers ----------------------------------------------------------------------------------------
def stars_for(c, cands, min_d=4):
    """keep the candidate sparkles that sit on background, clear of the sprite"""
    d = c.dist()
    out = []
    for x, y, st in cands:
        x, y = min(max(3, x), c.FW - 4), min(max(3, y), c.FH - 4)
        if d[y, x] > min_d:
            out.append((x, y, st))
    return out


def corner_stars(c):
    FW, FH = c.FW, c.FH
    cands = [(6, 6, 3), (FW - 8, 8, 2), (FW - 6, FH - 8, 3), (6, FH - 12, 2), (FW // 2, 3, 1),
             (FW // 4, FH - 4, 2), (FW - 4, FH // 2, 2), (4, FH // 2, 2), (3 * FW // 4, 4, 2)]
    return stars_for(c, cands)[:5]


def build_sprite(k):
    return Sprite(k["sprite"], flip=k.get("flip", False))


def place_sprite(c, spr, cid, k):
    x0, y0, S = k["x0"], k["y0"], k["S"]
    if "off" in k:
        return place(c, spr, cid, x0, y0, S, off=k["off"])
    return place(c, spr, cid, x0, y0, S, dx=k.get("dx", 0), dy=k.get("dy", 0), margin=k.get("margin", 1))


def ref_box(cid, k, c):
    return (cid, k["x0"], k["y0"], k["x0"] + c.W * k["S"], k["y0"] + c.H * k["S"])


def label_for(cid, kind, name, num):
    return {"rainbow": f"Rare Rainbow: {name} {num}/203, rainbow secret (gradient + etched lines + glitter)",
            "alt": f"Rare Rainbow (alt art): {name} {num}/203 (textured painting)",
            "gold": f"Rare Secret: {name} {num}/203 gold (gold remap, faceted etched gold, glitter)"}[kind]


# ---- true rainbow: Leafeon VMAX 204's recipe -------------------------------------------------------------
def build_rainbow(cid, k):
    x0, y0, S, W, H = k["x0"], k["y0"], k["S"], k["W"], k["H"]
    boxes = EDGES + k["boxes"]
    rgb, _ = E.clean(cid, grow=14, boxes=boxes, texture=False)
    spr = build_sprite(k)
    c = Card(W, H)
    place_sprite(c, spr, cid, k)
    rainbow_sprite(c)
    a = L.sample(rgb, x0, y0, S / 2, 2 * W, 2 * H, resample=L.Image.LANCZOS)
    FH, FW = c.FH, c.FW
    yy, xx = np.mgrid[0:FH, 0:FW]
    hue = -0.04 + (xx / FW * 0.5 + yy / FH * 0.42) + k.get("hue_shift", 0.0)
    a = colour_blend(np.clip(a * 0.9 + 0.12, 0, 1), rainbow_rgb(hue, s=0.45), 0.5)
    a = L.tone(a, sat=1.05, bright=1.0)
    a = L.focus_halo(c, a, radius=4, dark=0.82, soft=1.2)
    line, glint = rainbow_etch(FW, FH, seed=204)          # anim.anim_rainbow flashes the seed-204 lines
    a = np.clip(a + np.where(line, -0.07, 0.025)[..., None], 0, 1)
    L.finish(c, a, 150, method="median")
    q = c.bgq.astype(float) / 255
    d = c.dist()
    g = glint & (d > 2)
    q[g] = np.clip(q[g] * 0.3 + 0.75, 0, 1)
    c.bgq = L.to8(q)
    c.bgq = L.rim(c, c.bgq, colour=(1, 1, 1), amt=0.5)
    stars = corner_stars(c)
    for x, y, st in stars:
        L.sparkle(c, x, y, st, {"L": "#ffffff", "l": "#fff0fa", "j": "#b8f0ff"})
    return meta(c, card=cid, rarity="Rare Rainbow",
                finish="rainbow secret: pastel rainbow gradient, dense etched texture, glitter",
                variant="rare-rainbow", anim="rainbow", ref=ref_box(cid, k, c), S=S, stars=stars,
                frame="rainbow", glint=[(int(x), int(y)) for y, x in zip(*np.nonzero(g))])


# ---- alt art: Umbreon VMAX 215's recipe ------------------------------------------------------------------
def build_alt(cid, k):
    x0, y0, S, W, H = k["x0"], k["y0"], k["S"], k["W"], k["H"]
    boxes = EDGES + k["boxes"]
    rgb, _ = E.clean(cid, grow=5, boxes=boxes, tex_src=k.get("tex_src"))
    spr = build_sprite(k)
    c = Card(W, H)
    place_sprite(c, spr, cid, k)
    a = L.sample(rgb, x0, y0, S / 2, 2 * W, 2 * H, resample=L.Image.LANCZOS)
    a = L.tone(a, sat=1.15, bright=k.get("bright", 1.02))
    a = L.focus_halo(c, a, radius=4, dark=0.8, soft=1.2)
    lum = a @ W_LUM
    h = ndimage.gaussian_filter(lum, 0.6)
    gy, gx = np.gradient(h)
    relief = np.clip(-(gx * -1.0 + gy * -1.3) * 2.4, -0.3, 0.3)
    a = np.clip(a + relief[..., None] * (0.35 + 0.65 * a), 0, 1)
    a = L.vignette(a, 0.4, tint=k.get("vig", (0.02, 0.04, 0.12)))
    L.finish(c, a, 200, method="median")
    c.bgq = L.rim(c, c.bgq, colour=k.get("rim", (1.0, 1.0, 1.0)), amt=0.45)
    stars = corner_stars(c)[:4]
    for x, y, st in stars:
        L.sparkle(c, x, y, st, {"L": "#ffffff", "l": "#fff3c4", "j": "#8fd8ff"})
    return meta(c, card=cid, rarity="Rare Rainbow",
                finish="alternate-art secret: textured painting (brushwork embossed)",
                variant="rare-rainbow-alt", anim="paint", ref=ref_box(cid, k, c), S=S, stars=stars,
                height=h, frame="#f0c850")


# ---- gold secret: Froslass 226's recipe ------------------------------------------------------------------
def build_gold(cid, k):
    import tiers as s3t
    x0, y0, S, W, H = k["x0"], k["y0"], k["S"], k["W"], k["H"]
    boxes = EDGES + k["boxes"]
    rgb, _ = E.clean(cid, grow=5, boxes=boxes, texture=False)
    spr = build_sprite(k)
    c = Card(W, H)
    place_sprite(c, spr, cid, k)
    # some vendor sprites draw their outline in a near-black (Inteleon: #000400) instead of #000000; the
    # gold remap would turn it dark gold and lose the outline, so near-blacks are pinned to black
    # (still a pure palette remap)
    near = {v.lower(): "#000000" for v in list(spr.pal.values()) + list(spr.shiny.values())
            if max(L.hexrgb(v)) <= 20}          # incl. a black px whose shiny isn't black (own key, not "k")
    gpal, gshiny = L.gold_remap(spr, L.gold_ramp(s3t.RAMP, 24), L.gold_ramp(s3t.RAMP_AMBER, 24), special=near or None)
    c.put_sprite(spr, *c.off, gpal, gshiny)
    a = L.sample(rgb, x0, y0, S / 2, c.FW, c.FH, resample=L.Image.BOX)
    lum = a @ W_LUM
    lum = (lum - lum.min()) / max(1e-6, lum.max() - lum.min())
    h = np.clip((ndimage.gaussian_filter(lum, 0.8) - 0.1) / 0.8, 0, 1)
    seed = int(E.num(cid))
    fh, seam, _ = s3t.facet_height(c.FW, c.FH, n=70, seed=seed)
    s3t.gold_foil(c, np.zeros_like(h), 1 - h, lo=0.0, hi=0.0, relief=0.0, glow=0.3, glow_r=9, seed=seed,
                  glints=26, facets=0.34 + 0.22 * (h - 0.5) + 0.16 * (fh - 0.5) + 0.5 * s3t.emboss(fh) - 0.05 * seam)
    FW, FH = c.FW, c.FH
    stars = stars_for(c, [(6, 8, 3), (FW - 8, 6, 3), (FW - 6, FH - 26, 3), (5, FH - 20, 2), (FW // 2, FH - 4, 2),
                          (FW - 14, FH // 3, 1), (FW // 2, 4, 2), (8, FH // 2, 2)])[:6]
    for x, y, st in stars:
        L.sparkle(c, x, y, st, s3t.GOLD_SPARK)
    return meta(c, card=cid, rarity="Rare Secret",
                finish="gold secret: gold sprite remap, crystalline etched gold, glitter",
                variant="rare-secret", anim="gold", ref=ref_box(cid, k, c), S=S, stars=stars, sprite_recolour="gold")


KINDS = {"rainbow": build_rainbow, "alt": build_alt, "gold": build_gold}


def builder(cid):
    def fn():
        k = CFG[cid]
        c = KINDS[k["kind"]](cid, k)
        f = E.CARDS / f"{cid}.json"
        nm = json.load(open(f, encoding="utf-8"))["name"] if f.exists() else next(p["name"] for p in PLAN if p["id"] == cid)
        c.meta["label"] = label_for(cid, k["kind"], nm, E.num(cid)) + k.get("note", "")
        return c
    fn.__name__ = f"build_{cid.replace('-', '_')}"
    return fn


def register(ids):
    for cid in ids:
        evcards.BUILDERS[cid] = builder(cid)


# ---- masks ------------------------------------------------------------------------------------------------
def make_mask(cid):
    import masks as M
    k = CFG[cid]
    rgb = E.card_img(cid)
    sh = rgb.shape[:2]
    mk = k.get("mask", {})
    m = M.rembg(cid, mk.get("model", "isnet-general-use")) & M.rect(sh, *mk.get("box", (0, 60, 734, 900)))
    if "hull" in mk:                                  # hand polygon (card px) around the painted Pokemon
        m = M.poly(sh, mk["hull"])
    for cut in mk.get("cut", ()):
        m &= ~M.rect(sh, *cut)
    for p in mk.get("cut_poly", ()):
        m &= ~M.poly(sh, p)
    for p in mk.get("add_poly", ()):
        m |= M.poly(sh, p)
    if mk.get("close"):
        m = ndimage.binary_closing(m, iterations=mk["close"])
    m = ndimage.binary_fill_holes(M.largest(m, mk.get("keep", 1)))
    Image.fromarray((m * 255).astype(np.uint8)).save(E.MASKS / f"{cid}.png")
    o = np.where(m[..., None], rgb, rgb * 0.25 + np.array([0, 0.3, 0]))
    return Image.fromarray(L.to8(o)).resize((367, 512))


def evs_module(name):
    """import evs/<name>.py by path: evlib puts suite3/ first on sys.path, and suite3 has its own anim.py,
    build.py and verify.py"""
    import importlib.util
    spec = importlib.util.spec_from_file_location(f"evs_{name}", E.HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[f"evs_{name}"] = mod
    spec.loader.exec_module(mod)
    return mod


# ---- build / verify / sheet ------------------------------------------------------------------------------
def do_build(ids):
    register(ids)
    anim = evs_module("anim")
    build = evs_module("build")
    sizes_f = E.DATA / "sheets" / f"{GROUP}-sizes.json"
    sizes = json.load(open(sizes_f, encoding="utf-8")) if sizes_f.exists() else {}
    for cid in ids:
        _, info = build.render(cid)
        c = evcards.BUILDERS[cid]()
        info.update(kind=CFG[cid]["kind"], sprite=c.spr.name, sprite_px=[c.spr.w, c.spr.h])
        sizes[cid] = info
    sizes_f.parent.mkdir(exist_ok=True)
    sizes_f.write_text(json.dumps(sizes, indent=1), encoding="utf-8")
    anim.build(ids)


def do_verify(ids):
    """verify.py runs its checks over evcards.ORDER at import: point ORDER at this group, import it"""
    register(ids)
    evcards.ORDER[:] = ids
    try:
        evs_module("verify")
    except SystemExit as e:
        print("verify exit code", e.code)
        return e.code
    return 0


def do_sheet(ids, name=None):
    FONT = "C:/Windows/Fonts/consola.ttf"
    ROW_H, GAP = 820, 28
    sizes = json.load(open(E.DATA / "sheets" / f"{GROUP}-sizes.json", encoding="utf-8"))

    def fit_h(im, h):
        return im.resize((round(im.width * h / im.height), h), Image.LANCZOS)

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
        kind = {"rainbow": "true rainbow", "alt": "ALT ART (painted scene)", "gold": "gold"}[info["kind"]]
        label = (f"{cid}  {card['name']}  {card['number']}/203  tier: {card['tier']}  [{kind}]  sprite {info['sprite']}"
                 f" {info['sprite_px'][0]}x{info['sprite_px'][1]}{' flipped' if info['flip'] else ''}  |  art "
                 f"{info['cols']}x{info['lines']}, card {info['cols']}x{info['card_lines']}\n{info['finish']}")
        rows.append((label, [real, art, stacked]))
    W = max(sum(p.width for p in ps) + GAP * (len(ps) + 1) for _, ps in rows)
    H = sum(ROW_H + 90 + GAP for _ in rows) + 70
    o = Image.new("RGB", (W, H), (24, 24, 28))
    d = ImageDraw.Draw(o)
    d.text((GAP, 14), "Evolving Skies (swsh7) rainbow + secret: real card | pokeshell art | art + text half",
           font=ImageFont.truetype(FONT, 36), fill=(235, 235, 235))
    y = 70
    f = ImageFont.truetype(FONT, 24)
    for label, ps in rows:
        d.text((GAP, y + 8), label, font=f, fill=(200, 200, 200))
        x = GAP
        for p in ps:
            o.paste(p, (x, y + 80))
            x += p.width + GAP
        y += ROW_H + 90 + GAP
    out = E.DATA / "sheets" / (name or f"{GROUP}.png")
    o.save(out)
    print(out, o.size)


# ==== per-card configs (CFG_BEGIN) ====
# approved example geometry per kind: (x0 of a full-width crop, y0, max S, crop width, crop height, min W, min H)
GEO = {"rainbow": (17, 78, 17.5, 700, 595, 40, 34),       # Leafeon VMAX 204: 40x34 at S 17.5
       "alt": (10, 100, 17.0, 714, 544, 42, 32),          # Umbreon VMAX 215: 42x32 at S 17
       "gold": (47, 92, 20.0, 640, 660, 32, 33)}          # Froslass 226: 32x33 at S 20
TOP = (0, 0, 734, 80)
VMAX_LOGO = (0, 30, 112, 150)
EVOLVES = (95, 78, 345, 145)
STRIKE = (440, 84, 712, 170)
STAGE = (0, 58, 330, 140)


def card(cid, kind, sprite, flip=False, text_y=640, extra_boxes=(), W=None, H=None, dy_crop=0, **kw):
    """geometry: a sprite bigger than the approved canvas is built at TRUE size -- the canvas grows to hold it
    (S shrinks so the crop still spans the card's art height, W grows so it still spans the card's width)"""
    x0f, y0, smax, cw, ch, wmin, hmin = GEO[kind]
    spr = Sprite(sprite, flip)
    H = H or max(hmin, spr.h + 3)
    S = min(smax, ch / H)
    W = W or max(wmin, spr.w + 6, round(cw / S))
    x0 = 367 - W * S / 2
    top = (TOP, VMAX_LOGO, EVOLVES) if kind != "gold" else ((0, 0, 734, 96), STAGE)
    boxes = top + tuple(extra_boxes) + ((0, text_y, 734, 1024),)
    kw.setdefault("mask", {"model": "u2net", "close": 6, "keep": 3})
    CFG[cid] = dict(kind=kind, sprite=sprite, flip=flip, x0=x0, y0=y0 + dy_crop, S=S, W=W, H=H, boxes=boxes, **kw)


UMB_STRIKE = (430, 92, 708, 168)
# alternate-art secrets (full painted scenes): Umbreon VMAX 215's recipe, hand hulls round the Pokemon
card("swsh7-205", "alt", "leafeon", text_y=640, tex_src=(20, 250, 150, 420), rim=(1.0, 0.6, 0.8),
     mask={"hull": [(150, 110), (420, 100), (470, 270), (560, 330), (560, 610), (430, 620), (330, 560),
                    (130, 560), (120, 470), (190, 300)]})
card("swsh7-209", "alt", "glaceon", flip=True, text_y=598, tex_src=(20, 200, 180, 400), rim=(1.0, 0.55, 0.85),
     mask={"hull": [(200, 150), (330, 40), (560, 20), (620, 120), (600, 300), (560, 580), (390, 590), (300, 560),
                    (230, 420), (190, 300)]})
card("swsh7-212", "alt", "sylveon", text_y=590, extra_boxes=(UMB_STRIKE,), tex_src=(20, 400, 170, 560),
     rim=(1.0, 0.8, 0.95),
     mask={"hull": [(200, 100), (620, 95), (660, 220), (600, 370), (490, 400), (480, 560), (290, 560), (270, 420),
                    (180, 310)]})
card("swsh7-218", "alt", "rayquaza", flip=True, text_y=575, extra_boxes=(UMB_STRIKE,), tex_src=(20, 380, 190, 560),
     rim=(1.0, 0.45, 0.6),
     mask={"hull": [(200, 180), (330, 170), (450, 230), (460, 330), (560, 400), (660, 450), (660, 560), (470, 570),
                    (330, 540), (250, 470), (210, 330)]})
card("swsh7-220", "alt", "duraludon-gmax", text_y=595, extra_boxes=(UMB_STRIKE,), tex_src=(20, 200, 200, 400),
     rim=(1.0, 0.45, 0.7), note=" -- Gigantamax (the card is Gigantamax Duraludon)",
     mask={"hull": [(340, 60), (440, 60), (470, 250), (620, 320), (700, 420), (700, 600), (250, 620), (50, 620),
                    (50, 470), (200, 420), (300, 300)]})
# true rainbows: Leafeon VMAX 204's recipe
card("swsh7-216", "rainbow", "garbodor-gmax", text_y=595, note=" -- Gigantamax (the card is Gigantamax Garbodor)")
card("swsh7-219", "rainbow", "duraludon-gmax", text_y=595, extra_boxes=(UMB_STRIKE,),
     note=" -- Gigantamax (the card is Gigantamax Duraludon)")
card("swsh7-206", "rainbow", "trevenant", text_y=685, mask={"model": "isnet-general-use", "close": 6, "keep": 4})
card("swsh7-207", "rainbow", "gyarados", flip=True, text_y=715)
card("swsh7-210", "rainbow", "dracozolt", text_y=655, mask={"model": "isnet-general-use", "close": 6, "keep": 4})
card("swsh7-213", "rainbow", "lycanroc-dusk", flip=True, text_y=600,
     note=" -- Dusk Form (the card's orange Lycanroc)")
card("swsh7-208", "rainbow", "glaceon", text_y=612)
card("swsh7-211", "rainbow", "sylveon", text_y=592, extra_boxes=(STRIKE,))
card("swsh7-214", "rainbow", "umbreon", text_y=655, extra_boxes=(STRIKE,))
card("swsh7-217", "rainbow", "rayquaza", text_y=565, extra_boxes=(STRIKE,))
card("swsh7-227", "gold", "inteleon", text_y=548, extra_boxes=(STRIKE,),
     mask={"model": "isnet-general-use", "close": 4, "keep": 2, "box": (30, 80, 704, 1000)})
card("swsh7-228", "gold", "cresselia", flip=True, text_y=555,
     mask={"model": "u2net", "close": 4, "keep": 2, "box": (30, 60, 704, 1000)})
# ==== (CFG_END) ====


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    ids = [a for a in sys.argv[2:] if a in CFG] or [c["id"] for c in PLAN if c["id"] in CFG]
    if cmd == "masks":
        tiles = [make_mask(cid) for cid in ids]
        sheet = Image.new("RGB", (367 * min(6, len(tiles)), 512 * ((len(tiles) + 5) // 6)))
        for i, t in enumerate(tiles):
            sheet.paste(t, ((i % 6) * 367, (i // 6) * 512))
        sheet.save(E.WORK / "rs" / "masks.png")
    elif cmd == "build":
        do_build(ids)
    elif cmd == "verify":
        sys.exit(do_verify(ids))
    elif cmd == "preview":
        register(ids)
        ims = []
        for cid in ids:
            c = evcards.BUILDERS[cid]()
            rows, pal, _ = L.keyed(c)
            art = L.term_png(rows, pal, E.WORK / "rs" / f"{cid}-art.png").convert("RGB")
            real = Image.open(E.ref_path(cid)).convert("RGB")
            real = real.resize((round(real.width * 520 / real.height), 520))
            art = art.resize((round(art.width * 380 / art.height), 380), Image.LANCZOS)
            ims += [real, art]
            print(cid, c.W, c.H, "sprite", c.spr.w, c.spr.h, "at", c.off, "S", round(CFG[cid]["S"], 2))
        o = Image.new("RGB", (sum(i.width + 12 for i in ims), 520), (24, 24, 28))
        x = 0
        for i in ims:
            o.paste(i, (x, 0))
            x += i.width + 12
        o.save(E.WORK / "rs" / "preview.png")
    elif cmd == "sheet":
        do_sheet(ids, sys.argv[3] if len(sys.argv) > 3 and sys.argv[2] == "--name" else None)


if __name__ == "__main__":
    main()
