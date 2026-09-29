r"""plan.json: every remaining 30th Celebration Pokemon card (the 7 approved ladder cards are done), grouped by
the build agent that owns it, with its colorscripts sprite (form sprites read off the scans). Trainers and the 9
Gen 9 cards with no colorscripts sprite are left out (listed under "_skipped").

  ..\..\..\.venv\Scripts\python make_plan.py
"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent            # plan.json is written here (a tracked recipe)
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import artpaths  # noqa: E402
DATA = artpaths.data("p30")                       # setlist.json (the API records)
VENDOR = artpaths.VENDOR / "pokemon-colorscripts" / "colorscripts" / "large" / "regular"
LADDER = {"me55-9", "me55-65", "me55-23", "me55-92", "me55-131", "me55-154", "me55-157"}
GROUP = {"Common": "commons", "Rare": "rare", "Pikachu Rare": "pikachu_rare", "Double Rare": "double_rare",
         "Illustration Rare": "illustration_rare", "Special Illustration Rare": "sir_futuristic",
         "Futuristic Rare": "sir_futuristic"}
# forms, read off the scans (work/cforms*.png)
FORM = {"me55-7": "cherrim-sunshine",        # pink, petals open
        "me55-8": "vivillon-poke-ball",      # red / black / white Poke Ball wing pattern
        "me55-59": "toxtricity-low-key",     # pale blue-violet spikes (60 and 134 are the yellow Amped Form)
        "me55-85": "lycanroc-midnight", "me55-138": "lycanroc-midnight",
        "me55-124": "minior-red",            # core form, red / pink core
        "me55-106": "zacian-crowned", "me55-107": "zamazenta-crowned",
        "me55-72": "unown"}                  # a crowd of letters; the A sprite
SPECIAL = {"Nidoran ♀": "nidoran-f"}


def sprite(c):
    if c["id"] in FORM:
        return FORM[c["id"]]
    n = c["name"].removesuffix(" ex")
    if n in SPECIAL:
        return SPECIAL[n]
    for pre, suf in (("Alolan ", "-alola"), ("Galarian ", "-galar"), ("Hisuian ", "-hisui")):
        if n.startswith(pre):
            return n[len(pre):].lower() + suf
    return n.lower().replace(" ", "-")


def main():
    cs = json.loads((DATA / "setlist.json").read_text(encoding="utf-8"))
    plan = {g: [] for g in dict.fromkeys(GROUP.values())}
    skipped = []
    for c in cs:
        if c["supertype"] != "Pokémon":
            skipped.append({"id": c["id"], "name": c["name"], "reason": "Trainer (no Pokemon)"})
            continue
        s = sprite(c)
        if not (VENDOR / s).exists():
            skipped.append({"id": c["id"], "name": c["name"], "reason": f"no colorscripts sprite ({s}, Gen 9)"})
            continue
        if c["id"] in LADDER:
            continue
        e = {"id": c["id"], "name": c["name"], "number": c["number"], "rarity": c["rarity"], "sprite": s}
        if c["number"] in ("B", "G", "R"):
            e["note"] = "monochrome YOSHIROTTEN Mew the API labels Common: commons rule, plain sprite"
        plan[GROUP[c["rarity"]]].append(e)
    out = {**plan, "_skipped": skipped, "_ladder_done": sorted(LADDER)}
    (HERE / "plan.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    for g, v in plan.items():
        print(f"{g:18s} {len(v)}")
    print(f"skipped {len(skipped)}: " + ", ".join(f"{s['id']} {s['name']}" for s in skipped))


if __name__ == "__main__":
    main()
