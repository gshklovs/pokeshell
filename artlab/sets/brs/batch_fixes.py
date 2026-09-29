r"""Brilliant Stars audit fixes (ART_METHOD section 16): the clear errors the audit found, each a copy of the owning
row (ladder or group batch) with the one faulty setting overridden, in memory. Highest precedence
(audit/allcards.py): rebuild these ids through THIS module, never through their group batch or the ladder (which
would undo the fix).

  ..\..\..\.venv\Scripts\python batch_fixes.py all          masks + build + anim + verify + sheets/fixes.png

Taste calls (ambiguous poses, busy fills) are NOT changed here; they are listed in <DATA>/brs/audit/REPORT.md.
"""
import importlib.util
import sys

import brsbatch
import brscards as C
import brslib as P

GROUP = "fixes"


def _batch(name):
    spec = importlib.util.spec_from_file_location(f"brsfix_{name}", P.HERE / f"batch_{name}.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[f"brsfix_{name}"] = m
    spec.loader.exec_module(m)
    return m


UNC, RARE_A, V_A, ULTRA, TG_V = (_batch(n) for n in ("uncommon", "rare_a", "v_a", "ultra", "tg_v"))
LADDER = C.LADDER


def fix(src, cid, **over):
    table = src if isinstance(src, dict) else src.TABLE
    return {**table[cid], **over}


def mask_add(src, cid, *shapes):
    """the row's mask with more shapes OR-ed in (rects (x0, y0, x1, y1) or polygons, card px)"""
    table = src if isinstance(src, dict) else src.TABLE
    m = dict(table[cid]["mask"])
    m["add"] = list(m.get("add", [])) + list(shapes)
    return m


def fix_add(src, cid, *shapes, **over):
    return fix(src, cid, mask=mask_add(src, cid, *shapes), **over)


TG19_MASK = dict(TG_V.TABLE["swsh9tg-TG19"]["mask"])
TG19_MASK["cut_after"] = [c if c[0] != (30, 140) else [(30, 300), (65, 300), (70, 450), (30, 480)]
                          for c in TG19_MASK["cut_after"]]

TABLE = {
    # form: the card is Noice Face Eiscue (the ice block shattered, the bare blue head)
    "swsh9-44": fix(RARE_A, "swsh9-44", sprite="eiscue-noice"),
    # ghosts of the real Pokemon left in the fill: the mask grown over the missed parts
    "swsh9-2": fix_add(UNC, "swsh9-2", (140, 130, 220, 225), (525, 135, 610, 305)),          # leaf tips
    "swsh9-5": fix_add(UNC, "swsh9-5", (60, 195, 115, 295)),                                 # head leaf / wing edge
    "swsh9-25": fix_add(UNC, "swsh9-25", (110, 335, 195, 435)),                              # hand and forearm
    "swsh9-39": fix_add(UNC, "swsh9-39", (110, 325, 225, 465)),                              # tail wisps
    "swsh9-55": fix_add(UNC, "swsh9-55", (230, 360, 300, 445)),                              # lower-left star point
    "swsh9-93": fix_add(UNC, "swsh9-93", (135, 345, 205, 425), (435, 415, 515, 485)),        # claws
    "swsh9-118": fix_add(UNC, "swsh9-118", (595, 135, 675, 295), (120, 255, 165, 295)),      # wing tips
    "swsh9-48": fix_add(V_A, "swsh9-48", (100, 105, 260, 320)),                              # the zig-zag tail
    "swsh9-152": fix_add(LADDER, "swsh9-152", (30, 325, 85, 395), (565, 85, 635, 165)),      # wing tips
    "swsh9-154": fix_add(LADDER, "swsh9-154", (145, 145, 205, 225)),                         # wing tip by the head
    "swsh9-155": fix_add(ULTRA, "swsh9-155", (30, 440, 265, 550), (375, 555, 495, 615),      # tail + lower fin
                         (495, 85, 625, 145)),                                               # top-right fin tip
    "swsh9-157": fix_add(ULTRA, "swsh9-157", (495, 155, 595, 220), (645, 340, 720, 425)),    # ear tip, tail corner
    "swsh9-161": fix_add(ULTRA, "swsh9-161", [(560, 285), (600, 285), (630, 345), (608, 362), (560, 330)]),  # plume
    "swsh9tg-TG21": fix_add(TG_V, "swsh9tg-TG21", [(25, 380), (70, 365), (130, 410), (190, 428), (262, 452),
                                                   (200, 470), (130, 510), (90, 540), (40, 570), (30, 600)]),  # G-Max fist
    "swsh9tg-TG19": fix(TG_V, "swsh9tg-TG19", mask=TG19_MASK),                            # red hair tips, top left
}

if __name__ == "__main__":
    brsbatch.main(GROUP, TABLE)
