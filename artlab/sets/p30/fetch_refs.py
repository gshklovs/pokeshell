"""hires scans for every card in setlist.json -> ref/me55_<number>.png (skip existing)"""
import json
from pathlib import Path
from fetch_set import get, HERE
for c in json.loads((HERE / "setlist.json").read_text(encoding="utf-8")):
    p = HERE / "ref" / f"me55_{c['number']}.png"
    if p.exists() and p.stat().st_size > 10000:
        continue
    try:
        p.write_bytes(get(c["images"]["large"], raw=True))
        print("ok", c["id"], flush=True)
    except SystemExit as e:
        print("skip", c["id"], e, flush=True)
print("done", flush=True)
