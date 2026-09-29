r"""re-run p30verify.check over every built card (the ladder + all six batch groups), batch modules loaded by path
(their builders registered as their own main() would). Writes nothing but stdout.
  ..\..\..\..\.venv\Scripts\python verify_all.py [ids]"""
import importlib.util
import json
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]         # artlab/sets/p30: the set's code
sys.path.insert(0, str(CODE.parents[1]))
import artpaths  # noqa: E402
HERE = artpaths.data("p30")                       # style-lab/p30: the set's data
sys.path.insert(0, str(CODE))
import p30lib as P  # noqa: E402
import p30cards  # noqa: E402


def load(name):
    spec = importlib.util.spec_from_file_location(f"audit_{name}", CODE / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[f"audit_{name}"] = m
    spec.loader.exec_module(m)
    return m


def register_all():
    com = load("batch_commons")
    p30cards.BUILDERS.update({cid: com.make_builder(e) for cid, e in com.BY_ID.items()})
    for n in ("batch_rare", "batch_pikachu_rare", "batch_double_rare", "batch_illustration_rare"):
        load(n)                                          # these register on import
    sf = load("batch_sir_futuristic")
    p30cards.BUILDERS.update(sf.builders())


if __name__ == "__main__":
    register_all()
    import p30verify
    plan = json.loads((CODE / "plan.json").read_text(encoding="utf-8"))
    ids = sys.argv[1:] or (plan["_ladder_done"] + [c["id"] for g, v in plan.items() if not g.startswith("_") for c in v])
    for cid in ids:
        p30verify.check(cid)
    print(f"{len(ids)} cards, {p30verify.fails} failures")
