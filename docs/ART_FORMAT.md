# Art format

One JSON file per character (real-card packs: per card, see below): `packs/<pack>/art/<id>.json`. Built to ANSI with `tools/build_art.py`.

```json
{
  "id": "pikachu",
  "name": "Pikachu",
  "palette": { "k": "#1b1b1f", "y": "#f7d02c", "r": "#e3350d", "w": "#ffffff" },
  "shiny":   { "y": "#f4b92a" },
  "variants": {
    "common":  { "rows": ["....kk....", "..."] },
    "holo":    { "rows": ["..."], "palette": { "s": "#fff6b0" } },
    "fullart": { "rows": ["..."], "palette": { "b": "#2a3a6e" } },
    "gold":    { "rows": ["..."], "palette": { "y": "#d4af37" }, "shiny": { "y": "#e8c86a" } }
  }
}
```

- `rows`: pixel grid, one string per pixel row, all the same width. Each character is a palette key; `.` is transparent (shows the terminal background).
- Palette keys are single Unicode code points, not just ASCII: any letter / digit / symbol character except `.` (backslash and `"` are best avoided). Rich backgrounds (hundreds of colours) use Latin-extended, Greek, Cyrillic and CJK characters as keys; `tools/build_art.py` already accepts them. A pixel is one half-block (1 col x half a line): a sprite drawn at "2 cols x 1 line" per pixel is stored as 2x2 identical keys, and a background may use every grid pixel individually (2x the sprite's resolution each way).
- `palette`: key -> `#rrggbb`. A variant's own `palette` overrides/extends the base one.
- `shiny` (optional): palette overrides for the shiny form, applied on top of the variant palette. A variant may add its own `shiny` overrides.
- Rendering: two pixel rows per text row using `▀`/`▄` with 24-bit color, so a 32x32 grid prints as 32 columns x 16 lines.

## Size limits (the art prints at the top of every new tab, so keep it compact)

`tools/build_art.py` refuses anything larger than **88 x 72 px** (88 columns x 36 lines: `MAX_W`, `MAX_H`).

| art | pixels (w x h) | prints as |
|---|---|---|
| hand-drawn pixel art, low tiers | up to 32 x 28 | <= 32 cols x 14 lines |
| hand-drawn pixel art, high tiers | up to 48 x 32 | <= 48 cols x 16 lines |
| real-card art: the plain sprite (commons) | about 40 x 40 | about 42 cols x 20 lines, 6-7 KB of ANSI |
| real-card art: sprite over the card's scene | 62 x 42 to 80 x 60 (suite3); up to 84 x 70 (Evolving Skies) | up to 84 cols x 35 lines, 30-77 KB of ANSI (suite3) |

The big scene art only prints on rarer pulls, and costs about 1 ms more per pull than a sprite common (a fresh
process reading and building the card text); how fast Windows Terminal draws 77 KB of ANSI is not measured.

## Real-card packs

A real-card pack (`pack.json` `"cards"`, see `PACK_FORMAT.md`) has one art file per card:
`packs/<pack>/art/<card id>.json`, written by `tools/build_realcards.py`. Its `id` is the character (the sprite
name), `card` the pokemontcg.io id, and its only variant is named after the card id, so it builds to
`dist/<pack>/<character>-<card id>[-shiny].ans`. The rows are the unmodified pokemon-colorscripts sprite (2x2 grid
px per sprite px) over the real card's scene; commons are the plain sprite. These files embed Nintendo sprites and
are never committed.

```json
{ "id": "pikachu", "card": "swsh4-170", "name": "Pikachu V", "source": "suite3:pikachu-suite3.json#fullart",
  "palette": { "a": "#f6d02c", "...": "..." }, "shiny": { "a": "#f4b92a" },
  "variants": { "swsh4-170": { "rows": ["..."] } } }
```

## Quality bar (hand-drawn pixel-art packs)

- Real pixel-art craft: clear 1px dark outline (not pure black; a dark hue of the body color), 2-3 shade ramp per color (base, shadow, highlight), readable silhouette at a glance, iconic features exaggerated (Pikachu's black ear tips and red cheeks, Charmander's tail flame, ...).
- Original drawings in the spirit of the characters, not traced game sprites.
- Transparent background for common; the higher variants may add a background panel/scene, sparkles, or a frame, which is what makes them feel rarer.
- Always check your work by rendering: `.venv/Scripts/python tools/build_art.py <id>` then open `previews/<pack>/<id>-<variant>.png` with the Read tool and iterate until it looks good.
