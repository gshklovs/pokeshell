"""Lost Origin group `radiant`: the Radiant Rare cards (ladder Radiant Gardevoir 69; cz Radiant Charizard 20: the
SHINY sprite (automatic in the kind), silver log-spiral crosshatch, RAD_WIN window, anim radiant). Masks: the
segmenter that caught the Pokemon best (work/radiant_rembg.png), windowed, OR-ed with a generous hand hull (card
px read off work/grid_<n>.png)."""
import lorbatch
from lorcards import RAD_WIN

GROUP = "radiant"
TABLE = {
    # the head top left facing left, the body and claws running down to the right onto the rock: as the sprite.
    # The crest plume (the yellow crescent) is the Pokemon's; isnet-general-use also takes cloud edges and the
    # rock, so it is ANDed with a hull round Sneasler (the rock under the claws stays scenery).
    "swsh11-123": dict(kind="radiant", sprite="sneasler", grow=7, tex_src=(65, 105, 195, 330),
                       scene="the frozen highland sky",
                       mask=dict(model="isnet-general-use", win=RAD_WIN, keep=4, close=5,
                                 hull=[(190, 98), (560, 98), (612, 140), (600, 200), (520, 200), (505, 255),
                                       (560, 325), (640, 365), (650, 450), (570, 478), (480, 488), (225, 488),
                                       (225, 420), (245, 330), (195, 255), (182, 160)],
                                 add=[[(190, 200), (205, 150), (245, 108), (285, 98), (340, 98), (430, 108),
                                       (520, 125), (605, 145), (605, 205), (560, 200), (485, 215), (455, 260),
                                       (475, 305), (560, 335), (630, 375), (635, 445), (560, 465), (470, 475),
                                       (400, 485), (228, 485), (218, 380), (235, 300), (198, 245)]])),
    # the head on the right facing right, the body trailing up-left: flipped. isnet-anime catches Steelix cleanly.
    "swsh11-124": dict(kind="radiant", sprite="steelix", flip=True, grow=7, tex_src=(470, 105, 670, 220),
                       scene="the shattered crystal",
                       mask=dict(model="isnet-anime", win=RAD_WIN, keep=6, close=5,
                                 add=[[(70, 105), (135, 98), (205, 155), (265, 135), (335, 130), (405, 158),
                                       (425, 215), (475, 225), (565, 225), (615, 295), (628, 385), (605, 425),
                                       (525, 445), (425, 425), (365, 445), (345, 485), (225, 480), (155, 405),
                                       (118, 350), (155, 298), (200, 278), (165, 235), (75, 135)]])),
}
if __name__ == "__main__":
    lorbatch.main(GROUP, TABLE)
