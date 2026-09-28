# Art format

One JSON file per character: `packs/<pack>/art/<id>.json`. Built to ANSI with `tools/build_art.py`.

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
- `palette`: key -> `#rrggbb`. A variant's own `palette` overrides/extends the base one.
- `shiny` (optional): palette overrides for the shiny form, applied on top of the variant palette. A variant may add its own `shiny` overrides.
- Rendering: two pixel rows per text row using `▀`/`▄` with 24-bit color, so a 32x32 grid prints as 32 columns x 16 lines.

## Size limits (the art prints at the top of every new tab, so keep it compact)

| variant role | max pixels (w x h) | prints as |
|---|---|---|
| common, holo (or pack tier 1) | 32 x 28 | <= 32 cols x 14 lines |
| fullart, gold (or pack tiers 2-3) | 48 x 32 | <= 48 cols x 16 lines |

## Quality bar

- Real pixel-art craft: clear 1px dark outline (not pure black; a dark hue of the body color), 2-3 shade ramp per color (base, shadow, highlight), readable silhouette at a glance, iconic features exaggerated (Pikachu's black ear tips and red cheeks, Charmander's tail flame, ...).
- Original drawings in the spirit of the characters, not traced game sprites.
- Transparent background for common; the higher variants may add a background panel/scene, sparkles, or a frame, which is what makes them feel rarer.
- Always check your work by rendering: `.venv/Scripts/python tools/build_art.py <id>` then open `previews/<pack>/<id>-<variant>.png` with the Read tool and iterate until it looks good.
