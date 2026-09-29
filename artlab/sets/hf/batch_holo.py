r"""Group "holo" of Hidden Fates (sm115): the Rare Holo cards, built exactly like the approved Vaporeon 18
(hfcards.vaporeon, the evs Salamence recipe): window_rgb(grow=5, texture fill) in SM_WIN +
tiers.holo_scene(ncol=12, foil=0.22, bright=1.0, 4 sparkles), anim `holo`, frame #56d0e0.

Facing read off the scans (most vendor sprites face left):
  24 Zapdos  -      beak left on card and sprite
  48 Eevee   flip   leaps to the right (tail left, head right, face turned to the viewer / right)

Local fixes (shared files untouched): everything outside the art window is boxed out of the texture fill (else it
mirrors the name / NO. line text into the holes).

  ..\..\..\.venv\Scripts\python batch_holo.py [masks|build|all|sheet] [ids]
"""
import sys

import numpy as np
from scipy import ndimage

import hflib as P  # noqa: F401
from hflib import E, Sprite
import hfcards as C
import hfmasks as HM
import hfbatch as HB
from evcards import meta

GROUP = "holo"
PLAN = HB.plan(GROUP)
GRID = (40, 60, 700, 500, 900)          # grid.py --crop 40 60 700 500: image px -> card px
OUTSIDE = ((0, 0, 734, HM.SM_WIN[1] + 5), (0, HM.SM_WIN[3] - 5, 734, 1024), (0, 0, HM.SM_WIN[0] + 5, 1024),
           (HM.SM_WIN[2] - 5, 0, 734, 1024))


def G(pts):
    x0, y0, x1, _, w = GRID
    f = (x1 - x0) / w
    return [(x0 + x * f, y0 + y * f) for x, y in pts]


# ---------------------------------------------------------------- masks
def m_24():
    """rembg takes the whole storm: Zapdos is its own colours (yellow plumage, orange beak / legs, brown
    underside) inside the window, the white / pale lightning excluded; closed over the spiky outline"""
    cid = "sm115-24"
    rgb, h, s, v = HM.hsv(cid)
    sh = rgb.shape[:2]
    yellow = (h > 36) & (h < 66) & (s > 0.5) & (v > 0.45)
    orange = (h >= 8) & (h <= 36) & (s > 0.5) & (v > 0.35)
    brown = (h < 40) & (s > 0.3) & (v > 0.18) & (v <= 0.6)
    m = (yellow | orange | brown) & HM.rect(sh, *HM.SM_WIN)
    m = ndimage.binary_opening(m, iterations=1)
    m = HM.largest(ndimage.binary_closing(m, iterations=4), 1)
    m = ndimage.binary_fill_holes(ndimage.binary_closing(m, iterations=8))
    # the shaded undersides of the wing spikes (dark olive / brown / grey-brown) next to the plumage
    shade = (h < 70) & (s > 0.15) & (v > 0.1) & (v <= 0.62) & ndimage.binary_dilation(m, iterations=30)
    m |= ndimage.binary_opening(shade, iterations=1) & HM.rect(sh, *HM.SM_WIN)
    m = ndimage.binary_fill_holes(ndimage.binary_closing(HM.largest(m, 1), iterations=6))
    return ndimage.binary_dilation(m, iterations=5) & HM.rect(sh, *HM.SM_WIN)


def m_48():
    """isnet-anime has Eevee alone (the Pidgeotto, Voltorb, Grimer and Poke Balls are the scene) but misses the
    tip of the right ear and the front paws: added by hand"""
    cid = "sm115-48"
    sh = E.card_img(cid).shape[:2]
    ear = HM.poly(sh, G([(630, 236), (680, 222), (800, 136), (850, 114), (840, 170), (772, 268), (700, 305), (640, 330)]))
    paws = HM.poly(sh, G([(468, 398), (572, 408), (578, 482), (522, 504), (458, 472)]))
    return HM.sm_window(cid, ("isnet-anime",), close=4, extra=ear | paws)


MASKS = {"sm115-24": m_24, "sm115-48": m_48}

# ---------------------------------------------------------------- per card
CFG = {
    "sm115-24": dict(flip=False, stage=False, tex_src=(70, 360, 170, 470), seed=24, scene="thunderstorm"),
    "sm115-48": dict(flip=True, stage=False, tex_src=(560, 110, 670, 230), seed=48, scene="forest of Poke Balls"),
}


def make(cid):
    import tiers as s3t
    cfg = CFG[cid]
    spr = Sprite(PLAN[cid]["sprite"], flip=cfg["flip"])
    x0, y0, S, W, H = cfg.get("crop") or HB.layout_window(cid, spr)
    boxes = OUTSIDE + ((HM.ICON, HM.EVOLVES) if cfg["stage"] else ())
    rgb = C.window_rgb(cid, boxes=boxes, grow=5, tex_src=cfg["tex_src"])
    off = E.anchor(cid, x0, y0, S, spr, cfg.get("dx", 0), cfg.get("dy", 0))
    off = (max(1, min(W - spr.w - 1, off[0])), max(1, min(H - spr.h - 1, off[1])))
    c = s3t.holo_scene(spr, cid, None, x0, y0, S, W, H, cid, "", off=off, rgb=rgb, ncol=12, foil=0.22, bright=1.0,
                       sparkles=[(5, 5, 3), (2 * W - 6, 6, 2), (2 * W - 6, 2 * H - 6, 3), (4, 2 * H - 8, 2)],
                       seed=cfg["seed"])
    return meta(c, card=cid, label=f"Rare Holo: {C.name_of(cid)}, {cfg['scene']} (holo in the art box)",
                rarity="Rare Holo", finish="SM rare holo: rainbow foil bands + starlight inside the art box (evs Rare Holo)",
                variant="rare-holo", anim="holo", ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S,
                frame=C.FRAMES["Rare Holo"])


BUILDERS = {cid: (lambda cid=cid: make(cid)) for cid in PLAN}
assert set(BUILDERS) == set(CFG) == set(MASKS)

if __name__ == "__main__":
    HB.run(GROUP, BUILDERS, MASKS, sys.argv[1:])
