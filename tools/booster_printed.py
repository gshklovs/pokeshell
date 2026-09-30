"""Fill packs/pokemon/boosters.json with printed-card counts, and check its rates.

Every outcome of a booster slot ("pick") covers some printed cards (a rarity, a set, explicit ids, a supertype). The
roll needs to know how many of them are printed, so that when we serve only some (Trainer / Energy cards, TAG TEAMs,
docs/SKIPPED.md) each served card keeps its real per-pack odds and the rest goes to the slot's base outcome
(docs/BOOSTERS.md). This counts them from the pokemontcg.io set lists (the same cache tools/skipped_report.py uses:
style-lab/<dir>/setlist-<set id>.json, or a setlist.json holding the set; fetched and cached when missing), writes
"printed" into every pick and "printed" (the whole set) into every set, and checks that each slot's rates add up to 1.

  .venv\\Scripts\\python tools\\booster_printed.py                   # rewrite boosters.json
  .venv\\Scripts\\python tools\\booster_printed.py --check           # only report (exit 1 on a problem)
  .venv\\Scripts\\python tools\\booster_printed.py --lab <style-lab>  # where the set lists are (default: the checkout's)
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOOSTERS = ROOT / "packs" / "pokemon" / "boosters.json"
sys.path.insert(0, str(Path(__file__).resolve().parent))


def find_setlist(lab, set_id):
    for f in sorted(lab.glob(f"*/setlist-{set_id}.json")):
        return json.loads(f.read_text(encoding="utf-8"))
    for f in sorted(lab.glob("*/setlist.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        d = d.get("data", d) if isinstance(d, dict) else d
        hit = [c for c in d if c["id"].rsplit("-", 1)[0] == set_id]
        if hit:
            return hit
    import skipped_report                       # fetch it from pokemontcg.io and cache it
    skipped_report.LAB = lab
    return skipped_report.setlist("boosters", set_id, False)


def matches(card, pick, default_sets):
    cset = card["id"].rsplit("-", 1)[0]
    if pick.get("ids"):
        return card["id"] in pick["ids"]
    if cset not in (pick.get("sets") or default_sets):
        return False
    if card["id"] in (pick.get("exclude") or []):
        return False
    if pick.get("rarity") and card.get("rarity") not in pick["rarity"]:
        return False
    if pick.get("supertype") and not (card.get("supertype") or "").startswith(pick["supertype"]):
        return False
    return True


def dump(o, ind=0, width=200):
    """JSON with short objects on one line (one pick per line), like the hand-written file"""
    flat = json.dumps(o, ensure_ascii=False)
    if len(flat) + ind <= width or not isinstance(o, (dict, list)) or not o:
        return flat
    pad = " " * (ind + 2)
    if isinstance(o, list):
        return "[\n" + ",\n".join(pad + dump(v, ind + 2, width) for v in o) + "\n" + " " * ind + "]"
    return "{\n" + ",\n".join(pad + json.dumps(k) + ": " + dump(v, ind + 2, width) for k, v in o.items()) + "\n" + " " * ind + "}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lab", default=str(ROOT / "style-lab"))
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    lab = Path(a.lab)
    data = json.loads(BOOSTERS.read_text(encoding="utf-8-sig"))
    problems, changed = [], 0
    for s in data["sets"]:
        printed = []
        for sid in sorted({x for sl in s["slots"] for p in sl["pick"] for x in (p.get("sets") or [])} | set(s["cardSets"])):
            printed += find_setlist(lab, sid)
        s_total = sum(1 for c in printed if c["id"].rsplit("-", 1)[0] in s["cardSets"])
        if s.get("printed") != s_total:
            s["printed"] = s_total; changed += 1
        for sl in s["slots"]:
            total = 0.0
            for p in sl["pick"]:
                n = sum(1 for c in printed if matches(c, p, s["cardSets"]))
                if p.get("printed") != n:
                    p["printed"] = n; changed += 1
                if n == 0:
                    problems.append(f"{s['id']} {sl['id']} '{p['label']}': matches no printed card")
                total += p.get("rate", 1.0)
            if abs(total - 1.0) > 0.00005:
                problems.append(f"{s['id']} {sl['id']}: rates add up to {total:.4f}, not 1")
            if sum(1 for p in sl["pick"] if p.get("base")) != 1:
                problems.append(f"{s['id']} {sl['id']}: needs exactly one base outcome")
    for p in problems:
        print("problem:", p, file=sys.stderr)
    if a.check:
        print(f"{len(data['sets'])} sets checked, {changed} printed counts out of date, {len(problems)} problems")
        sys.exit(1 if problems or changed else 0)
    order = ["pack", "about", "sources", "sets"]
    data = {k: data[k] for k in order if k in data} | {k: v for k, v in data.items() if k not in order}
    BOOSTERS.write_text(dump(data) + "\n", encoding="utf-8")
    print(f"{BOOSTERS.relative_to(ROOT)}: {changed} printed counts updated, {len(problems)} problems")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
