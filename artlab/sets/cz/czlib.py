"""Crown Zenith (swsh12pt5 + the Galarian Gallery swsh12pt5gg) on top of the approved Evolving Skies pipeline
(artlab/sets/evs), unchanged -- the p30 pattern (artlab/sets/p30/p30lib.py).

evs's own modules (evlib, evcards, evcards2, bottom) are imported from artlab/sets/evs (put first on sys.path);
evs's anim.py / build.py are loaded BY FILE PATH. evlib's card-scan / mask / output paths are pointed at
<DATA>/cz at runtime (setlib.use_set): scans ref/swsh12pt5_<number>.png for both sets (GG numbers are GG01..GG70,
so swsh12pt5_GG01.png etc.). No evs or p30 file is edited.
"""
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent            # artlab/sets/cz: this set's code (plan.json, batch_*.py)
EVS = HERE.parent / "evs"                         # the reference set's code: the approved recipes
P30 = HERE.parent / "p30"                         # 30th Celebration: ex grain, IR etch, pearl, chrome ...
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

SET = "swsh12pt5"
GG = "swsh12pt5gg"
SETS = (SET, GG)
LAB = artpaths.DATA
DATA = setlib.use_set(E, "cz", SET)              # style-lab/cz: ref/swsh12pt5_<n>.png, masks, cards, work, art, out
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


def is_gg(cid):
    return cid.startswith(GG + "-")


def plan():
    return json.loads((HERE / "plan.json").read_text(encoding="utf-8"))


def num_label(cid):
    """the printed number: 014/159, GG35/GG70"""
    n = E.num(cid)
    return f"{n}/GG70" if n.startswith("GG") else f"{int(n):03d}/159"
