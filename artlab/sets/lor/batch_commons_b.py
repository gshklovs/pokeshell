r"""Lost Origin group "commons_b": the Commons, built exactly like the ladder's Pikachu 52 -- the plain
colorscripts sprite (normal and shiny), no background, no animation. Facing: set.json "flip_commons" (read off the
scans; the importer applies the same list). Forms checked on the scans.

  C:\Users\grego\repos\pokeshell\.venv\Scripts\python batch_commons_b.py all
"""
import lorbatch
import lorlib as P

GROUP = "commons_b"
TABLE = {e["id"]: dict(kind="common", sprite=e["sprite"]) for e in P.plan()[GROUP]}

if __name__ == "__main__":
    lorbatch.main(GROUP, TABLE)
