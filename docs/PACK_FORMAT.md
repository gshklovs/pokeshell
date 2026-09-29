# Pack format

A pack is a folder `packs/<id>/` with:

- `pack.json` — odds, tiers, characters (below)
- `shaders/<skin>.hlsl` — Windows Terminal pixel shaders (the holo/foil skins); see `docs/SHADER_SPEC.md`
- `art/<character>.json` — pixel art, one file per character, with one variant per art name used by the tiers; see `docs/ART_FORMAT.md`

## pack.json

```json
{
  "id": "pokemon",
  "name": "Pokemon",
  "foil_chance": 0.20,          // odds a new tab is a foil pull (tiers after the first); otherwise tier 0
  "shiny_chance": 0.015625,     // odds any pull's art uses the shiny palette (1/64)
  "characters": ["bulbasaur", "charmander", "squirtle", "pikachu"],
  "tiers": [                    // tier 0 = the non-foil tier (plain tab, no shader)
    { "id": "common", "label": "common", "art": "common", "skins": {} },
    { "id": "holo", "label": "holo", "art": "holo", "skins": { "starlight": 10, "sheen": 10 } },
    ...
  ]
}
```

- A foil pull picks a skin across all foil tiers, weighted by the skin weights; the tier it belongs to decides the label and which art variant is shown.
- The character is picked uniformly from `characters`; every character must define every `art` variant named by the tiers.
- The banner printed under the art reads `<label> : <character name>` (plus `shiny` when shiny), e.g. `secret rare : Pikachu`.

### Optional keys

```json
{
  "names": { "mr-mime": "Mr. Mime" },   // display names (otherwise read from art/<id>.json, else the title-cased id)
  "tags":  { "mr-mime": "#122" },       // short text for the right of a card frame's top edge
  "tiers": [ { "id": "holo", "label": "holo", "art": "common", "skins": { "sheen": 10 }, "frame": "silver" } ]
}
```

- `frame` on a tier draws that tier's pulls inside a rounded box-drawing card frame instead of the banner:
  name (with a `✦` when shiny) and tag on the top edge, the label on the bottom edge, art height + 2 lines.
  The value is a preset (`plain`, `silver`, `holo`, `rainbow`, `gold`) or a list of `#rrggbb` gradient stops,
  e.g. `["#ff0000", "#0000ff"]`, or a style object (see Frame styles below). Tiers without `frame` print as before.
- With frames, tiers can share one art variant: `pokeshell show <pack>/<character> <variant>` also accepts a
  tier id, a tier label (`secret-rare`) or a frame preset name (`gold`) as the variant.

### Frame styles

A tier's `frame` can also be an object naming a **style**, a card frame drawn by its own code instead of the
rounded box:

```json
{
  "names":        { "luffy": "Luffy" },
  "poster_names": { "luffy": "MONKEY·D·LUFFY" },   // optional: the full name a style prints (else the name, upper-cased)
  "bounties":     { "luffy": "3,000,000,000" },    // optional: the wanted poster's bounty (else the tag)
  "tiers": [
    { "id": "common", "label": "common", "art": "common", "skins": {},
      "frame": { "style": "wanted", "palette": "common" } },
    { "id": "manga-rare", "label": "manga rare", "art": "manga", "skins": { "manga-halftone": 5 },
      "frame": { "style": "wanted", "palette": "manga" } }
  ]
}
```

- `wanted` — a One Piece wanted poster: aged paper all round (background-colored cells) with torn corners,
  nibbled edges and stains, `W A N T E D` on the top edge, the poster name under the art, the bounty
  (`฿ <bounty>-`) bottom left and the upper-cased label bottom right (with a `✦` when shiny).
  Art height + 3 lines, art width + 4 columns (wider when the texts need it).
  - `palette`: `common` (parchment), `super-rare` (darker, red rarity), `secret-rare` (gold-leaf gradient paper),
    `manga` (newsprint white with a screentone speckle, red rarity; `manga-rare` works too). Default `common`.
  - `paper`, `stain`, `ink`, `accent`: optional `#rrggbb` overrides of the palette's paper, stain, text ink and
    bounty/rarity ink.
  - `seed`: the stain / nibble pattern (deterministic: the same card always draws the same poster).
    Defaults to the tier id, so tiers sharing a palette still differ.
- Keys other than `style` are passed to the style as `key=value`; the pack loader flattens the object to one
  string (`wanted;palette=manga;seed=manga-rare`), which is what the roll cache stores and a foil passes to
  its tab. An unknown style draws a plain grey rounded box.
- `display picture` still prints only the art.
