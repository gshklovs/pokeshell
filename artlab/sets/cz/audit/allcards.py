r"""Every Crown Zenith card's builder, in precedence order (ART_METHOD section 14): the ladder (czcards.LADDER) <
the group batches (batch_<group>.py TABLE) < batch_fixes.py (the audit's fixes). Importing this registers them all
in czcards.CFG / BUILDERS, in memory.
"""
import importlib.util
import sys
from pathlib import Path

CZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CZ))
import czlib as P  # noqa: E402
import czcards as C  # noqa: E402

GROUPS = ["commons", "uncommon", "rare", "holo", "v", "vstar", "radiant", "secret", "gg_v", "gg_vstar", "gg_tg_a",
          "gg_tg_b"]
OWNER = {cid: "ladder" for cid in C.LADDER}


def _load(name):
    f = CZ / f"{name}.py"
    if not f.exists():
        return None
    spec = importlib.util.spec_from_file_location(f"cz_{name}", f)
    m = importlib.util.module_from_spec(spec)
    sys.modules[f"cz_{name}"] = m
    spec.loader.exec_module(m)
    return m


for g in GROUPS:
    m = _load(f"batch_{g}")
    if m is not None:
        C.register(m.TABLE)
        OWNER.update({cid: g for cid in m.TABLE})
FIXES = _load("batch_fixes")
if FIXES is not None:
    C.register(FIXES.TABLE)
    OWNER.update({cid: "fixes" for cid in FIXES.TABLE})
IDS = list(OWNER)
