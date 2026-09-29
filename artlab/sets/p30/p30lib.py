"""30th Celebration (me55) on top of the approved Evolving Skies pipeline (artlab/sets/evs), unchanged.

evs's own modules (evlib, evcards, evcards2, bottom) are imported from artlab/sets/evs (put first on sys.path);
evs's anim.py / build.py / verify.py are loaded BY FILE PATH (a plain `import anim` / `build` / `verify` picks
up suite3's modules or a pip package). evlib's card-scan / mask / output paths are pointed at p30 at runtime;
no evs file is edited.
"""
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent            # artlab/sets/p30: this set's code (plan.json, batch_*.py)
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

SET = "me55"
LAB = artpaths.DATA
DATA = setlib.use_set(E, "p30", SET)             # style-lab/p30: ref/me55_<n>.png, masks, cards, work, art, out
ref_path = E.ref_path                            # evlib.card_img / clean / region all go through this


def load_evs(name, alias):
    """load artlab/sets/evs/<name>.py by file path under a private module name"""
    spec = importlib.util.spec_from_file_location(alias, EVS / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[alias] = m
    spec.loader.exec_module(m)
    return m


def card_json(cid):
    return json.loads((E.CARDS / f"{cid}.json").read_text(encoding="utf-8"))
