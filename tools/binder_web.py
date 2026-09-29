"""Export the pokeshell web binder: pulls.log + pack.json -> data.json, art PNGs, and a baked single-file page.
`pokeshell binder --web` runs this (then opens the page); nothing stays running.

  python tools/binder_web.py                          # everything, into <state>/web
  python tools/binder_web.py --no-art                 # data.json + binder.html only (fast)
  python tools/binder_web.py --state <dir> --out <dir> --root <checkout>

Reads
  <state>/pulls.log                       TSV: time, pack, character, tier, art, skin, shiny(0/1), flags, [key=value...]
  <state>/viewed.txt                      pull ids the binder has shown (no NEW sticker)
  packs/<pack>/pack.json                  characters, names, tags, tiers, skins + weights, odds (+ cards, retired)
  packs/<pack>/art/<id>.json              pixel grids (pokemon, onepiece; onepiece falls back to ../opshell)
  dist/pokedex/<id>-common[-shiny].ans    pokedex sprites (half-block ANSI -> pixels)
  packs/<pack>/shaders/<skin>.hlsl        the header comment becomes the skin's description
<state> is $POKESHELL_HOME, else %LOCALAPPDATA%/pokeshell.

Writes (into --out, default <state>/web)
  data.json                               everything the page needs
  img/<pack>/<character>/<tier>[-shiny].png   one PNG per character / tier / shiny, 1 px per art pixel
  img/pokedex/_silhouettes.png            atlas of all 905 pokedex silhouettes (alpha only), for empty slots
  binder.html                             tools/binder-web/index.html with data.json inlined (with the img/ folder)

Swapping art: drop a PNG into tools/binder-web/art-override/<pack>/<character>/<tier>[-shiny].png and it is copied
instead of rendered.

The earned rule (docs/BINDER_SPEC.md, the same as Pokeshell.cs ReadPulls): a pull line with an id and the
"pending" flag is pending until an `earned:<id>` line; it expires on an `expired:<id>` line, after 24 h, or when its
boot session (boot=) is over. Pending pulls export as status "pending" (shown greyed, not counted); expired ones are
dropped; earned ones are "collected", with "new" when viewed.txt doesn't list them. Lines without an id are earned.
Pulls that don't resolve to a current card (unknown or `retired` in pack.json) are left out; pulls.log is never
rewritten.
"""
import argparse
import datetime as dt
import json
import os
import re
import shutil
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


# ---------------------------------------------------------------- pulls
def read_pulls(log, viewed=frozenset(), now=None, boot=None):
    """pulls.log with the earned rule applied (see the module doc)"""
    import time
    now = time.time() if now is None else now
    boot = boot_id() if boot is None else boot
    pulls = []
    if not log.exists():
        print(f"warning: no pulls log at {log}", file=sys.stderr)
        return pulls
    lines = log.read_text(encoding="utf-8-sig").splitlines()
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
            continue
        else:
            t = ulid_secs(pid)
            if (t is not None and now - t > EXPIRE_SECS) or (pboot and boot and abs(pboot - boot) > BOOT_SLACK_SECS):
                continue                            # expired: the tab was never used
            status = "pending"
        pulls.append({
            "id": n + 1, "pull": pid or None, "card": card or None,
            "time": f[0], "pack": f[1], "char": f[2], "tier": f[3], "art": f[4],
            "skin": f[5] or None, "shiny": f[6].strip() == "1",
            "flags": [x for x in re.split(r"[,; ]+", flags) if x],
            "status": status,
            "new": status == "collected" and bool(pid) and pid not in viewed,
        })
    return pulls


def load_pack_json(pid):
    f = ROOT / "packs" / pid / "pack.json"
    return json.loads(f.read_text(encoding="utf-8-sig")) if f.exists() else None


def resolve_pull(pk, char, tier, art, card=None):
    """what a pull shows today: (character, tier id, card id or None), or None to hide it. The rule of
    Resolve-PokeshellPull (scripts/lib/common.ps1, docs/PACK_FORMAT.md "retired"):
      packs without "cards": as logged (tier by id, or by label);
      real-card packs: the art column (or a card= column) is a card id of the pack whose character matches ->
      that card; else retired["<character>/<tier>"] names a card -> that card; else hidden"""
    cards = pk.get("cards")
    if not isinstance(cards, dict):
        tiers = pk.get("tiers") or []
        ids = [t["id"] for t in tiers]
        t = tier if tier in ids else next((x["id"] for x in tiers if x.get("label", "").lower() == tier.lower()), None)
        return (char, t, None) if t and char in (pk.get("characters") or []) else None
    for cid in (card, art):
        c = cards.get(cid) if cid else None
        if c and c.get("character") == char:
            return char, c["tier"], cid
    retired = pk.get("retired") or {}
    now = retired.get(f"{char}/{tier}") if isinstance(retired, dict) else None
    c = cards.get(now) if now else None
    return (c["character"], c["tier"], now) if c else None


def resolve_pulls(pulls):
    """each pull as the card it shows today; the ones that don't resolve (retired art) are left out and counted"""
    out, hidden, cache = [], 0, {}
    for p in pulls:
        if p["pack"] not in cache:
            cache[p["pack"]] = load_pack_json(p["pack"])
        pk = cache[p["pack"]]
        r = resolve_pull(pk, p["char"], p["tier"], p["art"], p["card"]) if pk else None
        if not r:
            hidden += 1
            continue
        char, tier, card = r
        out.append({**p, "char": char, "tier": tier, "card": card or p["card"]})
    return out, hidden


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


def card_pack_info(pid, p, n_active_packs):
    """a real-card pack (pack.json "cards", docs/PACK_FORMAT.md): characters come from the cards, the tiers shown are
    the rarities that have cards, a tier's odds are its weight among those"""
    cards = p["cards"]
    live = [t for t in p["tiers"] if any(c.get("tier") == t["id"] for c in cards.values())]
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
                          "odds": pr, "card_odds": pr / n if n else 0,
                          "skins": [{"id": s, "weight": int(w), "odds": pr * int(w) / sw} for s, w in skins.items()]})
    order = []
    for c in cards.values():
        if c.get("character") and c["character"] not in order:
            order.append(c["character"])
    chars = [{"id": ch, "no": i + 1, "name": (p.get("names") or {}).get(ch) or ch.replace("-", " ").title(),
              "tag": "", "poster": None, "bounty": None} for i, ch in enumerate(order)]
    return {"id": pid, "name": p.get("name", pid), "about": p.get("about"), "foil_chance": 0,
            "shiny_chance": float(p.get("shiny_chance", 0)), "layout": "grid", "tiers": out_tiers,
            "characters": chars, "active_packs": n_active_packs,
            "cards": {cid: {k: c.get(k) for k in ("character", "tier", "name", "number", "rarity", "set")} for cid, c in cards.items()}}


def pack_info(pid, n_active_packs):
    p = json.loads((ROOT / "packs" / pid / "pack.json").read_text(encoding="utf-8-sig"))
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
    im.save(path, optimize=True)
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


def out_path(pack, char, tier, shiny):
    return IMG / pack / char / f"{tier}{'-shiny' if shiny else ''}.png"


def place(pack, char, tier, shiny, grid):
    """write one card image (or copy the override); returns [w, h] of the file"""
    rel = Path(pack) / char / f"{tier}{'-shiny' if shiny else ''}.png"
    ov = OVERRIDE / rel
    dst = IMG / rel
    if ov.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ov, dst)
        with Image.open(dst) as im:
            return list(im.size)
    return list(save_grid(grid, dst))


def art_json_path(pack, char):
    for base in (ROOT / "packs" / pack / "art", OPSHELL / "packs" / pack / "art"):
        f = base / f"{char}.json"
        if f.exists():
            return f
    return None


def export_art(packs, pulls, do_art):
    """returns {pack: {char: {"tint": .., "img": {"tier[-shiny]": [w,h]}}}} and the pokedex atlas info"""
    art = {}
    atlas = None
    for pk in packs:
        pid = pk["id"]
        art[pid] = {}
        if pk["layout"] == "dex":
            sys.path.insert(0, str(ROOT / "packs" / "pokedex"))
            import build as dexbuild                              # parse() / trim() of the colorscripts
            pulled = {}
            for p in pulls:
                if p["pack"] == pid:
                    pulled.setdefault(p["char"], set()).add((p["tier"], p["shiny"]))
            sils = []
            for ch in pk["characters"]:
                c = ch["id"]
                src = ROOT / "dist" / "pokedex" / f"{c}-common.ans"
                grid = dexbuild.trim(dexbuild.parse(src.read_text(encoding="utf-8"))) if src.exists() else [[None]]
                sils.append(grid)
                entry = {"tint": tint_of(grid), "img": {}}
                for tier, shiny in sorted(pulled.get(c, ())):
                    g = grid
                    if shiny:
                        s2 = ROOT / "dist" / "pokedex" / f"{c}-common-shiny.ans"
                        if s2.exists():
                            g = dexbuild.trim(dexbuild.parse(s2.read_text(encoding="utf-8")))
                    key = f"{tier}{'-shiny' if shiny else ''}"
                    entry["img"][key] = place(pid, c, tier, shiny, g) if do_art else [len(g[0]), len(g)]
                art[pid][c] = entry
            # silhouette atlas: uniform cells, sprites centered on the bottom edge, alpha only
            cw = max(len(g[0]) for g in sils)
            chh = max(len(g) for g in sils)
            cols = 32
            rows = (len(sils) + cols - 1) // cols
            if do_art:
                im = Image.new("LA", (cols * cw, rows * chh), (0, 0))
                px = im.load()
                for i, g in enumerate(sils):
                    ox = (i % cols) * cw + (cw - len(g[0])) // 2
                    oy = (i // cols) * chh + (chh - len(g))
                    for y, row in enumerate(g):
                        for x, c in enumerate(row):
                            if c is not None:
                                px[ox + x, oy + y] = (0, 255)
                (IMG / pid).mkdir(parents=True, exist_ok=True)
                im.save(IMG / pid / "_silhouettes.png", optimize=True)
            atlas = {"file": f"img/{pid}/_silhouettes.png", "cell": [cw, chh], "cols": cols, "rows": rows}
            continue
        if pk.get("cards"):
            # real cards: each (character, tier) slot shows its card's prebuilt art, dist/<pack>/<character>-<card id>.ans
            # (the pulled card when there is one), converted back to pixels
            pulled = {(p["char"], p["tier"]): p["card"] for p in pulls if p["pack"] == pid and p.get("card")}
            for ch in pk["characters"]:
                c = ch["id"]
                entry = {"tint": "#9aa4b0", "img": {}}
                for t in pk["tiers"]:
                    ids = [cid for cid, x in pk["cards"].items() if x["character"] == c and x["tier"] == t["id"]]
                    if not ids:
                        continue
                    cid = pulled.get((c, t["id"])) if pulled.get((c, t["id"])) in ids else ids[0]
                    for shiny in ([False, True] if pk["shiny_chance"] > 0 else [False]):
                        src = ROOT / "dist" / pid / f"{c}-{cid}{'-shiny' if shiny else ''}.ans"
                        if not src.exists():
                            continue
                        g = ansi_grid(src.read_text(encoding="utf-8"))
                        if entry["tint"] == "#9aa4b0":
                            entry["tint"] = tint_of(g)
                        key = f"{t['id']}{'-shiny' if shiny else ''}"
                        entry["img"][key] = place(pid, c, t["id"], shiny, g) if do_art else [len(g[0]), len(g)]
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
            d = json.loads(f.read_text(encoding="utf-8"))
            entry["tint"] = tint_of(grid_from_json(d, "common", False)) if "common" in d["variants"] else "#9aa4b0"
            for t in pk["tiers"]:
                v = t["art"]
                if v not in d["variants"]:
                    continue
                for shiny in ([False, True] if has_shiny(d, v) and pk["shiny_chance"] > 0 else [False]):
                    g = grid_from_json(d, v, shiny)
                    key = f"{t['id']}{'-shiny' if shiny else ''}"
                    entry["img"][key] = place(pid, c, t["id"], shiny, g) if do_art else [len(g[0]), len(g)]
            art[pid][c] = entry
    return art, atlas


# ---------------------------------------------------------------- main
def main():
    global ROOT, OPSHELL, IMG
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--state", default=None, help="the state folder (default: $POKESHELL_HOME, else %%LOCALAPPDATA%%/pokeshell)")
    ap.add_argument("--log", default=None, help="pulls.log (default: <state>/pulls.log)")
    ap.add_argument("--root", default=None, help="the pokeshell checkout (default: this file's)")
    ap.add_argument("--out", default=None, help="where the page goes (default: <state>/web)")
    ap.add_argument("--owner", default=os.environ.get("POKESHELL_OWNER") or os.environ.get("USERNAME", "you"), help="name on the cover label")
    ap.add_argument("--no-art", action="store_true", help="skip writing PNGs (sizes still computed)")
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
    viewed = frozenset(l.strip() for l in vf.read_text(encoding="utf-8-sig").splitlines() if l.strip()) if vf.exists() else frozenset()
    pulls, hidden = resolve_pulls(read_pulls(log, viewed))
    cfg = {}
    cfg_file = log.parent / "config.txt"
    if cfg_file.exists():
        for line in cfg_file.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip()
    pack_ids = [p for p in PACK_ORDER if (ROOT / "packs" / p / "pack.json").exists()]
    pack_ids += sorted(p.name for p in (ROOT / "packs").iterdir()
                       if p.is_dir() and (p / "pack.json").exists() and p.name not in pack_ids)
    n_active = len(pack_ids) if cfg.get("pack", "all") == "all" else 1
    packs = [pack_info(p, n_active) for p in pack_ids]

    skins = {}
    for pk in packs:
        for t in pk["tiers"]:
            for s in t["skins"]:
                if s["id"] in skins:
                    continue
                title, desc = skin_blurb(ROOT / "packs" / pk["id"] / "shaders" / f"{s['id']}.hlsl")
                skins[s["id"]] = {"title": title or s["id"].replace("-", " ").title(), "desc": desc}

    art, atlas = export_art(packs, pulls, not a.no_art)
    for pk in packs:
        for ch in pk["characters"]:
            e = art.get(pk["id"], {}).get(ch["id"], {})
            ch["tint"] = e.get("tint")
            ch["img"] = e.get("img", {})
        if pk["layout"] == "dex":
            pk["atlas"] = atlas

    data = {
        "owner": a.owner,
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "source": {"log": str(log).replace(os.environ.get("USERPROFILE", "~"), "~"), "pack_setting": cfg.get("pack", "all")},
        "earned": {"enforced": True,
                   "note": "A card only counts once you use the tab it was pulled in: its first command earns it "
                           "(docs/BINDER_SPEC.md). Pending cards show greyed until then."},
        "hidden": hidden,   # pulls of retired art that no longer resolve to a current card (not shown; still in pulls.log)
        "packs": packs, "skins": skins, "pulls": pulls,
    }
    (out / "data.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    # bake: index.html with the data inlined
    page = PAGE.read_text(encoding="utf-8")
    marker = "/*__INLINE_DATA__*/null"
    if marker not in page:
        raise SystemExit("index.html has no inline-data marker")
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    (out / "binder.html").write_text(page.replace(marker, blob, 1), encoding="utf-8")

    n_img = sum(1 for _ in IMG.rglob("*.png")) if IMG.exists() else 0
    n_pend = sum(1 for p in pulls if p["status"] == "pending")
    n_new = sum(1 for p in pulls if p["new"])
    print(f"{len(pulls) - n_pend} earned, {n_pend} pending, {n_new} new{f', {hidden} retired (not shown)' if hidden else ''}; "
          f"{len(packs)} packs, {len(skins)} skins, {n_img} images -> {out}")


if __name__ == "__main__":
    main()
