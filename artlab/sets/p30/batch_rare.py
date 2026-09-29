r"""30th Celebration full set, group "rare" (15 cards): every Rare built as the approved Mew 65 was --
ME rares are holo, so the evs Rare Holo recipe (suite3 tiers.holo_scene) inside the ME art window ME_WIN,
the 30th stamp STAMP_REG painted out, anim "holo", frame #6ea5ff.

The Pokemon here are big legendaries that fill the window, so each card is sized to fit its sprite: the
scale S is the largest that fits the sprite (+1 px all round) in the window; the card is at most ~50 sprite
px (~100 cols) wide, so for tall sprites it takes a crop of the window, centred on the real Pokemon.

  ..\..\..\.venv\Scripts\python batch_rare.py [masks] [me55-12 ...]
"""
import json
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

import p30lib as P
from p30lib import E, L, Sprite
import p30cards
import p30masks as PM
import p30build
import p30anim
import p30verify
import p30sheet
from p30cards import ME_WIN, STAMP_REG, window_rgb, meta
from evcards import place

GROUP = "rare"
poly, rect, largest, rembg, hsv = PM.poly, PM.rect, PM.largest, PM.rembg, PM.hsv
STAGE1 = ((0, 40, 300, 106), (0, 40, 112, 152))      # the Stage 1 "evolves from" bar + icon over the window
# everything outside the art window is unknown too: the fill's mirrored texture must never reach the card's
# name, frame or flavour text (these Pokemon touch the window edges; Mew 65 did not)
OUTSIDE = ((0, 0, 652, ME_WIN[1]), (0, ME_WIN[3], 652, 914), (0, 0, ME_WIN[0], 914), (ME_WIN[2], 0, 652, 914))


# ============================================================ masks (card px, white = the real Pokemon)
def win(sh):
    a, b, c, d = ME_WIN
    return rect(sh, a, b, c, d) & ~rect(sh, *STAMP_REG)


def fin(m, close=3):
    m = ndimage.binary_closing(m, iterations=close)
    return ndimage.binary_fill_holes(m)


def m_seg(cid, models=("isnet-general-use",), keep=1, close=3, extra=None, cut=None):
    """rembg (union of models) inside the window, largest parts"""
    sh = E.card_img(cid).shape[:2]
    m = np.zeros(sh, bool)
    for mo in models:
        m |= rembg(cid, mo)
    m &= win(sh)
    if cut is not None:
        m &= ~cut
    m = ndimage.binary_opening(m, iterations=1)
    if extra is not None:
        m |= extra & win(sh)
    return fin(largest(m, keep), close)


def ho_oh():
    """isnet-general-use has the body, u2net the full wings with their green tips"""
    return m_seg("me55-12", ("isnet-general-use", "u2net"), keep=1, close=4)


def reshiram():
    """segmenters take the whole window: Reshiram is the pale white-grey fur; the red flame streaks and
    the orange cloud (top right) are the scene"""
    cid = "me55-14"
    rgb, h, s, v = hsv(cid)
    sh = rgb.shape[:2]
    hull = poly(sh, [(52, 88), (360, 88), (475, 96), (478, 175), (445, 212), (560, 255), (606, 290), (606, 365),
                     (520, 385), (470, 432), (52, 432)])
    pale = (s < 0.3) & (v > 0.5)
    arm = poly(sh, [(440, 150), (520, 150), (525, 250), (440, 250)])       # his raised claw by the cloud
    m = (hull | arm) & pale & win(sh)
    m = ndimage.binary_opening(m, iterations=1)
    m = ndimage.binary_closing(m, iterations=6)
    return fin(largest(m, 3), 2)


def kyogre():
    cid = "me55-19"
    sh = E.card_img(cid).shape[:2]
    rgb, h, s, v = hsv(cid)
    # the tail fin arcs off to the upper right (u2net has it, with spray)
    tail = poly(sh, [(470, 150), (560, 88), (606, 88), (606, 200), (560, 300), (500, 330), (470, 300)])
    blue = (h > 190) & (h < 240) & (s > 0.35) & (v > 0.25) & (v < 0.85)
    ex = tail & ndimage.binary_closing(rembg(cid, "u2net") & blue, iterations=4)
    # isnet only has the jaw rim: the body is his hull (read off grid_19)
    fin_l = poly(sh, [(52, 188), (110, 183), (182, 215), (212, 280), (202, 322), (140, 302), (52, 282)])
    body = fin_l | poly(sh, [(185, 150), (240, 92), (330, 88), (385, 108), (415, 160), (445, 240), (475, 300), (435, 348),
                     (300, 362), (200, 348), (168, 282), (168, 200)])
    return m_seg(cid, keep=2, close=4, extra=ex | body)


def palkia():
    """all segmenters miss Palkia in the grey dust: his hull (read off grid_20)"""
    cid = "me55-20"
    sh = E.card_img(cid).shape[:2]
    hull = poly(sh, [(62, 100), (120, 88), (560, 88), (596, 140), (606, 240), (580, 300), (520, 330), (470, 372),
                     (420, 398), (300, 395), (240, 350), (190, 280), (130, 220), (80, 180), (62, 140)])
    return hull & win(sh)


def zekrom():
    """segmenters take the whole window: Zekrom's hull, body and both wings (read off grid_56)"""
    cid = "me55-56"
    sh = E.card_img(cid).shape[:2]
    hull = poly(sh, [(88, 210), (200, 160), (240, 88), (320, 88), (360, 110), (420, 92), (500, 92), (560, 88), (606, 95),
                     (606, 330), (560, 380), (500, 432), (380, 432), (320, 390), (250, 345), (140, 345), (88, 305)])
    return hull & win(sh)


def mewtwo():
    """isnet-general-use, plus the top of his head it clips"""
    cid = "me55-63"
    sh = E.card_img(cid).shape[:2]
    head = poly(sh, [(215, 88), (305, 88), (322, 130), (302, 190), (230, 190), (208, 140)])
    return m_seg(cid, keep=1, close=4, extra=head)


def xerneas():
    """isnet-general-use has the body; the rainbow antler rays and the tail are his too (hulls, grid_76)"""
    cid = "me55-76"
    sh = E.card_img(cid).shape[:2]
    antlers = poly(sh, [(250, 150), (290, 88), (560, 88), (606, 110), (600, 200), (520, 222), (430, 242), (330, 232),
                        (270, 200)])
    tail = poly(sh, [(360, 298), (420, 288), (505, 298), (512, 342), (450, 372), (380, 362)])
    return m_seg(cid, keep=1, close=4, extra=antlers | tail)


def lunala():
    """segmenters take everything or nothing: Lunala's wing hull (read off grid_80)"""
    cid = "me55-80"
    sh = E.card_img(cid).shape[:2]
    hull = poly(sh, [(55, 105), (120, 100), (200, 140), (270, 190), (335, 215), (360, 170), (375, 120), (405, 98),
                     (440, 98), (470, 130), (490, 175), (530, 150), (560, 100), (580, 88), (606, 150), (600, 280),
                     (560, 320), (500, 330), (450, 310), (430, 380), (440, 432), (360, 432), (385, 345), (360, 300),
                     (290, 290), (210, 275), (150, 255), (90, 225), (55, 190)])
    arcs = rect(sh, 52, 100, 112, 332) | rect(sh, 528, 88, 606, 352)          # the gold wing crescents
    claws = poly(sh, [(180, 130), (300, 120), (385, 170), (385, 252), (250, 252), (200, 212)])
    claws |= rect(sh, 260, 238, 500, 336) | rect(sh, 320, 360, 440, 432)     # lower wing membrane, foot crescent
    return (hull | arcs | claws) & win(sh) & ~rect(sh, *STAGE1[0]) & ~rect(sh, *STAGE1[1])


def groudon():
    """segmenters take the whole window: Groudon's hull (read off grid_82)"""
    cid = "me55-82"
    sh = E.card_img(cid).shape[:2]
    hull = poly(sh, [(78, 285), (125, 240), (180, 205), (200, 150), (250, 120), (300, 105), (380, 88), (470, 92),
                     (512, 140), (530, 210), (520, 285), (470, 330), (430, 380), (410, 432), (78, 432)])
    return hull & win(sh)


def yveltal():
    """isnet-general-use, plus his right wing tip and talons by the swirl"""
    cid = "me55-100"
    sh = E.card_img(cid).shape[:2]
    tip = poly(sh, [(470, 150), (606, 120), (606, 362), (480, 362)])
    return m_seg(cid, keep=1, close=4, extra=tip)


def dialga():
    """isnet-general-use misses his white spikes and fins: rembg plus his hull (grid_103)"""
    cid = "me55-103"
    sh = E.card_img(cid).shape[:2]
    hull = poly(sh, [(80, 100), (160, 92), (240, 120), (270, 108), (340, 88), (430, 100), (520, 128), (548, 230),
                     (560, 280), (560, 380), (470, 432), (180, 432), (215, 330), (185, 280), (160, 210), (100, 160)])
    return m_seg(cid, keep=2, close=4, extra=hull)


def solgaleo():
    cid = "me55-105"
    sh = E.card_img(cid).shape[:2]
    cut = rect(sh, *STAGE1[0]) | rect(sh, *STAGE1[1])
    return m_seg(cid, ("isnet-general-use", "isnet-anime"), keep=1, close=4, cut=cut)


def zacian():
    """isnet-general-use, plus the sword blade and the left half of the red mane, and his crown tips"""
    cid = "me55-106"
    sh = E.card_img(cid).shape[:2]
    sword = poly(sh, [(52, 225), (110, 180), (200, 170), (270, 180), (292, 262), (200, 287), (110, 287), (52, 267)])
    crown = poly(sh, [(220, 88), (380, 88), (372, 152), (228, 152)])
    return m_seg(cid, keep=1, close=4, extra=sword | crown)


def zamazenta():
    return m_seg("me55-107", ("isnet-general-use", "isnet-anime"), keep=1, close=4)


def lugia():
    """segmenters take the whole window (the water swirls are as pale as he is): Lugia's hull"""
    cid = "me55-121"
    sh = E.card_img(cid).shape[:2]
    hull = poly(sh, [(52, 150), (110, 110), (200, 95), (290, 88), (440, 88), (540, 105), (600, 170), (590, 230),
                     (540, 270), (480, 300), (460, 360), (440, 432), (230, 432), (200, 360), (150, 300), (90, 250),
                     (52, 220)])
    return hull & win(sh)


MASKS = {"me55-12": ho_oh, "me55-14": reshiram, "me55-19": kyogre, "me55-20": palkia, "me55-56": zekrom,
         "me55-63": mewtwo, "me55-76": xerneas, "me55-80": lunala, "me55-82": groudon, "me55-100": yveltal,
         "me55-103": dialga, "me55-105": solgaleo, "me55-106": zacian, "me55-107": zamazenta, "me55-121": lugia}


def fills(ids):
    """work/fills-rare.png: each card's cleaned window (the scene the holo is sampled from)"""
    tiles = []
    for cid in ids:
        name, flip, tex, boxes, _ = SPEC[cid]
        rgb = window_rgb(cid, boxes=(STAMP_REG,) + OUTSIDE + tuple(boxes), grow=6, tex_src=tex)
        tiles.append(Image.fromarray(L.to8(rgb[ME_WIN[1]:ME_WIN[3], ME_WIN[0]:ME_WIN[2]])).resize((400, 248)))
    sheet = Image.new("RGB", (2000, 250 * ((len(tiles) + 4) // 5)))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % 5) * 400, (i // 5) * 250))
    sheet.save(E.WORK / "fills-rare.png")


def make_masks(ids):
    E.MASKS.mkdir(exist_ok=True)
    tiles = []
    for cid in ids:
        m = MASKS[cid]()
        Image.fromarray((m * 255).astype(np.uint8)).save(E.MASKS / f"{cid}.png")
        rgb = E.card_img(cid)
        o = np.where(m[..., None], rgb, rgb * 0.25 + np.array([0, 0.3, 0]))[40:480]
        tiles.append(Image.fromarray(L.to8(o)).resize((400, 270)))
        ys, xs = np.nonzero(m)
        print(cid, "mask bbox", xs.min(), ys.min(), xs.max(), ys.max(), f"{m.mean():.2f}")
    sheet = Image.new("RGB", (2000, 270 * ((len(tiles) + 4) // 5)))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % 5) * 400, (i // 5) * 270))
    sheet.save(E.WORK / "masks-rare.png")


# ============================================================ builders (the Mew 65 recipe)
# id: sprite, flip, tex_src (a clean scene patch), extra boxes, (dx, dy) sprite nudge, seed
SPEC = {
    "me55-12": ("ho-oh", True, (60, 330, 160, 425), (), (0, 0)),
    "me55-14": ("reshiram", True, (470, 110, 600, 200), (), (0, 0)),
    "me55-19": ("kyogre", False, (60, 100, 200, 200), (), (0, 0)),
    "me55-20": ("palkia", False, (60, 330, 220, 425), (), (0, 0)),
    "me55-56": ("zekrom", False, (60, 100, 300, 180), (), (0, 0)),
    "me55-63": ("mewtwo", False, (60, 100, 200, 180), (), (0, 0)),
    "me55-76": ("xerneas", False, (400, 300, 590, 330), (), (0, 0)),
    "me55-80": ("lunala", False, (60, 300, 200, 425), STAGE1, (0, 0)),
    "me55-82": ("groudon", True, (540, 120, 600, 330), (), (0, 0)),
    "me55-100": ("yveltal", False, (60, 330, 250, 425), (), (0, 0)),
    "me55-103": ("dialga", False, (60, 330, 200, 425), (), (0, 0)),
    "me55-105": ("solgaleo", False, (450, 110, 600, 250), STAGE1, (0, 0)),
    "me55-106": ("zacian-crowned", False, (60, 330, 200, 425), (), (0, 0)),
    "me55-107": ("zamazenta-crowned", True, (480, 100, 600, 300), (), (0, 0)),
    "me55-121": ("lugia", False, (60, 330, 200, 425), (), (0, 0)),
}
MAXW = 50                                     # sprite px (~100 cols); wider sprites get sprite w + 2


def layout(cid, spr):
    """(x0, y0, S, W, H): the largest scale that fits the sprite (+1 px all round) in the window; a crop of
    the window, centred on the real Pokemon, when the card would be wider than MAXW"""
    a, b, c, d = ME_WIN
    ww, wh = c - a, d - b
    S = min(wh / (spr.h + 2), ww / (spr.w + 2))
    W = min(int(ww / S), max(MAXW, spr.w + 2))
    H = int(round(wh / S))
    m = E.mask(cid)
    ys, xs = np.nonzero(m)
    cx = (xs.min() + xs.max()) / 2
    x0 = float(np.clip(cx - W * S / 2, a, c - W * S))
    return round(x0, 1), b, round(S, 2), W, H


def make(cid):
    import tiers as s3t
    name, flip, tex, boxes, (dx, dy) = SPEC[cid]
    card = P.card_json(cid)
    spr = Sprite(name, flip=flip)
    x0, y0, S, W, H = layout(cid, spr)
    A, B = E.anchor(cid, x0, y0, S, spr, dx, dy)
    A = max(1, min(W - spr.w - 1, A))
    B = max(1, min(H - spr.h - 1, B))
    rgb = window_rgb(cid, boxes=(STAMP_REG,) + OUTSIDE + tuple(boxes), grow=6, tex_src=tex)
    FW, FH = 2 * W, 2 * H
    sparkles = [(5, 5, 3), (FW - 6, 6, 2), (FW - 6, FH - 6, 3), (4, FH - 8, 2)]
    seed = int(card["number"])
    c = s3t.holo_scene(spr, cid, None, x0, y0, S, W, H, cid, "", off=(A, B), rgb=rgb, ncol=12, foil=0.22,
                       bright=1.0, sparkles=sparkles, seed=seed)
    num = f"{int(card['number']):03d}/{card['set']['printedTotal']}"
    return meta(c, card=cid, label=f"Rare: {card['name']} {num} (ME rare = holo in the art box)",
                rarity="Rare", finish="ME rare holo: rainbow foil bands + starlight inside the art box (evs Rare Holo)",
                variant="rare", anim="holo", ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S, frame="#6ea5ff")


IDS = list(SPEC)
p30cards.BUILDERS.update({cid: (lambda cid=cid: make(cid)) for cid in IDS})


def main(argv):
    ids = [a for a in argv if a in SPEC] or IDS
    if "masks" in argv:
        make_masks(ids)
    sizes = {}
    for cid in ids:
        _, sizes[cid] = p30build.render(cid)
    (P.DATA / "sheets" / f"{GROUP}-sizes.json" if ids == IDS else E.WORK / "sizes-rare.json").write_text(json.dumps(sizes, indent=1), encoding="utf-8")
    if "noanim" in argv:
        p30sheet.sheet(ids, E.WORK / "sheet-rare-part.png", sizes)
        return
    p30anim.build(ids)
    for cid in ids:
        p30verify.check(cid)
    print(f"{p30verify.fails} failures")
    assert p30verify.fails == 0
    out = P.DATA / "sheets" / f"{GROUP}.png" if ids == IDS else E.WORK / "sheet-rare-part.png"
    out.parent.mkdir(exist_ok=True)
    p30sheet.sheet(ids, out, sizes)


if __name__ == "__main__":
    main(sys.argv[1:])
