r"""audit/REPORT.md for Brilliant Stars: every card of the set list (main + Trainer Gallery) with its outcome
(ok / fixed / flagged / skipped), from work/audit/meta.json (verify_all.py) and the review findings below.
Writes <DATA>/brs/audit/REPORT.md and the tracked copy artlab/sets/brs/audit/REPORT.md.

  ..\..\..\..\.venv\Scripts\python audit\report.py
"""
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import brslib as P  # noqa: E402

FIXED = {
    "swsh9-44": "form: the card is Noice Face Eiscue (ice block shattered); sprite eiscue-noice",
    "swsh9-2": "ghost: Exeggutor's outer leaf tips were left in the sky; mask grown",
    "swsh9-5": "ghost: a green sliver of Tropius's head leaf / wing at the left edge; mask grown",
    "swsh9-25": "ghost: Monferno's outstretched hand and forearm; mask grown",
    "swsh9-39": "ghost: Floatzel's lower tail wisps; mask grown",
    "swsh9-55": "ghost: Starmie's lower-left star point; mask grown",
    "swsh9-93": "ghost: Morgrem's claws (left hand, lower right); mask grown",
    "swsh9-118": "ghost: Staravia's right wing tip and left wing-tip feathers; mask grown",
    "swsh9-48": "ghost: Raikou's zig-zag lightning tail top left; mask grown",
    "swsh9-152": "LADDER ghost: Shaymin's two white wing tips; mask grown",
    "swsh9-154": "LADDER ghost: a Charizard wing-tip remnant by the head; mask grown",
    "swsh9-155": "ghost: Lumineon's long tail fin, lower fin and top-right fin tip; mask grown",
    "swsh9-157": "ghost: Pikachu's black ear tip and the tail corner; mask grown",
    "swsh9-161": "ghost: the tips of Honchkrow's hat plume; mask grown",
    "swsh9tg-TG21": "ghost: G-Max Urshifu's giant fist lower left; mask grown (Mustard kept)",
    "swsh9tg-TG19": "ghost: red hair tips top left, kept by a scenery cut; the cut starts lower",
}
FLAGGED = {
    "swsh9-93": "facing: Morgrem crawls left in 3/4 view; flipped (the reviewer leans unflipped) -- decide",
    "swsh9-116": "facing: Castform's eye/mouth on the right (flip_commons), but its tail curl then opposes the card",
    "swsh9-84": "facing: Grimer's head right, arm/body reaching left; kept unflipped",
    "swsh9-12": "facing: Cherubi's face slightly right; kept unflipped",
    "swsh9-124": "facing: Minccino looks left in 3/4 with the tail swept left; flipped (borderline)",
    "swsh9-125": "Cinccino: white sprite on a pale snow fill (low contrast); a pale block left of the head may be scarf fur",
    "swsh9-41": "facing: Manaphy frontal; flipped on the antenna's trail",
    "swsh9-76": "facing: Flygon's head frontal / diving; flipped on the tail curl",
    "swsh9-79": "facing: Lucario faces left (unflipped) but the sprite's snout can read right at pixel scale",
    "swsh9-4": "facing: Breloom 3/4 turned right, near-frontal sprite kept unflipped; faint grey smear by the raised arm",
    "swsh9-165": "facing: Arceus V full art: head points left, body mirrored; flipped on the body",
    "swsh9-176": "facing: Arceus VSTAR rainbow flipped to match gold 184 (same illustration); snout points left/down",
    "swsh9-175": "facing: Whimsicott near-frontal, flipped (barely shows)",
    "swsh9tg-TG19": "facing: G-Max Urshifu's fist goes right (flipped), the mask-face is frontal-to-left",
    "swsh9tg-TG22": "LADDER facing: Umbreon's head turned left (kept), the body walks right",
    "swsh9-105": "form: Zamazenta V drawn in the Crowned Shield armour; sprite zamazenta-crowned (as 163 and cz 98)",
    "swsh9-173": "Shaymin VSTAR rainbow: an orange-brown smear at the top edge of the ground (maybe the head crest)",
    "swsh9-69": "Mimikyu VMAX: a small dark smudge from the shadow-tail along the top edge",
    "swsh9tg-TG05": "Zekrom: N's green hair shows through a gap inside the sprite (scenery, N kept); right side a dark smooth fill",
    "swsh9tg-TG10": "Houndoom: faint grey smear above Grimsley where the horn was; small sprite",
    "swsh9tg-TG08": "vendor alcremie: the regular and shiny sprites differ by one pixel; batch_tg / batch_rare_a patch "
                    "the SHINY load (the regular stays pixel-exact)",
    "swsh9-71": "vendor alcremie: see TG08",
}
SKIP_NOTE = {"swsh9tg-TG20": "no colorscripts sprite: the vendor has no non-Gigantamax Rapid Strike Urshifu "
                             "(only urshifu-rapid-strike-gmax); the Single Strike form would be the wrong form"}
FORMS = """shaymin-sky 13 14 152 173, wormadam 10 / wormadam-sandy 77 / wormadam-trash 98, burmy (plant) 9, morpeko-hangry 95,
zamazenta-crowned 105 163, eiscue-noice 44, kingler-gmax 29, urshifu 18 / urshifu-gmax TG19 TG29 /
urshifu-rapid-strike-gmax TG21 TG30, the Galarian birds 181-183, alcremie (vanilla cream strawberry) 71 TG08,
tornadus (Incarnate) 126, zarude (no cape) 16. The Dynamax VMAXes (Mimikyu 69 TG17, Aggron 97, Sylveon TG15,
Umbreon TG23) use the plain sprites."""


def main():
    meta = json.loads((P.DATA / "work" / "audit" / "meta.json").read_text(encoding="utf-8"))
    rows, outc, kinds = [], Counter(), Counter()
    for cid, r in meta.items():
        if r["status"] == "skipped":
            o, note = "skipped", SKIP_NOTE.get(cid, r["reason"])
        elif r["status"] != "built":
            o, note = "FAIL", str(r.get("bad_lines"))
        elif cid in FIXED:
            o, note = "fixed", FIXED[cid] + ("; FLAG: " + FLAGGED[cid] if cid in FLAGGED else "")
        elif cid in FLAGGED:
            o, note = "flagged", FLAGGED[cid]
        else:
            o, note = "ok", ""
        outc[o] += 1
        if r["status"] == "built":
            kinds[(r["rarity"], r["kind"])] += 1
        size = f"{r['grid'][0]}x{r['grid'][1]}" if r.get("grid") else ""
        spr = (r.get("sprite") or "") + (" (flipped)" if r.get("flip") else "")
        rows.append(f"| {cid} | {r['name']} | {r['rarity']} | {r.get('kind', '')} | {spr} | {size} | "
                    f"{'yes' if r.get('anim') else ''} | {o} | {note} |")
    built = sum(1 for r in meta.values() if r["status"] == "built")
    per = " | ".join(f"{rar} = {k} ({n})" for (rar, k), n in sorted(kinds.items()))
    nl = "\n"
    txt = f"""# Brilliant Stars audit report

Set list: {len(meta)} cards (swsh9: 186, swsh9tg Trainer Gallery: 30). Built: **{built}** Pokemon cards;
skipped: {outc['skipped']} (Trainers / Energy, and Rapid Strike Urshifu V TG20: no sprite for its form).
Outcomes: {', '.join(f'{k} {v}' for k, v in sorted(outc.items()))}.

## How the audit ran (ART_METHOD section 16)
- **Machine checks, every card** (`audit/verify_all.py` -> `work/audit/meta.json`): sprite pixel-exact against the
  vendor sprite in normal AND shiny (shape, outline, colours; the gold remap only at Rare Secret, the 0.55 rainbow
  re-tint only at Rare Rainbow), commons plain with no background and flipped exactly as `set.json` `flip_commons`,
  size <= 140 x 110 grid px, card data verbatim with tier == API rarity, the 16-frame anims (normal + shiny) with
  the final frame == the static art on every foil card, and the treatment (builder kind) allowed for the printed
  rarity (Rare Ultra: the four painted alt arts 154 / 156 / 162 / 166 = alt, the rest fullart; Trainer Gallery
  V / VMAX = alt). Result: 0 failures.
- **Visual review, every card**: three reviewers went through real | ours contact sheets (`work/audit/*.png`), with
  zooms and mask overlays, for facing, form, ghosts, text / logo residue and treatment.
- **Clear errors fixed** in `batch_fixes.py` (highest precedence): see "fixed" rows; before / after in
  `work/audit/fixed_*.png` (real | before | after).
- **Taste calls flagged** for the lookbook: see "flagged" rows.

## Treatment per rarity (printed rarity = kind (cards))
{per}

## Forms read off the scans
{FORMS}

## Every card
| id | name | printed rarity | kind | sprite | grid px | anim | outcome | note |
|---|---|---|---|---|---|---|---|---|
{nl.join(rows)}
"""
    for f in (P.DATA / "audit" / "REPORT.md", HERE / "REPORT.md"):
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(txt, encoding="utf-8", newline="\n")
        print(f)
    print(outc)


if __name__ == "__main__":
    main()
