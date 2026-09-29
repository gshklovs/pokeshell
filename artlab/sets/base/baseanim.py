r"""Animated Base Set cards: 16 frames at 12 fps, the evs way (evs/anim.py loaded by file path). Only the Rare Holo
is foil in Base Set; its loop is the approved `holo` loop (a wide rainbow band sweeps the art box, starlight
glitters, sparkles twinkle, a light gloss on the sprite) on the WotC starlight foil, where the starbursts flare as
the band passes. The FINAL frame is asserted identical to the static art (normal and shiny).

  wotc   Rare Holo   (Charizard 4)   the band sweeps; starbursts flare in it and at their own phase; specks glitter

  ..\..\..\.venv\Scripts\python baseanim.py [base1-4 ...]
"""
import shutil
import sys

import numpy as np

import baselib as P
from baselib import E
import basecards as C

A = P.load_evs("anim", "evs_anim")          # evs/anim.py (its suite3 anim module is A.s3)
A.s3.ANIM = P.DATA / "anim"
N = A.N
lerp = A.lerp
WHITE = (255, 255, 255)


def anim_wotc(c, shiny):
    g0, a0 = A.base_arrays(c, shiny)
    bg, body = A.layers(c)
    FH, FW = c.FH, c.FW
    yy, xx = np.mgrid[0:FH, 0:FW].astype(float)
    q0 = c.bgq.astype(float)                      # the static foil (with its bursts and specks)
    qp = c.meta["q_pre"] * 255                    # the foil under the bursts / specks
    ctr, arm, specks = c.meta["burst_ctr"], c.meta["burst_arm"], c.meta["specks"]
    phase = np.zeros((FH, FW), int)
    for x, y, r, ph in c.meta["bursts"]:
        phase[max(0, y - r):y + r + 1, max(0, x - r):x + r + 1] = ph
    rnd = np.random.default_rng(4)
    sp_phase = rnd.integers(0, 6, (FH, FW))
    band = 22.0
    dd = xx + yy                                  # the approved holo band's 45-degree sweep
    span = FW + FH + band
    pts = A.spark_pts(c, 4, 7)
    frames = []
    for f in range(N):
        if f == N - 1:
            frames.append(g0)
            continue
        ctr_d = -band + f * span / (N - 2)
        u = (dd - ctr_d) / band
        inb = (u >= 0) & (u < 1)
        core = np.where(inb, 1 - np.abs(u - 0.5) * 2, 0.0)
        hue = C.rainbow_rgb(u * 1.2 + (xx - yy) / 90, s=0.55) * 255
        a = np.where(bg[..., None], q0, a0)
        a = np.where((bg & inb)[..., None], lerp(a, hue, 0.18 + 0.4 * core), a)
        # starbursts: flare white in the band's core, and once per loop at their own phase
        own = ((f - phase) % N) < 2
        k = np.clip(0.9 * core + 0.6 * own, 0, 1)
        a = np.where((bg & ctr)[..., None], lerp(a, WHITE, np.maximum(k, 0.85)), a)
        a = np.where((bg & arm)[..., None], lerp(np.where(inb[..., None], a, q0), WHITE, 0.2 + 0.6 * k), a)
        # starlight specks glitter in waves (holo: white, dimmed, back)
        kk = (f + sp_phase) % 6
        a = np.where((bg & specks & (kk == 0))[..., None], WHITE, a)
        a = np.where((bg & specks & (kk == 3))[..., None], lerp(qp, (40, 40, 60), 0.4), a)
        a = np.where((body & (core > 0.5))[..., None], lerp(a0, WHITE, 0.28 * core ** 2), a)
        frames.append(A.finish_frame(c, a, f, pts, C.SPARK_PAL))
    return frames


KINDS = {**A.KINDS, "wotc": anim_wotc}
NOTES = {**A.NOTES,
         "wotc": "Rare Holo (WotC starlight): a wide rainbow band sweeps the art box, the starbursts flare in it and "
                 "at their own phase, specks glitter, sparkles twinkle"}


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
