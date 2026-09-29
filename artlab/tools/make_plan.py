r"""plan.json for a set: every buildable Pokemon card, grouped by the build agent that owns it (docs/ART_METHOD.md,
step 3), with the colorscripts sprite each card gets. Generalised from artlab/sets/p30/make_plan.py.

  .venv\Scripts\python artlab\tools\make_plan.py <set folder> [--check]

Reads <DATA>/<folder>/setlist.json (tools/fetch_set.py) and artlab/sets/<folder>/set.json:
  groups   {API rarity: group}           one group per rarity family, e.g. "Rare Rainbow" + "Rare Secret" -> one
  split    {group: [group_a, group_b]}   a big group split in two halves (in card-number order)
  ladder   [ids]                         the approved one-per-rarity cards, left out (listed as _ladder_done)
  forms    {id: sprite}                  forms read off the scans (Dusk Lycanroc, Crowned Zacian, Sunshine Cherrim ...)
  notes    {id: text}                    carried into the card's entry
Writes artlab/sets/<folder>/plan.json (tracked). --check compares with the existing plan.json instead of writing.

Sprite choice, in order: forms[id]; a Gigantamax card (an attack named "G-Max ...") takes <name>-gmax when the vendor
has it; regional prefixes map to -alola / -galar / -hisui / -paldea; then the lower-cased name with the badge (V,
VMAX, VSTAR, ex, GX ...) stripped and accents folded. Trainers / Energy and cards with no colorscripts sprite (Gen 9)
go to _skipped with the reason. ALWAYS check forms against the scans: the API name does not say Dusk / Midnight.
"""
import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import artpaths  # noqa: E402

REGULAR = artpaths.VENDOR / "pokemon-colorscripts" / "colorscripts" / "large" / "regular"
BADGE = re.compile(r"\s+(V|VMAX|VSTAR|V-UNION|ex|EX|GX|LV\.X|BREAK|Prime|LEGEND|δ|☆|◇|star)$")
REGION = {"Alolan ": "-alola", "Galarian ": "-galar", "Hisuian ": "-hisui", "Paldean ": "-paldea"}
SPECIAL = {"Nidoran ♀": "nidoran-f", "Nidoran ♂": "nidoran-m", "Mr. Mime": "mr-mime", "Mime Jr.": "mime-jr",
           "Mr. Rime": "mr-rime", "Farfetch'd": "farfetchd", "Sirfetch'd": "sirfetchd", "Type: Null": "type-null"}


def fold(s):
    return "".join(ch for ch in unicodedata.normalize("NFKD", s) if not unicodedata.combining(ch))


def sprite(c, forms):
    if c["id"] in forms:
        return forms[c["id"]]
    n = BADGE.sub("", c["name"].strip())
    base = SPECIAL.get(n)
    if base is None:
        suf = ""
        for pre, s in REGION.items():
            if n.startswith(pre):
                n, suf = n[len(pre):], s
        base = re.sub(r"[^a-z0-9]+", "-", re.sub(r"[.'’:]", "", fold(n).lower())).strip("-") + suf
    if any(a.get("name", "").startswith("G-Max") for a in c.get("attacks") or []) and (REGULAR / f"{base}-gmax").exists():
        return f"{base}-gmax"
    return base


def plan_for(folder):
    meta = json.loads((artpaths.code(folder) / "set.json").read_text(encoding="utf-8"))
    cs = json.loads((artpaths.data(folder) / "setlist.json").read_text(encoding="utf-8"))
    groups, forms, notes = meta["groups"], meta.get("forms", {}), meta.get("notes", {})
    notes = notes if isinstance(notes, dict) else {}
    ladder = set(meta.get("ladder", []))
    plan = {g: [] for g in dict.fromkeys(groups.values())}
    skipped = []
    for c in cs:
        if c["supertype"] not in ("Pokémon", "Pokemon"):
            skipped.append({"id": c["id"], "name": c["name"], "reason": f"{c['supertype']} (no Pokemon)"})
            continue
        if c.get("rarity") not in groups:
            skipped.append({"id": c["id"], "name": c["name"], "reason": f"rarity {c.get('rarity')!r} has no group in set.json"})
            continue
        s = sprite(c, forms)
        if not (REGULAR / s).exists():
            skipped.append({"id": c["id"], "name": c["name"], "reason": f"no colorscripts sprite ({s})"})
            continue
        if c["id"] in ladder:
            continue
        e = {"id": c["id"], "name": c["name"], "number": c["number"], "rarity": c["rarity"], "sprite": s}
        if c["id"] in notes:
            e["note"] = notes[c["id"]]
        plan[groups[c["rarity"]]].append(e)
    for g, halves in meta.get("split", {}).items():
        v = plan.pop(g)
        k = (len(v) + 1) // 2
        plan[halves[0]], plan[halves[1]] = v[:k], v[k:]
    return {**plan, "_skipped": skipped, "_ladder_done": sorted(ladder)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    out = plan_for(a.folder)
    f = artpaths.code(a.folder) / "plan.json"
    if a.check:
        old = json.loads(f.read_text(encoding="utf-8"))
        want = {c["id"]: (g, c.get("sprite")) for g, v in old.items() if not g.startswith("_") for c in v}
        got = {c["id"]: (g, c["sprite"]) for g, v in out.items() if not g.startswith("_") for c in v}
        for cid in sorted(set(want) | set(got)):
            if want.get(cid) != got.get(cid):
                print(f"  {cid:10s} plan.json {want.get(cid)}  generated {got.get(cid)}")
        print(f"{len(want)} cards in plan.json, {len(got)} generated")
        return
    f.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    for g, v in out.items():
        print(f"{g:18s} {len(v)}")
    print("skipped: " + ", ".join(f"{s['id']} {s['name']} ({s['reason']})" for s in out["_skipped"]))


if __name__ == "__main__":
    main()
