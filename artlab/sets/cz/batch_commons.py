r"""Crown Zenith group "commons": the 36 remaining Commons, built exactly like the ladder's Oddish 1 -- the plain
colorscripts sprite (normal and shiny), no background, no animation. Facing: set.json "flip_commons" (read off the
scans; the importer applies the same list). czbatch runs build + verify + sheets/commons.png.

  ..\..\..\.venv\Scripts\python batch_commons.py all
"""
import json

import czbatch
import czlib as P

GROUP = "commons"
TABLE = {e["id"]: dict(kind="common", sprite=e["sprite"]) for e in P.plan()[GROUP]}

if __name__ == "__main__":
    czbatch.main(GROUP, TABLE)
