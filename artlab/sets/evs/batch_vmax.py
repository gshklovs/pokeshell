r"""Evolving Skies full set, group "vmax": every Rare Holo VMAX card, built exactly like the approved example
Vaporeon VMAX 30 (evcards2.vaporeon): the card's own scene with the real Pokemon painted out (tex_fill),
grid-scale sample, sat 1.25, focus halo, k-means 40 -> VMAX etched contours (vmax_texture) -> sunpillar
rainbow stripes -> median 110 colours, light rim, gunmetal grooved 3 px frame, 4 sparkles; animation
"sunpillar" (the beam lights the etched grooves).

Per card only the geometry differs: the crop (x0, y0, S) is the full card width, W = sprite width + 7,
H = sprite height + 3 (Vaporeon: 39x30 sprite on a 46x33 card), the text boxes that get painted out, the
flip (face the way the card does) and the mask model.

  ..\..\..\.venv\Scripts\python batch_vmax.py masks [ids]     masks/<id>.png + work/vmax_masks.png
  ..\..\..\.venv\Scripts\python batch_vmax.py build [ids]     art/, out/ (normal + shiny, art + card)
  ..\..\..\.venv\Scripts\python batch_vmax.py anim [ids]      anim/<id>/ + anim/<id>_shiny/
  ..\..\..\.venv\Scripts\python batch_vmax.py verify [ids]    verify.py's checks on these ids
  ..\..\..\.venv\Scripts\python batch_vmax.py sheet           sheets/vmax.png
  ..\..\..\.venv\Scripts\python batch_vmax.py all [ids]
"""
import json
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

import evcards
import evcards2 as B2
import evlib as E
from evlib import L, Card, Sprite
from evcards import W_LUM, colour_blend, meta, place, rainbow_rgb, silver_frame

GROUP = "vmax"
PLAN = json.load(open(E.HERE / "plan.json", encoding="utf-8"))[GROUP]
IDS = [p["id"] for p in PLAN]
SIZES = E.DATA / "sheets" / "vmax_sizes.json"

# the VMAX card's header: name bar, stage icon, "Evolves from" bar, Rapid / Single Strike logo (Vaporeon's boxes)
# (the name and HP run down to y ~98 on these scans: a shorter box lets their lower half mirror into the fill)
HEAD = ((0, 0, 734, 102), (0, 28, 120, 160), (100, 72, 360, 150))
STRIKE = (430, 84, 712, 172)

# per card: sprite (plan.json, or its -gmax form when the card shows Gigantamax), flip = face the way the card
# does, text = card-px y where the attack / ability text starts (painted out below), model = rembg model for the
# Pokemon's mask, win = rect the mask is limited to, keep = mask components kept, dx/dy = sprite nudge,
# tex = texture source rect for the fill, mx/my = margins added to the sprite size (default 7 / 3)
SPEC = {
    "swsh7-8":   dict(flip=True, text=632, strike=False, model=None,
                      hull=[(20, 240), (130, 230), (260, 280), (280, 130), (350, 110), (420, 150), (430, 260),
                            (500, 230), (520, 80), (640, 60), (680, 120), (640, 300), (650, 400), (620, 520),
                            (640, 640), (240, 640), (240, 560), (80, 560), (20, 470), (60, 420), (20, 330)]),
    "swsh7-14":  dict(flip=False, text=680, strike=False, model=None,
                      hull=[(40, 250), (200, 250), (300, 140), (380, 95), (470, 110), (560, 130), (570, 220),
                            (530, 300), (560, 340), (660, 380), (705, 420), (705, 580), (640, 690), (100, 690),
                            (20, 600), (0, 420), (10, 300)]),
    "swsh7-41":  dict(flip=False, text=592, strike=False, model=None,
                      hull=[(90, 95), (260, 100), (300, 200), (420, 220), (560, 150), (725, 110), (730, 260), (640, 300),
                            (690, 370), (690, 600), (600, 620), (560, 800), (60, 800), (60, 480), (100, 350),
                            (180, 300), (190, 200)]),
    "swsh7-59":  dict(flip=True, text=640, strike=False, model=None,
                      hull=[(100, 300), (150, 150), (260, 120), (360, 90), (460, 80), (560, 100), (640, 140),
                            (620, 230), (560, 280), (600, 420), (700, 520), (700, 640), (40, 640), (40, 450),
                            (90, 380)]),
    "swsh7-29":  dict(flip=True, text=680, strike=False, model=None,
                      hull=[(80, 340), (150, 200), (300, 120), (420, 60), (520, 80), (660, 70), (700, 120),
                            (640, 260), (700, 400), (720, 500), (700, 700), (60, 700), (60, 500)]),
    "swsh7-18":  dict(flip=True, text=708, model=None,
                      hull=[(60, 230), (150, 200), (230, 130), (300, 105), (365, 105), (400, 140), (440, 150),
                            (520, 170), (580, 240), (620, 330), (640, 450), (630, 560), (600, 720), (80, 720),
                            (50, 560), (60, 420), (90, 340)]),
    "swsh7-51":  dict(flip=True, text=708, strike=False, model=None,
                      hull=[(290, 60), (345, 55), (380, 110), (480, 95), (560, 95), (650, 55), (710, 55),
                            (690, 200), (640, 300), (720, 420), (690, 480), (620, 560), (710, 630), (710, 715),
                            (60, 715), (70, 560), (160, 480), (190, 420), (160, 350), (230, 300), (220, 250),
                            (300, 200)]),
    "swsh7-65":  dict(flip=False, text=592, strike=False, model=None, tex=(20, 330, 150, 560),
                      hull=[(135, 92), (345, 92), (365, 190), (400, 190), (700, 45), (725, 90), (610, 190), (610, 260),
                            (680, 200), (740, 230), (700, 330), (650, 450), (640, 600), (590, 780), (160, 780),
                            (170, 470), (160, 420), (170, 330), (165, 285), (60, 260), (70, 225), (170, 220)]),
    # Sylveon's ribbons fill the whole card: only the head + body are painted out (a full hull leaves nothing
    # but a flat membrane), the outer ribbon loops stay in the scene as pink / white bands (cf. Altaria's clouds)
    "swsh7-75":  dict(flip=False, text=592, model=None, tex=(20, 330, 120, 560),
                      hull=[(150, 150), (300, 130), (420, 140), (560, 160), (600, 300), (560, 420), (600, 600),
                            (120, 600), (160, 420), (150, 300)]),
    # the card is Dusk Form Lycanroc (orange / grey-white, green eyes): plan.json's "lycanroc" is the Midday
    # sprite, so the vendor's lycanroc-dusk is used
    "swsh7-92":  dict(flip=True, text=585, strike=False, sprite="lycanroc-dusk", model=None,
                      hull=[(150, 150), (260, 120), (380, 160), (430, 130), (560, 140), (600, 200), (610, 300),
                            (700, 330), (720, 420), (700, 520), (620, 560), (620, 590), (160, 590), (150, 420),
                            (120, 330), (170, 250)]),
    "swsh7-95":  dict(flip=False, text=640, model=None,
                      hull=[(60, 200), (200, 180), (340, 200), (380, 40), (470, 50), (480, 150), (560, 200),
                            (600, 420), (700, 480), (720, 560), (720, 640), (160, 640), (40, 420), (20, 290),
                            (100, 280), (80, 250)]),
    # Gigantamax on the card (G-Max Malodor): the -gmax sprite
    "swsh7-101": dict(flip=False, text=592, strike=False, sprite="garbodor-gmax", model=None,
                      tex=(645, 190, 720, 400),
                      hull=[(20, 230), (120, 180), (250, 160), (300, 130), (420, 120), (500, 150), (560, 120),
                            (620, 80), (700, 100), (690, 170), (640, 200), (640, 400), (720, 420), (720, 590),
                            (20, 590)]),
    "swsh7-111": dict(flip=False, text=566, model=None,
                      hull=[(120, 130), (330, 120), (520, 110), (640, 220), (705, 300), (712, 560), (620, 700),
                            (560, 860), (300, 880), (100, 700), (120, 500), (90, 300)]),
    "swsh7-123": dict(flip=False, text=592, sprite="duraludon-gmax", model=None,
                      hull=[(330, 85), (400, 85), (470, 250), (520, 230), (640, 270), (700, 400), (690, 620),
                            (620, 650), (560, 600), (510, 800), (450, 900), (260, 900), (200, 700), (180, 600),
                            (60, 640), (30, 500), (80, 380), (200, 360), (260, 250)]),
}
for p in PLAN:
    SPEC[p["id"]].setdefault("sprite", p["sprite"])
    SPEC[p["id"]]["name"] = p["name"]


# ============================================================ masks
MODELS = ("isnet-anime", "isnet-general-use", "u2net")


def rembg(cid, model):
    f = E.WORK / f"rembg-{model}-{cid}.png"
    if not f.exists():
        from rembg import new_session, remove
        m = remove(Image.open(E.ref_path(cid)).convert("RGB"), session=new_session(model), only_mask=True)
        m.save(f)
    return np.asarray(Image.open(f)) > 128


def rect(shape, a, b, c, d):
    m = np.zeros(shape, bool)
    m[b:d, a:c] = True
    return m


def poly(shape, pts):
    im = Image.new("L", (shape[1], shape[0]), 0)
    ImageDraw.Draw(im).polygon(pts, fill=255)
    return np.asarray(im) > 0


def largest(m, keep=1):
    lbl, n = ndimage.label(m)
    if n <= keep:
        return m
    sz = ndimage.sum(m, lbl, range(1, n + 1))
    return np.isin(lbl, 1 + np.argsort(sz)[::-1][:keep])


def make_mask(cid):
    p = SPEC[cid]
    sh = E.card_img(cid).shape[:2]
    win = rect(sh, *p.get("win", (0, 60, 734, 900)))
    if "hull" in p:                  # a hand hull (card px, read off work/grid_<n>.png)
        win &= poly(sh, p["hull"])
    model = p.get("model", "isnet-anime")
    m = (rembg(cid, model) & win) if model else win
    for c in p.get("cut", ()):
        m &= ~(poly(sh, c) if isinstance(c[0], (tuple, list)) else rect(sh, *c))
    for c in p.get("add", ()):
        m |= poly(sh, c) if isinstance(c[0], (tuple, list)) else rect(sh, *c)
    if p.get("close"):
        m = ndimage.binary_closing(m, iterations=p["close"])
    return ndimage.binary_fill_holes(largest(m, p.get("keep", 1)))


def masks(ids):
    E.MASKS.mkdir(exist_ok=True)
    tiles = []
    for cid in ids:
        m = make_mask(cid)
        Image.fromarray((m * 255).astype(np.uint8)).save(E.MASKS / f"{cid}.png")
        rgb = E.card_img(cid)
        o = np.where(m[..., None], rgb, rgb * 0.25 + np.array([0, 0.3, 0]))
        tiles.append(Image.fromarray(L.to8(o)).resize((367, 512)))
        ys, xs = np.nonzero(m)
        print(cid, "bbox", xs.min(), ys.min(), xs.max(), ys.max(), f"{m.mean():.2f}")
    n = min(7, len(tiles))
    sheet = Image.new("RGB", (367 * n, 512 * ((len(tiles) + n - 1) // n)))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % n) * 367, (i // n) * 512))
    sheet.save(E.WORK / "vmax_masks.png")


# ============================================================ the card (Vaporeon VMAX 30's recipe)
def geometry(cid, spr):
    p = SPEC[cid]
    W = spr.w + p.get("mx", 7)
    H = spr.h + p.get("my", 3)
    x0 = p.get("x0", 6)
    S = p.get("S", (710 - x0) / W)
    y0 = p.get("y0", 72)
    return x0, y0, S, W, H


def scene(cid):
    """the scan with the Pokemon, the header, the strike logo and the text half painted out"""
    p = SPEC[cid]
    boxes = B2.EDGES + HEAD + ((STRIKE,) if p.get("strike", True) else ()) + ((0, p["text"], 734, 1024),) +         tuple(p.get("boxes", ()))
    rgb, _ = E.clean(cid, grow=5, boxes=boxes, tex_src=p.get("tex", (30, 170, 130, 560)))
    return rgb


def vmax(cid):
    p = SPEC[cid]
    spr = Sprite(p["sprite"], flip=p["flip"])
    x0, y0, S, W, H = geometry(cid, spr)
    rgb = scene(cid)
    c = Card(W, H)
    place(c, spr, cid, x0, y0, S, off=p.get("off"), dx=p.get("dx", 0), dy=p.get("dy", 0), margin=2)
    a = L.sample(rgb, x0, y0, S / 2, 2 * W, 2 * H, resample=L.Image.BOX)
    a = L.tone(a, sat=1.25, bright=1.0)
    a = L.focus_halo(c, a, radius=3, dark=0.85, soft=1.0)
    _, lbl, pal = L.kmeans_q(a, 40, 0, ignore=c.fig_mask())
    base = pal[L.orphan_clean(lbl, 1)]
    base, groove = B2.vmax_texture(base)
    FH, FW = c.FH, c.FW
    yy, xx = np.mgrid[0:FH, 0:FW]
    q = colour_blend(base, rainbow_rgb((xx * 0.9 + yy * 0.35) / 9.0, s=0.7), 0.14 + 0.1 * (base @ W_LUM))
    q = L.median_q(q, 110)
    d = c.dist()
    rim = (d > 0) & (d <= 1.01)
    q[rim] = q[rim] + (1 - q[rim]) * 0.45
    q = silver_frame(c, q, width=3, ramp_hex=B2.GUNMETAL, groove=True)
    ring = c.meta["frame_ring"]
    c.bg = q
    c.bgq = L.to8(q)
    # sparkles in the four corners of the window (Vaporeon: 9,9 / 82,8 / 84,56 / 8,58 on a 92x66 grid)
    stars = [(9, 9, 3), (FW - 10, 8, 2), (FW - 8, FH - 10, 3), (8, FH - 8, 2)]
    for x, y, st in stars:
        L.sparkle(c, x, y, st, {"L": "#ffffff", "l": "#dff6ff", "j": "#8fd8ff"})
    num = E.num(cid)
    return meta(c, card=cid, label=f"Rare Holo VMAX: {p['name']} {int(num):03d}/203 (gunmetal frame, etched holo)",
                rarity="Rare Holo VMAX", finish="SWSH VMAX holo: gunmetal frame, sunpillar stripes, bold etched contours",
                variant="rare-holo-vmax", anim="sunpillar", ref=(cid, x0, y0, x0 + W * S, y0 + H * S), S=S,
                stars=stars, grooves=groove & ~ring)


BUILDERS = {cid: (lambda cid=cid: vmax(cid)) for cid in IDS}
evcards.BUILDERS.update(BUILDERS)          # in this process only: build.render / anim.build look builders up here


# ============================================================ build / anim / verify / sheet
def local(name):
    """evs/<name>.py by path: suite3 (put on sys.path first by evlib) has its own build.py / anim.py"""
    import importlib.util
    key = f"evs_{name}"
    if key not in sys.modules:
        spec = importlib.util.spec_from_file_location(key, E.HERE / f"{name}.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return sys.modules[key]


def build(ids):
    Bd = local("build")
    E.OUT.mkdir(exist_ok=True)
    sizes = json.load(open(SIZES, encoding="utf-8")) if SIZES.exists() else {}
    for cid in ids:
        _, info = Bd.render(cid)
        info["sprite"] = SPEC[cid]["sprite"]
        sizes[cid] = info
    SIZES.parent.mkdir(exist_ok=True)
    SIZES.write_text(json.dumps(sizes, indent=1), encoding="utf-8")


def anim(ids):
    A = local("anim")
    A.build(ids)


def verify(ids):
    """verify.py's checks (sprite shape / outline / colours exact vs the vendor sprite, card data verbatim,
    16 frames with the final frame == static art), run on this group's ids"""
    import sprites
    fails = 0

    def report(ok, msg):
        nonlocal fails
        fails += not ok
        print(("ok  " if ok else "BAD ") + msg)

    for cid in ids:
        c = BUILDERS[cid]()
        art = json.load(open(E.ART / f"{cid}.json", encoding="utf-8"))
        v = art["variants"][c.meta["variant"]]
        rows = v["rows"]
        A, B = c.off
        name = c.spr.name
        report(c.meta.get("sprite_recolour") is None, f"{cid:10s} no sprite recolour at Rare Holo VMAX")
        for sh in (False, True):
            pal = {**art["palette"], **v.get("palette", {})}
            if sh:
                pal = {**pal, **art["shiny"], **v.get("shiny", {})}
            src = sprites.load(name, sh)
            w, h = len(src[0]), len(src)
            flip = v["flip"]
            tot = split = outline_bad = bad = 0
            want_cells = set()
            for j in range(h):
                for i in range(w):
                    want = src[j][i]
                    if want is None:
                        continue
                    tot += 1
                    ci = w - 1 - i if flip else i
                    X, Y = 2 * (A + ci), 2 * (B + j)
                    block = {rows[Y + b][X + a] for a in (0, 1) for b in (0, 1)}
                    for a in (0, 1):
                        for b in (0, 1):
                            want_cells.add((X + a, Y + b))
                    if len(block) != 1:
                        split += 1
                        continue
                    got = L.hexrgb(pal[block.pop()])
                    if want == (0, 0, 0):
                        outline_bad += got != (0, 0, 0)
                        continue
                    bad += got != want
            spr_cells = {q for q, (Lr, k) in c.cells.items() if Lr == "sprite"}
            shape_ok = spr_cells == want_cells and split == 0
            report(shape_ok and outline_bad == 0 and bad == 0,
                   f"{cid:10s} {name:14s} {'shiny ' if sh else 'normal'} flip={flip!s:5s} {tot} px: shape "
                   f"{'exact' if shape_ok else 'WRONG'}, {outline_bad} outline px off, {bad} colour errors (exact vendor colours)")
        api = json.load(open(E.CARDS / "api" / f"{cid}.json", encoding="utf-8"))
        card = json.load(open(E.CARDS / f"{cid}.json", encoding="utf-8"))
        diff = [k for k in card if k not in ("tier", "set", "images")
                and card[k] != api.get(k, card[k] if card[k] in ([], "") else None)]
        real = api["set"]["id"] == "swsh7" and api["id"] == cid and card["tier"] == api["rarity"] == c.meta["rarity"]
        report(real and not diff, f"{cid:10s} card data: real swsh7 printing, API rarity '{api['rarity']}', tier "
                                  f"'{card['tier']}', fields verbatim{'' if not diff else ' EXCEPT ' + str(diff)}")
        for sh in (False, True):
            nm = cid + ("_shiny" if sh else "")
            f = E.DATA / "anim" / nm / f"{nm}.json"
            if not f.exists():
                report(False, f"{nm}: animation missing")
                continue
            m = json.load(open(f, encoding="utf-8"))
            last = m["frames"][m["final_frame"]]
            got = [[None if ch == "." else L.hexrgb(m["palette"][ch]) for ch in r] for r in last]
            report(got == c.rgb(sh) and len(m["frames"]) == 16,
                   f"{nm:16s} animation: {len(m['frames'])} frames, final frame == static art")
    print(f"{fails} failures")
    return fails


def sheet(ids):
    """sheets/vmax.png: one row per card -- real card | ours | ours + text half (sheet.py's layout)"""
    from PIL import ImageFont
    Sh = local("sheet")
    sizes = json.load(open(SIZES, encoding="utf-8"))
    rows = []
    for cid in ids:
        card = json.load(open(E.CARDS / f"{cid}.json", encoding="utf-8"))
        info = sizes[cid]
        real = Sh.fit_h(Image.open(E.ref_path(cid)).convert("RGB"), Sh.ROW_H)
        cim = Image.open(E.OUT / f"{cid}-card.png").convert("RGB")
        stacked = Sh.fit_h(cim, Sh.ROW_H)
        art0 = Image.open(E.OUT / f"{cid}-art.png").convert("RGB")
        k = stacked.height / cim.height
        art = art0.resize((round(art0.width * k), round(art0.height * k)), Image.LANCZOS)
        label = (f"{cid}  {card['name']}  {card['number']}/{card['set']['printedTotal']}  tier: {card['tier']}"
                 f"  |  sprite {info['sprite']}{' (flipped)' if info['flip'] else ''}  |  art {info['cols']}x{info['lines']},"
                 f" card {info['cols']}x{info['card_lines']}\n{info['finish']}")
        rows.append((label, [real, art, stacked]))
    G = Sh.GAP
    W = max(sum(p.width for p in ps) + G * (len(ps) + 1) for _, ps in rows)
    H = sum(Sh.ROW_H + 90 + G for _ in rows) + 70
    o = Image.new("RGB", (W, H), (24, 24, 28))
    d = ImageDraw.Draw(o)
    d.text((G, 14), "Evolving Skies (swsh7) Rare Holo VMAX: real card | pokeshell art | art + text half",
           font=ImageFont.truetype(Sh.FONT, 36), fill=(235, 235, 235))
    y = 70
    f = ImageFont.truetype(Sh.FONT, 26)
    for label, ps in rows:
        d.text((G, y + 8), label, font=f, fill=(200, 200, 200))
        x = G
        for p in ps:
            o.paste(p, (x, y + 80))
            x += p.width + G
        y += Sh.ROW_H + 90 + G
    (E.DATA / "sheets").mkdir(exist_ok=True)
    o.save(E.DATA / "sheets" / f"{GROUP}.png")
    print(f"sheets/{GROUP}.png", o.size)


def preview(ids):
    """work/vmax_prev.png: the scan's crop | the cleaned scene | our art (normal), per card -- for iterating
    before the card data exists"""
    tiles = []
    for cid in ids:
        c = BUILDERS[cid]()
        x0, y0, x1, y1 = c.meta["ref"][1:]
        g = c.rgb(False)
        a = np.array([[v if v is not None else (0, 0, 0) for v in r] for r in g], np.uint8)
        art = Image.fromarray(a).resize((c.FW * 6, c.FH * 6), Image.NEAREST)
        real = Image.open(E.ref_path(cid)).convert("RGB")
        crop = real.crop((round(x0), round(y0), round(x1), round(y1))).resize(art.size, Image.LANCZOS)
        rgb = scene(cid)
        cl = Image.fromarray(L.to8(rgb)).crop((round(x0), round(y0), round(x1), round(y1))).resize(art.size)
        t = Image.new("RGB", (art.width * 3 + 20, art.height), (20, 20, 20))
        for i, im in enumerate((crop, cl, art)):
            t.paste(im, (i * (art.width + 10), 0))
        tiles.append(t)
        t.save(E.WORK / f"vmax_prev_{cid}.png")
        print(cid, c.W, c.H, "off", c.off)


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    ids = [a for a in sys.argv[2:] if a in SPEC] or IDS
    if cmd == "preview":
        preview(ids)
    if cmd in ("masks",):
        masks(ids)
    if cmd in ("build", "all"):
        build(ids)
    if cmd in ("anim", "all"):
        anim(ids)
    if cmd in ("verify", "all"):
        sys.exit(1 if verify(ids) else 0) if cmd == "verify" else verify(ids)
    if cmd in ("sheet", "all"):
        sheet([i for i in IDS if (E.OUT / f"{i}-card.png").exists()])


if __name__ == "__main__":
    main()
