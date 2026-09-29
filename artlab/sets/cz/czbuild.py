r"""Render Crown Zenith cards the evs way (evs/build.py's art_json / check / variant_pal, loaded by path):
  art/<id>.json                          ART_FORMAT
  out/<id>-art[-shiny].ans/.png          the art alone
  out/<id>-card[-shiny].ans/.png         the art over its text half (evs bottom.py, the builder's meta["frame"])

  ..\..\..\.venv\Scripts\python czbuild.py [ids]      (the ladder by default; writes sizes.json for the ladder only)
"""
import json
import sys

import czlib as P
from czlib import E, L, bottom
import czcards

B = P.load_evs("build", "evs_build")


def render(cid):
    E.OUT.mkdir(exist_ok=True)
    E.ART.mkdir(exist_ok=True)
    c = czcards.BUILDERS[cid]()
    art = B.art_json(c)
    var = c.meta["variant"]
    (E.ART / f"{cid}.json").write_text(json.dumps(art, indent=1, ensure_ascii=False), encoding="utf-8")
    rows = art["variants"][var]["rows"]
    card = P.card_json(cid)
    assert card["tier"] == c.meta["rarity"], (cid, card["tier"], c.meta["rarity"])
    frame = c.meta.get("frame") or czcards.FRAMES.get(card["tier"])
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
            "sprite": c.spr.name, "flip": c.spr.flip, "rarity": c.meta["rarity"], "finish": c.meta["finish"],
            "frame": frame, "kind": czcards.CFG[cid]["kind"]}
    assert c.FW <= 140 and c.FH <= 110, f"{cid}: {c.FW}x{c.FH} grid px is over the 140 x 110 cap"
    print(f"{cid:17s} {c.meta['rarity']:26s} {c.FW} cols x {c.FH // 2} lines, {ncol:3d} non-sprite colours, "
          f"sprite {c.spr.name} flip={c.spr.flip} at {c.off}")
    return ims, info


def main():
    ids = [a for a in sys.argv[1:] if a in czcards.BUILDERS] or czcards.ORDER
    f = P.DATA / "sizes.json"
    infos = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    for cid in ids:
        _, infos[cid] = render(cid)
    f.write_text(json.dumps({k: infos[k] for k in czcards.ORDER if k in infos}, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
