r"""30th Celebration (me55) full set, group "illustration_rare": the 15 Illustration Rares, built exactly as the
approved Lapras 131 (p30cards.lapras): evs Rare Ultra full-art pipeline -- the full painting (header, stage icon,
30th stamp and text half painted out), the IR's lighter, wider-spaced etch that follows the painting's shading
(period 4, amplitude 0.065, f + 9 * lum), a soft glow with no rays; anim "etch".

Vividness (user note on painted alt-arts): the painting must stay vivid, not washed out by the texture. So the
tone keeps a little extra saturation, the warm glow / vignette are lighter than Lapras's pastel card needed, and
the etch is Lapras's (a subtle lift on 1 px contour lines).

  ..\..\..\.venv\Scripts\python batch_illustration_rare.py [masks|build|anim|verify|sheet|all] [me55-129 ...]
"""
import json
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

import p30lib as P
from p30lib import E, L, Card, Sprite
import p30cards
import p30masks as PM
import p30build
import p30anim
import p30verify
import p30sheet
from evcards import W_LUM, meta, place, fingerprint

GROUP = "illustration_rare"
poly, rect, largest, rembg, hsv = PM.poly, PM.rect, PM.largest, PM.rembg, PM.hsv


def line(sh, p0, p1, w):
    """a thick straight segment (a string / thin limb) as a polygon"""
    (x0, y0), (x1, y1) = p0, p1
    d = np.hypot(x1 - x0, y1 - y0)
    nx, ny = -(y1 - y0) / d * w / 2, (x1 - x0) / d * w / 2
    return poly(sh, [(x0 + nx, y0 + ny), (x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)])


def band(h, lo, hi):
    return (h >= lo) & (h < hi) if lo < hi else (h >= lo) | (h < hi)


# ============================================================ masks (white = the card's own Pokemon; cameos stay)
def m129(cid):
    """the three heads + the neck coming in from the top left (the long palm trunks are scenery)"""
    rgb, h, s, v = hsv(cid)
    sh = rgb.shape[:2]
    heads = poly(sh, [(365, 110), (395, 95), (440, 95), (470, 108), (500, 115), (530, 150), (537, 210), (508, 240),
                      (497, 262), (470, 282), (430, 287), (390, 267), (360, 272), (310, 267), (280, 252), (270, 212),
                      (290, 190), (320, 170), (340, 140)])
    neck = poly(sh, [(200, 62), (300, 58), (368, 108), (342, 150), (312, 180), (272, 172), (240, 122), (200, 96)])
    return heads | neck


def m130(cid):
    """the yellow body, neck and head (the flame wings read as the scene's fire)"""
    rgb, h, s, v = hsv(cid)
    sh = rgb.shape[:2]
    hull = poly(sh, [(265, 255), (330, 238), (470, 212), (560, 222), (622, 242), (618, 302), (560, 322), (532, 380),
                     (522, 442), (470, 452), (400, 442), (330, 422), (278, 382), (258, 320)])
    yellow = band(h, 36, 64) & (s > 0.4) & (v > 0.7)
    head = poly(sh, [(478, 228), (560, 218), (618, 242), (602, 262), (560, 302), (498, 302)])
    m = ndimage.binary_closing(hull & yellow, iterations=6) | head
    return ndimage.binary_fill_holes(largest(m))


def m132(cid):
    """blue wings / body / crest inside Articuno's hull, plus the grey claws"""
    rgb, h, s, v = hsv(cid)
    sh = rgb.shape[:2]
    hull = poly(sh, [(20, 95), (140, 115), (250, 165), (330, 135), (385, 115), (450, 195), (550, 105), (605, 115),
                     (605, 300), (560, 382), (505, 422), (485, 492), (230, 495), (200, 450), (250, 382), (150, 322),
                     (45, 282), (20, 200)])
    blue = band(h, 185, 235) & (s > 0.4) & (v > 0.3)
    m = ndimage.binary_opening(hull & blue, iterations=2)
    m = ndimage.binary_closing(m, iterations=8)
    claws = poly(sh, [(228, 445), (300, 438), (370, 448), (500, 455), (500, 495), (228, 495)])
    return ndimage.binary_fill_holes(largest(m) | claws)


def m133(cid):
    """yellow plumage, orange beak / legs, tan tufts inside Zapdos's hull"""
    rgb, h, s, v = hsv(cid)
    sh = rgb.shape[:2]
    hull = poly(sh, [(20, 250), (150, 238), (250, 118), (330, 58), (420, 68), (560, 108), (640, 200), (630, 332),
                     (560, 380), (560, 495), (250, 495), (150, 442), (60, 402)])
    yellow = band(h, 36, 66) & (s > 0.45) & (v > 0.65)
    orange = band(h, 5, 36) & (s > 0.45) & (v > 0.45)
    tan = band(h, 20, 50) & (s > 0.12) & (s < 0.45) & (v > 0.45) & poly(sh, [(360, 330), (460, 330), (470, 440), (360, 440)])
    m = hull & (yellow | orange | tan)
    m = ndimage.binary_opening(m, iterations=2)
    m = ndimage.binary_closing(m, iterations=8)
    return ndimage.binary_fill_holes(largest(m, 2))


def m134(cid):
    sh = E.card_img(cid).shape[:2]
    return poly(sh, [(158, 128), (215, 113), (262, 133), (272, 193), (330, 158), (372, 183), (398, 250), (422, 290),
                     (462, 378), (507, 378), (527, 420), (507, 477), (450, 482), (410, 462), (382, 502), (367, 552),
                     (208, 552), (190, 472), (122, 432), (118, 402), (188, 432), (198, 380), (198, 300), (183, 230),
                     (158, 190)])


def m135(cid):
    sh = E.card_img(cid).shape[:2]
    return poly(sh, [(252, 342), (268, 308), (300, 293), (335, 288), (350, 272), (382, 262), (408, 288), (423, 330),
                     (418, 372), (392, 403), (330, 413), (298, 398), (258, 382), (247, 360)])


def m136(cid):
    """the balloon body + tuft, both strings, both yellow hands"""
    sh = E.card_img(cid).shape[:2]
    body = poly(sh, [(228, 120), (258, 88), (298, 78), (308, 57), (362, 52), (392, 73), (402, 93), (432, 113),
                     (452, 170), (447, 242), (422, 287), (392, 322), (372, 348), (330, 353), (288, 322), (248, 292),
                     (228, 242), (220, 180)])
    strings = line(sh, (318, 300), (326, 492), 10) | line(sh, (382, 300), (474, 476), 10)
    hands = poly(sh, [(293, 488), (335, 478), (357, 510), (347, 547), (298, 547)]) | \
        poly(sh, [(453, 468), (492, 466), (507, 500), (497, 532), (458, 532)])
    return body | strings | hands


def m137(cid):
    """isnet-general-use has the arms and the lamp; limited to Chandelure's hull, lamp and flame by hand"""
    sh = E.card_img(cid).shape[:2]
    hull = poly(sh, [(108, 118), (200, 98), (290, 158), (330, 98), (400, 78), (440, 148), (460, 218), (520, 168),
                     (602, 148), (622, 262), (562, 332), (522, 362), (472, 422), (422, 472), (360, 472), (300, 452),
                     (230, 402), (160, 332), (118, 262), (98, 180)])
    m = rembg(cid, "isnet-general-use") & hull
    lamp = poly(sh, [(248, 288), (300, 258), (420, 258), (482, 298), (492, 380), (452, 422), (390, 442), (300, 432),
                     (258, 392)])
    flame = poly(sh, [(308, 98), (392, 68), (422, 150), (402, 222), (340, 252), (308, 200)])
    m = ndimage.binary_closing(m | lamp | flame, iterations=3)
    return ndimage.binary_fill_holes(m)


def m138(cid):
    sh = E.card_img(cid).shape[:2]
    return poly(sh, [(138, 108), (330, 98), (452, 158), (502, 218), (482, 300), (472, 332), (462, 422), (472, 500),
                     (452, 540), (168, 540), (148, 452), (88, 422), (108, 380), (168, 330), (158, 250), (128, 170)])


def m139(cid):
    sh = E.card_img(cid).shape[:2]
    return poly(sh, [(213, 295), (240, 288), (255, 268), (290, 298), (310, 288), (337, 298), (348, 320), (332, 347),
                     (322, 383), (348, 393), (338, 412), (300, 422), (273, 417), (253, 397), (223, 372), (211, 355),
                     (222, 320)])


def m140(cid):
    """the big face and hood (the small Scraggys around it are cameos and stay)"""
    sh = E.card_img(cid).shape[:2]
    return poly(sh, [(43, 210), (78, 148), (150, 103), (250, 83), (298, 58), (330, 38), (342, 88), (422, 108),
                     (482, 148), (522, 228), (542, 300), (532, 422), (482, 472), (422, 512), (360, 535), (200, 535),
                     (118, 502), (68, 442), (43, 340)])


def m141(cid):
    sh = E.card_img(cid).shape[:2]
    return poly(sh, [(268, 300), (283, 273), (310, 278), (335, 263), (372, 283), (382, 320), (377, 345), (397, 358),
                     (397, 392), (362, 402), (330, 417), (300, 422), (273, 412), (266, 370), (273, 345), (260, 320)])


def m143(cid):
    sh = E.card_img(cid).shape[:2]
    return poly(sh, [(88, 278), (130, 248), (200, 228), (213, 158), (238, 128), (292, 118), (332, 158), (390, 198),
                     (420, 168), (472, 148), (522, 158), (562, 208), (562, 272), (522, 332), (462, 342), (380, 332),
                     (342, 352), (342, 422), (332, 492), (290, 502), (260, 472), (220, 502), (178, 492), (188, 422),
                     (168, 352), (118, 342), (78, 322)])


def m144(cid):
    sh = E.card_img(cid).shape[:2]
    return poly(sh, [(203, 375), (223, 353), (247, 358), (252, 398), (290, 388), (300, 368), (320, 358), (347, 348),
                     (367, 363), (387, 398), (412, 418), (397, 452), (372, 462), (377, 502), (340, 507), (320, 472),
                     (290, 472), (270, 507), (243, 507), (243, 457), (223, 422), (208, 402)])


def m145(cid):
    sh = E.card_img(cid).shape[:2]
    return poly(sh, [(183, 215), (260, 208), (290, 188), (298, 148), (328, 58), (362, 73), (342, 158), (332, 193),
                     (360, 203), (392, 178), (432, 288), (472, 318), (472, 372), (442, 402), (412, 392), (382, 422),
                     (360, 432), (320, 412), (290, 442), (268, 452), (248, 422), (228, 402), (198, 332), (178, 290),
                     (218, 270), (198, 240)])


# ============================================================ per-card spec
HDR_BASIC = ((0, 0, 652, 88),)
HDR_STAGE = ((0, 0, 652, 108), (0, 0, 128, 168))
RB = (630, 0, 652, 914)                       # the right silver border
TXT_A = (0, 487, 652, 914)                    # the Ability banner of the four A-layout cards
ST_A, ST_B, ST_C, ST_D = (486, 355, 652, 482), (486, 400, 652, 525), (486, 435, 652, 560), (486, 452, 652, 578)

# id: sprite, flip, (x0, y0, S, W, H), boxes, mask fn, extra settings
SPEC = {
    "me55-129": dict(spr="exeggutor-alola", flip=False, crop=(218, 26, 8.2, 50, 57), hdr=HDR_STAGE,
                     stamp=ST_A, mask=m129, off=(5, 1), tex=(60, 280, 200, 440)),
    "me55-130": dict(spr="moltres", flip=True, crop=(100, 25, 10.4, 50, 45), hdr=HDR_BASIC, stamp=ST_A, mask=m130,
                     tex=(40, 380, 250, 480)),
    "me55-132": dict(spr="articuno", flip=False, crop=(75, 25, 9.75, 50, 48), hdr=HDR_BASIC, stamp=ST_A, mask=m132,
                     tex=(30, 320, 200, 440)),
    "me55-133": dict(spr="zapdos", flip=False, crop=(45, 25, 11.4, 50, 41), hdr=HDR_BASIC, stamp=ST_A, mask=m133,
                     tex=(30, 420, 200, 495)),
    "me55-134": dict(spr="toxtricity", flip=True, crop=(40, 25, 12.4, 46, 42), hdr=HDR_STAGE,
                     stamp=(486, 412, 652, 540), mask=m134, tex=(420, 110, 600, 250)),
    "me55-135": dict(spr="morpeko", flip=True, crop=(25, 26, 13.6, 44, 37), hdr=HDR_BASIC, stamp=ST_B, mask=m135,
                     tex=(40, 380, 200, 470)),
    "me55-136": dict(spr="drifloon", flip=False, crop=(25, 28, 14.3, 42, 37), hdr=HDR_BASIC, stamp=ST_C, mask=m136,
                     tex=(40, 110, 200, 330)),
    "me55-137": dict(spr="chandelure", flip=False, crop=(25, 25, 14.0, 43, 38), hdr=HDR_STAGE, stamp=ST_C,
                     mask=m137, tex=(40, 430, 200, 540)),
    "me55-138": dict(spr="lycanroc-midnight", flip=True, crop=(30, 25, 13.5, 44, 37), hdr=HDR_STAGE,
                     stamp=(476, 405, 652, 528), mask=m138, tex=(30, 180, 130, 330)),
    "me55-139": dict(spr="meowth-alola", flip=False, crop=(25, 25, 13.6, 44, 39), hdr=HDR_BASIC, stamp=ST_C,
                     mask=m139, tex=(380, 330, 480, 430)),
    "me55-140": dict(spr="scraggy", flip=False, crop=(32, 35, 19.5, 30, 25), hdr=HDR_BASIC, stamp=ST_B, mask=m140,
                     texture=False),
    "me55-141": dict(spr="meowth-galar", flip=False, crop=(25, 35, 13.6, 44, 36), hdr=HDR_BASIC, stamp=ST_B,
                     mask=m141, tex=(420, 280, 520, 380)),
    "me55-143": dict(spr="kommo-o", flip=False, crop=(18, 20, 14.6, 41, 37), hdr=((0, 0, 634, 105), (0, 0, 126, 162)),
                     stamp=(466, 430, 634, 550), mask=m143, rb=(615, 0, 634, 888), tex=(30, 380, 170, 540)),
    "me55-144": dict(spr="meowth", flip=True, crop=(25, 25, 13.6, 44, 39), hdr=HDR_BASIC, stamp=ST_C, mask=m144,
                     tex=(40, 200, 180, 330)),
    "me55-145": dict(spr="zorua-hisui", flip=False, crop=(25, 30, 14.3, 42, 38), hdr=HDR_BASIC, stamp=ST_D,
                     mask=m145, tex=(40, 300, 150, 440)),
}
IDS = list(SPEC)


def make_masks(ids):
    E.MASKS.mkdir(exist_ok=True)
    tiles = []
    for cid in ids:
        m = ndimage.binary_fill_holes(SPEC[cid]["mask"](cid))
        Image.fromarray((m * 255).astype(np.uint8)).save(E.MASKS / f"{cid}.png")
        rgb = E.card_img(cid)
        o = np.where(m[..., None], rgb * 0.35 + np.array([0.6, 0, 0.4]) * 0.65, rgb)
        tiles.append(Image.fromarray(L.to8(o)).resize((326, 457)))
        ys, xs = np.nonzero(m)
        print(cid, "mask bbox", xs.min(), ys.min(), xs.max(), ys.max(), f"{m.mean():.2f}")
    n = 5
    sheet = Image.new("RGB", (326 * n, 457 * ((len(tiles) + n - 1) // n)))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % n) * 326, (i // n) * 457))
    sheet.save(E.WORK / f"masks-{GROUP}.png")


def centre_off(cid, x0, y0, S, spr):
    """sprite centred on the real Pokemon's mask bbox centre"""
    ys, xs = np.nonzero(E.mask(cid))
    cx = ((xs.min() + xs.max()) / 2 - x0) / S
    cy = ((ys.min() + ys.max()) / 2 - y0) / S
    return round(cx - spr.w / 2), round(cy - spr.h / 2)


# ============================================================ the builder (Lapras 131, card by card)
def build_ir(cid):
    sp = SPEC[cid]
    x0, y0, S, W, H = sp["crop"]
    n = int(E.num(cid))
    boxes = tuple(sp["hdr"]) + (sp["stamp"], sp.get("rb", RB)) + ((TXT_A,) if sp["stamp"] == ST_A else ())
    rgb, _ = E.clean(cid, grow=5, boxes=boxes, texture=sp.get("texture", True), tex_src=sp.get("tex"))
    spr = Sprite(sp["spr"], flip=sp["flip"])
    c = Card(W, H)
    place(c, spr, cid, x0, y0, S, off=sp.get("off") or centre_off(cid, x0, y0, S, spr), margin=1)
    a = L.sample(rgb, x0, y0, S / 2, 2 * W, 2 * H, resample=L.Image.LANCZOS)
    a = L.tone(a, sat=sp.get("sat", 1.2), bright=1.0, gamma=0.97)
    a = L.focus_halo(c, a, radius=4, dark=0.82, soft=1.2)
    a = L.radial_glow(c, a, (1.0, 0.96, 0.85), max(c.FW, c.FH) * 0.55, sp.get("glow", 0.1))
    a = L.vignette(a, 0.18, tint=(0.08, 0.12, 0.22))
    # IR texture (as Lapras 131): lighter and wider-spaced than the Rare Ultra's fingerprint, following the shading
    FW, FH = c.FW, c.FH
    lum = ndimage.gaussian_filter(a @ W_LUM, 2.0)
    f, _ = fingerprint(FW, FH, [(0.24 * FW, 0.21 * FH, 1.0), (0.8 * FW, 0.79 * FH, 0.7)], period=4.0, seed=n)
    f = f + 9.0 * lum
    period = 4.0
    ln = ((f / period) % 1.0) < (1.0 / period)
    a = np.clip(a + np.where(ln, 0.065, 0.0)[..., None] * (0.6 + 0.4 * a), 0, 1)
    L.finish(c, a, 170, method="median")
    c.bgq = L.rim(c, c.bgq, colour=(1.0, 0.98, 0.9), amt=0.3)
    stars = [(6, 6, 3), (FW - 8, 8, 2), (FW - 6, FH - 12, 2), (round(0.2 * FW), round(0.45 * FH), 2)]
    for x, y, st in stars:
        L.sparkle(c, x, y, st, {"L": "#ffffff", "l": "#fff6dc", "j": "#9fe8ff"})
    card = P.card_json(cid)
    return meta(c, card=cid, label=f"Illustration Rare: {card['name']} {card['number']}/128 (light etch, full art)",
                rarity="Illustration Rare", finish="illustration rare: full painting, light etched texture along the art",
                variant="illustration-rare", anim="etch", ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S,
                stars=stars, etch_field=f, etch_period=period, frame="#7fd6e6")


p30cards.BUILDERS.update({cid: (lambda cid=cid: build_ir(cid)) for cid in IDS})


def main():
    args = sys.argv[1:]
    step = args[0] if args and args[0] in ("masks", "build", "anim", "verify", "sheet", "all") else "all"
    ids = [a for a in args if a in SPEC] or IDS
    sizes_f = P.DATA / "sheets" / f"{GROUP}-sizes.json"
    sizes = json.loads(sizes_f.read_text(encoding="utf-8")) if sizes_f.exists() else {}
    if step in ("masks", "all"):
        make_masks(ids)
    if step in ("build", "all"):
        for cid in ids:
            _, sizes[cid] = p30build.render(cid)
        sizes_f.parent.mkdir(exist_ok=True)
        sizes_f.write_text(json.dumps({k: sizes[k] for k in IDS if k in sizes}, indent=1), encoding="utf-8")
    if step in ("anim", "all"):
        p30anim.build(ids)
    if step in ("verify", "all"):
        for cid in ids:
            p30verify.check(cid)
        print(f"{p30verify.fails} failures")
        assert p30verify.fails == 0
    if step in ("sheet", "all"):
        p30sheet.sheet([k for k in IDS if k in sizes], P.DATA / "sheets" / f"{GROUP}.png", sizes)


if __name__ == "__main__":
    main()
