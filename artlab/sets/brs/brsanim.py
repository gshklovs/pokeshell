r"""Animated Brilliant Stars cards: 16 frames at 12 fps (lib/s3anim's format), the evs effects (evs/anim.py, loaded by
file path) and cz's vstar / gallery loops, reused as they are. The FINAL frame is asserted identical to the
static art; only the background / foil moves, the sprite takes at most a light gloss (the Rare Rainbow's
rainbow sprite flows with the ground, as evs Leafeon VMAX 204).

  holo       Rare Holo             evs: a wide rainbow band sweeps the art box, starlight glitters
  etch       Rare Ultra full art   evs: the fingerprint lines light up in a rainbow wave along the contours
  rainbow    Rare Rainbow          evs: the hue flows along the diagonal over ground AND sprite, lines flash
  sunpillar  Rare Holo V / VMAX    evs: 45-degree rainbow beam pair over window + frame (VMAX grooves catch it)
  paint      alt-art paintings     evs: the light swings across the embossed brushwork, soft sheen, stars
  gold       Rare Secret gold      evs: 45-degree metallic sheen over the faceted gold, glitter, star flares
  vstar      Rare Holo VSTAR  cz:  the VMAX sunpillar loop + a gold pulse running out along the star-crest rays
  gallery    Trainer Gallery  cz:  the light swings gently over the brushwork, a vertical pastel band sweeps
                                   left -> right and the linen threads glint inside it

  ..\..\..\.venv\Scripts\python brsanim.py [ids]
"""
import math
import shutil
import sys

import numpy as np

import brslib as P
from brslib import E, L
import brscards as C

A = P.load_evs("anim", "evs_anim")
A.s3.ANIM = P.DATA / "anim"
N = A.N
lerp = A.lerp


def q4(col):
    return tuple(int(v) for v in np.clip(np.round(np.asarray(col, float) / 4) * 4, 0, 255))


def anim_vstar(c, shiny):
    frames = A.anim_sunpillar(c, shiny)
    rays = c.meta["rays"]
    r = c.meta["ray_r"]
    rmax = float(r[rays].max()) if rays.any() else 1.0
    ys, xs = np.nonzero(rays)
    gold = np.array((255, 214, 110), float)
    for f in range(N - 1):
        t = f / (N - 2)
        front = -8 + t * (rmax + 16)
        g = frames[f]
        for x, y in zip(xs, ys):
            if (x, y) in c.cells:
                continue
            k = math.exp(-((r[y, x] - front) / 5.0) ** 2)
            if k < 0.02:
                continue
            g[y][x] = q4(lerp(np.array(g[y][x], float), gold, 0.75 * k) + 40 * k)
    return frames


def anim_gallery(c, shiny):
    g0, a0 = A.base_arrays(c, shiny)
    bg, body = A.layers(c)
    FH, FW = c.FH, c.FW
    h = c.meta["height"]
    gy, gx = np.gradient(h)
    wv = c.meta["weave"]

    def relief(theta):
        return np.clip(-(gx * math.cos(theta) + gy * math.sin(theta)) * 1.6, -0.2, 0.2)

    base_th = math.atan2(-1.3, -1.0)
    r0 = relief(base_th)
    lumv = a0 @ A.W_LUM / 255
    pts = A.spark_pts(c, 4, 31)
    frames = []
    for f in range(N):
        if f == N - 1:
            frames.append(g0)
            continue
        t = f / (N - 2)
        dr = relief(base_th + math.sin(t * 2 * math.pi) * 1.0) - r0
        a = a0 + (dr * (0.35 + 0.65 * lumv) * 255 * 2.0)[..., None]
        band, hue = C.gallery_sheen(FW, FH, -0.2 * FW + t * 1.45 * FW, 0.11 * FW, t)
        a = np.where(bg[..., None], lerp(a, hue * 255, 0.3 * band), a0)
        a = np.where((bg & wv)[..., None], lerp(a, (255, 255, 255), 0.22 * band), a)
        a = np.where(body[..., None], lerp(a0, (255, 255, 255), 0.12 * band), a)
        frames.append(A.finish_frame(c, a, f, pts, {"L": "#ffffff", "l": "#fff2fb", "j": "#bfe8ff"}))
    return frames


KINDS = {**A.KINDS, "vstar": anim_vstar, "gallery": anim_gallery}
NOTES = {**A.NOTES,
         "vstar": "Rare Holo VSTAR: sunpillar beam pair over window + platinum-gold frame (grooves catch it), a gold pulse runs out along the star-crest rays",
         "gallery": "Trainer Gallery: light swings over the brushwork, a vertical pastel band sweeps across, the linen threads glint"}


def build(ids):
    A.s3.ANIM.mkdir(exist_ok=True)
    shutil.copy(E.LIB / "play.ps1", A.s3.ANIM / "play.ps1")
    for cid in ids:
        c = C.BUILDERS[cid]()
        kind = c.meta.get("anim")
        if not kind:
            print(f"{cid}: {c.meta['rarity']} is non-foil, no animation")
            continue
        for shiny in (False, True):
            frames = KINDS[kind](c, shiny)
            assert len(frames) == N
            assert frames[N - 1] == c.rgb(shiny), f"{cid}: final frame differs from the static render"
            name = cid + ("_shiny" if shiny else "")
            A.s3.export(name, c.meta["label"] + (" (shiny)" if shiny else ""), frames, N - 1, NOTES[kind])


if __name__ == "__main__":
    build([a for a in sys.argv[1:] if a in C.BUILDERS] or C.ORDER)
