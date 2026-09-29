r"""Build the Base Set ladder, the evs way (evs/build.py's art_json / check / variant_pal, loaded by path):
  art/<id>.json                          ART_FORMAT
  out/<id>-art[-shiny].ans/.png          the art alone
  out/<id>-card[-shiny].ans/.png         the art over its text half (evs bottom.py, frame colour of the tier)
  sizes.json

  ..\..\..\.venv\Scripts\python basebuild.py [base1-4 ...]
"""
import json
import sys

import baselib as P
from baselib import E, L, bottom
import basecards

B = P.load_evs("build", "evs_build")

# bottom.py knows the evs tiers only; the new tiers get their frame colour from the builder's meta
FRAMES = basecards.FRAMES


def render(cid):
    E.OUT.mkdir(exist_ok=True)
    E.ART.mkdir(exist_ok=True)
    c = basecards.BUILDERS[cid]()
    art = B.art_json(c)
    var = c.meta["variant"]
    (E.ART / f"{cid}.json").write_text(json.dumps(art, indent=1, ensure_ascii=False), encoding="utf-8")
    rows = art["variants"][var]["rows"]
    card = P.card_json(cid)
    frame = c.meta.get("frame") or FRAMES.get(card["tier"])
    ims = {}
    for sh in (False, True):
        p = B.variant_pal(art, var, sh)
        B.check(rows, p, cid)
        direct = c.rgb(sh)
        for y, r in enumerate(rows):
            for x, ch in enumerate(r):
                assert (ch == "." and direct[y][x] is None) or L.hexrgb(p[ch]) == direct[y][x], (cid, sh, x, y)
        sfx = "-shiny" if sh else ""
        ims[("art", sh)] = L.term_png(rows, p, E.OUT / f"{cid}-art{sfx}.png")
        used = {ch for r in rows for ch in r if ch != "."}
        top = L.to_ansi(rows, {k: p[k] for k in used})
        bot = bottom.render_text(card, len(rows[0]), frame=frame)
        (E.OUT / f"{cid}-card{sfx}.ans").write_text(top + bot, encoding="utf-8", newline="\n")
        ims[("card", sh)] = L.render(top + bot, str(E.OUT / f"{cid}-card{sfx}.png"))
    spr_keys = set(c.pals["sprite"])
    ncol = len({ch for r in rows for ch in r if ch != "." and ch not in spr_keys})
    info = {"cols": c.FW, "lines": c.FH // 2, "grid_px": [c.FW, c.FH], "bg_colours": ncol,
            "art_ans_bytes": (E.OUT / f"{cid}-art.ans").stat().st_size,
            "card_lines": len((E.OUT / f"{cid}-card.ans").read_text(encoding="utf-8").rstrip("\n").split("\n")),
            "card_ans_bytes": (E.OUT / f"{cid}-card.ans").stat().st_size, "sprite_at": list(c.off),
            "flip": c.spr.flip, "rarity": c.meta["rarity"], "finish": c.meta["finish"], "frame": frame}
    print(f"{cid:9s} {c.meta['rarity']:26s} {c.FW} cols x {c.FH // 2} lines, {ncol:3d} non-sprite colours, "
          f"art {info['art_ans_bytes']} B, card {info['card_lines']} lines, sprite at {c.off}")
    return ims, info


def main():
    ids = [a for a in sys.argv[1:] if a in basecards.BUILDERS] or basecards.ORDER
    f = P.DATA / "sizes.json"
    infos = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    for cid in ids:
        _, infos[cid] = render(cid)
    f.write_text(json.dumps({k: infos[k] for k in basecards.ORDER if k in infos}, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
