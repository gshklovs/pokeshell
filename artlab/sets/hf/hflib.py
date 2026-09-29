"""Hidden Fates (sm115) + its Shiny Vault (sma) on top of the approved Evolving Skies pipeline (artlab/sets/evs),
unchanged: the p30lib pattern (docs/ART_METHOD.md section 14). Both subsets share one data folder,
<DATA>/hf/ (scans ref/hf_<number>.png: sm115 numbers 1..69, Shiny Vault numbers SV1..SV94, so they never collide).

evs's own modules (evlib, evcards, evcards2, bottom) are imported from artlab/sets/evs; evs's anim.py / build.py are
loaded BY FILE PATH (load_evs). evlib's scan / mask / output paths are pointed at hf at runtime; no evs file is edited.

New here: ShinySprite, the Shiny Vault's sprite. The real Shiny Vault cards print the SHINY Pokemon, so their art
is the colorscripts SHINY sprite, pixel-exact and unchanged (flip only): its normal palette IS the vendor shiny
palette. The shiny roll of such a card has no other printing to show, so its shiny palette is the same shiny
colours (see FULLSET.md, "the shiny roll").
"""
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent            # artlab/sets/hf: this set's code (plan.json, batch_*.py)
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

SET = "sm115"
SETS = ("sm115", "sma")
LAB = artpaths.DATA
DATA = setlib.use_set(E, "hf", "hf")             # style-lab/hf: ref/hf_<n>.png, masks, cards, work, art, out
ref_path = E.ref_path


def load_evs(name, alias):
    """load artlab/sets/evs/<name>.py by file path under a private module name"""
    spec = importlib.util.spec_from_file_location(alias, EVS / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[alias] = m
    spec.loader.exec_module(m)
    return m


def card_json(cid):
    return json.loads((E.CARDS / f"{cid}.json").read_text(encoding="utf-8"))


def is_vault(cid):
    """a Shiny Vault printing (sma, Rare Shiny / Rare Shiny GX): the Pokemon is printed shiny. The Shiny Vault's
    gold Tapu GX (Rare Secret) are gold cards, not shiny: they take the evs gold remap of the regular sprite."""
    return cid.startswith("sma-") and card_json(cid)["tier"] in VAULT_RARITIES


VAULT_RARITIES = ("Rare Shiny", "Rare Shiny GX")


class ShinySprite(Sprite):
    """the colorscripts SHINY sprite, verbatim (flip only): evlib.Sprite with the shiny palette as its palette.
    Keys and rows are evlib.Sprite's (so the shape is the vendor's); both palettes are the vendor shiny colours."""

    def __init__(self, name, flip=False):
        super().__init__(name, flip)
        self.normal = dict(self.pal)              # the regular colours, kept only for reference / verify
        self.pal = dict(self.shiny)
        self.vault = True


def sprite_for(cid, name, flip=False):
    return ShinySprite(name, flip) if is_vault(cid) else Sprite(name, flip)
