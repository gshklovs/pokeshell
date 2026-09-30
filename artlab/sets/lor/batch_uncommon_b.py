r"""Lost Origin Uncommons, group uncommon_b (plan.json "uncommon_b"): the Gloom 2 / evs Shelgon treatment (matte,
sprite-scale scene, 12 colours, SWSH window). Masks are hand hulls in card px (read off work/grid_<n>.png), drawn
generously (tails, claws, fins, crystal tips), plus a colour rule for Lickilicky's tongue spiral.

  ..\..\..\.venv\Scripts\python batch_uncommon_b.py masks|quick|all [ids]
"""
from scipy import ndimage

import lorbatch
import lorcards
import lormasks as CM

GROUP = "uncommon_b"
DIL = 16          # the uncommon kind paints out with a fixed grow of 6: the hulls are dilated here, so no rim of the
                  # real Pokemon's outline is left for the smooth membrane to smear into a ghost


def grown(spec, dil=DIL):
    """a lormasks spec, dilated by `dil` card px (a custom fn mask)"""
    def fn(cid):
        m = CM.make(cid, spec)
        return ndimage.binary_dilation(m, iterations=dil) if dil else m
    return dict(fn=fn)


def hand(*polys, close=0, dil=DIL):
    return grown(dict(model=None, add=list(polys), close=close), dil)


ART = [(55, 118), (680, 118), (680, 480), (55, 480)]                 # the art window, card px


MIEN = [(55, 255), (200, 235), (260, 185), (330, 145), (380, 105), (560, 105), (610, 195), (665, 245), (665, 345),
        (600, 365), (520, 385), (440, 395), (420, 490), (55, 490)]   # Mienshao's reach (not the top-left rays)


def lavender(h, s, v):
    """Mienshao's pale lavender / white fur (the ground is saturated pink, orange, yellow and green)"""
    return (((h >= 190) & (h <= 315) & (s < 0.4) & (v > 0.5)) | ((s < 0.1) & (v > 0.8)))


def pink(h, s, v):
    """Lickilicky's pink tongue / body and cream belly (the poppies are far more saturated, the grass green)"""
    return ((h >= 320) | (h <= 22)) & (s > 0.08) & (s < 0.6) & (v > 0.78)


TABLE = {
    "swsh11-90": dict(kind="uncommon", sprite="rhydon", flip=True, scene="the dust storm",
                      mask=hand([(157, 268), (187, 275), (216, 290), (227, 239), (223, 198), (260, 187), (304, 202),
                                 (341, 187), (348, 129), (377, 140), (407, 165), (451, 151), (480, 165), (524, 147),
                                 (531, 173), (509, 217), (495, 261), (480, 279), (539, 283), (553, 253), (583, 261),
                                 (586, 305), (553, 327), (509, 319), (517, 378), (553, 407), (575, 459), (451, 470),
                                 (363, 444), (304, 437), (201, 466), (198, 422), (216, 393), (194, 378), (165, 319)])),
    "swsh11-98": dict(kind="uncommon", sprite="hariyama", flip=True, scene="the splashing wave",
                      mask=hand([(200, 150), (240, 122), (300, 110), (360, 112), (410, 132), (455, 162), (475, 210),
                                 (490, 258), (515, 298), (530, 350), (530, 420), (520, 470), (485, 497), (255, 497),
                                 (215, 460), (185, 410), (155, 360), (140, 310), (140, 258), (158, 198)])),
    "swsh11-100": dict(kind="uncommon", sprite="medicham", scene="the waterfall",          # frontal: ambiguous
                       mask=hand([(289, 187), (333, 173), (341, 143), (377, 125), (436, 129), (451, 151), (429, 180),
                                  (421, 209), (451, 213), (454, 242), (414, 253), (407, 275), (451, 305), (495, 334),
                                  (498, 378), (465, 407), (407, 415), (392, 477), (370, 477), (363, 422), (319, 422),
                                  (282, 415), (267, 363), (282, 319), (333, 290), (333, 261), (260, 253), (253, 228),
                                  (311, 217), (304, 206), (289, 202)],
                                 [(240, 380), (258, 450), (330, 492), (420, 492), (480, 430), (510, 380)])),
    "swsh11-101": dict(kind="uncommon", sprite="relicanth", flip=True, scene="the starry deep sea",
                       mask=hand([(187, 250), (253, 246), (304, 250), (348, 202), (363, 151), (407, 143), (451, 151),
                                  (487, 187), (517, 246), (509, 275), (553, 312), (553, 341), (517, 341), (480, 349),
                                  (451, 400), (407, 400), (370, 378), (348, 415), (304, 415), (253, 437), (223, 437),
                                  (209, 378), (187, 327), (194, 290)],
                                  [(535, 295), (578, 318), (580, 362), (525, 365)])),
    # both forms are on the card (West left, East right): both masked out, the West (vendor gastrodon) sprite
    # anchored on the West one
    "swsh11-102": dict(kind="uncommon", sprite="gastrodon", scene="the seaweed bed", dx=-8,
                       mask=hand([(110, 217), (150, 202), (187, 187), (231, 187), (260, 143), (286, 158), (282, 195),
                                  (304, 187), (348, 187), (392, 195), (407, 173), (436, 154), (480, 158), (509, 143),
                                  (553, 118), (575, 129), (572, 165), (539, 187), (517, 217), (524, 268), (546, 312),
                                  (546, 363), (531, 393), (539, 451), (495, 462), (421, 451), (370, 451), (304, 422),
                                  (231, 459), (198, 459), (209, 415), (253, 393), (253, 349), (223, 305), (172, 290),
                                  (135, 261), (113, 246)],
                                  (185, 370, 335, 485), (495, 175, 575, 290))),
    "swsh11-104": dict(kind="uncommon", sprite="mienshao", flip=True, scene="the pink and green brushwork",
                       mask=grown(dict(model=None, hull=MIEN, colour=lavender, close=2, keep=6, fill=False, add=[[(69, 275), (150, 261), (231, 202), (260, 180), (333, 187), (363, 129), (392, 114),
                                  (495, 114), (553, 180), (568, 239), (619, 261), (597, 305), (553, 290), (539, 319),
                                  (583, 349), (597, 393), (553, 407), (487, 371), (451, 349), (385, 378), (385, 481),
                                  (187, 481), (201, 415), (157, 378), (69, 378)], (95, 375, 190, 445)]), dil=10)),
    "swsh11-108": dict(kind="uncommon", sprite="carbink", scene="the lantern by the window",   # frontal: ambiguous
                       mask=hand([(172, 180), (260, 165), (326, 129), (355, 96), (385, 99), (407, 121), (451, 114),
                                  (509, 114), (553, 136), (575, 165), (597, 180), (605, 275), (597, 349), (575, 378),
                                  (553, 451), (495, 455), (451, 415), (421, 444), (348, 459), (333, 415), (355, 378),
                                  (326, 349), (289, 334), (267, 297), (260, 261), (245, 224), (179, 202)],
                                  [(160, 175), (250, 160), (262, 240), (240, 330), (300, 380), (325, 440), (270, 440), (225, 330), (200, 215)],
                                  (330, 395, 575, 485))),
    "swsh11-116": dict(kind="uncommon", sprite="seviper", flip=True, scene="the red room",
                       mask=hand([(121, 400), (128, 356), (172, 305), (209, 253), (253, 209), (282, 158), (407, 151),
                                  (451, 180), (509, 195), (524, 224), (495, 261), (465, 312), (451, 363), (451, 400),
                                  (407, 437), (348, 437), (282, 422), (223, 407), (165, 415)],
                                  [(150, 400), (200, 380), (330, 400), (420, 420), (440, 465), (330, 468), (200, 440)])),
    "swsh11-126": dict(kind="uncommon", sprite="bronzong", scene="the stone ruins",        # tilted frontal: ambiguous
                       mask=hand([(150, 349), (179, 312), (231, 283), (282, 253), (333, 224), (333, 165), (377, 147),
                                  (436, 151), (451, 187), (495, 202), (575, 217), (627, 239), (649, 283), (641, 312),
                                  (597, 312), (553, 290), (539, 305), (546, 349), (495, 400), (436, 429), (385, 422),
                                  (363, 393), (326, 363), (275, 312), (260, 363), (238, 400), (223, 437), (172, 400),
                                  (150, 385)])),
    "swsh11-127": dict(kind="uncommon", sprite="stunfisk-galar", scene="the lily-pad mud",
                       mask=hand([(198, 253), (216, 180), (238, 151), (289, 140), (311, 151), (355, 143), (377, 114),
                                  (429, 136), (451, 114), (480, 151), (509, 187), (495, 217), (524, 246), (509, 275),
                                  (451, 319), (480, 341), (509, 356), (509, 378), (451, 393), (363, 378), (311, 415),
                                  (282, 415), (260, 378), (223, 349), (198, 312)],
                                  [(230, 380), (330, 445), (470, 445), (535, 410), (535, 365), (450, 385)],
                                  (190, 320, 255, 430), (495, 130, 545, 235))),
    "swsh11-133": dict(kind="uncommon", sprite="sliggoo-hisui", flip=True, scene="the marsh pool",
                       mask=hand([(165, 191), (187, 173), (260, 169), (319, 180), (348, 187), (355, 165), (392, 136),
                                  (436, 132), (443, 158), (451, 217), (451, 290), (480, 319), (517, 356), (495, 393),
                                  (451, 400), (451, 451), (348, 481), (267, 473), (253, 422), (260, 349), (297, 312),
                                  (341, 290), (341, 246), (341, 217), (289, 213), (187, 213)],
                                  [(500, 330), (560, 360), (565, 470), (460, 485)], (465, 295, 545, 350), (395, 100, 485, 150))),
    # the tongue loops round the whole art: a pink colour rule over the window, OR the body hull
    "swsh11-139": dict(kind="uncommon", sprite="lickilicky", flip=True, scene="the flower meadow",
                       mask=grown(dict(model=None, hull=ART, colour=pink, close=3, keep=4,
                                 add=[[(304, 187), (333, 180), (385, 158), (429, 129), (480, 129), (517, 158),
                                       (509, 195), (553, 239), (561, 275), (524, 297), (480, 290), (451, 312),
                                       (421, 363), (377, 378), (333, 378), (311, 349), (304, 290), (304, 246)]]), dil=10)),
    "swsh11-141": dict(kind="uncommon", sprite="porygon2", flip=True, scene="the night city",
                       mask=hand([(231, 202), (253, 195), (289, 224), (304, 268), (348, 275), (355, 209), (363, 173),
                                  (399, 151), (436, 158), (465, 173), (546, 176), (550, 195), (495, 217), (458, 224),
                                  (458, 283), (451, 305), (480, 319), (487, 363), (465, 393), (363, 400), (260, 393),
                                  (231, 378), (231, 341), (260, 312), (267, 283), (238, 239)],
                                  (200, 175, 275, 265))),
    "swsh11-145": dict(kind="uncommon", sprite="ambipom", scene="the windswept meadow",    # tumbling, frontal: ambiguous
                       mask=hand([(150, 151), (194, 114), (451, 114), (451, 158), (495, 195), (553, 180), (612, 202),
                                  (605, 231), (553, 224), (517, 224), (553, 275), (561, 319), (568, 378), (546, 415),
                                  (561, 466), (509, 466), (451, 415), (385, 385), (363, 356), (297, 334), (260, 319),
                                  (216, 319), (165, 290), (150, 246), (179, 209), (150, 187)],
                                  (555, 150, 650, 290), (280, 340, 370, 410), (440, 100, 500, 150), (440, 420, 490, 470))),
    "swsh11-149": dict(kind="uncommon", sprite="komala", scene="the park",
                       mask=hand([(157, 268), (179, 246), (238, 239), (282, 253), (333, 253), (385, 246), (451, 253),
                                  (473, 290), (465, 334), (436, 349), (407, 349), (385, 378), (363, 459), (267, 477),
                                  (216, 451), (176, 400), (172, 349), (194, 327), (172, 305)],
                                  (150, 265, 205, 315))),
}

# the shared STAGE_BOX stops at x 312 but the "Evolves from ..." plate runs to about x 420: box the whole plate on
# every evolved card, or its letters get mirrored into the fill (the lead's note from the holo agent)
EVO = (0, 58, 425, 124)
for _cid, _row in TABLE.items():
    if lorcards.evolves(_cid):
        _row["boxes"] = tuple(_row.get("boxes", ())) + (EVO,)

if __name__ == "__main__":
    lorbatch.main(GROUP, TABLE)
