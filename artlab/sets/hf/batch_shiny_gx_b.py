r"""Group "shiny_gx_b" of Hidden Fates' Shiny Vault (sma-SV64 .. SV80): the Rare Shiny GX cards, built exactly like
the approved Charizard-GX SV49 (hfcards.charizard_svgx): the SHINY colorscripts sprite (flip only), full-art crop
from y 92 down to where the first ability / attack starts (HB.layout_full), the card's white ground painted out with
a smooth membrane (texture=False) and re-cut as the dark vault foil with the etched texture, silver frame, flares.

Mask: rembg (union of models) over the full art, minus the stage icon / evolves bar / Ultra Beast banner, plus
HM.outline_halo so the thick coloured outline the real Pokemon is drawn with leaves no ghost.
Boxes: the frame edges, TOP, ICON + EVOLVES (Stage 1 / 2), the Ultra Beast banner (UBs), and (0, text_y) down.

  ..\..\..\.venv\Scripts\python batch_shiny_gx_b.py [masks|build|all|sheet] [ids]
"""
import sys

import numpy as np
from scipy import ndimage

from hflib import E, ShinySprite
import hfcards as C
import hfmasks as HM
import hfbatch as HB

GROUP = "shiny_gx_b"
PLAN = HB.plan(GROUP)

# per card, read off the scans (card px, 734 x 1024).
#   flip: the vendor sprite faces the other way from the real card
#   text_y: where the first ability / attack starts
#   stage: Stage 1 / 2 (ICON + EVOLVES boxed); ub: the Ultra Beast banner rect
#   models: rembg models unioned for the mask; reach: outline_halo reach
CFG = {
    "sma-SV64": dict(flip=False, text_y=528, stage=True),              # Lucario, head in profile to the right (as vendor)
    "sma-SV65": dict(flip=False, text_y=540),                          # Zygarde Complete, frontal (ambiguous)
    "sma-SV66": dict(flip=True, text_y=488, stage=True,                # Lycanroc Midnight, leans in to the left
                     cut=[[(0, 92), (140, 92), (140, 500), (0, 500)]]),
    "sma-SV67": dict(flip=True, text_y=520, stage=True),               # Lycanroc Dusk, head to the right
    "sma-SV68": dict(flip=False, text_y=478, ub=(440, 118, 706, 160)),  # Buzzwole, frontal flex (ambiguous)
    "sma-SV69": dict(flip=False, text_y=448, stage=True),              # Umbreon, faces left (as vendor)
    "sma-SV70": dict(flip=False, text_y=452),                          # Darkrai, faces left (as vendor)
    "sma-SV71": dict(flip=False, text_y=545, ub=(440, 118, 706, 164)),  # Guzzlord, frontal (ambiguous)
    "sma-SV72": dict(flip=False, text_y=438, stage=True,               # Scizor, faces left (as vendor); pale wings
                     extra=[[(460, 200), (560, 110), (706, 92), (706, 150), (650, 250), (580, 330), (500, 320)],
                            [(130, 92), (330, 92), (320, 160), (250, 170), (170, 130)]]),
    "sma-SV73": dict(flip=False, text_y=455, ub=(440, 118, 706, 160),  # Kartana, frontal (ambiguous); pale blades
                     extra=[[(95, 260), (200, 190), (250, 92), (440, 92), (440, 164), (706, 164), (706, 330),
                             (560, 360), (460, 440), (300, 455), (95, 455)]]),
    "sma-SV74": dict(flip=False, text_y=540, ub=(436, 118, 706, 164),  # Stakataka, frontal (ambiguous)
                     cut=[[(0, 92), (168, 92), (168, 300), (140, 335), (0, 322)],
                          [(628, 164), (734, 164), (734, 335), (628, 335)]]),
    "sma-SV75": dict(flip=False, text_y=490, stage=True),              # Gardevoir, faces right (as vendor)
    "sma-SV76": dict(flip=False, text_y=538, stage=True),              # Sylveon, faces left (as vendor)
    "sma-SV77": dict(flip=True, text_y=448, stage=True,                # Altaria, head right of the cloud body; crest
                     extra=[[(95, 165), (180, 118), (300, 95), (430, 92), (430, 112), (300, 128), (200, 160),
                             (130, 200), (95, 195)]]),
    "sma-SV78": dict(flip=True, text_y=494, stage=True),               # Noivern, head turned to the right
    "sma-SV79": dict(flip=False, text_y=522, stage=True,               # Silvally, head left, tail right (as vendor)
                     extra=[[(250, 170), (330, 120), (420, 92), (560, 92), (620, 250), (560, 330), (470, 420),
                             (440, 522), (170, 522), (150, 400), (200, 330), (250, 250)]]),
    "sma-SV80": dict(flip=False, text_y=478,                           # Drampa, head top-left (as vendor); cream body
                     extra=[[(520, 330), (600, 295), (690, 325), (708, 400), (708, 478), (520, 478)]]),
}
DEFAULT_MODELS = ("isnet-general-use",)


def cfg(cid):
    return {"models": DEFAULT_MODELS, "reach": 10, "close": 5, "stage": False, "ub": None, "dx": 0, "dy": 0,
            "extra": None, "cut": None, "keep": 12, **CFG[cid]}


def boxes_of(cid):
    k = cfg(cid)
    b = C.EDGES + (C.TOP,)
    if k["stage"]:
        b += (HM.ICON, HM.EVOLVES)
    if k["ub"]:
        b += (k["ub"],)
    return b + ((0, k["text_y"], 734, 1024),)


RED_UB = ("sma-SV68", "sma-SV71", "sma-SV73", "sma-SV74")   # the Ultra Beasts are drawn with a red outline


def outline_ink(cid):
    """the thick coloured outline the real Pokemon is drawn with: cyan on most cards, red on the Ultra Beasts
    (the printed sparkle stars are gold, hue 30-60, so they stay out)"""
    rgb, h, s, v = HM.hsv(cid)
    if cid in RED_UB:
        return ((h < 16) | (h > 335)) & (s > 0.45) & (v > 0.35)
    return (h > 180) & (h < 215) & (s > 0.4) & (v > 0.55)


def silhouette(cid, win, base, min_area=6000):
    """the Pokemon on the white card: every coloured (not white) part big enough or rembg (`base`) agrees with, plus
    its outline; then the white parts it encloses (the window's edges close it where it runs off the art), kept
    where rembg mostly agrees or they are mostly coloured -- the white ground and its gold stars drop out"""
    rgb, h, s, v = HM.hsv(cid)
    sh = rgb.shape[:2]
    w = HM.rect(sh, *win)
    paper = (v > 0.88) & (s < 0.15)
    white = paper | ((v > 0.75) & (h > 25) & (h < 65))          # the ground plus its gold sparkle stars
    fg = ndimage.binary_opening(~paper & w, iterations=2)
    lab, n = ndimage.label(fg)
    idx = range(1, n + 1)
    area = ndimage.sum(np.ones(sh), lab, idx)
    cov = ndimage.sum(base, lab, idx) / np.maximum(area, 1)
    keep = np.zeros(n + 1, bool)
    keep[1:] = (area > min_area) | ((cov > 0.3) & (area > 300))
    m0 = keep[lab] | (outline_ink(cid) & w)
    m0 = ndimage.binary_closing(m0, iterations=3) & w
    edge = w & ~ndimage.binary_erosion(w, iterations=2)
    inner = ndimage.binary_fill_holes(m0 | edge) & w & ~m0 & ~edge
    lab, n = ndimage.label(inner)
    idx = range(1, n + 1)
    area = ndimage.sum(np.ones(sh), lab, idx)
    cov = ndimage.sum(base, lab, idx) / np.maximum(area, 1)
    wf = ndimage.sum(white, lab, idx) / np.maximum(area, 1)
    touch = np.zeros(n + 1, bool)                              # runs out to the window's edge (open ground)
    touch[np.unique(lab[ndimage.binary_dilation(edge, iterations=2) & (lab > 0)])] = True
    keep = np.zeros(n + 1, bool)
    keep[1:] = (cov > 0.5) | (wf < 0.5) | (area < 400) | ~touch[1:]
    return m0 | keep[lab]


def make_mask(cid):
    k = cfg(cid)
    sh = E.card_img(cid).shape[:2]
    cut = HM.rect(sh, *C.TOP)
    if k["stage"]:
        cut |= HM.rect(sh, *HM.ICON) | HM.rect(sh, *HM.EVOLVES)
    if k["ub"]:
        cut |= HM.rect(sh, *k["ub"])
    for pts in k["cut"] or ():
        cut |= HM.poly(sh, pts)
    win = (0, 92, 734, k["text_y"])
    w = HM.rect(sh, *win) & ~cut
    base = np.zeros(sh, bool)
    for mo in k["models"]:
        base |= HM.rembg(cid, mo)
    base &= w
    m = silhouette(cid, (26, 92, 708, k["text_y"]), base) & w
    for pts in k["extra"] or ():
        m |= HM.poly(sh, pts) & w
    m = ndimage.binary_opening(m, iterations=2)
    m = HM.fin(m, k["close"], k["keep"])
    m |= ndimage.binary_dilation(ndimage.binary_opening(outline_ink(cid) & w, iterations=1), iterations=3)
    m = HM.outline_halo(cid, m, reach=k["reach"])
    return m & w


MASKS = {cid: (lambda cid=cid: make_mask(cid)) for cid in PLAN}


def make(cid):
    k = cfg(cid)
    spr = ShinySprite(PLAN[cid]["sprite"], k["flip"])
    x0, y0, S, W, H = HB.layout_full(cid, spr, top=92, text_y=k["text_y"])
    return C.vault_gx_card(cid, spr, x0, y0, S, W, H, boxes_of(cid), texture=False, dx=k["dx"], dy=k["dy"])


BUILDERS = {cid: (lambda cid=cid: make(cid)) for cid in PLAN}

if __name__ == "__main__":
    HB.run(GROUP, BUILDERS, MASKS, sys.argv[1:])
