r"""audit/REPORT.md for Base Set: every card of the set list (base1) as ok / fixed / flagged / skipped,
from work/audit/meta.json (audit_meta.py), the verify_all result and the visual verdicts below (read off the
contact sheets, work/audit/sheets/). Writes artlab/sets/base/audit/REPORT.md and <DATA>/base/audit/REPORT.md.

  ..\..\..\..\.venv\Scripts\python report.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import baselib as P  # noqa: E402
from baselib import E  # noqa: E402

TREATMENT = {
    "Common": "plain sprite, no background, no anim (Charmander 46)",
    "Uncommon": "sprite-scale matte scene, 12 colours (Charmeleon 24)",
    "Rare": "grid-scale matte scene, 16 colours, non-foil (Dragonair 18)",
    "Rare Holo": "WotC starlight holo in the art box, 16-frame wotc anim (Charizard 4)",
}

# visual verdicts: id -> (status, reason). Everything not listed passed the visual check (sprite + form, facing,
# scene, no text / ghost) and is "ok".
VERDICTS = {
    "base1-32": ("fixed", "the Uncommon matte's light rim picked the red of the psychic orbs on the black scene: a red outline ran round the whole sprite; the rim is now a neutral grey (batch_fixes.py, audit/fixed.png)"),
    "base1-59": ("flagged", "Common facing: near-frontal Poliwag, flipped (set.json flip_commons) because the body turns so the tail sweeps out to the left"),
    "base1-43": ("flagged", "Common facing ambiguous: Abra sits frontal, head down; not flipped"),
    "base1-44": ("flagged", "Common facing ambiguous: Bulbasaur lies near-frontal, head down; not flipped"),
    "base1-26": ("flagged", "facing a judgement call: the tail curls out to the left and the head turns right / to the viewer; flipped"),
    "base1-1": ("flagged", "facing ambiguous (near-frontal, head a touch left): not flipped; a very faint trace of the purple halo is left, mostly under the sprite"),
    "base1-3": ("flagged", "facing ambiguous (frontal): not flipped"),
    "base1-7": ("flagged", "facing ambiguous (frontal): not flipped"),
    "base1-8": ("flagged", "facing ambiguous (frontal): not flipped; the rainbow ring behind him is scene, mostly under the sprite"),
    "base1-9": ("flagged", "facing ambiguous (frontal): not flipped"),
    "base1-13": ("flagged", "facing ambiguous (frontal): not flipped"),
    "base1-16": ("flagged", "facing ambiguous (near-frontal, beak down-left): not flipped; the lightning rays are scene"),
    "base1-17": ("flagged", "facing ambiguous (near-frontal, head a little left): not flipped"),
    "base1-19": ("flagged", "facing ambiguous (three near-frontal heads): not flipped; the mound is scene"),
    "base1-20": ("flagged", "facing ambiguous (frontal): not flipped; the glow halo is painted out with him (smooth fill), the lightning bolts turn into soft glow streaks near his hands"),
    "base1-21": ("flagged", "facing ambiguous (frontal ball): not flipped; the default layout makes the sprite larger than the real ball, so the burst's white centre is mostly hidden"),
    "base1-31": ("flagged", "facing ambiguous (near-frontal): not flipped"),
    "base1-33": ("flagged", "facing ambiguous: not flipped; the glowing oval goes with Kakuna (else a halo ghost), so most of the white rays are lost"),
    "base1-34": ("flagged", "facing ambiguous (frontal flex): not flipped"),
    "base1-38": ("flagged", "facing ambiguous (frontal): not flipped"),
    "base1-41": ("flagged", "facing ambiguous (head toward the viewer): not flipped"),
    "base1-42": ("flagged", "facing ambiguous (frontal): not flipped"),
    "base1-25": ("flagged", "a small dark-blue patch of water left in the fill between the tail and the body (scene colour, not the Pokemon)"),
}
INTRO = ("Every built card (69: the 4 ladder cards + 65 from the four group batches) was checked against its real scan "
         "on contact sheets (work/audit/sheets/, real | ours). A card is ok when its treatment is the ladder card of its printed "
         "rarity (FULLSET.md), the sprite is the right Pokemon and faces the way the card does, the scene is the card's own "
         "with all text, logos and the Stage badge painted out and no noticeable ghost, and the data, text half and "
         "animations are right. Frontal Pokemon (Diglett, Gastly, Koffing, Magnemite, Staryu, Starmie, Tangela, Voltorb, "
         "Pikachu 58 ...) have no facing to match and are ok unflipped; the near-frontal ones a reader could argue are flagged.")
SUMMARY = ("Automated checks, all clean: audit/verify_all.py (baseverify on all 69: sprite shape, outline and colours "
           "exact apart from the flip, no recolour at any Base Set rarity; card data verbatim from the API record, tier == API "
           "rarity; size <= 140 x 110 grid px; 16-frame loops whose final frame is the static art; 0 failures) and "
           "audit/audit_meta.py (finish = the rarity's recipe, sprite = plan.json's, commons flipped exactly as set.json "
           "flip_commons, text half with the rarity's frame colour, renders normal + shiny, 16-frame 12 fps anims normal + "
           "shiny on the 16 Rare Holos and none on the 53 non-foil cards, commons plain). The biggest card is 104 x 88 grid px "
           "(Mewtwo 10: 104 cols x 44 lines).\n\n"
           "Coverage: 102 cards in the set list; 69 built (16 Rare Holo, 6 Rare, 20 Uncommon, 27 Common), 33 skipped: the "
           "26 Trainers (70-95) and 7 Energy (96-102), no Pokemon.")


def main():
    meta = json.loads((E.WORK / "audit" / "meta.json").read_text(encoding="utf-8"))
    ladder = set(json.loads((P.HERE / "set.json").read_text(encoding="utf-8"))["ladder"])
    rows, n = [], {"ok": 0, "fixed": 0, "flagged": 0, "skipped": 0}
    for cid, r in meta.items():
        if r["status"] == "skipped":
            st, why = "skipped", r["reason"]
        else:
            auto = "" if r["status"] == "ok" else " AUTOMATED CHECK FAILED: " + ", ".join(k for k, v in r["checks"].items() if not v)
            base = ("approved ladder card; " if cid in ladder else "") + TREATMENT[r["tier"]]
            if r.get("sprite") and r["sprite"] != r["name"].lower():
                base += f", sprite {r['sprite']}"
            if r.get("flip"):
                base += ", flipped to the card's facing"
            st, why = VERDICTS.get(cid, ("ok", "sprite, facing, scene, data OK"))
            why = f"{base}; {why}{auto}"
            if auto and st == "ok":
                st = "flagged"
        n[st] += 1
        rows.append(f"| {cid} | {r['name']} | {r.get('tier') or ''} | {st} | {why} |")
    total = len(meta)
    head = f"# Base Set (base1) audit\n\n{INTRO}\n\nCounts: " + \
           ", ".join(f"{k} {v}" for k, v in n.items()) + f" (set list {total})\n\n{SUMMARY}\n\n" + \
           "| id | name | tier | status | reason |\n|---|---|---|---|---|\n"
    text = head + "\n".join(rows) + "\n"
    for f in (P.HERE / "audit" / "REPORT.md", P.DATA / "audit" / "REPORT.md"):
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text, encoding="utf-8")
        print(f)
    print(n)


if __name__ == "__main__":
    main()
