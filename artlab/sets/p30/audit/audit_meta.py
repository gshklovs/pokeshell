"""metadata half of the 30th Celebration audit: per card, what we built (art / out / anim / data) against the
brief (FULLSET.md) -> work/audit/meta.json; prints every issue found. Read-only on the build outputs."""
import json
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]         # artlab/sets/p30: the set's code
sys.path.insert(0, str(CODE.parents[1]))
import artpaths  # noqa: E402
HERE = artpaths.data("p30")                       # style-lab/p30: the set's data
ROOT = artpaths.ROOT                                 # repo
sys.path.insert(0, str(CODE))
import p30lib as P  # noqa: E402
from p30lib import L  # noqa: E402

plan = json.load(open(CODE / "plan.json", encoding="utf-8"))
group, sprite = {}, {}
for g, v in plan.items():
    if g.startswith("_"):
        continue
    for c in v:
        group[c["id"]], sprite[c["id"]] = g, c["sprite"]
LADDER = {"me55-9": "vulpix", "me55-65": "mew", "me55-23": "pikachu", "me55-92": "umbreon", "me55-131": "lapras",
          "me55-154": "gengar", "me55-157": "mewtwo"}
for c, s in LADDER.items():
    group[c], sprite[c] = "ladder", s
skipped = {e["id"]: e["reason"] for e in plan["_skipped"]}
setlist = json.load(open(HERE / "setlist.json", encoding="utf-8"))

# the approved example's treatment per rarity: finish prefix, anim kind, frame colour
RECIPE = {"Common": ("plain sprite, no background", None, "#9aa0aa"),
          "Rare": ("ME rare holo", "holo", "#6ea5ff"),
          "Pikachu Rare": ("Pikachu Rare: fireworks-burst holo", "fireworks", "#f6d02c"),
          "Double Rare": ("ex holo: silver frame, fine sparkle-grain", "ex", "#c9d1da"),
          "Illustration Rare": ("illustration rare: full painting, light etched", "etch", "#7fd6e6"),
          "Special Illustration Rare": ("SIR: textured painting", "sir", "#f0c850"),
          "Futuristic Rare": ("futuristic rare: liquid chrome", "chrome", "#c07cff")}
VENDOR = artpaths.VENDOR / "pokemon-colorscripts/colorscripts/large"
sizes = {}
for f in list((HERE / "sheets").glob("*-sizes.json")) + [HERE / "work/dr_sizes.json", HERE / "work/sizes-pikachu_rare.json",
                                                         HERE / "sizes.json"]:
    if f.exists():
        sizes.update(json.load(open(f, encoding="utf-8")))

out = {}
for sc in setlist:
    cid = sc["id"]
    r = {"name": sc["name"], "number": sc["number"], "api_rarity": sc["rarity"], "supertype": sc["supertype"],
         "group": group.get(cid), "issues": []}
    if cid in skipped:
        r["status"] = "skipped"
        r["reason"] = skipped[cid]
        if (HERE / "art" / f"{cid}.json").exists():
            r["issues"].append("skipped card has art")
        out[cid] = r
        continue
    if cid not in group:
        r["issues"].append("NOT IN PLAN (neither built nor skipped)")
        out[cid] = r
        continue
    card = json.load(open(HERE / "cards" / f"{cid}.json", encoding="utf-8"))
    api = json.load(open(HERE / "cards/api" / f"{cid}.json", encoding="utf-8"))
    tier = card["tier"]
    r["tier"] = tier
    diff = [k for k in card if k not in ("tier", "set", "images")
            and card[k] != api.get(k, card[k] if card[k] in ([], "") else None)]
    if diff or tier != api["rarity"] or api["id"] != cid or api["set"]["id"] != "me55":
        r["issues"].append(f"card data not verbatim: {diff}, tier {tier} api {api['rarity']}")
    if not (card.get("attacks") or card.get("abilities")):
        r["issues"].append("card data has no attacks/abilities")
    af = HERE / "art" / f"{cid}.json"
    if not af.exists():
        r["issues"].append("no art json")
        out[cid] = r
        continue
    art = json.load(open(af, encoding="utf-8"))
    (vn, v), = art["variants"].items()
    r.update(pokemon=art["pokemon"], variant=vn, finish=v["finish"], label=v["label"], flip=v["flip"],
             size=[len(v["rows"][0]), len(v["rows"]) // 2], art_rarity=v["rarity"])
    if art["pokemon"] != sprite[cid]:
        r["issues"].append(f"sprite {art['pokemon']} != plan {sprite[cid]}")
    for d in ("regular", "shiny"):
        if not (VENDOR / d / art["pokemon"]).exists():
            r["issues"].append(f"vendor sprite {d}/{art['pokemon']} missing")
    if v["rarity"] != tier:
        r["issues"].append(f"art rarity {v['rarity']} != tier {tier}")
    fin, kind, frame = RECIPE[tier]
    if not v["finish"].startswith(fin):
        r["issues"].append(f"finish '{v['finish']}' is not the {tier} recipe")
    info = sizes.get(cid, {})
    r["frame"] = info.get("frame")
    if info and info.get("frame") != frame:
        r["issues"].append(f"frame {info.get('frame')} != {frame}")
    # frame colour actually in the card's text half
    ca = HERE / "out" / f"{cid}-card.ans"
    if not ca.exists():
        r["issues"].append("out card.ans missing")
    else:
        rgb = L.hexrgb(frame)
        if "2;%d;%d;%d" % rgb not in ca.read_text(encoding="utf-8"):
            r["issues"].append(f"frame colour {frame} not in card.ans")
    for k in ("art", "card"):
        for sfx in ("", "-shiny"):
            for ext in ("png", "ans"):
                if not (HERE / "out" / f"{cid}-{k}{sfx}.{ext}").exists():
                    r["issues"].append(f"out {k}{sfx}.{ext} missing")
    if tier == "Common":
        pal = art["palette"]
        if any(ch not in ".k" and ch not in pal for row in v["rows"] for ch in row):
            r["issues"].append("common: key without colour")
        if vn != "common":
            r["issues"].append("common variant name")
    if art.get("sprite_recolour") or v.get("sprite_recolour"):
        r["issues"].append("recolour recorded in art")
    stat = {}
    for sh in (False, True):
        p = {**art["palette"], **v.get("palette", {})}
        if sh:
            p = {**p, **art.get("shiny", {}), **v.get("shiny", {})}
        stat[sh] = [[None if ch == "." else L.hexrgb(p[ch]) for ch in row] for row in v["rows"]]
    r["anim"] = []
    for sh in (False, True):
        nm = cid + ("_shiny" if sh else "")
        d = HERE / "anim" / nm
        if kind is None:
            if d.exists():
                r["issues"].append(f"common has anim {nm}")
            continue
        f = d / f"{nm}.json"
        if not f.exists() or not (d / f"{nm}.anim").exists():
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
        hdr = json.loads((d / f"{nm}.anim").read_text(encoding="utf-8").split("\f")[0])
        r["anim"].append(f"{nm}:{hdr.get('frames')}")
    out[cid] = r

(HERE / "work/audit/meta.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
built = [c for c, r in out.items() if r.get("pokemon")]
print("setlist", len(setlist), "built", len(built), "skipped", sum(r.get("status") == "skipped" for r in out.values()))
for cid, r in out.items():
    if r["issues"]:
        print(cid, r["name"], r.get("tier"), r["issues"])
