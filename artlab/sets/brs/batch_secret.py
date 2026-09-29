"""Brilliant Stars group `secret`: the gold Rare Secrets, built like the ladder's Arceus VSTAR 184 / Urshifu VMAX TG29
(evs Froslass gold remap, faceted gold). Generous hand hulls (card px, work/grid_<n>.png)."""
import brsbatch
from brscards import STRIKE


def hand(*polys, close=0):
    return dict(model=None, add=list(polys), close=close)


GROUP = "secret"
TABLE = {
    # Galarian Articuno: head top right, looking right -> flip
    "swsh9-181": dict(kind="gold", sprite="articuno-galar", flip=True, text_y=625,
                      mask=hand([(30, 380), (100, 250), (200, 160), (330, 120), (440, 105), (520, 105), (635, 125),
                                 (625, 205), (545, 245), (560, 330), (610, 430), (705, 560), (705, 630),
                                 (30, 630)])),
    # Galarian Zapdos: beak pointing right -> flip
    "swsh9-182": dict(kind="gold", sprite="zapdos-galar", flip=True, text_y=615,
                      mask=hand([(30, 330), (100, 215), (200, 165), (310, 135), (330, 85), (420, 75), (520, 105),
                                 (615, 165), (635, 300), (695, 380), (685, 500), (645, 560), (705, 620),
                                 (30, 620)])),
    # Galarian Moltres: wings spread frontal, head turned right (beak right) -> flip
    "swsh9-183": dict(kind="gold", sprite="moltres-galar", flip=True, text_y=615,
                      mask=hand([(30, 130), (200, 100), (560, 100), (705, 100), (705, 620), (30, 620)])),
    # Rapid Strike Urshifu VMAX (Gigantamax): frontal like the ladder's TG29 -> unflipped; Rapid Strike badge boxed
    "swsh9tg-TG30": dict(kind="gold", sprite="urshifu-rapid-strike-gmax", text_y=585, boxes=[STRIKE],
                         mask=hand([(30, 150), (430, 90), (705, 150), (705, 590), (30, 590)])),
}
if __name__ == "__main__":
    brsbatch.main(GROUP, TABLE)
