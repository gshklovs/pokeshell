r"""Fetch Brilliant Stars: the main set swsh9 (186 cards) AND its Trainer Gallery subset swsh9tg (30 cards)
into ONE data folder, <DATA>/brs, with artlab/tools/fetch_set.py's own helpers (User-Agent, retries with backoff,
files on disk kept, scans in several passes). set.json "subsets" lists the extra set ids.

The scans share one prefix: ref/swsh9_<number>.png, so the main cards are swsh9_1 .. _186 and the
gallery cards swsh9_TG01 .. _TG30 (the numbers never collide), and evlib.ref_path / lb_set find both.

  ..\..\..\.venv\Scripts\python fetch_brs.py [--ids id,id] [--no-scans] [--passes N]
"""
import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
sys.path.insert(0, str(HERE.parents[1]))
import artpaths  # noqa: E402
import fetch_set as F  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", default="")
    ap.add_argument("--no-scans", action="store_true")
    ap.add_argument("--passes", type=int, default=6)
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    meta = json.loads((HERE / "set.json").read_text(encoding="utf-8"))
    set_ids = [meta["set_id"]] + [s["set_id"] for s in meta.get("subsets", [])]
    prefix = meta["prefix"]
    d = artpaths.data("brs")
    for sub in ("cards/api", "ref", "work"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    lst = d / "setlist.json"
    cs = json.loads(lst.read_text(encoding="utf-8")) if lst.exists() else []
    have = Counter(c["set"]["id"] for c in cs)
    for sid in set_ids:
        if not have.get(sid):
            got = F.set_cards(sid)
            print(f"{sid}: {len(got)} cards")
            cs += got
    cs = sorted(cs, key=lambda c: (c["set"]["id"] != meta["set_id"], F.number_key(c)))
    lst.write_text(json.dumps(cs, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{len(cs)} cards  supertype {dict(Counter(c['supertype'] for c in cs))}")
    print(f"  rarity {dict(Counter((c['set']['id'], c.get('rarity')) for c in cs))}")
    only = {i for i in a.ids.split(",") if i}
    cs = [c for c in cs if not only or c["id"] in only]
    for c in cs:
        assert c["set"]["id"] in set_ids, c["id"]
        (d / "cards/api" / f"{c['id']}.json").write_text(json.dumps(c, indent=1, ensure_ascii=False), encoding="utf-8")
        (d / "cards" / f"{c['id']}.json").write_text(json.dumps(F.card_format(c), indent=1, ensure_ascii=False),
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
                (d / "ref" / f"{prefix}_{c['number']}.png").write_bytes(F.get(c["images"]["large"], tries=4, raw=True))
            except SystemExit as e:
                print("  skip", c["id"], e, flush=True)
        time.sleep(10)
    else:
        raise SystemExit("some scans are still missing: run again")


if __name__ == "__main__":
    main()
