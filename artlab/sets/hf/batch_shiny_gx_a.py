r"""Group "shiny_gx_a" of Hidden Fates' Shiny Vault (sma): 17 Rare Shiny GX cards (SV46 .. SV63), built exactly like
the approved Charizard-GX SV49 (hfcards.charizard_svgx): the SHINY sprite, full-art crop (HB.layout_full from y 92
to the first ability / attack), vault foil with the etched texture, silver frame, star flares; texture=False (the
white ground). Mask = a colour rule (not white, not star-gold) OR rembg isnet-general-use (u2net takes the whole
white card here), + HM.outline_halo so the thick coloured outline leaves no ghost, + every printed star the hole or a
box cuts (else a smudge). Crop / placement are read off the Pokemon's own mask (layout(), HB.layout_full's maths). Boxes: frame edges, TOP, ICON / EVOLVES (Stage 1 / 2), the Ultra Beast banner (UBs), everything from text_y.

  ..\..\..\.venv\Scripts\python batch_shiny_gx_a.py [masks|build|all|sheet] [ids]
"""
import sys

import numpy as np
from scipy import ndimage

import hflib as P
from hflib import E, ShinySprite
import hfcards as C
import hfmasks as HM
import hfbatch as HB

GROUP = "shiny_gx_a"
PLAN = HB.plan(GROUP)
FRAME_IN = ((28, 0, 40, 1024), (694, 0, 706, 1024))   # the frame's inner silver shading (else a grey bar in the fill)
GROW = 14                               # mask growth: swallows the half-stars cut by the outline (read as smudges)
UB = (425, 114, 712, 162)               # the "Ultra Beast" banner at the top right (read off grid_SV58)

# flip: the real card faces the other way from the vendor sprite (vendor sprites face left).
# text_y: where the first ability / attack starts (read off the scans).
CFG = {
    "sma-SV46": dict(flip=False, text_y=520, close_top=True),             # Leafeon: head left, looks at us
    "sma-SV47": dict(flip=False, text_y=550),               # Decidueye: near-frontal, looks left
    "sma-SV48": dict(flip=False, text_y=495),               # Golisopod: frontal, head down
    "sma-SV50": dict(flip=True, text_y=520),                # Ho-Oh: faces right
    "sma-SV51": dict(flip=False, text_y=515),               # Reshiram: head top right, snout up-left
    "sma-SV52": dict(flip=False, text_y=488),               # Turtonator: head right (vendor already right)
    "sma-SV53": dict(flip=True, text_y=485),                # Alolan Ninetales: head left, snout right
    "sma-SV54": dict(flip=False, text_y=492),               # Articuno: beak left
    "sma-SV55": dict(flip=True, text_y=425),                # Glaceon: body left, head right
    "sma-SV56": dict(flip=False, text_y=470),               # Greninja: near-frontal, looks left
    "sma-SV57": dict(flip=True, text_y=490),                # Electrode: face on the right of the ball
    "sma-SV58": dict(flip=False, text_y=488, ub=True),      # Xurkitree: frontal
    "sma-SV59": dict(flip=True, text_y=510),                # Mewtwo: faces right
    "sma-SV60": dict(flip=True, text_y=510),                # Espeon: faces right
    "sma-SV61": dict(flip=False, text_y=440),               # Banette: eye + grin to the left
    "sma-SV62": dict(flip=False, text_y=458, ub=True),      # Nihilego: frontal
    "sma-SV63": dict(flip=False, text_y=515, ub=True),      # Naganadel: head looks down-left
}

STAGE = {cid for cid in PLAN if any(s.startswith("Stage") for s in P.card_json(cid).get("subtypes", []))}


def boxes(cid):
    b = C.EDGES + (C.TOP,) + FRAME_IN
    if cid in STAGE:
        b += (HM.ICON, HM.EVOLVES)
    if CFG[cid].get("ub"):
        b += (UB,)
    return b + ((0, CFG[cid]["text_y"], 734, 1024),)


def art_region(cid):
    """card px where the Pokemon can show: inside the frame, y 92 .. text_y + 30, minus TOP / ICON / EVOLVES / UB"""
    sh = E.card_img(cid).shape[:2]
    art = HM.rect(sh, 28, 92, 706, CFG[cid]["text_y"] + 30)
    for bx in boxes(cid)[:-1]:
        art &= ~HM.rect(sh, *bx)
    return art


def lid(cid):
    """the art region's top edge and the box outlines as a 3 px line: closes a Pokemon that runs behind the name
    bar / stage icon, so its (near-white) inside fills"""
    sh = E.card_img(cid).shape[:2]
    m = np.zeros(sh, bool)
    m[92:95, 28:706] = True
    for (a, b, c, d) in [bx for bx in boxes(cid)[:-1] if bx not in C.EDGES + FRAME_IN]:
        t = np.zeros(sh, bool)
        t[max(b - 3, 0):d + 3, max(a - 3, 0):c + 3] = True
        t[b:d, a:c] = False
        m |= t
    return m


def make_mask(cid, swallow=True):
    """rembg alone takes the whole white card (u2net) or misses pale bodies, so the Pokemon is read by colour: the
    card ground is pure white with pale-gold sparkle stars, the Pokemon is everything not white and not star-gold
    (inside its thick coloured outline), closed + filled, specks < 2500 px dropped; OR isnet-general-use; then
    HM.outline_halo so no outline ghost is left"""
    cfg = CFG[cid]
    rgb, h, s, v = HM.hsv(cid)
    art = art_region(cid)
    star = (h > 28) & (h < 70) & (s < cfg.get("star_s", 0.55)) & (v > 0.8)
    m = ((s > 0.06) | (v < 0.94)) & ~star & art
    m = ndimage.binary_opening(m, iterations=1)
    m = ndimage.binary_closing(m, iterations=4)
    if cfg.get("close_top"):
        m = ndimage.binary_fill_holes(m | (lid(cid) & ndimage.binary_dilation(art, iterations=4))) & art
    m = ndimage.binary_fill_holes(m)
    lab, n = ndimage.label(m)
    sz = ndimage.sum(m, lab, range(1, n + 1))
    m = np.isin(lab, [i + 1 for i, z in enumerate(sz) if z >= cfg.get("speck", 2500)])
    m |= HM.rembg(cid, "isnet-general-use") & art
    if "add" in cfg:
        m |= HM.poly(m.shape, cfg["add"])
    m = ndimage.binary_fill_holes(ndimage.binary_closing(m, iterations=3)) & art
    m = HM.outline_halo(cid, m, reach=cfg.get("reach", 10)) & art
    return swallow_cut_stars(cid, m, art) if swallow else m


def swallow_cut_stars(cid, m, art, near=GROW + 2):
    """a printed sparkle star cut by the (grown) hole reads as a smudge in the vault foil: add every star / glow
    blob that reaches within `near` px of the Pokemon (or is cut by a box / the frame) to the mask, whole; isolated
    stars stay (embossed)"""
    rgb, h, s, v = HM.hsv(cid)
    ink = ((s > 0.04) | (v < 0.97)) & art & ~m
    lab, n = ndimage.label(ndimage.binary_dilation(ink, iterations=2) & art)
    seed = ndimage.binary_dilation(m, iterations=near) | ndimage.binary_dilation(~art, iterations=4)
    hit = np.unique(lab[seed & (lab > 0)])
    return m | ndimage.binary_dilation(np.isin(lab, hit[hit > 0]), iterations=2) & art


MASKS = {cid: (lambda cid=cid: make_mask(cid)) for cid in PLAN}


def layout(cid, spr, core):
    """HB.layout_full's crop and E.anchor's placement, read off the Pokemon's own (core) mask rather than the saved
    mask, which also holds the swallowed stars (a local copy of the shared helpers: same maths)"""
    ty = CFG[cid]["text_y"]
    top, left, right, pad = 92, 20, 714, 2
    wh, ww = ty - top, right - left
    H = spr.h + 2 * pad
    S = wh / H
    W = min(int(ww / S), max(HB.MAXW, spr.w + 2 * pad))
    if W < spr.w + 2 * pad:
        W = spr.w + 2 * pad
        S = ww / W
        H = int(wh / S)
    ys, xs = np.nonzero(core)
    cx = (xs.min() + xs.max()) / 2
    x0 = round(float(np.clip(cx - W * S / 2, left, right - W * S)), 1)
    S = round(S, 2)
    off = (round((cx - x0) / S - spr.w / 2) + CFG[cid].get("dx", 0),
           round((ys.max() - top) / S - spr.h) + CFG[cid].get("dy", 0))
    return x0, top, S, W, H, off


def make(cid):
    cfg = CFG[cid]
    spr = ShinySprite(PLAN[cid]["sprite"], cfg["flip"])
    x0, y0, S, W, H, off = layout(cid, spr, make_mask(cid, swallow=False))
    return C.vault_gx_card(cid, spr, x0, y0, S, W, H, boxes(cid), texture=False, off=cfg.get("off", off),
                           grow=cfg.get("grow", GROW))


BUILDERS = {cid: (lambda cid=cid: make(cid)) for cid in PLAN}

if __name__ == "__main__":
    HB.run(GROUP, BUILDERS, MASKS, sys.argv[1:])
