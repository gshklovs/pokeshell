r"""The audit's machine checks over EVERY card of the Brilliant Stars set list (main + Trainer Gallery):
coverage (built / skipped with a reason), brsverify's per-card checks (sprite exact, allowed recolour, commons plain +
flip_commons, size cap, data verbatim, anims), the treatment per printed rarity (the builder kind), forms, facing and
size -> work/audit/meta.json. Builders come from audit/allcards.py (ladder < batches < batch_fixes).

  ..\..\..\..\.venv\Scripts\python audit\verify_all.py
"""
import contextlib
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import allcards as AC  # noqa: E402
import brsverify  # noqa: E402

P, C, E = AC.P, AC.C, AC.P.E
# printed rarity -> the kinds allowed for it (the approved example of that finish)
KIND_OK = {"Common": {"common"}, "Uncommon": {"uncommon"}, "Rare": {"rare"}, "Rare Holo": {"holo"},
           "Rare Holo V": {"v", "alt"}, "Rare Holo VMAX": {"vmax", "alt"}, "Rare Holo VSTAR": {"vstar"},
           "Rare Ultra": {"fullart", "alt"}, "Rare Rainbow": {"rainbow"}, "Rare Secret": {"gold"},
           "Trainer Gallery Rare Holo": {"gallery"}}
ALT_ULTRA = {"swsh9-154", "swsh9-156", "swsh9-162", "swsh9-166"}          # the painted Rare Ultras (from the scans)


def main():
    setlist = json.loads((P.DATA / "setlist.json").read_text(encoding="utf-8"))
    plan = P.plan()
    skipped = {s["id"]: s["reason"] for s in plan["_skipped"]}
    sizes = {}
    for f in (P.DATA / "sheets").glob("*-sizes.json"):
        sizes.update(json.loads(f.read_text(encoding="utf-8")))
    out, bad = {}, 0
    for c in setlist:
        cid = c["id"]
        row = {"name": c["name"], "number": c["number"], "rarity": c.get("rarity"), "set": c["set"]["id"]}
        if cid in skipped:
            row.update(status="skipped", reason=skipped[cid])
            out[cid] = row
            continue
        if cid not in C.CFG:
            row.update(status="MISSING")
            bad += 1
            out[cid] = row
            continue
        k = C.cfg(cid)
        before = brsverify.fails
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            brsverify.check(cid)
        fails = brsverify.fails - before
        info = sizes.get(cid, {})
        tg = P.is_tg(cid)
        rar = c.get("rarity")
        kind_ok = k["kind"] in KIND_OK.get(rar, set()) and \
            (rar != "Rare Ultra" or (k["kind"] == "alt") == (cid in ALT_ULTRA)) and \
            (rar not in ("Rare Holo V", "Rare Holo VMAX") or (k["kind"] == "alt") == tg)
        row.update(status="built" if not fails and kind_ok else "FAIL", owner=AC.OWNER[cid], kind=k["kind"],
                   sprite=k["sprite"], flip=(cid in P.META.get("flip_commons", [])) if k["kind"] == "common" else k["flip"],
                   cols=info.get("cols"), lines=info.get("lines"), grid=info.get("grid_px"), verify_fails=fails,
                   kind_ok=kind_ok, frame=info.get("frame"), anim=bool((P.DATA / "anim" / cid / f"{cid}.anim").exists()),
                   bad_lines=[ln for ln in buf.getvalue().splitlines() if ln.startswith("BAD")])
        bad += row["status"] != "built"
        out[cid] = row
    d = E.WORK / "audit"
    d.mkdir(parents=True, exist_ok=True)
    (d / "meta.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    from collections import Counter
    print(Counter(r["status"] for r in out.values()))
    for cid, r in out.items():
        if r["status"] not in ("built", "skipped"):
            print(cid, r)
    print("problems:", bad)


if __name__ == "__main__":
    main()
