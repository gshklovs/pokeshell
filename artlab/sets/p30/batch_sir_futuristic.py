r"""Group "sir_futuristic" of the 30th Celebration (me55) full set: 8 Special Illustration Rares, built exactly like
the approved Gengar ex 154 (evs alt-art textured painting + the SIR pearl lustre, anim `sir`), and the Futuristic
Rare Mew ex 158, built exactly like the approved Mewtwo ex 157 (liquid chrome over the card's own scene, smooth
fill, the low-opacity animated Futuristic tint on the sprite, anim `chrome`).

Masks of the real Pokemon go to masks/<id>.png (rembg or a colour rule inside a hand hull, card px read off
work/grid_<n>.png). Writes sheets/sir_futuristic.png and sheets/sir_futuristic-sizes.json (never the ladder's).

  ..\..\..\.venv\Scripts\python batch_sir_futuristic.py [masks] [me55-148 ...]
"""
import json
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

import p30lib as P
from p30lib import E, L, Card, Sprite
import p30cards as C
import p30masks as PM
from evcards import W_LUM, meta, place, rainbow_rgb

GROUP = "sir_futuristic"
PLAN = json.loads((P.HERE / "plan.json").read_text(encoding="utf-8"))[GROUP]
BY_ID = {e["id"]: e for e in PLAN}
poly, rect, largest, rembg, hsv = PM.poly, PM.rect, PM.largest, PM.rembg, PM.hsv


def stroke(shape, pts, width):
    """a thick polyline (ribbons, tails) as a mask"""
    im = Image.new("L", (shape[1], shape[0]), 0)
    d = ImageDraw.Draw(im)
    d.line(pts, fill=255, width=width, joint="curve")
    for x, y in (pts[0], pts[-1]):
        d.ellipse((x - width / 2, y - width / 2, x + width / 2, y + width / 2), fill=255)
    return np.asarray(im) > 0


# ============================================================ masks (white = the real Pokemon)
def m148():
    """Greninja fills the middle: pink tongue-scarf loop, blue arm with the pale bulbs, head, webbed hand; the
    scene is the same pink / blue, so a hand hull (generous) -- filled smooth anyway"""
    cid = "me55-148"
    sh = E.card_img(cid).shape[:2]
    m = poly(sh, [(38, 250), (80, 205), (150, 190), (215, 205), (250, 200), (258, 128), (300, 112), (345, 118),
                  (398, 150), (400, 215), (455, 162), (475, 170), (470, 300), (500, 340), (595, 380), (530, 415),
                  (528, 470), (522, 530), (468, 530), (425, 480), (412, 530), (390, 575), (250, 575), (245, 480),
                  (200, 425), (140, 425), (85, 400), (38, 365)])
    return cid, m


def m149():
    """Pikachu running right in the crowd: yellow inside his hull (tail zigzag, ears, body), closed"""
    cid = "me55-149"
    rgb, h, s, v = hsv(cid)
    sh = rgb.shape[:2]
    hull = poly(sh, [(158, 245), (215, 238), (252, 298), (300, 298), (368, 292), (383, 262), (412, 268), (422, 330),
                     (445, 400), (435, 470), (365, 482), (352, 525), (298, 525), (258, 472), (198, 452), (196, 418),
                     (236, 398), (208, 362), (158, 302)])
    yellow = (h > 36) & (h < 66) & (s > 0.45) & (v > 0.55)
    dark = (v < 0.3)
    m = hull & (yellow | (dark & ndimage.binary_dilation(yellow, iterations=6)))
    m = ndimage.binary_closing(m, iterations=6)
    m = ndimage.binary_opening(m, iterations=1)
    return cid, ndimage.binary_fill_holes(largest(m, 2))


def m150():
    """Pikachu waving, front and centre, Eevee overlapping his right leg (Eevee's brown is outside the rule)"""
    cid = "me55-150"
    rgb, h, s, v = hsv(cid)
    sh = rgb.shape[:2]
    hull = poly(sh, [(222, 420), (258, 380), (268, 330), (292, 252), (348, 262), (362, 290), (430, 286), (498, 286),
                     (494, 342), (442, 372), (442, 432), (422, 482), (402, 528), (298, 528), (246, 472)])
    yellow = (h > 38) & (h < 66) & (s > 0.45) & (v > 0.55)
    dark = (v < 0.3)
    m = hull & (yellow | (dark & ndimage.binary_dilation(yellow, iterations=6)))
    m = ndimage.binary_closing(m, iterations=6)
    m = ndimage.binary_opening(m, iterations=1)
    return cid, ndimage.binary_fill_holes(largest(m, 2))


def m151():
    """isnet-anime has Mewtwo (and the dark halo round his head, cut back out by value)"""
    cid = "me55-151"
    rgb, h, s, v = hsv(cid)
    sh = rgb.shape[:2]
    m = rembg(cid, "isnet-anime") & rect(sh, 0, 90, 634, 888)
    m &= (v > 0.22) | ~rect(sh, 0, 0, 634, 260)
    m = ndimage.binary_opening(m, iterations=2)
    m = ndimage.binary_closing(m, iterations=3)
    return cid, ndimage.binary_fill_holes(largest(m))


def m152():
    """isnet-general-use has Mew curled in the light, tail and all"""
    cid = "me55-152"
    sh = E.card_img(cid).shape[:2]
    m = rembg(cid, "isnet-general-use") & rect(sh, 0, 90, 634, 470)
    m = ndimage.binary_closing(m, iterations=3)
    tail = stroke(sh, [(287, 250), (288, 200), (295, 165), (318, 138), (360, 124), (400, 117), (445, 112)], 16)
    return cid, ndimage.binary_fill_holes(largest(m)) | tail


def m153():
    """Sylveon: the head / body hull, plus her four feelers as thick strokes (pale pink with blue tips)"""
    cid = "me55-153"
    rgb, h, s, v = hsv(cid)
    sh = rgb.shape[:2]
    body = poly(sh, [(218, 190), (262, 178), (300, 205), (328, 232), (372, 172), (412, 176), (425, 230), (408, 285),
                     (388, 320), (392, 360), (420, 395), (430, 450), (425, 500), (400, 525), (350, 528), (318, 500),
                     (300, 450), (292, 400), (280, 345), (250, 300), (222, 250)])
    ribbons = (stroke(sh, [(313, 332), (250, 330), (195, 322), (140, 300), (112, 272), (120, 250), (150, 238),
                           (195, 240)], 30)
               | poly(sh, [(115, 238), (200, 232), (205, 272), (140, 272)])
               | stroke(sh, [(300, 385), (240, 398), (180, 410), (120, 435), (80, 455)], 34)
               | poly(sh, [(55, 410), (150, 405), (160, 470), (80, 480), (50, 455)])
               | stroke(sh, [(395, 250), (430, 205), (465, 160), (500, 145), (520, 185), (528, 245), (525, 300),
                             (482, 338), (420, 330)], 30)
               | poly(sh, [(455, 135), (520, 120), (530, 200), (470, 175)])
               | stroke(sh, [(410, 380), (500, 392), (590, 408), (648, 420)], 30)
               | poly(sh, [(350, 440), (430, 440), (430, 500), (360, 500)]))
    return cid, body | ribbons


def m155():
    """Jirachi: the body hull, plus the yellow wish-tag streams (yellow rule inside their hull) and the green tags"""
    cid = "me55-155"
    rgb, h, s, v = hsv(cid)
    sh = rgb.shape[:2]
    body = poly(sh, [(125, 205), (165, 198), (215, 212), (260, 205), (310, 225), (350, 285), (352, 325), (325, 345),
                     (298, 385), (268, 392), (255, 355), (205, 370), (175, 355), (160, 300)])
    tags = poly(sh, [(330, 280), (380, 190), (420, 120), (455, 68), (475, 72), (440, 160), (400, 250), (360, 310),
                     (300, 380), (330, 385), (420, 340), (500, 280), (525, 265), (520, 300), (440, 360), (340, 405),
                     (285, 400)])
    yellow = (h > 30) & (h < 62) & (s > 0.45) & (v > 0.55)
    t = ndimage.binary_closing(tags & yellow, iterations=4)
    t = ndimage.binary_opening(t, iterations=1)
    green = poly(sh, [(118, 195), (160, 190), (165, 220), (125, 225)]) | poly(sh, [(150, 380), (178, 380),
                                                                                (178, 420), (150, 420)])
    streams = (stroke(sh, [(463, 70), (447, 118), (426, 168), (400, 215), (370, 255), (335, 292)], 24)
               | stroke(sh, [(517, 255), (485, 295), (450, 328), (400, 358), (350, 385), (300, 405), (282, 398)], 26))
    return cid, body | largest(t, 3) | green | streams


def m156():
    """isnet-general-use has Salamence, wings, tail and claws (the stamp is a box of its own)"""
    cid = "me55-156"
    sh = E.card_img(cid).shape[:2]
    m = rembg(cid, "isnet-general-use") & rect(sh, 0, 100, 652, 914) & ~rect(sh, 470, 385, 652, 540)
    m = ndimage.binary_closing(m, iterations=4)
    return cid, ndimage.binary_fill_holes(largest(m))


def m158():
    """Mew in iridescent chrome, half the card: a hand hull (head, ears, body, the long tail down the left)"""
    cid = "me55-158"
    sh = E.card_img(cid).shape[:2]
    m = poly(sh, [(235, 102), (282, 115), (305, 150), (365, 128), (470, 118), (505, 150), (522, 262), (505, 330),
                  (475, 380), (458, 440), (480, 468), (505, 490), (505, 560), (160, 560), (138, 470), (112, 380),
                  (118, 260), (150, 160), (195, 108)])
    return cid, m


MASKS = {"me55-148": m148, "me55-149": m149, "me55-150": m150, "me55-151": m151, "me55-152": m152,
         "me55-153": m153, "me55-155": m155, "me55-156": m156, "me55-158": m158}


def make_masks(ids):
    E.MASKS.mkdir(exist_ok=True)
    tiles = []
    for cid in ids:
        _, m = MASKS[cid]()
        Image.fromarray((m * 255).astype(np.uint8)).save(E.MASKS / f"{cid}.png")
        rgb = E.card_img(cid)
        o = np.where(m[..., None], rgb * 0.35 + np.array([0, 0.5, 0]), rgb)
        tiles.append(Image.fromarray(L.to8(o)).resize((326, 457)))
        ys, xs = np.nonzero(m)
        print(cid, "mask bbox", xs.min(), ys.min(), xs.max(), ys.max(), f"{m.mean():.2f}")
    sheet = Image.new("RGB", (326 * min(5, len(tiles)), 457 * ((len(tiles) + 4) // 5)))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % 5) * 326, (i // 5) * 457))
    sheet.save(E.WORK / f"masks-{GROUP}.png")


# ============================================================ SIR: the Gengar ex 154 recipe
# per card: art window (x0, y0, S, W, H), painted-out boxes (header / stage icon / 30th stamp / text / edges),
# texture source, sprite flip, sprite offset nudge, stars (grid px), label
EDGE652 = ((0, 0, 20, 914), (632, 0, 652, 914))
EDGE634 = ((0, 0, 16, 888), (620, 0, 634, 888))

SIR = {
    "me55-148": dict(win=(20, 96, 16.0, 38, 27), flip=True, tex=(470, 110, 620, 250),
                     boxes=((0, 0, 652, 96), (0, 20, 128, 160), (100, 60, 470, 108), (478, 382, 652, 530),
                            (0, 528, 652, 914)) + EDGE652,
                     scene="Greninja ex 148/128, GIDORA (concert light show)"),
    "me55-149": dict(win=(20, 95, 13.9, 44, 31), flip=True, tex=(40, 100, 200, 200),
                     boxes=((0, 0, 652, 95), (482, 395, 652, 538), (0, 528, 652, 914)) + EDGE652,
                     scene="Pikachu ex 149/128, kantaro (the Pika-Pika parade)"),
    "me55-150": dict(win=(20, 95, 13.9, 44, 31), flip=False, tex=(40, 100, 200, 200),
                     boxes=((0, 0, 652, 95), (482, 392, 652, 535), (0, 528, 652, 914)) + EDGE652,
                     scene="Pikachu ex 150/128, kantaro (fireworks party)"),
    "me55-151": dict(win=(95, 88, 9.4, 48, 44), flip=False, tex=(30, 110, 150, 300),
                     boxes=((0, 0, 634, 90), (465, 380, 634, 505), (0, 505, 634, 888)) + EDGE634,
                     scene="Mewtwo ex 151/128, Yano Keiji (psychic art-deco)"),
    "me55-152": dict(win=(20, 95, 12.9, 46, 29), flip=False, tex=(30, 110, 200, 300),
                     boxes=((0, 0, 634, 95), (465, 375, 634, 500), (0, 474, 634, 888)) + EDGE634,
                     scene="Mew ex 152/128, Kuroimori (sunbeam in the flowering wood)"),
    "me55-153": dict(win=(20, 100, 13.3, 46, 34), flip=False, tex=(30, 120, 190, 300),
                     boxes=((0, 0, 652, 100), (0, 20, 128, 160), (100, 60, 470, 110), (485, 430, 652, 565),
                            (0, 560, 652, 914)) + EDGE652,
                     scene="Sylveon ex 153/128, You Iribi (the rose party)"),
    "me55-155": dict(win=(20, 92, 13.9, 44, 31), flip=False, tex=(530, 110, 630, 380),
                     boxes=((0, 0, 652, 92), (485, 395, 652, 540), (0, 528, 652, 914)) + EDGE652,
                     scene="Jirachi ex 155/128, AKIRA EGAWA (star-stream vortex)"),
    "me55-156": dict(win=(20, 100, 13.3, 46, 32), flip=False, tex=(30, 300, 200, 420),
                     boxes=((0, 0, 652, 100), (0, 20, 128, 160), (100, 60, 470, 110), (476, 390, 652, 535),
                            (0, 528, 652, 914)) + EDGE652,
                     scene="Salamence ex 156/128, Ryota Murayama (balloon festival town)"),
}


def sir(cid):
    cfg = SIR[cid]
    x0, y0, S, W, H = cfg["win"]
    rgb, _ = E.clean(cid, grow=5, boxes=cfg["boxes"], tex_src=cfg["tex"])
    spr = Sprite(BY_ID[cid]["sprite"], flip=cfg["flip"])
    c = Card(W, H)
    place(c, spr, cid, x0, y0, S, off=cfg.get("off"), margin=1)
    a = L.sample(rgb, x0, y0, S / 2, 2 * W, 2 * H, resample=L.Image.LANCZOS)
    a = L.tone(a, sat=1.32, bright=1.0, gamma=1.1)            # vivid: deeper + more saturated than 154
    a = L.focus_halo(c, a, radius=4, dark=0.8, soft=1.2)
    lum = a @ W_LUM
    h = ndimage.gaussian_filter(lum, 0.6)
    gy, gx = np.gradient(h)
    relief = np.clip(-(gx * -1.0 + gy * -1.3) * 2.4, -0.3, 0.3)
    a = np.clip(a + relief[..., None] * (0.35 + 0.65 * a), 0, 1)
    a = L.vignette(a, 0.4, tint=(0.02, 0.04, 0.12))
    FH, FW = c.FH, c.FW
    yy, xx = np.mgrid[0:FH, 0:FW]
    diag, span = xx + yy, FW + FH
    dd = diag - 0.26 * span
    pearl = rainbow_rgb(C.PEARL[0] + (C.PEARL[1] - C.PEARL[0]) * np.clip(dd / 40 + 0.5, 0, 1), s=0.3)
    k = 0.36 * np.exp(-0.5 * (dd / 18) ** 2)
    a = a + (pearl - a) * k[..., None]
    L.finish(c, a, 200, method="median")
    c.bgq = L.rim(c, c.bgq, colour=(1.0, 0.6, 0.9), amt=0.4)
    stars = free_stars(c, [(0.07, 0.42, 2), (0.65, 0.08, 3), (0.93, 0.72, 2), (0.43, 0.92, 2)])
    for x, y, st in stars:
        L.sparkle(c, x, y, st, {"L": "#ffffff", "l": "#ffe0f4", "j": "#a8f0ff"})
    card = P.card_json(cid)
    return meta(c, card=cid, label=f"Special Illustration Rare: {cfg['scene']} (textured painting, pearl)",
                rarity="Special Illustration Rare",
                finish="SIR: textured painting (brushwork embossed) + pearlescent pink/cyan lustre",
                variant="special-illustration-rare", anim="sir", ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S,
                stars=stars, height=h, frame="#f0c850", name=card["name"])


def free_stars(c, rel):
    """stars at relative spots (Gengar's layout), nudged off the sprite onto the background"""
    out = []
    for fx, fy, st in rel:
        x, y = round(fx * (c.FW - 1)), round(fy * (c.FH - 1))
        for r in range(0, 12):
            cand = [(x + dx, y + dy) for dx in range(-r, r + 1) for dy in range(-r, r + 1)
                    if max(abs(dx), abs(dy)) == r]
            ok = [(X, Y) for X, Y in cand if 3 <= X < c.FW - 3 and 3 <= Y < c.FH - 3
                  and all((X + a, Y + b) not in c.cells for a in range(-2, 3) for b in range(-2, 3))]
            if ok:
                x, y = ok[0]
                break
        out.append((x, y, st))
    return out


# ============================================================ Futuristic Rare: the Mewtwo ex 157 recipe
def mew158():
    cid = "me55-158"
    x0, y0, S, W, H = 20, 90, 13.7, 44, 29
    boxes = ((0, 0, 652, 90), (485, 355, 652, 480), (0, 488, 652, 914)) + EDGE652
    rgb, _ = E.clean(cid, grow=5, boxes=boxes, texture=False)      # the hole is half the card: smooth fill
    spr = Sprite("mew")
    c = Card(W, H)
    place(c, spr, cid, x0, y0, S, margin=1)
    C.futuristic_sprite(c, C.futuristic_tint(cid))
    a = L.sample(rgb, x0, y0, S / 2, 2 * W, 2 * H, resample=L.Image.LANCZOS)
    a = L.tone(a, sat=1.2, bright=1.0)
    a = L.focus_halo(c, a, radius=4, dark=0.75, soft=1.2)
    scene = a
    q, refl = C.chrome(a)
    FH, FW = c.FH, c.FW
    yy, xx = np.mgrid[0:FH, 0:FW]
    spec = np.abs((xx + yy) - 0.3 * (FW + FH)) < 0.8
    q = np.where(spec[..., None], q + (1 - q) * 0.55, q)
    L.finish(c, q, 180, method="median")
    c.bgq = L.rim(c, c.bgq, colour=(0.8, 1.0, 1.0), amt=0.45)
    stars = free_stars(c, [(0.06, 0.07, 3), (0.94, 0.12, 2), (0.92, 0.9, 3), (0.06, 0.7, 2)])
    for x, y, st in stars:
        L.sparkle(c, x, y, st, {"L": "#ffffff", "l": "#e0fbff", "j": "#ff9af0"})
    return meta(c, card=cid, label="Futuristic Rare: Mew ex 158/128, YOSHIROTTEN (liquid chrome over the energy orbs)",
                rarity="Futuristic Rare",
                finish="futuristic rare: liquid chrome over the iridescent scene, specular line; sprite tinted (<=0.3), flowing",
                variant="futuristic-rare", anim="chrome", ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S,
                stars=stars, scene=scene, frame="#c07cff")


POOL = 21000          # suite3 anim.quantise's key pool is 21792 colours over all 16 frames


def fit_pool(kind):
    """local fix (shared p30anim / suite3 untouched): the busiest paintings (e.g. the Pikachu 149 crowd) run
    the 16-frame palette past the key pool. Coarsen the MOVING frames' steps (4 -> 6 -> 8 ...) until it fits;
    the final frame stays the exact static art"""
    def run(c, shiny):
        frames = kind(c, shiny)
        for step in (4, 6, 8, 10, 12):
            if step > 4:
                frames = [[[None if v is None else tuple(min(255, int(round(ch / step) * step)) for ch in v)
                            for v in r] for r in g] if i < len(frames) - 1 else g for i, g in enumerate(frames)]
            n = len({v for g in frames for r in g for v in r if v is not None})
            if n <= POOL:
                break
        return frames
    return run


def builders():
    b = {cid: (lambda cid=cid: sir(cid)) for cid in SIR}
    b["me55-158"] = mew158
    return b


def main():
    args = sys.argv[1:]
    ids = [a for a in args if a in BY_ID] or list(BY_ID)
    if "masks" in args:
        make_masks(ids)
        if "only" in args:
            return
    import p30build
    import p30anim
    import p30verify
    import p30sheet
    C.BUILDERS.update(builders())
    p30anim.KINDS["sir"] = fit_pool(p30anim.KINDS["sir"])
    p30anim.KINDS["chrome"] = fit_pool(p30anim.KINDS["chrome"])
    f = P.DATA / "sheets" / f"{GROUP}-sizes.json"
    sizes = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    for cid in ids:
        _, sizes[cid] = p30build.render(cid)
    f.parent.mkdir(exist_ok=True)
    f.write_text(json.dumps({k: sizes[k] for k in BY_ID if k in sizes}, indent=1), encoding="utf-8")
    if "noanim" not in args:
        p30anim.build(ids)
        for cid in ids:
            p30verify.check(cid)
        print(f"{p30verify.fails} failures")
        assert p30verify.fails == 0
    done = [k for k in BY_ID if k in sizes]
    p30sheet.sheet(done, P.DATA / "sheets" / f"{GROUP}.png", sizes)


if __name__ == "__main__":
    main()
