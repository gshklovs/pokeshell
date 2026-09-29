r"""Evolving Skies full set, group "holo": the 19 Rare Holo cards in plan.json, each built exactly like the
approved Rare Holo example, Salamence 109 (evcards2.salamence):

  the scan's art window with the real Pokemon masked out (rembg / colour rules / hand polygons, per id) and
  filled, the UNMODIFIED colorscripts sprite (horizontal flip only, to face the way the card does) placed where
  the card's Pokemon stands, suite3's holo_scene: grid-scale scene, 12 colours, rainbow foil bands (0.22),
  starlight specks, 1 px light rim, four sparkles; anim "holo" (a wide rainbow band sweeps the art box).

Geometry: the SWSH art window (64, 96)-(684, 492) scaled so the sprite fills it about as much as Salamence's
does (H = sprite height + 2 grid rows, S = 396 / H). Tall sprites would make the art very wide, so the crop
may be narrowed (never below 1.3:1) around the card's Pokemon ("fit to the card").

  ..\..\..\.venv\Scripts\python batch_holo.py masks|build|anim|verify|sheet|all [ids...]
"""
import json
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

import evlib as E
from evlib import L, Sprite
import evcards
from evcards import meta
from evcards2 import STAGE_BOX, window_rgb

GROUP = "holo"
PLAN = json.load(open(E.HERE / "plan.json", encoding="utf-8"))[GROUP]
IDS = [p["id"] for p in PLAN]
WIN = (64, 96, 684, 492)                   # Salamence's crop: x0, y0 and 47 x 13.2 by 30 x 13.2
BASIC_BOX = (0, 58, 250, 110)              # a Basic's "BASIC" tag overlapping the window's top-left corner
STRIKE_BOX = (462, 96, 712, 168)           # Rapid / Single Strike badge
FRAME_BOXES = ((0, 0, 734, 100), (0, 0, 62, 1024), (682, 0, 734, 1024), (0, 484, 734, 1024))

# per card: sprite, flip (face the card's way), mask recipe, optional overrides
#   mask: ("rembg", model, keep, close, cuts) | ("colour", fn) ; H: grid rows; aspect: crop w/h;
#   off: sprite offset (grid sprite px) or None = anchored on the card's Pokemon (centre x, feet)
CFG = {
    "swsh7-4": dict(sprite="jumpluff", flip=False, H=26, mask=dict(poly_only=True, poly=[(150, 250), (230, 170), (250, 110), (420, 110), (425, 180), (470, 260), (560, 280), (600, 330), (600, 420), (520, 455), (420, 445), (380, 475), (250, 465), (228, 380), (150, 345)])),
    "swsh7-34": dict(sprite="ludicolo", flip=False),
    "swsh7-16": dict(sprite="eldegoss", flip=False),
    "swsh7-50": dict(sprite="raichu", flip=True, off=(6, 1), mask=dict(poly=[(60, 300), (180, 190), (300, 130), (320, 80), (470, 80), (458, 260), (448, 400), (470, 480), (60, 480)])),
    "swsh7-19": dict(sprite="entei", flip=True, mask=dict(keep=3, close=4, poly=[(90, 200), (150, 130), (250, 100), (330, 100), (380, 130), (420, 110), (470, 180), (520, 250), (570, 280), (580, 380), (540, 440), (460, 450), (380, 480), (280, 470), (200, 420), (120, 380), (90, 300)])),
    "swsh7-20": dict(sprite="victini", flip=False, mask=dict(poly_only=True, poly=[(220, 160), (300, 80), (420, 80), (540, 110), (560, 200), (530, 290), (560, 330), (520, 400), (420, 420), (380, 455), (250, 425), (210, 330), (220, 250)])),
    "swsh7-63": dict(sprite="articuno-galar", flip=True),
    "swsh7-60": dict(sprite="regieleki", flip=False, mask=dict(poly_only=True, poly=[(170, 150), (250, 100), (360, 100), (430, 140), (475, 160), (475, 250), (420, 300), (420, 350), (380, 400), (420, 470), (330, 485), (300, 400), (280, 350), (210, 300), (170, 230)])),
    "swsh7-73": dict(sprite="florges", flip=False, mask=dict(poly_only=True, poly=[(150, 100), (440, 100), (470, 160), (470, 230), (420, 260), (380, 300), (360, 420), (300, 440), (240, 400), (250, 300), (200, 280), (160, 240), (140, 180)])),
    "swsh7-80": dict(sprite="marshadow", flip=False, mask=dict(poly=[(60, 100), (360, 100), (360, 470), (60, 470)])),
    "swsh7-82": dict(sprite="zapdos-galar", flip=False),
    "swsh7-93": dict(sprite="moltres-galar", flip=False, mask=dict(poly_only=True, poly=[(200, 100), (560, 100), (600, 250), (520, 420), (420, 480), (260, 480), (200, 350), (160, 200)])),
    "swsh7-103": dict(sprite="zoroark", flip=True, mask=dict(poly_only=True, poly=[(150, 120), (560, 110), (560, 250), (520, 300), (540, 470), (420, 480), (300, 470), (150, 470), (90, 400), (100, 300)])),
    "swsh7-112": dict(sprite="dialga", flip=False, mask=dict(poly_only=True, poly=[(70, 120), (160, 80), (330, 80), (450, 90), (520, 160), (500, 250), (460, 300), (440, 480), (200, 480), (150, 380), (80, 280)])),
    "swsh7-116": dict(sprite="kyurem", flip=True, mask=dict(poly_only=True, poly=[(60, 80), (180, 80), (300, 100), (420, 110), (560, 110), (640, 200), (620, 420), (520, 440), (400, 480), (160, 480), (100, 300), (60, 220)])),
    "swsh7-115": dict(sprite="hydreigon", flip=True, mask=dict(keep=3, close=4)),
    "swsh7-118": dict(sprite="zygarde", flip=False, mask=dict(poly_only=True, poly=[(170, 110), (560, 90), (620, 200), (600, 330), (560, 390), (440, 410), (300, 480), (150, 480), (110, 300), (160, 200)])),
    "swsh7-124": dict(sprite="regidrago", flip=False, mask=dict(poly_only=True, poly=[(100, 150), (240, 90), (380, 120), (470, 180), (560, 190), (620, 280), (630, 400), (560, 470), (300, 480), (200, 420), (100, 350)])),
    "swsh7-131": dict(sprite="slaking", flip=False, mask=dict(poly_only=True, poly=[(100, 110), (420, 100), (560, 180), (590, 300), (590, 440), (520, 480), (160, 480), (100, 400)])),
}


def card_json(cid):
    return json.load(open(E.CARDS / f"{cid}.json", encoding="utf-8"))


def text_boxes(cid):
    """the stage / Basic tag that overlaps the art window's top-left corner"""
    card = card_json(cid)
    boxes = (STAGE_BOX,) if "Basic" not in card["subtypes"] else (BASIC_BOX,)
    if {"Rapid Strike", "Single Strike", "Fusion Strike"} & set(card["subtypes"]):
        boxes += (STRIKE_BOX,)              # the strike badge over the window's top-right corner
    # everything outside the window (name, frame, info bar) is unknown too, so the textured fill never
    # mirrors card text / frame into a hole that reaches the window edge (these Pokemon often do)
    return boxes + FRAME_BOXES


# ---------------------------------------------------------------- masks
def make_mask(cid):
    import masks as M
    cfg = CFG[cid]
    sh = E.card_img(cid).shape[:2]
    win = (58, 98, 688, 488)
    mk = cfg.get("mask", {})
    if "poly" in mk and mk.get("poly_only"):
        m = M.poly(sh, mk["poly"])
    else:
        m = M.rembg(cid, mk.get("model", "isnet-general-use")) & M.rect(sh, *win)
        for c in mk.get("cut", ()):
            m &= ~M.rect(sh, *c)
        for p in mk.get("cutpoly", ()):
            m &= ~M.poly(sh, p)
        if "poly" in mk:
            m &= M.poly(sh, mk["poly"])
        if mk.get("close"):
            m = ndimage.binary_closing(m, iterations=mk["close"])
        if mk.get("open"):
            m = ndimage.binary_opening(m, iterations=mk["open"])
        m = M.largest(m, mk.get("keep", 1))
        for p in mk.get("addpoly", ()):
            m |= M.poly(sh, p)
        m = ndimage.binary_fill_holes(m)
    E.MASKS.mkdir(exist_ok=True)
    Image.fromarray((m * 255).astype(np.uint8)).save(E.MASKS / f"{cid}.png")
    rgb = E.card_img(cid)
    o = np.where(m[..., None], rgb, rgb * 0.25 + np.array([0, 0.3, 0]))
    return Image.fromarray(E.L.to8(o)).resize((367, 512))


def masks_sheet(ids):
    tiles = [make_mask(cid) for cid in ids]
    per = 7
    o = Image.new("RGB", (367 * per, 512 * ((len(tiles) + per - 1) // per)))
    for i, t in enumerate(tiles):
        o.paste(t, ((i % per) * 367, (i // per) * 512))
    o.save(E.WORK / "masks-holo.png")


# ---------------------------------------------------------------- geometry + build
def geometry(cid, spr):
    cfg = CFG[cid]
    a, b, c, d = WIN
    H = cfg.get("H", max(30, spr.h + 2))
    if round((c - a) / ((d - b) / H)) < spr.w + 4:     # a wide sprite: fit the width instead
        H = round((d - b) / ((c - a) / (spr.w + 4)))
    S = (d - b) / H
    Wfull = round((c - a) / S)
    W = cfg.get("W", Wfull if H <= 34 else max(spr.w + 6, min(Wfull, round(H * cfg.get("aspect", 1.35)))))
    W = min(W, Wfull)
    x0 = a
    if W < Wfull:                           # narrowed: centre the crop on the card's Pokemon
        ys, xs = np.nonzero(E.mask(cid))
        cx = (xs.min() + xs.max()) / 2 + cfg.get("crop_dx", 0)
        x0 = min(max(a, cx - W * S / 2), c - W * S)
    return x0, b, S, W, H


def builder(cid):
    import tiers as s3t
    cfg = CFG[cid]
    card = card_json(cid)
    spr = Sprite(cfg["sprite"], flip=cfg["flip"])
    x0, y0, S, W, H = geometry(cid, spr)
    rgb = window_rgb(cid, boxes=text_boxes(cid) + tuple(cfg.get("boxes", ())), grow=cfg.get("grow", 5),
                     tex_src=cfg.get("tex_src"))
    off = cfg.get("off")
    if off is None:
        off = E.anchor(cid, x0, y0, S, spr, cfg.get("dx", 0), cfg.get("dy", 0))
        off = (off[0], min(off[1], H - spr.h - 1))          # Salamence stands 1 row above the bottom
    FW, FH = 2 * W, 2 * H
    sparkles = cfg.get("sparkles", [(5, 5, 3), (FW - 6, 6, 2), (FW - 8, FH - 8, 3), (4, FH - 10, 2)])
    seed = int(E.num(cid))
    c = s3t.holo_scene(spr, cid, None, x0, y0, S, W, H, cid, "", off=off, rgb=rgb, ncol=12, foil=0.22,
                       bright=cfg.get("bright", 1.0), sat=cfg.get("sat", 1.0), sparkles=sparkles, seed=seed)
    scene = cfg.get("scene", "")
    return meta(c, card=cid, label=f"Rare Holo: {card['name']} {card['number']}/203{', ' + scene if scene else ''} (holo in the art box)",
                rarity="Rare Holo", finish="SWSH rare holo: rainbow foil bands + starlight inside the art box",
                variant="rare-holo", anim="holo", ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S)


def register(ids):
    """hand our builders to the shared build / anim code IN MEMORY (evcards.py is not edited)"""
    for cid in ids:
        evcards.BUILDERS[cid] = (lambda k: (lambda: builder(k)))(cid)


# ---------------------------------------------------------------- verify (verify.py's checks, on our ids)
def verify(ids):
    import sprites
    fails = 0

    def report(ok, msg):
        nonlocal fails
        fails += not ok
        print(("ok  " if ok else "BAD ") + msg)

    for cid in ids:
        c = evcards.BUILDERS[cid]()
        art = json.load(open(E.ART / f"{cid}.json", encoding="utf-8"))
        v = art["variants"][c.meta["variant"]]
        rows = v["rows"]
        A, B = c.off
        name = c.spr.name
        report(c.meta.get("sprite_recolour") is None, f"{cid:10s} no sprite recolour")
        for sh in (False, True):
            pal = {**art["palette"], **v.get("palette", {})}
            if sh:
                pal = {**pal, **art["shiny"], **v.get("shiny", {})}
            src = sprites.load(name, sh)
            w, h = len(src[0]), len(src)
            flip = v["flip"]
            tot = split = outline_bad = bad = 0
            want_cells = set()
            for j in range(h):
                for i in range(w):
                    want = src[j][i]
                    if want is None:
                        continue
                    tot += 1
                    ci = w - 1 - i if flip else i
                    X, Y = 2 * (A + ci), 2 * (B + j)
                    block = {rows[Y + b][X + a] for a in (0, 1) for b in (0, 1)}
                    want_cells |= {(X + a, Y + b) for a in (0, 1) for b in (0, 1)}
                    if len(block) != 1:
                        split += 1
                        continue
                    got = L.hexrgb(pal[block.pop()])
                    if want == (0, 0, 0):
                        outline_bad += got != (0, 0, 0)
                    else:
                        bad += got != want
            spr_cells = {p for p, (Lr, k) in c.cells.items() if Lr == "sprite"}
            shape_ok = spr_cells == want_cells and split == 0
            report(shape_ok and outline_bad == 0 and bad == 0,
                   f"{cid:10s} {name:14s} {'shiny ' if sh else 'normal'} flip={flip!s:5s} {tot} px: shape "
                   f"{'exact' if shape_ok else 'WRONG'}, {outline_bad} outline px off, {bad} colour errors")
        api = json.load(open(E.CARDS / "api" / f"{cid}.json", encoding="utf-8"))
        card = card_json(cid)
        diff = [k for k in card if k not in ("tier", "set", "images")
                and card[k] != api.get(k, card[k] if card[k] in ([], "") else None)]
        real = (api["set"]["id"] == "swsh7" and api["id"] == cid and card["tier"] == api["rarity"] == "Rare Holo"
                and card["tier"] == c.meta["rarity"])
        report(real and not diff, f"{cid:10s} card data: real swsh7 printing, API rarity '{api['rarity']}', tier "
                                  f"'{card['tier']}', fields verbatim{'' if not diff else ' EXCEPT ' + str(diff)}")
        for sh in (False, True):
            nm = cid + ("_shiny" if sh else "")
            f = E.DATA / "anim" / nm / f"{nm}.json"
            if not f.exists():
                report(False, f"{nm}: animation missing")
                continue
            m = json.load(open(f, encoding="utf-8"))
            last = m["frames"][m["final_frame"]]
            got = [[None if ch == "." else L.hexrgb(m["palette"][ch]) for ch in r] for r in last]
            report(got == c.rgb(sh) and len(m["frames"]) == 16,
                   f"{nm:16s} animation: {len(m['frames'])} frames, final frame == static art")
    print(f"{fails} failures")
    return fails


# ---------------------------------------------------------------- sheet
def sheet(ids, infos, name="sheets/holo.png", row_h=820, gap=28):
    font = "C:/Windows/Fonts/consola.ttf"

    def fit_h(im, h):
        return im.resize((round(im.width * h / im.height), h), Image.LANCZOS)

    rows = []
    for cid in ids:
        card = card_json(cid)
        info = infos[cid]
        real = fit_h(Image.open(E.ref_path(cid)).convert("RGB"), row_h)
        c0 = Image.open(E.OUT / f"{cid}-card.png").convert("RGB")
        stacked = fit_h(c0, row_h)
        k = stacked.height / c0.height
        art0 = Image.open(E.OUT / f"{cid}-art.png").convert("RGB")
        art = art0.resize((round(art0.width * k), round(art0.height * k)), Image.LANCZOS)
        label = (f"{cid}  {card['name']}  {card['number']}/{card['set']['printedTotal']}  tier: {card['tier']}"
                 f"  |  art {info['cols']}x{info['lines']}, card {info['cols']}x{info['card_lines']}\n{info['finish']}")
        rows.append((label, [real, art, stacked]))
    W = max(sum(p.width for p in ps) + gap * (len(ps) + 1) for _, ps in rows)
    H = len(rows) * (row_h + 90 + gap) + 70
    o = Image.new("RGB", (W, H), (24, 24, 28))
    d = ImageDraw.Draw(o)
    d.text((gap, 14), "Evolving Skies (swsh7) Rare Holo: real card | pokeshell art | art + text half",
           font=ImageFont.truetype(font, 36), fill=(235, 235, 235))
    y = 70
    f = ImageFont.truetype(font, 26)
    for label, ps in rows:
        d.text((gap, y + 8), label, font=f, fill=(200, 200, 200))
        x = gap
        for p in ps:
            o.paste(p, (x, y + 80))
            x += p.width + gap
        y += row_h + 90 + gap
    (E.DATA / name).parent.mkdir(exist_ok=True)
    o.save(E.DATA / name)
    print(name, o.size)


def _local(name):
    """evs/<name>.py by path (suite3 / style-lab have modules of the same names on sys.path)"""
    import importlib.util
    spec = importlib.util.spec_from_file_location("evs_" + name, E.HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    ids = [a for a in sys.argv[2:] if a in CFG] or IDS
    register(ids)
    if cmd == "masks":
        masks_sheet(ids)
        return
    infos_f = E.WORK / "sizes-holo.json"
    infos = json.load(open(infos_f)) if infos_f.exists() else {}
    if cmd in ("build", "all"):
        build = _local("build")
        for cid in ids:
            _, infos[cid] = build.render(cid)
        infos_f.write_text(json.dumps(infos, indent=1), encoding="utf-8")
    if cmd in ("anim", "all"):
        anim = _local("anim")
        anim.build(ids)
    if cmd in ("verify", "all"):
        if verify(ids):
            sys.exit(1)
    if cmd in ("sheet", "all"):
        sheet([i for i in IDS if i in infos], infos)


if __name__ == "__main__":
    main()
