"""suite3 shared helpers: the vendor colorscripts sprite, UNMODIFIED, over a background built at the
full half-block resolution of the art grid.

Resolution
  The art grid (docs/ART_FORMAT.md) prints two grid pixels per text row with half blocks, so ONE grid
  pixel is 1 col x half a line (a square). The colorscripts sprite is stored doubled: each sprite pixel
  is a 2x2 block of grid pixels (2 cols x 1 line). suite2 built everything at sprite scale and doubled
  it; suite3 composes directly on the grid ("fine" pixels), so a background can be up to 2x finer than
  the sprite in each direction.

A Card holds
  bg      float RGB array (FH, FW, 3) in 0..1 -- the scene / foil, before quantisation
  cells   {(fx, fy): (layer, key)} for keyed layers: sprite (2x2 blocks), over (crown), deco (sparkles)
  pals / shiny   per keyed layer {key: hex}; only the sprite has a shiny palette
The background is quantised per tier (few colours for common, many for full art) and then every
distinct background colour gets its own palette key (see KEY_POOL).
"""
import math
import sys
import unicodedata
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

import sprites

LIB = Path(__file__).resolve().parent             # artlab/lib: this code
sys.path.insert(0, str(LIB.parent))
import artpaths  # noqa: E402
LAB = artpaths.DATA                               # the data root: style-lab/ (or $ARTLAB_DATA)
ROOT = artpaths.ROOT
HERE = LAB / "suite3"                             # suite3's data (out/, work/, masks/, <poke>-suite3.json)
SUITE = LAB / "suite"
OUT = HERE / "out"
WORK = HERE / "work"
MASKS = HERE / "masks"
for p in (artpaths.TOOLS, LIB):
    sys.path.insert(0, str(p))
from build_art import to_ansi  # noqa: E402
from render_ansi import render  # noqa: E402

FONT = "C:/Windows/Fonts/consola.ttf"
BLACK = (0, 0, 0)
SPRITE_KEYS = "abcdefghijmnopqrstuvwxyz"     # 'k' is the black outline


def _key_pool():
    """palette keys for non-sprite colours: printable ASCII first, then single BMP code points that are
    letters / digits / symbols (no combining marks, no spaces, no quotes or backslash)"""
    ascii_ = [c for c in "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZlw!#$%&*+-/:;<=>?@^_~|{}()[],'"
              if c not in SPRITE_KEYS + "k."]
    ext = []
    for cp in list(range(0x00C0, 0x0250)) + list(range(0x0391, 0x03FF)) + list(range(0x0400, 0x0482)) + \
            list(range(0x048A, 0x0530)) + list(range(0x4E00, 0x9FA0)):
        ch = chr(cp)
        if unicodedata.category(ch)[0] in "LNS" and ch.isprintable():
            ext.append(ch)
    return ascii_ + ext


KEY_POOL = _key_pool()


def hexrgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def rgbhex(c):
    return "#%02x%02x%02x" % tuple(int(v) for v in c)


def lum(c):
    if isinstance(c, str):
        c = hexrgb(c)
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def to8(a):
    return np.clip(np.round(np.asarray(a) * 255), 0, 255).astype(np.uint8)


# ---- sprite -------------------------------------------------------------------------------
class Sprite:
    """rows of keys + normal/shiny palettes, straight from the colorscripts large sprite"""

    def __init__(self, name, flip=False):
        n, s = sprites.load(name), sprites.load(name, shiny=True)
        assert len(n) == len(s) and len(n[0]) == len(s[0]), name
        pairs, rows = {}, []
        for rn, rs in zip(n, s):
            row = ""
            for cn, cs in zip(rn, rs):
                assert (cn is None) == (cs is None), name
                if cn is None:
                    row += "."
                    continue
                if (cn, cs) not in pairs:
                    pairs[(cn, cs)] = "k" if cn == BLACK and cs == BLACK else SPRITE_KEYS[len([k for k in pairs.values() if k != "k"])]
                row += pairs[(cn, cs)]
            rows.append(row[::-1] if flip else row)
        self.name, self.flip, self.rows = name, flip, rows
        self.pal = {k: rgbhex(cn) for (cn, cs), k in pairs.items()}
        self.shiny = {k: rgbhex(cs) for (cn, cs), k in pairs.items()}
        self.w, self.h = len(rows[0]), len(rows)


def gold_ramp(stops, n):
    """interpolate a dark->light hex ramp to n levels"""
    cs = np.array([hexrgb(s) for s in stops], float)
    t = np.linspace(0, len(cs) - 1, n)
    out = []
    for v in t:
        i = min(int(v), len(cs) - 2)
        f = v - i
        out.append(cs[i] * (1 - f) + cs[i + 1] * f)
    return [rgbhex(c) for c in out]


def gold_remap(spr, ramp, shiny_ramp=None, special=None, lo=0.3, hi=0.86):
    """palette remap of the sprite onto a (long) gold ramp. suite2 mapped linear luminance onto 5 ramp
    steps, so colours of similar luminance but different role (Bulbasaur's bulb vs body) collapsed.
    Here the level is a blend of linear luminance and luminance RANK over the sprite's distinct colours,
    which spreads close shades apart and keeps the sprite's internal shading. Black stays black, pure
    white stays the top of the ramp, the dark greys go to the bottom of the range, `special` pins hues
    (the cheeks). Returns (normal pal, shiny pal)."""
    def one(src, rp):
        keys = [k for k in src if k != "k" and src[k].lower() != "#ffffff"]
        ls = {k: lum(src[k]) for k in keys}
        order = sorted(set(round(v, 1) for v in ls.values()))
        vlo, vhi = min(ls.values()), max(ls.values())
        n = len(rp)
        out = {"k": "#000000"}
        for k, c in src.items():
            if k == "k":
                continue
            c = c.lower()
            if c == "#ffffff":
                out[k] = rp[-1]
            elif special and c in special:
                out[k] = special[c]
            else:
                lin = (ls[k] - vlo) / max(1, vhi - vlo)
                rank = order.index(round(ls[k], 1)) / max(1, len(order) - 1)
                t = (0.45 * lin + 0.55 * rank) ** 1.2
                if ls[k] < 60:                      # the sprite's dark greys (eyes, inner strokes)
                    t = min(t, 0.12)
                out[k] = rp[round((lo + (hi - lo) * t) * (n - 1))]
        return out
    return one(spr.pal, ramp), one(spr.shiny, shiny_ramp or ramp)


# ---- the card composite ---------------------------------------------------------------------
class Card:
    def __init__(self, W, H):
        self.W, self.H = W, H                 # sprite px
        self.FW, self.FH = 2 * W, 2 * H       # grid (fine) px
        self.bg = None                        # float (FH, FW, 3) or None (transparent)
        self.bgq = None                       # quantised bg, uint8 (FH, FW, 3)
        self.cells = {}
        self.pals, self.shiny, self.meta = {}, {}, {}
        self.off = (0, 0)

    # keyed layers
    def put(self, layer, rows, ox, oy, pal, shiny=None, scale=2, skip="."):
        """rows at sprite scale (scale=2, ox/oy in sprite px) or grid scale (scale=1, grid px)"""
        self.pals.setdefault(layer, {}).update(pal)
        if shiny:
            self.shiny.setdefault(layer, {}).update(shiny)
        for j, r in enumerate(rows):
            for i, ch in enumerate(r):
                if ch in skip:
                    continue
                for a in range(scale):
                    for b in range(scale):
                        x, y = (ox + i) * scale + a, (oy + j) * scale + b
                        if 0 <= x < self.FW and 0 <= y < self.FH:
                            self.cells[(x, y)] = (layer, ch)
        return self

    def put_sprite(self, spr, A, B, pal=None, shiny=None):
        self.off = (A, B)
        self.spr = spr
        return self.put("sprite", spr.rows, A, B, pal or spr.pal, shiny or spr.shiny)

    def layer_at(self, x, y):
        c = self.cells.get((x, y))
        return c[0] if c else ("bg" if self.bg is not None else None)

    def fig_mask(self, layers=("sprite", "over")):
        m = np.zeros((self.FH, self.FW), bool)
        for (x, y), (L, k) in self.cells.items():
            if L in layers:
                m[y, x] = True
        return m

    def outline_mask(self):
        m = np.zeros((self.FH, self.FW), bool)
        for (x, y), (L, k) in self.cells.items():
            if L in ("sprite", "over") and k == "k":
                m[y, x] = True
        return m

    def dist(self, layers=("sprite", "over")):
        """grid-px distance of every cell to the figure (0 inside)"""
        from scipy import ndimage
        return ndimage.distance_transform_edt(~self.fig_mask(layers))

    def colour(self, x, y, shiny=False):
        c = self.cells.get((x, y))
        if c is None:
            if self.bgq is None:
                return None
            return tuple(int(v) for v in self.bgq[y, x])
        L, k = c
        if shiny and k in self.shiny.get(L, {}):
            return hexrgb(self.shiny[L][k])
        return hexrgb(self.pals[L][k])

    def rgb(self, shiny=False):
        return [[self.colour(x, y, shiny) for x in range(self.FW)] for y in range(self.FH)]

    def n_bg_colours(self):
        vis = [tuple(self.bgq[y, x]) for y in range(self.FH) for x in range(self.FW) if (x, y) not in self.cells] \
            if self.bgq is not None else []
        return len(set(vis))


def keyed(card):
    """-> rows (chars, grid px), palette {char: hex}, shiny overrides {char: hex}. Sprite keys keep their
    own chars (so the ART_FORMAT base palette / shiny apply); every other colour gets a pool key."""
    pool = iter(KEY_POOL)
    tok2c, pal, shiny = {}, {}, {}
    rows = []
    for y in range(card.FH):
        s = []
        for x in range(card.FW):
            c = card.cells.get((x, y))
            if c is None:
                if card.bgq is None:
                    s.append(".")
                    continue
                tok = ("rgb", rgbhex(card.bgq[y, x]))
            elif c[0] == "sprite":
                tok = c
            else:
                tok = ("rgb", card.pals[c[0]][c[1]])
            if tok not in tok2c:
                if tok[0] == "sprite":
                    ch = tok[1]
                    pal[ch] = card.pals["sprite"][ch]
                    if ch in card.shiny.get("sprite", {}):
                        shiny[ch] = card.shiny["sprite"][ch]
                else:
                    ch = next(pool)
                    pal[ch] = tok[1]
                tok2c[tok] = ch
            s.append(tok2c[tok])
        rows.append("".join(s))
    return rows, pal, shiny


# ---- card images, masks, inpainting -----------------------------------------------------------
def card_img(ref):
    return np.asarray(Image.open(SUITE / f"{ref}.png").convert("RGB")).astype(float) / 255


def mask(name):
    return np.asarray(Image.open(MASKS / f"{name}.png")) > 0


def _resize_f(a, size, resample=Image.BILINEAR):
    return np.stack([np.asarray(Image.fromarray(a[..., c].astype(np.float32), "F").resize(size, resample))
                     for c in range(a.shape[2])], -1)


def pushpull(rgb, known):
    """smooth membrane fill of the unknown pixels (multi-scale push-pull): no streaks, no blobs"""
    img = rgb * known[..., None]
    w = known.astype(float)
    pyr = [(img, w)]
    while min(w.shape) > 2:
        h, wd = w.shape
        h2, w2 = (h + 1) // 2, (wd + 1) // 2
        img = np.pad(img, ((0, h2 * 2 - h), (0, w2 * 2 - wd), (0, 0)), mode="edge")
        w = np.pad(w, ((0, h2 * 2 - h), (0, w2 * 2 - wd)), mode="edge")
        img = img.reshape(h2, 2, w2, 2, 3).sum((1, 3))
        w = w.reshape(h2, 2, w2, 2).sum((1, 3))
        s = np.minimum(w, 1) / np.maximum(w, 1e-9)
        img, w = img * s[..., None], np.minimum(w, 1)
        pyr.append((img, w))
    col = pyr[-1][0] / np.maximum(pyr[-1][1], 1e-9)[..., None]
    for img, w in reversed(pyr[:-1]):
        up = _resize_f(col, (w.shape[1], w.shape[0]))
        col = img + up * (1 - w)[..., None]
    return col


def colour_grow(rgb, m, reach=24, tol=16, k=4):
    """extend the Pokemon mask to nearby pixels of the Pokemon's own colours (the scraps the traced
    mask missed: Charmander's orange edge, tail tips)"""
    from scipy import ndimage
    from skimage.color import rgb2lab
    from sklearn.cluster import KMeans
    lab = rgb2lab(rgb)
    inner = ndimage.binary_erosion(m, iterations=6)
    pts = lab[inner] if inner.sum() > 50 else lab[m]
    cent = KMeans(k, n_init=3, random_state=0).fit(pts[:: max(1, len(pts) // 4000)]).cluster_centers_
    near = ndimage.binary_dilation(m, iterations=reach) & ~m
    d = np.min(np.linalg.norm(lab[..., None, :] - cent[None, None], axis=-1), -1)
    add = near & (d < tol)
    # only keep additions connected to the mask
    lbl, _ = ndimage.label(add | m)
    keep = np.unique(lbl[m])
    return m | (np.isin(lbl, keep[keep > 0]) & add)


def clean_card(ref, maskname=None, grow=0, boxes=(), win=None, cgrow=None):
    """the card with the real Pokemon (mask) and furniture boxes smoothly inpainted"""
    from scipy import ndimage
    rgb = card_img(ref)
    m = mask(maskname).copy() if maskname else np.zeros(rgb.shape[:2], bool)
    if cgrow and maskname:
        m = colour_grow(rgb, m, **cgrow)
    if grow:
        m = ndimage.binary_dilation(m, iterations=grow)
    for (a, b, c, d) in boxes:
        m[max(0, b):d, max(0, a):c] = True
    if win:
        a, b, c, d = win
        out = np.ones(m.shape, bool)
        out[b:d, a:c] = False
        m |= out
    return pushpull(rgb, ~m), m


def sample(rgb, x0, y0, S, W, H, resample=Image.LANCZOS):
    """card region starting at (x0, y0), S card px per OUTPUT px, to a (H, W, 3) float array"""
    X0, Y0 = int(np.floor(x0)), int(np.floor(y0))
    X1, Y1 = int(np.ceil(x0 + W * S)), int(np.ceil(y0 + H * S))
    h, w = rgb.shape[:2]
    pad = ((max(0, -Y0), max(0, Y1 - h)), (max(0, -X0), max(0, X1 - w)), (0, 0))
    big = np.pad(rgb, pad, mode="symmetric")
    big = big[Y0 + pad[0][0]: Y1 + pad[0][0], X0 + pad[1][0]: X1 + pad[1][0]]
    im = Image.fromarray(to8(big)).resize((W, H), resample)
    return np.asarray(im).astype(float) / 255


def anchor(maskname, x0, y0, S, spr, dx=0, dy=0):
    """sprite offset (sprite px) so its bottom-centre sits on the real Pokemon's bottom-centre"""
    m = mask(maskname)
    ys, xs = np.nonzero(m)
    cx = ((xs.min() + xs.max()) / 2 - x0) / S
    by = (ys.max() - y0) / S
    return round(cx - spr.w / 2) + dx, round(by - spr.h) + dy


# ---- colour ops -----------------------------------------------------------------------------
def tone(a, sat=1.0, bright=1.0, gamma=1.0, lift=0.0):
    from skimage.color import rgb2hsv, hsv2rgb
    hsv = rgb2hsv(np.clip(a, 0, 1))
    hsv[..., 1] = np.clip(hsv[..., 1] * sat, 0, 1)
    hsv[..., 2] = np.clip(lift + (hsv[..., 2] ** gamma) * bright, 0, 1)
    return hsv2rgb(hsv)


def hsv(h, s, v):
    from colorsys import hsv_to_rgb
    return np.array(hsv_to_rgb(h % 1, s, v))


def kmeans_q(a, n, seed=0, ignore=None):
    """quantise to n colours with k-means in Lab (fit on the visible pixels)"""
    from skimage.color import rgb2lab, lab2rgb
    from sklearn.cluster import KMeans
    lab = rgb2lab(np.clip(a, 0, 1))
    fit = lab[~ignore] if ignore is not None else lab.reshape(-1, 3)
    km = KMeans(n, n_init=6, random_state=seed).fit(fit.reshape(-1, 3))
    lbl = km.predict(lab.reshape(-1, 3)).reshape(a.shape[:2])
    pal = np.clip(lab2rgb(km.cluster_centers_[None])[0], 0, 1)
    return pal[lbl], lbl, pal


def median_q(a, n):
    """near-truecolour: median-cut to n colours, no dithering"""
    im = Image.fromarray(to8(a)).quantize(n, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    return np.asarray(im.convert("RGB")).astype(float) / 255


def orphan_clean(lbl, passes=2):
    """single cells whose label no 4-neighbour shares take the 8-neighbour majority"""
    H, W = lbl.shape
    for _ in range(passes):
        new = lbl.copy()
        for y in range(H):
            for x in range(W):
                n4 = [lbl[yy, xx] for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)) if 0 <= yy < H and 0 <= xx < W]
                if lbl[y, x] not in n4:
                    n8 = [lbl[yy, xx] for yy in range(y - 1, y + 2) for xx in range(x - 1, x + 2)
                          if (yy, xx) != (y, x) and 0 <= yy < H and 0 <= xx < W]
                    v, c = np.unique(n8, return_counts=True)
                    new[y, x] = v[c.argmax()]
        lbl = new
    return lbl


def blur(a, r):
    from scipy import ndimage
    return np.stack([ndimage.gaussian_filter(a[..., c], r, mode="nearest") for c in range(3)], -1)


def lerp(a, b, t):
    t = np.asarray(t, float)
    if t.ndim == 2:
        t = t[..., None]
    return a + (np.asarray(b, float) - a) * t


# ---- focus / light effects (on the float bg, before quantisation) ------------------------------
def focus_halo(card, a, radius=7, dark=0.7, soft=1.6):
    """darker, blurred zone just behind the sprite: separates it from busy scenery"""
    d = card.dist()
    t = np.clip(1 - (d - 1) / radius, 0, 1) ** 1.3
    return lerp(a, blur(a, soft) * dark, t)


def radial_glow(card, a, colour, radius, strength=0.6, rays=0, ray_amt=0.5, centre=None, twist=0.0):
    """additive light centred behind the sprite; rays > 0 adds a sunburst"""
    H, W = a.shape[:2]
    cx, cy = centre if centre else fig_centre(card)
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.hypot(xx - cx, yy - cy)
    g = np.clip(1 - r / radius, 0, 1) ** 1.6
    if rays:
        th = np.arctan2(yy - cy, xx - cx) + twist
        ray = (0.5 + 0.5 * np.cos(rays * th)) ** 5
        g = g * (1 - ray_amt) + g * ray_amt * ray * 2.2 + np.clip(1 - r / (radius * 1.6), 0, 1) * ray * ray_amt * 0.5
    return np.clip(a + np.asarray(colour)[None, None] * (g * strength)[..., None], 0, 1)


def vignette(a, strength=0.55, power=2.2, tint=None):
    H, W = a.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W]
    u = np.maximum(np.abs(xx - (W - 1) / 2) / (W / 2), np.abs(yy - (H - 1) / 2) / (H / 2))
    r = np.hypot((xx - (W - 1) / 2) / (W / 2), (yy - (H - 1) / 2) / (H / 2)) / 1.414
    v = np.clip(0.55 * u ** 3 + 0.6 * r ** power, 0, 1)
    if tint is not None:                        # darken toward a deep tint (keeps hues rich, no mud)
        return lerp(a, np.asarray(tint, float) * 0.6 + a * 0.25, strength * v)
    return a * (1 - strength * v)[..., None]


def fig_centre(card):
    ys, xs = np.nonzero(card.fig_mask(("sprite",)))
    return xs.mean(), ys.mean()


def rim(card, q, colour=(1, 1, 1), amt=0.45, width=1):
    """after quantisation: bg cells within `width` of the sprite silhouette lifted toward `colour`
    (keeps the black outline readable on dark scenery). Works on the uint8 quantised bg."""
    d = card.dist()
    t = (d > 0) & (d <= width + 0.01)
    out = q.astype(float)
    out[t] = out[t] + (np.asarray(colour, float) * 255 - out[t]) * amt
    return np.round(out).astype(np.uint8)


def finish(card, a, n=None, method="kmeans", seed=0):
    """quantise the float bg (colour budget per tier) and store it"""
    card.bg = a
    ign = card.fig_mask()
    if n is None:
        card.bgq = to8(a)
    elif method == "kmeans":
        q, _, _ = kmeans_q(a, n, seed, ignore=ign)
        card.bgq = to8(q)
    else:
        card.bgq = to8(median_q(a, n))
    return card


# ---- sparkles (grid px) --------------------------------------------------------------------------
def star_rows(stage):
    """4-point sparkle centred at (3, 3): keys L (core), l (mid), j (tip)"""
    g = [["."] * 7 for _ in range(7)]
    if stage == 1:
        g[3][3] = "l"
    elif stage == 2:
        g[3][3] = "L"
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            g[3 + dy][3 + dx] = "j"
    elif stage >= 3:
        g[3][3] = "L"
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            g[3 + dy][3 + dx] = "l"
            g[3 + 2 * dy][3 + 2 * dx] = "j"
        g[0][3] = g[6][3] = "j"
    return ["".join(r) for r in g]


def sparkle(card, x, y, stage, pal, layer="deco"):
    """4-point sparkle at grid px (x, y), drawn only over the background"""
    card.pals.setdefault(layer, {}).update(pal)
    for j, r in enumerate(star_rows(stage)):
        for i, ch in enumerate(r):
            X, Y = x - 3 + i, y - 3 + j
            if ch != "." and 0 <= X < card.FW and 0 <= Y < card.FH and card.cells.get((X, Y), ("bg",))[0] in ("bg", "deco"):
                card.cells[(X, Y)] = (layer, ch)


# ---- rendering -----------------------------------------------------------------------------
def term_png(rows, pal, path):
    """rows are grid px; prints as the terminal would; also writes the .ans"""
    used = {c for r in rows for c in r if c != "."}
    ans = to_ansi(rows, {k: pal[k] for k in used})
    path = Path(path)
    path.with_suffix(".ans").write_text(ans, encoding="utf-8", newline="\n")
    render(ans, str(path))
    return Image.open(path).convert("RGB")


def region(ref, x0, y0, x1, y1, height):
    reg = Image.open(SUITE / f"{ref}.png").convert("RGB").crop((round(x0), round(y0), round(x1), round(y1)))
    return reg.resize((max(1, round(reg.width * height / reg.height)), height), Image.LANCZOS)
