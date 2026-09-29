r"""Assemble the real-card pokemon pack: every card is a real printed card keyed by its pokemontcg.io id.

  .venv\Scripts\python tools\build_realcards.py                    # rebuild every card in pack.json from its source
  .venv\Scripts\python tools\build_realcards.py import suite3      # import a batch: the last batch (style-lab/suite3)
  .venv\Scripts\python tools\build_realcards.py import evs         # the Evolving Skies batch (style-lab/evs), when it lands
  .venv\Scripts\python tools\build_realcards.py import p30         # the 30th Celebration batch (style-lab/p30)
  .venv\Scripts\python tools\build_realcards.py import <folder>    # any folder of ART_FORMAT files (see "Batches" below)
  .venv\Scripts\python tools\build_realcards.py tiers              # sync tier labels/weights/families from rarities.json
  The batches' code, and how every card is made, is in artlab/ (docs/ART_METHOD.md); --lab is where their data and
  outputs live (art/, anim/, cards/ per batch: the git-excluded style-lab/ by default).
  options: --lab <style-lab folder> (default: <repo>\style-lab), --vendor <folder> (default: <repo>\vendor),
           --pack <id> (default pokemon), --only <id,id,...>, --effects (render with artlab/rarities/effects.py),
           --dry-run (report what would change, write nothing)

For each card it writes (all local-only, git-ignored: they embed Nintendo sprites and copyrighted card text)
  packs/pokemon/cards/<id>.json                 the text half, from the API (tools/fetch_cards.py, docs/CARD_FORMAT.md)
  packs/pokemon/art/<id>.json                   the art (docs/ART_FORMAT.md): one variant named after the card id
  dist/pokemon/<character>-<id>[-shiny].ans     the prebuilt ANSI the runtime prints (tools/build_art.py)
  dist/pokemon/<character>-<id>[-shiny].anim    the card's approved effect loop, copied from the batch when it has one
                                                (<batch>/anim/<id>[_shiny]/, suite3: anim/<variant>_<character>[_shiny]/)
                                                and its final frame is exactly the .ans; played by scripts/lib/anim.ps1
and records the card in pack.json "cards" (character, tier, name, number, rarity, set, source): the one tracked
file. A card's tier is its printed rarity: the pack tier whose "rarity" matches the API's `rarity` field. A card
whose rarity no tier names is refused (add the tier to pack.json first).

Batches
  A batch is a folder of ART_FORMAT JSON files whose variants carry "card": "<pokemontcg.io id>" (style-lab's
  suite3 files do: {"id": "pikachu", "variants": {"fullart": {"card": "swsh4-170", "rows": [...]}}}). The art
  file's "id" (or "pokemon", or a variant's "character") is the sprite name. Only real ids count: variants whose card is
  "invented", carries a "*" (a made-up variation), or whose label says "invented" are skipped, and so are the
  batch's skip_variants (suite3: common_bg, the scene-backed common; commons use the plain sprite).
  A batch may also have cards/<id>.json (CARD_FORMAT, e.g. style-lab/evs/cards): those are used instead of the API
  and every card listed there is imported. A Common card with no art in the batch gets the plain
  pokemon-colorscripts sprite from vendor/ (2x2 grid px per sprite px, like suite3's commons). Listed Commons that
  are Trainers or have no colorscripts sprite (the Gen 9 ones) are skipped and reported.

Effects (later)
  --effects loads artlab/rarities/effects.py and calls, per card,
      render_card(card=<CARD_FORMAT dict>, art=<the ART_FORMAT dict built from the batch>, rarity=<rarities.json entry or None>)
  which returns an ART_FORMAT dict (same shape) to save instead. Without --effects the batch art is used as-is.
"""
import argparse
import importlib.util
import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import build_art  # noqa: E402
import fetch_cards  # noqa: E402

REAL_ID = re.compile(r"^[a-z0-9]+-[A-Za-z0-9]+$")
BATCHES = {
    # name: folder under --lab, art file globs, variants to skip
    "suite3": {"dir": "suite3", "globs": ["*-suite3.json"], "skip_variants": ["common_bg"]},
    "evs": {"dir": "evs", "globs": ["*.json", "art/*.json", "out/*.json", "suite/*.json"], "skip_variants": ["common_bg"]},
    # 30th Celebration (me55): one ART_FORMAT file per card in art/ (commons too; the importer uses the plain sprite
    # for those anyway), card data in p30/cards/, effect loops in p30/anim/<id>[_shiny]/ as evs
    "p30": {"dir": "p30", "globs": ["art/*.json"], "skip_variants": []},
}
NOT_ART_DIRS = {"cards", "api", "masks", "ref", "work", "__pycache__", "anim"}
NAME_SUFFIXES = re.compile(r"\s+(V|VMAX|VSTAR|V-UNION|ex|EX|GX|LV\.X|BREAK|Prime|LEGEND|δ|☆|◇|star)$")
NAME_PREFIXES = re.compile(r"^(Radiant|Dark|Light|Shining|Galarian|Alolan|Hisuian|Paldean|Team Rocket's|Rocket's|[A-Z][a-z]+'s)\s+")


# ---------------------------------------------------------------- pack.json
def pack_path(pack):
    return ROOT / "packs" / pack / "pack.json"


def load_pack(pack):
    return json.loads(pack_path(pack).read_text(encoding="utf-8"))


def save_pack(pack, pj):
    pack_path(pack).write_text(json.dumps(pj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def character_of(name):
    """the sprite name for an API card name: 'Umbreon VMAX' -> umbreon, 'Mr. Mime' -> mr-mime"""
    n = NAME_SUFFIXES.sub("", name.strip())
    n = NAME_PREFIXES.sub("", n)
    n = n.replace("♀", "-f").replace("♂", "-m").replace("é", "e")
    n = re.sub(r"[.'’:]", "", n.lower())
    return re.sub(r"[^a-z0-9]+", "-", n).strip("-")


def name_matches(character, name):
    import unicodedata
    fold = lambda s: "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))  # Flabébé -> Flabebe  # noqa: E731
    squash = lambda s: re.sub(r"[^a-z0-9]", "", fold(s).lower().replace("♀", "f").replace("♂", "m"))  # noqa: E731
    # form sprites (garbodor-gmax, lycanroc-dusk, articuno-galar) match on the base Pokémon's name
    base = re.sub(r"-(gmax|galar|alola|hisui|paldea|dusk|midday|midnight|mega.*|sunshine|poke-ball|low-key|crowned|red|orange|yellow|green|blue|indigo|violet)$", "", character)
    return squash(character) in squash(name) or squash(base) in squash(name)


def tag_of(card):
    """what the card frame's top edge shows on the right: the printed number, e.g. 170/185, SV6/SV94"""
    num, tot = str(card.get("number") or ""), (card.get("set") or {}).get("printedTotal")
    if not num:
        return ""
    if not tot:
        return num
    m = re.match(r"^([A-Za-z]+)\d+$", num)
    return f"{num}/{m.group(1) if m else ''}{tot}"


# ---------------------------------------------------------------- art
def used_keys(rows):
    return {ch for r in rows for ch in r if ch != "."}


def card_art(character, card_id, name, rows, palette, shiny, source):
    """one card's ART_FORMAT dict: palette / shiny trimmed to the keys the rows use; the variant is the card id,
    so build_art writes dist/<pack>/<character>-<card id>[-shiny].ans"""
    keys = used_keys(rows)
    missing = keys - set(palette)
    if missing:
        raise SystemExit(f"{card_id}: rows use keys with no colour: {''.join(sorted(missing))}")
    pal = {k: palette[k] for k in sorted(keys)}
    sh = {k: shiny[k] for k in sorted(keys) if k in shiny and shiny[k].lower() != pal[k].lower()}
    art = {"id": character, "card": card_id, "name": name, "source": source, "palette": pal}
    if sh:
        art["shiny"] = sh
    art["variants"] = {card_id: {"rows": rows}}
    return art


def batch_variants(folder, globs, skip_variants):
    """(card id, character, variant name, rows, palette, shiny, file) for every real card variant in a batch folder"""
    out, seen_files = [], set()
    for g in globs:
        for f in sorted(folder.glob(g)):
            if f in seen_files or not f.is_file() or set(f.relative_to(folder).parts[:-1]) & NOT_ART_DIRS:
                continue
            seen_files.add(f)
            try:
                d = json.loads(f.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            if not isinstance(d, dict):
                continue
            variants = d.get("variants")
            if not isinstance(variants, dict):
                if "rows" in d and "card" in d:        # a single-card art file
                    variants = {d.get("variant", "card"): d}
                else:
                    continue
            base_pal, base_sh = d.get("palette") or {}, d.get("shiny") or {}
            for vname, v in variants.items():
                cid = str(v.get("card") or "")
                if not cid or vname in skip_variants:
                    continue
                if "*" in cid or not REAL_ID.match(cid) or "invented" in str(v.get("label", "")).lower():
                    print(f"  skip {f.name}:{vname} ({cid or 'no card'}: not a real card)")
                    continue
                pal = {**base_pal, **(v.get("palette") or {})}
                sh = {**pal, **base_sh, **(v.get("shiny") or {})}
                # the sprite name: suite3 files are per Pokemon ("id": "pikachu"); evs files are per card
                # ("id": "swsh7-125", "pokemon": "eevee")
                ch = v.get("character") or d.get("character") or d.get("pokemon") or (None if REAL_ID.match(str(d.get("id", ""))) else d.get("id"))
                out.append((cid, ch, vname, v["rows"], pal, sh, f))
    return out


def load_sprite(vendor, character, shiny=False):
    """the pokemon-colorscripts large sprite as an RGB grid (each sprite px = '██', 2 cols x 1 line)"""
    f = vendor / "pokemon-colorscripts" / "colorscripts" / "large" / ("shiny" if shiny else "regular") / character
    if not f.exists():
        raise SystemExit(f"no colorscripts sprite for '{character}' ({f})")
    tok = re.compile(r"\x1b\[([0-9;]*)m|(.)", re.S)
    rows, fg = [], None
    for ln in f.read_text(encoding="utf-8").replace("\r\n", "\n").split("\n"):
        cells = []
        for m in tok.finditer(ln):
            if m.group(2) is None:
                p = [int(x) if x else 0 for x in (m.group(1) or "0").split(";")]
                if p[:2] == [38, 2]:
                    fg = tuple(p[2:5])
                elif p == [0]:
                    fg = None
                continue
            cells.append(fg if m.group(2) == "█" else None)
        rows.append(cells)
    while rows and not any(rows[-1]):
        rows.pop()
    while rows and not any(rows[0]):
        rows.pop(0)
    w = max(len(r) for r in rows)
    rows = [r + [None] * (w - len(r)) for r in rows]
    g = [r[0::2] for r in rows]
    cols = [x for x in range(len(g[0])) if any(r[x] for r in g)]
    return [r[min(cols):max(cols) + 1] for r in g]


def sprite_rows(vendor, character):
    """the plain sprite at grid resolution (2x2 grid px per sprite px): rows, palette, shiny palette"""
    n, s = load_sprite(vendor, character), load_sprite(vendor, character, True)
    if len(n) != len(s) or len(n[0]) != len(s[0]):
        raise SystemExit(f"{character}: regular and shiny sprites differ in size")
    # palette keys may be any single code point (docs/ART_FORMAT.md); some sprites pair up >60 regular/shiny colours
    keys = "abcdefghijmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" + "".join(chr(c) for c in range(0x3B1, 0x3CA)) + "".join(chr(c) for c in range(0x430, 0x450)) + "".join(chr(c) for c in range(0x100, 0x180)) + "".join(chr(c) for c in range(0x410, 0x430))  # busy sprites (Moltres)
    pairs, pal, sh, rows = {}, {}, {}, []
    for rn, rs in zip(n, s):
        row = ""
        for cn, cs in zip(rn, rs):
            if cn is None:
                row += ".."
                continue
            if (cn, cs) not in pairs:
                k = "k" if cn == (0, 0, 0) and cs == (0, 0, 0) else keys[len([v for v in pairs.values() if v != "k"])]
                pairs[(cn, cs)] = k
                pal[k], sh[k] = "#%02x%02x%02x" % cn, "#%02x%02x%02x" % cs
            row += pairs[(cn, cs)] * 2
        rows += [row, row]
    return rows, pal, sh


# ---------------------------------------------------------------- effects / rarities (artlab/rarities)
def rarities_dir(lab):
    """rarities.json + effects.py: the tracked artlab/rarities (docs/ART_METHOD.md), else the lab's own copy"""
    tracked = ROOT / "artlab" / "rarities"
    return tracked if (tracked / "rarities.json").exists() else lab / "rarities"


def load_rarities(lab):
    f = rarities_dir(lab) / "rarities.json"
    if not f.exists():
        return None
    d = json.loads(f.read_text(encoding="utf-8"))
    items = d.get("rarities", d) if isinstance(d, dict) else d
    if isinstance(items, dict):
        items = [{"id": k, **v} for k, v in items.items()]
    return {str(r.get("id")): r for r in items if isinstance(r, dict) and r.get("id")}


def load_effects(lab):
    f = rarities_dir(lab) / "effects.py"
    if not f.exists():
        raise SystemExit(f"--effects: {f} does not exist yet")
    spec = importlib.util.spec_from_file_location("pokeshell_effects", f)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(f.parent))
    spec.loader.exec_module(mod)
    if not hasattr(mod, "render_card"):
        raise SystemExit(f"--effects: {f} has no render_card(card=, art=, rarity=)")
    return mod


def rarity_entry(rarities, tier, api_rarity):
    if not rarities:
        return None
    if tier in rarities:
        return rarities[tier]
    for r in rarities.values():
        names = [r.get(k) for k in ("rarity", "api_rarity", "printed", "label")]
        if api_rarity in names:
            return r
    return None


# ---------------------------------------------------------------- import / build
def anim_bundles(folder, cid, vname, character):
    """the batch's effect-loop bundles for a card: {"": <.anim>, "-shiny": <.anim>} (either may be missing).
    evs: <batch>/anim/<card id>[_shiny]/<card id>[_shiny].anim; suite3: <batch>/anim/<variant>_<character>[_shiny]/..."""
    out = {}
    for name in [cid] + ([f"{vname}_{character}"] if vname and character else []):
        for suffix, sub in (("", name), ("-shiny", f"{name}_shiny")):
            f = folder / "anim" / sub / f"{sub}.anim"
            if suffix not in out and f.is_file():
                out[suffix] = f
    return out


def anim_final(anim_file):
    """the final frame of an .anim bundle (JSON header line, then frames after form feeds): what it must end on"""
    parts = anim_file.read_text(encoding="utf-8").split("\f")
    hdr = json.loads(parts[0])
    frames = parts[1:]
    if len(frames) != int(hdr.get("frames", len(frames))) or not frames:
        raise ValueError(f"{anim_file.name}: {len(frames)} frames, header says {hdr.get('frames')}")
    return frames[int(hdr.get("final", len(frames) - 1))]


def copy_anims(pack, character, cid, anims, dry_run):
    """copy a card's effect loops next to its .ans (dist/<pack>/<character>-<card id>[-shiny].anim), each only if
    its final frame is exactly that .ans (the runtime ends the loop on it); stale ones are removed. Returns notes."""
    notes = []
    for suffix in ("", "-shiny"):
        dst = ROOT / "dist" / pack / f"{character}-{cid}{suffix}.anim"
        ans = ROOT / "dist" / pack / f"{character}-{cid}{suffix}.ans"
        src = anims.get(suffix)
        ok = False
        if src and dry_run:
            notes.append(f"anim{suffix}")
            continue
        if src and ans.exists():
            try:
                ok = anim_final(src) == ans.read_text(encoding="utf-8")
            except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as e:
                notes.append(f"anim{suffix} unreadable ({e})")
            else:
                if not ok:
                    notes.append(f"anim{suffix} skipped: its final frame is not the card's .ans")
        if ok:
            if not dst.exists() or dst.read_bytes() != src.read_bytes():
                shutil.copyfile(src, dst)
            notes.append(f"anim{suffix}")
        elif dst.exists() and not dry_run:
            dst.unlink()
            notes.append(f"removed stale {dst.name}")
    return notes


def write_card(pack, pj, cid, character, art, card, source, opts, rarities, effects, anims=None):
    """save one card: art JSON, dist ANSI (+ the batch's effect loops, if any), pack.json entry. Returns the pack.json entry."""
    tier = card.get("tier")
    if not tier:
        raise SystemExit(f"{cid}: printed rarity '{card.get('rarity')}' has no tier in pack.json (add one with that \"rarity\")")
    if not name_matches(character, card["name"]):
        raise SystemExit(f"{cid} is '{card['name']}', not {character}: check the batch's card ids")
    if effects:
        art = effects.render_card(card=card, art=art, rarity=rarity_entry(rarities, tier, card.get("rarity")))
        if not isinstance(art, dict) or "variants" not in art:
            raise SystemExit(f"{cid}: effects.render_card must return an ART_FORMAT dict")
    entry = {"character": character, "tier": tier, "name": card["name"], "number": tag_of(card),
             "rarity": card.get("rarity"), "set": (card.get("set") or {}).get("name"), "source": source}
    v = next(iter(art["variants"].values()))
    size = f"{len(v['rows'][0])}x{len(v['rows'])}px"
    if opts.dry_run:
        big = len(v["rows"][0]) > build_art.MAX_W or len(v["rows"]) > build_art.MAX_H
        notes = copy_anims(pack, character, cid, anims or {}, True)
        print(f"  would build {cid:12s} {character:11s} {tier:20s} {size:9s} {card['name']} [{source}]"
              + (f"  TOO BIG (max {build_art.MAX_W}x{build_art.MAX_H}, tools/build_art.py)" if big else "")
              + (f"  + {', '.join(notes)}" if notes else ""))
        return entry
    adir = ROOT / "packs" / pack / "art"
    adir.mkdir(parents=True, exist_ok=True)
    af = adir / f"{cid}.json"
    af.write_text(json.dumps(art, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    files = build_art.build_file(af, previews=not opts.no_previews)
    kb = sum(f.stat().st_size for f in files if not f.stem.endswith("-shiny")) / 1024
    notes = copy_anims(pack, character, cid, anims or {}, False)
    print(f"  built {cid:12s} {character:11s} {tier:20s} {size:9s} {kb:5.1f} KB  {card['name']} [{source}]"
          + (f"  + {', '.join(notes)}" if notes else ""))
    pj.setdefault("cards", {})[cid] = entry
    return entry


def import_batch(batch, opts, pj, rarities, effects):
    if batch in BATCHES:
        conf = BATCHES[batch]
        folder = opts.lab / conf["dir"]
    else:
        folder = Path(batch).resolve()
        conf = {"globs": ["*.json", "*/*.json"], "skip_variants": []}
        batch = folder.name
    if not folder.is_dir():
        raise SystemExit(f"batch folder {folder} not found (pass --lab <style-lab folder>)")
    found = batch_variants(folder, conf["globs"], conf["skip_variants"])
    by_id = {}
    for item in found:
        if item[0] in by_id:
            a, b = by_id[item[0]], item
            raise SystemExit(f"{item[0]} appears twice in batch {batch} ({a[6].name}:{a[2]}, {b[6].name}:{b[2]}); "
                             "add one of them to the batch's skip_variants")
        by_id[item[0]] = item
    batch_cards = folder / "cards"
    listed = sorted(p.stem for p in batch_cards.glob("*.json")) if batch_cards.is_dir() else []
    ids = list(by_id) + [c for c in listed if c not in by_id]
    if opts.only:
        ids = [c for c in ids if c in opts.only]
    print(f"batch {batch} ({folder}): {len(by_id)} real card variants, {len(listed)} listed cards -> {len(ids)} cards")
    cards_dir = ROOT / "packs" / opts.pack / "cards"
    done, skipped = [], []
    for cid in ids:
        card = fetch_cards.fetch(cid, pj, cards_dir, from_dir=batch_cards if batch_cards.is_dir() else None, quiet=True) \
            if not opts.dry_run else fetch_cards.card_format(_peek(cid, batch_cards, cards_dir), None)
        if opts.dry_run:
            card["tier"] = fetch_cards.tier_of(pj, card.get("rarity"))
        if card.get("rarity") == "Common":   # commons never get a background: always the plain sprite
            ch = by_id[cid][1] if cid in by_id else character_of(card["name"])
            if card.get("supertype") not in ("Pokémon", "Pokemon"):
                skipped.append(f"{cid} ({card['name']}, {card.get('rarity')}): {card.get('supertype')}, no Pokémon")
                continue
            if not (opts.vendor / "pokemon-colorscripts" / "colorscripts" / "large" / "regular" / ch).exists():
                skipped.append(f"{cid} ({card['name']}, {card.get('rarity')}): no colorscripts sprite '{ch}'")
                continue
            rows, pal, sh = sprite_rows(opts.vendor, ch)
            src = f"{batch}:sprite"
            art = card_art(ch, cid, card["name"], rows, pal, sh, src)
            anims = {}   # commons have no effect loop
        elif cid in by_id:
            _, ch, vname, rows, pal, sh, f = by_id[cid]
            art = card_art(ch, cid, card["name"], rows, pal, sh, f"{batch}:{f.name}#{vname}")
            src = f"{batch}:{f.name}#{vname}"
            anims = anim_bundles(folder, cid, vname, ch)
        else:
            skipped.append(f"{cid} ({card['name']}, {card.get('rarity')}): no art in the batch yet")
            continue
        write_card(opts.pack, pj, cid, ch, art, card, src, opts, rarities, effects, anims)
        done.append(cid)
    for s in skipped:
        print(f"  skip {s}")
    return done


def _peek(cid, batch_cards, cards_dir):
    for d in (cards_dir, batch_cards):
        if d and (d / f"{cid}.json").exists():
            return json.loads((d / f"{cid}.json").read_text(encoding="utf-8"))
    return fetch_cards.get_json(fetch_cards.API + cid)["data"]


def rebuild(opts, pj, rarities, effects):
    """rebuild every card in pack.json from its recorded source batch (the batch is re-imported for those ids)"""
    cards = pj.get("cards") or {}
    ids = [c for c in cards if not opts.only or c in opts.only]
    batches = {}
    for cid in ids:
        batches.setdefault(cards[cid].get("source", "").split(":")[0], []).append(cid)
    for b, cids in batches.items():
        if b not in BATCHES or not (opts.lab / BATCHES[b]["dir"]).is_dir():
            print(f"  cannot rebuild {', '.join(cids)}: source batch '{b}' not found under {opts.lab}")
            continue
        only = opts.only
        opts.only = set(cids)
        import_batch(b, opts, pj, rarities, effects)
        opts.only = only


def prune(pack, pj, dry_run):
    """drop art / dist files of cards that aren't in pack.json (e.g. after a card is removed from the roster)"""
    cards = pj.get("cards") or {}
    keep = {f"{v['character']}-{cid}" for cid, v in cards.items()}
    gone = []
    for f in sorted([*(ROOT / "dist" / pack).glob("*.ans"), *(ROOT / "dist" / pack).glob("*.anim")]):
        stem = f.stem[:-6] if f.stem.endswith("-shiny") else f.stem
        if stem not in keep:
            gone.append(f)
    for f in sorted((ROOT / "packs" / pack / "art").glob("*.json")):
        if f.stem not in cards:
            gone.append(f)
    for f in gone:
        print(f"  {'would remove' if dry_run else 'removed'} {f.relative_to(ROOT)} (not a card in pack.json)")
        if not dry_run:
            f.unlink()


def sync_tiers(opts, pj, rarities):
    """copy label / family / weight / rarity / skins / frame from rarities.json into pack.json tiers (by id);
    new ids are appended. pack.json stays the runtime's only source."""
    if not rarities:
        raise SystemExit(f"no {rarities_dir(opts.lab) / 'rarities.json'}")
    tiers = {t["id"]: t for t in pj["tiers"]}
    for rid, r in rarities.items():
        t = tiers.get(rid)
        if t is None:
            t = {"id": rid, "label": r.get("label", rid.replace("-", " ")), "skins": {}}
            pj["tiers"].append(t)
            tiers[rid] = t
            print(f"  + tier {rid}")
        for src, dst in (("label", "label"), ("family", "family"), ("rarity", "rarity"), ("api_rarity", "rarity"),
                         ("weight", "weight"), ("odds_weight", "weight"), ("odds", "weight"), ("skins", "skins"), ("frame", "frame")):
            if src in r and r[src] is not None and t.get(dst) != r[src]:
                print(f"  {rid}.{dst}: {t.get(dst)!r} -> {r[src]!r}")
                t[dst] = r[src]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", nargs="?", default="build", choices=["build", "import", "tiers"])
    ap.add_argument("batches", nargs="*")
    ap.add_argument("--pack", default="pokemon")
    ap.add_argument("--lab", default=str(ROOT / "style-lab"))
    ap.add_argument("--vendor", default=str(ROOT / "vendor"))
    ap.add_argument("--only", default="", help="comma-separated card ids")
    ap.add_argument("--effects", action="store_true", help="render each card with artlab/rarities/effects.py")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-previews", action="store_true", help="skip the previews/*.png")
    opts = ap.parse_args()
    opts.lab, opts.vendor = Path(opts.lab).resolve(), Path(opts.vendor).resolve()
    opts.only = {c.strip() for c in opts.only.split(",") if c.strip()}
    pj = load_pack(opts.pack)
    rarities = load_rarities(opts.lab)
    effects = load_effects(opts.lab) if opts.effects else None
    if opts.command == "tiers":
        sync_tiers(opts, pj, rarities)
    elif opts.command == "import":
        if not opts.batches:
            ap.error("import needs a batch: " + ", ".join(BATCHES) + ", or a folder")
        for b in opts.batches:
            import_batch(b, opts, pj, rarities, effects)
    else:
        rebuild(opts, pj, rarities, effects)
    if not opts.dry_run:
        if opts.command != "tiers" and not opts.only:
            prune(opts.pack, pj, False)
        save_pack(opts.pack, pj)
        n = len(pj.get("cards") or {})
        print(f"pack.json: {n} cards")


if __name__ == "__main__":
    main()
