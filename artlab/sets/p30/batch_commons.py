r"""Group "commons" of the 30th Celebration (me55) full set: 64 Common cards, built exactly like the approved
Vulpix 9 -- the plain colorscripts sprite (normal and shiny), no background, no animation (commons rule, which
also covers the B / G / R monochrome Mews the API labels Common). Checks per id: card data loads, the sprite
name resolves (normal and shiny, same shape), render + verify pass. Writes sheets/commons.png and
sheets/commons-sizes.json (never the ladder's sizes.json).

  ..\..\..\.venv\Scripts\python batch_commons.py [me55-1 ...]
"""
import json
import sys

import p30lib as P
from p30lib import E, Card, Sprite
import p30cards
from evcards import meta
import sprites

GROUP = "commons"
PLAN = json.loads((P.HERE / "plan.json").read_text(encoding="utf-8"))[GROUP]
BY_ID = {e["id"]: e for e in PLAN}


def make_builder(e):
    cid, name = e["id"], e["sprite"]

    def build():
        spr = Sprite(name)
        c = Card(spr.w, spr.h)
        c.put_sprite(spr, 0, 0)
        card = P.card_json(cid)
        return meta(c, card=cid,
                    label=f"Common: {card['name']} {card['number']}/{card['set']['printedTotal']} -- the plain "
                          f"sprite (commons get no background)",
                    rarity="Common", finish="plain sprite, no background (commons rule; the real print is foil)",
                    variant="common", anim=None, ref=(cid, 52, 88, 606, 432), S=None)
    return build


def precheck(e):
    """card data loads and is a Common; the sprite resolves normal + shiny with the same shape"""
    cid = e["id"]
    card = P.card_json(cid)
    assert card["tier"] == "Common", (cid, card["tier"])
    assert card["number"] == e["number"], (cid, card["number"])
    n, s = sprites.load(e["sprite"], False), sprites.load(e["sprite"], True)
    assert (len(n), len(n[0])) == (len(s), len(s[0])), (cid, "shape differs")
    assert [[p is None for p in r] for r in n] == [[p is None for p in r] for r in s], (cid, "mask differs")
    return len(n[0]), len(n)


def main():
    import p30build
    import p30verify
    import p30sheet
    ids = [a for a in sys.argv[1:] if a in BY_ID] or list(BY_ID)
    p30cards.BUILDERS.update({cid: make_builder(BY_ID[cid]) for cid in ids})
    for cid in ids:
        w, h = precheck(BY_ID[cid])
        print(f"{cid:9s} data ok, sprite {BY_ID[cid]['sprite']} {w}x{h} (normal+shiny)")
    f = P.DATA / "sheets" / f"{GROUP}-sizes.json"
    sizes = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    for cid in ids:
        _, sizes[cid] = p30build.render(cid)
    f.parent.mkdir(exist_ok=True)
    f.write_text(json.dumps({k: sizes[k] for k in BY_ID if k in sizes}, indent=1), encoding="utf-8")
    for cid in ids:
        p30verify.check(cid)
    print(f"{p30verify.fails} failures")
    assert p30verify.fails == 0
    p30sheet.sheet(ids, P.DATA / "sheets" / f"{GROUP}.png", sizes)


if __name__ == "__main__":
    main()
