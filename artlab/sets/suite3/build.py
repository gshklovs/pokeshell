"""Build suite3: per-Pokemon ART_FORMAT JSON (grid-resolution rows), static terminal renders (normal +
shiny), grid.png (Pokemon x 5 tiers), ladder.png (Pikachu's 5 tiers, big), crowns.png.

  ..\\..\\..\\.venv\\Scripts\\python build.py [pokemon ...]        (animations: python anim.py)
"""
import json
import sys

from PIL import Image, ImageDraw, ImageFont

from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))
import s3lib as L  # noqa: E402
import tiers

GRID_TIERS = {"pikachu": ["common", "common_bg", "holo", "fullart", "gold"],
              "charmander": ["common", "common_bg", "holo", "fullart", "top"],
              "bulbasaur": ["common", "common_bg", "holo", "fullart", "gold"],
              "squirtle": ["common", "common_bg", "holo", "fullart", "gold"]}
COLS = ["common", "common + scene", "holo", "full art / ultra", "gold / top tier"]


def check(rows, pal, where):
    w = len(rows[0])
    for i, r in enumerate(rows):
        assert len(r) == w, f"{where}: row {i} is {len(r)} wide, expected {w}"
        for ch in r:
            assert ch == "." or ch in pal, f"{where}: row {i} uses '{ch}' not in palette"


def render_poke(poke, only=None):
    L.OUT.mkdir(exist_ok=True)
    T = tiers.TIERS[poke]
    s = tiers.Sprite(poke, False)
    art = {"id": poke, "name": poke.capitalize(), "palette": dict(s.pal),
           "shiny": {k: v for k, v in s.shiny.items() if v != s.pal[k]}, "variants": {}}
    base = art["palette"]
    ims, info = {}, {}
    for t, fn in T.items():
        if only and t not in only:
            continue
        c = fn()
        rows, pal, shiny = L.keyed(c)
        spr_keys = set(c.pals["sprite"])
        vpal = {k: v for k, v in pal.items() if base.get(k) != v}
        v = {"card": c.meta["card"], "label": c.meta["label"], "rows": rows}
        if vpal:
            v["palette"] = vpal
        vsh = {k: val for k, val in shiny.items() if art["shiny"].get(k, base.get(k)) != val and k in spr_keys}
        if vsh:
            v["shiny"] = vsh
        art["variants"][t] = v
        for sh in (False, True):
            p = {**art["palette"], **v.get("palette", {})}
            if sh:
                p = {**p, **art["shiny"], **v.get("shiny", {})}
            check(rows, p, f"{poke}/{t}")
            stem = f"{poke}-{t}" + ("-shiny" if sh else "")
            direct = c.rgb(sh)                     # the JSON must reproduce the composite exactly
            for y, r in enumerate(rows):
                for x, ch in enumerate(r):
                    assert (ch == "." and direct[y][x] is None) or L.hexrgb(p[ch]) == direct[y][x], (poke, t, sh, x, y)
            ims[(t, sh)] = L.term_png(rows, p, L.OUT / f"{stem}.png")
        ncol = len({ch for r in rows for ch in r if ch != "." and ch not in spr_keys})
        ansb = (L.OUT / f"{poke}-{t}.ans").stat().st_size
        info[t] = {"cols": c.FW, "lines": c.FH // 2, "grid_px": [c.FW, c.FH], "bg_colours": ncol,
                   "keys": len(pal), "ans_bytes": ansb}
        print(f"{poke:10s} {t:9s} {c.meta['card']:10s} {c.FW} cols x {c.FH // 2} lines, {ncol:3d} non-sprite colours, "
              f"{ansb} B .ans, sprite at {c.off}")
    if not only:
        (L.HERE / f"{poke}-suite3.json").write_text(json.dumps(art, indent=1, ensure_ascii=False), encoding="utf-8")
    return ims, info


def font(n):
    return ImageFont.truetype(L.FONT, n)


def grid(all_ims, all_info):
    gap, lab, top, left = 24, 50, 80, 330
    colw = [max(all_ims[p][(GRID_TIERS[p][i], False)].width for p in all_ims) for i in range(len(COLS))]
    xs = [left + gap + sum(colw[:i]) + gap * i for i in range(len(COLS))]
    rows_h = {p: max(ims[(t, False)].height for t in GRID_TIERS[p]) for p, ims in all_ims.items()}
    W = xs[-1] + colw[-1] + gap
    H = top + sum(rows_h[p] + lab + gap for p in all_ims)
    o = Image.new("RGB", (W, H), (24, 24, 28))
    d = ImageDraw.Draw(o)
    for i, c in enumerate(COLS):
        d.text((xs[i], 10), c, font=font(60), fill=(220, 220, 220))
    y = top
    for p, ims in all_ims.items():
        d.text((gap, y + lab + rows_h[p] // 2 - 30), p, font=font(60), fill=(240, 240, 240))
        for i, t in enumerate(GRID_TIERS[p]):
            im = ims[(t, False)]
            x = xs[i]
            nf = all_info[p][t]
            d.text((x, y + 2), f"{t}  {nf['cols']}x{nf['lines']}  {nf['bg_colours']} col", font=font(36), fill=(170, 170, 170))
            o.paste(im, (x, y + lab))
        y += rows_h[p] + lab + gap
    o.save(L.HERE / "grid.png")


def ladder(ims, info, poke="pikachu"):
    """the five tiers side by side, big (terminal renders scaled to one height)"""
    k = 700 / max(ims[(t, False)].height for t in GRID_TIERS[poke])      # one scale: true relative sizes
    panels = []
    for t in GRID_TIERS[poke]:
        im = ims[(t, False)]
        panels.append((t, im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)))
    Ht = max(p.height for _, p in panels)
    gap = 24
    W = sum(p.width for _, p in panels) + gap * (len(panels) + 1)
    o = Image.new("RGB", (W, Ht + 2 * gap + 44), (24, 24, 28))
    d = ImageDraw.Draw(o)
    x = gap
    for (t, p), name in zip(panels, COLS):
        o.paste(p, (x, gap + 44))
        nf = info[t]
        d.text((x, 10), f"{name}", font=font(28), fill=(235, 235, 235))
        d.text((x, 42 - 4), f"{nf['cols']}x{nf['lines']}, {nf['bg_colours']} colours", font=font(18), fill=(160, 160, 160))
        x += p.width + gap
    o.save(L.HERE / "ladder.png")


def crowns_sheet():
    import crowns
    panels, labels = [], []
    panels.append(L.region("pikachu/ref/sv8_247", 120, 150, 620, 560, 440))
    labels.append("card sv8/247 (crop)")
    for name in [None] + list(crowns.CROWNS):
        c = tiers.pika_gold(crown=name)
        rows, pal, _ = L.keyed(c)
        L.WORK.mkdir(exist_ok=True)
        im = L.term_png(rows, pal, L.WORK / f"crown-{name or 'none'}.png")
        panels.append(im.resize((round(im.width * 440 / im.height), 440), Image.LANCZOS))
        labels.append(f"crown: {name}" if name else "no crown")
    gap = 16
    Wt = sum(p.width for p in panels) + gap * (len(panels) + 1)
    o = Image.new("RGB", (Wt, 440 + 2 * gap + 30), (24, 24, 28))
    d = ImageDraw.Draw(o)
    x = gap
    for p, lb in zip(panels, labels):
        o.paste(p, (x, gap + 30))
        d.text((x, 8), lb, font=font(20), fill=(230, 230, 230))
        x += p.width + gap
    o.save(L.HERE / "crowns.png")


def main():
    args = sys.argv[1:]
    pokes = [a for a in args if a in tiers.TIERS] or list(tiers.TIERS)
    only = [a for a in args if a not in tiers.TIERS] or None
    all_ims, all_info = {}, {}
    for p in pokes:
        all_ims[p], all_info[p] = render_poke(p, only)
        if not only:
            L.WORK.mkdir(exist_ok=True)
            ims = [all_ims[p][(t, False)] for t in GRID_TIERS[p]]
            o = Image.new("RGB", (sum(i.width for i in ims) + 10 * len(ims), max(i.height for i in ims)), (24, 24, 28))
            x = 0
            for i in ims:
                o.paste(i, (x, 0))
                x += i.width + 10
            o.save(L.WORK / f"strip-{p}.png")
    if len(pokes) == 4 and not only:
        grid(all_ims, all_info)
        ladder(all_ims["pikachu"], all_info["pikachu"])
        crowns_sheet()
        (L.HERE / "sizes.json").write_text(json.dumps(all_info, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
