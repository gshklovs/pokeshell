r"""Every Brilliant Stars card's builder, in precedence order (ART_METHOD section 14): the ladder (brscards.LADDER) <
the group batches (batch_<group>.py TABLE) < batch_fixes.py (the audit's fixes). Importing this registers them all
in brscards.CFG / BUILDERS, in memory.
"""
import importlib.util
import sys
from pathlib import Path

BRS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BRS))
import brslib as P  # noqa: E402
import brscards as C  # noqa: E402

GROUPS = ["commons_a", "commons_b", "uncommon", "rare_a", "rare_b", "holo", "v_a", "v_b", "vstar", "ultra", "rainbow",
          "secret", "tg", "tg_v"]
OWNER = {cid: "ladder" for cid in C.LADDER}


def _load(name):
    f = BRS / f"{name}.py"
    if not f.exists():
        return None
    spec = importlib.util.spec_from_file_location(f"brs_{name}", f)
    m = importlib.util.module_from_spec(spec)
    sys.modules[f"brs_{name}"] = m
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
