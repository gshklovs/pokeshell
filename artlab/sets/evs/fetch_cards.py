r"""Fetch the real swsh7 cards from the pokemontcg.io v2 API and write cards/<id>.json (docs/CARD_FORMAT.md).
Every field except `tier` is copied verbatim from the API; `tier` is ours and, per the user's decision
(every real rarity gets its own effect), it IS the printed rarity: the API's `rarity` string. Also caches the API response in cards/api/<id>.json and the hires scan in ref/.

  ..\..\..\.venv\Scripts\python fetch_cards.py
"""
import json
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import artpaths  # noqa: E402
HERE = artpaths.data("evs")                       # writes style-lab/evs/cards, cards/api, ref
PICKS = ["swsh7-125", "swsh7-74", "swsh7-174", "swsh7-215", "swsh7-204",
         "swsh7-108", "swsh7-106", "swsh7-49", "swsh7-109", "swsh7-30", "swsh7-226"]
# a reverse holo is a parallel PRINT of a common / uncommon / rare, not an API rarity: same id, same card data,
# `rarity` stays the API's, `tier` names the finish
TIER_OVERRIDE = {"swsh7-49": "Reverse Holo"}
FIELDS = ["id", "name", "supertype", "subtypes", "hp", "types", "evolvesFrom", "abilities", "attacks", "weaknesses",
          "resistances", "retreatCost", "rules", "flavorText", "set", "number", "rarity", "artist", "tier", "images"]


def get(url, tries=8):
    import time
    for i in range(tries):
        try:
            r = requests.get(url, timeout=60)
            if r.status_code == 200:
                return r
            print(f"  {url}: HTTP {r.status_code}, retry")
        except requests.RequestException as e:
            print(f"  {url}: {e}, retry")
        time.sleep(2 + 2 * i)
    raise SystemExit(f"giving up on {url}")


def main():
    (HERE / "cards" / "api").mkdir(parents=True, exist_ok=True)
    (HERE / "ref").mkdir(exist_ok=True)
    for cid in PICKS:
        r = get(f"https://api.pokemontcg.io/v2/cards/{cid}")
        d = r.json()["data"]
        assert d["id"] == cid and d["set"]["id"] == "swsh7", cid
        tier = TIER_OVERRIDE.get(cid, d["rarity"])
        if tier == "Reverse Holo":
            assert d["rarity"] in ("Common", "Uncommon", "Rare"), (cid, d["rarity"])
        (HERE / "cards" / "api" / f"{cid}.json").write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding="utf-8")
        out = {}
        for k in FIELDS:
            if k == "tier":
                out[k] = tier
            elif k == "set":
                out[k] = {s: d["set"][s] for s in ("id", "name", "printedTotal")}
            elif k == "images":
                out[k] = {"large": d["images"]["large"]}
            else:
                out[k] = d.get(k, [] if k in ("abilities", "attacks", "weaknesses", "resistances", "retreatCost", "rules", "subtypes", "types") else "")
        (HERE / "cards" / f"{cid}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
        png = HERE / "ref" / f"swsh7_{d['number']}.png"
        if not png.exists():
            png.write_bytes(get(d["images"]["large"]).content)
        print(f"{cid:10s} {d['name']:16s} {d.get('rarity')!s:14s} tier={tier:12s} {d['images']['large']}")


if __name__ == "__main__":
    main()
