# Pack format

A pack is a folder `packs/<id>/` with:

- `pack.json` — odds, tiers, characters (below)
- `carddata.json` (real-card packs, optional) — the cards' gameplay data, built by `tools/build_carddata.py`
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

## Real-card packs (`cards`)

A pack whose `pack.json` has a `"cards"` object is a **real-card pack**: every card it can drop is a real printed
card, keyed by its [pokemontcg.io](https://pokemontcg.io) id. `packs/pokemon` is one. `characters`, `foil_chance`
and the tiers' `art` are not used (characters come from the cards).

```json
{
  "id": "pokemon", "name": "Pokemon", "shiny_chance": 0.015625,
  "tiers": [
    { "id": "common", "label": "common", "rarity": "Common", "family": "non-foil", "weight": 50000, "skins": {}, "frame": "plain" },
    { "id": "rare-holo", "label": "rare holo", "rarity": "Rare Holo", "family": "holo", "weight": 5000,
      "skins": { "starlight": 10, "cosmos": 10 }, "frame": "holo" },
    { "id": "rare-ultra", "label": "rare ultra", "rarity": "Rare Ultra", "family": "full-art", "weight": 650,
      "skins": { "sunpillar": 10, "illustration-rare": 4 }, "frame": "rainbow" }
  ],
  "cards": {
    "base1-58":  { "character": "pikachu", "tier": "common", "name": "Pikachu", "number": "58/102",
                   "rarity": "Common", "set": "Base", "source": "suite3:pikachu-suite3.json#common" },
    "swsh4-170": { "character": "pikachu", "tier": "rare-ultra", "name": "Pikachu V", "number": "170/185",
                   "rarity": "Rare Ultra", "set": "Vivid Voltage", "source": "suite3:pikachu-suite3.json#fullart" }
  },
  "retired": { "pikachu/common": "base1-58", "pikachu/holo": null, "pikachu/secret-rare": null }
}
```

- **Tiers are the printed rarities**, one tier per rarity, as many as needed, all data:
  - `rarity`: the API's `rarity` string this tier stands for. `tools/build_realcards.py` gives each card the tier
    whose `rarity` is its printed rarity, and refuses a card whose rarity no tier names. A tier may have no
    `rarity` (e.g. `reverse-holo`, a parallel print the API doesn't list as a rarity).
  - `weight`: the tier's odds weight. A pull picks a tier with probability `weight / (sum of the weights of the tiers
    that have at least one built card)`. A tier with no card never rolls; its odds are shared by the others (the same
    as rerolling). There is no fallback art: nothing invented is ever shown.
  - `skins`: the tier's shaders, with relative weights. A pull of a tier with skins opens the skinned tab (one skin,
    by weight); a tier with `{}` (common, uncommon, rare) prints in the plain tab. A skin may serve several tiers.
  - `family` (optional): a grouping for display (`non-foil`, `holo`, `special`, `ultra`, `full-art`, `secret`).
  - `shiny` (optional): `"printed"` on a tier whose real cards print the shiny Pokémon (Rare Shiny, Rare Shiny GX,
    Radiant Rare). Its art is the shiny sprite and has no `-shiny` form, so the shiny roll never applies to it: the
    pull, `pokeshell show ... -shiny` and both binders show it unmarked. Anything that asks for a `-shiny.ans` falls
    back to the regular art when there is none.
  - `frame`, `label`: as above.
  - Switching ladders (5 tiers, 6, or every rarity) is a `pack.json` edit; `pokeshell odds` prints what it means.
- **Cards** (`cards`, written by `tools/build_realcards.py`): `character` is the sprite name, `tier` a tier id,
  `name` and `number` are what the frame's top edge shows (`number` is the printed number, e.g. `170/185`).
  Only cards whose art is built (`dist/<pack>/<character>-<card id>.ans`) can drop; the art and the card text
  (`cards/<id>.json`, docs `CARD_FORMAT.md`) are local-only. The gameplay fields alone ship in `carddata.json`
  (optional; `tools/build_carddata.py`, `tools/README.md`), which `pokeshell collection --json` reads.
- **The roll**: tier by weight (above), then one card of that tier uniformly, then a skin of that tier, then shiny.
  A foil that the spawn gate denies, or that can't find its tab, shows the same character's lowest-tier card in
  place (like tier 0 in other packs).
- **Logging**: `pulls.log` keeps its columns; for a real-card pack the `tier` column is the card's tier id and the
  `art` column is the card id (`...\tpokemon\tpikachu\trare-ultra\tswsh4-170\tsunpillar\t0\t`).

### `retired`: old pulls in the binders

`pulls.log` is append-only and keeps the pulls of art that no longer exists (e.g. the pokemon pack's hand-drawn
art before it became real cards). `retired` maps an old `"<character>/<tier id>"` to what it shows now: a card id
of this pack (an old common is the same Pokemon's real base-set common) or `null` (hidden). Every binder resolves a
pull of a real-card pack the same way (`Resolve-PokeshellPull` in `scripts/lib/common.ps1`):

1. the `art` column is a card id in `cards` and its `character` matches: **that card** (shown in the card's tier);
2. else `retired["<character>/<tier>"]` is a card id: **that card**;
3. else (`null`, or not listed): **hidden**. It stays in `pulls.log`, it just isn't shown or counted.

A card whose art isn't built (`dist/<pack>/<character>-<card id>.ans` missing, `Test-PokeshellCardBuilt`) is
**muted**: it never rolls, it is no binder slot (not in completion, set checklists or totals), and the rule above
treats it as absent from `cards`, so a pull that would show it is hidden and counted with the retired ones. This is
decided when a binder reads the log, so once the card's art is built its pulls come back.

Pulls of packs without `cards` show as logged. `pokeshell binder` / `collection` applies this and says how many
retired pulls it left out; binder-tui and the web export should do the same.
