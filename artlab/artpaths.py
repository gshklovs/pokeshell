"""Where artlab's code finds its data (docs/ART_METHOD.md, "Code and data").

artlab/ holds only code and our own recipes (tracked). Everything copyrighted or generated lives in the DATA root,
one folder per set, never committed:

  <DATA>/<set>/ref/        the real card scans (pokemontcg.io hires PNGs)
  <DATA>/<set>/cards/      card JSON with the card text (CARD_FORMAT) + cards/api/ (the raw API records)
  <DATA>/<set>/masks/      the real-Pokemon masks (derived from the scans)
  <DATA>/<set>/work/       caches (rembg-<model>-<id>.png), coordinate grids, audit scratch
  <DATA>/<set>/art/ out/ anim/ sheets/   the outputs: ART_FORMAT JSON, renders, 16-frame loops, review sheets

DATA defaults to <repo>/style-lab (git-excluded), which is also where tools/build_realcards.py imports batches from
(`--lab`). Override it with the ARTLAB_DATA environment variable, e.g. to rebuild into an isolated folder.
The pokemon-colorscripts sprites come from <repo>/vendor (override: POKESHELL_VENDOR).
"""
import os
from pathlib import Path

ARTLAB = Path(__file__).resolve().parent
ROOT = ARTLAB.parent                     # the pokeshell checkout
LIB = ARTLAB / "lib"
SETS = ARTLAB / "sets"
TOOLS = ROOT / "tools"                   # build_art.py (to_ansi), render_ansi.py (render)
DATA = Path(os.environ.get("ARTLAB_DATA") or ROOT / "style-lab").resolve()
VENDOR = Path(os.environ.get("POKESHELL_VENDOR") or ROOT / "vendor").resolve()


def data(name):
    """the data folder of one set (or of a lab area such as 'suite', 'rarities')"""
    return DATA / name


def code(name):
    """the code folder of one set: artlab/sets/<name>"""
    return SETS / name
