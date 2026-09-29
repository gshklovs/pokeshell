r"""Group "holo_gx" of Hidden Fates (sm115): the 7 Rare Holo GX cards, built exactly like the approved Charizard-GX 9
(hfcards.gx_card): art frame to frame from y 92 down to where the attacks start (text_y, read per card off
work/grid_<n>.png), silver frame, the GX cracked-web foil, anim `gxweb`.

The Pokemon fills the card, so every mask is rembg (union of models) inside the art plus a hand hull read off the
grid (the Charizard 9 method); the fill is a textured push-pull with a tex_src patch of clean scenery.

Facing (vendor sprite vs the scan): Pinsir, Raichu, Mewtwo and Wigglytuff face right on the card -> flipped;
Gyarados and Onix face left like the sprite; Starmie is frontal (not flipped, ambiguous).

  ..\..\..\.venv\Scripts\python batch_holo_gx.py [masks|build|all|sheet|anim|verify] [ids]
"""
import sys

import hflib as P  # noqa: F401
from hflib import Sprite
import hfcards as C
import hfmasks as HM
import hfbatch as HB

GROUP = "holo_gx"
PLAN = HB.plan(GROUP)

STAGE_BOXES = (HM.ICON, HM.EVOLVES)
# text_y: top of the first attack row; stage: Stage 1 cards carry the icon + "Evolves from" bar
CFG = {
    "sm115-6": dict(flip=True, text_y=665, stage=False, tex_src=(600, 420, 700, 640),
                    scene="dusty clearing", models=("isnet-general-use", "u2net")),
    "sm115-14": dict(flip=False, text_y=545, stage=True, tex_src=(560, 420, 700, 540),
                     scene="sea-spray swirl", models=("isnet-general-use", "u2net")),
    "sm115-16": dict(flip=False, text_y=665, stage=True, tex_src=(260, 470, 420, 580),
                     scene="whirlpool", models=("isnet-general-use", "u2net")),
    "sm115-20": dict(flip=True, text_y=665, stage=True, tex_src=(30, 430, 100, 660),
                     scene="hilltop meadow", top_box=102, models=("isnet-general-use", "u2net")),
    "sm115-31": dict(flip=True, text_y=665, stage=False, tex_src=(40, 110, 200, 290),
                     scene="crystal cavern", models=("isnet-general-use", "u2net")),
    "sm115-36": dict(flip=False, text_y=545, stage=False, tex_src=(400, 100, 560, 190),
                     scene="stadium", top_box=106, models=("isnet-general-use", "u2net")),
    "sm115-42": dict(flip=True, text_y=600, stage=True, tex_src=(560, 300, 700, 480),
                     scene="blue sky over the grass", models=("isnet-general-use", "isnet-anime")),
}

# hand hulls (card px) read off work/grid_<n>.png: the Pokemon's outline, generous
HULLS = {
    "sm115-6": [(28, 92), (300, 92), (310, 140), (400, 120), (470, 150), (470, 92), (595, 92), (578, 200),
                (568, 260), (575, 350), (568, 440), (550, 520), (585, 560), (605, 600), (575, 645), (520, 668),
                (28, 668)],
    "sm115-14": [(190, 135), (330, 160), (420, 125), (475, 145), (545, 170), (570, 205), (645, 270), (660, 400),
                 (630, 470), (650, 545), (85, 545), (115, 480), (35, 400), (65, 345), (125, 245), (175, 225)],
    "sm115-16": [(28, 200), (100, 175), (150, 125), (190, 92), (435, 92), (475, 120), (540, 165), (590, 145),
                 (575, 230), (615, 300), (645, 420), (655, 560), (640, 668), (470, 668), (455, 620), (440, 560),
                 (470, 500), (420, 482), (330, 452), (250, 442), (185, 482), (115, 530), (55, 525), (28, 465)],
    "sm115-20": [(28, 160), (80, 178), (200, 92), (405, 92), (412, 190), (520, 200), (528, 92), (628, 92),
                 (612, 260), (602, 340), (706, 355), (706, 668), (115, 668), (88, 560), (88, 420), (28, 385)],
    "sm115-31": [(28, 435), (90, 445), (118, 365), (200, 295), (290, 298), (350, 325), (405, 298), (400, 200),
                 (425, 92), (595, 92), (605, 155), (706, 145), (706, 315), (622, 300), (565, 330), (565, 440),
                 (645, 455), (645, 545), (585, 565), (565, 668), (28, 668)],
    "sm115-36": [(35, 265), (55, 195), (135, 150), (140, 92), (205, 92), (215, 110), (300, 158), (380, 215),
                 (470, 205), (560, 195), (600, 165), (650, 250), (706, 340), (706, 545), (235, 545), (195, 520),
                 (115, 420), (35, 335)],
    "sm115-42": [(40, 190), (80, 120), (140, 115), (215, 170), (240, 115), (320, 92), (430, 92), (440, 92),
                 (475, 92), (560, 92), (560, 180), (650, 215), (680, 300), (680, 540), (640, 600), (225, 600),
                 (205, 550), (220, 470), (115, 470), (95, 420), (150, 350), (170, 290), (130, 250)],
}
# hulls intersect rembg? (False: the hull is OR-ed on top of rembg, the Charizard 9 way)
POLY_ONLY = {}
# extra hand parts OR-ed in: Gyarados' tail fin and the whisker that trails through the whirlpool
ADD = {
    "sm115-16": [[(222, 668), (248, 622), (300, 592), (348, 606), (362, 668)],
                 [(292, 462), (335, 466), (375, 555), (378, 645), (340, 645), (332, 560)]],
}


def win(cid):
    return (28, 92, 706, CFG[cid]["text_y"])


def make_mask(cid):
    cfg = CFG[cid]
    sh = C.E.card_img(cid).shape[:2]
    cut = HM.rect(sh, *HM.ICON) | HM.rect(sh, *HM.EVOLVES) if cfg["stage"] else None
    hull = HM.poly(sh, HULLS[cid])
    for pts in ADD.get(cid, ()):
        hull |= HM.poly(sh, pts)
    return HM.sm_window(cid, cfg["models"], close=5, win=win(cid), cut=cut, extra=hull)


MASKS = {cid: (lambda cid=cid: make_mask(cid)) for cid in PLAN}


def make(cid):
    cfg = CFG[cid]
    spr = Sprite(PLAN[cid]["sprite"], cfg["flip"])
    x0, y0, S, W, H = HB.layout_full(cid, spr, top=92, text_y=cfg["text_y"], left=28, right=706)
    # top_box: where the name bar's coloured border ends (it dips below y 92 on some cards and bled into the fill)
    boxes = C.EDGES + ((0, 0, 734, cfg.get("top_box", 92)),) + (STAGE_BOXES if cfg["stage"] else ()) + ((0, cfg["text_y"], 734, 1024),)
    return C.gx_card(cid, spr, x0, y0, S, W, H, boxes, tex_src=cfg["tex_src"], dx=cfg.get("dx", 0),
                     dy=cfg.get("dy", 0), scene=cfg["scene"], texture=cfg.get("texture", True))


BUILDERS = {cid: (lambda cid=cid: make(cid)) for cid in PLAN}

if __name__ == "__main__":
    HB.run(GROUP, BUILDERS, MASKS, sys.argv[1:])
