r"""Build the Evolving Skies batch:
  art/<id>.json            ART_FORMAT (one variant, keyed by the printed-rarity finish)
  out/<id>-art[-shiny].ans/.png          the art alone, as the terminal prints it
  out/<id>-card[-shiny].ans/.png         the art stacked over its text half (bottom.py), like a real card
  strip.png                the five arts side by side (true relative size)

  ..\..\..\.venv\Scripts\python build.py [swsh7-74 ...]      (animations: anim.py, check: verify.py, sheet: sheet.py)
"""
import json
import sys

from PIL import Image

import evlib  # noqa: F401,I001  (first: puts artlab/lib, where bottom.py lives, on sys.path)
import bottom
import evcards
import evlib as E
from evlib import L


def check(rows, pal, where):
    w = len(rows[0])
    for i, r in enumerate(rows):
        assert len(r) == w, f"{where}: row {i} is {len(r)} wide, expected {w}"
        for ch in r:
            assert ch == "." or ch in pal, f"{where}: row {i} uses '{ch}' not in palette"


def art_json(c):
    """ART_FORMAT for one card: base palette = the sprite's colours, the variant carries the rest"""
    rows, pal, shiny = L.keyed(c)
    spr = c.spr
    base = dict(spr.pal)
    art = {"id": c.meta["card"], "name": json.load(open(E.CARDS / f"{c.meta['card']}.json", encoding="utf-8"))["name"],
           "pokemon": spr.name, "palette": base,
           "shiny": {k: v for k, v in spr.shiny.items() if v != spr.pal[k]}, "variants": {}}
    spr_keys = set(c.pals["sprite"])
    v = {"card": c.meta["card"], "rarity": c.meta["rarity"], "finish": c.meta["finish"], "label": c.meta["label"],
         "flip": spr.flip, "rows": rows}
    vpal = {k: val for k, val in pal.items() if base.get(k) != val}
    if vpal:
        v["palette"] = vpal
    vsh = {k: val for k, val in shiny.items() if art["shiny"].get(k, base.get(k)) != val and k in spr_keys}
    if vsh:
        v["shiny"] = vsh
    art["variants"][c.meta["variant"]] = v
    return art


def variant_pal(art, var, shiny):
    v = art["variants"][var]
    p = {**art["palette"], **v.get("palette", {})}
    if shiny:
        p = {**p, **art["shiny"], **v.get("shiny", {})}
    return p


def render(cid):
    E.OUT.mkdir(exist_ok=True)
    E.ART.mkdir(exist_ok=True)
    c = evcards.BUILDERS[cid]()
    art = art_json(c)
    var = c.meta["variant"]
    (E.ART / f"{cid}.json").write_text(json.dumps(art, indent=1, ensure_ascii=False), encoding="utf-8")
    rows = art["variants"][var]["rows"]
    card = json.load(open(E.CARDS / f"{cid}.json", encoding="utf-8"))
    ims = {}
    for sh in (False, True):
        p = variant_pal(art, var, sh)
        check(rows, p, cid)
        direct = c.rgb(sh)
        for y, r in enumerate(rows):
            for x, ch in enumerate(r):
                assert (ch == "." and direct[y][x] is None) or L.hexrgb(p[ch]) == direct[y][x], (cid, sh, x, y)
        sfx = "-shiny" if sh else ""
        ims[("art", sh)] = L.term_png(rows, p, E.OUT / f"{cid}-art{sfx}.png")
        used = {ch for r in rows for ch in r if ch != "."}
        top = L.to_ansi(rows, {k: p[k] for k in used})
        bot = bottom.render_text(card, len(rows[0]))
        ans = top + bot
        (E.OUT / f"{cid}-card{sfx}.ans").write_text(ans, encoding="utf-8", newline="\n")
        ims[("card", sh)] = L.render(ans, str(E.OUT / f"{cid}-card{sfx}.png"))
    spr_keys = set(c.pals["sprite"])
    ncol = len({ch for r in rows for ch in r if ch != "." and ch not in spr_keys})
    info = {"cols": c.FW, "lines": c.FH // 2, "grid_px": [c.FW, c.FH], "bg_colours": ncol,
            "art_ans_bytes": (E.OUT / f"{cid}-art.ans").stat().st_size,
            "card_lines": len((E.OUT / f"{cid}-card.ans").read_text(encoding="utf-8").rstrip("\n").split("\n")),
            "card_ans_bytes": (E.OUT / f"{cid}-card.ans").stat().st_size, "sprite_at": list(c.off),
            "flip": c.spr.flip, "rarity": c.meta["rarity"], "finish": c.meta["finish"]}
    print(f"{cid:10s} {c.meta['rarity']:13s} {c.FW} cols x {c.FH // 2} lines, {ncol:3d} non-sprite colours, "
          f"art {info['art_ans_bytes']} B, card {info['card_lines']} lines, sprite at {c.off}")
    return ims, info


def strip(all_ims, key="art", name="strip.png"):
    ims = [all_ims[cid][(key, False)] for cid in evcards.ORDER if cid in all_ims]
    o = Image.new("RGB", (sum(i.width for i in ims) + 16 * (len(ims) + 1), max(i.height for i in ims) + 32), (24, 24, 28))
    x = 16
    for i in ims:
        o.paste(i, (x, 16))
        x += i.width + 16
    o.save(E.DATA / name)


def main():
    ids = [a for a in sys.argv[1:] if a in evcards.BUILDERS] or evcards.ORDER
    all_ims, infos = {}, {}
    for cid in ids:
        all_ims[cid], infos[cid] = render(cid)
    if len(ids) == len(evcards.ORDER):
        strip(all_ims)
        strip(all_ims, "card", "strip-cards.png")
        (E.DATA / "sizes.json").write_text(json.dumps(infos, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
