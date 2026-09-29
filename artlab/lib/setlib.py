"""The per-set lib pattern: a new set runs the approved Evolving Skies pipeline (artlab/sets/evs) unchanged, with
evlib's scan / mask / card / output paths pointed at the new set's data folder.

evs is the reference set: its modules hold the approved recipes every later set reuses (evcards: the ladder
builders, silver_frame, fingerprint, rainbow_sprite, colour_blend ...; evcards2: window_rgb, matte, vmax_texture;
anim.py: the effect loops; build.py: art_json / render). A new set's `<set>lib.py` (see artlab/sets/p30/p30lib.py,
and artlab/sets/_template/) does:

    sys.path.insert(0, <artlab/sets/evs>)
    import evlib as E            # (puts artlab/lib first on sys.path)
    import setlib
    DATA = setlib.use_set(E, "<set folder>", "<scan prefix>")   # e.g. ("p30", "me55")

after which E.card_img / E.clean / E.mask / E.anchor / E.region and evs build.render read and write the new set.
evs anim.py / build.py / verify.py must be loaded BY FILE PATH (setlib.load / p30lib.load_evs): a plain
`import anim` / `build` / `verify` can pick up another module of the same name.
"""
import importlib.util
import sys

import artpaths


def use_set(E, name, prefix, data=None):
    """point evlib (module E) at <DATA>/<name>/: scans ref/<prefix>_<number>.png, masks/, out/, work/, cards/, art/.
    Returns the set's data folder. (E.DATA, where evs's own sheets / sizes / anim go, is left alone.)"""
    d = data or artpaths.data(name)
    E.REF = d / "ref"
    E.MASKS = d / "masks"
    E.OUT = d / "out"
    E.WORK = d / "work"
    E.CARDS = d / "cards"
    E.ART = d / "art"

    def ref_path(cid):
        return E.REF / f"{prefix}_{E.num(cid)}.png"

    E.ref_path = ref_path                  # evlib.card_img / clean / region all go through this
    return d


def load(path, alias):
    """load a module by file path under a private name (registered in sys.modules)"""
    spec = importlib.util.spec_from_file_location(alias, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[alias] = m
    spec.loader.exec_module(m)
    return m
