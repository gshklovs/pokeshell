"""Export the pokeshell web binder: pulls.log + pack.json -> data.json, art PNGs, and a baked single-file page.
`pokeshell binder --web` runs this (then opens the page); nothing stays running.

  python tools/binder_web.py                          # everything, into <state>/web (about 1 s once the art is cached)
  python tools/binder_web.py --no-art                 # data.json + binder.html only: no art is decoded or written
  python tools/binder_web.py --state <dir> --out <dir> --root <checkout>

Reads
  <state>/pulls.log                       TSV: time, pack, character, tier, art, skin, shiny(0/1), flags, [key=value...]
                                          (read lossily: a line with bytes that aren't UTF-8 or a bad time is skipped)
  <state>/viewed.txt                      pull ids the binder has shown (no NEW sticker)
  packs/<pack>/pack.json                  characters, names, tags, tiers, skins + weights, odds (+ cards, retired)
  packs/<pack>/cards/<id>.json            a real card's text half (docs/CARD_FORMAT.md): HP, attacks, weakness...
  packs/<pack>/art/<id>.json              pixel grids (onepiece; falls back to ../opshell)
  dist/<pack>/<character>-<card id>[-shiny].ans   a real card's art (half-block ANSI -> pixels)
  dist/pokedex/<id>-common[-shiny].ans    pokedex sprites (half-block ANSI -> pixels)
  packs/<pack>/shaders/<skin>.hlsl        the header comment becomes the skin's description
<state> is $POKESHELL_HOME, else %LOCALAPPDATA%/pokeshell.

Writes (into --out, default <state>/web; every file is written to a temp name and swapped in)
  data.json                               everything the page needs
  img/<pack>/<character>/<tier or card id>[-shiny].png   1 px per art pixel: every built card, shiny forms that were pulled
  img/<pack>/<character>/_seen.png, <card id>-seen.png   a seen card's silhouette, when no exported art gives it (below)
  img/pokedex/_silhouettes.png            atlas of all 905 pokedex silhouettes (alpha only): the dex characters' tints
  img/.cache.json                         decoded-art cache (source mtime + size -> PNG size, tint): reruns skip decoding
  binder.html                             tools/binder-web/index.html with data.json inlined (with the img/ folder)
PNGs that no current card needs are pruned from img/ (not with --no-art, which leaves img/ alone).

Swapping art: drop a PNG into tools/binder-web/art-override/<pack>/<character>/<tier>[-shiny].png and it is copied
instead of rendered.

The earned rule (docs/BINDER_SPEC.md, the same as Pokeshell.cs ReadPulls): a pull line with an id and the
"pending" flag is pending until an `earned:<id>` line; it expires on an `expired:<id>` line, after 24 h, or when its
boot session (boot=) is over. Earned pulls export as status "collected" (caught), with "new" when viewed.txt doesn't
list them; the others as "pending" (its tab can still catch it) or "expired": both are seen, never counted, and the
page shows a seen card as its silhouette. Lines without an id are earned. Pulls that don't resolve to a current card
(unknown or `retired` in pack.json) are left out; pulls.log is never rewritten.

A seen card's silhouette (docs/BINDER_SPEC.md "Empty, seen, caught"; the same order as the app's
ArtStore::silhouette): a real card whose art is the plain sprite (it has transparent pixels, the commons; "sprite" on
the card) is its own; a scene card takes one of its character's commons ("seen" on the character: that image), else the
colorscripts sprite (vendor/pokemon-colorscripts large, or dist/pokedex/<character>-common.ans: _seen.png), else its
own art's sprite layer (the pixels its shiny art recolours, plus the dark outline, holes filled: <card id>-seen.png).
Other packs use their base art (grid) or the pulled sprite (dex). The page draws any of them as a flat shadow.
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent     # tools/
PAGE = HERE / "binder-web" / "index.html"
OVERRIDE = HERE / "binder-web" / "art-override"
ROOT = HERE.parent                         # the checkout (--root overrides)
OPSHELL = ROOT.parent / "opshell"
IMG = HERE / "img"                         # set from --out in main()
PACK_ORDER = ["pokemon", "onepiece", "pokedex"]
EXPIRE_SECS = 24 * 3600                    # Pokeshell.cs ExpireSec
BOOT_SLACK_SECS = 120                      # Pokeshell.cs BootSlackSec
CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def state_dir():
    s = os.environ.get("POKESHELL_HOME")
    return Path(s) if s else Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "pokeshell"


def ulid_secs(pid):
    """unix seconds in a ULID pull id, or None"""
    if len(pid) != 26:
        return None
    ms = 0
    for ch in pid[:10].upper():
        v = CROCKFORD.find(ch)
        if v < 0:
            return None
        ms = ms * 32 + v
    return ms / 1000


def boot_id():
    """unix seconds of this machine's last boot (0 if unknown: then boot sessions aren't compared)"""
    try:
        import ctypes
        import time
        k = ctypes.windll.kernel32
        k.GetTickCount64.restype = ctypes.c_uint64
        return int(time.time()) - int(k.GetTickCount64() // 1000)
    except Exception:
        return 0

# frame presets from scripts/lib/Pokeshell.cs (FramePresets) and the wanted-poster palettes (WantedPalettes)
FRAME_PRESETS = {
    "plain": ["#c9a93a", "#f4dc6a", "#c9a93a"],
    "silver": ["#8d97a5", "#eef3f8", "#9aa6b4", "#f7fafc", "#8d97a5"],
    "holo": ["#7fa7d9", "#e6f0ff", "#b59ce0", "#e8fbff", "#7fd3c9"],
    "rainbow": ["#ff6b8b", "#ffb86b", "#ffe66b", "#7df09a", "#6bd5ff", "#9a8bff", "#ff6bd6"],
    "gold": ["#b8862b", "#fff1b0", "#d4a43a", "#fff7d6", "#c8952e"],
}
WANTED_PALETTES = {   # paper, stain, ink, accent; "" paper = gold leaf
    "common": ["#e6d3a3", "#cfb57c", "#3b2616", "#3b2616"],
    "super-rare": ["#cfa467", "#9c7040", "#2a170a", "#8e1b12"],
    "secret-rare": ["", "", "#3a2408", "#7a1a10"],
    "manga": ["#ecebe4", "#c9c8c0", "#111111", "#c8281e"],
}


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def read_text(path):
    """a text file, read lossily (a stray ANSI byte from PowerShell 5 becomes U+FFFD instead of a crash)"""
    return path.read_bytes().decode("utf-8-sig", errors="replace")


def write_atomic(path, data):
    """write text or bytes to a temp file next to path, then swap it in (a browser never reads half a file)"""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    if isinstance(data, str):
        tmp.write_text(data, encoding="utf-8")
    else:
        tmp.write_bytes(data)
    os.replace(tmp, path)


TIME_RE = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?([+-]\d{2}:?\d{2}|Z)?")


# ---------------------------------------------------------------- pulls
def read_pulls(log, viewed=frozenset(), now=None, boot=None, bad=None):
    """pulls.log with the earned rule applied (see the module doc). Lines that can't be read (bytes that aren't
    UTF-8, a time that isn't ISO) are skipped and counted in bad[0]"""
    import time
    now = time.time() if now is None else now
    boot = boot_id() if boot is None else boot
    bad = [0] if bad is None else bad
    pulls = []
    if not log.exists():
        print(f"warning: no pulls log at {log}", file=sys.stderr)
        return pulls
    lines = read_text(log).splitlines()
    earned, expired = set(), set()
    for line in lines:
        f = line.split("\t")
        if 2 <= len(f) < 7:
            ev = f[1].strip()
            if ev.startswith("earned:"):
                earned.add(ev[7:])
            elif ev.startswith("expired:"):
                expired.add(ev[8:])
    for n, line in enumerate(lines):
        f = line.split("\t")
        if len(f) < 7:
            continue
        flags = f[7].strip() if len(f) >= 8 else ""
        if "dryrun" in flags:                       # same rule as Read-Pulls in scripts/pokeshell.ps1
            continue
        if "�" in line or not TIME_RE.fullmatch(f[0].strip()):
            bad[0] += 1                             # mangled bytes or a corrupt time: not a pull we can show
            continue
        kv = dict(x.split("=", 1) for x in f[8:] if "=" in x)
        pid, card = kv.get("id", "").strip(), kv.get("card", "").strip()
        try:
            pboot = int(kv.get("boot", "0"))
        except ValueError:
            pboot = 0
        pending = "pending" in [x.strip() for x in flags.split(",")]
        if not pid or not pending or pid in earned:
            status = "collected"
        elif pid in expired:
            status = "expired"                      # seen, not caught (docs/BINDER_SPEC.md "Empty, seen, caught")
        else:
            t = ulid_secs(pid)
            expired_now = (t is not None and now - t > EXPIRE_SECS) or (pboot and boot and abs(pboot - boot) > BOOT_SLACK_SECS)
            status = "expired" if expired_now else "pending"   # expired: the tab was never used
        pulls.append({
            "id": n + 1, "pull": pid or None, "card": card or None,
            "time": f[0].strip().replace(" ", "T"), "pack": f[1], "char": f[2], "tier": f[3], "art": f[4],
            "skin": f[5] or None, "shiny": f[6].strip() == "1",
            "flags": [x for x in re.split(r"[,; ]+", flags) if x],
            "status": status,
            "new": status == "collected" and bool(pid) and pid not in viewed,
        })
    return pulls


def card_built(pid, char, cid):
    """a real card's art is built: dist/<pack>/<character>-<card id>.ans exists (the roll's test,
    Test-PokeshellCardBuilt in scripts/lib/common.ps1). Cards without it never roll."""
    return (ROOT / "dist" / pid / f"{char}-{cid}.ans").is_file()


def mute_unbuilt(pid, pk):
    """a real-card pack keeps only its built cards: an unbuilt card is muted, so it is no binder slot and pulls that
    resolve to it are hidden (like retired ones) until its art is built; pulls.log is never rewritten"""
    if pk and isinstance(pk.get("cards"), dict):
        built = {cid: c for cid, c in pk["cards"].items() if card_built(pid, c.get("character") or "", cid)}
        pk["_unbuilt"] = [cid for cid in pk["cards"] if cid not in built]
        pk["cards"] = built
    return pk


def load_pack_json(pid, quiet=True):
    """pack.json with unbuilt cards muted, or None (missing, or not valid JSON: warned about unless quiet)"""
    f = ROOT / "packs" / pid / "pack.json"
    if not f.exists():
        return None
    try:
        return mute_unbuilt(pid, json.loads(read_text(f)))
    except ValueError as e:
        if not quiet:
            print(f"warning: {f} is not valid JSON ({e}); pack left out", file=sys.stderr)
        return None


def logged_card(pk, char, art, card=None):
    """the real card a pull line names itself (its card= or art column, same character), else None"""
    cards = pk.get("cards")
    if not isinstance(cards, dict):
        return None
    return next((cid for cid in (card, art) if cid and (cards.get(cid) or {}).get("character") == char), None)


def resolve_pull(pk, char, tier, art, card=None):
    """what a pull shows today: (character, tier id, card id or None), or None to hide it. The rule of
    Resolve-PokeshellPull (scripts/lib/common.ps1, docs/PACK_FORMAT.md "retired"):
      packs without "cards": as logged (tier by id, or by label);
      real-card packs: the art column (or a card= column) is a card id of the pack whose character matches ->
      that card; else retired["<character>/<tier>"] names a card -> that card; else hidden.
    pk comes from load_pack_json: unbuilt cards are left out, so a pull resolving to one is hidden too"""
    cards = pk.get("cards")
    if not isinstance(cards, dict):
        tiers = pk.get("tiers") or []
        ids = [t["id"] for t in tiers]
        t = tier if tier in ids else next((x["id"] for x in tiers if x.get("label", "").lower() == tier.lower()), None)
        return (char, t, None) if t and char in (pk.get("characters") or []) else None
    cid = logged_card(pk, char, art, card)
    if cid:
        return char, cards[cid]["tier"], cid
    retired = pk.get("retired") or {}
    now = retired.get(f"{char}/{tier}") if isinstance(retired, dict) else None
    c = cards.get(now) if now else None
    return (c["character"], c["tier"], now) if c else None


def resolve_pulls(pulls):
    """each pull as the card it shows today; the ones that don't resolve (retired art, an unbuilt card) are left out
    and counted. Also returns when the real cards went live: the time of the first shown pull whose line names a
    built real card itself (the default best_since)"""
    out, hidden, cache, real_since = [], 0, {}, None
    for p in pulls:
        if p["pack"] not in cache:
            cache[p["pack"]] = load_pack_json(p["pack"])
        pk = cache[p["pack"]]
        r = resolve_pull(pk, p["char"], p["tier"], p["art"], p["card"]) if pk else None
        if not r:
            hidden += 1
            continue
        char, tier, card = r
        if logged_card(pk, p["char"], p["art"], p["card"]) and (real_since is None or p["time"] < real_since):
            real_since = p["time"]
        out.append({**p, "char": char, "tier": tier, "card": card or p["card"]})
    return out, hidden, real_since


def best_since(setting, default):
    """config.txt best_since: "all" -> None (every pull); "YYYY-MM-DD[THH:MM[:SS]]" -> that local time (pull times
    compare as ISO strings); anything else (unset) -> default, when the real cards went live"""
    v = (setting or "").strip()
    if v.lower() == "all":
        return None
    v = v.replace(" ", "T")
    return v if re.fullmatch(r"\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}(:\d{2})?)?", v) else default


def ansi_grid(text):
    """a half-block truecolor .ans (dist/) back to pixels: two pixel rows per text row, None = transparent"""
    rows = []
    for line in text.replace("\r\n", "\n").split("\n"):
        if not line.strip() and not rows:
            continue
        top, bot = [], []
        fg = bg = None
        i = 0
        while i < len(line):
            ch = line[i]
            if ch == "\x1b" and i + 1 < len(line) and line[i + 1] == "[":
                j = i + 2
                while j < len(line) and not ("@" <= line[j] <= "~"):
                    j += 1
                if j < len(line) and line[j] == "m":
                    ps = [int(x) if x.isdigit() else 0 for x in line[i + 2:j].split(";")] or [0]
                    k = 0
                    while k < len(ps):
                        v = ps[k]
                        if v == 0:
                            fg = bg = None
                        elif v in (38, 48) and k + 4 < len(ps) + 0 and ps[k + 1] == 2:
                            col = tuple(ps[k + 2:k + 5])
                            if v == 38:
                                fg = col
                            else:
                                bg = col
                            k += 4
                        elif v == 39:
                            fg = None
                        elif v == 49:
                            bg = None
                        k += 1
                i = j + 1
                continue
            if ch == "▀":
                top.append(fg); bot.append(bg)
            elif ch == "▄":
                top.append(bg); bot.append(fg)
            elif ch == "█":
                top.append(fg); bot.append(fg)
            else:
                top.append(bg); bot.append(bg)
            i += 1
        rows += [top, bot]
    while rows and not any(rows[-1]):
        rows.pop()
    w = max((len(r) for r in rows), default=1)
    return [r + [None] * (w - len(r)) for r in rows] or [[None]]


# ---------------------------------------------------------------- packs + odds
def skin_blurb(path):
    """The shader's header comment: 'Imitates: ...' paragraph, flattened to one or two sentences."""
    if not path.exists():
        return None, None
    lines = []
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines()[:40]:
        s = raw.strip()
        if not s.startswith("//"):
            break
        lines.append(s.lstrip("/").strip())
    text = " ".join(l for l in lines if l and not set(l) <= set("=-"))
    title = None
    m = re.search(r"Skin:\s*([^\n]+?)(?:\s+Imitates:|$)", text)
    if m:
        title = m.group(1).strip()
    else:
        m = re.match(r"([A-Z0-9' .-]+?)\s+-\s+Windows Terminal", text)
        if m:
            title = m.group(1).strip()
    if title:
        title = re.sub(r"\s*\([^)]*\)", "", title).replace("-", " ").strip() or title   # "Shiny-Vault", "X (etched texture)"
    m = re.search(r"Imitates:\s*(.+)", text)
    desc = m.group(1) if m else text
    desc = re.sub(r"\s+", " ", desc).strip()
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z])", desc)
    parts = [p for p in parts if "Windows Terminal" not in p and "ps_4" not in p and "shader" not in p.lower()]
    out = ""
    for p in parts:
        if len(out) + len(p) > 260 and out:
            break
        out = (out + " " + p).strip()
    return title, out[:320]


SUFFIX_WORDS = {"V", "VMAX", "VSTAR", "GX", "EX", "ex", "BREAK", "LV.X", "Prime", "δ", "◇", "☆", "Star", "Radiant"}


def base_name(name):
    """a card name without its mechanic words: "Rayquaza VMAX" -> "Rayquaza", "Radiant Charizard" -> "Charizard" """
    words = [w for w in (name or "").split() if w not in SUFFIX_WORDS]
    return " ".join(words) or (name or "")


def card_pack_info(pid, p, n_active_packs):
    """a real-card pack (pack.json "cards", docs/PACK_FORMAT.md). The odds are the game's (Show-CardOdds /
    Add-PokeshellCardRows): a tier rolls by its weight among the tiers that have a weight and at least one built card
    (p comes muted: unbuilt cards are gone), then one of its built cards uniformly. Tiers that can't drop are left out."""
    cards = p["cards"]
    unbuilt = p.get("_unbuilt") or []
    if unbuilt:
        print(f"warning: {pid}: {len(unbuilt)} cards in pack.json have no built art (they never drop and get no slot): "
              f"{', '.join(unbuilt[:12])}{' ...' if len(unbuilt) > 12 else ''}", file=sys.stderr)
    live = [t for t in p["tiers"] if int(t.get("weight", 0)) > 0 and any(c.get("tier") == t["id"] for c in cards.values())]
    total = sum(int(t.get("weight", 0)) for t in live) or 1
    out_tiers = []
    for t in live:
        pr = int(t.get("weight", 0)) / total
        n = sum(1 for c in cards.values() if c.get("tier") == t["id"])
        skins = t.get("skins") or {}
        sw = sum(int(x) for x in skins.values()) or 1
        frame = t.get("frame")
        if isinstance(frame, list):
            fr = {"style": "card", "preset": "custom", "colors": frame}
        else:
            name = frame if isinstance(frame, str) and frame in FRAME_PRESETS else "plain"
            fr = {"style": "card", "preset": name, "colors": FRAME_PRESETS[name]}
        out_tiers.append({"id": t["id"], "label": t.get("label", t["id"]), "art": t["id"], "frame": fr,
                          "family": t.get("family") or "", "rarity": t.get("rarity") or "",
                          "shiny": t.get("shiny") or "",   # "printed": the cards print the shiny Pokemon, never rolled shiny
                          "odds": pr, "card_odds": pr / n if n else 0, "cards": n,
                          "skins": [{"id": s, "weight": int(w), "odds": pr * int(w) / sw} for s, w in skins.items()]})
    live_ids = {t["id"] for t in live}
    # every droppable card with its tags and text half (docs/BINDER_SPEC.md "Tags and search", CARD_FORMAT.md),
    # set by set in checklist (printed number) order
    card_list, no_text = [], []
    for cid, c in cards.items():
        if c.get("tier") not in live_ids or not c.get("character"):
            continue
        m = card_meta(pid, cid, c)
        if not m.get("text"):
            no_text.append(cid)
        card_list.append(m)
    if no_text:
        print(f"warning: {pid}: {len(no_text)} cards have no card text (packs/{pid}/cards/<id>.json; tools/fetch_cards.py): "
              f"{', '.join(no_text[:12])}{' ...' if len(no_text) > 12 else ''}", file=sys.stderr)
    # characters, named after their cards ("moltres-galar" -> "Galarian Moltres", "rayquaza" -> "Rayquaza")
    order, names = [], {}
    for c in card_list:
        ch = c["character"]
        if ch not in order:
            order.append(ch)
        b = base_name(c["name"])
        if b and (ch not in names or len(b) < len(names[ch])):
            names[ch] = b
    given = p.get("names") or {}
    chars = [{"id": ch, "no": i + 1, "name": given.get(ch) or names.get(ch) or ch.replace("-", " ").title(),
              "tag": "", "poster": None, "bounty": None} for i, ch in enumerate(order)]
    sets = []
    for c in card_list:
        if c["set_id"] and c["set_id"] not in [s["id"] for s in sets]:
            sets.append({"id": c["set_id"], "name": c["set_name"] or c["set_id"]})
    set_ix = {s["id"]: i for i, s in enumerate(sets)}
    card_list.sort(key=lambda c: (set_ix.get(c["set_id"], 1 << 30), number_key(c["number"]), c["id"]))
    for s in sets:
        s["total"] = sum(1 for c in card_list if c["set_id"] == s["id"])
        s["printed"] = max([c.get("printed") or 0 for c in card_list if c["set_id"] == s["id"]] + [0])
    for c in card_list:
        c.pop("printed", None)
    return {"id": pid, "name": p.get("name", pid), "about": p.get("about"), "foil_chance": 0,
            "shiny_chance": float(p.get("shiny_chance", 0)), "layout": "cards", "tiers": out_tiers,
            "characters": chars, "active_packs": n_active_packs, "cards": card_list, "sets": sets,
            "unbuilt": len(unbuilt)}


def number_key(n):
    """checklist order (as the app's): the numbered main run first (1, 2, ... 215; "215/203" -> 215, "25a" after "25"),
    then each prefixed group in numeric order inside it (GG01..GG70, SV1..SV94, TG01..TG30), then letters alone (B, G,
    R), then cards without a number"""
    head = (n or "").split("/")[0].strip()
    if not head:
        return (3, "", 0, "", "")
    m = re.fullmatch(r"([A-Za-z]*)(\d*)(.*)", head)
    prefix, digits, rest = m.groups() if m else ("", "", head)
    num = int(digits) if digits else -1
    return (0 if not prefix else 1 if digits else 2, prefix.upper(), num, rest.lower(), head)


def energy(xs):
    return [x for x in (xs or []) if isinstance(x, str)]


def scan_url(cid, large):
    """the printed card's scan (the page's `p` toggle shows it beside ours, caught cards only): its card data's
    images.large, else pokemontcg.io's image for the card id (<set>-<number>); None when the id isn't one. Only the
    URL goes into data.json: the browser fetches the scan itself, nothing is downloaded or shipped here."""
    if isinstance(large, str) and large.strip().startswith(("https://", "http://")):
        return large.strip()
    s, _, n = cid.partition("-")
    ok = lambda x: bool(x) and bool(re.fullmatch(r"[A-Za-z0-9_]+", x))
    return f"https://images.pokemontcg.io/{s}/{n}_hires.png" if ok(s) and ok(n) else None


def card_meta(pid, cid, c):
    """a real card's display fields and tags: pack.json's card entry, completed from packs/<pack>/cards/<id>.json
    (docs/CARD_FORMAT.md) when it exists: set, printed rarity, subtypes, types, artist, and the text half ("text":
    HP, stage, abilities, attacks with their energy cost, weakness / resistance / retreat, rules, flavor)"""
    number = c.get("number") or ""
    m = {"id": cid, "character": c["character"], "tier": c["tier"], "name": c.get("name") or "", "number": number,
         "rarity": c.get("rarity") or "", "set_id": cid.rsplit("-", 1)[0] if "-" in cid else "", "set_name": c.get("set") or "",
         "subtypes": [], "types": [], "artist": ""}
    m["scan"] = scan_url(cid, None)
    f = ROOT / "packs" / pid / "cards" / f"{cid}.json"
    if not f.exists():
        return m
    try:
        d = json.loads(read_text(f))
    except ValueError:
        print(f"warning: {f} is not valid JSON; card text left out", file=sys.stderr)
        return m
    m["scan"] = scan_url(cid, (d.get("images") or {}).get("large"))
    s = d.get("set") or {}
    m["set_id"] = s.get("id") or m["set_id"]
    m["set_name"] = s.get("name") or m["set_name"]
    m["printed"] = int(s.get("printedTotal") or 0)
    m["rarity"] = d.get("rarity") or m["rarity"]
    m["name"] = m["name"] or d.get("name") or ""
    m["subtypes"] = [x for x in d.get("subtypes") or [] if isinstance(x, str)]
    m["types"] = energy(d.get("types"))
    m["artist"] = d.get("artist") or ""
    if not m["number"] and d.get("number"):
        m["number"] = f"{d['number']}/{m['printed']}" if m["printed"] else str(d["number"])
    txt = {
        "supertype": d.get("supertype") or "",
        "hp": str(d.get("hp") or ""),
        "evolves": d.get("evolvesFrom") or "",
        "abilities": [{"name": a.get("name") or "", "type": a.get("type") or "Ability", "text": a.get("text") or ""}
                      for a in d.get("abilities") or [] if isinstance(a, dict)],
        "attacks": [{"name": a.get("name") or "", "cost": energy(a.get("cost")), "damage": a.get("damage") or "",
                     "text": a.get("text") or ""} for a in d.get("attacks") or [] if isinstance(a, dict)],
        "weak": [{"type": w.get("type") or "", "value": w.get("value") or ""} for w in d.get("weaknesses") or [] if isinstance(w, dict)],
        "resist": [{"type": w.get("type") or "", "value": w.get("value") or ""} for w in d.get("resistances") or [] if isinstance(w, dict)],
        "retreat": len(energy(d.get("retreatCost"))),
        "rules": [r for r in d.get("rules") or [] if isinstance(r, str) and r.strip()],
        "flavor": d.get("flavorText") or "",
    }
    m["text"] = {k: v for k, v in txt.items() if v or k in ("retreat", "supertype")}
    return m


def pack_info(pid, n_active_packs):
    p = load_pack_json(pid, quiet=False)
    if p is None:
        return None
    if isinstance(p.get("cards"), dict):
        return card_pack_info(pid, p, n_active_packs)
    tiers = p["tiers"]
    foil = float(p.get("foil_chance", 0))
    total = sum(int(w) for t in tiers[1:] for w in (t.get("skins") or {}).values())
    n = len(p["characters"])
    out_tiers = []
    for i, t in enumerate(tiers):
        skins = t.get("skins") or {}
        w = sum(int(x) for x in skins.values())
        pr = (1 - foil) if i == 0 else (foil * w / total if total else 0)
        frame = t.get("frame")
        if isinstance(frame, dict):
            fr = {"style": frame.get("style"), "palette": frame.get("palette"),
                  "colors": WANTED_PALETTES.get(frame.get("palette"), WANTED_PALETTES["common"])}
        else:
            name = frame or ("gold" if t["id"] == "secret-rare" else "plain")
            fr = {"style": "card", "preset": name, "colors": FRAME_PRESETS.get(name, FRAME_PRESETS["plain"])}
        out_tiers.append({
            "id": t["id"], "label": t["label"], "art": t["art"], "frame": fr,
            "odds": pr,                                 # per pull of this pack
            "card_odds": pr / n if n else 0,            # this exact character in this tier
            "skins": [{"id": s, "weight": int(wt), "odds": foil * int(wt) / total if total else 0}
                      for s, wt in skins.items()],
        })
    chars = []
    for i, c in enumerate(p["characters"]):
        chars.append({
            "id": c, "no": i + 1,
            "name": (p.get("names") or {}).get(c) or c.replace("-", " ").title(),
            "tag": (p.get("tags") or {}).get(c, ""),
            "poster": (p.get("poster_names") or {}).get(c),
            "bounty": (p.get("bounties") or {}).get(c),
        })
    return {
        "id": pid, "name": p.get("name", pid), "about": p.get("about"),
        "foil_chance": foil, "shiny_chance": float(p.get("shiny_chance", 0)),
        "layout": "dex" if n > 60 else "grid",
        "tiers": out_tiers, "characters": chars,
        "active_packs": n_active_packs,
    }


# ---------------------------------------------------------------- art
def grid_from_json(d, variant, shiny):
    v = d["variants"][variant]
    pal = dict(d.get("palette") or {})
    pal.update(v.get("palette") or {})
    if shiny:
        pal.update(d.get("shiny") or {})
        pal.update(v.get("shiny") or {})
    return [[hex_rgb(pal[ch]) if ch != "." else None for ch in row] for row in v["rows"]]


def has_shiny(d, variant):
    return bool(d.get("shiny") or d["variants"][variant].get("shiny"))


def save_grid(grid, path):
    h, w = len(grid), len(grid[0])
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()
    for y, row in enumerate(grid):
        for x, c in enumerate(row):
            if c is not None:
                px[x, y] = (*c, 255)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    im.save(tmp, format="PNG", optimize=True)
    os.replace(tmp, path)
    return w, h


def tint_of(grid):
    """a representative, saturated body color of the art: the art window's backdrop tint"""
    import colorsys
    buckets = {}
    for row in grid:
        for c in row:
            if c is None:
                continue
            hh, ll, ss = colorsys.rgb_to_hls(*(v / 255 for v in c))
            if ss < 0.25 or ll < 0.2 or ll > 0.85:
                continue
            k = int(hh * 12) % 12
            buckets.setdefault(k, []).append(c)
    if not buckets:
        return "#9aa4b0"
    best = max(buckets.values(), key=len)
    r, g, b = (sum(c[i] for c in best) / len(best) for i in range(3))
    return "#%02x%02x%02x" % (int(r), int(g), int(b))


def art_json_path(pack, char):
    for base in (ROOT / "packs" / pack / "art", OPSHELL / "packs" / pack / "art"):
        f = base / f"{char}.json"
        if f.exists():
            return f
    return None


class ArtCache:
    """decoded art, cached by source file: img/.cache.json maps each PNG (relative to img/) to the source it was
    made from (path, mtime, size) plus its pixel size and tint. A PNG whose source is unchanged isn't decoded again.
    kept collects every PNG this export uses; prune() removes the rest (retired / renamed cards, old shiny forms).
    Each entry also keeps the art's transparent share ("clear"): a card's plain sprite has one, a scene none."""
    VERSION = 3

    def __init__(self, img, do_art):
        self.img, self.do_art, self.kept = img, do_art, set()
        self.decoded = self.reused = 0
        self.file = img / ".cache.json"
        try:
            d = json.loads(read_text(self.file))
            ok = d.get("v") == self.VERSION
        except (OSError, ValueError, AttributeError):
            d, ok = {}, False
        self.entries = d.get("entries", {}) if ok else {}
        self.extra = d.get("extra", {}) if ok else {}

    @staticmethod
    def stamp(src):
        st = src.stat()
        return [str(src), st.st_mtime_ns, st.st_size]

    def get(self, rel, src, decode, also=None):
        """(size [w, h] or None, tint or None) of the PNG img/<rel> made from src (and `also`, a second source it
        depends on) by decode() -> pixel grid. --no-art: nothing is decoded or written; a cached entry still gives the
        size and tint."""
        ov = OVERRIDE / rel
        stamp = self.stamp(src) + (self.stamp(also) if also else [])
        if ov.exists():
            stamp[0] += "|" + str(ov)
            stamp[1] = max(stamp[1], ov.stat().st_mtime_ns)
        e = self.entries.get(rel)
        dst = self.img / rel
        if e and e.get("src") == stamp and (not self.do_art or dst.exists()):
            self.kept.add(rel)
            self.reused += 1
            return e["size"], e["tint"]
        if not self.do_art:
            return (e or {}).get("size"), (e or {}).get("tint")
        grid = decode()
        self.decoded += 1
        tint = tint_of(grid)
        n = sum(len(r) for r in grid)
        clear = round(sum(1 for r in grid for x in r if x is None) / n, 3) if n else 0
        if ov.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            write_atomic(dst, ov.read_bytes())
            with Image.open(dst) as im:
                size = list(im.size)
        else:
            size = list(save_grid(grid, dst))
        self.entries[rel] = {"src": stamp, "size": size, "tint": tint, "clear": clear}
        self.kept.add(rel)
        return size, tint

    def clear(self, rel):
        """the transparent share of img/<rel>'s art (None when it isn't known)"""
        return (self.entries.get(rel) or {}).get("clear")

    def save(self):
        if not self.do_art:
            return
        live = {k: v for k, v in self.entries.items() if k in self.kept}
        write_atomic(self.file, json.dumps({"v": self.VERSION, "entries": live, "extra": self.extra}, separators=(",", ":")))

    def prune(self, keep_also=()):
        """remove PNGs no card uses any more (and folders left empty); only after a full art export"""
        if not self.do_art or not self.img.exists():
            return 0
        keep = self.kept | set(keep_also)
        n = 0
        for f in list(self.img.rglob("*.png")):
            rel = f.relative_to(self.img).as_posix()
            if rel not in keep:
                f.unlink()
                n += 1
        for d in sorted((p for p in self.img.rglob("*") if p.is_dir()), key=lambda p: -len(p.parts)):
            try:
                d.rmdir()                                  # only succeeds when empty
            except OSError:
                pass
        return n


def sprite_layer(a, b):
    """a scene card's sprite layer from its normal and shiny art (pixel grids): the pixels that differ, grown twice into
    the dark pixels touching them (8 neighbours: the outline and eyes, the same in both), with enclosed holes filled.
    None when they don't line up or too little differs (the app's art::sprite_layer)"""
    h, w = len(a), len(a[0]) if a else 0
    if not w or len(b) != h or any(len(r) != w for r in b) or any(len(r) != w for r in a):
        return None
    m = [[a[y][x] is not None and a[y][x] != b[y][x] for x in range(w)] for y in range(h)]
    if sum(map(sum, m)) * 100 < w * h:
        return None
    dark = lambda c: c is not None and (0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]) / 255 < 0.16
    for _ in range(2):
        prev = [r[:] for r in m]
        for y in range(h):
            for x in range(w):
                if not prev[y][x] and dark(a[y][x]) and any(prev[yy][xx] for yy in range(max(0, y - 1), min(h, y + 2)) for xx in range(max(0, x - 1), min(w, x + 2))):
                    m[y][x] = True
    out = [[False] * w for _ in range(h)]
    stack = [(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)]
    while stack:
        x, y = stack.pop()
        if out[y][x] or m[y][x]:
            continue
        out[y][x] = True
        stack += [(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if 0 <= x + dx < w and 0 <= y + dy < h]
    return [[None if out[y][x] else (0, 0, 0) for x in range(w)] for y in range(h)]


SPRITE_CLEAR = 0.1   # a card art with at least this share of transparent pixels is a plain sprite (a scene has none)


def sprite_source(ch):
    """the character's plain colorscripts sprite in this checkout (vendor/ or $POKESHELL_VENDOR, else the pokedex
    pack's art), or None"""
    vendor = Path(os.environ["POKESHELL_VENDOR"]) if os.environ.get("POKESHELL_VENDOR") else ROOT / "vendor"
    for f in (vendor / "pokemon-colorscripts" / "colorscripts" / "large" / "regular" / ch, ROOT / "dist" / "pokedex" / f"{ch}-common.ans"):
        if f.is_file():
            return f
    return None


def export_art(packs, pulls, cache):
    """returns {pack: {char: {"tint": .., "img": {"tier[-shiny]" or "card id[-shiny]": [w,h] or None}}}}, per-card
    tints {pack: {card id: tint}} and the pokedex atlas info"""
    art, card_tints = {}, {}
    atlas = None
    shiny_pulled = {(p["pack"], p["card"] or p["char"], p["tier"]) for p in pulls if p["shiny"]}
    for pk in packs:
        pid = pk["id"]
        art[pid] = {}
        if pk["layout"] == "dex":
            sys.path.insert(0, str(ROOT / "packs" / "pokedex"))
            import build as dexbuild                              # parse() / trim() of the colorscripts
            dex = ROOT / "dist" / "pokedex"
            parse = lambda f: dexbuild.trim(dexbuild.parse(f.read_text(encoding="utf-8", errors="replace")))
            pulled = {}
            for p in pulls:
                if p["pack"] == pid:
                    pulled.setdefault(p["char"], set()).add((p["tier"], p["shiny"]))
            # the silhouette atlas (every sprite) is rebuilt only when a sprite changed; tints come from the cache
            srcs = [dex / f"{ch['id']}-common.ans" for ch in pk["characters"]]
            sig = [[s.name, *ArtCache.stamp(s)[1:]] if s.exists() else [s.name] for s in srcs]
            meta = cache.extra.get("dex") or {}
            atlas_file = cache.img / pid / "_silhouettes.png"
            if meta.get("sig") == sig and (atlas_file.exists() or not cache.do_art):
                tints, cell, cols, rows = meta["tints"], meta["cell"], meta["cols"], meta["rows"]
            elif cache.do_art:
                sils = [parse(s) if s.exists() else [[None]] for s in srcs]
                tints = [tint_of(g) for g in sils]
                cw, chh = max(len(g[0]) for g in sils), max(len(g) for g in sils)
                cols = 32
                rows = (len(sils) + cols - 1) // cols
                im = Image.new("LA", (cols * cw, rows * chh), (0, 0))
                px = im.load()
                for i, g in enumerate(sils):
                    ox = (i % cols) * cw + (cw - len(g[0])) // 2
                    oy = (i // cols) * chh + (chh - len(g))
                    for y, row in enumerate(g):
                        for x, c in enumerate(row):
                            if c is not None:
                                px[ox + x, oy + y] = (0, 255)
                atlas_file.parent.mkdir(parents=True, exist_ok=True)
                tmp = atlas_file.with_name(f".{atlas_file.name}.{os.getpid()}.tmp")
                im.save(tmp, format="PNG", optimize=True)
                os.replace(tmp, atlas_file)
                cell = [cw, chh]
                cache.extra["dex"] = {"sig": sig, "tints": tints, "cell": cell, "cols": cols, "rows": rows}
            else:
                tints, cell = None, None                  # --no-art on a first run: no atlas, default tints
            if cell:
                atlas = {"file": f"img/{pid}/_silhouettes.png", "cell": cell, "cols": cols, "rows": rows}
                cache.kept.add(f"{pid}/_silhouettes.png")
            for i, ch in enumerate(pk["characters"]):
                c = ch["id"]
                entry = {"tint": tints[i] if tints else "#9aa4b0", "img": {}}
                for tier, shiny in sorted(pulled.get(c, ())):
                    src = dex / f"{c}-common{'-shiny' if shiny else ''}.ans"
                    if not src.exists():
                        src = dex / f"{c}-common.ans"
                    if not src.exists():
                        continue
                    key = f"{tier}{'-shiny' if shiny else ''}"
                    entry["img"][key], _ = cache.get(f"{pid}/{c}/{key}.png", src, lambda s=src: parse(s))
                art[pid][c] = entry
            continue
        if pk.get("layout") == "cards":
            # real cards: one image per card, from its prebuilt art dist/<pack>/<character>-<card id>.ans converted
            # back to pixels; keyed by card id (img/<pack>/<character>/<card id>[-shiny].png). Every card's normal
            # form (a deep link or search can open any card), shiny forms only once pulled (caught or seen).
            card_tints[pid] = {}
            seen_cards = {p["card"] for p in pulls if p["pack"] == pid and p["status"] != "collected" and p["card"]}
            for ch in pk["characters"]:
                c = ch["id"]
                entry = {"tint": None, "img": {}}
                for card in pk["cards"]:
                    if card["character"] != c:
                        continue
                    cid = card["id"]
                    for shiny in (False, True):
                        if shiny and (pid, cid, card["tier"]) not in shiny_pulled:
                            continue
                        src = ROOT / "dist" / pid / f"{c}-{cid}{'-shiny' if shiny else ''}.ans"
                        if not src.exists():
                            continue
                        key = f"{cid}{'-shiny' if shiny else ''}"
                        size, tint = cache.get(f"{pid}/{c}/{key}.png", src,
                                               lambda s=src: ansi_grid(s.read_text(encoding="utf-8", errors="replace")))
                        entry["img"][key] = size
                        if not shiny and tint:
                            card_tints[pid][cid] = tint
                            entry["tint"] = entry["tint"] or tint
                entry["tint"] = entry["tint"] or "#9aa4b0"
                # a seen card's silhouette (the module doc). A card whose art has transparent pixels is the plain
                # sprite (a common; a scene is full-bleed): its own image is its shape, and a scene card of the same
                # character takes it; else the colorscripts sprite; else the scene card's own sprite layer
                mine = [cd for cd in pk["cards"] if cd["character"] == c]
                for cd in mine:
                    if (cache.clear(f"{pid}/{c}/{cd['id']}.png") or 0) >= SPRITE_CLEAR:
                        cd["sprite"] = True
                scenes = [cd for cd in mine if cd["id"] in seen_cards and not cd.get("sprite")]
                if scenes:
                    common = next((cd["id"] for cd in mine if cd.get("sprite")), None)
                    src = None if common else sprite_source(c)
                    if common:
                        entry["seen"] = common
                    elif src:
                        size, _ = cache.get(f"{pid}/{c}/_seen.png", src, lambda s=src: ansi_grid(s.read_text(encoding="utf-8", errors="replace")))
                        if size:
                            entry["img"]["_seen"] = size
                            entry["seen"] = "_seen"
                    else:
                        for cd in scenes:
                            a, b = (ROOT / "dist" / pid / f"{c}-{cd['id']}{x}.ans" for x in ("", "-shiny"))
                            if not (a.exists() and b.exists()):
                                continue
                            dec = lambda a=a, b=b: sprite_layer(*(ansi_grid(f.read_text(encoding="utf-8", errors="replace")) for f in (a, b))) or [[None]]
                            size, _ = cache.get(f"{pid}/{c}/{cd['id']}-seen.png", a, dec, also=b)
                            if size and size != [1, 1]:
                                entry["img"][f"{cd['id']}-seen"] = size
                                cd["seen"] = f"{cd['id']}-seen"
                art[pid][c] = entry
            continue
        for ch in pk["characters"]:
            c = ch["id"]
            f = art_json_path(pid, c)
            entry = {"tint": "#9aa4b0", "img": {}}
            if f is None:
                print(f"warning: no art for {pid}/{c}", file=sys.stderr)
                art[pid][c] = entry
                continue
            d = json.loads(read_text(f))
            for i, t in enumerate(pk["tiers"]):
                v = t["art"]
                if v not in d["variants"]:
                    continue
                for shiny in ([False, True] if has_shiny(d, v) and pk["shiny_chance"] > 0 else [False]):
                    key = f"{t['id']}{'-shiny' if shiny else ''}"
                    size, tint = cache.get(f"{pid}/{c}/{key}.png", f, lambda v=v, s=shiny: grid_from_json(d, v, s))
                    entry["img"][key] = size
                    if i == 0 and not shiny and tint:
                        entry["tint"] = tint
            art[pid][c] = entry
    return art, card_tints, atlas


# ---------------------------------------------------------------- main
def main():
    global ROOT, OPSHELL, IMG
    import time
    t0 = time.perf_counter()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--state", default=None, help="the state folder (default: $POKESHELL_HOME, else %%LOCALAPPDATA%%/pokeshell)")
    ap.add_argument("--log", default=None, help="pulls.log (default: <state>/pulls.log)")
    ap.add_argument("--root", default=None, help="the pokeshell checkout (default: this file's)")
    ap.add_argument("--out", default=None, help="where the page goes (default: <state>/web)")
    ap.add_argument("--owner", default=os.environ.get("POKESHELL_OWNER") or os.environ.get("USERNAME", "you"), help="name on the cover label")
    ap.add_argument("--no-art", action="store_true", help="don't decode or write any art (sizes and tints come from the cache when there is one)")
    a = ap.parse_args()

    state = Path(a.state) if a.state else state_dir()
    if a.root:
        ROOT = Path(a.root).resolve()
        OPSHELL = ROOT.parent / "opshell"
    out = Path(a.out) if a.out else state / "web"
    out.mkdir(parents=True, exist_ok=True)
    IMG = out / "img"
    log = Path(a.log) if a.log else state / "pulls.log"
    vf = log.parent / "viewed.txt"
    viewed = frozenset(l.strip() for l in read_text(vf).splitlines() if l.strip()) if vf.exists() else frozenset()
    bad = [0]
    pulls, hidden, real_since = resolve_pulls(read_pulls(log, viewed, bad=bad))
    if bad[0]:
        print(f"warning: {bad[0]} lines of {log.name} couldn't be read (not UTF-8, or a bad time) and were skipped", file=sys.stderr)
    cfg = {}
    cfg_file = log.parent / "config.txt"
    if cfg_file.exists():
        for line in read_text(cfg_file).splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip()
    pack_ids = [p for p in PACK_ORDER if (ROOT / "packs" / p / "pack.json").exists()]
    pack_ids += sorted(p.name for p in (ROOT / "packs").iterdir()
                       if p.is_dir() and (p / "pack.json").exists() and p.name not in pack_ids)
    n_active = len(pack_ids) if cfg.get("pack", "all") == "all" else 1
    packs = [pk for pk in (pack_info(p, n_active) for p in pack_ids) if pk]

    skins = {}
    for pk in packs:
        for t in pk["tiers"]:
            for s in t["skins"]:
                if s["id"] in skins:
                    continue
                title, desc = skin_blurb(ROOT / "packs" / pk["id"] / "shaders" / f"{s['id']}.hlsl")
                skins[s["id"]] = {"title": title or s["id"].replace("-", " ").title(), "desc": desc}

    cache = ArtCache(IMG, not a.no_art)
    art, card_tints, atlas = export_art(packs, pulls, cache)
    for pk in packs:
        for ch in pk["characters"]:
            e = art.get(pk["id"], {}).get(ch["id"], {})
            ch["tint"] = e.get("tint")
            ch["img"] = e.get("img", {})
            if e.get("seen"):
                ch["seen"] = e["seen"]          # a seen card's silhouette: this image key (the module doc)
        for c in pk.get("cards") or []:
            c["tint"] = card_tints.get(pk["id"], {}).get(c["id"])
        if pk["layout"] == "dex":
            pk["atlas"] = atlas
    cache.save()
    pruned = cache.prune()

    # slots (the page's: a real card, a character in a tier, or a pokedex character), caught vs only seen
    layout = {pk["id"]: pk["layout"] for pk in packs}
    slot = lambda p: (p["pack"], p["card"] if layout.get(p["pack"]) == "cards" else p["char"], None if layout.get(p["pack"]) in ("cards", "dex") else p["tier"])
    caught_slots = {slot(p) for p in pulls if p["status"] == "collected"}
    seen_slots = {slot(p) for p in pulls} - caught_slots
    # the text half (HP, abilities, attacks ...) is for caught cards only (docs/BINDER_SPEC.md "Empty, seen, caught"):
    # an empty or seen card's text isn't even in data.json, so neither the page nor its search can show it; nor is its
    # printed card's scan (the `p` toggle)
    for pk in packs:
        for c in pk.get("cards") or []:
            if (pk["id"], c["id"], None) not in caught_slots:
                c.pop("text", None)
                c.pop("scan", None)
            elif not c.get("scan"):
                c.pop("scan", None)
    data = {
        "owner": a.owner,
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "source": {"log": str(log).replace(os.environ.get("USERPROFILE", "~"), "~"), "pack_setting": cfg.get("pack", "all")},
        "earned": {"enforced": True,
                   "note": "A card is caught once you use the tab it was pulled in: its first command earns it "
                           "(docs/BINDER_SPEC.md). Until then (or if the tab closed unused) it is only seen: its silhouette."},
        # what the header counts: caught pulls and cards; seen cards (pulled, never caught) apart, never counted
        "counts": {"pulls": sum(1 for p in pulls if p["status"] == "collected"),
                   "caught": len(caught_slots),
                   "seen": len(seen_slots),
                   "shiny": sum(1 for p in pulls if p["status"] == "collected" and p["shiny"]),
                   "new": sum(1 for p in pulls if p["new"])},
        "hidden": hidden,   # pulls that no longer resolve to a current built card (retired art, unbuilt; still in pulls.log)
        "bad_lines": bad[0],   # pulls.log lines that couldn't be read (skipped)
        "best_since": best_since(cfg.get("best_since"), real_since),   # best pulls start here (local ISO time); None: all
        "packs": packs, "skins": skins, "pulls": pulls,
    }
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    write_atomic(out / "data.json", blob)

    # bake: index.html with the data inlined
    page = PAGE.read_text(encoding="utf-8")
    marker = "/*__INLINE_DATA__*/null"
    if marker not in page:
        raise SystemExit("index.html has no inline-data marker")
    write_atomic(out / "binder.html", page.replace(marker, blob.replace("</", "<\\/"), 1))

    n_img = len(cache.kept)
    n_got = sum(1 for p in pulls if p["status"] == "collected")
    n_new = sum(1 for p in pulls if p["new"])
    art_note = (f"{n_img} images ({cache.decoded} decoded, {cache.reused} cached{f', {pruned} stale removed' if pruned else ''})"
                if not a.no_art else "art skipped (--no-art)")
    print(f"{n_got} pulls caught ({len(caught_slots)} cards), {len(seen_slots)} seen, {n_new} new{f', {hidden} retired (not shown)' if hidden else ''}; "
          f"{len(packs)} packs, {len(skins)} skins, {art_note} -> {out} ({time.perf_counter() - t0:.1f} s)")


if __name__ == "__main__":
    main()
