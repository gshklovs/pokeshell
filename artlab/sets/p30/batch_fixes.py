r"""Audit fixes (artlab/sets/p30/audit/REPORT.md): cards with a clear error, re-rendered with the approved recipe of
their rarity. Shared files (p30*.py, artlab/sets/evs) and the other batch modules are NOT edited: the owning batch
module is loaded by path and only the faulty per-card setting is overridden in memory.

  me55-66  Mew ex (Double Rare): the card's Mew faces left (head and big eye lower left, tail sweeping up
           behind to the right); ours faced right (the vendor mew sprite faces right, which is why the approved
           Mew 65 is flipped). Fix: flip=True, Umbreon 92's ex recipe otherwise unchanged.
  me55-26  Pikachu (Pikachu Rare): the mask missed the lower half of the tail (yellow zigzag at the art's right
           edge) and the right paw, so both were left in the fill as a tan ghost beside the sprite. Fix: those two
           parts added to the mask (MASKS[26]["add"]), Pikachu 23's recipe otherwise unchanged.
  me55-129 Alolan Exeggutor (Illustration Rare): the art was 100 x 114 px (57 lines), over the pack's art cap
           (tools/build_art.py MAX_H 110), so the import refused it. Fix: the same crop two sprite rows shorter
           (H 57 -> 55; the 54-row sprite still fits whole), Lapras 131's recipe otherwise unchanged.

Before copies of every output these touch are kept in work/audit/before/ (the first run makes them).

  ..\..\..\.venv\Scripts\python batch_fixes.py [build|verify] [ids]
"""
import importlib.util
import shutil
import sys

import numpy as np
from PIL import Image

import p30lib as P
from p30lib import E
import p30cards

BEFORE = P.DATA / "work/audit/before"


def module(name):
    key = f"p30fix_{name}"
    if key not in sys.modules:
        spec = importlib.util.spec_from_file_location(key, P.HERE / f"{name}.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return sys.modules[key]


def keep_before(cid):
    """copy art / out / anim / mask of a card to work/audit/before/ once (never overwritten)"""
    if (BEFORE / "art" / f"{cid}.json").exists():
        return
    for sub, pats in (("art", [f"{cid}.json"]), ("out", [f"{cid}-*"]), ("masks", [f"{cid}.png"])):
        (BEFORE / sub).mkdir(parents=True, exist_ok=True)
        for pat in pats:
            for f in (P.DATA / sub).glob(pat):
                shutil.copy2(f, BEFORE / sub / f.name)
    for nm in (cid, f"{cid}_shiny"):
        src = P.DATA / "anim" / nm
        if src.is_dir():
            shutil.copytree(src, BEFORE / "anim" / nm, dirs_exist_ok=True)


def fix_66():
    DR = module("batch_double_rare")
    assert not DR.CFG["me55-66"].get("flip")
    DR.CFG["me55-66"]["flip"] = True


TAIL26 = [(515, 250), (560, 262), (606, 285), (606, 400), (575, 400), (545, 350), (520, 300)]
PAW26 = [(458, 240), (505, 240), (508, 318), (462, 318)]


def fix_26(write_mask=True):
    PR = module("batch_pikachu_rare")
    sp = PR.MASKS[26]
    if TAIL26 not in sp["add"]:
        sp["add"] = list(sp["add"]) + [TAIL26, PAW26]
    if write_mask:
        cid, m = PR.make_mask(26)
        Image.fromarray((m * 255).astype(np.uint8)).save(E.MASKS / f"{cid}.png")


def fix_129():
    IR = module("batch_illustration_rare")
    x0, y0, S, W, H = IR.SPEC["me55-129"]["crop"]
    assert H in (57, 55)
    IR.SPEC["me55-129"]["crop"] = (x0, y0, S, W, 55)


FIXES = {"me55-66": fix_66, "me55-26": fix_26, "me55-129": fix_129}


def build(ids):
    import p30build
    import p30anim
    import p30verify
    for cid in ids:
        keep_before(cid)
        FIXES[cid]()
    for cid in ids:
        p30build.render(cid)
    p30anim.build(ids)
    for cid in ids:
        p30verify.check(cid)
    print(f"{p30verify.fails} failures")
    assert p30verify.fails == 0


def verify(ids):
    import p30verify
    for cid in ids:
        FIXES[cid](**({"write_mask": False} if cid == "me55-26" else {}))
        p30verify.check(cid)
    print(f"{p30verify.fails} failures")
    return 1 if p30verify.fails else 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    ids = [a for a in sys.argv[2:] if a in FIXES] or list(FIXES)
    if cmd == "build":
        build(ids)
    else:
        sys.exit(verify(ids))
