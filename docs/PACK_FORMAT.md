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
