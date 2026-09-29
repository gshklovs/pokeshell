r"""The card's text half ("bottom half", docs/CARD_FORMAT.md) as terminal text: exactly the art's width, boxed in
the rarity's frame colour, rows = header / abilities / attacks / rules / footer. Energy costs and type glyphs
are one-cell `●` in the type colour (no emoji: they are two cells wide).

  ..\..\.venv\Scripts\python bottom.py cards\swsh7-215.json 84     -> prints it
"""
import json
import sys
import textwrap
import unicodedata

ESC = "\x1b"
TYPE_COL = {"Grass": "#5fbf4a", "Fire": "#f0603a", "Water": "#3fa9f0", "Lightning": "#f6d02c", "Psychic": "#b56ae0",
            "Fighting": "#c8743c", "Darkness": "#4f8596", "Metal": "#a9b3bd", "Fairy": "#f283c4", "Dragon": "#c9a53c",
            "Colorless": "#e6e6e6"}
# frame colour per printed rarity (the tier is the printed rarity); "rainbow" = a hue sweep around the box
RARITY_FRAME = {"Common": "#9aa0aa", "Uncommon": "#8fc4a8", "Rare": "#6ea5ff", "Reverse Holo": "#b9d7eb",
                "Rare Holo": "#56d0e0", "Rare Holo V": "#c9d1da", "Rare Holo VMAX": "#8f9cff", "Rare Ultra": "#e178e6",
                "Rare Rainbow": "rainbow", "Rare Secret": "#f0c850"}
RARITY_SYM = {"Common": "●", "Uncommon": "◆"}
TEXT = "#e8e6e1"
DIM = "#9d9a94"
LABEL = "#c9c4ba"


def hexrgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def mix(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def hue(t):
    from colorsys import hsv_to_rgb
    r, g, b = hsv_to_rgb(t % 1, 0.5, 1.0)
    return (round(r * 255), round(g * 255), round(b * 255))


def cw(s):
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 0 if unicodedata.combining(ch) else 1 for ch in s)


class Line:
    """a row of styled segments: (text, fg rgb, bold)"""

    def __init__(self):
        self.segs = []

    def add(self, text, fg=TEXT, bold=False):
        self.segs.append((text, hexrgb(fg) if isinstance(fg, str) else fg, bold))
        return self

    def width(self):
        return sum(cw(t) for t, _, _ in self.segs)

    def right(self, total, segs):
        """pad so that `segs` end flush right in `total` cells"""
        w = sum(cw(t) for t, _, _ in segs)
        pad = total - self.width() - w
        self.add(" " * max(1, pad))
        for t, f, b in segs:
            self.add(t, f, b)
        return self


def energy(types):
    return [("●", hexrgb(TYPE_COL.get(t, "#e6e6e6")), False) for t in types]


def wrap(text, width, indent=0):
    return textwrap.wrap(text, width=width - indent, break_long_words=True) or [""]


def lines_for(card, inner):
    out = []
    subs = card.get("subtypes", [])
    badge = next((s for s in ("VMAX", "VSTAR", "V", "ex", "EX", "GX") if s in subs), None)
    stage = next((s for s in subs if s in ("Basic", "Stage 1", "Stage 2", "VMAX", "VSTAR", "BREAK")), "")
    tcol = TYPE_COL.get((card.get("types") or ["Colorless"])[0], "#e6e6e6")
    name = card["name"]
    if badge and name.endswith(" " + badge):
        name = name[: -len(badge) - 1]
    # header: name, badge, HP, type glyph
    hd = Line().add(name, "#ffffff", True)
    if badge:
        hd.add(" ").add(badge, tcol, True)
    right = [("HP ", DIM, False), (card.get("hp", ""), "#ffffff", True), (" ", TEXT, False)] + energy(card.get("types", []))
    right = [(t, hexrgb(f) if isinstance(f, str) else f, b) for t, f, b in right]
    out.append(hd.right(inner, right))
    sub = Line()
    if card.get("evolvesFrom"):
        if stage and stage != badge:
            sub.add(stage + "  ", DIM)
        sub.add("evolves from ", DIM).add(card["evolvesFrom"], LABEL)
    else:
        sub.add(stage, DIM)
    extra = [s for s in subs if s not in ("Basic", "Stage 1", "Stage 2", "V", "VMAX", "VSTAR", "ex", "EX", "GX")]
    if extra:
        sub.right(inner, [(" · ".join(extra), hexrgb(DIM), False)])
    out.append(sub)
    out.append("rule")
    # abilities
    for ab in card.get("abilities", []):
        out.append(Line().add(ab.get("type", "Ability"), "#ff6b5b", True).add("  ").add(ab["name"], "#ff9a8a", True))
        for t in wrap(ab.get("text", ""), inner, 2):
            out.append(Line().add("  " + t, TEXT))
        out.append("blank")
    # attacks
    for at in card.get("attacks", []):
        ln = Line()
        for t, f, b in energy(at.get("cost", [])) or [("·", hexrgb(DIM), False)]:
            ln.add(t, f, b)
        ln.add("  ").add(at["name"], "#ffffff", True)
        if at.get("damage"):
            ln.right(inner, [(at["damage"], hexrgb("#ffffff"), True)])
        out.append(ln)
        if at.get("text"):
            for t in wrap(at["text"], inner, 2):
                out.append(Line().add("  " + t, TEXT))
        out.append("blank")
    if out[-1] == "blank":
        out.pop()
    out.append("rule")
    # footer: weakness / resistance / retreat
    ft = Line().add("weak ", DIM)
    ws = card.get("weaknesses", [])
    if ws:
        for w in ws:
            ft.add("●", TYPE_COL.get(w["type"], "#e6e6e6")).add(w["value"], TEXT)
    else:
        ft.add("—", DIM)
    ft.add("   resist ", DIM)
    rs = card.get("resistances", [])
    if rs:
        for r in rs:
            ft.add("●", TYPE_COL.get(r["type"], "#e6e6e6")).add(r["value"], TEXT)
    else:
        ft.add("—", DIM)
    rc = card.get("retreatCost", [])
    ft.right(inner, [("retreat ", hexrgb(DIM), False)] + (energy(rc) if rc else [("—", hexrgb(DIM), False)]))
    out.append(ft)
    for rule in card.get("rules", []):
        for t in wrap(rule, inner):
            out.append(Line().add(t, DIM))
    if card.get("flavorText"):
        for t in wrap(card["flavorText"], inner):
            out.append(Line().add(t, DIM))
    st = card["set"]
    n = card["number"]
    num = f"{int(n):03d}/{st['printedTotal']}" if n.isdigit() else f"{n}/{st['printedTotal']}"
    sym = RARITY_SYM.get(card.get("rarity", ""), "★")
    ln = Line().add(st["name"], LABEL).add(" ").add(num, TEXT).add(" ").add(sym, "#ffffff")
    ln.right(inner, [("illus. ", hexrgb(DIM), False), (card.get("artist", ""), hexrgb(LABEL), False)])
    if ln.width() > inner:                      # too long: artist on its own line
        out.append(Line().add(st["name"], LABEL).add(" ").add(num, TEXT).add(" ").add(sym, "#ffffff")
                   .right(inner, [(card.get("rarity", ""), hexrgb(DIM), False)]))
        out.append(Line().right(inner, [("illus. ", hexrgb(DIM), False), (card.get("artist", ""), hexrgb(LABEL), False)]))
    else:
        out.append(ln)
    return out


def render_text(card, width, frame=None, shiny=False):
    """-> ANSI text block, `width` cells wide"""
    frame = frame or RARITY_FRAME.get(card.get("tier", ""), RARITY_FRAME.get(card.get("rarity", ""), "#9aa0aa"))
    inner = width - 4
    body = lines_for(card, inner)
    H = len(body) + 2
    tcol = hexrgb(TYPE_COL.get((card.get("types") or ["Colorless"])[0], "#e6e6e6"))
    panel = mix((14, 14, 18), tcol, 0.10)

    def fcol(x, y):
        if frame == "rainbow":                   # hue runs around the box perimeter
            per = 2 * (width + H)
            if y == 0:
                p = x
            elif x == width - 1:
                p = width + y
            elif y == H - 1:
                p = width + H + (width - 1 - x)
            else:
                p = 2 * width + H + (H - 1 - y)
            return hue(p / per)
        return hexrgb(frame)

    def cell(ch, fg, bg=panel, bold=False):
        return f"{ESC}[0;{'1;' if bold else ''}38;2;{fg[0]};{fg[1]};{fg[2]};48;2;{bg[0]};{bg[1]};{bg[2]}m{ch}"

    rows = []
    top = "".join(cell("╭" if x == 0 else "╮" if x == width - 1 else "─", fcol(x, 0)) for x in range(width))
    rows.append(top)
    for j, ln in enumerate(body, start=1):
        s = cell("│", fcol(0, j)) + cell(" ", (0, 0, 0))
        if ln in ("rule", "blank"):
            ch = "┄" if ln == "rule" else " "
            rc = mix(panel, fcol(width // 2, j), 0.45)
            s = cell("├" if ln == "rule" else "│", fcol(0, j)) + "".join(cell(ch, rc) for _ in range(width - 2)) + \
                cell("┤" if ln == "rule" else "│", fcol(width - 1, j))
            rows.append(s + f"{ESC}[0m")
            continue
        used = 0
        for t, f, b in ln.segs:
            for chh in t:
                if used + cw(chh) > inner:
                    break
                s += cell(chh, f, bold=b)
                used += cw(chh)
        s += cell(" " * (inner - used + 1), (0, 0, 0)) + cell("│", fcol(width - 1, j))
        rows.append(s + f"{ESC}[0m")
    rows.append("".join(cell("╰" if x == 0 else "╯" if x == width - 1 else "─", fcol(x, H - 1)) for x in range(width)) + f"{ESC}[0m")
    rows[0] += f"{ESC}[0m"
    return "\n".join(rows) + "\n"


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    c = json.load(open(sys.argv[1], encoding="utf-8"))
    sys.stdout.write(render_text(c, int(sys.argv[2]) if len(sys.argv) > 2 else 64))
