r"""Group "commons" of the Base Set (base1): the Common cards, built exactly like the approved Charmander 46 -- the
plain colorscripts sprite (normal and shiny), no background, no animation (commons rule).

Facing (read off work/facing-commons{1,2}.png; nearly every vendor sprite faces left): the commons whose real card
faces the other way are in set.json "flip_commons", which the importer applies (the plain sprite mirrored, normal
and shiny) and this builder reads too:
  46 Charmander  flip   stands facing right, snout right
  59 Poliwag     flip   near-frontal, but the body is turned so the tail sweeps out to the left (flagged)
Near-frontal, no facing to match (not flipped): Abra 43, Bulbasaur 44, Diglett 47, Gastly 50, Koffing 51,
Magnemite 53, Pikachu 58, Starmie 64, Staryu 65, Tangela 66, Voltorb 67.

  ..\..\..\.venv\Scripts\python batch_commons.py [all|build|verify|sheet] [ids]
"""
import sys

import basebatch as HB
import basecards as C

GROUP = "commons"
PLAN = HB.plan(GROUP)


def make_builder(e):
    return lambda: C.common(e["id"], e["sprite"])


BUILDERS = {cid: make_builder(e) for cid, e in PLAN.items()}

if __name__ == "__main__":
    HB.run(GROUP, BUILDERS, None, sys.argv[1:])
