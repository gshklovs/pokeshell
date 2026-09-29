"""audit/REPORT.md from work/audit/meta.json + the visual pass (contact sheets in work/audit/sheets/)"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import artpaths  # noqa: E402
H = artpaths.data("p30")
m = json.load(open(H / "work/audit/meta.json", encoding="utf-8"))
FIXED = {
 "me55-66": "faced right; the card's Mew faces left (head and eye lower left, tail up behind to the right). Re-rendered flipped with Umbreon 92's ex recipe (batch_fixes.py), verified, imported.",
 "me55-26": "mask missed the lower tail zigzag and the right paw, left as a tan ghost at the art's right. Both added to the mask, re-rendered with Pikachu 23's recipe (batch_fixes.py), verified, imported.",
 "me55-129": "art was 57 lines (114 px), over the pack's 110 px art cap, so the import refused it. Same crop two sprite rows shorter (55 lines, sprite whole), Lapras 131's recipe (batch_fixes.py), verified, imported.",
}
FLAG = {
 "me55-5": "Common: the card's Tropius faces right (head top right); the plain sprite faces left. Commons are never flipped (Vulpix rule), so left as is.",
 "me55-93": "Common: the card's Murkrow faces right; the sprite faces left. Left unflipped (commons rule).",
 "me55-114": "Common: the card's Kangaskhan faces right (head up right); the sprite faces left. Left unflipped (commons rule).",
 "me55-44": "the card's own after-image Pikachus stay in the fill as yellow blobs around the sprite. They are part of the scene, but they can read as ghosts. Taste call.",
 "me55-140": "the big Scraggy face fills the card, so the fill is smooth (texture=False) and the scene is a soft colour smear with the small cameo Scraggys as orange blobs. Weakest scene in the set.",
 "me55-158": "Futuristic tint falls back to the card's darkest tone (little red on the card). At blend 0.3 it barely reads: the sprite looks plain pink next to Mewtwo 157. Taste call on whether it should read more.",
 "me55-152": "the card's Mew is curled, facing ambiguous; ours is unflipped (faces right). Check.",
}
TREAT = {"Common": "plain sprite, no background, no anim",
         "Rare": "ME rare holo (Mew 65 recipe), 16-frame holo anim",
         "Pikachu Rare": "fireworks lattice + yellow bevel (Pikachu 23), 16-frame fireworks anim",
         "Double Rare": "silver frame + sparkle grain (Umbreon 92), 16-frame ex anim",
         "Illustration Rare": "subtle etch, vivid painting (Lapras 131), 16-frame etch anim",
         "Special Illustration Rare": "textured painting + pearl lustre (Gengar 154), 16-frame sir anim",
         "Futuristic Rare": "chrome + red-black sprite tint <=0.3 (Mewtwo 157), 16-frame chrome anim"}
LADDER = {"me55-9", "me55-65", "me55-23", "me55-92", "me55-131", "me55-154", "me55-157"}
FORMS = ("-alola", "-galar", "-hisui", "-midnight", "-crowned", "-sunshine", "-poke-ball", "-low-key", "-red")
rows, cnt = [], {"ok": 0, "fixed": 0, "flagged": 0, "skipped": 0}
for cid, r in m.items():
    if r.get("status") == "skipped":
        st, rs = "skipped", r["reason"]
    elif cid in FIXED:
        st, rs = "fixed", FIXED[cid]
    elif cid in FLAG:
        st, rs = "flagged", FLAG[cid]
    else:
        st = "ok"
        p = r["pokemon"]
        extra = f", sprite {p}" if any(p.endswith(f) for f in FORMS) or p == "toxtricity" else ""
        rs = ("approved ladder card; " if cid in LADDER else "") + TREAT[r["tier"]] + extra + "; sprite, facing, scene, data OK"
    cnt[st] += 1
    rows.append(f"| {cid} | {r['name']} | {r.get('tier') or r['api_rarity']} | {st} | {rs} |")
out = ["# 30th Celebration (me55) audit", "",
 "Every built card (149: the 7 ladder cards + 142 from the six batches) was checked against its real scan on contact sheets (work/audit/sheets/, real | ours). A card is ok when its treatment matches the approved example of its rarity (FULLSET.md), the sprite is the right Pokémon and form and faces the way the card does, the scene is the card's own with the 30th stamp and all text painted out and no noticeable ghost, and the data, text half and animations are right.", "",
 "Counts: " + ", ".join(f"{k} {v}" for k, v in cnt.items()) + f" (setlist {len(m)} = 149 built + 12 skipped)", "",
 "Automated checks, all clean (work/audit/audit_meta.py, work/audit/verify_all.py): p30verify on all 149 (sprite shape, outline and colours exact apart from the allowed flip; the only recolour is the Futuristic tint on 157/158 at blend 0.3; card data verbatim from the API record; tier == API rarity); every art file's finish is its rarity's recipe and its text half carries the rarity's frame colour; 84 foil cards have 16-frame anims (normal + shiny) whose last frame equals the static art; the 65 commons have no background and no anim. Forms: Alolan / Galarian / Hisuian sprites on those cards, lycanroc-midnight (85, 138), zacian-crowned / zamazenta-crowned, cherrim-sunshine, vivillon-poke-ball, toxtricity-low-key on 59 and amped on 60 / 134 (read off the crests), minior-red.", "",
 "Coverage: setlist.json has 161 cards; all 149 buildable ones are built. Skipped: 9 Gen 9 cards with no colorscripts sprite (Fuecoco ex 15 / 147, Miraidon 62, Gimmighoul 81, Koraidon 86, Gholdengo 108 / 142, Maushold 125 / 146) and 3 Trainers (Poké Pad 126, Switch 127, Ultra Ball 128).", "",
 "Fixes are in batch_fixes.py (owning batch module loaded by path, one per-card setting overridden); before copies in work/audit/before/, real | before | after in audit/fixed.png.", "",
 "| id | name | tier | status | reason |", "|---|---|---|---|---|"] + rows
(H / "audit/REPORT.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print(cnt)
