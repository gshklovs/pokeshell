import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import artpaths  # noqa: E402
H = artpaths.data("evs")
m = json.load(open(H / "work/audit/meta.json", encoding="utf-8"))
ALT = {"swsh7-167","swsh7-175","swsh7-180","swsh7-184","swsh7-182","swsh7-186","swsh7-189","swsh7-192","swsh7-194","swsh7-196","swsh7-198"}
FIXED = {"swsh7-210": "was facing left; the card's Dracozolt faces right (head top-right, as on VMAX 59). Re-rendered flipped with Leafeon 204's rainbow recipe (batch_fixes.py), verified, re-imported."}
FLAG = {
 "swsh7-49": "ladder built it as a Reverse Holo (foil ring + anim), but the live pack imports it as its printed rarity, Common (plain sprite, no .anim). Pack is consistent with the real card; decide which you want.",
 "swsh7-95": "card's Umbreon looks right (head three-quarter to the right); ours faces left. Same pose as Umbreon 215 (approved unflipped), so left as is.",
 "swsh7-214": "same pose as 95/215: card looks right, ours faces left. Left as is for consistency with the approved 215.",
 "swsh7-94": "card Umbreon lunges near-frontal, slightly right; ours faces left. Ambiguous.",
 "swsh7-171": "card Gyarados' head turns right (mouth lower right); ours faces left. Three-quarter pose, arguable.",
 "swsh7-85": "card Hippowdon's head is on the left; the sprite's facing is hard to read at this size. Check whether it should be flipped.",
 "swsh7-120": "card Flapple's head sits right of the apple; the sprite's head is left. The pose is ambiguous.",
 "swsh7-80": "a dark smudge right of the sprite: the card's own black shadow wisps, part of Marshadow's move. Could read as a ghost of the Pokémon.",
 "swsh7-197": "card Duraludon is near-frontal, head top-right; ours unflipped. Ambiguous.",
}
L = {"Common": "plain sprite, no background, no anim", "Uncommon": "matte sprite-scale scene, no anim",
     "Rare": "matte grid-scale scene, no anim", "Rare Holo": "holo foil in the scene, 16-frame anim",
     "Rare Holo V": "silver frame + sunpillar, anim", "Rare Holo VMAX": "gunmetal frame + sunpillar, anim",
     "Rare Ultra": "plain full art, fingerprint etch, anim", "Rare Secret": "gold remap + gold scene, anim",
     "Reverse Holo": "ladder example"}
def why(cid, r):
    t = r["tier"]; f = r.get("finish", "")
    if t == "Rare Rainbow":
        s = "painted alt-art secret, Umbreon 215 recipe" if "alternate" in f else "true rainbow, Leafeon 204 recipe, sprite blend 0.55"
    else:
        s = L[t]
    extra = []
    p = r.get("pokemon") or r["pack"]["character"]
    if any(k in p for k in ("-galar", "-gmax", "-dusk")): extra.append(f"sprite {p}")
    return s + (" (" + ", ".join(extra) + ")" if extra else "") + "; sprite, facing, scene, data and pack OK"
rows, cnt = [], {"ok": 0, "fixed": 0, "flagged": 0, "out of scope": 0}
for cid, r in m.items():
    if cid in FIXED: st, rs = "fixed", FIXED[cid]
    elif cid in ALT: st, rs = "out of scope", "painted alt-art Rare Ultra, being redone with the Umbreon 215 treatment in batch_altart.py by the other agent (it currently has the full-art etch; art/ is newer than the live pack)"
    elif cid in FLAG: st, rs = "flagged", FLAG[cid]
    else: st, rs = "ok", why(cid, r)
    cnt[st] += 1
    rows.append(f"| {cid} | {r['name']} | {r['tier']} | {st} | {rs} |")
out = ["# Evolving Skies audit", "",
 f"All {len(m)} Pokémon cards were checked against their real scans on contact sheets (work/audit/sheets/). A card is ok when its treatment matches its real finish, the sprite is the right Pokémon and form, the scene is the card's own, and the data, text half and animations are right. The live pack was checked too: tier, dist .ans/.anim and art rows.", "",
 "Counts: " + ", ".join(f"{k} {v}" for k, v in cnt.items()), "",
 "Checks that passed for every card: every batch verify run was clean (sprite shape, outline and colours exact apart from the allowed flip, rainbow or gold; card data verbatim; 16 frames with the last equal to the static art). Commons have no background and no anim. Non-foil cards have no anim. Foil cards have both .anim files in dist/. Every card is in pack.json at its printed-rarity tier (Pikachu 49 is the one to look at). Gigantamax sprites appear only on cards that say Gigantamax (101, 123, 216, 219, 220). The Galarian birds use -galar sprites, and every Lycanroc uses lycanroc-dusk.", "",
 "Alt-art check: the 11 painted Rare Ultras (167, 175, 180, 182, 184, 186, 189, 192, 194, 196, 198) are the complete list. Every other Rare Ultra is a plain full art. The five painted Rare Rainbows (205, 209, 212, 218, 220) already use the Umbreon 215 recipe. The other 10 Rare Rainbows are true rainbows.", "",
 "| id | name | tier | status | reason |", "|---|---|---|---|---|"] + rows
(H / "audit/REPORT.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print(cnt)
