"""coordinator: fetch every plan.json card missing cards/<id>.json, skipping failures, several passes"""
import json, time
from pathlib import Path
import fetch_cards as f
HERE = Path(__file__).resolve().parent   # plan.json (code)
DATA = f.HERE                            # cards/ (data)
plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
ids = [c["id"] for g in plan.values() for c in g]
for rnd in range(6):
    missing = [i for i in ids if not (DATA / "cards" / f"{i}.json").exists()]
    print(f"pass {rnd}: {len(missing)} missing", flush=True)
    if not missing: break
    for cid in missing:
        f.PICKS = [cid]
        try: f.main()
        except SystemExit as e: print("skip", cid, e, flush=True)
    time.sleep(20)
print("done", flush=True)
