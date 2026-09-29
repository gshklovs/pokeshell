r"""Fetch a whole Pokemon TCG set from the pokemontcg.io v2 API into its data folder (docs/ART_METHOD.md, step 1).

  .venv\Scripts\python artlab\tools\fetch_set.py <set folder>            (reads artlab/sets/<folder>/set.json)
  .venv\Scripts\python artlab\tools\fetch_set.py <set folder> --set-id sv3pt5 --prefix sv3pt5
  options: --ids <id,id>   only these cards      --no-scans   skip the hires scans      --passes N (default 6)

Writes, under <DATA>/<folder>/ (artlab/artpaths.py: style-lab/<folder>, or $ARTLAB_DATA/<folder>):
  setlist.json          every card of the set, the full API records, sorted by number (one paged query)
  cards/api/<id>.json   the API record of each card
  cards/<id>.json       CARD_FORMAT (docs/CARD_FORMAT.md): the API fields verbatim, `tier` = the API rarity
  ref/<prefix>_<number>.png   the hires scan (images.large)

The API is flaky and refuses requests without a User-Agent: every request sends one and retries with backoff; files
already on disk are kept, and the scans are fetched in several passes (a pass skips what failed, the next retries
it). Card text and scans are copyrighted: they stay in the data folder, never in git.
"""
import argparse
import json
import sys
import time
import urllib.request
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import artpaths  # noqa: E402

API = "https://api.pokemontcg.io/v2"
UA = {"User-Agent": "pokeshell-fetch-cards/1"}
FIELDS = ["id", "name", "supertype", "subtypes", "hp", "types", "evolvesFrom", "abilities", "attacks", "weaknesses",
          "resistances", "retreatCost", "rules", "flavorText", "set", "number", "rarity", "artist", "tier", "images"]
LISTS = ("abilities", "attacks", "weaknesses", "resistances", "retreatCost", "rules", "subtypes", "types")


def get(url, tries=10, raw=False):
    for i in range(tries):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90).read()
            return r if raw else json.loads(r)
        except Exception as e:  # noqa: BLE001  (HTTP 5xx / 429, timeouts, resets: all retried)
            print(f"  {url}: {e}, retry {i + 1}/{tries}", flush=True)
            time.sleep(min(60, 2 + 3 * i))
    raise SystemExit(f"giving up on {url}")


def number_key(c):
    n = c["number"]
    return (int("".join(ch for ch in n if ch.isdigit()) or 0), n)


def set_cards(set_id):
    out, page = [], 1
    while True:
        d = get(f"{API}/cards?q=set.id:{set_id}&pageSize=250&page={page}")
        out += d["data"]
        if len(out) >= d["totalCount"] or not d["data"]:
            return sorted(out, key=number_key)
        page += 1


def card_format(d):
    """CARD_FORMAT: every field the API's, verbatim; `tier` is ours and IS the printed rarity (the API string)"""
    out = {}
    for k in FIELDS:
        if k == "tier":
            out[k] = d.get("rarity", "")
        elif k == "set":
            out[k] = {s: d["set"][s] for s in ("id", "name", "printedTotal")}
        elif k == "images":
            out[k] = {"large": d["images"]["large"]}
        else:
            out[k] = d.get(k, [] if k in LISTS else "")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder")
    ap.add_argument("--set-id")
    ap.add_argument("--prefix")
    ap.add_argument("--ids", default="")
    ap.add_argument("--no-scans", action="store_true")
    ap.add_argument("--passes", type=int, default=6)
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    meta_f = artpaths.code(a.folder) / "set.json"
    meta = json.loads(meta_f.read_text(encoding="utf-8")) if meta_f.exists() else {}
    set_id = a.set_id or meta.get("set_id")
    prefix = a.prefix or meta.get("prefix") or set_id
    if not set_id:
        ap.error(f"no --set-id and no {meta_f}")
    d = artpaths.data(a.folder)
    for sub in ("cards/api", "ref", "work"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    lst = d / "setlist.json"
    cs = json.loads(lst.read_text(encoding="utf-8")) if lst.exists() else None
    if not cs or "images" not in cs[0]:           # none yet, or a reduced list (evs's): fetch the full records
        cs = set_cards(set_id)
        lst.write_text(json.dumps(cs, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{set_id}: {len(cs)} cards  supertype {dict(Counter(c['supertype'] for c in cs))}")
    print(f"  rarity {dict(Counter(c.get('rarity') for c in cs))}")
    only = {i for i in a.ids.split(",") if i}
    cs = [c for c in cs if not only or c["id"] in only]
    for c in cs:
        assert c["set"]["id"] == set_id, c["id"]
        (d / "cards/api" / f"{c['id']}.json").write_text(json.dumps(c, indent=1, ensure_ascii=False), encoding="utf-8")
        (d / "cards" / f"{c['id']}.json").write_text(json.dumps(card_format(c), indent=1, ensure_ascii=False),
                                                     encoding="utf-8")
    print(f"  wrote cards/ and cards/api/ for {len(cs)} cards")
    if a.no_scans:
        return
    for p in range(a.passes):
        missing = [c for c in cs if not ((f := d / "ref" / f"{prefix}_{c['number']}.png").exists()
                                         and f.stat().st_size > 10000)]
        print(f"scans, pass {p + 1}: {len(missing)} missing", flush=True)
        if not missing:
            break
        for c in missing:
            try:
                (d / "ref" / f"{prefix}_{c['number']}.png").write_bytes(get(c["images"]["large"], tries=4, raw=True))
            except SystemExit as e:
                print("  skip", c["id"], e, flush=True)
        time.sleep(10)
    else:
        raise SystemExit("some scans are still missing: run again")


if __name__ == "__main__":
    main()
