r"""30th Celebration full set, group "double_rare": the 10 remaining Double Rare ex cards, built exactly as the
approved Umbreon ex 92 (p30cards.umbreon): evs Rare Holo V silver frame + the card's own scene (Pokemon masked
out and filled), the SV/ME ex fine sparkle grain (ex_grain), anim 'ex'. Crop as 92: the upper card, x0 = 20,
S ~ 15.

  ..\..\..\.venv\Scripts\python batch_double_rare.py masks     masks/<id>.png + work/dr_masks.png (overlay check)
  ..\..\..\.venv\Scripts\python batch_double_rare.py [ids]     build + anim + verify + sheets/double_rare.png
"""
import json
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

import p30lib as P
from p30lib import E, L, Sprite
import p30cards as C
import p30masks as PM
from evcards import colour_blend, meta, place, rainbow_rgb, silver_frame
import p30build
import p30anim
import p30verify
import p30sheet

GROUP = "double_rare"
poly, rect, largest, rembg, hsv = PM.poly, PM.rect, PM.largest, PM.rembg, PM.hsv

STAMP_R = (466, 326, 652, 470)               # the 30th stamp on the right (all but 54)
STAMP_L = (0, 326, 186, 470)                 # ... on the left (54, as 92)
ICON = (0, 40, 172, 178)                     # the stage icon (Stage 1 / 2 only)


def bar(x0, x1):
    """the ex frame's dark rule across the art bottom (beside the stamp)"""
    return (x0, 428, x1, 462)


# ============================================================ masks (white = the real Pokemon), card px
def _finish(m, close=5, keep=1, stamp=None):
    sh = m.shape
    if stamp is not None:
        m = m & ~rect(sh, *stamp)
    m = ndimage.binary_closing(m, iterations=close)
    return ndimage.binary_fill_holes(largest(m, keep))


def m21():
    """Greninja: isnet has the head, body and legs; the tongue scarf by its pink inside its hull"""
    cid = "me55-21"
    rgb, h, s, v = hsv(cid)
    sh = rgb.shape[:2]
    m = rembg(cid, "isnet-general-use") & rect(sh, 0, 88, 652, 470)
    pink = ((h > 320) | (h < 15)) & (s > 0.35) & (v > 0.35)
    tongue = poly(sh, [(440, 88), (652, 88), (652, 215), (560, 215), (470, 140)])
    m |= ndimage.binary_opening(pink & tongue, iterations=1)
    m |= poly(sh, [(70, 100), (250, 100), (330, 200), (450, 230), (470, 330), (420, 440), (120, 440), (80, 330)])
    return cid, _finish(m, 5, 2, STAMP_R)


def m53():
    cid = "me55-53"
    rgb, h, s, v = hsv(cid)
    sh = rgb.shape[:2]
    hull = poly(sh, [(20, 95), (175, 95), (260, 150), (380, 110), (632, 95), (632, 200), (570, 260), (560, 330),
                     (470, 470), (90, 480), (20, 430)])
    yel = (h > 30) & (h < 68) & (s > 0.45) & (v > 0.55)
    red = ((h > 330) | (h < 20)) & (s > 0.4)
    dark = v < 0.3
    m = hull & (rembg(cid, "u2net") | yel | red | dark)
    m = ndimage.binary_opening(m, iterations=2)
    return cid, _finish(m, 6, 1, STAMP_R)


def m54():
    cid = "me55-54"
    rgb, h, s, v = hsv(cid)
    sh = rgb.shape[:2]
    hull = poly(sh, [(120, 95), (270, 95), (420, 120), (560, 150), (640, 230), (640, 520), (480, 530), (300, 480),
                     (200, 420), (130, 260)])
    m = hull & rembg(cid, "isnet-general-use")
    body = ((h > 20) & (h < 65) & (s > 0.3) & (v > 0.45)) | (((h > 300) | (h < 20)) & (s > 0.3))
    m |= hull & ndimage.binary_opening(body, iterations=2)
    return cid, _finish(m, 6, 1, STAMP_L)


def m64():
    cid = "me55-64"
    rgb, h, s, v = hsv(cid)
    sh = rgb.shape[:2]
    hull = poly(sh, [(20, 95), (632, 95), (632, 330), (560, 470), (20, 470)])
    lav = (h > 250) & (h < 335) & (s > 0.06) & (s < 0.5) & (v > 0.45)
    m = hull & (rembg(cid, "isnet-general-use") | ndimage.binary_opening(lav, iterations=2))
    m |= poly(sh, [(200, 110), (460, 95), (560, 180), (560, 330), (480, 440), (300, 460), (260, 330), (180, 250)])
    return cid, _finish(m, 5, 2, STAMP_R)


def m66():
    cid = "me55-66"
    rgb, h, s, v = hsv(cid)
    sh = rgb.shape[:2]
    hull = poly(sh, [(20, 95), (632, 95), (632, 330), (560, 470), (20, 470)])
    pink = ((h > 290) | (h < 25)) & (s > 0.1) & (s < 0.65) & (v > 0.55)
    eye = (h > 190) & (h < 225) & (s > 0.45) & poly(sh, [(180, 230), (300, 230), (300, 420), (60, 430), (60, 340)])
    m = hull & (ndimage.binary_opening(pink, iterations=2) | eye)
    return cid, _finish(m, 5, 2, STAMP_R)


def m70():
    cid = "me55-70"
    rgb, h, s, v = hsv(cid)
    sh = rgb.shape[:2]
    hull = poly(sh, [(20, 110), (120, 95), (632, 95), (632, 330), (470, 440), (300, 470), (150, 560), (20, 560)])
    pink = ((h > 265) | (h < 15)) & (s > 0.08) & (s < 0.6) & (v > 0.5)
    m = hull & ndimage.binary_opening(pink, iterations=2)
    return cid, _finish(m, 8, 2, STAMP_R)


def m71():
    cid = "me55-71"
    rgb, h, s, v = hsv(cid)
    sh = rgb.shape[:2]
    hull = poly(sh, [(40, 200), (280, 190), (300, 88), (560, 88), (632, 150), (632, 330), (560, 440), (300, 470),
                     (130, 440), (40, 280)])
    m = hull & rembg(cid, "isnet-general-use")
    return cid, _finish(m, 5, 2, STAMP_R)


def m90():
    cid = "me55-90"
    rgb, h, s, v = hsv(cid)
    sh = rgb.shape[:2]
    hull = poly(sh, [(20, 110), (100, 110), (180, 125), (300, 95), (470, 95), (545, 130), (565, 260), (500, 330),
                     (470, 440), (120, 455), (90, 330), (20, 270)])
    violet = (h > 235) & (h < 290) & (s > 0.3) & (v > 0.18)
    white = (s < 0.15) & (v > 0.75)
    red = ((h > 330) | (h < 15)) & (s > 0.35) & (v > 0.12)
    m = hull & ndimage.binary_opening(violet | white | red, iterations=2)
    m |= poly(sh, [(100, 120), (250, 110), (330, 100), (450, 110), (530, 160), (520, 300), (470, 440), (130, 440),
                   (100, 330)])
    return cid, _finish(m, 5, 1, STAMP_R)


def m102():
    cid = "me55-102"
    rgb, h, s, v = hsv(cid)
    sh = rgb.shape[:2]
    hull = poly(sh, [(20, 330), (120, 230), (230, 150), (380, 110), (480, 95), (600, 150), (620, 280), (580, 330),
                     (530, 470), (330, 470), (160, 440), (20, 440)])
    orange = (h > 18) & (h < 58) & (s > 0.35) & (v > 0.55)
    white = (s < 0.2) & (v > 0.7)
    teal = (h > 150) & (h < 200) & (s > 0.3)
    m = hull & ndimage.binary_opening(orange | white | teal, iterations=2)
    m |= poly(sh, [(20, 180), (100, 165), (190, 95), (632, 95), (632, 210), (600, 300), (540, 460), (300, 465),
                   (120, 440), (20, 420)])        # the body fills the window: the hull itself (ghosts otherwise)
    return cid, _finish(m, 6, 1, STAMP_R)


def m109():
    cid = "me55-109"
    rgb, h, s, v = hsv(cid)
    sh = rgb.shape[:2]
    hull = poly(sh, [(20, 95), (632, 95), (632, 330), (470, 440), (20, 470)])
    m = hull & rembg(cid, "isnet-general-use")
    return cid, _finish(m, 5, 2, STAMP_R)


MASKS = {f.__name__[1:]: f for f in (m21, m53, m54, m64, m66, m70, m71, m90, m102, m109)}


def make_masks(nums=None):
    E.MASKS.mkdir(exist_ok=True)
    tiles = []
    for n, fn in MASKS.items():
        if nums and n not in nums:
            continue
        cid, m = fn()
        Image.fromarray((m * 255).astype(np.uint8)).save(E.MASKS / f"{cid}.png")
        rgb = E.card_img(cid)
        o = np.where(m[..., None], rgb, rgb * 0.3 + np.array([0, 0.35, 0]))
        t = Image.fromarray(L.to8(o[:600]))
        ImageDraw.Draw(t).text((10, 580), cid, fill=(255, 255, 0))
        tiles.append(t)
        ys, xs = np.nonzero(m)
        print(cid, "bbox", xs.min(), ys.min(), xs.max(), ys.max(), f"{m.mean():.2f}")
    per = 5
    sheet = Image.new("RGB", (652 * min(per, len(tiles)), 600 * ((len(tiles) + per - 1) // per)))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % per) * 652, (i // per) * 600))
    sheet.save(E.WORK / "dr_masks.png")


# ============================================================ the builder: umbreon() with per-card settings
# cfg: sprite, flip, stamp box, text top, stage icon?, bar, (x0, y0, S, W, H), off, tex_src, tone, stars
CFG = {
    "me55-21": dict(name="Greninja ex 021/128", spr="greninja", stamp=STAMP_R, text=520, icon=True, bar=bar(15, 470)),
    "me55-53": dict(name="Pikachu ex 053/128", spr="pikachu", stamp=STAMP_R, text=520, icon=False, bar=bar(15, 470)),
    "me55-54": dict(name="Pikachu ex 054/128", spr="pikachu", flip=True, stamp=STAMP_L, text=520, icon=False,
                    bar=bar(180, 640)),
    "me55-64": dict(name="Mewtwo ex 064/128", spr="mewtwo", stamp=STAMP_R, text=520, icon=False, S=13.0, W=47, H=44, bar=bar(15, 470)),
    "me55-66": dict(name="Mew ex 066/128", spr="mew", stamp=STAMP_R, text=490, icon=False, bar=bar(15, 470)),
    "me55-70": dict(name="Espeon ex 070/128", spr="espeon", stamp=STAMP_R, text=555, icon=True, bar=bar(15, 470)),
    "me55-71": dict(name="Sylveon ex 071/128", spr="sylveon", stamp=STAMP_R, text=555, icon=True, bar=bar(15, 470)),
    "me55-90": dict(name="Gengar ex 090/128", spr="gengar", stamp=STAMP_R, text=490, icon=True, S=13.9, W=44, H=37, bar=bar(15, 470)),
    "me55-102": dict(name="Jirachi ex 102/128", spr="jirachi", stamp=STAMP_R, text=520, icon=False, texture=False, bar=bar(15, 470)),
    "me55-109": dict(name="Salamence ex 109/128", spr="salamence", stamp=STAMP_R, text=520, icon=True, S=14.6, W=42,
                     bar=bar(15, 470)),
}
DEFAULT = dict(flip=False, x0=20, y0=90, S=15.3, W=40, H=33, off=None, dx=0, dy=0, tex_src=None, sat=1.25,
               bright=0.92, gamma=1.15, scene="", stars=[(8, 8, 3), (70, 8, 2), (72, 58, 3), (7, 56, 2)])


def ex_card(cid):
    k = {**DEFAULT, **CFG[cid]}
    x0, y0, S, W, H = k["x0"], k["y0"], k["S"], k["W"], k["H"]
    boxes = C.EDGES + ((0, 0, 652, 88), k["stamp"], k["bar"], (0, k["text"], 652, 914))
    if k["icon"]:
        boxes += (ICON,)
    rgb, _ = E.clean(cid, grow=5, boxes=boxes, tex_src=k["tex_src"], texture=k.get("texture", True))
    spr = Sprite(k["spr"], flip=k["flip"])
    c = P.Card(W, H)
    place(c, spr, cid, x0, y0, S, off=k["off"], dx=k["dx"], dy=k["dy"], margin=1)
    a = L.sample(rgb, x0, y0, S / 2, 2 * W, 2 * H, resample=L.Image.BOX)
    a = L.tone(a, sat=k["sat"], bright=k["bright"], gamma=k["gamma"])
    a = L.focus_halo(c, a, radius=3, dark=0.85, soft=1.0)
    _, lbl, pal = L.kmeans_q(a, 24, 0, ignore=c.fig_mask())
    base = pal[L.orphan_clean(lbl, 1)]
    FH, FW = c.FH, c.FW
    yy, xx = np.mgrid[0:FH, 0:FW]
    q = colour_blend(base, rainbow_rgb((xx + yy) / 30.0, s=0.6), 0.16)
    q = np.clip(q * 1.02 + 0.02, 0, 1)
    q = L.median_q(q, 72)
    d = c.dist()
    rim = (d > 0) & (d <= 1.01)
    q[rim] = q[rim] + (1 - q[rim]) * 0.45
    q = silver_frame(c, q)
    ring = c.meta["frame_ring"]
    seed = int(cid.split("-")[1])
    grain = [(x, y, ph) for (x, y, ph) in C.ex_grain(FW, FH, seed) if d[y, x] > 1.5 and not ring[y, x]]
    q_pre = q.copy()
    for x, y, ph in grain:
        q[y, x] = q[y, x] + (1 - q[y, x]) * C.GRAIN_LIFE[(15 + ph) % 6]
    c.bg = q
    c.bgq = L.to8(q)
    stars = [(x, y, st) for (x, y, st) in k["stars"] if x < FW and y < FH]
    for x, y, st in stars:
        L.sparkle(c, x, y, st, {"L": "#ffffff", "l": "#fff6c8", "j": "#9fd8ff"})
    scene = f", {k['scene']}" if k["scene"] else ""
    return meta(c, card=cid, label=f"Double Rare: {k['name']}{scene} (silver frame, sparkle-grain holo)",
                rarity="Double Rare", finish="ex holo: silver frame, fine sparkle-grain foil, sunpillar beam pair",
                variant="double-rare", anim="ex", ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S, stars=stars,
                grain=grain, q_pre=q_pre, frame="#c9d1da")


def builder(cid):
    return lambda: ex_card(cid)


C.BUILDERS.update({cid: builder(cid) for cid in CFG})
IDS = list(CFG)


def main(ids):
    sizes = {}
    for cid in ids:
        _, sizes[cid] = p30build.render(cid)
    p30anim.build(ids)
    for cid in ids:
        p30verify.check(cid)
    assert p30verify.fails == 0, f"{p30verify.fails} verification failures"
    (P.DATA / "sheets").mkdir(exist_ok=True)
    f = P.DATA / "work" / "dr_sizes.json"
    allsz = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    allsz.update(sizes)
    f.write_text(json.dumps(allsz, indent=1), encoding="utf-8")
    done = [c for c in IDS if c in allsz]
    p30sheet.sheet(done, P.DATA / "sheets" / f"{GROUP}.png", allsz)


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["masks"]:
        make_masks(args[1:])
    elif args[:1] == ["quick"]:                  # static renders only (iteration)
        for cid in args[1:] or IDS:
            p30build.render(cid)
    else:
        main([a for a in args if a in CFG] or IDS)
