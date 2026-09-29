r"""Fetch real cards from the pokemontcg.io v2 API and write their text half, packs/<pack>/cards/<id>.json
(docs/CARD_FORMAT.md). Every field is the API's, copied verbatim, except `tier`: the pack tier whose
`rarity` (pack.json) is the card's printed rarity.

  .venv\Scripts\python tools\fetch_cards.py swsh4-170 sv8-247      # these cards
  .venv\Scripts\python tools\fetch_cards.py --all                  # every card in packs/pokemon/pack.json "cards"
  .venv\Scripts\python tools\fetch_cards.py --all --refresh        # ... re-downloading ones already fetched
  options: --pack <id> (default pokemon), --from <dir> (use <dir>/<id>.json, e.g. a batch's cards/, when present)

The generated files are copyrighted card text and stay local (git-ignored, see .gitignore).
The API is flaky (500/502 now and then): every request is retried with backoff. No API key is sent.
Standard library only.
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://api.pokemontcg.io/v2/cards/"
FIELDS = ["id", "name", "supertype", "subtypes", "hp", "types", "evolvesFrom", "abilities", "attacks", "weaknesses",
          "resistances", "retreatCost", "rules", "flavorText", "set", "number", "rarity", "artist", "tier", "images"]
LISTS = {"abilities", "attacks", "weaknesses", "resistances", "retreatCost", "rules", "subtypes", "types"}


def get_json(url, tries=25):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "pokeshell-fetch-cards/1"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            if e.code == 404:
                raise SystemExit(f"{url}: 404, no such card")
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last = str(e)
        time.sleep(min(1 + i, 6))
    raise SystemExit(f"giving up on {url} after {tries} tries ({last})")


def load_pack(pack):
    return json.loads((ROOT / "packs" / pack / "pack.json").read_text(encoding="utf-8"))


def tier_of(pack_json, rarity):
    """the pack tier whose printed rarity this is (pack.json tiers[].rarity: a string or a list), else None"""
    for t in pack_json.get("tiers", []):
        r = t.get("rarity")
        names = r if isinstance(r, list) else [r] if r else []
        if rarity in names:
            return t["id"]
    return None


def card_format(d, tier):
    """an API card -> the CARD_FORMAT dict (API fields verbatim, plus our tier)"""
    out = {}
    for k in FIELDS:
        if k == "tier":
            out[k] = tier
        elif k == "set":
            s = d.get("set") or {}
            out[k] = {x: s.get(x) for x in ("id", "name", "printedTotal")}
        elif k == "images":
            out[k] = {"large": (d.get("images") or {}).get("large", "")}
        else:
            out[k] = d.get(k, [] if k in LISTS else "")
    return out


def fetch(card_id, pack_json, cards_dir, refresh=False, from_dir=None, quiet=False):
    """write cards_dir/<id>.json (fetched, or copied from from_dir) and return it; the tier is (re)mapped each time"""
    dst = cards_dir / f"{card_id}.json"
    src = None
    if dst.exists() and not refresh:
        src = json.loads(dst.read_text(encoding="utf-8"))
    elif from_dir and (Path(from_dir) / f"{card_id}.json").exists():
        src = json.loads((Path(from_dir) / f"{card_id}.json").read_text(encoding="utf-8"))
    if src is None:
        src = get_json(API + card_id)["data"]
        if src.get("id") != card_id:
            raise SystemExit(f"{card_id}: the API answered with {src.get('id')}")
    out = card_format(src, tier_of(pack_json, src.get("rarity")))
    cards_dir.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    if not quiet:
        print(f"  {card_id:12s} {out['name']:18s} {str(out['rarity']):22s} tier={out['tier']}")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--pack", default="pokemon")
    ap.add_argument("--all", action="store_true", help="every card in the pack's pack.json")
    ap.add_argument("--refresh", action="store_true", help="download again even when cards/<id>.json exists")
    ap.add_argument("--from", dest="from_dir", help="read <dir>/<id>.json instead of the API when it exists")
    a = ap.parse_args()
    pj = load_pack(a.pack)
    ids = list(a.ids) + (list((pj.get("cards") or {}).keys()) if a.all else [])
    if not ids:
        ap.error("name card ids, or --all")
    cards_dir = ROOT / "packs" / a.pack / "cards"
    unmapped = []
    for cid in ids:
        c = fetch(cid, pj, cards_dir, a.refresh, a.from_dir)
        if not c["tier"]:
            unmapped.append(f"{cid} ({c['rarity']})")
    if unmapped:
        print("no tier in pack.json for these rarities (add a tier with that \"rarity\"): " + ", ".join(unmapped), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
