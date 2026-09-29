r"""hfverify over every built Hidden Fates card: the ladder (hfcards) and every group batch, loaded by path, plus
batch_fixes (the audit fixes win, section 14's precedence). Rebuilds each card in memory (no file is written).

  ..\..\..\..\.venv\Scripts\python verify_all.py
"""
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import hflib as P  # noqa: E402,F401
import hfcards  # noqa: E402
import hfverify  # noqa: E402

BATCHES = ["commons", "uncommon", "rare", "holo", "holo_gx", "secret", "shiny_a", "shiny_b", "shiny_gx_a",
           "shiny_gx_b", "fixes"]


def load(name):
    f = HERE / f"batch_{name}.py"
    if not f.exists():
        return None
    spec = importlib.util.spec_from_file_location(f"hf_batch_{name}", f)
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


def main():
    ids = list(hfcards.ORDER)
    for b in BATCHES:
        m = load(b)
        if m is None:
            continue
        hfcards.BUILDERS.update(m.BUILDERS)
        ids += [c for c in m.BUILDERS if c not in ids]
    for cid in ids:
        hfverify.check(cid)
    print(f"{len(ids)} cards, {hfverify.fails} failures")
    return hfverify.fails


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
