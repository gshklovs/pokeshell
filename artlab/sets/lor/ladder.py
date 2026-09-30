r"""The Lost Origin ladder: one real card per printed rarity and finish (lorcards.LADDER), run through the shared
pipeline (masks -> build -> anim -> verify -> sheets/ladder.png). Sizes go to sheets/ladder-sizes.json.

  ..\..\..\.venv\Scripts\python ladder.py masks|quick|all [ids]
"""
import lorbatch
import lorcards as C

if __name__ == "__main__":
    lorbatch.main("ladder", C.LADDER)
