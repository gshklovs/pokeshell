r"""30th Celebration (me55) full set, group "pikachu_rare": the 29 Pikachu Rares 24..52 (02/30 .. 30/30), each
built exactly the way the approved Pikachu 23 was (p30cards.pikachu): the card's own scene in the ME art window
with the real Pikachu masked out and filled, the colorscripts pikachu sprite (flipped only to face the way the
card does), the yellow bevel border, the fireworks-burst foil over art AND border (same lattice, seed 30), and
the `fireworks` animation. The 30th Pikachu stamp is not in the art window on the Pikachu Rares (the big
Pikachu "30" logo sits in the text half, which the text half replaces), so no stamp box is painted out.

Masks (masks/<id>.png, white = Pikachu): rembg run on the ART WINDOW crop (full-card rembg takes the whole card
on these busy scenes; cache work/rembg-<model>-win-<id>.png), inside a hand hull read off the scan, plus a
Pikachu-yellow colour rule inside hand polygons for the tails / ears the segmenters drop, plus hand polygons
where neither catches the body (yellow Pikachu on a yellow scene: 24, 48, 49, 52).

  ..\..\..\.venv\Scripts\python batch_pikachu_rare.py masks [n ...]    masks + work/pr-masks-*.png previews
  ..\..\..\.venv\Scripts\python batch_pikachu_rare.py build [n ...]    render + anim + verify (+ sheet when all)
"""
import json
import sys

import numpy as np
from PIL import Image
from scipy import ndimage
from skimage.color import rgb2hsv

import p30lib as P
from p30lib import E, L, Sprite
import p30cards as C
import p30masks as PM
import p30build
import p30anim
import p30verify
import p30sheet
from evcards import colour_blend, meta, place, rainbow_rgb, silver_frame

GROUP = "pikachu_rare"
NUMS = list(range(24, 53))
WIN = (52, 88, 606, 432)
MODELS = ("isnet-general-use", "u2net", "isnet-anime")
ALL = MODELS


def R(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


# ------------------------------------------------------------------ masks
# models: rembg (window crop) models unioned; hull: the rembg result is kept only inside it;
# yellow: polygons in which the Pikachu-yellow colour rule adds pixels; add: polygons added as they are;
# sub: polygons removed; keep: connected parts kept; close: closing iterations
TAIL49 = [(60, 185), (240, 195), (255, 250), (250, 320), (300, 375), (300, 410), (265, 432), (235, 432), (250, 390),
          (215, 340), (200, 330), (60, 330)]
H43 = [(170, 240), (300, 215), (320, 180), (400, 175), (410, 130), (460, 130), (450, 200), (470, 240), (640, 260),
       (640, 330), (440, 340), (350, 400), (170, 400)]
MASKS = {
    24: dict(models=ALL, hull=[(215, 96), (470, 96), (475, 300), (430, 380), (330, 392), (240, 330), (205, 230)]),
    25: dict(models=ALL, hull=R(235, 90, 455, 415), yellow=[[(400, 205), (492, 200), (492, 235), (462, 280), (450, 335),
                                                             (410, 335), (400, 280)]], sat=0.5),
    26: dict(models=("isnet-general-use", "u2net"), hull=R(52, 88, 470, 432),
             add=[[(465, 88), (540, 88), (590, 170), (606, 250), (606, 330), (570, 390), (530, 330), (490, 250),
                   (465, 200)]]),
    27: dict(models=("isnet-general-use", "u2net"), hull=R(190, 130, 570, 420)),
    28: dict(models=ALL, hull=R(125, 90, 420, 420), yellow=[R(360, 150, 525, 340)], sat=0.3,
             add=[[(400, 300), (430, 250), (470, 215), (510, 200), (512, 235), (470, 262), (445, 300), (430, 335),
                   (400, 335)]]),
    29: dict(models=("isnet-anime",), hull=R(180, 90, 560, 380), yellow=[R(80, 150, 560, 380)], dark=12,
             add=[[(375, 92), (430, 88), (430, 150), (385, 150)]]),
    30: dict(models=ALL, hull=R(90, 140, 470, 390)),
    31: dict(models=("isnet-general-use", "u2net"), hull=R(52, 88, 606, 432), yellow=[[(52, 88), (250, 88), (250, 140), (560, 140), (560, 432), (52, 432)]],
             sub=[R(470, 170, 606, 235), R(170, 88, 290, 140)]),
    32: dict(models=ALL, hull=[(320, 230), (370, 150), (430, 105), (510, 95), (548, 130), (548, 240), (500, 310),
                               (470, 340), (410, 340), (390, 285), (340, 270)], hue=(40, 85), sat=0.3,
             yellow=[[(320, 230), (370, 150), (430, 105), (510, 95), (548, 130), (548, 240), (500, 310), (470, 340),
                      (410, 340), (390, 285), (340, 270)]]),
    33: dict(models=ALL, hull=R(100, 88, 560, 432), yellow=[R(100, 88, 560, 432)], dark=10,
             add=[R(58, 195, 135, 245)]),                                  # the left ear's black tip
    34: dict(models=ALL, hull=R(70, 95, 470, 395), yellow=[R(70, 95, 470, 395)], dark=10),
    35: dict(models=ALL, hull=R(90, 95, 480, 400), yellow=[R(415, 95, 570, 410)]),
    36: dict(models=ALL, hull=R(60, 88, 530, 432), yellow=[R(60, 88, 530, 432)], hue=(32, 64)),
    37: dict(models=ALL, hull=R(160, 90, 570, 432), yellow=[R(380, 130, 570, 330)]),
    38: dict(models=ALL, hull=R(190, 95, 560, 380), yellow=[R(380, 95, 560, 240)]),
    39: dict(models=(), hull=R(0, 0, 1, 1), yellow=[R(370, 270, 465, 375)], hue=(25, 64), min_area=60),
    40: dict(models=ALL, hull=R(180, 90, 470, 380)),
    41: dict(models=ALL, hull=R(180, 100, 530, 410), yellow=[R(180, 100, 540, 410)]),
    42: dict(models=ALL, hull=R(130, 90, 570, 390), yellow=[R(130, 90, 570, 390)]),
    43: dict(models=(), hull=H43, yellow=[H43], dark=12, add=[R(470, 262, 545, 318)]),     # + right ear tip
    44: dict(models=("u2net",), hull=R(170, 120, 430, 380)),
    45: dict(models=ALL, hull=R(220, 110, 606, 380), yellow=[R(220, 110, 606, 380)]),
    46: dict(models=ALL, hull=R(180, 150, 540, 390), yellow=[R(180, 150, 540, 390)]),
    47: dict(models=ALL, hull=R(100, 88, 560, 432), yellow=[R(100, 88, 560, 395)]),
    48: dict(models=(), hull=R(0, 0, 1, 1), yellow=[R(52, 88, 606, 340)], min_area=2500, dark=6),
    49: dict(models=ALL, hull=R(52, 88, 606, 432), add=[TAIL49, [(300, 88), (372, 88), (372, 190), (310, 190)]]),
    50: dict(models=ALL, hull=R(130, 120, 520, 410), yellow=[R(130, 120, 520, 410)]),
    51: dict(models=ALL, hull=R(120, 100, 560, 420), add=[[(420, 175), (500, 160), (520, 190), (500, 240), (430, 245)]]),
    52: dict(models=(), hull=R(0, 0, 1, 1),
             add=[[(242, 100), (290, 140), (345, 115), (385, 160), (380, 230), (450, 300), (440, 340), (380, 345),
                   (320, 420), (250, 420), (200, 380), (150, 370), (52, 400), (52, 290), (100, 300), (140, 270),
                   (170, 200), (200, 150)]]),
}


def rembg_win(cid, model):
    """rembg on the art-window crop (cached per id + model), padded back to card size"""
    f = E.WORK / f"rembg-{model}-win-{cid}.png"
    if not f.exists():
        from rembg import new_session, remove
        im = Image.open(E.ref_path(cid)).convert("RGB")
        m = remove(im.crop(WIN), session=new_session(model), only_mask=True)
        full = Image.new("L", im.size, 0)
        full.paste(m, WIN[:2])
        full.save(f)
    return np.asarray(Image.open(f)) > 128


def yellow_rule(rgb, hue=(38, 64), sat=0.38, val=0.5):
    h = rgb2hsv(rgb)
    H, S, V = h[..., 0] * 360, h[..., 1], h[..., 2]
    return (H > hue[0]) & (H < hue[1]) & (S > sat) & (V > val)


def make_mask(n):
    """rembg (window crop) inside the hull, largest part(s); + Pikachu-yellow parts (>= min_area) inside the
    yellow polygons (tails / ears the segmenters drop); + hand polygons; + dark outline / ear tips next to it"""
    cid = f"me55-{n}"
    sp = MASKS[n]
    rgb = E.card_img(cid)
    sh = rgb.shape[:2]
    win = PM.rect(sh, *WIN)
    m = np.zeros(sh, bool)
    for mdl in sp.get("models", ()):
        m |= rembg_win(cid, mdl)
    m &= PM.poly(sh, sp["hull"]) & win
    if m.any():
        m = PM.largest(ndimage.binary_opening(m, iterations=1), sp.get("keep", 1))
    if sp.get("yellow"):
        y = yellow_rule(rgb, sp.get("hue", (38, 64)), sp.get("sat", 0.38))
        yp = np.zeros(sh, bool)
        for pg in sp["yellow"]:
            yp |= PM.poly(sh, pg)
        y = ndimage.binary_opening(y & yp & win, iterations=2)
        lbl, k = ndimage.label(y)
        if k:
            sz = ndimage.sum(y, lbl, range(1, k + 1))
            y = np.isin(lbl, 1 + np.nonzero(sz >= sp.get("min_area", 500))[0])
        m |= y
    for pg in sp.get("add", ()):
        m |= PM.poly(sh, pg)
    if sp.get("dark"):
        v = rgb.max(-1)
        m |= (v < 0.32) & ndimage.binary_dilation(m, iterations=sp["dark"]) & win
    for pg in sp.get("sub", ()):
        m &= ~PM.poly(sh, pg)
    m &= win
    m = ndimage.binary_closing(m, iterations=sp.get("close", 4)) & win
    holes = ndimage.binary_fill_holes(m) & ~m               # fill only small holes: a Pikachu touching the window
    lbl, k = ndimage.label(holes)                           # edge must not swallow the scene it encloses
    if k:
        sz = ndimage.sum(holes, lbl, range(1, k + 1))
        m |= np.isin(lbl, 1 + np.nonzero(sz < sp.get("max_hole", 3000))[0])
    return cid, m


def write_masks(ns):
    E.MASKS.mkdir(exist_ok=True)
    tiles = []
    for n in ns:
        cid, m = make_mask(n)
        Image.fromarray((m * 255).astype(np.uint8)).save(E.MASKS / f"{cid}.png")
        rgb = E.card_img(cid)
        edge = m ^ ndimage.binary_erosion(m, iterations=2)
        o = np.where(m[..., None], rgb * 0.75 + np.array([0.25, 0, 0]), rgb)
        o[edge] = (0, 0.4, 1)
        tiles.append(Image.fromarray(L.to8(o)).crop((40, 76, 618, 444)))
        print(cid, f"mask {m[88:432, 52:606].mean():.2f} of the window")
    for k in range(0, len(tiles), 4):
        sheet = Image.new("RGB", (2 * 578, 2 * 368))
        for i, t in enumerate(tiles[k:k + 4]):
            sheet.paste(t, ((i % 2) * 578, (i // 2) * 368))
        sheet.save(E.WORK / f"pr-masks-{ns[k]}.png")


# ------------------------------------------------------------------ builders
# flip: the vendor sprite looks to the viewer's left (head left, tail right); flipped when the card's Pikachu
# looks / turns right (or, facing front, carries its tail on the left). off / dx / dy: sprite placement.
CARDS = {
    24: dict(flip=True), 25: dict(), 26: dict(), 27: dict(), 28: dict(), 29: dict(flip=True), 30: dict(),
    31: dict(flip=True), 32: dict(), 33: dict(), 34: dict(flip=True), 35: dict(), 36: dict(flip=True), 37: dict(),
    38: dict(), 39: dict(off=(2, 4)),     # 39: the sprite steps left of the doorstep so the door still reads
    40: dict(), 41: dict(), 42: dict(), 43: dict(), 44: dict(), 45: dict(), 46: dict(),
    47: dict(flip=True), 48: dict(), 49: dict(), 50: dict(), 51: dict(), 52: dict(flip=True),
}


def auto_tex_src(cid, grow=6, w=140, h=95):
    """the window rectangle (w x h) with the least of the (grown) Pikachu mask in it: the texture source"""
    m = ndimage.binary_dilation(E.mask(cid), iterations=grow + 4).astype(float)
    ii = m.cumsum(0).cumsum(1)
    best = None
    x0, y0, x1, y1 = 60, 92, 600, 428
    for y in range(y0, y1 - h, 8):
        for x in range(x0, x1 - w, 8):
            s = ii[y + h, x + w] - ii[y, x + w] - ii[y + h, x] + ii[y, x]
            if best is None or s < best[0]:
                best = (s, (x, y, x + w, y + h))
    return best[1]


def make_builder(n):
    sp = CARDS[n]

    def build():
        cid = f"me55-{n}"
        card = P.card_json(cid)
        S, W, H = 15.6, 37, 24
        x0, y0 = 56 - S, 88 - S                          # the window + one sprite px all round (the border ring)
        tex = sp.get("tex_src") or auto_tex_src(cid)
        rgb = C.window_rgb(cid, grow=sp.get("grow", 6), tex_src=tex, texture=sp.get("texture", True))
        spr = Sprite("pikachu", flip=sp.get("flip", False))
        c = P.Card(W, H)
        place(c, spr, cid, x0, y0, S, off=sp.get("off"), dx=sp.get("dx", 0), dy=sp.get("dy", 0), margin=2)
        a = L.sample(rgb, x0, y0, S / 2, 2 * W, 2 * H, resample=L.Image.BOX)
        a = L.tone(a, sat=sp.get("sat", 1.1), bright=sp.get("bright", 1.0))
        a = L.focus_halo(c, a, radius=4, dark=0.84, soft=1.0)
        _, lbl, pal = L.kmeans_q(a, 14, n, ignore=c.fig_mask())
        base = pal[L.orphan_clean(lbl, 1)]
        FH, FW = c.FH, c.FW
        yy, xx = np.mgrid[0:FH, 0:FW]
        base = colour_blend(base, rainbow_rgb((xx + yy) / 60.0 + 0.1, s=0.5), 0.12)      # the foil's own sheen
        q = silver_frame(c, base, width=2, ramp_hex=C.YELLOW)                              # the yellow border
        ring = c.meta["frame_ring"]
        d = c.dist()
        rim = (d > 0) & (d <= 1.01)
        q[rim] = q[rim] + (1 - q[rim]) * 0.4
        bursts = C.fireworks(FW, FH)
        fig = c.fig_mask()
        q = L.median_q(q, 90)
        q_pre, skip = q.copy(), fig | (d <= 1.01)
        q = C.fireworks_paint(q, bursts, 15, skip)
        c.bg = q
        c.bgq = L.to8(q)
        k = int(n) - 22
        return meta(c, card=cid, label=f"Pikachu Rare: Pikachu {n:03d}/128 ({k:02d}/30), {card['artist']} "
                                        f"(fireworks holo, yellow border)",
                    rarity="Pikachu Rare", finish="Pikachu Rare: fireworks-burst holo over the art AND the yellow border",
                    variant="pikachu-rare", anim="fireworks", ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S,
                    bursts=bursts, q_pre=q_pre, skip=skip, ring=ring, frame="#f6d02c")
    build.__name__ = f"pikachu_{n}"
    return build


C.BUILDERS.update({f"me55-{n}": make_builder(n) for n in NUMS})


def main(argv):
    cmd = argv[0] if argv else "build"
    ns = [int(a) for a in argv[1:]] or NUMS
    if cmd == "masks":
        write_masks(ns)
        return
    ids = [f"me55-{n}" for n in ns]
    sizes = {}
    for cid in ids:
        _, sizes[cid] = p30build.render(cid)
    p30anim.build(ids)
    for cid in ids:
        p30verify.check(cid)
    print(f"{p30verify.fails} failures")
    assert p30verify.fails == 0
    (E.WORK / f"sizes-{GROUP}.json").write_text(json.dumps(sizes, indent=1), encoding="utf-8")
    out = P.DATA / "sheets" / f"{GROUP}.png" if ns == NUMS else E.WORK / f"sheet-{GROUP}-part.png"
    (P.DATA / "sheets").mkdir(exist_ok=True)
    p30sheet.sheet(ids, out, sizes)


if __name__ == "__main__":
    main(sys.argv[1:])
