r"""The Brilliant Stars ladder: one real card per printed rarity and finish (brscards.LADDER), run through the shared
pipeline (masks -> build -> anim -> verify -> sheets/ladder.png). Sizes go to sheets/ladder-sizes.json.

  ..\..\..\.venv\Scripts\python ladder.py masks|quick|all [ids]
"""
import brsbatch
import brscards as C

if __name__ == "__main__":
    brsbatch.main("ladder", C.LADDER)
