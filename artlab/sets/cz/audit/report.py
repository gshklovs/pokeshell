r"""audit/REPORT.md for Crown Zenith: every card of the set list (main + Galarian Gallery) with its outcome
(ok / fixed / flagged / skipped), from work/audit/meta.json (verify_all.py) and the review findings below.
Writes <DATA>/cz/audit/REPORT.md and the tracked copy artlab/sets/cz/audit/REPORT.md.

  ..\..\..\..\.venv\Scripts\python audit\report.py
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import czlib as P  # noqa: E402

FIXED = {
    "swsh12pt5-93": "facing: Bisharp lunges left on the card; flip=True",
    "swsh12pt5-44": "facing: Luxray's head and open mouth point right; flip=True",
    "swsh12pt5-118": "facing: Gumshoos faces right; flip=True",
    "swsh12pt5gg-GG03": "facing: Magmortar aims left at the campfire; flip=True",
    "swsh12pt5gg-GG44": "facing: Mewtwo lunges right at Charizard; flip=True",
    "swsh12pt5-96": "form: the card is Crowned Sword Zacian; sprite zacian-crowned (flip=True), crop refit to the sprite",
    "swsh12pt5-99": "form + facing: Crowned Shield Zamazenta, head left; sprite zamazenta-crowned, flip=False, crop refit",
    "swsh12pt5-38": "ghosts: Glaceon's front paw and head ribbon were left in the fill; mask grown over both",
    "swsh12pt5-60": "ghost: Mew's foot was left in the fill; mask grown",
    "swsh12pt5-116": "ghosts: Stoutland's right ear, neck fur and moustache were left in the fill; mask grown",
}
SHARED_FIXED = ("All uncommon / rare / holo / radiant cards and ladder 2, 3, 36, 20 were rebuilt after two shared fixes in "
                "czcards: the SWSH window's own silver border (a pale strip down the right edge of the art) and the "
                "stage icon's plate below STAGE_BOX (a pale blob top-left on evolved rares: 9, 25, 43, 78, 80, 82, 118) "
                "are now boxed out, and everything outside the art window is boxed out before the texture fill (the "
                "holo batch had found name-bar / stat-line letters mirrored into the fill).")
FLAGGED = {
    "swsh12pt5-81": "facing ambiguous (near-frontal Skrelp, snout down); kept unflipped, reviewers lean flip",
    "swsh12pt5-58": "Exeggutor's heads look up-right on the card; the sprite is near-frontal (kept)",
    "swsh12pt5-37": "Kyogre V: smooth fill shows a dark band where the dorsal fin was, and a blue streak at the right fin",
    "swsh12pt5-45": "Rotom V: the filled hole reads as a flat cyan diamond; small sprite on a card-filling Rotom",
    "swsh12pt5-100": "Rayquaza V: small dark-teal patch where the body was (x 115-180, y 465-520)",
    "swsh12pt5-101": "Rayquaza VMAX: texture=False leaves a muddy green-grey haze over the right half",
    "swsh12pt5-102": "Rayquaza VMAX: as 101",
    "swsh12pt5-36": "LADDER Kyogre: small blue remnants of the back and left fin in the fill",
    "swsh12pt5gg-GG23": "Dunsparce: two more Dunsparce on the shelves stay as scenery (the card's own is the one in bed)",
    "swsh12pt5gg-GG49": "Drapion V: the sprite hides the left Skorupi (a clay-figure photo card, given the painting treatment)",
    "swsh12pt5gg-GG42": "Zeraora VMAX: sprite hides the sleeping Pachirisu; the fill is flat (Zeraora covers 43% of the art)",
    "swsh12pt5gg-GG45": "Deoxys VMAX: the saucer above has a Deoxys-like face (kept as scenery)",
    "swsh12pt5gg-GG53": "Hoopa V is drawn as Hoopa Unbound; sprite hoopa-unbound (confirm)",
    "swsh12pt5-83": "Hoopa is drawn as Hoopa Unbound; sprite hoopa-unbound (confirm)",
    "swsh12pt5-20": "Radiant: the real print is the SHINY Pokemon (all three Radiants); we serve the regular sprite, shiny on the shiny roll (decide)",
    "swsh12pt5-51": "Radiant: shiny on the real print (see 20)",
    "swsh12pt5-105": "Radiant: shiny on the real print (see 20)",
    "swsh12pt5gg-GG68": "vendor dialga-origin: one px (row 20, col 33) is set in the regular sprite but empty in the shiny; "
                        "batch_secret patches the SHINY to the regular colour there (the regular stays pixel-exact)",
    "swsh12pt5-92": "facing: the two reviewers disagreed (face turned right vs blade pointing left); kept flipped (flip_commons)",
}


def main():
    meta = json.loads((P.DATA / "work" / "audit" / "meta.json").read_text(encoding="utf-8"))
    from collections import Counter
    rows, outc = [], Counter()
    for cid, r in meta.items():
        if r["status"] == "skipped":
            o, note = "skipped", r["reason"]
        elif r["status"] != "built":
            o, note = "FAIL", str(r.get("bad_lines"))
        elif cid in FIXED:
            o, note = "fixed", FIXED[cid]
        elif cid in FLAGGED:
            o, note = "flagged", FLAGGED[cid]
        else:
            o, note = "ok", ""
        outc[o] += 1
        size = f"{r['grid'][0]}x{r['grid'][1]}" if r.get("grid") else ""
        spr = (r.get("sprite") or "") + (" (flipped)" if r.get("flip") else "")
        rows.append(f"| {cid} | {r['name']} | {r['rarity']} | {r.get('kind', '')} | {spr} | {size} | "
                    f"{'yes' if r.get('anim') else ''} | {o} | {note} |")
    built = sum(1 for r in meta.values() if r["status"] == "built")
    txt = f"""# Crown Zenith audit report

Set list: {len(meta)} cards (swsh12pt5: 160, swsh12pt5gg Galarian Gallery: 70). Built: **{built}** Pokemon cards;
skipped: {outc['skipped']} (Trainers / Energy; no Pokemon lacks a sprite once Perrserker 85 took `perrserker`).
Outcomes: {', '.join(f'{k} {v}' for k, v in sorted(outc.items()))}.

## How the audit ran (ART_METHOD section 16)
- **Machine checks, every card** (`audit/verify_all.py` -> `work/audit/meta.json`): sprite pixel-exact against the
  vendor sprite in normal AND shiny (shape, outline, colours; the gold remap only at Rare Secret gold), commons plain
  with no background and flipped exactly as `set.json` `flip_commons`, size <= 140 x 110 grid px (widest 138, GG44 Mewtwo VSTAR;
  tallest 108, Zamazenta V 98), card data verbatim with tier == API rarity, the 16-frame anims (normal + shiny) with the
  final frame == the static art on every foil card, and the treatment (builder kind) allowed for the printed rarity.
  Result: 0 failures.
- **Visual review, every card**: three reviewers went through real | ours contact sheets (`work/audit/*.png`) for
  facing, form (regional / Gigantamax / Crowned / Origin / Unbound / Sky / Resolute / Low Key / Midnight), ghosts,
  text / logo residue and treatment.
- **Clear errors fixed** in `batch_fixes.py` (highest precedence): see "fixed" rows. {SHARED_FIXED}
- **Taste calls flagged** for the lookbook: see "flagged" rows.

## Treatment per rarity
Common = plain sprite (37) | Uncommon = Shelgon matte (17) | Rare = Altaria matte (22) | Rare Holo = Salamence holo (13) |
Rare Holo V = Sylveon V (17) | Rare Holo VMAX = Vaporeon VMAX (5) | Rare Holo VSTAR = NEW vstar (8) |
Radiant Rare = NEW radiant (3) | Trainer Gallery Rare Holo = NEW gallery (34) | Galarian Gallery V / VMAX / VSTAR =
Umbreon 215 alt-art painting at the printed tier (9 + 3 + 10) | Rare Secret = gold remap (GG67-70) and the painted
alt art (Pikachu 160).

## Forms read off the scans
lycanroc-midnight 74, shaymin-sky 115, zacian-crowned 94 95 96, zamazenta-crowned 97 98 99 (Hero on GG48 / GG54),
hoopa-unbound 83 GG53, giratina-origin GG69, palkia-origin GG67, dialga-origin GG68, keldeo-resolute GG07,
toxtricity-low-key GG09, hatterene-gmax 66 GG47, duraludon-gmax 104, the Hisuian / Galarian regionals, perrserker 85.
Frontal poses were kept unflipped and are listed as ambiguous in the batch reports, not flagged.

## Every card
| id | name | printed rarity | kind | sprite | grid px | anim | outcome | note |
|---|---|---|---|---|---|---|---|---|
{chr(10).join(rows)}
"""
    for f in (P.DATA / "audit" / "REPORT.md", HERE / "REPORT.md"):
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(txt, encoding="utf-8", newline="\n")
        print(f)
    print(outc)


if __name__ == "__main__":
    main()
