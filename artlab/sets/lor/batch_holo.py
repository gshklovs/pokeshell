"""Lost Origin group `holo`: the 20 Rare Holo cards (ladder Gengar 66; evs Salamence 109: holo_scene in the SWSH
window, anim holo). Every mask is a generous hand hull in card px, read off work/grid_<n>.png
(`grid.py lor <n> --crop 50 85 700 505 --step 25`). lorcards.window_rgb already boxes out everything outside the
art window before the fill (the brs OUT boxes), so no OUT is needed here; EVO boxes the whole "Evolves from" plate
(STAGE_BOX stops at x 312, the Hisuian names run to x ~405 and were mirrored into the fill)."""
import lorbatch

GROUP = "holo"
EVO = ((0, 58, 425, 124),)


def hull(*polys, **kw):
    return dict(model=None, add=[list(p) for p in polys], **kw)


def red_hair(h, s, v):
    """Hisuian Zoroark: the pink-red hair (the moon and the sky are white / blue)"""
    return ((h > 330) | (h < 20)) & (s > 0.28) & (v > 0.35)


TABLE = {
    "swsh11-3": dict(kind="holo", sprite="vileplume", scene="the flower meadow", boxes=EVO, mask=hull(
        [(205, 140), (280, 104), (389, 98), (500, 100), (640, 125), (686, 145), (686, 310), (580, 318), (575, 380),
         (560, 430), (525, 482), (389, 484), (290, 484), (282, 417), (300, 345), (270, 320), (205, 250)])),
    "swsh11-8": dict(kind="holo", sprite="beautifly", scene="the cherry blossoms", boxes=EVO, mask=hull(
        [(118, 215), (223, 172), (232, 118), (281, 104), (339, 118), (389, 108), (498, 102), (560, 125), (585, 229),
         (580, 360), (640, 365), (660, 420), (600, 442), (560, 442), (460, 447), (389, 478), (280, 480), (250, 410),
         (240, 352), (200, 330), (190, 280), (115, 265)])),
    "swsh11-13": dict(kind="holo", sprite="shiftry", scene="the leaf gale", texture=False, boxes=EVO, mask=hull(
        [(70, 310), (100, 190), (194, 155), (353, 135), (454, 128), (556, 140), (686, 170), (686, 310), (505, 330),
         (460, 395), (440, 486), (230, 486), (200, 430), (130, 420), (80, 390)])),
    "swsh11-17": dict(kind="holo", sprite="trevenant", scene="the forest brawl", boxes=EVO, mask=hull(
        [(62, 170), (110, 118), (180, 104), (245, 110), (290, 148), (318, 206), (395, 212), (408, 305), (348, 332),
         (348, 395), (320, 486), (185, 486), (130, 432), (58, 432), (58, 260)])),
    "swsh11-20": dict(kind="holo", sprite="orbeetle", scene="the sunlit wood", boxes=EVO, mask=hull(
        [(205, 186), (262, 118), (353, 98), (460, 104), (535, 158), (558, 251), (520, 328), (464, 355), (472, 412),
         (408, 478), (353, 486), (185, 486), (212, 390), (198, 350), (198, 300), (198, 229)])),
    "swsh11-26": dict(kind="holo", sprite="chandelure", scene="the spectral glow", boxes=EVO, mask=hull(
        [(98, 270), (112, 150), (172, 140), (202, 198), (235, 238), (285, 218), (322, 160), (292, 112), (353, 98),
         (454, 98), (519, 98), (602, 162), (612, 278), (568, 368), (508, 414), (428, 434), (402, 486), (352, 480),
         (318, 434), (168, 430), (126, 372)])),
    "swsh11-29": dict(kind="holo", sprite="pyroar", scene="the wall of flame", boxes=EVO, tex_src=(64, 130, 160, 330), mask=hull(
        [(152, 172), (208, 108), (315, 108), (372, 140), (454, 188), (480, 152), (562, 145), (642, 192), (642, 250),
         (662, 285), (648, 398), (592, 398), (582, 482), (500, 482), (450, 422), (320, 414), (272, 460), (175, 468),
         (122, 432), (162, 359), (182, 302), (152, 258)])),
    "swsh11-37": dict(kind="holo", sprite="kingdra", flip=True, scene="the deep current", texture=False, boxes=EVO,
                      mask=hull([(78, 400), (122, 280), (178, 162), (230, 108), (353, 100), (454, 108), (518, 96),
                                 (508, 193), (562, 350), (634, 420), (618, 466), (454, 466), (324, 466), (86, 444)])),
    "swsh11-45": dict(kind="holo", sprite="basculegion", scene="the spirit wake", texture=False, boxes=EVO, mask=hull(
        [(88, 250), (140, 178), (267, 116), (411, 100), (556, 96), (686, 112), (686, 486), (353, 486), (250, 458),
         (168, 392), (108, 332)])),
    "swsh11-51": dict(kind="holo", sprite="glastrier", scene="the snowy pines", mask=hull(
        [(190, 150), (236, 96), (339, 90), (384, 148), (428, 190), (512, 198), (602, 218), (625, 323), (603, 374),
         (632, 480), (234, 480), (234, 388), (255, 302), (220, 252), (190, 230)])),
    "swsh11-70": dict(kind="holo", sprite="sableye", scene="the crystal cave", texture=False, mask=hull(
        [(104, 222), (228, 146), (286, 108), (456, 102), (500, 198), (600, 204), (686, 268), (686, 410), (572, 410),
         (560, 466), (485, 484), (228, 484), (154, 406), (132, 302)])),
    "swsh11-74": dict(kind="holo", sprite="cresselia", scene="the starry night", mask=hull(
        [(245, 150), (310, 100), (385, 104), (395, 180), (440, 214), (512, 214), (612, 238), (606, 280), (562, 294),
         (562, 392), (512, 418), (497, 478), (405, 482), (378, 430), (345, 420), (268, 404), (262, 330), (343, 300),
         (343, 240), (250, 216), (235, 176)])),
    "swsh11-76": dict(kind="holo", sprite="zoroark-hisui", scene="the moonlit wood", texture=False, boxes=EVO,
                      mask=dict(model=None, keep=12,
                                hull=[(56, 130), (686, 100), (686, 486), (56, 486)], colour=red_hair,
                                add=[[(120, 212), (194, 160), (288, 124), (389, 124), (556, 108), (670, 150),
                                      (686, 251), (686, 478), (397, 478), (361, 400), (267, 408), (158, 452),
                                      (118, 400), (160, 320)]])),
    "swsh11-81": dict(kind="holo", sprite="spectrier", scene="the snowfield", mask=hull(
        [(142, 237), (156, 112), (216, 96), (353, 138), (454, 143), (560, 148), (628, 175), (628, 262), (582, 332),
         (582, 402), (522, 442), (404, 442), (353, 486), (236, 486), (243, 388), (207, 302), (149, 280)])),
    "swsh11-84": dict(kind="holo", sprite="arcanine-hisui", scene="the crag in the clouds", boxes=EVO, mask=hull(
        [(248, 186), (260, 136), (335, 132), (397, 186), (440, 194), (512, 176), (557, 225), (537, 316), (562, 385),
         (547, 432), (454, 434), (353, 420), (300, 412), (268, 367), (246, 302), (238, 244)])),
    "swsh11-88": dict(kind="holo", sprite="machamp", scene="the grassy hills", texture=False, boxes=EVO, mask=hull(
        [(143, 150), (187, 108), (252, 116), (324, 103), (454, 126), (491, 96), (577, 96), (607, 193), (567, 300),
         (527, 340), (537, 440), (577, 440), (572, 486), (298, 486), (228, 452), (193, 390), (148, 302)])),
    "swsh11-107": dict(kind="holo", sprite="barbaracle", scene="the reef", texture=False, boxes=EVO, mask=hull(
        [(86, 244), (116, 194), (216, 126), (288, 110), (339, 178), (382, 184), (433, 184), (512, 163), (621, 118),
         (686, 156), (686, 412), (628, 432), (562, 432), (537, 442), (472, 486), (223, 486), (238, 403), (188, 330),
         (98, 324)])),
    "swsh11-120": dict(kind="holo", sprite="darkrai", scene="the dark vortex", mask=hull(
        [(178, 150), (223, 90), (296, 83), (345, 108), (432, 120), (507, 193), (530, 287), (574, 390), (562, 442),
         (472, 442), (456, 486), (353, 486), (343, 417), (262, 432), (186, 410), (136, 362), (150, 287), (178, 229)])),
    "swsh11-134": dict(kind="holo", sprite="goodra-hisui", flip=True, scene="the sea cave", boxes=EVO, mask=hull(
        [(133, 266), (188, 193), (281, 170), (350, 178), (385, 113), (454, 103), (550, 158), (557, 229), (520, 287),
         (502, 355), (562, 420), (550, 464), (397, 490), (192, 490), (140, 395)])),
    "swsh11-143": dict(kind="holo", sprite="snorlax", scene="the park bench", mask=hull(
        [(118, 300), (138, 250), (188, 218), (262, 163), (397, 138), (487, 143), (562, 228), (647, 298), (664, 360),
         (607, 432), (540, 464), (430, 442), (300, 442), (198, 432), (183, 380), (138, 372)])),
}

if __name__ == "__main__":
    lorbatch.main(GROUP, TABLE)
