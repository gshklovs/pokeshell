"""Brilliant Stars (swsh9 + the Trainer Gallery swsh9tg) on top of the approved Evolving Skies pipeline
(artlab/sets/evs), unchanged -- the p30 / cz pattern (artlab/sets/cz/czlib.py).

evs's own modules (evlib, evcards, evcards2, bottom) are imported from artlab/sets/evs (put first on sys.path);
evs's anim.py / build.py are loaded BY FILE PATH. evlib's card-scan / mask / output paths are pointed at
<DATA>/brs at runtime (setlib.use_set): scans ref/swsh9_<number>.png for both sets (TG numbers are TG01..TG30,
so swsh9_TG01.png etc.). No evs, p30 or cz file is edited.
"""
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent            # artlab/sets/brs: this set's code (plan.json, batch_*.py)
EVS = HERE.parent / "evs"                         # the reference set's code: the approved recipes
CZ = HERE.parent / "cz"                           # Crown Zenith: the approved VSTAR crest + gallery recipes
sys.path.insert(0, str(EVS))
import evlib as E  # noqa: E402
sys.path.insert(0, str(EVS))            # s3lib inserted suite3 in front: evs must win for evcards / bottom
import evcards  # noqa: E402,F401
import evcards2  # noqa: E402,F401
import bottom  # noqa: E402
assert Path(bottom.__file__).parent == E.LIB and Path(evcards.__file__).parent == EVS

from evlib import L, Card, Sprite  # noqa: E402,F401

import artpaths  # noqa: E402
import setlib  # noqa: E402

SET = "swsh9"
TG = "swsh9tg"
SETS = (SET, TG)
LAB = artpaths.DATA
DATA = setlib.use_set(E, "brs", SET)             # style-lab/brs: ref/swsh9_<n>.png, masks, cards, work, art, out
ref_path = E.ref_path
META = json.loads((HERE / "set.json").read_text(encoding="utf-8"))


def load_evs(name, alias):
    """load artlab/sets/evs/<name>.py by file path under a private module name"""
    if alias in sys.modules:
        return sys.modules[alias]
    spec = importlib.util.spec_from_file_location(alias, EVS / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[alias] = m
    spec.loader.exec_module(m)
    return m


def card_json(cid):
    return json.loads((E.CARDS / f"{cid}.json").read_text(encoding="utf-8"))


def is_tg(cid):
    return cid.startswith(TG + "-")


def plan():
    return json.loads((HERE / "plan.json").read_text(encoding="utf-8"))


def num_label(cid):
    """the printed number: 014/172, TG05/TG30"""
    n = E.num(cid)
    return f"{n}/TG30" if n.startswith("TG") else f"{int(n):03d}/172"


def seed_of(cid):
    return int("".join(ch for ch in E.num(cid) if ch.isdigit()))
