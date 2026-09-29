"""Regenerate the README images in docs/media from the current art (run after rebuilding dist/pokemon).

  .venv\\Scripts\\python.exe tools\\make_media.py

  hero.png   a grid of framed Pokemon cards (all four characters across the tiers, one shiny)
  tiers.png  Pikachu at every tier, side by side, with the tier names and odds
  pull.gif   pack pulls as they land in a new tab, prompt underneath

The card text is the real engine output: PowerShell compiles scripts/lib/Pokeshell.cs (like the tests do) and
calls [Pokeshell.Core]::PullText with the tiers, frames, names and tags from packs/pokemon/pack.json, so the
images show exactly what a tab prints. tools/render_ansi.py draws that ANSI at Windows Terminal cell proportions.
Only the public pokemon pack is used. foil.png is a real Windows Terminal screenshot and is not regenerated here.

Needs Windows PowerShell and Pillow (fontTools optional).
"""
import json
import os
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_ansi  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "media")
PACK = "pokemon"
BG = render_ansi.BG
FG = render_ansi.FG
MONO = render_ansi.CASCADIA

PS = r"""
param([string]$Root, [string]$Specs, [string]$Out)
$ErrorActionPreference = 'Stop'
foreach ($k in 'POKESHELL_DISPLAY') { [Environment]::SetEnvironmentVariable($k, $null) }
. (Join-Path $Root 'scripts\lib\roll.ps1')
. (Join-Path $Root 'scripts\lib\common.ps1')
Import-PokeshellCore (Join-Path ([IO.Path]::GetTempPath()) 'pokeshell-media-core')
$p = Read-PokeshellPack $Root 'pokemon'
$tiers = @($p.tiers)
$utf8 = New-Object Text.UTF8Encoding $false
$n = 0
foreach ($line in [IO.File]::ReadAllLines($Specs)) {
  if (-not $line.Trim()) { continue }
  $c, $ti, $sh = $line.Split("`t"); $ti = [int]$ti; $t = $tiers[$ti]
  $txt = [Pokeshell.Core]::PullText($Root, 'pokemon', $c, $p.names[$c], $t.art, $t.label, $ti, ($sh -eq '1'),
                                    $p.frames[$ti], $p.tags[$c], $false, '', '')
  [IO.File]::WriteAllText((Join-Path $Out "$n.ans"), $txt, $utf8); $n++
}
"""


def pack():
    with open(os.path.join(ROOT, "packs", PACK, "pack.json"), encoding="utf-8") as f:
        return json.load(f)


def tier_index(p, tid):
    return next(i for i, t in enumerate(p["tiers"]) if t["id"] == tid)


def cards(specs):
    """specs: [(character, tier index, shiny)] -> the ANSI text each pull prints."""
    with tempfile.TemporaryDirectory() as tmp:
        ps1, lst = os.path.join(tmp, "cards.ps1"), os.path.join(tmp, "specs.tsv")
        with open(ps1, "w", encoding="utf-8-sig") as f:
            f.write(PS)
        with open(lst, "w", encoding="utf-8") as f:
            f.write("".join(f"{c}\t{t}\t{int(s)}\n" for c, t, s in specs))
        subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps1,
                        "-Root", ROOT, "-Specs", lst, "-Out", tmp], check=True)
        res = []
        for i in range(len(specs)):
            with open(os.path.join(tmp, f"{i}.ans"), encoding="utf-8") as f:
                res.append(f.read())
        return res


def card_img(text, scale=1):
    return render_ansi.render(text, scale=scale, pad=0)


def font(px, bold=False):
    f = ImageFont.truetype(MONO, px)
    if bold:
        try: f.set_variation_by_name("Bold")
        except Exception: pass
    return f


def odds(p):
    """tier id -> chance of one tab pulling that tier"""
    foil = p["foil_chance"]
    w = {t["id"]: sum(t["skins"].values()) for t in p["tiers"][1:]}
    tot = sum(w.values())
    res = {p["tiers"][0]["id"]: 1 - foil}
    res.update({k: foil * v / tot for k, v in w.items()})
    return res


def save_png(img, name):
    path = os.path.join(OUT, name)
    img.save(path, optimize=True)
    print(f"{name}: {img.size[0]}x{img.size[1]}, {os.path.getsize(path) // 1024} KB")


# ---------------------------------------------------------------- hero.png
def hero(p):
    T = lambda tid: tier_index(p, tid)
    specs = [("bulbasaur", T("common"), False), ("charmander", T("holo"), False),
             ("squirtle", T("rare-holo"), False), ("pikachu", T("ultra-rare"), False),
             ("squirtle", T("ultra-rare"), False), ("pikachu", T("common"), True),
             ("charmander", T("secret-rare"), False), ("bulbasaur", T("ultra-rare"), True)]
    imgs = [card_img(t) for t in cards(specs)]
    cols, gx, gy, m = 4, 28, 28, 36
    colw = [max(imgs[r * cols + c].width for r in range(len(imgs) // cols)) for c in range(cols)]
    rowh = [max(im.height for im in imgs[r * cols:(r + 1) * cols]) for r in range(len(imgs) // cols)]
    W, H = sum(colw) + gx * (cols - 1) + 2 * m, sum(rowh) + gy * (len(rowh) - 1) + 2 * m
    out = Image.new("RGB", (W, H), BG)
    y = m
    for r, h in enumerate(rowh):
        x = m
        for c, w in enumerate(colw):
            im = imgs[r * cols + c]
            out.paste(im, (x + (w - im.width) // 2, y + (h - im.height) // 2))
            x += w + gx
        y += h + gy
    save_png(out, "hero.png")


# ---------------------------------------------------------------- tiers.png
def tiers(p):
    tl = p["tiers"]
    imgs = [card_img(t) for t in cards([("pikachu", i, False) for i in range(len(tl))])]
    od = odds(p)
    gx, m, cap = 32, 36, 64
    H = max(im.height for im in imgs)
    W = sum(im.width for im in imgs) + gx * (len(imgs) - 1) + 2 * m
    out = Image.new("RGB", (W, H + cap + 2 * m), BG)
    d = ImageDraw.Draw(out)
    fb, fs = font(22, True), font(16)
    colors = [(150, 150, 150), (185, 215, 235), (110, 165, 255), (225, 120, 230), (240, 200, 80)]
    x = m
    for i, (im, t) in enumerate(zip(imgs, tl)):
        out.paste(im, (x, m + H - im.height))
        cx, cy = x + im.width // 2, m + H + 14
        col = colors[min(i, len(colors) - 1)]
        d.text((cx, cy), t["label"], font=fb, fill=col, anchor="ma")
        pct = od[t["id"]] * 100
        n = 1 / od[t["id"]]
        d.text((cx, cy + 32), f"{pct:.2f}%  ~1 tab in {n:.0f}" if n >= 2 else f"{pct:.0f}%", font=fs, fill=(140, 140, 140), anchor="ma")
        x += im.width + gx
    save_png(out, "tiers.png")


# ---------------------------------------------------------------- pull.gif
def terminal(card, title, width, height, reveal=1.0, cursor=True, s=2):
    """a dark fake Windows Terminal tab: tab bar, the card at the top, the prompt under it (s = render scale)"""
    bar = 20 * s
    out = Image.new("RGB", (width, height), BG)
    d = ImageDraw.Draw(out)
    d.rectangle([0, 0, width, bar - 1], fill=(32, 32, 32))
    tw = 150 * s
    d.rounded_rectangle([4 * s, 4 * s, 4 * s + tw, bar + 4 * s], radius=4 * s, fill=BG)
    d.text((11 * s, bar // 2 + 2 * s), title, font=font(7 * s), fill=(220, 220, 220), anchor="lm")
    d.text((4 * s + tw - 9 * s, bar // 2 + 2 * s), "×", font=font(8 * s), fill=(150, 150, 150), anchor="mm")
    d.text((4 * s + tw + 11 * s, bar // 2 + 2 * s), "+", font=font(9 * s), fill=(170, 170, 170), anchor="mm")
    top, left = bar + 16 * s, 8 * s   # one blank line, then the card, like a new tab
    if card is not None:
        h = int(card.height * reveal)
        if h > 0:
            out.paste(card.crop((0, 0, card.width, h)), (left, top))
        if reveal >= 1:
            y = top + card.height + 16 * s   # the card's trailing blank line
            f = font(int(16 * s * 0.74))
            prompt = r"PS C:\Users\you> "
            d.text((left, y + int(16 * s * 0.08)), prompt, font=f, fill=FG)
            if cursor:
                x = left + len(prompt) * 8 * s
                d.rectangle([x, y, x + 8 * s - 1, y + 16 * s - 1], fill=FG)
    return out


def pull_gif(p, s=2):
    T = lambda tid: tier_index(p, tid)
    # a common pull stays in the plain tab; a foil pull reopens the tab with one of its tier's skins
    seq = [("squirtle", T("common"), False, None), ("charmander", T("holo"), False, "starlight"),
           ("bulbasaur", T("common"), False, None), ("pikachu", T("rare-holo"), False, "cosmos"),
           ("charmander", T("common"), True, None), ("squirtle", T("ultra-rare"), False, "radiant"),
           ("bulbasaur", T("rare-holo"), False, "cracked-ice"), ("pikachu", T("secret-rare"), False, "gold")]
    imgs = [card_img(t, s) for t in cards([(c, t, sh) for c, t, sh, _ in seq])]
    W = max(im.width for im in imgs) + 16 * s
    H = 20 * s + 16 * s + max(im.height for im in imgs) + 16 * s + 16 * s + 16 * s
    frames, durs = [], []
    for (c, t, sh, skin), im in zip(seq, imgs):
        title = "Windows PowerShell" if skin is None else f"pokeshell: {PACK}/{skin}"
        frames.append(terminal(None, title, W, H, s=s)); durs.append(350)
        for r in (0.25, 0.5, 0.75):
            frames.append(terminal(im, title, W, H, r, s=s)); durs.append(45)
        for k in range(4):
            frames.append(terminal(im, title, W, H, 1, cursor=k % 2 == 0, s=s)); durs.append(500)
    # one shared palette keeps the GIF small and the colors steady between frames
    strip = Image.new("RGB", (W, H * len(imgs)))
    for i, im in enumerate(imgs):
        strip.paste(terminal(im, "pokeshell: pokemon/x", W, H, s=s), (0, i * H))
    pal = strip.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    q = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    path = os.path.join(OUT, "pull.gif")
    q[0].save(path, save_all=True, append_images=q[1:], duration=durs, loop=0, optimize=True, disposal=1)
    print(f"pull.gif: {W}x{H}, {len(q)} frames, {os.path.getsize(path) // 1024} KB")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    p = pack()
    hero(p)
    tiers(p)
    pull_gif(p)
