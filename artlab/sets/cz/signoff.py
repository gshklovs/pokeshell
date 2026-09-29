r"""The sign-off sheet for the rarities new in Crown Zenith (the user approves each before it goes live):
one row per example card, real card | ours | ours + text half (| ours shiny, for Radiant: the real print is the
shiny Pokemon), plus one animated GIF per example: the real card beside our 16-frame loop.

  ..\..\..\.venv\Scripts\python signoff.py        -> sheets/signoff.png, sheets/signoff-<id>.gif
"""
import json

from PIL import Image, ImageDraw, ImageFont, ImageSequence

import czlib as P
from czlib import E

ROWS = [
    ("Rare Holo VSTAR (NEW)", "swsh12pt5-14", "VMAX scene + grooves, platinum-gold grooved frame, gold star-crest rays; anim vstar (sunpillar + gold ray pulse); skin vstar-crest"),
    ("Rare Holo VSTAR, Galarian Gallery", "swsh12pt5gg-GG35", "the approved alt-art painting (Umbreon 215) at the VSTAR tier; anim paint; skin vstar-crest"),
    ("Radiant Rare (NEW)", "swsh12pt5-20", "silver log-spiral crosshatch burst from the Pokemon, glints at the crossings, thin light frame; anim radiant; skin radiant. QUESTION: the real card prints the SHINY Pokemon (last panel = our shiny roll)"),
    ("Radiant Rare (NEW)", "swsh12pt5-105", "second example"),
    ("Trainer Gallery Rare Holo (NEW)", "swsh12pt5gg-GG05", "painting, soft brushwork emboss, linen weave, pastel sheen; anim gallery; skin gallery"),
    ("Trainer Gallery Rare Holo (NEW)", "swsh12pt5gg-GG30", "second example"),
    ("Rare Holo V, Galarian Gallery", "swsh12pt5gg-GG36", "the approved alt-art painting (Umbreon 215) at the V tier; anim paint; skin v-beam"),
    ("Rare Holo VMAX, Galarian Gallery", "swsh12pt5gg-GG47", "the approved alt-art painting at the VMAX tier; anim paint; skin vmax-lattice"),
    ("Rare Secret, painted (main set)", "swsh12pt5-160", "Pikachu 160 is a painted secret, not gold: the alt-art painting at the Rare Secret tier; anim paint; skin gold-facet"),
]
H = 560
GAP = 24
FONT = "C:/Windows/Fonts/consola.ttf"


def fit(im, h, nearest=False):
    return im.resize((max(1, round(im.width * h / im.height)), h), Image.NEAREST if nearest else Image.LANCZOS)


def main():
    f1, f2 = ImageFont.truetype(FONT, 30), ImageFont.truetype(FONT, 21)
    rows = []
    for title, cid, note in ROWS:
        if not (E.OUT / f"{cid}-art.png").exists():
            print("not built yet:", cid)
            continue
        ims = [fit(Image.open(P.ref_path(cid)).convert("RGB"), H),
               fit(Image.open(E.OUT / f"{cid}-art.png").convert("RGB"), round(H * 0.62), True),
               fit(Image.open(E.OUT / f"{cid}-card.png").convert("RGB"), H, True)]
        if P.card_json(cid)["tier"] == "Radiant Rare":
            ims.append(fit(Image.open(E.OUT / f"{cid}-art-shiny.png").convert("RGB"), round(H * 0.62), True))
        rows.append((title, cid, note, ims))
        gif(cid)
    W = max(sum(i.width for i in ims) + GAP * (len(ims) + 1) for *_, ims in rows)
    o = Image.new("RGB", (W, 80 + sum(H + 110 for _ in rows)), (22, 22, 27))
    d = ImageDraw.Draw(o)
    d.text((GAP, 20), "Crown Zenith: new rarities for sign-off -- real card | ours | ours + text half",
           font=ImageFont.truetype(FONT, 38), fill=(240, 240, 240))
    y = 80
    for title, cid, note, ims in rows:
        card = P.card_json(cid)
        d.text((GAP, y + 6), f"{title}:  {card['name']} {card['number']}  ({cid}, tier {card['tier']})", font=f1,
               fill=(250, 220, 120))
        d.text((GAP, y + 46), note[:190], font=f2, fill=(190, 190, 190))
        x = GAP
        for im in ims:
            o.paste(im, (x, y + 96 + (H - im.height) // 2))
            x += im.width + GAP
        y += H + 110
    out = P.DATA / "sheets" / "signoff.png"
    out.parent.mkdir(exist_ok=True)
    o.save(out)
    print(out, o.size)


def gif(cid):
    """the real card beside our animated loop (anim/<id>/<id>-term.gif), one GIF"""
    src = P.DATA / "anim" / cid / f"{cid}-term.gif"
    if not src.exists():
        return
    real = fit(Image.open(P.ref_path(cid)).convert("RGB"), 420)
    g = Image.open(src)
    frames, durs = [], []
    for fr in ImageSequence.Iterator(g):
        im = fit(fr.convert("RGB"), 300, True)
        c = Image.new("RGB", (real.width + im.width + 3 * GAP, 420 + 2 * GAP), (22, 22, 27))
        c.paste(real, (GAP, GAP))
        c.paste(im, (real.width + 2 * GAP, GAP + (420 - im.height) // 2))
        frames.append(c.quantize(255))
        durs.append(fr.info.get("duration", 83))
    frames[0].save(P.DATA / "sheets" / f"signoff-{cid}.gif", save_all=True, append_images=frames[1:], duration=durs,
                   loop=0, optimize=False)


if __name__ == "__main__":
    main()
