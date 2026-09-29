r"""plan.json for Crown Zenith: artlab/tools/make_plan.py's plan (same sprite choice, same skips), with one addition
for the Galarian Gallery subset: its cards (swsh12pt5gg, numbers GG01..GG70) go to the groups in set.json
"gg_groups" instead of "groups". The printed rarity (the tier) stays the API's: a GG Rare Holo V is still tier
Rare Holo V, only its finish (the alt-art painting) differs from the main set's V cards.

  ..\..\..\.venv\Scripts\python plan_cz.py [--check]
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
sys.path.insert(0, str(HERE.parents[1]))
import artpaths  # noqa: E402
import make_plan as MP  # noqa: E402


def plan():
    meta = json.loads((HERE / "set.json").read_text(encoding="utf-8"))
    cs = json.loads((artpaths.data("cz") / "setlist.json").read_text(encoding="utf-8"))
    forms, notes = meta.get("forms", {}), meta.get("notes", {}) or {}
    ladder = set(meta.get("ladder", []))
    gg = {s["set_id"] for s in meta.get("subsets", [])}
    groups = list(dict.fromkeys(list(meta["groups"].values()) + list(meta["gg_groups"].values())))
    out = {g: [] for g in groups}
    skipped = []
    for c in cs:
        table = meta["gg_groups"] if c["set"]["id"] in gg else meta["groups"]
        if c["supertype"] not in ("Pokémon", "Pokemon"):
            skipped.append({"id": c["id"], "name": c["name"], "reason": f"{c['supertype']} (no Pokemon)"})
            continue
        if c.get("rarity") not in table:
            skipped.append({"id": c["id"], "name": c["name"], "reason": f"rarity {c.get('rarity')!r} has no group"})
            continue
        s = MP.sprite(c, forms)
        if not (MP.REGULAR / s).exists():
            skipped.append({"id": c["id"], "name": c["name"], "reason": f"no colorscripts sprite ({s})"})
            continue
        if c["id"] in ladder:
            continue
        e = {"id": c["id"], "name": c["name"], "number": c["number"], "rarity": c["rarity"], "sprite": s}
        if c["id"] in notes:
            e["note"] = notes[c["id"]]
        out[table[c["rarity"]]].append(e)
    for g, halves in meta.get("split", {}).items():
        v = out.pop(g)
        k = (len(v) + 1) // 2
        out[halves[0]], out[halves[1]] = v[:k], v[k:]
    out = {g: v for g, v in out.items() if v}
    return {**out, "_skipped": skipped, "_ladder_done": sorted(ladder)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    p = plan()
    f = HERE / "plan.json"
    if a.check:
        old = json.loads(f.read_text(encoding="utf-8"))
        print("same" if old == p else "DIFFERS")
        return
    f.write_text(json.dumps(p, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    for g, v in p.items():
        print(f"{g:14s} {len(v)}")
    print("skipped: " + ", ".join(f"{s['id']} {s['name']} ({s['reason']})" for s in p["_skipped"]
                                  if "no Pokemon" not in s["reason"]))


if __name__ == "__main__":
    main()
