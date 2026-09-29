r"""audit/REPORT.md for Hidden Fates: every card of the set list (sm115 + sma) as ok / fixed / flagged / skipped,
from work/audit/meta.json (audit_meta.py), the verify_all result and the visual verdicts below (read off the
contact sheets, work/audit/sheets/). Writes artlab/sets/hf/audit/REPORT.md and <DATA>/hf/audit/REPORT.md.

  ..\..\..\..\.venv\Scripts\python report.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import hflib as P  # noqa: E402
from hflib import E  # noqa: E402

TREATMENT = {
    "Common": "plain sprite, no background, no anim (Charmander 7)",
    "Uncommon": "sprite-scale matte scene, 12 colours (Charmeleon 8)",
    "Rare": "grid-scale matte scene, 16 colours, non-foil (Mew 32)",
    "Rare Holo": "holo bands + starlight in the art box, 16-frame holo anim (Vaporeon 18)",
    "Rare Holo GX": "silver frame + GX web foil, 16-frame gxweb anim (Charizard-GX 9)",
    "Rare Shiny": "SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6)",
    "Rare Shiny GX": "SHINY sprite, etched vault foil + flares + silver frame, 16-frame vaultgx anim (Charizard-GX SV49)",
    "Rare Secret": "gold remap + faceted gold, 16-frame gold anim (Tapu Koko-GX SV93)",
}

# visual verdicts: id -> (status, reason). Everything not listed passed the visual check (sprite + form, facing,
# scene, no text / ghost) and is "ok".
VERDICTS = {
    "sm115-8": ("fixed", "the stage icon ran past ICON and left a tan ghost top-left: paint-out boxes grown (batch_fixes.py, audit/fixed.png)"),
    "sm115-18": ("fixed", "the Evolves-from bar's lower edge left a dark strip along the top: paint-out box grown (batch_fixes.py, audit/fixed.png)"),
    "sm115-1": ("flagged", "Common facing: the card's Caterpie faces left, the plain sprite right. Listed in set.json flip_commons; the importer builds it unflipped until the per-set flip_commons change (Crown Zenith branch) lands"),
    "sm115-12": ("flagged", "Common facing: the card's Slowpoke faces right, the plain sprite left. Listed in set.json flip_commons (as sm115-1)"),
    "sm115-26": ("flagged", "Common facing ambiguous: head turned up and back, mouth open; not flipped"),
    "sm115-17": ("flagged", "facing arguable: flipped because the body swims right, but the head bends down toward the ball"),
    "sm115-42": ("flagged", "near-frontal; flipped because the head is turned slightly right"),
    "sm115-47": ("flagged", "Kangaskhan covers most of the window: the fill is a soft orange blur of the explosion (the weakest scene of the set)"),
    "sm115-36": ("flagged", "faint warm-orange streaks in the fill from the scan's red stadium seats (scene, not a ghost of Onix)"),
    "sma-SV2": ("flagged", "every segmenter took the window: hand hull; a broken printed-star fragment near the top"),
    "sma-SV5": ("flagged", "hand hull; Pheromosa is huge and faint, about 60% of the window is fill; the sprite is frontal, the card faces left"),
    "sma-SV19": ("flagged", "flipped so the tail curls left as on the card; the body is near-frontal"),
    "sma-SV24": ("flagged", "printed stars half-hidden behind the real Buzzwole come out as scribbly silver fragments"),
    "sma-SV26": ("flagged", "printed stars half-hidden behind the real Guzzlord come out as scribbly silver fragments"),
    "sma-SV34": ("flagged", "facing ambiguous: the card's Ralts looks right, the near-frontal sprite is not flipped"),
    "sma-SV36": ("flagged", "facing ambiguous: the card's Diancie faces left, the near-frontal sprite is not flipped"),
    "sma-SV53": ("flagged", "facing ambiguous: head on the left but the snout points right; flipped"),
    "sma-SV56": ("flagged", "facing ambiguous: near-frontal Greninja, looks left; not flipped"),
    "sma-SV57": ("flagged", "a front-facing ball; flipped because the face sits right of centre on the card"),
    "sma-SV65": ("flagged", "a few faint specks left from the thin cyan cape outline lines"),
    "sma-SV77": ("flagged", "flipped on the head's position (right of the cloud body); the face itself is frontal"),
    "sma-SV78": ("flagged", "three-quarter pose, head turned right: flipped"),
}
INTRO = ("Every built card (133: the 8 ladder cards + 125 from the ten group batches) was checked against its real scan "
         "on contact sheets (work/audit/sheets/, real | ours). A card is ok when its treatment is the ladder card's of its "
         "printed rarity (FULLSET.md), the sprite is the right Pokemon and form (SHINY sprite on every Shiny Vault card) and "
         "faces the way the card does, the scene is the card's own with all text and logos painted out and no noticeable "
         "ghost, and the data, text half and animations are right. Near-frontal Pokemon (Voltorb, Staryu, Starmie, "
         "Electrode 22, the Tapus, Nihilego, Xurkitree ...) have no facing to match and are ok unflipped.")
SUMMARY = ("Automated checks, all clean: audit/verify_all.py (hfverify on all 133: sprite shape, outline and colours exact "
           "apart from the flip; the SHINY vendor colours on both rolls of every Rare Shiny / Rare Shiny GX card; the only "
           "recolour is the gold remap on the 4 Rare Secret Tapus; card data verbatim from the API record, tier == API "
           "rarity; size <= 140 x 110; 0 failures, 877 checks) and audit/audit_meta.py (finish = the rarity's recipe, "
           "sprite = plan.json's, text half with the rarity's frame colour, renders normal + shiny, 16-frame 12 fps anims "
           "normal + shiny on the 95 foil cards (Rare Holo, Rare Holo GX, Rare Shiny, Rare Shiny GX, Rare Secret) and none on the 38 non-foil ones, commons plain). Forms: vulpix-alola, "
           "ninetales-alola, lycanroc-midnight (SV66), lycanroc-dusk (SV67), zygarde-complete (SV65, read off the scan).\n\n"
           "Coverage: 163 cards in the set list (sm115 69 + sma 94); 133 built, 30 skipped: 27 Trainers and the three "
           "Moltres & Zapdos & Articuno-GX TAG TEAM cards (44, 66, 69: three Pokemon, no single colorscripts sprite; three "
           "~45x40 sprites cannot fit the 70x55 sprite-px cap without covering each other).")


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
    head = f"# Hidden Fates (sm115) + Shiny Vault (sma) audit\n\n{INTRO}\n\nCounts: " + \
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
