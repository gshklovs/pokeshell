"""Lost Origin group `secret`: the gold Rare Secrets, built like the ladder's Giratina VSTAR 212 / Mew VMAX TG30
(evs Froslass gold remap, faceted gold). Generous hand hulls (card px, work/grid_<n>.png)."""
import lorbatch


def hand(*polys, close=0):
    return dict(model=None, add=list(polys), close=close)


GROUP = "secret"
TABLE = {
    # Hisuian Zoroark: the same illustration as the rainbow 203; lunging left, snout down-left -> unflipped;
    # the whole art is masked except the dark ground right of the claws, so the gold ground reads dark behind it
    "swsh11-213": dict(kind="gold", sprite="zoroark-hisui", text_y=555,
                       mask=hand([(30, 560), (30, 92), (705, 92), (705, 338), (645, 342), (632, 445), (705, 445), (705, 560),
                                  (30, 560)])),
    # Pikachu VMAX (Gigantamax, G-Max Volt Tackle): head in profile facing left like the vendor sprite -> unflipped;
    # the Gigantamax tag under the name boxed; the tall sprite is held inside the 140 x 110 cap (H 54)
    "swsh11tg-TG29": dict(kind="gold", sprite="pikachu-gmax", text_y=745, H=54, boxes=[(100, 110, 310, 160)],
                          mask=hand([(60, 600), (110, 470), (170, 330), (190, 200), (300, 130), (430, 110),
                                     (560, 140), (660, 190), (700, 280), (705, 600), (705, 750), (40, 750)],
                                    [(430, 15), (590, 15), (590, 200), (430, 200)])),
}
if __name__ == "__main__":
    lorbatch.main(GROUP, TABLE)
