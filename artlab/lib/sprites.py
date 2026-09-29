"""Parse pokemon-colorscripts large sprites (each pixel = '██', 2 cols x 1 line) into RGB grids."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import artpaths  # noqa: E402

CS = artpaths.VENDOR / "pokemon-colorscripts/colorscripts/large"
TOK = re.compile(r"\x1b\[([0-9;]*)m|(.)", re.S)


def load(name, shiny=False):
    txt = (CS / ("shiny" if shiny else "regular") / name).read_text(encoding="utf-8")
    lines = txt.replace("\r\n", "\n").split("\n")
    fg = None
    rows = []
    for ln in lines:
        cells = []
        for m in TOK.finditer(ln):
            if m.group(2) is None:
                p = [int(x) if x else 0 for x in (m.group(1) or "0").split(";")]
                if p[:2] == [38, 2]:
                    fg = tuple(p[2:5])
                elif p == [0]:
                    fg = None
                continue
            ch = m.group(2)
            cells.append(fg if ch == "█" else None)
        rows.append(cells)
    while rows and not any(rows[-1]):
        rows.pop()
    while rows and not any(rows[0]):
        rows.pop(0)
    w = max(len(r) for r in rows)
    rows = [r + [None] * (w - len(r)) for r in rows]
    # 2 cols per pixel
    for r in rows:
        for i in range(0, w - 1, 2):
            assert r[i] == r[i + 1], (name, r[i], r[i + 1])
    g = [r[0::2] for r in rows]
    # trim transparent columns
    cols = [x for x in range(len(g[0])) if any(r[x] for r in g)]
    x0, x1 = min(cols), max(cols) + 1
    return [r[x0:x1] for r in g]


def show(g):
    cols = {}
    keys = "k0123456789abcdefghijmnopqrstuvwxyzABCDEFGH"
    out = []
    for r in g:
        s = ""
        for c in r:
            if c is None:
                s += "."
            else:
                if c == (0, 0, 0):
                    s += "#"; continue
                if c not in cols:
                    cols[c] = keys[1 + len(cols)]
                s += cols[c]
        out.append(s)
    return "\n".join(out), cols


if __name__ == "__main__":
    import sys
    for n in sys.argv[1:]:
        g = load(n)
        s, c = show(g)
        print(n, len(g[0]), "x", len(g))
        print(s)
        print(c)
