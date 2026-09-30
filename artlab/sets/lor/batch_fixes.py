r"""Lost Origin audit fixes (ART_METHOD section 16): the clear errors the audit found (audit A / B / C reviewers, see
audit/REPORT.md), each a copy of the owning row (ladder or group batch) with the one faulty setting overridden, in
memory. Highest precedence (audit/allcards.py): rebuild these ids through THIS module, never through their group
batch or the ladder (which would undo the fix).

  ..\..\..\.venv\Scripts\python batch_fixes.py all          masks + build + anim + verify + sheets/fixes.png

Taste calls (ambiguous poses, busy fills) are NOT changed here; they are listed in <DATA>/lor/audit/REPORT.md.
The Shellos 39 facing fix is set.json "flip_commons" (commons are flipped there, not in a row); it is rebuilt here too.
"""
import importlib.util
import sys

import lorbatch
import lorcards as C
import lorlib as P
import lormasks as CM

GROUP = "fixes"
EVO = (0, 58, 425, 124)          # the whole "Evolves from ..." plate (STAGE_BOX stops at x 312, the plate at ~x 420)


def _batch(name):
    spec = importlib.util.spec_from_file_location(f"lorfix_{name}", P.HERE / f"batch_{name}.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[f"lorfix_{name}"] = m
    spec.loader.exec_module(m)
    return m


RARE_A, UNC_B, V, COM_A = (_batch(n) for n in ("rare_a", "uncommon_b", "v", "commons_a"))
LADDER = C.LADDER


def fix(src, cid, **over):
    table = src if isinstance(src, dict) else src.TABLE
    return {**table[cid], **over}


def add_box(src, cid, *boxes):
    table = src if isinstance(src, dict) else src.TABLE
    return fix(src, cid, boxes=tuple(table[cid].get("boxes", ())) + boxes)


def grow(src, cid, *shapes):
    """the row's own mask (any recipe, custom fn masks too) with more shapes OR-ed in (rects or polygons, card px)"""
    table = src if isinstance(src, dict) else src.TABLE
    spec = table[cid]["mask"]

    def fn(cid, spec=spec):
        m = CM.make(cid, spec)
        sh = m.shape
        for s in shapes:
            m = m | CM.shape(sh, s)
        return m
    return fix(src, cid, mask=dict(fn=fn))


TABLE = {
    # "Evolves from" plate ghost (a pale smear at the top of the art): the whole plate boxed out
    **{cid: add_box(RARE_A, cid, EVO) for cid in ("swsh11-5", "swsh11-10", "swsh11-22", "swsh11-32", "swsh11-34",
                                                  "swsh11-55", "swsh11-61", "swsh11-63", "swsh11-73", "swsh11-78")},
    "swsh11-2": add_box(LADDER, "swsh11-2", EVO),
    "swsh11-53": add_box(LADDER, "swsh11-53", EVO),
    "swsh11-66": add_box(LADDER, "swsh11-66", EVO),
    # ghosts of the real Pokemon left in the fill: the mask grown over the missed parts
    "swsh11tg-TG16": grow(LADDER, "swsh11tg-TG16",                                            # ear tips
                          [(380, 160), (440, 160), (450, 238), (560, 230), (690, 230), (706, 255), (560, 302),
                           (470, 338), (420, 300), (380, 230)]),
    "swsh11-133": grow(UNC_B, "swsh11-133", (240, 105, 392, 160)),                            # the second horn
    "swsh11-58": grow(V, "swsh11-58", [(355, 96), (450, 96), (425, 180), (410, 265), (385, 265), (372, 215)]),  # spike
    "swsh11-82": grow(V, "swsh11-82", [(300, 95), (420, 95), (395, 150), (355, 165), (375, 255), (330, 262),
                                       (300, 200)], (415, 330, 640, 425)),                    # the heart-ribbon tail
    # facing: set.json flip_commons now lists Shellos 39 (both Shellos on the card face right)
    "swsh11-39": fix(COM_A, "swsh11-39"),
}

if __name__ == "__main__":
    lorbatch.main(GROUP, TABLE)
