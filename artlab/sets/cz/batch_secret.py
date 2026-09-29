"""Crown Zenith group `secret`: the gold Rare Secret VSTARs of the Galarian Gallery (ladder: Arceus VSTAR GG70).

Shared-code workaround (local): the vendor `dialga-origin` sprite has one pixel (row 20, col 33) that is set in the
regular sprite but transparent in the shiny one, which evlib.Sprite asserts against. The shiny load is patched here
to take the regular colour at such pixels; the regular sprite (the one served) stays pixel-exact."""
import czbatch
import sprites  # noqa: E402 (on the path once czbatch / czlib is imported)

_load = sprites.load


def _load_fixed(name, shiny=False):
    s = _load(name, shiny=shiny)
    if not shiny:
        return s
    n = _load(name)
    return [[(c if c is not None else a) if a is not None else None for a, c in zip(ra, rc)] for ra, rc in zip(n, s)]


sprites.load = _load_fixed

GROUP = "secret"
TABLE = {
    "swsh12pt5gg-GG67": dict(kind="gold", sprite="palkia-origin", text_y=560,
                             mask=dict(model="isnet-general-use", hull=[(150, 170), (480, 170), (540, 290),
                                                                         (500, 520), (150, 520)], keep=2, close=4)),
    "swsh12pt5gg-GG68": dict(kind="gold", sprite="dialga-origin", text_y=560,
                             mask=dict(model="isnet-anime", hull=[(320, 100), (620, 100), (620, 480), (290, 480),
                                                                     (290, 190)], keep=3, close=4)),
    "swsh12pt5gg-GG69": dict(kind="gold", sprite="giratina-origin", text_y=530,
                             mask=dict(model=None,
                                       add=[[(200, 185), (240, 165), (290, 175), (330, 140), (400, 120), (440, 150),
                                             (470, 180), (520, 160), (560, 190), (560, 240), (530, 300), (490, 340),
                                             (460, 360), (450, 420), (410, 445), (380, 420), (340, 360), (280, 350),
                                             (240, 330), (215, 280)]])),
}
if __name__ == "__main__":
    czbatch.main(GROUP, TABLE)
