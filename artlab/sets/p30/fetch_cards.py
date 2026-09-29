r"""cards/<id>.json (CARD_FORMAT, fields verbatim from the API; `tier` = the API rarity, as in evs) and the cached
API record cards/api/<id>.json, for the given ids (default: the ladder picks), from setlist.json (fetched by
fetch_set.py straight from the API); scans in ref/ (fetch_refs.py).
  ..\..\..\.venv\Scripts\python fetch_cards.py [me55-23 ...]
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import artpaths  # noqa: E402
HERE = artpaths.data("p30")                       # cards/, cards/api/, ref/, setlist.json
FIELDS = ["id", "name", "supertype", "subtypes", "hp", "types", "evolvesFrom", "abilities", "attacks", "weaknesses",
          "resistances", "retreatCost", "rules", "flavorText", "set", "number", "rarity", "artist", "tier", "images"]
LISTS = ("abilities", "attacks", "weaknesses", "resistances", "retreatCost", "rules", "subtypes", "types")


def write(d):
    (HERE / "cards" / "api").mkdir(parents=True, exist_ok=True)
    (HERE / "cards" / "api" / f"{d['id']}.json").write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding="utf-8")
    out = {}
    for k in FIELDS:
        if k == "tier":
            out[k] = d["rarity"]
        elif k == "set":
            out[k] = {s: d["set"][s] for s in ("id", "name", "printedTotal")}
        elif k == "images":
            out[k] = {"large": d["images"]["large"]}
        else:
            out[k] = d.get(k, [] if k in LISTS else "")
    (HERE / "cards" / f"{d['id']}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")


def main(ids):
    sys.stdout.reconfigure(encoding="utf-8")
    by = {c["id"]: c for c in json.loads((HERE / "setlist.json").read_text(encoding="utf-8"))}
    for cid in ids:
        d = by[cid]
        assert d["set"]["id"] == "me55"
        write(d)
        assert (HERE / "ref" / f"me55_{d['number']}.png").exists(), cid
        print(f"{cid:9s} {d['name']:12s} {d['rarity']}")


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import p30cards
    main(sys.argv[1:] or p30cards.ORDER)
