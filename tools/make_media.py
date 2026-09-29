"""Render showcase images of the real-card pokemon pack from the locally built art (tools/build_realcards.py).

  .venv\\Scripts\\python.exe tools\\make_media.py                  # -> previews/media (git-ignored)
  .venv\\Scripts\\python.exe tools\\make_media.py --out docs/media # only once publishing these images is settled

  hero.png   a grid of every built card, framed (one shiny)
  tiers.png  Pikachu's real cards side by side, each with its rarity tier and odds
  pull.gif   pack pulls as they land in a new tab, prompt underneath

The default output is local-only on purpose: the card art embeds the pokemon-colorscripts sprites (Nintendo
artwork), which is why the README no longer carries images (see its TODO).
The card text is the real engine output: PowerShell compiles scripts/lib/Pokeshell.cs (like the tests do) and
calls [Pokeshell.Core]::PullText with each card's tier, frame, name and number from packs/pokemon/pack.json, so
the images show exactly what a tab prints. tools/render_ansi.py draws that ANSI at Windows Terminal cell proportions.

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
OUT = os.path.join(ROOT, "previews", "media")   # local-only by default (the art embeds Nintendo sprites)
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
  $id, $sh = $line.Split("`t"); $c = $p.cardIndex[$id]; $t = $tiers[$c.tier]
  $txt = [Pokeshell.Core]::PullText($Root, 'pokemon', $c.character, $c.name, $c.id, $t.label, $c.tier, ($sh -eq '1'),
                                    $p.frames[$c.tier], $c.tag, $false, '', '')
  [IO.File]::WriteAllText((Join-Path $Out "$n.ans"), $txt, $utf8); $n++
}
"""


def pack():
    with open(os.path.join(ROOT, "packs", PACK, "pack.json"), encoding="utf-8") as f:
        return json.load(f)


def built_cards(p):
    """card id -> pack.json card entry, for the cards whose art is built (dist/pokemon/<character>-<id>.ans)"""
    return {cid: c for cid, c in p.get("cards", {}).items()
            if os.path.exists(os.path.join(ROOT, "dist", PACK, f"{c['character']}-{cid}.ans"))}


def cards(specs):
    """specs: [(card id, shiny)] -> the ANSI text each pull prints."""
    with tempfile.TemporaryDirectory() as tmp:
        ps1, lst = os.path.join(tmp, "cards.ps1"), os.path.join(tmp, "specs.tsv")
        with open(ps1, "w", encoding="utf-8-sig") as f:
            f.write(PS)
        with open(lst, "w", encoding="utf-8") as f:
            f.write("".join(f"{c}\t{int(s)}\n" for c, s in specs))
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
    """tier id -> chance of one tab pulling that tier (weight among the tiers that have a built card)"""
    live = {c["tier"] for c in built_cards(p).values()}
    w = {t["id"]: int(t.get("weight", 0)) for t in p["tiers"] if t["id"] in live}
    tot = sum(w.values()) or 1
    return {k: v / tot for k, v in w.items()}


def save_png(img, name):
    path = os.path.join(OUT, name)
    img.save(path, optimize=True)
    print(f"{name}: {img.size[0]}x{img.size[1]}, {os.path.getsize(path) // 1024} KB")


# ---------------------------------------------------------------- hero.png
def hero(p):
    rank = {t["id"]: i for i, t in enumerate(p["tiers"])}
    ids = sorted(built_cards(p).items(), key=lambda kv: (rank[kv[1]["tier"]], kv[1]["character"]))
    specs = [(cid, i == 1) for i, (cid, _) in enumerate(ids)]   # one shiny
    imgs = [card_img(t) for t in cards(specs)]
    cols, gx, gy, m = 4, 28, 28, 36
    imgs += [Image.new("RGB", (1, 1), BG)] * (-len(imgs) % cols)
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
    rank = {t["id"]: i for i, t in enumerate(p["tiers"])}
    tdef = {t["id"]: t for t in p["tiers"]}
    pika = sorted(((cid, c) for cid, c in built_cards(p).items() if c["character"] == "pikachu"), key=lambda kv: rank[kv[1]["tier"]])
    tl = [tdef[c["tier"]] for _, c in pika]
    imgs = [card_img(t) for t in cards([(cid, False) for cid, _ in pika])]
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
    # a common pull stays in the plain tab; a pull of a skinned tier reopens the tab with one of its skins
    have = built_cards(p)
    want = [("base1-63", False), ("cel25-5", False), ("base1-44", False), ("sv3pt5-168", False),
            ("base1-46", True), ("swsh4-170", False), ("sma-SV6", False), ("sv8-247", False)]
    tdef = {t["id"]: t for t in p["tiers"]}
    seq = []
    for cid, sh in want:
        if cid in have:
            sk = list(tdef[have[cid]["tier"]].get("skins", {}))
            seq.append((cid, sh, sk[0] if sk else None))
    imgs = [card_img(t, s) for t in cards([(cid, sh) for cid, sh, _ in seq])]
    W = max(im.width for im in imgs) + 16 * s
    H = 20 * s + 16 * s + max(im.height for im in imgs) + 16 * s + 16 * s + 16 * s
    frames, durs = [], []
    for (_, sh, skin), im in zip(seq, imgs):
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
    if "--out" in sys.argv:
        OUT = os.path.abspath(sys.argv[sys.argv.index("--out") + 1])
    os.makedirs(OUT, exist_ok=True)
    p = pack()
    if not built_cards(p):
        sys.exit("no pokemon card art built yet: run tools/build_realcards.py first")
    hero(p)
    tiers(p)
    pull_gif(p)
