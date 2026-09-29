r"""Audit fixes (artlab/sets/evs/audit/REPORT.md): cards whose treatment or sprite was clearly wrong, re-rendered with
the approved recipe of their rarity. Shared files and the other batch modules are NOT edited: the owning batch
module is loaded by path and only the faulty per-card setting is overridden in memory; build / anim / verify are
loaded by path too.

  swsh7-210 Dracozolt VMAX (Rare Rainbow, true rainbow): the card's Dracozolt faces right (head top-right, as on
            Dracozolt VMAX 59, which is flipped); ours faced left. Fix: flip=True, Leafeon 204's rainbow recipe
            otherwise unchanged (rainbow blend 0.55 re-computed on the flipped sprite).

  ..\..\..\.venv\Scripts\python batch_fixes.py build|verify [ids]
"""
import importlib.util
import sys

import evcards
import evlib as E


def evs_module(name):
    key = f"evs_{name}"
    if key not in sys.modules:
        spec = importlib.util.spec_from_file_location(key, E.HERE / f"{name}.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return sys.modules[key]


def fix_210():
    RS = evs_module("batch_rainbow_secret")
    old = dict(RS.CFG["swsh7-210"])
    RS.card("swsh7-210", "rainbow", "dracozolt", flip=True, text_y=655,
            mask={"model": "isnet-general-use", "close": 6, "keep": 4})
    assert RS.CFG["swsh7-210"]["flip"] and not old["flip"]
    RS.register(["swsh7-210"])


FIXES = {"swsh7-210": fix_210}


def build(ids):
    for cid in ids:
        FIXES[cid]()
    B = evs_module("build")
    anim = evs_module("anim")
    for cid in ids:
        B.render(cid)
    anim.build(ids)


def verify(ids):
    for cid in ids:
        FIXES[cid]()
    evcards.ORDER[:] = ids
    try:
        evs_module("verify")
    except SystemExit as e:
        return e.code
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    ids = sys.argv[2:] or list(FIXES)
    if cmd == "build":
        build(ids)
    else:
        sys.exit(verify(ids))
