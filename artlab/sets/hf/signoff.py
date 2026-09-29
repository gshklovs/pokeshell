r"""The sign-off material for Hidden Fates' new rarities (docs/ART_METHOD.md section 15): per card one image
real card | ours | ours + text half, plus its 16-frame gif, into a lookbook folder; and the Shiny Vault look's
alternative ("silver", the scan's white window read as bright silver) rendered to work/alt/ for comparison with the
default ("dark", black-and-silver). Nothing in art/ or anim/<id>/ is touched by the alternative.

  ..\..\..\.venv\Scripts\python signoff.py alt                          work/alt/<id>-silver-{art,card}.png + gif
  ..\..\..\.venv\Scripts\python signoff.py page <lookbook dir> <ids>    the sign-off section in <dir>/index.html
"""
import json
import re
import shutil
import sys

from PIL import Image

import hflib as P
from hflib import E, L, bottom
import hfcards as C

ALT = E.WORK / "alt"
H = 460


def alt():
    import hfanim
    B = P.load_evs("build", "evs_build")
    ALT.mkdir(parents=True, exist_ok=True)
    hfanim.A.s3.ANIM = ALT
    for cid, fn in (("sma-SV6", C.charmander_sv), ("sma-SV49", C.charizard_svgx)):
        c = fn(tone="silver")
        art = B.art_json(c)
        rows = art["variants"][c.meta["variant"]]["rows"]
        p = B.variant_pal(art, c.meta["variant"], False)
        L.term_png(rows, p, ALT / f"{cid}-silver-art.png")
        used = {ch for r in rows for ch in r if ch != "."}
        top = L.to_ansi(rows, {k: p[k] for k in used})
        bot = bottom.render_text(P.card_json(cid), len(rows[0]), frame=c.meta["frame"])
        L.render(top + bot, str(ALT / f"{cid}-silver-card.png"))
        frames = hfanim.KINDS[c.meta["anim"]](c, False)
        assert frames[-1] == c.rgb(False)
        hfanim.A.s3.export(f"{cid}_silver", c.meta["label"] + " (silver alternative)", frames, len(frames) - 1,
                           hfanim.NOTES[c.meta["anim"]])
        print(cid, "silver alternative:", ALT)


def combo(cid, art_png, card_png):
    card = P.card_json(cid)
    ims = [Image.open(P.ref_path(cid)).convert("RGB"), Image.open(art_png).convert("RGB"),
           Image.open(card_png).convert("RGB")]
    ims = [im.resize((max(1, round(im.width * H / im.height)), H), Image.LANCZOS if i == 0 else Image.NEAREST)
           for i, im in enumerate(ims)]
    c = Image.new("RGB", (sum(i.width for i in ims) + 40, H), (20, 21, 27))
    x = 0
    for im in ims:
        c.paste(im, (x, 0))
        x += im.width + 20
    return c, card


def page(lb, ids):
    """one section per new rarity, rows = real | ours | ours + text, figs = the gifs (and the silver alternative)"""
    lb = P.Path(lb)
    out = lb / "img" / "hf_signoff"
    out.mkdir(parents=True, exist_ok=True)
    files = {}
    by = {}
    for cid in ids:
        by.setdefault(P.card_json(cid)["tier"], []).append(cid)
    about = {
        "Rare Holo GX": "Sun &amp; Moon GX: the art frame to frame under a silver frame, the GX 'water-web' holo (a cracked web of foil lines, a faint rainbow per cell). Loop <b>gxweb</b>: a rainbow sheen sweeps, the web lights up along it. Tier rare-holo-gx (weight 1200), tab skin <b>gx-web</b> (new).",
        "Rare Shiny": "Shiny Vault: the colorscripts SHINY sprite, unchanged, in the card's window; the window's own printed sparkle stars recut as black-and-silver vault foil (brushed gunmetal, stars embossed in silver), glitter, 4-point stars. Loop <b>vault</b>: a silver specular band with cyan / pink fringes crosses, the stars catch it, glitter flashes. Tier rare-shiny (weight 500, unchanged), tab skin <b>vault-foil</b> (new).",
        "Rare Shiny GX": "Shiny Vault GX, a step above: full-art crop, the SHINY sprite, the vault foil cut with an etched fingerprint texture, star flares, a silver bevel frame. Loop <b>vaultgx</b>: a silver beam pair (a whisper of prism) over foil and frame, the etch flashes, glitter, flares. Tier rare-shiny-gx (weight 200), tab skin <b>vault-gx</b> (new).",
        "Rare Secret": "Sun &amp; Moon gold GX: the approved evs gold (Froslass 226) on the SM full-art gold card: gold sprite remap, faceted etched gold, glitter. Loop <b>gold</b>. Tier rare-secret (existing), tab skin gold-facet (existing).",
    }
    secs = []
    for tier, cids in by.items():
        rows, figs = [], []
        for cid in cids:
            im, card = combo(cid, E.OUT / f"{cid}-art.png", E.OUT / f"{cid}-card.png")
            im.save(out / f"{cid}.jpg", quality=86)
            files[f"img/hf_signoff/{cid}.jpg"] = str(out / f"{cid}.jpg")
            rows.append(f'        ["{card["name"]}<br>{card["number"]}", ["{cid}.jpg", "real card | ours | ours + text half"]],')
            g = P.DATA / "anim" / cid / f"{cid}-term.gif"
            if g.exists():
                shutil.copy(g, out / f"{cid}.gif")
                files[f"img/hf_signoff/{cid}.gif"] = str(out / f"{cid}.gif")
                figs.append(f'      FIG("img/hf_signoff/{cid}.gif", "{card["name"]} {card["number"]}: the 16-frame loop (12 fps)", "loop"),')
            if (ALT / f"{cid}-silver-card.png").exists():
                im2, _ = combo(cid, ALT / f"{cid}-silver-art.png", ALT / f"{cid}-silver-card.png")
                im2.save(out / f"{cid}-silver.jpg", quality=86)
                files[f"img/hf_signoff/{cid}-silver.jpg"] = str(out / f"{cid}-silver.jpg")
                rows.append(f'        ["{card["name"]}<br>{card["number"]}<br><i>silver alternative</i>", ["{cid}-silver.jpg", "real card | ours, silver | + text half"]],')
                sg = ALT / f"{cid}_silver" / f"{cid}_silver-term.gif"
                if sg.exists():
                    shutil.copy(sg, out / f"{cid}-silver.gif")
                    files[f"img/hf_signoff/{cid}-silver.gif"] = str(out / f"{cid}-silver.gif")
                    figs.append(f'      FIG("img/hf_signoff/{cid}-silver.gif", "{card["name"]} {card["number"]}: the silver alternative loop", "alt"),')
        sid = "hfsign_" + re.sub(r"\W+", "_", tier.lower())
        vault = tier in ("Rare Shiny", "Rare Shiny GX")
        qs = [f'''      {{ id: "{sid}_ok", q: "{tier}: this effect and tier", opts: [
        ["ok", "Approve", "It goes live with the set.", true],
        ["fix", "Change it", "Say what in the notes."],
      ]}},''']
        if vault:
            qs.append(f'''      {{ id: "{sid}_tone", q: "The vault foil's tone", opts: [
        ["dark", "Black-and-silver", "Gunmetal metal, the printed stars in silver (built).", true],
        ["silver", "Bright silver", "The scan's white window read as bright silver foil."],
      ]}},''')
        secs.append(f'''  {{
    id: "{sid}", eyebrow: "Hidden Fates sign-off · {tier}", title: "{tier}: new effect",
    blurb: "{about.get(tier, "")}",
    figs: [
{chr(10).join(figs)}
    ],
    grid: {{
      dir: "img/hf_signoff/",
      cols: ["Real card | ours | ours + text half"],
      rows: [
{chr(10).join(rows)}
      ],
    }},
    questions: [
{chr(10).join(qs)}
    ],
  }},
''')
    html = lb / "index.html"
    if not html.exists():
        s = (P.HERE.parents[1] / "lookbook" / "template.html").read_text(encoding="utf-8")
        s = re.sub(r"const SECTIONS = \[\n.*?\n\];", "const SECTIONS = [\n];", s, flags=re.S)
    else:
        s = html.read_text(encoding="utf-8")
    for sec in secs:
        sid = re.search(r'id: "(\w+)"', sec).group(1)
        m = re.search(r'  \{\n    id: "' + sid + r'"', s)
        if m:
            e = re.search(r'\n  \{\n    id: "\w+"', s[m.start() + 5:])
            s = s[:m.start()] + (s[m.start() + 5 + e.start() + 1:] if e else s[s.index("];", m.start()):])
        at = s.index("const SECTIONS = [\n") + len("const SECTIONS = [\n")
        s = s[:at] + sec + s[at:]
    html.write_text(s, encoding="utf-8")
    (lb / "files-signoff.json").write_text(json.dumps(files, indent=1), encoding="utf-8")
    print(html, len(files), "files")


if __name__ == "__main__":
    if sys.argv[1] == "alt":
        alt()
    else:
        page(sys.argv[2], sys.argv[3].split(","))
