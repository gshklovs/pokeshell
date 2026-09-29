"""Demo inputs for effects.py: a clean card scene at GRID resolution (Pokemon inpainted away) + the
colorscripts sprite + its offset (sprite px). Scenes are cached in work/ as .npy.

  scene('pikachu') -> (scene float (FH, FW, 3), Sprite, (A, B))
"""
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "lib"))
import s3lib as L  # noqa: E402
import tiers  # noqa: E402
import artpaths  # noqa: E402

WORK = artpaths.data("rarities") / "work"

# name: (card ref, mask, x0, y0, S, W, H, clean kwargs, sprite(flip), anchor kwargs)
SCENES = {
    # the suite3 'holo' backdrop: Celebrations 005/025, Arita's jungle
    "pikachu": ("pikachu/ref/cel25_5", "pikachu_holo", 26, 96, 22, 32, 27,
                dict(grow=5, boxes=((10, 440, 200, 580), (230, 620, 380, 700), (530, 620, 640, 700)),
                     win=(30, 0, 704, 1024), cgrow=dict(reach=24, tol=16)),
                ("pikachu", False), dict(dx=3)),
    "charmander": ("charmander/ref/sv3pt5_168", "charmander_fullart", 34, 95, 16, 36, 28, dict(grow=4),
                   ("charmander", True), dict(dy=1)),
    "bulbasaur": ("bulbasaur/ref/sv3pt5_166", "bulbasaur_fullart", 40, 92, 12, 38, 28,
                  dict(grow=5, cgrow=dict(reach=16, tol=12)), ("bulbasaur", False), {}),
    "squirtle": ("squirtle/ref/sv3pt5_170", "squirtle_fullart", 40, 112, 16, 40, 30, dict(grow=5),
                 ("squirtle", False), dict(dy=-2)),
}


def scene(name):
    ref, mk, x0, y0, S, W, H, ck, (sp, flip), ak = SCENES[name]
    spr = L.Sprite(sp, flip)
    WORK.mkdir(exist_ok=True)
    cache = WORK / f"scene-{name}.npy"
    if cache.exists():
        a = np.load(cache)
    else:
        rgb, _ = L.clean_card(ref, mk, **ck)
        a = L.sample(rgb, x0, y0, S / 2, 2 * W, 2 * H, resample=L.Image.BOX if name == "pikachu" else L.Image.LANCZOS)
        np.save(cache, a)
    A, B = L.anchor(mk, x0, y0, S, spr, **ak)
    A = max(0, min(W - spr.w, A))
    B = max(0, min(H - spr.h, B))
    return a, spr, (A, B)
