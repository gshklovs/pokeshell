r"""Evolving Skies full set, group "rare": the 18 Rare (non-foil) Pokemon cards in plan.json["rare"], built
exactly like the approved Rare, Altaria 106 (evcards2.altaria): the vendor colorscripts sprite (flip only)
over the card's own scene -- the real Pokemon masked out (rembg, windowed like masks.py) and filled with the
scene's own texture -- sampled at GRID scale (2x finer than the sprite) and k-means'd to 16 colours. Non-foil:
no animation.

  ..\..\..\.venv\Scripts\python batch_rare.py masks            masks/<id>.png + work/rare-masks.png
  ..\..\..\.venv\Scripts\python batch_rare.py build [ids]      art/ + out/ (+ work/rare-sizes.json)
  ..\..\..\.venv\Scripts\python batch_rare.py verify           sprite / card-data checks (verify.py's)
  ..\..\..\.venv\Scripts\python batch_rare.py sheet            sheets/rare.png
  ..\..\..\.venv\Scripts\python batch_rare.py all
"""
import json
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

import evcards
import evcards2 as B2
import evlib as E
import masks as M
from evcards import meta, place
from evlib import L, Card, Sprite

PLAN = json.load(open(E.HERE / "plan.json", encoding="utf-8"))["rare"]
IDS = [p["id"] for p in PLAN]
SPRITE = {p["id"]: p["sprite"] for p in PLAN}
WIN = (66, 106, 680, 476)          # evcards2.SWSH_WIN
# local fix: evcards2.window_rgb only membranes the frame AFTER the fill, so where a Pokemon touches the window
# edge the card's coloured frame bleeds into the painted-out hole. Painting the frame out as boxes (boxes are
# not dilated) keeps the fill to the window's own scene.
FRAME = ((0, 0, 734, WIN[1] + 6), (0, 0, WIN[0] + 5, 1024), (WIN[2] - 5, 0, 734, 1024), (0, WIN[3] - 5, 734, 1024))   # + the window's own edge line
STAGE_CUT = (0, 60, 310, 135)      # stage icon / "Evolves from" bar (masks.py cut)
STAGE_ICON = (0, 58, 125, 175)     # the pre-evolution icon + its frame hang lower than evcards2.STAGE_BOX
STAGE_BAR = (0, 58, 345, 142)      # the "Evolves from" bar's slanted end runs past evcards2.STAGE_BOX

# per card (all optional): flip, mask = dict(model, cut, keep, close, extra polys), frame = (x0, y0, S, W, H),
# off = sprite offset, dx/dy nudges, grow, tex_src, sat, bright, boxes
LOGO = (440, 95, 700, 185)        # the "Single Strike" / "Rapid Strike" logo at the window's top right
BASIC = dict(stage=False)          # Basic cards have no stage icon / "Evolves from" bar over the window
CONF = {
    "swsh7-6": dict(flip=True, **BASIC, mask=dict(model=None, hull=[
        [(60, 110), (300, 120), (420, 200), (480, 150), (530, 110), (590, 120), (600, 190), (560, 210), (470, 250),
         (520, 330), (640, 380), (640, 430), (560, 440), (400, 360), (300, 360), (180, 340), (60, 330)]])),
    "swsh7-1": dict(**BASIC, boxes=(LOGO,), mask=dict(model="u2net", close=4, hull=[
        [(170, 250), (220, 160), (260, 100), (460, 100), (470, 170), (560, 240), (560, 400), (500, 480), (200, 480),
         (160, 380)]])),
    "swsh7-10": dict(flip=True, mask=dict(model=None, hull=[
        [(300, 110), (450, 110), (480, 190), (600, 190), (610, 230), (560, 300), (520, 320), (580, 440), (560, 480),
         (360, 480), (340, 340), (300, 300), (290, 200)]])),
    "swsh7-36": dict(mask=dict(model=None, hull=[
        [(105, 290), (170, 250), (200, 170), (300, 130), (320, 100), (430, 100), (430, 160), (480, 230), (610, 290),
         (610, 345), (480, 335), (420, 400), (340, 475), (270, 475), (250, 420), (180, 350), (105, 330)]])),
    "swsh7-46": dict(flip=True, **BASIC, boxes=(LOGO,), mask=dict(model=None, hull=[
        [(230, 190), (330, 180), (420, 170), (500, 170), (560, 220), (575, 330), (540, 420), (470, 450), (390, 440),
         (330, 380), (270, 320), (220, 270)]])),
    "swsh7-38": dict(flip=True, boxes=(LOGO,), mask=dict(model=None, hull=[
        [(130, 170), (330, 140), (440, 150), (688, 165), (688, 265), (560, 265), (570, 330), (560, 470), (160, 470),
         (120, 380), (130, 260)]])),
    "swsh7-56": dict(mask=dict(model=None, hull=[
        [(130, 190), (200, 190), (210, 120), (260, 120), (270, 190), (310, 230), (380, 230), (420, 290), (480, 260),
         (490, 210), (560, 200), (620, 210), (620, 300), (605, 400), (560, 420), (470, 470), (390, 470), (330, 440),
         (240, 440), (200, 380), (250, 330), (200, 300), (130, 270)]])),
    "swsh7-77": dict(mask=dict(model=None, hull=[
        [(150, 250), (250, 130), (330, 110), (420, 120), (480, 150), (560, 160), (688, 170), (688, 340), (620, 420),
         (560, 440), (560, 480), (330, 480), (330, 380), (260, 300), (160, 320)]])),
    "swsh7-88": dict(mask=dict(model=None, hull=[
        [(190, 480), (230, 380), (300, 300), (340, 230), (380, 130), (420, 100), (690, 100), (690, 480)]])),
    "swsh7-90": dict(mask=dict(model="isnet-general-use", close=4, hull=[
        [(80, 190), (160, 150), (250, 120), (290, 100), (470, 100), (570, 120), (610, 190), (600, 260), (540, 250),
         (510, 300), (480, 400), (510, 440), (460, 470), (300, 470), (250, 400), (230, 260), (190, 270), (90, 280)]])),
    "swsh7-97": dict(mask=dict(model=None, hull=[
        [(180, 110), (470, 100), (520, 120), (640, 150), (640, 260), (560, 300), (560, 380), (460, 400), (440, 440),
         (360, 440), (300, 380), (220, 380), (180, 300)],
        [(60, 380), (200, 360), (300, 380), (360, 440), (300, 480), (60, 480)]])),
    "swsh7-105": dict(flip=True, mask=dict(model=None, hull=[
        [(360, 140), (420, 110), (480, 120), (530, 160), (500, 240), (470, 330), (450, 470), (100, 470), (100, 380),
         (150, 300), (250, 260), (320, 200), (370, 180)]])),
    "swsh7-119": dict(**BASIC, mask=dict(model=None, hull=[
        [(130, 180), (230, 150), (300, 110), (400, 90), (520, 70), (560, 110), (560, 280), (480, 320), (380, 300),
         (330, 230), (280, 280), (250, 340), (160, 340), (120, 280)]])),
    "swsh7-120": dict(mask=dict(model="isnet-general-use", close=4, hull=[
        [(150, 100), (380, 100), (420, 170), (520, 160), (690, 190), (690, 400), (520, 400), (420, 400), (300, 400),
         (250, 330), (200, 280), (150, 260)]])),
    "swsh7-121": dict(flip=True, mask=dict(model="u2net", close=4, hull=[
        [(60, 200), (100, 130), (200, 105), (330, 110), (400, 150), (450, 190), (520, 210), (555, 260), (555, 340),
         (510, 395), (440, 390), (390, 440), (330, 470), (100, 470), (60, 400)]])),
    "swsh7-128": dict(**BASIC, mask=dict(model="isnet-general-use", close=4, hull=[
        [(80, 110), (300, 110), (360, 200), (430, 180), (470, 250), (560, 330), (580, 420), (500, 480), (80, 480)]])),
    "swsh7-135": dict(mask=dict(model="isnet-general-use", close=6, hull=[
        [(90, 400), (120, 300), (180, 260), (240, 230), (250, 160), (290, 140), (340, 170), (370, 230), (420, 240),
         (500, 280), (590, 350), (560, 420), (480, 450), (340, 480), (260, 480), (150, 450), (80, 440)]])),
    "swsh7-140": dict(mask=dict(model=None, hull=[
        [(60, 200), (150, 210), (250, 220), (360, 210), (390, 170), (470, 170), (520, 120), (620, 110), (690, 130),
         (690, 380), (620, 400), (600, 480), (200, 480), (160, 420), (60, 380)]])),
}


# ---------------------------------------------------------------- masks
def make_mask(cid):
    """hand hull polygon(s) (card px, read off a 25 px grid of the scan), intersected with the rembg model that
    caught this Pokemon best when one did (model=None: the hull alone)"""
    cf = CONF[cid].get("mask", {})
    sh = E.card_img(cid).shape[:2]
    hull = np.zeros(sh, bool)
    for p in cf.get("hull", ()):
        hull |= M.poly(sh, p)
    model = cf.get("model")
    m = (M.rembg(cid, model) & hull) if model else hull
    m &= M.rect(sh, 58, 98, 688, 488)
    if CONF[cid].get("stage", True):
        m &= ~M.rect(sh, *STAGE_CUT)
    if cf.get("close"):
        m = ndimage.binary_closing(m, iterations=cf["close"])
    m = ndimage.binary_fill_holes(M.largest(m, cf.get("keep", 3)))
    return m


def masks_main(ids):
    E.MASKS.mkdir(exist_ok=True)
    tiles = []
    for cid in ids:
        m = make_mask(cid)
        Image.fromarray((m * 255).astype(np.uint8)).save(E.MASKS / f"{cid}.png")
        rgb = E.card_img(cid)
        o = np.where(m[..., None], rgb, rgb * 0.25 + np.array([0, 0.3, 0]))
        tiles.append(Image.fromarray(L.to8(o)).resize((367, 512)))
        ys, xs = np.nonzero(m)
        print(cid, "bbox", xs.min(), ys.min(), xs.max(), ys.max(), f"{m.mean():.2f}")
    per = 6
    sheet = Image.new("RGB", (367 * per, 512 * ((len(tiles) + per - 1) // per)))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % per) * 367, (i // per) * 512))
    sheet.save(E.WORK / "rare-masks.png")


# ---------------------------------------------------------------- framing
def auto_frame(cid, spr):
    """Altaria's framing rule: a crop of about the art window (Altaria: x0 64, y0 94, 616 x 402 card px) at a
    scale that fits the sprite with a little room; small sprites are capped at S = 20 (Froslass's scale) so the
    scene still reads"""
    S = min(616 / (spr.w + 4), 402 / (spr.h + 1), 20.0)
    W = round(616 / S)
    S = 616 / W
    H = round(402 / S)
    return 64, 94 + (402 - H * S) / 2, S, W, H


def tex_rect(cid, grow):
    """a scene rectangle clear of the Pokemon (and the stage box) to borrow texture from"""
    m = ndimage.binary_dilation(E.mask(cid), iterations=grow + 6)
    for a, b, c, d in ((STAGE_BAR, STAGE_ICON) if CONF[cid].get("stage", True) else ()) + tuple(CONF[cid].get("boxes", ())):
        m[b:d, a:c] = True
    best, area = None, 0
    for w, h in ((260, 170), (200, 140), (160, 120), (120, 100), (90, 80), (70, 60)):
        for y in range(WIN[1] + 4, WIN[3] - h - 3, 10):
            for x in range(WIN[0] + 4, WIN[2] - w - 3, 10):
                if not m[y:y + h, x:x + w].any():
                    return (x, y, x + w, y + h)
    return best


def build_card(cid):
    cf = CONF[cid]
    spr = Sprite(SPRITE[cid], flip=cf.get("flip", False))
    x0, y0, S, W, H = cf.get("frame") or auto_frame(cid, spr)
    grow = cf.get("grow", 8)
    ts = cf.get("tex_src", "auto")
    if ts == "auto":
        ts = tex_rect(cid, grow)
    stage = (STAGE_BAR, STAGE_ICON) if cf.get("stage", True) else ()
    rgb = B2.window_rgb(cid, boxes=stage + tuple(cf.get("boxes", ())) + FRAME, grow=grow, tex_src=ts)
    c = Card(W, H)
    off = cf.get("off")
    if off is None:
        A, B = E.anchor(cid, x0, y0, S, spr, cf.get("dx", 0), cf.get("dy", 0))
        off = (A, B)
    place(c, spr, cid, x0, y0, S, off=off)
    B2.matte(c, rgb, x0, y0, S, 16, sat=cf.get("sat", 0.95), bright=cf.get("bright", 0.95), scale=1)
    card = json.load(open(E.CARDS / f"{cid}.json", encoding="utf-8"))
    return meta(c, card=cid, label=f"Rare: {card['name']} {int(card['number']):03d}/203 (non-foil)", rarity="Rare",
                finish="non-foil: grid-scale scene, 16 colours", variant="rare", anim=None,
                ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S)


def register():
    for cid in IDS:
        evcards.BUILDERS[cid] = (lambda cid=cid: build_card(cid))


# ---------------------------------------------------------------- build
def build_main(ids):
    import importlib.util
    spec = importlib.util.spec_from_file_location("evs_build", E.HERE / "build.py")   # not suite3's build.py
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)
    register()
    sizes_f = E.WORK / "rare-sizes.json"
    sizes = json.load(open(sizes_f, encoding="utf-8")) if sizes_f.exists() else {}
    for cid in ids:
        _, info = build.render(cid)
        sizes[cid] = info
    sizes_f.write_text(json.dumps(sizes, indent=1), encoding="utf-8")


# ---------------------------------------------------------------- verify (verify.py's checks, on our ids)
def verify_main(ids):
    import sprites
    register()
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
        report(c.meta.get("sprite_recolour") is None and c.meta["anim"] is None,
               f"{cid:10s} no sprite recolour, no animation (non-foil Rare)")
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
                    for a in (0, 1):
                        for b in (0, 1):
                            want_cells.add((X + a, Y + b))
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
                   f"{cid:10s} {name:10s} {'shiny ' if sh else 'normal'} flip={flip!s:5s} {tot} px: shape "
                   f"{'exact' if shape_ok else 'WRONG'}, {outline_bad} outline px off, {bad} colour errors (exact vendor colours)")
        api = json.load(open(E.CARDS / "api" / f"{cid}.json", encoding="utf-8"))
        card = json.load(open(E.CARDS / f"{cid}.json", encoding="utf-8"))
        diff = [k for k in card if k not in ("tier", "set", "images")
                and card[k] != api.get(k, card[k] if card[k] in ([], "") else None)]
        real = api["set"]["id"] == "swsh7" and api["id"] == cid and card["tier"] == api["rarity"] == "Rare" \
            and card["tier"] == c.meta["rarity"]
        report(real and not diff, f"{cid:10s} card data: real swsh7 printing, API rarity '{api['rarity']}', tier "
                                  f"'{card['tier']}', fields verbatim{'' if not diff else ' EXCEPT ' + str(diff)}")
        bgc = len({ch for r in rows for ch in r if ch != "." and ch not in c.pals["sprite"]})
        report(bgc <= 16, f"{cid:10s} scene colours {bgc} <= 16")
    print(f"{fails} failures")
    return fails


# ---------------------------------------------------------------- sheet
def sheet_main(ids):
    from PIL import ImageDraw, ImageFont
    import sheet as SH
    sizes = json.load(open(E.WORK / "rare-sizes.json", encoding="utf-8"))
    ROW_H, GAP = SH.ROW_H, SH.GAP
    rows = []
    for cid in ids:
        card = json.load(open(E.CARDS / f"{cid}.json", encoding="utf-8"))
        info = sizes[cid]
        real = SH.fit_h(Image.open(E.ref_path(cid)).convert("RGB"), ROW_H)
        st0 = Image.open(E.OUT / f"{cid}-card.png").convert("RGB")
        stacked = SH.fit_h(st0, ROW_H)
        art0 = Image.open(E.OUT / f"{cid}-art.png").convert("RGB")
        k = stacked.height / st0.height
        art = art0.resize((round(art0.width * k), round(art0.height * k)), Image.LANCZOS)
        label = (f"{cid}  {card['name']}  {card['number']}/{card['set']['printedTotal']}  tier: {card['tier']}"
                 f"  |  art {info['cols']}x{info['lines']}, card {info['cols']}x{info['card_lines']}  |  {info['finish']}")
        rows.append((label, [real, art, stacked]))
    W = max(sum(p.width for p in ps) + GAP * (len(ps) + 1) for _, ps in rows)
    H = sum(ROW_H + 60 + GAP for _ in rows) + 70
    o = Image.new("RGB", (W, H), (24, 24, 28))
    d = ImageDraw.Draw(o)
    d.text((GAP, 14), "Evolving Skies (swsh7) -- group 'rare': real card | pokeshell art | art + text half",
           font=ImageFont.truetype(SH.FONT, 36), fill=(235, 235, 235))
    y = 70
    f = ImageFont.truetype(SH.FONT, 26)
    for label, ps in rows:
        d.text((GAP, y + 8), label, font=f, fill=(200, 200, 200))
        x = GAP
        for p in ps:
            o.paste(p, (x, y + 50))
            x += p.width + GAP
        y += ROW_H + 60 + GAP
    (E.DATA / "sheets").mkdir(exist_ok=True)
    o.save(E.DATA / "sheets" / "rare.png")
    print("sheets/rare.png", o.size)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    ids = [a for a in sys.argv[2:] if a in IDS] or IDS
    if cmd in ("masks", "all"):
        masks_main(ids)
    if cmd in ("build", "all"):
        build_main(ids)
    if cmd in ("sheet", "all"):
        sheet_main(ids)
    if cmd in ("verify", "all"):
        sys.exit(1 if verify_main(ids) else 0)
