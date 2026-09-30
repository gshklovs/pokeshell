"""Write docs/SKIPPED.md: every card of every imported set that pokeshell does NOT serve, and why.

For each set below it reads the full printed card list from pokemontcg.io (cached in style-lab/<dir>/setlist-<id>.json,
so later runs are offline), compares it with the cards packs/pokemon/pack.json serves (a built dist/pokemon/<char>-<id>.ans),
and gives each missing card a reason: Trainer / Energy, TAG TEAM (several Pokemon on one card), no dotfiles sprite
for that Pokemon or form, or an override from SETS[...]["why"]. Anything left as "not built" is a gap to look at.

  .venv\\Scripts\\python tools\\skipped_report.py            # refresh docs/SKIPPED.md
  .venv\\Scripts\\python tools\\skipped_report.py --refetch  # re-download the set lists

Add a set to SETS when you import it (docs/ART_METHOD.md, definition of done).
"""
import argparse
import json
import re
import sys
import time
import unicodedata
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LAB = ROOT / "style-lab"
VENDOR = ROOT / "vendor" / "pokemon-colorscripts" / "colorscripts" / "small" / "regular"
PACK = ROOT / "packs" / "pokemon" / "pack.json"
DIST = ROOT / "dist" / "pokemon"
OUT = ROOT / "docs" / "SKIPPED.md"
API = "https://api.pokemontcg.io/v2/cards?q=set.id:{}&pageSize=250&page={}&select=id,name,number,supertype,subtypes,rarity"

# name, data dir under style-lab, pokemontcg set ids, and reasons for Pokemon cards skipped on purpose
SETS = [
    ("Evolving Skies", "evs", ["swsh7"], {}),
    ("30th Celebration", "p30", ["me55"], {}),
    ("Crown Zenith + Galarian Gallery", "cz", ["swsh12pt5", "swsh12pt5gg"], {}),
    ("Hidden Fates + Shiny Vault", "hf", ["sm115", "sma"], {}),
    ("Base Set", "base", ["base1"], {}),
    ("Brilliant Stars + Trainer Gallery", "brs", ["swsh9", "swsh9tg"],
     {"swsh9tg-TG20": "no dotfiles sprite for Rapid Strike Urshifu (only its Gigantamax form), and the Single Strike "
                      "sprite would be the wrong form"}),
    ("Neo Genesis", "neo1", ["neo1"], {}),
    ("Lost Origin + Trainer Gallery", "lor", ["swsh11", "swsh11tg"],
     {"swsh11tg-TG22": "the card is Eternamax Eternatus: its dotfiles sprite is 56 rows (112 grid px), over the "
                       "110 cap, and the plain Eternatus sprite would be the wrong form"}),
]


def fetch(set_id):
    cards, page = [], 1
    while True:
        for attempt in range(6):
            try:
                req = urllib.request.Request(API.format(set_id, page), headers={"User-Agent": "pokeshell-skipped-report/1"})
                with urllib.request.urlopen(req, timeout=60) as r:
                    data = json.load(r)
                break
            except Exception as e:  # pokemontcg.io is flaky: retry with backoff
                if attempt == 5:
                    raise SystemExit(f"{set_id} page {page}: {e}")
                time.sleep(2 + attempt * 3)
        cards += data["data"]
        if page * data["pageSize"] >= data["totalCount"]:
            return cards
        page += 1


def setlist(dirname, set_id, refetch):
    cache = LAB / dirname / f"setlist-{set_id}.json"
    if cache.exists() and not refetch:
        return json.loads(cache.read_text(encoding="utf-8"))
    cards = fetch(set_id)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(cards, ensure_ascii=False, indent=1), encoding="utf-8")
    return cards


def squash(s):
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", s.lower().replace("♀", "f").replace("♂", "m"))


def has_sprite(name):
    """is there a colorscripts sprite whose base name appears in the card name (Radiant Charizard -> charizard)"""
    words = [squash(w) for w in re.split(r"[\s\-]+", name) if squash(w)]
    grams = {"".join(words[i:j]) for i in range(len(words)) for j in range(i + 1, min(len(words), i + 3) + 1)}
    return any(squash(d.name) in grams or squash(d.name.split("-")[0]) in grams for d in SPRITES)


SPRITES = sorted(VENDOR.iterdir()) if VENDOR.exists() else []


def reason(card, why):
    if card["id"] in why:
        return why[card["id"]]
    if card.get("supertype") == "Trainer":
        return "Trainer"
    if card.get("supertype") == "Energy":
        return "Energy"
    if "&" in card["name"] or "TAG TEAM" in (card.get("subtypes") or []):
        return "TAG TEAM: several Pokémon on one card, too many sprites for one card"
    if not has_sprite(card["name"]):
        return "no dotfiles sprite for this Pokémon (pokemon-colorscripts stops at Gen 8)"
    return "not built (check the set's audit)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refetch", action="store_true")
    a = ap.parse_args()
    pack = json.loads(PACK.read_text(encoding="utf-8"))["cards"]
    served = {cid for cid, c in pack.items() if (DIST / f"{c['character']}-{cid}.ans").exists()}
    lines = ["# Skipped cards", "",
             "Every printed card of the imported sets that pokeshell does not serve, and why. Written by",
             "`tools/skipped_report.py` (re-run it after importing a set). Trainer and Energy cards have no Pokémon, so",
             "they're counted per set and listed at the bottom of each set; Pokémon cards are listed one by one.", ""]
    total_poke = total_other = 0
    summary = ["| Set | Printed | Served | Skipped Pokémon | Skipped Trainer / Energy |", "|---|---|---|---|---|"]
    body = []
    for name, dirname, ids, why in SETS:
        cards = [c for sid in ids for c in setlist(dirname, sid, a.refetch)]
        skipped = [(c, reason(c, why)) for c in cards if c["id"] not in served]
        poke = [(c, r) for c, r in skipped if r not in ("Trainer", "Energy")]
        other = [c for c, r in skipped if r in ("Trainer", "Energy")]
        total_poke += len(poke)
        total_other += len(other)
        summary.append(f"| {name} | {len(cards)} | {len(cards) - len(skipped)} | {len(poke)} | {len(other)} |")
        body += [f"## {name} ({', '.join(ids)})", ""]
        if poke:
            body += ["| Card | Number | Rarity | Why |", "|---|---|---|---|"]
            body += [f"| {c['name']} | {c['id']} | {c.get('rarity') or '-'} | {r} |" for c, r in poke]
        else:
            body += ["Every Pokémon card is served."]
        if other:
            tr = [c for c in other if c.get("supertype") == "Trainer"]
            en = [c for c in other if c.get("supertype") == "Energy"]
            body += ["", f"Trainer and Energy ({len(other)}): "
                     + ", ".join(f"{c['name']} {c['number']}" for c in tr + en) + "."]
        body.append("")
    lines += summary + ["", f"In all: {total_poke} Pokémon cards and {total_other} Trainer / Energy cards skipped.", ""] + body
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"{OUT.relative_to(ROOT)}: {total_poke} Pokémon + {total_other} Trainer/Energy skipped across {len(SETS)} sets")


if __name__ == "__main__":
    sys.exit(main())
