r"""Fetch the full 30th Celebration list (me55) and its Classic Collection subset (me55c) from pokemontcg.io v2.
-> setlist.json (me55, every card, full API records), setlist-me55c.json, and a summary printed.
  ..\..\..\.venv\Scripts\python fetch_set.py
"""
import json, time, urllib.request
from collections import Counter
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import artpaths  # noqa: E402
HERE = artpaths.data("p30")                       # setlist*.json (API records: data)
UA = {"User-Agent": "pokeshell-fetch-cards/1"}


def get(url, tries=10, raw=False):
    for i in range(tries):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90).read()
            return r if raw else json.loads(r)
        except Exception as e:
            print(f"  {url}: {e}, retry", flush=True)
            time.sleep(min(60, 2 + 3 * i))
    raise SystemExit(f"giving up on {url}")


def cards(sid):
    out, page = [], 1
    while True:
        d = get(f"https://api.pokemontcg.io/v2/cards?q=set.id:{sid}&pageSize=250&page={page}")
        out += d["data"]
        if len(out) >= d["totalCount"] or not d["data"]:
            return out
        page += 1


def key(c):
    n = c["number"]
    return (int("".join(ch for ch in n if ch.isdigit()) or 0), n)


def main():
    for sid, fn in (("me55", "setlist.json"), ("me55c", "setlist-me55c.json")):
        cs = sorted(cards(sid), key=key)
        (HERE / fn).write_text(json.dumps(cs, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"== {sid}: {len(cs)} cards")
        print(" supertype:", dict(Counter(c["supertype"] for c in cs)))
        print(" rarity   :", dict(Counter(c.get("rarity") for c in cs)))


if __name__ == "__main__":
    main()
