r"""Group "commons" of Hidden Fates (sm115): the Common cards, built exactly like the approved Charmander 7 -- the
plain colorscripts sprite (normal and shiny), no background, no animation (commons rule).

Facing: the importer builds a Common from the plain vendor sprite with no flip. The commons whose real card faces
the other way from the vendor sprite are listed in set.json "flip_commons" (the per-set field the importer is
getting on the Crown Zenith branch); here they are rendered unflipped, exactly as the importer builds them today,
and FLIP_COMMONS below records the reading.

  ..\..\..\.venv\Scripts\python batch_commons.py [all|build|verify|sheet] [ids]
"""
import json
import sys

import hflib as P
from hflib import Card, Sprite
import hfbatch as HB
from evcards import meta

GROUP = "commons"
PLAN = HB.plan(GROUP)
FLIP_COMMONS = json.loads((P.HERE / "set.json").read_text(encoding="utf-8")).get("flip_commons", [])


def make_builder(e):
    cid, name = e["id"], e["sprite"]

    def build():
        spr = Sprite(name)
        c = Card(spr.w, spr.h)
        c.put_sprite(spr, 0, 0)
        card = P.card_json(cid)
        assert card["tier"] == "Common", (cid, card["tier"])
        return meta(c, card=cid,
                    label=f"Common: {card['name']} {card['number']}/{card['set']['printedTotal']} -- the plain "
                          f"sprite (commons get no background)",
                    rarity="Common", finish="plain sprite, no background (commons rule)", variant="common",
                    anim=None, ref=(cid, 58, 100, 676, 482), S=None, frame="#9aa0aa",
                    wrong_facing=cid in FLIP_COMMONS)
    return build


BUILDERS = {cid: make_builder(e) for cid, e in PLAN.items()}

if __name__ == "__main__":
    HB.run(GROUP, BUILDERS, None, sys.argv[1:])
