r"""Crown Zenith audit fixes (ART_METHOD section 16): the clear errors the audit found, each a copy of the owning
batch's row with the one faulty setting overridden, in memory. Highest precedence (audit/allcards.py): rebuild
these ids through THIS module, never through their group batch (which would undo the fix).

  ..\..\..\.venv\Scripts\python batch_fixes.py all          masks + build + anim + verify + sheets/fixes.png

Taste calls (ambiguous poses, busy fills, which characters stay as scenery) are NOT changed here; they are
listed in <DATA>/cz/audit/REPORT.md for the user.
"""
import importlib.util
import sys

import czbatch
import czlib as P

GROUP = "fixes"


def _batch(name):
    spec = importlib.util.spec_from_file_location(f"czfix_{name}", P.HERE / f"batch_{name}.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[f"czfix_{name}"] = m
    spec.loader.exec_module(m)
    return m


V, VSTAR, UNC, RARE = _batch("v"), _batch("vstar"), _batch("uncommon"), _batch("rare")
TGA, GGVSTAR = _batch("gg_tg_a"), _batch("gg_vstar")


def fix(src, cid, **over):
    row = {**src.TABLE[cid], **over}
    return row


def mask_add(src, cid, *polys):
    m = dict(src.TABLE[cid]["mask"])
    m["add"] = list(m.get("add", [])) + list(polys)
    return m


TABLE = {
    # facing: the real Pokemon faces the other way from the placed sprite
    "swsh12pt5-93": fix(UNC, "swsh12pt5-93", flip=True),          # Bisharp lunges left
    "swsh12pt5-44": fix(RARE, "swsh12pt5-44", flip=True),         # Luxray: head upper right, mouth open right
    "swsh12pt5-118": fix(RARE, "swsh12pt5-118", flip=True),       # Gumshoos: head upper right
    "swsh12pt5gg-GG03": fix(TGA, "swsh12pt5gg-GG03", flip=True),  # Magmortar aims left at the campfire
    "swsh12pt5gg-GG44": fix(GGVSTAR, "swsh12pt5gg-GG44", flip=True),  # Mewtwo lunges right at Charizard
    # form: both VSTARs wear the crowned armour on the scan (as 94 / 95 and 97 / 98 do)
    "swsh12pt5-96": fix(VSTAR, "swsh12pt5-96", sprite="zacian-crowned", flip=True, **VSTAR.fit(46, 560)),
    "swsh12pt5-99": fix(VSTAR, "swsh12pt5-99", sprite="zamazenta-crowned", flip=False, **VSTAR.fit(40, 525)),
    # ghosts of the real Pokemon left in the fill
    "swsh12pt5-38": fix(V, "swsh12pt5-38", mask=mask_add(V, "swsh12pt5-38",
                                                         [(545, 380), (715, 380), (715, 560), (545, 560)],   # front paw
                                                         [(195, 140), (305, 130), (305, 260), (195, 260)])),  # ribbon
    "swsh12pt5-60": fix(V, "swsh12pt5-60", mask=mask_add(V, "swsh12pt5-60",
                                                         [(500, 460), (712, 460), (712, 575), (500, 575)])),  # foot
    "swsh12pt5-116": fix(V, "swsh12pt5-116", mask=mask_add(V, "swsh12pt5-116",
                                                           [(585, 130), (715, 130), (715, 610), (585, 610)])),  # ear, fur, arm
}

if __name__ == "__main__":
    czbatch.main(GROUP, TABLE)
