"""Brilliant Stars group `rainbow`: the true Rare Rainbow VSTARs (pastel rainbow wash, not paintings), built like the
ladder's Charizard VSTAR 174 (evs Leafeon VMAX 204: smooth fill, rainbow sprite 0.55, rainbow ground, etch, glitter).
The Pokemon covers most of each art, so the masks are generous hand hulls (card px, work/grid_<n>.png)."""
import brsbatch


def hand(*polys, close=0):
    return dict(model=None, add=list(polys), close=close)


GROUP = "rainbow"
TABLE = {
    # Shaymin Sky Forme: face at x~330 turned to the viewer's left, like the vendor sprite -> unflipped
    "swsh9-173": dict(kind="rainbow", sprite="shaymin-sky", text_y=550, scene="the rainbow petals",
                      mask=hand([(30, 330), (60, 250), (110, 200), (125, 135), (250, 125), (340, 170), (420, 195),
                                 (500, 185), (600, 150), (705, 120), (705, 560), (250, 560), (225, 500),
                                 (100, 470), (30, 430)])),
    # Whimsicott: cotton on the left, face on the right looking right -> flip
    "swsh9-175": dict(kind="rainbow", sprite="whimsicott", flip=True, text_y=490, scene="the rainbow cotton",
                      mask=hand([(30, 150), (130, 115), (420, 105), (640, 120), (705, 160), (705, 495),
                                 (100, 495), (30, 440)])),
    # Arceus: the same illustration as the ladder's gold 184 (flip=True there): one pose, one choice
    "swsh9-176": dict(kind="rainbow", sprite="arceus", flip=True, text_y=530, scene="the rainbow wheel",
                      mask=hand([(30, 170), (200, 125), (440, 100), (560, 140), (705, 200), (705, 540),
                                 (30, 540)])),
}
if __name__ == "__main__":
    brsbatch.main(GROUP, TABLE)
