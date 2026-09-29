r"""Group "commons" of Neo Genesis (neo1): the Common cards, built exactly like the approved ladder Totodile 81 -- the
plain colorscripts sprite (normal and shiny), no background, no animation (commons rule).

Facing (read off work/facing-com{A,B,C}.png; nearly every vendor sprite faces left): the commons whose real card
faces the other way are in set.json "flip_commons", which the importer applies (the plain sprite mirrored, normal
and shiny) and this builder reads too:
  80 Totodile    flip   runs to the right, snout and open jaw to the right
Near-frontal, no facing to match (not flipped): Chikorita 53 / 54, Chinchou 55, Hoothoot 60, Hoppip 61 (face a
little right: flagged), Ledyba 63, Oddish 68 (lying on its back), Sentret 71, Snubbull 74, Spinarak 75,
Sudowoodo 77, Sunkern 78, Wooper 82. Every other common faces left like its sprite.

  ..\..\..\.venv\Scripts\python batch_commons.py [all|build|verify|sheet] [ids]
"""
import sys

import neobatch as HB
import neocards as C

GROUP = "commons"
PLAN = HB.plan(GROUP)


def make_builder(e):
    return lambda: C.common(e["id"], e["sprite"])


BUILDERS = {cid: make_builder(e) for cid, e in PLAN.items()}

if __name__ == "__main__":
    HB.run(GROUP, BUILDERS, None, sys.argv[1:])
