"""Crown Zenith group `radiant`: the Radiant Rare cards (ladder: Radiant Charizard 20)."""
import czbatch
from czcards import RAD_WIN

GROUP = "radiant"
TABLE = {
    # rembg only catches Charjabug's face: a hand hull of the red Charjabug (the rock under it stays). The green
    # Charjabugs in the background are part of the card's own scene (not the card's Pokemon) and are kept.
    "swsh12pt5-51": dict(kind="radiant", sprite="charjabug", flip=True, grow=7, tex_src=(70, 110, 220, 250),
                         scene="the forest clearing",
                         mask=dict(model=None, add=[[(172, 280), (198, 232), (258, 205), (330, 198), (425, 210),
                                                     (475, 248), (508, 300), (512, 382), (475, 425), (400, 446),
                                                     (300, 450), (228, 436), (186, 392), (170, 340)]])),
    # Eternatus fills the window (generous hull + smooth fill against ghosts, as Radiant Charizard); its sprite
    # (58 x 49) would give an 83-wide crop (166 grid cols > 140), so W = 68, centred
    "swsh12pt5-105": dict(kind="radiant", sprite="eternatus", texture=False, grow=7, W=68, x0=113,
                          scene="the energy vortex",
                          mask=dict(model="isnet-general-use", win=RAD_WIN, keep=6, close=5,
                                    add=[[(465, 125), (560, 98), (680, 98), (680, 245), (600, 255), (520, 235),
                                          (465, 205)]])),
}
if __name__ == "__main__":
    czbatch.main(GROUP, TABLE)
