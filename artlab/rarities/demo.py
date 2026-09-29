"""Render every rarity on ONE scene + sprite (Pikachu over the Celebrations cel25-5 jungle), plus a few on the
other suite3 Pokemon, in suite3's .anim format (play.ps1) with terminal-look GIFs.

  ..\\..\\.venv\\Scripts\\python demo.py              everything
  ..\\..\\.venv\\Scripts\\python demo.py hyper_rare   just some ids (pikachu)
  then:  .\\anim\\play.ps1 hyper_rare

Writes anim/<id>/ (<id>.anim, <id>-term.gif, <id>-sheet.png, <id>-final-term.png), catalog-sheet.png,
generalize-sheet.png.
"""
import json
import shutil
import sys
import time

from PIL import Image, ImageDraw, ImageFont

import effects as E
import scenes

sys.path.insert(0, str(E.HERE.parent / "lib"))
import s3anim as a3  # noqa: E402  (suite3 exporter: .anim bundle, gif, contact sheet)

import artpaths  # noqa: E402
DATA = artpaths.data("rarities")
ANIM = DATA / "anim"
a3.ANIM = ANIM
FONT = "C:/Windows/Fonts/consola.ttf"
OTHERS = {"charmander": ["rare_holo_v", "radiant_rare", "hyper_rare", "reverse_fireworks"],
          "bulbasaur": ["rare_holo_cosmos", "special_illustration_rare", "rare_shiny", "amazing_rare"],
          "squirtle": ["reverse_masterball", "ultra_rare", "rare_rainbow", "rare_prism_star"]}


def render(rid, poke, ctx, suffix=""):
    r = E.rarities()[rid]
    res = E.apply(rid, None, ctx.spr, ctx.off, ctx=ctx)
    assert all(f.shape == res.static.shape for f in res.frames)
    card = rid + suffix
    a3.export(card, f"{poke} {r['label']}" + (" (shiny sprite)" if res.shiny else ""), res.rows(), E.N - 1,
              f"{r['family']} / {res.recipe}: {r['finish']}")
    return Image.open(ANIM / card / f"{card}-final-term.png").convert("RGB"), res


def sheet(items, path, cols, title):
    """items [(label, sub, img)] -> labelled grid"""
    w = max(i.width for _, _, i in items)
    h = max(i.height for _, _, i in items)
    gap, lab = 22, 64
    rows = (len(items) + cols - 1) // cols
    o = Image.new("RGB", (cols * (w + gap) + gap, 90 + rows * (h + lab + gap)), (22, 22, 26))
    d = ImageDraw.Draw(o)
    f1, f2, f0 = ImageFont.truetype(FONT, 26), ImageFont.truetype(FONT, 19), ImageFont.truetype(FONT, 40)
    d.text((gap, 22), title, font=f0, fill=(235, 235, 235))
    for n, (a, b, im) in enumerate(items):
        x = gap + (n % cols) * (w + gap)
        y = 90 + (n // cols) * (h + lab + gap)
        mx = max(8, int(w / 14.5))
        d.text((x, y), a if len(a) <= mx else a[:mx - 1] + "~", font=f1, fill=(240, 240, 240))
        d.text((x, y + 32), b, font=f2, fill=(150, 150, 160))
        o.paste(im, (x, y + lab))
    o.save(path)
    return o


def main():
    only = sys.argv[1:]
    ANIM.mkdir(exist_ok=True)
    shutil.copy(E.HERE.parent / "lib" / "play.ps1", ANIM / "play.ps1")
    R = sorted(E.rarities().values(), key=lambda r: r["order"])
    sc, spr, off = scenes.scene("pikachu")
    ctx = E.Ctx(sc, spr, off)
    items, t0 = [], time.time()
    for r in R:
        if only and r["id"] not in only:
            continue
        im, res = render(r["id"], "pikachu", ctx)
        jp = " [JP]" if r["jp_only"] else ""
        items.append((f"{r['order'] + 1}. {r['label']}{jp}", f"{r['family']} / {r['recipe']}", im))
    print(f"{len(items)} rarities in {time.time() - t0:.0f}s")
    if not only:
        sheet(items, DATA / "catalog-sheet.png", 6,
              "pokeshell rarity catalog: Pikachu over Celebrations 005/025, static renders in rarity order")
        gen = []
        for poke, ids in OTHERS.items():
            sc2, spr2, off2 = scenes.scene(poke)
            c2 = E.Ctx(sc2, spr2, off2)
            for rid in ids:
                im, res = render(rid, poke, c2, suffix=f"_{poke}")
                gen.append((f"{poke}: {E.rarities()[rid]['label']}", E.rarities()[rid]["family"], im))
        sheet(gen, DATA / "generalize-sheet.png", 4, "the same engine on the other suite3 scenes")


if __name__ == "__main__":
    main()
