r"""Group "shiny_b" of Hidden Fates' Shiny Vault (sma-SV24 .. SV45, Rare Shiny): built exactly like the approved
Charmander SV6 (hfcards.charmander_sv) -- the SHINY colorscripts sprite (flip only) in the card's white art window,
the window's pale gold sparkle-star pattern (Pokemon painted out, star texture from `tex_src`) re-cut as the vault
foil; anim `vault`. Crop: HB.layout_window. Stage 1 / 2: ICON + EVOLVES boxed and cut from the mask; Ultra Beasts:
the "Ultra Beast" banner (read off grid_SV24 / 26 / 32 / 33: x 434..706, y 116..164) boxed and cut from the mask.

Facing (read off the scans against the vendor sprites, which mostly face left): see CFG `flip` and the notes.

  ..\..\..\.venv\Scripts\python batch_shiny_b.py [masks|build|all|sheet] [ids]
"""
import sys

import numpy as np  # noqa: F401
from scipy import ndimage

import hflib as P  # noqa: F401
from hflib import E, ShinySprite
import hfcards as C
import hfmasks as HM
import hfbatch as HB

GROUP = "shiny_b"
PLAN = HB.plan(GROUP)

ICON, EVOLVES = HM.ICON, HM.EVOLVES
UB = (434, 116, 706, 164)                  # the "Ultra Beast" banner at the window's top right

TL = (64, 106, 170, 230)                   # star-pattern patches of the white window, by corner
TR = (560, 106, 670, 230)
BL = (64, 360, 170, 476)
BR = (560, 360, 670, 476)

# flip: True when the real card faces the other way from the vendor sprite. amb: near-frontal pose (not flipped).
CFG = {
    "sma-SV24": dict(flip=False, amb=True, ub=True, tex=BL, reach=50,  # Buzzwole: near-frontal sprite; card leans left
                     extra=lambda sh: HM.poly(sh, [(462, 272), (592, 278), (598, 306), (522, 328), (462, 328)])),  # pale wing
    "sma-SV25": dict(flip=False, tex=TL),                              # Zorua: faces left on both
    "sma-SV26": dict(flip=False, amb=True, ub=True, tex=BR, models=("isnet-anime",), ink=True, reach=50),          # Guzzlord: frontal
    "sma-SV27": dict(flip=False, tex=BL),                              # Magnemite: eye looks left on both
    "sma-SV28": dict(flip=False, amb=True, stage=True, tex=BR),       # Magneton: frontal trio
    "sma-SV29": dict(flip=False, amb=True, stage=True, tex=TL),       # Magnezone: 3/4, front lower left
    "sma-SV30": dict(flip=True, tex=BR, ink=True),                               # Beldum: card eye right, sprite eye left
    "sma-SV31": dict(flip=False, amb=True, stage=True, tex=BR),       # Metang: side-on dive vs frontal sprite
    "sma-SV32": dict(flip=False, amb=True, ub=True, tex=TL, ink=True, keep=3),          # Celesteela: frontal
    "sma-SV33": dict(flip=False, amb=True, ub=True, tex=BR),          # Kartana: frontal
    "sma-SV34": dict(flip=False, amb=True, tex=TR, ink=True,     # Ralts: frontal sprite, card looks right
                     extra=lambda sh: HM.poly(sh, [(180, 432), (212, 422), (210, 392), (248, 410), (246, 386),
                                                   (282, 394), (295, 378), (345, 378), (380, 398), (402, 412),
                                                   (385, 470), (372, 482), (190, 482), (192, 460)])),  # tail frill
    "sma-SV35": dict(flip=False, amb=True, stage=True, tex=TR),       # Kirlia: near-frontal sprite; card looks left
    "sma-SV36": dict(flip=False, amb=True, tex=BR),                    # Diancie: frontal sprite; card faces left
    "sma-SV37": dict(flip=False, stage=True, tex=BL, ink=True),                  # Altaria: head left on both
    "sma-SV38": dict(flip=False, tex=TR, models=("isnet-general-use", "u2net")),                              # Gible: faces left on both
    "sma-SV39": dict(flip=True, stage=True, tex=BL, models=("isnet-anime",)),                   # Gabite: card faces right
    "sma-SV40": dict(flip=False, stage=True, tex=BR),                  # Garchomp: head turned left on both
    "sma-SV41": dict(flip=False, tex=BL),                              # Eevee: head left, tail right on both
    "sma-SV42": dict(flip=True, tex=BL),                               # Swablu: card faces right
    "sma-SV43": dict(flip=False, amb=True, tex=BR),                    # Noibat: frontal
    "sma-SV44": dict(flip=False, tex=TR),                              # Oranguru: faces left on both
    "sma-SV45": dict(flip=True, tex=TR, models=("isnet-anime", "isnet-general-use")),                               # Type: Null: card faces right
}


# everything outside the art window (frame, name bar, card text): boxed, so the mirrored texture fill cannot pull
# text / frame into the window where the Pokemon touches its edge (Buzzwole, Guzzlord, Celesteela ...)
OUTSIDE = ((0, 0, 734, 106), (0, 478, 734, 1024), (0, 0, 62, 1024), (668, 0, 734, 1024))   # incl. the window bevel


def boxes_of(cid):
    f = CFG[cid]
    b = OUTSIDE
    if f.get("stage"):
        b += (ICON, EVOLVES)
    if f.get("ub"):
        b += (UB,)
    return b


def ink(cid, cut=None, close=4):
    """the Pokemon on the white vault window by colour: everything saturated or darker than the white ground,
    minus the pale gold sparkle stars, closed and hole-filled (for when rembg takes the whole window or misses
    white parts: Guzzlord, Celesteela's arms, Altaria's clouds)"""
    rgb, h, s, v = HM.hsv(cid)
    star = (h > 25) & (h < 70) & (s < 0.5) & (v > 0.75)
    m = ((s > 0.2) | (v < 0.78)) & ~star & HM.rect(rgb.shape[:2], 62, 104, 672, 478)
    if cut is not None:
        m &= ~cut
    m = ndimage.binary_fill_holes(ndimage.binary_closing(m, iterations=close))
    return ndimage.binary_opening(m, iterations=2)


def make_mask(cid):
    f = CFG[cid]
    sh = E.card_img(cid).shape[:2]
    cut = HM.rect(sh, *UB) if f.get("ub") else None
    if f.get("stage"):
        sc = HM.rect(sh, *ICON) | HM.rect(sh, *EVOLVES)
        cut = sc if cut is None else (cut | sc)
    extra = f["extra"](sh) if f.get("extra") else None
    if f.get("ink"):
        k = ink(cid, cut)
        extra = k if extra is None else (extra | k)
    m = HM.sm_window(cid, f.get("models", ("isnet-general-use",)), keep=f.get("keep", 1), close=f.get("close", 3),
                     extra=extra, cut=cut, stage=bool(f.get("stage")))
    return halo(cid, m, cut, f.get("reach", 50 if f.get("ub") else 25))


def halo(cid, m, cut=None, reach=25):
    """no ghosts: add every non-white, non-star ink px within `reach` px of the mask (thin antennae, spikes, claw
    tips, the jaw rembg left out), so the painted-out window keeps only the printed sparkle stars"""
    rgb, h, s, v = HM.hsv(cid)
    star = (h > 25) & (h < 70) & (s < 0.5) & (v > 0.75)
    k = ((s > 0.2) | (v < 0.78)) & ~star & HM.rect(rgb.shape[:2], 62, 104, 672, 478)
    if cut is not None:
        k &= ~cut
    for _ in range(3):                       # follow thin parts outwards
        m = m | (k & ndimage.binary_dilation(m, iterations=reach))
    return ndimage.binary_fill_holes(ndimage.binary_closing(m, iterations=2))


MASKS = {cid: (lambda cid=cid: make_mask(cid)) for cid in PLAN}


def make(cid):
    f = CFG[cid]
    spr = ShinySprite(PLAN[cid]["sprite"], f["flip"])
    x0, y0, S, W, H = HB.layout_window(cid, spr)
    return C.vault_card(cid, spr, x0, y0, S, W, H, boxes=boxes_of(cid), tex_src=f["tex"], dx=f.get("dx", 0),
                        dy=f.get("dy", 0), scene=f.get("scene", ""))


BUILDERS = {cid: (lambda cid=cid: make(cid)) for cid in PLAN}
assert set(CFG) == set(PLAN), set(CFG) ^ set(PLAN)

if __name__ == "__main__":
    HB.run(GROUP, BUILDERS, MASKS, sys.argv[1:])
