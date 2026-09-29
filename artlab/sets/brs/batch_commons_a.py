r"""Brilliant Stars group "commons_a": the remaining Commons, built exactly like the ladder's Turtwig 6 -- the plain
colorscripts sprite (normal and shiny), no background, no animation. Facing: set.json "flip_commons" (read off the
scans; the importer applies the same list). Forms checked on the scans: every plan sprite is the card's own form
(Burmy 9 is the Grass card, plant cloak = "burmy"; Castform 116 is the normal form).

  C:\Users\grego\repos\pokeshell\.venv\Scripts\python batch_commons_a.py all
"""
import brsbatch
import brslib as P

GROUP = "commons_a"
TABLE = {e["id"]: dict(kind="common", sprite=e["sprite"]) for e in P.plan()[GROUP]}

if __name__ == "__main__":
    brsbatch.main(GROUP, TABLE)
