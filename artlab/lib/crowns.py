"""Terapagos Tera-crystal crown for the gold Pikachu ex (sv8/247), as an OVERLAY on the unmodified sprite.

Built procedurally in sprite-pixel style: crystal shards (triangles) standing on a faceted band, each shard
split into a lit left face and a shaded right face, 1px black outline added around the whole silhouette.
Coordinates are relative to the FLIPPED pikachu sprite (head top at rows 5-6, x 9..19, eye at (14, 9)).

  CROWNS[name] -> (rows, palette)      anchor(name) -> (dx, dy) of the crown's top-left vs the sprite
"""
CPAL = {
    "k": "#000000",
    "W": "#fffdf0",   # shard highlight
    "G": "#fbe08a",   # gold shard, lit face
    "g": "#d9a43c",   # gold shard, shaded face
    "h": "#9c6a1c",   # gold band shadow
    "T": "#5ee6d6",   # teal facet (lit)
    "t": "#1f9a96",   # teal facet (shade)
    "V": "#b48cff",   # violet
    "v": "#6f4ad0",
    "P": "#ff8fc0",   # pink
    "p": "#d04a86",
    "N": "#8ff08a",   # green
    "n": "#2faa4e",
    "B": "#8cc8ff",   # blue
    "b": "#3a74e0",
    "O": "#ffc070",   # orange
    "o": "#e0782a",
    "R": "#ff6a6a",   # red
    "r": "#c02838",
}


def build(W, H, shards, band_top, band, gems):
    """shards: [(tip_x, tip_y, slope, lit, shade)] crystal triangles, drawn back to front (list order),
    each with a lit left face, a shaded right face and a pale ridge glint; where one shard meets
    another a dark seam separates the facets. band: (lit, shade) rows band_top..H-2; gems: 3x3
    diamonds [(x, lit, shade)] set into the band. 1px black outline round the silhouette."""
    owner, col = {}, {}
    H, band_top = H + 1, band_top + 1                # one clear row on top so the tips get an outline
    for sid, (tx, ty, slope, lit, shade) in enumerate(shards):
        ty += 1
        for y in range(ty, band_top + 1):
            half = int((y - ty) / slope)
            for x in range(max(1, tx - half), min(W - 2, tx + half) + 1):
                owner[(x, y)] = sid
                col[(x, y)] = "W" if (x == tx and y == ty + 1) else lit if x <= tx else shade
    seam = {}
    for (x, y), sid in owner.items():
        o = owner.get((x + 1, y))
        if o is not None and o != sid and y < band_top:
            seam[(x, y)] = "h"
    col.update(seam)
    lit, shade = band
    for y in range(band_top, H - 1):
        for x in range(0, W):
            col[(x, y)] = shade if (x + y) % 4 == 0 or y == H - 2 else lit
            owner[(x, y)] = -1
    cy = band_top + (H - 1 - band_top) // 2
    for gx, gl, gs in gems:
        col[(gx, cy)] = gl
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            col[(gx + dx, cy + dy)] = gs if dx > 0 or dy > 0 else gl
    g = [["."] * W for _ in range(H)]
    for (x, y), c in col.items():
        if 0 <= x < W and 0 <= y < H:
            g[y][x] = c
    for x in (0, W - 1):                      # band ends are outline
        for y in range(band_top, H):
            g[y][x] = "k"
    out = [r[:] for r in g]
    for y in range(H):
        for x in range(W):
            if g[y][x] == "." and any(0 <= x + dx < W and 0 <= y + dy < H and g[y + dy][x + dx] not in ".k"
                                      for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out[y][x] = "k"
    for x in range(W):
        out[H - 1][x] = "k" if 0 < x < W - 1 else "."
    rows = ["".join(r) for r in out]
    return rows


# a) tall spiky tiara: five gold shards, the centre one tallest and teal, teal gems in a gold band
TIARA = build(17, 11, [(2, 4, 1.1, "G", "g"), (14, 4, 1.1, "G", "g"), (5, 1, 1.6, "G", "g"),
                       (11, 1, 1.6, "G", "g"), (8, 0, 2.4, "T", "t")], 7, ("G", "g"),
              [(4, "T", "t"), (12, "T", "t")])
# b) low crystal band: short gold nubs, violet/teal gems in a deeper band
BAND = build(17, 7, [(3, 1, 1.0, "G", "g"), (13, 1, 1.0, "G", "g"), (8, 0, 1.0, "T", "t")], 3, ("G", "g"),
             [(4, "V", "v"), (8, "T", "t"), (12, "V", "v")])
# c) rainbow-faceted: the card's crown, a white/teal crest ringed by shards in every Tera hue
RAINBOW = build(17, 11, [(2, 3, 1.0, "P", "p"), (14, 3, 1.0, "V", "v"), (5, 1, 2.2, "N", "n"),
                         (11, 1, 2.2, "B", "b"), (8, 0, 2.6, "W", "T")], 7, ("G", "g"),
                [(3, "R", "r"), (8, "T", "t"), (13, "O", "o")])


def _pal(rows):
    return {k: CPAL[k] for k in {c for r in rows for c in r if c != "."}}


CROWNS = {n: (r, _pal(r)) for n, r in (("tiara", TIARA), ("band", BAND), ("rainbow", RAINBOW))}
# the crown's bottom seam lands on sprite row 7 (just above the brow), centred on the head (x 6..22)
ANCHORS = {"tiara": (6, -4), "band": (6, 0), "rainbow": (6, -4)}


def anchor(name):
    return ANCHORS[name]


if __name__ == "__main__":
    for n, (rows, pal) in CROWNS.items():
        print(n)
        for r in rows:
            print("  " + r)
