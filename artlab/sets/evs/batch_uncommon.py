r"""Evolving Skies full set, group "uncommon": the 25 Uncommon Pokemon cards in plan.json, built exactly like the
approved Uncommon, Shelgon 108 (evcards2.shelgon):

  non-foil, sprite-scale scene: the card's own art window with the real Pokemon masked out (rembg,
  masks.windowed) and filled, sampled at SPRITE scale (one 2x2 block per sample), k-means to 12 muted colours
  (sat 0.84, bright 0.88), the light rim where dark scenery touches the outline. No animation (non-foil).

Size (fit to the card): Shelgon's 39 x 24 sprite px when the sprite fits (sprite + 3 rows), else the same
window at a finer S so the sprite fits: H = sprite h + 3, W keeps the window's 624:384 aspect.

  ..\..\..\.venv\Scripts\python batch_uncommon.py masks  [ids]   -> masks/<id>.png + work/unc/masks-*.png
  ..\..\..\.venv\Scripts\python batch_uncommon.py build  [ids]   -> art/, out/
  ..\..\..\.venv\Scripts\python batch_uncommon.py verify [ids]
  ..\..\..\.venv\Scripts\python batch_uncommon.py sheet          -> sheets/uncommon.png
  ..\..\..\.venv\Scripts\python batch_uncommon.py all
"""
import json
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

import evlib as E
from evlib import L, Card, Sprite
import evcards
import evcards2 as B2
from evcards import meta, place

GROUP = "uncommon"
PLAN = json.load(open(E.HERE / "plan.json", encoding="utf-8"))[GROUP]
IDS = [p["id"] for p in PLAN]
SPRITE = {p["id"]: p["sprite"] for p in PLAN}
UW = E.WORK / "unc"

# Shelgon's frame: window crop (62, 100) .. (686, 484) card px
X0, Y0, WPX, HPX = 62, 100, 624, 384
STAGE_CUT = (0, 60, 310, 135)
# the slanted right end of the "Evolves from" bar reaches x ~425 over the window's top edge; evcards2.STAGE_BOX
# stops at 312, so on these cards the bar's grey leaked into the scene as a stripe along the top
EVOLVE_BAR = (300, 90, 432, 127)            # stage icon + "Evolves from" bar (masks.shelgon's cut)

# per card: flip (face the way the card does), placement nudge (sprite px), mask options, scene tone
# mask: model / extra cuts (card px rects removed from the rembg cut) / keep (components) / close
CFG = {cid: {} for cid in IDS}
CFG.update({
    "swsh7-3": dict(hull=[(160, 280), (240, 180), (330, 160), (460, 165), (550, 210), (550, 300), (500, 340), (470, 420),
                          (380, 460), (340, 445), (300, 390), (260, 330), (160, 320)],
                    boxes=[(470, 100, 710, 168)]),                                   # the Rapid Strike badge
    "swsh7-12": dict(hull=[(195, 175), (280, 150), (480, 148), (585, 250), (570, 360), (550, 455), (500, 465),
                           (148, 468), (148, 430), (170, 390), (200, 370), (192, 250)]),
    "swsh7-47": dict(poly=[[(260, 125), (420, 100), (440, 110), (478, 145), (478, 300), (470, 350), (495, 395), (508, 450),
                            (500, 487), (248, 487), (248, 340), (245, 220), (258, 200)]]),     # both Eiscue (one stacked)
    "swsh7-25": dict(flip=True, poly=[[(135, 265), (200, 300), (205, 145), (250, 130), (290, 145), (325, 115), (380, 130),
                                       (430, 150), (535, 110), (648, 195), (625, 275), (560, 330), (545, 370), (455, 420),
                                       (360, 420), (335, 487), (240, 487), (250, 410), (260, 350), (150, 340)]]),
    "swsh7-27": dict(poly=[[(95, 130), (250, 120), (400, 150), (420, 270), (360, 300), (340, 380), (330, 487), (200, 487),
                            (170, 420), (95, 380)]]),                     # head + tentacle mass; ribbons stay as scene
    "swsh7-53": dict(poly=[[(305, 120), (395, 120), (400, 210), (305, 210)],                    # lure 1
                           [(390, 95), (480, 90), (500, 140), (545, 150), (550, 215), (390, 200)],  # antennae
                           [(505, 170), (595, 170), (595, 250), (505, 250)],                    # lure 2
                           [(335, 200), (515, 200), (560, 320), (645, 285), (632, 380), (605, 455), (530, 435),
                            (410, 430), (290, 420), (298, 375), (335, 330), (330, 240)]]),
    "swsh7-23": dict(flip=True, poly=[[(70, 185), (140, 165), (240, 185), (305, 150), (310, 100), (560, 100), (620, 160),
                                       (625, 300), (640, 380), (680, 420), (680, 487), (270, 487), (250, 440), (140, 420),
                                       (135, 370), (170, 300), (120, 300), (80, 230)]]),
    "swsh7-45": dict(poly=[[(220, 180), (340, 130), (475, 135), (595, 185), (580, 275), (635, 370), (630, 470), (500, 475),
                            (390, 455), (290, 470), (150, 475), (148, 395), (165, 340), (112, 225)]]),
    "swsh7-55": dict(flip=True, poly=[[(305, 140), (445, 145), (495, 260), (485, 375), (455, 415), (270, 410), (240, 330),
                                       (285, 270), (280, 190)], [(520, 360), (600, 360), (600, 430), (520, 430)]]),
    "swsh7-33": dict(poly=[[(130, 145), (515, 145), (505, 215), (440, 215), (440, 300), (480, 300), (530, 340), (560, 340),
                            (610, 395), (608, 415), (520, 410), (420, 405), (370, 380), (160, 440), (130, 330), (220, 320),
                            (220, 215), (135, 215)]]),
    "swsh7-69": dict(poly=[[(58, 185), (200, 185), (320, 225), (310, 150), (360, 145), (450, 100), (680, 100), (680, 175),
                            (600, 250), (590, 300), (545, 455), (505, 460), (425, 445), (360, 370), (325, 290), (250, 265),
                            (58, 200)]]),                              # the white blast stays as scene
    "swsh7-72": dict(flip=True, dx=7, boxes=[(470, 100, 710, 168)],
                     poly=[[(100, 160), (250, 140), (305, 190), (310, 300), (250, 380), (160, 405), (90, 370), (60, 300),
                            (60, 210)],                                 # Floette's red flower
                           [(290, 300), (330, 300), (470, 430), (465, 445), (300, 390)],                   # stem
                           [(320, 100), (480, 95), (510, 165), (545, 160), (548, 210), (510, 260), (470, 300), (400, 310),
                            (370, 380), (420, 450), (420, 487), (380, 487), (340, 420), (340, 300), (320, 200)]]),
    "swsh7-79": dict(poly=[[(178, 130), (250, 125), (330, 190), (365, 110), (420, 105), (460, 180), (510, 125), (522, 200),
                            (500, 300), (495, 350), (490, 410), (430, 440), (440, 470), (410, 475), (380, 420), (340, 420),
                            (290, 390), (230, 360), (185, 280)]]),
    "swsh7-85": dict(poly=[[(270, 160), (420, 130), (520, 130), (555, 220), (555, 300), (525, 390), (560, 420), (545, 480),
                            (440, 480), (420, 440), (370, 450), (320, 470), (260, 420), (255, 350), (210, 300), (170, 250),
                            (190, 200)]]),
    "swsh7-87": dict(poly=[[(290, 140), (390, 140), (500, 130), (510, 200), (520, 260), (580, 270), (575, 310), (540, 330),
                            (590, 360), (585, 440), (510, 440), (470, 400), (430, 420), (400, 410), (380, 360), (320, 380),
                            (300, 360), (200, 380), (115, 400), (130, 320), (190, 280), (210, 230), (290, 210)]]),
    "swsh7-89": dict(poly=[[(245, 145), (330, 130), (450, 150), (460, 190), (510, 190), (545, 240), (530, 290), (510, 330),
                            (495, 390), (440, 440), (380, 460), (300, 450), (280, 400), (265, 330), (240, 260),
                            (235, 200)]]),
    "swsh7-96": dict(poly=[[(170, 140), (360, 120), (380, 200), (460, 260), (455, 300), (420, 330), (470, 380), (525, 390),
                            (520, 460), (460, 460), (400, 487), (300, 487), (260, 440), (260, 380), (200, 320), (170, 250),
                            (175, 190)]]),
    "swsh7-99": dict(flip=True, poly=[[(290, 130), (330, 100), (420, 100), (440, 160), (435, 230), (470, 230), (470, 265),
                                       (430, 280), (440, 330), (455, 420), (435, 487), (270, 487), (275, 420), (240, 360),
                                       (245, 300), (260, 285), (245, 235), (285, 225), (280, 180)]]),
    "swsh7-114": dict(flip=True, poly=[[(110, 215), (250, 200), (240, 170), (300, 120), (320, 150), (405, 145), (455, 225),
                                        (455, 290), (420, 305), (400, 350), (430, 420), (420, 445), (320, 465), (265, 460),
                                        (250, 420), (200, 415), (105, 385), (150, 340), (210, 320), (240, 260), (110, 235)]]),
    "swsh7-130": dict(boxes=[(488, 100, 712, 170)],                                  # the Single Strike badge
                      poly=[[(60, 190), (110, 140), (210, 120), (320, 170), (400, 140), (470, 115), (500, 180), (560, 190),
                             (610, 150), (645, 170), (640, 210), (590, 250), (540, 260), (520, 300), (560, 340), (580, 370),
                             (610, 400), (560, 420), (520, 380), (500, 440), (470, 487), (360, 487), (320, 420), (300, 340),
                             (330, 290), (250, 300), (130, 300), (60, 260)]]),
    "swsh7-127": dict(flip=True, poly=[[(58, 120), (260, 120), (300, 180), (420, 165), (480, 190), (490, 260), (510, 300),
                                        (640, 320), (690, 300), (690, 440), (500, 440), (520, 487), (58, 487)]]),
    "swsh7-134": dict(poly=[[(300, 120), (380, 110), (470, 125), (450, 180), (440, 210), (470, 230), (575, 175), (560, 250),
                             (540, 300), (555, 370), (510, 380), (470, 340), (470, 400), (430, 425), (400, 380), (350, 350),
                             (300, 310), (245, 270), (250, 240), (290, 240), (270, 210), (265, 180)]]),
    "swsh7-137": dict(poly=[[(105, 150), (250, 160), (350, 190), (400, 240), (450, 240), (530, 270), (620, 330), (672, 375),
                             (640, 370), (600, 340), (530, 330), (470, 320), (460, 400), (440, 440), (420, 475), (380, 480),
                             (360, 440), (310, 440), (280, 400), (255, 370), (250, 300), (300, 245), (260, 200), (150, 170)]]),
    "swsh7-139": dict(flip=True, poly=[[(60, 280), (200, 260), (200, 200), (240, 195), (300, 260), (380, 240), (375, 120),
                                        (470, 100), (500, 190), (510, 240), (560, 270), (600, 320), (640, 420), (560, 455),
                                        (460, 445), (340, 425), (200, 405), (60, 385)]]),
    "swsh7-62": dict(hull=[(165, 125), (580, 125), (590, 330), (560, 450), (165, 450)]),
})


def cfg(cid, k, d=None):
    return CFG[cid].get(k, d)


# ------------------------------------------------------------------ masks
def make_mask(cid):
    import masks
    c = CFG[cid]
    if c.get("poly"):                     # hand polygons only (the segmenters take the whole painted window)
        m = np.zeros(E.card_img(cid).shape[:2], bool)
        for p in c["poly"]:
            m |= masks.poly(m.shape, p)
        E.MASKS.mkdir(exist_ok=True)
        Image.fromarray((m * 255).astype(np.uint8)).save(E.MASKS / f"{cid}.png")
        return m
    cid_, m = masks.windowed(cid, model=c.get("model", "isnet-general-use"), cut=(STAGE_CUT,) + tuple(c.get("cut", ())),
                             keep=c.get("keep", 1), close=c.get("close", 0))
    if c.get("hull"):
        m &= masks.poly(m.shape, c["hull"])
        m = ndimage.binary_fill_holes(masks.largest(m, c.get("keep", 1)))
    for p in c.get("add_poly", ()):                                   # hand polygons the segmenter missed
        m |= masks.poly(m.shape, p)
    for p in c.get("sub_poly", ()):
        m &= ~masks.poly(m.shape, p)
    E.MASKS.mkdir(exist_ok=True)
    Image.fromarray((m * 255).astype(np.uint8)).save(E.MASKS / f"{cid}.png")
    return m


def mask_sheet(ids):
    UW.mkdir(parents=True, exist_ok=True)
    tiles = []
    for cid in ids:
        rgb = E.card_img(cid)
        m = E.mask(cid)
        edge = m & ~ndimage.binary_erosion(m, iterations=3)
        o = np.where(m[..., None], rgb, rgb * 0.3)
        o[edge] = (1, 0, 0)
        t = Image.fromarray(L.to8(o)).crop((30, 50, 704, 500)).resize((449, 300))
        ImageDraw.Draw(t).text((4, 4), cid, fill=(255, 255, 0))
        tiles.append(t)
    for k in range(0, len(tiles), 9):
        part = tiles[k:k + 9]
        sheet = Image.new("RGB", (449 * 3, 300 * ((len(part) + 2) // 3)))
        for i, t in enumerate(part):
            sheet.paste(t, ((i % 3) * 449, (i // 3) * 300))
        sheet.save(UW / f"masks-{k // 9}.png")


def grid(cid):
    """the art window with a 50 card-px grid, to read hand polygons off"""
    im = Image.open(E.ref_path(cid)).convert("RGB").crop((0, 50, 734, 520))
    im = im.resize((im.width * 2, im.height * 2), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    for x in range(0, 734, 50):
        d.line([(2 * x, 0), (2 * x, im.height)], fill=(255, 0, 255) if x % 100 == 0 else (0, 255, 255), width=1)
        d.text((2 * x + 2, 2), str(x), fill=(255, 255, 0))
    for y in range(50, 520, 50):
        d.line([(0, 2 * (y - 50)), (im.width, 2 * (y - 50))], fill=(255, 0, 255) if y % 100 == 0 else (0, 255, 255), width=1)
        d.text((2, 2 * (y - 50) + 2), str(y), fill=(255, 255, 0))
    UW.mkdir(parents=True, exist_ok=True)
    im.save(UW / f"grid-{cid}.png")


def model_sheet(ids):
    """the three rembg cuts side by side per card (to pick a model)"""
    import masks
    UW.mkdir(parents=True, exist_ok=True)
    rows = []
    for cid in ids:
        rgb = E.card_img(cid)
        row = []
        for mdl in masks.MODELS:
            m = masks.rembg(cid, mdl)
            o = np.where(m[..., None], rgb, rgb * 0.3)
            t = Image.fromarray(L.to8(o)).crop((30, 50, 704, 500)).resize((449, 300))
            ImageDraw.Draw(t).text((4, 4), f"{cid} {mdl}", fill=(255, 255, 0))
            row.append(t)
        rows.append(row)
    sheet = Image.new("RGB", (449 * 3, 300 * len(rows)))
    for j, row in enumerate(rows):
        for i, t in enumerate(row):
            sheet.paste(t, (i * 449, j * 300))
    sheet.save(UW / "models.png")


# ------------------------------------------------------------------ builder (Shelgon's recipe)
def window_rgb(cid, boxes=(), grow=6):
    """evcards2.window_rgb (texture=False), with one local fix: the card's frame outside the art window is
    unknown DURING the fill, not only after it. Where a Pokemon touches the window edge (Ursaring, Pyroar,
    Tentacruel, ...) the shared version fills the hole from the silver/yellow frame; here only scene pixels
    feed the membrane. Identical to the shared one for a Pokemon clear of the edges (Shelgon)."""
    rgb = E.card_img(cid)
    m = ndimage.binary_dilation(E.mask(cid), iterations=grow)
    for (a, b, c, d) in boxes:
        m[max(0, b):d, max(0, a):c] = True
    a, b, c, d = B2.SWSH_WIN
    out = np.ones(m.shape, bool)
    out[b:d, a:c] = False
    return L.pushpull(rgb, ~m & ~out)


def dims(spr):
    H = max(24, spr.h + 3)
    S = HPX / H
    W = max(round(WPX / S), spr.w + 4)
    return W, H, S


def build_card(cid):
    card = json.load(open(E.CARDS / f"{cid}.json", encoding="utf-8"))
    spr = Sprite(SPRITE[cid], flip=cfg(cid, "flip", False))
    W, H, S = dims(spr)
    bar = (EVOLVE_BAR,) if card.get("evolvesFrom") else ()
    rgb = window_rgb(cid, boxes=(B2.STAGE_BOX,) + bar + tuple(cfg(cid, "boxes", ())))
    c = Card(W, H)
    if cfg(cid, "off"):
        place(c, spr, cid, X0, Y0, S, off=cfg(cid, "off"), margin=1)
    else:
        A, B = E.anchor(cid, X0, Y0, S, spr, cfg(cid, "dx", 0), cfg(cid, "dy", 0))
        A = max(1, min(W - spr.w - 1, A))
        B = max(1, min(H - spr.h - 1, B))
        c.put_sprite(spr, A, B)
    B2.matte(c, rgb, X0, Y0, S, 12, sat=cfg(cid, "sat", 0.84), bright=cfg(cid, "bright", 0.88))
    return meta(c, card=cid, label=f"Uncommon: {card['name']} {card['number']}/203 (non-foil)", rarity="Uncommon",
                finish="non-foil: sprite-scale scene, 12 colours", variant="uncommon", anim=None,
                ref=(cid, X0, Y0, X0 + W * S, Y0 + H * S), S=S)


BUILDERS = {cid: (lambda cid=cid: build_card(cid)) for cid in IDS}


def build(ids):
    import importlib.util
    spec = importlib.util.spec_from_file_location("evs_build", E.HERE / "build.py")   # (a pip 'build' shadows it)
    BLD = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(BLD)
    evcards.BUILDERS.update({cid: BUILDERS[cid] for cid in ids})     # in this process only (shared file untouched)
    f = UW / "sizes.json"
    infos = json.load(open(f, encoding="utf-8")) if f.exists() else {}
    for cid in ids:
        _, infos[cid] = BLD.render(cid)
    UW.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(infos, indent=1), encoding="utf-8")


# ------------------------------------------------------------------ verify (verify.py's checks, on our ids)
def verify(ids):
    import sprites
    fails = 0

    def report(ok, msg):
        nonlocal fails
        fails += not ok
        print(("ok  " if ok else "BAD ") + msg)

    for cid in ids:
        c = BUILDERS[cid]()
        art = json.load(open(E.ART / f"{cid}.json", encoding="utf-8"))
        v = art["variants"][c.meta["variant"]]
        rows = v["rows"]
        A, B = c.off
        name = c.spr.name
        report(not c.meta.get("sprite_recolour"), f"{cid:10s} no sprite recolour at Uncommon")
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
                        continue
                    bad += got != want
            spr_cells = {p for p, (Lr, k) in c.cells.items() if Lr == "sprite"}
            shape_ok = spr_cells == want_cells and split == 0
            report(shape_ok and outline_bad == 0 and bad == 0,
                   f"{cid:10s} {name:11s} {'shiny ' if sh else 'normal'} flip={flip!s:5s} {tot} px: shape "
                   f"{'exact' if shape_ok else 'WRONG'}, {outline_bad} outline px off, {bad} colour errors (exact vendor colours)")
        api = json.load(open(E.CARDS / "api" / f"{cid}.json", encoding="utf-8"))
        card = json.load(open(E.CARDS / f"{cid}.json", encoding="utf-8"))
        diff = [k for k in card if k not in ("tier", "set", "images")
                and card[k] != api.get(k, card[k] if card[k] in ([], "") else None)]
        real = api["set"]["id"] == "swsh7" and api["id"] == cid and card["tier"] == api["rarity"] == c.meta["rarity"]
        report(real and not diff, f"{cid:10s} card data: real swsh7 printing, API rarity '{api['rarity']}', tier "
                                  f"'{card['tier']}', fields verbatim{'' if not diff else ' EXCEPT ' + str(diff)}")
        # non-foil: no animation; the art has a background (uncommons are not commons) of <= 12 colours
        spr_keys = set(c.pals["sprite"])
        ncol = len({ch for r in rows for ch in r if ch != "." and ch not in spr_keys})
        report(c.meta["anim"] is None and 0 < ncol <= 12, f"{cid:10s} non-foil, no animation, {ncol} bg colours")
    print(f"{len(ids)} cards, {fails} failures")
    return fails


# ------------------------------------------------------------------ sheet
FONT = "C:/Windows/Fonts/consola.ttf"


def fit_h(im, h):
    return im.resize((round(im.width * h / im.height), h), Image.LANCZOS)


def sheet(ids, path=None, row_h=600):
    GAP = 24
    infos = json.load(open(UW / "sizes.json", encoding="utf-8"))
    rows = []
    for cid in ids:
        card = json.load(open(E.CARDS / f"{cid}.json", encoding="utf-8"))
        info = infos[cid]
        real = fit_h(Image.open(E.ref_path(cid)).convert("RGB"), row_h)
        full = Image.open(E.OUT / f"{cid}-card.png").convert("RGB")
        stacked = fit_h(full, row_h)
        k = stacked.height / full.height
        art0 = Image.open(E.OUT / f"{cid}-art.png").convert("RGB")
        art = art0.resize((round(art0.width * k), round(art0.height * k)), Image.LANCZOS)
        label = (f"{cid}  {card['name']}  {card['number']}/{card['set']['printedTotal']}  tier: {card['tier']}  |  "
                 f"art {info['cols']}x{info['lines']}, card {info['cols']}x{info['card_lines']}, flip={info['flip']}  |  {info['finish']}")
        rows.append((label, [real, art, stacked]))
    Wd = max(sum(p.width for p in ps) + GAP * (len(ps) + 1) for _, ps in rows)
    Ht = sum(row_h + 50 + GAP for _ in rows) + 60
    o = Image.new("RGB", (Wd, Ht), (24, 24, 28))
    d = ImageDraw.Draw(o)
    d.text((GAP, 12), "Evolving Skies (swsh7) Uncommons: real card | pokeshell art | art + text half",
           font=ImageFont.truetype(FONT, 30), fill=(235, 235, 235))
    y = 60
    f = ImageFont.truetype(FONT, 20)
    for label, ps in rows:
        d.text((GAP, y + 6), label, font=f, fill=(200, 200, 200))
        x = GAP
        for p in ps:
            o.paste(p, (x, y + 40))
            x += p.width + GAP
        y += row_h + 50 + GAP
    path = path or (E.DATA / "sheets" / f"{GROUP}.png")
    path.parent.mkdir(exist_ok=True)
    o.save(path)
    print(path, o.size)


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    ids = [a for a in sys.argv[2:] if a in IDS] or IDS
    if cmd in ("masks", "all"):
        for cid in ids:
            make_mask(cid)
        mask_sheet(ids)
    if cmd in ("build", "all"):
        build(ids)
    if cmd == "grid":
        for cid in ids:
            grid(cid)
    if cmd == "models":
        model_sheet(ids)
    if cmd == "peek":                       # review sheet of a few ids
        sheet(ids, UW / "peek.png", row_h=520)
    if cmd in ("verify", "all"):
        if verify(ids):
            sys.exit(1)
    if cmd in ("sheet", "all"):
        sheet(IDS)


if __name__ == "__main__":
    main()
