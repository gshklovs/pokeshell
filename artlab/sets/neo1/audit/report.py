r"""audit/REPORT.md for Neo Genesis: every card of the set list (neo1) as ok / fixed / flagged / skipped,
from work/audit/meta.json (audit_meta.py), the verify_all result and the visual verdicts below (read off the
contact sheets, work/audit/sheets/). Writes artlab/sets/neo1/audit/REPORT.md and <DATA>/neo1/audit/REPORT.md.

  ..\..\..\..\.venv\Scripts\python report.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import neolib as P  # noqa: E402
from neolib import E  # noqa: E402

TREATMENT = {
    "Common": "plain sprite, no background, no anim (Totodile 81)",
    "Uncommon": "sprite-scale matte scene, 12 colours (Quilava 46)",
    "Rare": "grid-scale matte scene, 16 colours, non-foil (Murkrow 24)",
    "Rare Holo": "WotC starlight holo in the art box, 16-frame wotc anim (Lugia 9)",
}

AMB = "facing ambiguous ({}): not flipped"
# visual verdicts: id -> (status, reason). Everything not listed passed the visual check (sprite + form, facing,
# scene, no text / ghost) and is "ok".
VERDICTS = {
    # Rare Holo
    "neo1-2": ("flagged", AMB.format("frontal")),
    "neo1-3": ("flagged", AMB.format("two frontal Bellossom") + "; the second Bellossom (top right) is painted out too, one sprite on the big one"),
    "neo1-5": ("flagged", "a faint pale streak of the white halo is left near the tail tip, barely visible at grid scale"),
    "neo1-7": ("flagged", AMB.format("floating, face to the viewer")),
    "neo1-11": ("flagged", AMB.format("frontal, looking up")),
    "neo1-12": ("flagged", AMB.format("frontal")),
    "neo1-14": ("flagged", AMB.format("frontal") + "; the fill mirrors the dark rock a little blockily at the right edge"),
    "neo1-16": ("flagged", "the glow-orb background leaves a slightly lighter, seam-edged patch where Togetic was (the smooth fill was worse)"),
    # Rare
    "neo1-20": ("flagged", "facing a judgement call: the head turns three-quarter to the right and the body leans right into the yarn; flipped (the brief's first read was ambiguous / unflipped)"),
    "neo1-21": ("ok", "the sky fill is a per-row blend of the visible strip (batch_rare rowfill), so it reads sky / horizon / hills like the card"),
    "neo1-22": ("flagged", AMB.format("frontal, leaning") + "; the lightning bolts and clouds are scene"),
    "neo1-23": ("flagged", AMB.format("frontal, beak a touch left")),
    # Uncommon
    "neo1-26": ("flagged", AMB.format("hangs upside down, face to the viewer")),
    "neo1-27": ("ok", "the second Ariados behind and the blurred one in the foreground are painted out too; most of the fill is the dark deck"),
    "neo1-29": ("flagged", "a faint pale-green patch near the front foot (probably the ground's own colour)"),
    "neo1-30": ("flagged", AMB.format("frontal, on a swing") + "; the swing is scene"),
    "neo1-31": ("flagged", AMB.format("frontal body, snout up-left")),
    "neo1-33": ("flagged", AMB.format("frontal") + "; he fills most of the window, so the fill is a smooth blend, mostly under the sprite"),
    "neo1-35": ("flagged", AMB.format("head turned slightly left, tail curls out at the left") + "; the tiny Furret far off at the right stays as scene"),
    "neo1-36": ("flagged", AMB.format("lying on its back, face to the viewer")),
    "neo1-37": ("flagged", AMB.format("frontal") + "; a large smooth fill, mostly under the sprite"),
    "neo1-38": ("flagged", "the left lure's faint teal haze partly stays, blending into the dark sea"),
    "neo1-39": ("flagged", AMB.format("frontal") + "; the two smaller Ledian behind are painted out too; the matte's light rim is olive on the dark sky"),
    "neo1-41": ("flagged", AMB.format("body turned left, head three-quarter to the right") + "; the herd far off at the right stays as scene; a slightly flat green patch where the tail shadow was"),
    "neo1-42": ("flagged", AMB.format("frontal") + "; the tiny Hoothoot in the trees stay as scene"),
    "neo1-49": ("flagged", AMB.format("near-frontal, face a little right")),
    "neo1-50": ("flagged", AMB.format("frontal")),
    "neo1-51": ("flagged", AMB.format("frontal, in a tree hollow")),
    # Common
    "neo1-53": ("flagged", "Common facing ambiguous: Chikorita stands frontal; not flipped"),
    "neo1-54": ("flagged", "Common facing ambiguous: Chikorita frontal; not flipped"),
    "neo1-61": ("flagged", "Common facing ambiguous: Hoppip frontal, face a little right; not flipped"),
    "neo1-63": ("flagged", "Common facing ambiguous: Ledyba flies toward the viewer; not flipped"),
    "neo1-68": ("flagged", "Common facing ambiguous: Oddish lies on its back; not flipped"),
}
INTRO = ("Every built card (81: the 4 ladder cards + 77 from the five group batches) was checked against its real scan "
         "on contact sheets (work/audit/sheets/, real | ours). A card is ok when its treatment is the ladder card of its printed "
         "rarity (FULLSET.md), the sprite is the right Pokemon and faces the way the card does, the scene is the card's own "
         "with all text, logos and the Stage badge painted out and no noticeable ghost, and the data, text half and "
         "animations are right. Frontal Pokemon (Chinchou, Hoothoot, Sentret, Snubbull, Spinarak, Sudowoodo, Sunkern, "
         "Wooper, Noctowl ...) have no facing to match and are ok unflipped; the near-frontal ones a reader could argue are "
         "flagged. No clear error was found, so batch_fixes.py has no fixes; every flag is a taste call for the lookbook.")
SUMMARY = ("Automated checks, all clean: audit/verify_all.py (neoverify on all 81: sprite shape, outline and colours "
           "exact apart from the flip, no recolour at any Neo Genesis rarity; card data verbatim from the API record, tier == "
           "API rarity; size <= 140 x 110 grid px; 16-frame loops whose final frame is the static art; 0 failures) and "
           "audit/audit_meta.py (finish = the rarity's recipe, sprite = plan.json's, commons flipped exactly as set.json "
           "flip_commons, text half with the rarity's frame colour, renders normal + shiny, 16-frame 12 fps anims normal + "
           "shiny on the 18 Rare Holos and none on the 63 non-foil cards, commons plain).\n\n"
           "Coverage: 111 cards in the set list; 81 built (18 Rare Holo, 6 Rare, 27 Uncommon, 30 Common), 30 skipped, none "
           "of them a Pokemon: 21 Trainers (83-103), 3 special Energy (Metal 19, a Rare Holo; Darkness 104; Recycle 105) and "
           "6 basic Energy (106-111, which have no API rarity).")


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
    head = f"# Neo Genesis (neo1) audit\n\n{INTRO}\n\nCounts: " + \
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
