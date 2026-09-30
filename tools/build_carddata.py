r"""Build packs/<pack>/carddata.json: the gameplay data of every card in pack.json "cards", from pokemontcg.io.

  .venv\Scripts\python tools\build_carddata.py                 # (re)build it: local card JSON first, the API for the rest
  .venv\Scripts\python tools\build_carddata.py --check         # only check it against pack.json (no network, writes nothing)
  .venv\Scripts\python tools\build_carddata.py --refresh       # ignore local copies: every set again from the API
  options: --pack <id> (default pokemon), --root <checkout>, --lab <style-lab> (default $ARTLAB_DATA, else
           <repo>\style-lab), --from <dir> (more folders of <card id>.json; repeatable), --cache <dir> (the API
           responses, default <repo>\.cache\carddata), --offline (never touch the network), --out <file>

Run it whenever pack.json's cards change (a new set's import: docs/ART_METHOD.md section 19, the new-card-set skill).
It is incremental: cards already in carddata.json are kept unless --refresh, and a card is taken from the first of
  1. <cache>/<set id>.json            an API response of the whole set, cached by an earlier run
  2. packs/<pack>/cards/<id>.json     the text half (tools/fetch_cards.py, build_realcards.py; local, git-ignored)
  3. <lab>/*/cards/api/<id>.json, <lab>/*/cards/<id>.json, --from <dir>/<id>.json   the batches' API copies
  4. carddata.json itself             what an earlier run found
  5. the API: one query per set (set.id:<set>, 250 a page), cached into <cache>/<set id>.json. It sends a User-Agent
     and retries with backoff (the API answers 502 now and then). No API key is sent.
Cards with no data anywhere are listed in "missing" and printed (the gaps), and the exit code is 2 (--check: 1).

The file (shipped with the module, tools/publish.ps1): only the cards in pack.json, only gameplay fields, all keys
always present (empty lists, null), one card per line so a reader can pick lines without parsing the rest:
  {"format": "pokeshell-carddata/1", "pack": .., "source": .., "fields": [..], "missing": [ids],
   "cards": {
  "base1-4":{"supertype":"Pokémon","hp":120,"types":["Fire"],"subtypes":["Stage 2"],"evolvesFrom":"Charmeleon",
             "abilities":[{"name","type","text"}],"attacks":[{"name","cost":[..],"convertedEnergyCost":4,"damage":"100","text"}],
             "weaknesses":[{"type","value"}],"resistances":[..],"retreatCost":["Colorless",..],"rules":[..]},
  ...
  }}
hp is a number (null for Trainers and Energy). Standard library only.
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
API = "https://api.pokemontcg.io/v2/cards"
UA = {"User-Agent": "pokeshell-build-carddata/1 (+https://github.com/gshklovs/pokeshell)"}
FORMAT = "pokeshell-carddata/1"
FIELDS = ["supertype", "hp", "types", "subtypes", "evolvesFrom", "abilities", "attacks", "weaknesses", "resistances",
          "retreatCost", "rules"]


def set_of(cid):
    return cid.rsplit("-", 1)[0] if "-" in cid else cid


def strs(xs):
    return [x for x in (xs or []) if isinstance(x, str)]


def gameplay(d):
    """an API card record (or a CARD_FORMAT file: the same field names) -> the carddata entry, every key present"""
    hp = str(d.get("hp") or "").strip()
    out = {
        "supertype": d.get("supertype") or "",
        "hp": int(hp) if hp.isdigit() else None,
        "types": strs(d.get("types")),
        "subtypes": strs(d.get("subtypes")),
        "evolvesFrom": d.get("evolvesFrom") or None,
        "abilities": [{"name": a.get("name") or "", "type": a.get("type") or "Ability", "text": a.get("text") or ""}
                      for a in d.get("abilities") or [] if isinstance(a, dict)],
        "attacks": [],
        "weaknesses": [{"type": w.get("type") or "", "value": w.get("value") or ""} for w in d.get("weaknesses") or [] if isinstance(w, dict)],
        "resistances": [{"type": w.get("type") or "", "value": w.get("value") or ""} for w in d.get("resistances") or [] if isinstance(w, dict)],
        "retreatCost": strs(d.get("retreatCost")),
        "rules": [r for r in d.get("rules") or [] if isinstance(r, str) and r.strip()],
    }
    for a in d.get("attacks") or []:
        if not isinstance(a, dict):
            continue
        cost = strs(a.get("cost"))
        cec = a.get("convertedEnergyCost")
        out["attacks"].append({"name": a.get("name") or "", "cost": cost,
                               "convertedEnergyCost": cec if isinstance(cec, int) else len(cost),
                               "damage": a.get("damage") or "", "text": a.get("text") or ""})
    return out


def looks_like_card(d, cid):
    return isinstance(d, dict) and d.get("id") == cid and ("supertype" in d or "attacks" in d)


def read_json(f):
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def get_json(url, tries=12):
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            if e.code in (400, 404):
                break
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
            last = str(e)
        wait = min(2 + 3 * i, 30)
        print(f"  {url}: {last}, retry in {wait} s", file=sys.stderr, flush=True)
        time.sleep(wait)
    print(f"  giving up on {url} ({last})", file=sys.stderr)
    return None


def fetch_set(sid, cache, offline, use_cache=True):
    """every API record of one set, {id: record}, from <cache>/<sid>.json or the API (then cached); None if unavailable"""
    f = cache / f"{sid}.json"
    d = read_json(f) if use_cache and f.exists() else None
    if isinstance(d, list):
        return {c["id"]: c for c in d if isinstance(c, dict) and c.get("id")}
    if offline:
        return None
    out, page = [], 1
    while True:
        q = urllib.parse.urlencode({"q": f"set.id:{sid}", "pageSize": 250, "page": page})
        r = get_json(f"{API}?{q}")
        if not r or not isinstance(r.get("data"), list):
            return None
        out += r["data"]
        if not r["data"] or len(out) >= int(r.get("totalCount") or 0):
            break
        page += 1
    if out:
        cache.mkdir(parents=True, exist_ok=True)
        tmp = f.with_name(f".{f.name}.{os.getpid()}.tmp")
        tmp.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, f)
    return {c["id"]: c for c in out if isinstance(c, dict) and c.get("id")}


def dump(pack, cards, missing):
    """the file text: a header line, then one card per line (the module doc)"""
    head = {"format": FORMAT, "pack": pack,
            "source": "pokemontcg.io v2 API card data (gameplay fields only), built by tools/build_carddata.py",
            "fields": FIELDS, "missing": missing}
    h = json.dumps(head, ensure_ascii=False, separators=(",", ":"))
    lines = [f"{json.dumps(cid, ensure_ascii=False)}:{json.dumps(cards[cid], ensure_ascii=False, separators=(',', ':'))}"
             for cid in cards]
    return h[:-1] + ',"cards":{\n' + ",\n".join(lines) + "\n}}\n"


def check(pack_ids, data):
    """problems of an existing carddata.json against pack.json: [(what, ids)]"""
    probs = []
    if not isinstance(data, dict) or data.get("format") != FORMAT or not isinstance(data.get("cards"), dict):
        return [("not a carddata file", [])]
    cards, missing = data["cards"], set(data.get("missing") or [])
    absent = [c for c in pack_ids if c not in cards and c not in missing]
    if absent:
        probs.append(("in pack.json but not in carddata.json (re-run tools/build_carddata.py)", absent))
    extra = [c for c in cards if c not in pack_ids]
    if extra:
        probs.append(("in carddata.json but not in pack.json", extra))
    bad = [c for c, v in cards.items() if not isinstance(v, dict) or any(k not in v for k in FIELDS)]
    if bad:
        probs.append(("entries without every field", bad))
    return probs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pack", default="pokemon")
    ap.add_argument("--root", default=str(HERE.parent), help="the pokeshell checkout (default: this file's)")
    ap.add_argument("--lab", default=None, help="the batches' data root (default: $ARTLAB_DATA, else <root>/style-lab)")
    ap.add_argument("--from", dest="from_dirs", action="append", default=[], help="another folder of <card id>.json")
    ap.add_argument("--cache", default=None, help="cached API responses (default: <root>/.cache/carddata)")
    ap.add_argument("--out", default=None, help="default: <root>/packs/<pack>/carddata.json")
    ap.add_argument("--refresh", action="store_true", help="every set again from the API (local copies ignored)")
    ap.add_argument("--offline", action="store_true", help="never touch the network: cards with no local data are gaps")
    ap.add_argument("--check", action="store_true", help="only check carddata.json against pack.json (exit 1 on a problem)")
    a = ap.parse_args()

    root = Path(a.root).resolve()
    pj = json.loads((root / "packs" / a.pack / "pack.json").read_text(encoding="utf-8"))
    pack_ids = list((pj.get("cards") or {}).keys())
    out = Path(a.out) if a.out else root / "packs" / a.pack / "carddata.json"
    old = read_json(out) if out.exists() else None

    if a.check:
        probs = check(pack_ids, old) if old is not None else [(f"{out} is missing", [])]
        for what, ids in probs:
            print(f"carddata: {what}: {len(ids)}{': ' + ' '.join(ids[:40]) if ids else ''}{' ...' if len(ids) > 40 else ''}")
        if old is not None and not probs:
            miss = old.get("missing") or []
            print(f"carddata: ok, {len(old['cards'])} of {len(pack_ids)} cards"
                  f"{f'; no API data for {len(miss)}: ' + ' '.join(miss) if miss else ''}")
        sys.exit(1 if probs else 0)

    lab = Path(a.lab) if a.lab else Path(os.environ.get("ARTLAB_DATA") or root / "style-lab")
    cache = Path(a.cache) if a.cache else root / ".cache" / "carddata"
    dirs = [root / "packs" / a.pack / "cards"]
    if lab.is_dir():
        for s in sorted(p for p in lab.iterdir() if p.is_dir()):
            dirs += [s / "cards" / "api", s / "cards"]
    dirs += [Path(x) for x in a.from_dirs]
    dirs = [d for d in dirs if d.is_dir()]
    kept = (old.get("cards") or {}) if isinstance(old, dict) and old.get("format") == FORMAT and not a.refresh else {}

    cards, how, need = {}, {"api cache": 0, "local": 0, "kept": 0, "api": 0}, {}
    set_cache = {}
    for cid in pack_ids:
        sid = set_of(cid)
        if not a.refresh:
            if sid not in set_cache:
                set_cache[sid] = fetch_set(sid, cache, offline=True)
            rec = (set_cache[sid] or {}).get(cid)
            if rec:
                cards[cid] = gameplay(rec); how["api cache"] += 1
                continue
            rec = next((d for d in (read_json(x / f"{cid}.json") for x in dirs if (x / f"{cid}.json").exists())
                        if looks_like_card(d, cid)), None)
            if rec:
                cards[cid] = gameplay(rec); how["local"] += 1
                continue
            if isinstance(kept.get(cid), dict) and all(k in kept[cid] for k in FIELDS):
                cards[cid] = kept[cid]; how["kept"] += 1
                continue
        need.setdefault(sid, []).append(cid)
        cards[cid] = None
    missing = []
    for sid, ids in need.items():
        got = None if a.offline else fetch_set(sid, cache, offline=False, use_cache=not a.refresh)
        for cid in ids:
            rec = (got or {}).get(cid)
            if rec:
                cards[cid] = gameplay(rec); how["api"] += 1
            else:
                missing.append(cid)
    cards = {k: v for k, v in cards.items() if v is not None}

    text = dump(a.pack, cards, missing)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(f".{out.name}.{os.getpid()}.tmp")
    tmp.write_bytes(text.encode("utf-8"))
    os.replace(tmp, out)
    src = ", ".join(f"{n} {k}" for k, n in how.items() if n)
    print(f"carddata: {len(cards)} of {len(pack_ids)} cards ({src}) -> {out} ({len(text.encode('utf-8')) / 1024:.0f} KB)")
    if missing:
        print(f"carddata: GAPS, no API data for {len(missing)} cards: {' '.join(missing)}")
        sys.exit(2)


if __name__ == "__main__":
    main()
