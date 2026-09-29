r"""Animated Hidden Fates cards: 16 frames at 12 fps, the evs way (evs/anim.py loaded by file path; its kinds
reused as they are). The new rarities get their own loop, each imitating the real finish when the card is tilted.
The FINAL frame is asserted identical to the static art (normal and shiny).

  holo     Rare Holo      (Vaporeon 18)       evs Rare Holo: wide rainbow band, starlight glitter
  gxweb    Rare Holo GX   (Charizard-GX 9)    NEW: a soft rainbow sheen sweeps the art and the silver frame; the
                                              GX web lines inside it light up in rainbow, a faint counter-sheen
  vault    Rare Shiny     (Charmander SV6)    NEW: a narrow silver-white specular band crosses the vault foil with
                                              thin cyan / pink prismatic fringes, the embossed stars catch it, the
                                              glitter px flash one by one, the 4-point stars twinkle
  vaultgx  Rare Shiny GX  (Charizard-GX SV49) NEW: the step above: a silver beam pair over the foil AND the frame,
                                              the etched lines flash along the main beam, glitter, big star flares
  gold     Rare Secret    (Tapu Koko-GX SV93) evs gold: metallic sheen over the faceted gold, glitter, flares

  ..\..\..\.venv\Scripts\python hfanim.py [sm115-9 ...]
"""
import math
import shutil
import sys

import numpy as np

import hflib as P
from hflib import E, L
import hfcards as C

A = P.load_evs("anim", "evs_anim")          # evs/anim.py (its suite3 anim module is A.s3)
A.s3.ANIM = P.DATA / "anim"
N = A.N
lerp = A.lerp


def anim_gxweb(c, shiny):
    g0, a0 = A.base_arrays(c, shiny)
    bg, body = A.layers(c)
    FH, FW = c.FH, c.FW
    yy, xx = np.mgrid[0:FH, 0:FW].astype(float)
    web, whue = c.meta["web"], c.meta["web_hue"]
    ring = c.meta["frame_ring"]
    band = 22.0
    d1 = xx * 0.8 + yy                            # the sheen runs steeper than the V's 45 degrees
    span = FW * 0.8 + FH + 2 * band
    pts = A.spark_pts(c, 3, 19)
    frames = []
    for f in range(N):
        if f == N - 1:
            frames.append(g0)
            continue
        t = f / (N - 2)
        u = (d1 - (-band + t * span)) / band
        k = np.exp(-(u * 1.6) ** 2)
        k2 = np.exp(-(((xx - yy * 0.6) - (FW - t * (FW + FH * 0.6))) / (band * 0.8)) ** 2) * 0.35
        hue = C.rainbow_rgb(u * 0.6 + xx / 180 + 0.2, s=0.5) * 255
        a = a0.copy()
        a = np.where(bg[..., None], lerp(a, hue, 0.22 * k + 0.08 * k2), a)
        whc = C.rainbow_rgb(whue + t * 0.8, s=0.7) * 255
        a = np.where((web & bg)[..., None], lerp(a, lerp(whc, (255, 255, 255), 0.25), np.clip(0.85 * k + 0.3 * k2, 0, 1)), a)
        a = np.where((ring & bg)[..., None], lerp(a, (255, 255, 255), 0.35 * k), a)
        a = np.where((body & (k > 0.6))[..., None], lerp(a0, (255, 255, 255), 0.2 * k), a)
        frames.append(A.finish_frame(c, a, f, pts, {"L": "#ffffff", "l": "#e8f2ff", "j": "#9fd0ff"}))
    return frames


def _glitter(a, a0, c, f):
    for (x, y, ph) in c.meta["glitter"]:
        if (x, y) in c.cells:
            continue
        k = C.GLINT_LIFE[(f - ph) % 16]
        a[y, x] = lerp(c.meta["q_pre"][y, x] * 255, (255, 255, 255), k)
    return a


def anim_vault(c, shiny):
    g0, a0 = A.base_arrays(c, shiny)
    bg, body = A.layers(c)
    FH, FW = c.FH, c.FW
    yy, xx = np.mgrid[0:FH, 0:FW].astype(float)
    st = c.meta["star_map"]
    q0 = c.meta["q_pre"] * 255
    band = 7.0
    span = FW + FH + 6 * band
    pts = A.spark_pts(c, 2, 23)
    frames = []
    for f in range(N):
        if f == N - 1:
            frames.append(g0)
            continue
        t = f / (N - 2)
        dd = (xx + yy) - (-3 * band + t * span)
        k = np.exp(-(dd / band) ** 2)
        fr_c = np.exp(-((dd + 1.6 * band) / (0.6 * band)) ** 2)                 # cyan fringe ahead
        fr_p = np.exp(-((dd - 1.6 * band) / (0.6 * band)) ** 2)                 # pink fringe behind
        a = np.where(bg[..., None], q0, a0)
        a = np.where(bg[..., None], lerp(a, (255, 255, 255), 0.55 * k * (0.45 + 0.55 * st)), a)
        a = np.where(bg[..., None], lerp(a, (150, 235, 255), 0.22 * fr_c), a)
        a = np.where(bg[..., None], lerp(a, (255, 170, 230), 0.18 * fr_p), a)
        a = _glitter(a, a0, c, f)
        a = np.where(body[..., None], lerp(a0, (255, 255, 255), 0.18 * k * (k > 0.5)), a)
        frames.append(A.finish_frame(c, a, f, pts, C.VAULT_STAR))
    return frames


def anim_vaultgx(c, shiny):
    g0, a0 = A.base_arrays(c, shiny)
    bg, body = A.layers(c)
    FH, FW = c.FH, c.FW
    yy, xx = np.mgrid[0:FH, 0:FW].astype(float)
    q0 = c.meta["q_pre"] * 255
    etch = c.meta["etch"]
    ring = c.meta["frame_ring"]
    band = 14.0
    span = FW + FH + 2 * band
    pts = A.spark_pts(c, 3, 29)
    frames = []
    for f in range(N):
        if f == N - 1:
            frames.append(g0)
            continue
        t = f / (N - 2)
        u1 = ((xx + yy) - (-band + t * span)) / band
        k1 = np.clip(1 - np.abs(u1 * 1.6), 0, 1)
        u2 = ((xx - yy) - (FW + band - t * (FW + FH + 2 * band) * 0.9)) / (band * 0.7)
        k2 = np.clip(1 - np.abs(u2 * 2), 0, 1) * 0.4
        prism = C.rainbow_rgb(u1 * 0.5 + 0.55, s=0.28) * 255                    # a whisper of prism in the silver
        a = np.where(bg[..., None], q0, a0)
        a = np.where(bg[..., None], lerp(a, lerp(prism, (255, 255, 255), 0.5), 0.42 * k1 + 0.25 * k2), a)
        a = np.where((etch & bg)[..., None], lerp(a, (255, 255, 255), 0.8 * k1), a)
        a = np.where((ring & bg)[..., None], lerp(a, (255, 255, 255), 0.45 * k1), a)
        a = _glitter(a, a0, c, f)
        a = np.where((body & (k1 > 0.55))[..., None], lerp(a0, (255, 255, 255), 0.22 * k1), a)
        frames.append(A.finish_frame(c, a, f, pts, C.VAULT_STAR))
    return frames


KINDS = {**A.KINDS, "gxweb": anim_gxweb, "vault": anim_vault, "vaultgx": anim_vaultgx}
NOTES = {**A.NOTES,
         "holo": "Rare Holo: a wide rainbow band sweeps the art box, starlight glitters (evs Rare Holo)",
         "gxweb": "Rare Holo GX: a rainbow sheen sweeps art + silver frame, the GX web lines light up along it",
         "vault": "Rare Shiny (Shiny Vault): a silver specular band with prismatic fringes crosses the vault foil, the stars catch it, glitter flashes",
         "vaultgx": "Rare Shiny GX: a silver beam pair over the etched vault foil and frame, the etch flashes, glitter, star flares",
         "gold": "Rare Secret gold: 45-degree metallic sheen over the faceted gold, glitter, star flares"}


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
