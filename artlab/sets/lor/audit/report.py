r"""audit/REPORT.md for Lost Origin: every card of the set list (main + Trainer Gallery) with its outcome
(ok / fixed / flagged / skipped), from work/audit/meta.json (verify_all.py) and the review findings below.
Writes <DATA>/lor/audit/REPORT.md and the tracked copy artlab/sets/lor/audit/REPORT.md.

  ..\..\..\..\.venv\Scripts\python audit\report.py
"""
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import lorlib as P  # noqa: E402

EVO_NOTE = "text: the 'Evolves from' plate (STAGE_BOX stops at x 312, the plate at ~x 420) smeared into the top of the art; plate boxed out"
FIXED = {
    **{f"swsh11-{n}": EVO_NOTE for n in (5, 10, 22, 32, 34, 55, 61, 63, 73, 78)},
    "swsh11-2": "LADDER " + EVO_NOTE,
    "swsh11-53": "LADDER " + EVO_NOTE,
    "swsh11-66": "LADDER " + EVO_NOTE,
    "swsh11tg-TG16": "LADDER ghost: the real Pikachu's ear tips (a yellow / black streak by the head); mask grown",
    "swsh11-133": "ghost: Hisuian Sliggoo's second horn (a lavender block over the ears); mask grown",
    "swsh11-58": "ghost: the tip of Rotom's orange head spike and its plasma rim; mask grown",
    "swsh11-82": "ghost: Enamorus's heart-ribbon tail (upper-left arc, lower-right band); mask grown",
    "swsh11-39": "facing: both Shellos on the card face right; added to set.json flip_commons",
}
FLAGGED = {
    "swsh11-29": "form: the card is the FEMALE Pyroar (no mane); the vendor only has the male pyroar sprite",
    "swsh11-34": "facing: Dewgong flipped on the face (head and mouth right), but the body layout matches the unflipped sprite",
    "swsh11-142": "facing: Porygon-Z flipped on the eye / beak, the body layout is mirrored",
    "swsh11-55": "facing: Manectric frontal, flipped on the body trailing left",
    "swsh11-78": "pose: Malamar is upside down on the card; the upright sprite is used",
    "swsh11-115": "facing: Honchkrow three-quarter frontal, kept unflipped",
    "swsh11-143": "pose: Snorlax lies asleep on the card; the vendor sprite sits frontal",
    "swsh11-27": "facing: Delphox V three-quarter, snout turned right; kept unflipped (near-frontal), flip=True arguable",
    "swsh11-135": "facing: Hisuian Goodra V shell left / head right but looking left-down; flipped on the body",
    "swsh11-118": "facing: Drapion V frontal, unflipped (182, another illustration, is flipped)",
    "swsh11-182": "facing: Drapion V full art frontal, flipped on the tail alone",
    "swsh11-177": "facing: Rotom V alt art, the face turned right on the card, the frontal sprite kept unflipped; the true-size sprite covers much of the junk-pile painting",
    "swsh11-172": "Hisuian Electrode V: one giant ball face on the card; the small sprite sits in a mostly smooth lightning fill",
    "swsh11-123": "Radiant Hisuian Sneasler: the colorscripts SHINY sprite (olive, dark head) does not match the card's printed cream / purple shiny",
    "swsh11-213": "Hisuian Zoroark VSTAR gold: a mostly white / red / grey sprite, the gold remap gives many close mid-golds (lower contrast than 212)",
    "swsh11-7": "facing: Silcoon flipped on the eye right of centre; unflipped arguably matches better",
    "swsh11-9": "facing: Cascoon flipped on the eye right of centre; unflipped arguably matches better",
    "swsh11-138": "facing: Lickitung sprawled, flipped on the tongue reaching right (flip_commons, judgement call)",
    "swsh11-150": "facing: Skwovet frontal, flipped on the tail rising on the left (flip_commons, judgement call)",
    "swsh11-144": "facing: Aipom frontal, leaning right, kept unflipped",
    "swsh11-102": "the card shows BOTH Gastrodon (West left, East right): both painted out, the West sprite on the left one",
    "swsh11tg-TG13": "Orbeetle VMAX: the pink tube / beam kept as G-Max energy (cut_after); a ghost if they are the Pokemon's body",
    "swsh11tg-TG06": "facing: Gengar near-frontal, flipped on the face right of the body",
    "swsh11tg-TG18": "facing: Enamorus V near-frontal, flipped on the raised arm; the fill round the trainer is busy",
    "swsh11tg-TG21": "facing: Eternatus V near-frontal, flipped on the head right",
    "swsh11tg-TG29": "facing: G-Max Pikachu VMAX gold, unflipped (head in profile left)",
    "swsh11-131": "LADDER facing: Giratina VSTAR head on the right, body trailing left, face near-frontal; flipped (201 / 212 follow)",
    "swsh11tg-TG30": "LADDER facing: Mew VMAX head top right, body / tail curling left; flipped",
}
SKIP_NOTE = {}
FORMS = """giratina-origin 130 131 185 186 201 212 (Origin Forme on every Giratina card), shellos-east 39, gastrodon (West) 102,
basculin-white-striped 44, basculegion (male) 45, enamorus (Incarnate) 82 178 TG18, landorus (Incarnate) 105,
hoopa-unbound 122, perrserker (the species, 129 183 184), stunfisk-galar 127, the Hisuian forms (-hisui: Zorua 75,
Growlithe 83, Zoroark 76 146 147 203 213, Arcanine 84 TG08, Sliggoo 133, Goodra 134 135 136 187 202, Electrode 172),
sneasler 123 and gardevoir 69 / steelix 124 (Radiant: the SHINY sprites), Gigantamax orbeetle-gmax TG13,
centiskorch-gmax TG15, pikachu-gmax TG17 TG29; the Dynamax VMAXes (Kyurem 49 197, Mew TG30) use the plain sprites.
Eternamax Eternatus TG22 is skipped (see above). Pyroar 29 is the female on the card (no vendor sprite): flagged."""


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
    txt = f"""# Lost Origin audit report

Set list: {len(meta)} cards (swsh11: 217, swsh11tg Trainer Gallery: 30). Built: **{built}** Pokemon cards;
skipped: {outc['skipped']} (every Trainer / Energy, and Eternatus VMAX TG22: its Eternamax sprite is 56 rows = 112 grid px,
over the 110 cap, and the plain Eternatus would be the wrong form).
Outcomes: {', '.join(f'{k} {v}' for k, v in sorted(outc.items()))}.

## How the audit ran (ART_METHOD section 16)
- **Machine checks, every card** (`audit/verify_all.py` -> `work/audit/meta.json`): sprite pixel-exact against the
  vendor sprite in normal AND shiny (shape, outline, colours; the gold remap only at Rare Secret, the 0.55 rainbow
  re-tint only at Rare Rainbow; Radiant Rare = the vendor SHINY sprite on both rolls, no shiny overrides), commons
  plain with no background and flipped exactly as `set.json` `flip_commons`, size <= 140 x 110 grid px, card data
  verbatim with tier == API rarity, the 16-frame anims (normal + shiny) with the final frame == the static art on
  every foil card, and the treatment (builder kind) allowed for the printed rarity (Rare Ultra: the four painted alt
  arts 177 / 180 / 184 / 186 = alt, the rest fullart; Trainer Gallery V / VMAX = alt). Result: 0 failures.
- **Visual review, every card**: three reviewers went through real | ours contact sheets (`work/audit/auditA_*`,
  `auditB_*`, `auditC_*`), with zooms and mask overlays, for facing, form, ghosts, text / logo residue and treatment.
- **Clear errors fixed** in `batch_fixes.py` (highest precedence): see "fixed" rows; before / after in
  `work/audit/fixed_*.png` (real | before | after, `audit/fixed_sheet.py`).
- **Taste calls flagged** for the lookbook: see "flagged" rows.
- **Set-wide fill fix:** `s3lib.pushpull` stops its pyramid at 2 x 2, so a top-level cell with no known pixel came
  out black (dark bleeds in the smooth fills of big-Pokemon cards). `lorlib.pushpull_1x1` runs it to 1 x 1 in every
  Lost Origin process (identical wherever every cell had known pixels); the 53 cards it changed were rebuilt.

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
