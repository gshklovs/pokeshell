"""Base Set (base1, 1999) on top of the approved Evolving Skies pipeline (artlab/sets/evs), unchanged: the
p30lib / hflib pattern (docs/ART_METHOD.md section 14). The data lives in <DATA>/base/ (scans ref/base1_<n>.png,
600 x 825 WotC hires scans).

evs's own modules (evlib, evcards, evcards2, bottom) are imported from artlab/sets/evs; evs's anim.py / build.py are
loaded BY FILE PATH (load_evs). evlib's scan / mask / output paths are pointed at base at runtime; no evs file is
edited.
"""
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent            # artlab/sets/base: this set's code (plan.json, batch_*.py)
EVS = HERE.parent / "evs"                         # the reference set's code: the approved recipes
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

SET = "base1"
SETS = ("base1",)
LAB = artpaths.DATA
DATA = setlib.use_set(E, "base", "base1")         # style-lab/base: ref/base1_<n>.png, masks, cards, work, art, out
ref_path = E.ref_path
META = json.loads((HERE / "set.json").read_text(encoding="utf-8"))


def load_evs(name, alias):
    """load artlab/sets/evs/<name>.py by file path under a private module name"""
    spec = importlib.util.spec_from_file_location(alias, EVS / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[alias] = m
    spec.loader.exec_module(m)
    return m


def card_json(cid):
    return json.loads((E.CARDS / f"{cid}.json").read_text(encoding="utf-8"))


def sprite_for(cid, name, flip=False):
    return Sprite(name, flip)
