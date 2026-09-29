r"""Group "shiny_a" of Hidden Fates' Shiny Vault (sma): 22 Rare Shiny cards (SV1 .. SV23), built exactly like the
approved Charmander SV6 (hfcards.charmander_sv): the colorscripts SHINY sprite (flip only) in the card's white
art window, the window's pale gold sparkle-star pattern (the real Pokemon painted out) re-cut as vault foil.

  ..\..\..\.venv\Scripts\python batch_shiny_a.py masks [ids]
  ..\..\..\.venv\Scripts\python batch_shiny_a.py build [ids]
  ..\..\..\.venv\Scripts\python batch_shiny_a.py all [ids]

CFG per card: flip (facing read off the scan vs the vendor sprite; "ambig" = near-frontal, left unflipped unless
noted), tex_src (a star-pattern patch away from the Pokemon), boxes (the Ultra Beast banner), stage (Stage 1: the
evolution icon / Evolves bar are boxed and kept out of the mask), mask model(s).
"""
import sys

import numpy as np

import hflib as P  # noqa: F401
from hflib import E, ShinySprite  # noqa: F401
import hfcards as C
import hfmasks as HM
import hfbatch as HB

GROUP = "shiny_a"
PLAN = HB.plan(GROUP)

UB = (430, 116, 706, 164)                     # the "Ultra Beast" banner (grid_SV5: x 437..706, y 122..158)
R = (560, 110, 670, 470)                      # the ladder's tex_src: the window's right strip
L_ = (64, 110, 180, 470)                      # the window's left strip

CFG = {
    "sma-SV1":  dict(flip=True, tex_src=(500, 330, 670, 470),                  # Scyther faces right on the card
                add=[[(179, 101), (234, 123), (278, 171), (322, 237), (308, 277), (260, 277), (216, 240), (176, 174)],
                     [(333, 97), (374, 94), (395, 207), (348, 236)]]),  # the pale wings rembg drops
    "sma-SV2":  dict(flip=False, tex_src=R,                                 # Rowlet frontal (ambig)
                hull=[(80, 300), (85, 200), (150, 195), (215, 225), (250, 170), (300, 158), (400, 160), (470, 175),
                      (560, 140), (610, 130), (625, 200), (630, 300), (600, 355), (535, 380), (530, 420), (505, 450),
                      (410, 465), (280, 468), (240, 460), (215, 420), (160, 410), (110, 380), (80, 330)]),
    "sma-SV3":  dict(flip=True, tex_src=(470, 300, 670, 470), stage=True),  # Dartrix head turned right
    "sma-SV4":  dict(flip=True, tex_src=L_, add=[[(212, 145), (280, 145), (285, 335), (212, 335)]]),                                # Wimpod head at the right
    "sma-SV5":  dict(flip=False, tex_src=(470, 400, 670, 470), ub=True,     # Pheromosa: frontal sprite (ambig)
                hull=[(58, 365), (58, 150), (110, 140), (157, 130), (260, 108), (370, 112), (451, 134), (553, 160),
                      (670, 163), (681, 185), (674, 237), (667, 314), (597, 314), (495, 321), (436, 336), (553, 339),
                      (678, 332), (681, 358), (553, 376), (451, 394), (399, 405), (399, 431), (260, 438), (135, 479),
                      (102, 464), (150, 398), (165, 376), (150, 332), (84, 358)]),
    "sma-SV7":  dict(flip=False, tex_src=(64, 180, 170, 330), stage=True,  # Charmeleon faces left
                models=("isnet-general-use", "isnet-anime")),
    "sma-SV8":  dict(flip=False, tex_src=(480, 330, 670, 470)),             # Alolan Vulpix faces left
    "sma-SV9":  dict(flip=True, tex_src=(64, 330, 250, 470)),               # Wooper faces right
    "sma-SV10": dict(flip=True, tex_src=(560, 110, 670, 300), stage=True),  # Quagsire faces right
    "sma-SV11": dict(flip=False, tex_src=R),                                # Froakie frontal (ambig)
    "sma-SV12": dict(flip=False, tex_src=(500, 330, 670, 470), stage=True), # Frogadier faces left
    "sma-SV13": dict(flip=False, tex_src=(60, 110, 150, 470),                # Voltorb frontal (ambig)
                ellipse=(374, 284, 210, 198)),
    "sma-SV14": dict(flip=False, tex_src=(560, 330, 670, 470), ub=True),    # Xurkitree as the sprite (ambig)
    "sma-SV15": dict(flip=False, tex_src=(470, 330, 670, 470)),             # Seviper faces left
    "sma-SV16": dict(flip=False, tex_src=R),                                # Shuppet looks right, as the sprite
    "sma-SV17": dict(flip=False, tex_src=L_),                               # Inkay frontal (ambig)
    "sma-SV18": dict(flip=False, tex_src=(560, 110, 670, 300), stage=True), # Malamar frontal (ambig)
    "sma-SV19": dict(flip=True, tex_src=L_, ub=True, add=[[(322, 100), (362, 100), (362, 205), (322, 205)]]),                       # Poipole: tail curls left (ambig)
    "sma-SV20": dict(flip=False, tex_src=(64, 200, 150, 400),
                add=[[(325, 380), (380, 380), (420, 440), (420, 482), (325, 482)]]),  # the right leg rembg drops              # Sudowoodo frontal (ambig)
    "sma-SV21": dict(flip=False, tex_src=(560, 250, 670, 470)),             # Riolu faces left
    "sma-SV22": dict(flip=True, tex_src=(470, 110, 670, 300), stage=True),  # Lucario faces right
    "sma-SV23": dict(flip=True, tex_src=R,                                  # Rockruff: tail left, turned right
                add=[[(139, 244), (143, 171), (194, 116), (260, 101), (333, 130), (348, 200), (260, 237), (227, 317),
                      (187, 303), (150, 266)]],
                cut=[(58, 100), (138, 100), (138, 150), (58, 150)]),  # a printed star rembg joined to the tail
}


def boxes_of(cid):
    k = CFG[cid]
    b = ()
    if k.get("stage"):
        b += (HM.ICON, HM.EVOLVES)
    if k.get("ub"):
        b += (UB,)
    return b + tuple(k.get("boxes", ()))


def make_mask(cid):
    k = CFG[cid]
    sh = E.card_img(cid).shape[:2]
    cut = HM.rect(sh, *UB) if k.get("ub") else None
    if k.get("cut") is not None:
        c2 = HM.poly(sh, k["cut"])
        cut = c2 if cut is None else (cut | c2)
    if k.get("hull"):                         # every segmenter takes the window: the hand hull alone
        m = HM.poly(sh, k["hull"]) & HM.rect(sh, *HM.SM_WIN)
        if cut is not None:
            m &= ~cut
        return HM.fin(m, 2)
    extra = None
    for p in k.get("add", ()):
        extra = HM.poly(sh, p) if extra is None else (extra | HM.poly(sh, p))
    if k.get("ellipse"):
        cx, cy, rx, ry = k["ellipse"]
        yy, xx = np.mgrid[0:sh[0], 0:sh[1]]
        el = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1
        extra = el if extra is None else (extra | el)
    return HM.sm_window(cid, k.get("models", ("isnet-general-use",)), keep=k.get("keep", 1), close=k.get("close", 3),
                        extra=extra, cut=cut, stage=bool(k.get("stage")))


MASKS = {cid: (lambda cid=cid: make_mask(cid)) for cid in PLAN}


def make(cid):
    k = CFG[cid]
    spr = ShinySprite(PLAN[cid]["sprite"], k["flip"])
    x0, y0, S, W, H = HB.layout_window(cid, spr)
    return C.vault_card(cid, spr, x0, y0, S, W, H, boxes=boxes_of(cid), tex_src=k["tex_src"], dx=k.get("dx", 0),
                        dy=k.get("dy", 0), grow=k.get("grow", 6))


BUILDERS = {cid: (lambda cid=cid: make(cid)) for cid in PLAN}

if __name__ == "__main__":
    HB.run(GROUP, BUILDERS, MASKS, sys.argv[1:])
