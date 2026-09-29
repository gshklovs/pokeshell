r"""Animated 30th Celebration cards: 16 frames at 12 fps in suite3's frame format, the evs way. The approved evs
effects (evs/anim.py, loaded by file path) are reused as they are; the new rarities get their own effect,
each imitating the real finish when the card is tilted. The FINAL frame is asserted identical to the static art.

  holo       Rare              (Mew 65)        suite3 / evs Rare Holo: wide rainbow band, starlight glitter
  fireworks  Pikachu Rare      (Pikachu 23)    the bursts over the art AND the yellow border go off in turn
                                               (spark -> burst -> full -> fade), a soft vertical light bar sweeps
  ex         Double Rare       (Umbreon ex 92) evs sunpillar beam pair over window + silver frame, and the
                                               sparkle grain flickers pixel by pixel
  etch       Illustration Rare (Lapras 131)    evs Rare Ultra etch wave, on the IR's lighter art-following lines
  sir        Special Illus.    (Gengar ex 154) evs alt-art brushwork light swing + a broad pink -> cyan pearl sweep
  chrome     Futuristic Rare   (Mewtwo ex 157) the liquid-chrome reflections roll across the metal, a hard
                                               specular line crosses, star flares

  ..\..\..\.venv\Scripts\python p30anim.py [me55-23 ...]
"""
import math
import shutil
import sys

import numpy as np

import p30lib as P
from p30lib import E, L
import p30cards as C

A = P.load_evs("anim", "evs_anim")          # evs/anim.py (its suite3 anim module is A.s3)
A.s3.ANIM = P.DATA / "anim"
N = A.N
lerp = A.lerp


def bg_rgb(c, q, shiny):
    """a frame: float bg image q (0..1) under the static keyed layers (sprite as printed, no deco)"""
    g0, a0 = A.base_arrays(c, shiny)
    bg, _ = A.layers(c)
    return np.where(bg[..., None], q * 255, a0)


def anim_fireworks(c, shiny):
    g0, a0 = A.base_arrays(c, shiny)
    bg, body = A.layers(c)
    FH, FW = c.FH, c.FW
    xx = np.mgrid[0:FH, 0:FW][1].astype(float)
    frames = []
    for f in range(N):
        if f == N - 1:
            frames.append(g0)
            continue
        t = f / (N - 2)
        q = C.fireworks_paint(c.meta["q_pre"], c.meta["bursts"], f, c.meta["skip"])
        a = bg_rgb(c, q, shiny)
        bar = np.exp(-((xx - (-10 + t * (FW + 20))) / 5.0) ** 2)
        hue = C.rainbow_rgb(xx / 40 + t, s=0.5) * 255
        a = np.where(bg[..., None], lerp(a, hue, 0.22 * bar), a)
        a = np.where(body[..., None], lerp(a0, (255, 255, 255), 0.22 * bar * (bar > 0.5)), a)
        frames.append(A.to_frame(a))
    return frames


def anim_ex(c, shiny):
    frames = A.anim_sunpillar(c, shiny)
    q0 = c.meta["q_pre"] * 255
    for f in range(N - 1):
        g = frames[f]
        for (x, y, ph) in c.meta["grain"]:
            if (x, y) in c.cells:
                continue
            k = C.GRAIN_LIFE[(f + ph) % 6]
            col = lerp(np.array(g[y][x], float) * 0.5 + q0[y, x] * 0.5, (255, 255, 255), k)
            g[y][x] = tuple(int(v) for v in np.clip(np.round(col / 4) * 4, 0, 255))
    return frames


def anim_sir(c, shiny):
    frames = A.anim_paint(c, shiny)
    bg, _ = A.layers(c)
    FH, FW = c.FH, c.FW
    yy, xx = np.mgrid[0:FH, 0:FW].astype(float)
    diag, span, w = xx + yy, FW + FH, 16
    for f in range(N - 1):
        t = f / (N - 2)
        dd = diag * 0.8 + yy * 0.2 - (-w * 1.5 + t * (span + 3 * w))
        band = np.exp(-0.5 * (dd / w) ** 2)
        hue = C.PEARL[0] + (C.PEARL[1] - C.PEARL[0]) * np.clip(dd / (2 * w) + 0.5, 0, 1)
        pearl = C.rainbow_rgb(hue, s=0.3) * 255
        a = np.array([[v if v is not None else (0, 0, 0) for v in r] for r in frames[f]], float)
        a = np.where(bg[..., None], lerp(a, pearl, 0.42 * band), a)
        frames[f] = A.to_frame(a)
    return frames


def anim_chrome(c, shiny):
    g0, a0 = A.base_arrays(c, shiny)
    bg, body = A.layers(c)
    FH, FW = c.FH, c.FW
    yy, xx = np.mgrid[0:FH, 0:FW].astype(float)
    pts = A.spark_pts(c, 3, 157)
    d = c.dist()
    rim = (d > 0) & (d <= 1.01)
    frames = []
    for f in range(N):
        if f == N - 1:
            frames.append(g0)
            continue
        t = f / (N - 2)
        q, _ = C.chrome(c.meta["scene"], ph=t)
        dd = (xx + yy) - (-10 + t * (FW + FH + 20))
        q = q + (1 - q) * (0.6 * np.exp(-(dd / 1.2) ** 2) + 0.18 * np.exp(-(dd / 6.0) ** 2))[..., None]
        q[rim] = q[rim] + (np.array((0.8, 1.0, 1.0)) - q[rim]) * 0.45          # the static art's light rim
        a = bg_rgb(c, np.clip(q, 0, 1), shiny)
        spr_a = a0.copy()
        if c.meta.get("sprite_recolour") == "futuristic":           # the tint flows with the reflections
            spr = c.spr
            A0, B0 = c.off
            for j, r in enumerate(spr.rows):
                for i, ch in enumerate(r):
                    if ch in ".k":
                        continue
                    X, Y = 2 * (A0 + i), 2 * (B0 + j)
                    spr_a[Y:Y + 2, X:X + 2] = L.hexrgb(C.fr_colour(spr, ch, i, j, X, Y, t, c.meta["fr_tint"], shiny))
        a = np.where(body[..., None], lerp(spr_a, (255, 255, 255), 0.3 * np.exp(-(dd / 3.0) ** 2)), a)
        frames.append(A.finish_frame(c, a, f, pts, {"L": "#ffffff", "l": "#e0fbff", "j": "#ff9af0"}))
    return frames


KINDS = {**A.KINDS, "fireworks": anim_fireworks, "ex": anim_ex, "sir": anim_sir, "chrome": anim_chrome}
NOTES = {**A.NOTES,
         "holo": "Rare (ME rares are holo): a wide rainbow band sweeps the art box, starlight glitters (evs Rare Holo)",
         "fireworks": "Pikachu Rare: fireworks bursts over the art and the yellow border go off in turn, a soft light bar sweeps",
         "ex": "Double Rare ex: sunpillar beam pair over window + silver frame, the sparkle grain flickers",
         "etch": "Illustration Rare: the light art-following etch lines light up in a rainbow wave (evs etch)",
         "sir": "Special Illustration Rare: light swings across the embossed brushwork + a pink -> cyan pearl sweep",
         "chrome": "Futuristic Rare: chrome reflections roll, the sprite's red-black tint flows with them and pulses, a specular line crosses, star flares"}


def build(ids):
    A.s3.ANIM.mkdir(exist_ok=True)
    shutil.copy(E.LIB / "play.ps1", A.s3.ANIM / "play.ps1")
    for cid in ids:
        c = C.BUILDERS[cid]()
        kind = c.meta.get("anim")
        if not kind:
            print(f"{cid}: {c.meta['rarity']} has no background (plain sprite), no animation")
            continue
        for shiny in (False, True):
            frames = KINDS[kind](c, shiny)
            assert len(frames) == N
            assert frames[N - 1] == c.rgb(shiny), f"{cid}: final frame differs from the static render"
            name = cid + ("_shiny" if shiny else "")
            A.s3.export(name, c.meta["label"] + (" (shiny)" if shiny else ""), frames, N - 1, NOTES[kind])


if __name__ == "__main__":
    build([a for a in sys.argv[1:] if a in C.BUILDERS] or C.ORDER)
