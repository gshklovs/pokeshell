r"""The per-card metadata audit of Hidden Fates (docs/ART_METHOD.md section 16), from the built files only:
coverage (every Pokemon card of sm115 + sma built or skipped with a reason), treatment = the finish of the card's
printed rarity, sprite = plan.json's (forms), the Shiny Vault rule (both rolls the shiny sprite), text half present
with the rarity's frame colour, anims (16 frames, 12 fps, normal + shiny) for foil tiers and none for non-foil,
size <= 140 x 110 grid px. -> <DATA>/hf/work/audit/meta.json

  ..\..\..\..\.venv\Scripts\python audit_meta.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import hflib as P  # noqa: E402
from hflib import E, L  # noqa: E402
import hfcards as C  # noqa: E402

FINISH = {"Common": "plain sprite", "Uncommon": "non-foil: sprite-scale", "Rare": "non-foil: grid-scale",
          "Rare Holo": "SM rare holo", "Rare Holo GX": "SM GX holo", "Rare Shiny": "Shiny Vault:",
          "Rare Shiny GX": "Shiny Vault GX:", "Rare Secret": "gold secret"}
FOIL = {"Rare Holo", "Rare Holo GX", "Rare Shiny", "Rare Shiny GX", "Rare Secret"}
MAX_W, MAX_H = 140, 110


def anim_ok(cid, sfx):
    f = P.DATA / "anim" / f"{cid}{sfx}" / f"{cid}{sfx}.anim"
    if not f.exists():
        return False, "missing"
    hdr = json.loads(f.read_text(encoding="utf-8").split("\f")[0])
    return int(hdr.get("frames", 0)) == 16 and int(hdr.get("fps", 0)) == 12, f"{hdr.get('frames')} frames {hdr.get('fps')} fps"


def main():
    plan = json.loads((P.HERE / "plan.json").read_text(encoding="utf-8"))
    meta = json.loads((P.HERE / "set.json").read_text(encoding="utf-8"))
    sprite = {e["id"]: e["sprite"] for g, v in plan.items() if not g.startswith("_") for e in v}
    ladder = {cid: fn() for cid, fn in C.BUILDERS.items() if cid in meta["ladder"]}
    for cid, c in ladder.items():
        sprite[cid] = c.spr.name
    skipped = {s["id"]: s["reason"] for s in plan["_skipped"]}
    setlist = json.loads((P.DATA / "setlist.json").read_text(encoding="utf-8"))
    out, problems = {}, []
    for rec in setlist:
        cid = rec["id"]
        if cid in skipped:
            out[cid] = {"status": "skipped", "reason": skipped[cid], "name": rec["name"], "tier": rec.get("rarity")}
            continue
        card = P.card_json(cid)
        tier = card["tier"]
        r = {"name": card["name"], "tier": tier, "sprite": sprite.get(cid), "checks": {}}
        ck = r["checks"]
        af = E.ART / f"{cid}.json"
        if not af.exists():
            r["status"] = "missing"
            problems.append(f"{cid}: not built")
            out[cid] = r
            continue
        art = json.loads(af.read_text(encoding="utf-8"))
        (vn, v), = art["variants"].items()
        rows = v["rows"]
        ck["tier"] = v["rarity"] == tier == rec["rarity"]
        ck["finish"] = v["finish"].startswith(FINISH[tier]) or (tier == "Rare Shiny" and v["finish"].startswith("Shiny Vault:"))
        if tier == "Rare Shiny":
            ck["finish"] = v["finish"].startswith("Shiny Vault: ")
        ck["sprite"] = art["pokemon"] == sprite.get(cid)
        ck["size"] = len(rows[0]) <= MAX_W and len(rows) <= MAX_H
        r["size"] = f"{len(rows[0])}x{len(rows)}"
        r["flip"] = v.get("flip")
        vault = P.is_vault(cid)
        if vault:                       # the shiny roll shows the same shiny sprite: no shiny overrides at all
            ck["vault_shiny"] = not art.get("shiny") and not v.get("shiny")
        frame = C.FRAMES[tier]
        cans = (E.OUT / f"{cid}-card.ans")
        if cans.exists():
            if frame == "rainbow":
                ck["text_half"] = True
            else:
                rr, gg, bb = L.hexrgb(frame)
                ck["text_half"] = f"38;2;{rr};{gg};{bb}" in cans.read_text(encoding="utf-8")
        else:
            ck["text_half"] = False
        ck["renders"] = all((E.OUT / f"{cid}-{k}{s}.png").exists() for k in ("art", "card") for s in ("", "-shiny"))
        if tier in FOIL:
            a0, n0 = anim_ok(cid, "")
            a1, n1 = anim_ok(cid, "_shiny")
            ck["anim"] = a0 and a1
            r["anim"] = f"{n0} / {n1}"
        else:
            ck["anim"] = not (P.DATA / "anim" / cid).exists()
            if tier == "Common":
                ck["plain"] = all(ch == "." or ch in art["palette"] for rw in rows for ch in rw) and not v.get("palette")
        bad = [k for k, ok in ck.items() if not ok]
        r["status"] = "ok" if not bad else "problem"
        if bad:
            problems.append(f"{cid} {card['name']} [{tier}]: {', '.join(bad)}")
        out[cid] = r
    f = E.WORK / "audit" / "meta.json"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    n = {s: sum(1 for r in out.values() if r["status"] == s) for s in ("ok", "problem", "missing", "skipped")}
    print(f"{len(out)} cards in the set list: {n}")
    for p in problems:
        print("  ", p)
    return out, problems


if __name__ == "__main__":
    main()
