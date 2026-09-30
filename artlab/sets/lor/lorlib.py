"""Lost Origin (swsh11 + the Trainer Gallery swsh11tg) on top of the approved Evolving Skies pipeline
(artlab/sets/evs), unchanged -- the p30 / cz pattern (artlab/sets/cz/czlib.py).

evs's own modules (evlib, evcards, evcards2, bottom) are imported from artlab/sets/evs (put first on sys.path);
evs's anim.py / build.py are loaded BY FILE PATH. evlib's card-scan / mask / output paths are pointed at
<DATA>/lor at runtime (setlib.use_set): scans ref/swsh11_<number>.png for both sets (TG numbers are TG01..TG30,
so swsh11_TG01.png etc.). No evs, p30, cz or brs file is edited. The Radiant Rare shiny sprite
(ShinySprite, PRINTED_SHINY) is czlib's, copied.
"""
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent            # artlab/sets/lor: this set's code (plan.json, batch_*.py)
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
import numpy as np  # noqa: E402

import artpaths  # noqa: E402
import setlib  # noqa: E402

SET = "swsh11"
TG = "swsh11tg"
SETS = (SET, TG)
LAB = artpaths.DATA
DATA = setlib.use_set(E, "lor", SET)             # style-lab/lor: ref/swsh11_<n>.png, masks, cards, work, art, out
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
    """the printed number: 014/196, TG05/TG30"""
    n = E.num(cid)
    return f"{n}/TG30" if n.startswith("TG") else f"{int(n):03d}/196"


def seed_of(cid):
    return int("".join(ch for ch in E.num(cid) if ch.isdigit()))


PRINTED_SHINY = ("Radiant Rare",)                 # rarities whose real card prints the SHINY Pokemon (czlib)


class ShinySprite(Sprite):
    """czlib.ShinySprite: the colorscripts SHINY sprite, verbatim (flip only), as the card's base art: the Radiant
    Rare cards print the shiny Pokemon. Both palettes are the vendor shiny colours, so the card has no separate shiny
    form (its tier is "shiny": "printed" in pack.json: the shiny roll never applies to it)."""

    def __init__(self, name, flip=False):
        super().__init__(name, flip)
        self.normal = dict(self.pal)              # the regular colours, kept only for reference
        self.pal = dict(self.shiny)
        self.printed_shiny = True


def pushpull_1x1(rgb, known):
    """s3lib.pushpull with its pyramid run down to 1 x 1 instead of stopping at 2 x 2. The original leaves a
    top-level cell with no known pixel at 0 / 1e-9 = BLACK (found by the Lost Origin vstar and rainbow batches: the
    text box paints out the lower half and the Pokemon fills an upper quadrant). Wherever every top-level cell has
    known pixels the result is identical. Installed for the whole Lost Origin set (every lor process), so all its
    cards are built the same way; s3lib itself (and every other set) is unchanged."""
    img = rgb * known[..., None]
    w = known.astype(float)
    pyr = [(img, w)]
    while max(w.shape) > 1:
        h, wd = w.shape
        h2, w2 = (h + 1) // 2, (wd + 1) // 2
        img = np.pad(img, ((0, h2 * 2 - h), (0, w2 * 2 - wd), (0, 0)), mode="edge")
        w = np.pad(w, ((0, h2 * 2 - h), (0, w2 * 2 - wd)), mode="edge")
        img = img.reshape(h2, 2, w2, 2, 3).sum((1, 3))
        w = w.reshape(h2, 2, w2, 2).sum((1, 3))
        s = np.minimum(w, 1) / np.maximum(w, 1e-9)
        img, w = img * s[..., None], np.minimum(w, 1)
        pyr.append((img, w))
    col = pyr[-1][0] / np.maximum(pyr[-1][1], 1e-9)[..., None]
    for img, w in reversed(pyr[:-1]):
        up = L._resize_f(col, (w.shape[1], w.shape[0]))
        col = img + up * (1 - w)[..., None]
    return col


L.pushpull = pushpull_1x1
