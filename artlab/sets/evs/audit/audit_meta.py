"""metadata half of the EVS audit: per card, what we built and what the live pack holds -> work/audit/meta.json"""
import json
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]         # artlab/sets/evs: the set's code
sys.path.insert(0, str(CODE.parents[1]))
import artpaths  # noqa: E402
HERE = artpaths.data("evs")                       # style-lab/evs: the set's data
ROOT = artpaths.ROOT                                 # repo
sys.path.insert(0, str(CODE))
import evlib as E  # noqa: E402
from evlib import L  # noqa: E402

plan = json.load(open(CODE / "plan.json", encoding="utf-8"))
group = {c["id"]: g for g, v in plan.items() for c in v}
LADDER = ["swsh7-125", "swsh7-108", "swsh7-106", "swsh7-49", "swsh7-109", "swsh7-74", "swsh7-30", "swsh7-174",
          "swsh7-204", "swsh7-215", "swsh7-226"]
for c in LADDER:
    group[c] = "ladder"
pack = json.load(open(ROOT / "packs/pokemon/pack.json", encoding="utf-8"))
FOIL = {"Rare Holo", "Rare Holo V", "Rare Holo VMAX", "Rare Ultra", "Rare Rainbow", "Rare Secret", "Reverse Holo"}
DIST = ROOT / "dist/pokemon"
ids = sorted((p.stem for p in (HERE / "cards").glob("swsh7-*.json")), key=lambda s: int(s.split("-")[1]))
out = {}
for cid in ids:
    card = json.load(open(HERE / "cards" / f"{cid}.json", encoding="utf-8"))
    api = json.load(open(HERE / "cards/api" / f"{cid}.json", encoding="utf-8"))
    r = {"name": card["name"], "api_rarity": api["rarity"], "tier": card["tier"], "group": group.get(cid), "issues": []}
    foil = card["tier"] in FOIL
    r["foil"] = foil
    af = HERE / "art" / f"{cid}.json"
    if af.exists():
        art = json.load(open(af, encoding="utf-8"))
        (vn, v), = art["variants"].items()
        r.update(pokemon=art["pokemon"], variant=vn, finish=v["finish"], label=v["label"], flip=v["flip"],
                 size=[len(v["rows"][0]), len(v["rows"])], art_rarity=v["rarity"])
        if v["rarity"] != card["tier"]:
            r["issues"].append(f"art rarity {v['rarity']} != tier {card['tier']}")
        # static rgb, normal + shiny
        stat = {}
        for sh in (False, True):
            p = {**art["palette"], **v.get("palette", {})}
            if sh:
                p = {**p, **art["shiny"], **v.get("shiny", {})}
            stat[sh] = [[None if ch == "." else L.hexrgb(p[ch]) for ch in row] for row in v["rows"]]
        for sh in (False, True):
            nm = cid + ("_shiny" if sh else "")
            f = HERE / "anim" / nm / f"{nm}.json"
            if foil:
                if not f.exists():
                    r["issues"].append(f"anim missing {nm}")
                    continue
                m = json.load(open(f, encoding="utf-8"))
                last = m["frames"][m["final_frame"]]
                got = [[None if ch == "." else L.hexrgb(m["palette"][ch]) for ch in row] for row in last]
                if len(m["frames"]) != 16:
                    r["issues"].append(f"{nm}: {len(m['frames'])} frames")
                if m["final_frame"] != 15:
                    r["issues"].append(f"{nm}: final_frame {m['final_frame']}")
                if got != stat[sh]:
                    r["issues"].append(f"{nm}: final frame != static art")
            elif f.exists() or (HERE / "anim" / nm).exists():
                r["issues"].append(f"non-foil has anim {nm}")
        for k in ("art", "card"):
            for sfx in ("", "-shiny"):
                if not (HERE / "out" / f"{cid}-{k}{sfx}.png").exists():
                    r["issues"].append(f"out {k}{sfx} missing")
    else:
        r["pokemon"] = None
        if card["tier"] != "Common":
            r["issues"].append("no art json")
        if (HERE / "anim" / cid).exists():
            r["issues"].append("common has anim")
    # text half: card data present with attacks/abilities
    if not (card.get("attacks") or card.get("abilities")):
        r["issues"].append("card data has no attacks/abilities")
    # live pack
    pc = pack["cards"].get(cid)
    if not pc:
        r["issues"].append("NOT IN PACK")
    else:
        tier_ok = next((t["id"] for t in pack["tiers"] if t.get("rarity") == api["rarity"]), None)
        if cid == "swsh7-49":
            tier_ok = "reverse-holo"
        r["pack"] = pc
        if pc["tier"] != tier_ok:
            r["issues"].append(f"pack tier {pc['tier']} expected {tier_ok}")
        ch = pc["character"]
        if r.get("pokemon") and ch != r["pokemon"]:
            r["issues"].append(f"pack character {ch} != art pokemon {r['pokemon']}")
        for sfx in ("", "-shiny"):
            if not (DIST / f"{ch}-{cid}{sfx}.ans").exists():
                r["issues"].append(f"dist ans{sfx} missing")
            has = (DIST / f"{ch}-{cid}{sfx}.anim").exists()
            if foil and not has:
                r["issues"].append(f"dist anim{sfx} missing")
            if not foil and has:
                r["issues"].append(f"dist anim{sfx} on non-foil")
        if not (ROOT / "packs/pokemon/cards" / f"{cid}.json").exists():
            r["issues"].append("pack text half missing")
        if not (ROOT / "packs/pokemon/art" / f"{cid}.json").exists():
            r["issues"].append("pack art missing")
        else:
            pa = json.load(open(ROOT / "packs/pokemon/art" / f"{cid}.json", encoding="utf-8"))
            if af.exists():
                (pv,) = pa["variants"].values()
                if pv["rows"] != v["rows"]:
                    r["issues"].append("pack art rows differ from batch art (stale import?)")
    out[cid] = r
(HERE / "work/audit/meta.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
extra = [k for k in pack["cards"] if k.startswith("swsh7-") and k not in out]
print("cards", len(out), "pack swsh7 extra", extra)
for cid, r in out.items():
    if r["issues"]:
        print(cid, r["name"], r["tier"], r["issues"])
