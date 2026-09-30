# Real booster packs

`pokeshell pack open <set>` opens one **real booster** of a set we serve: the set's printed slot layout, rolled with
its published pull rates, from the real cards we have built. `pokeshell pack open random` rolls the set too, weighted by
what a real pack costs: cheap modern packs come up every few opens, a vintage Base Set or Neo Genesis pack about once in
60 ([Random packs](#random-packs-weighted-by-price)). Every card goes into your binder at once, caught (a pack
is already earned; there is no "use the tab" step). The pack token ledger lets anything that awards packs (a game, a
script, you) grant them; `pack open` spends one.

The data is `packs/pokemon/boosters.json`; the roll is `scripts/lib/booster.ps1` (the model, recording, tokens) and
`scripts/lib/Booster.cs` (the dice, the booster index and the open, compiled once into
`<state>\pokeshell-booster-*.dll`); the tests are `tests/test-boosters.ps1`.

## Commands

| command | |
|---|---|
| `pokeshell pack sets [--json]` | the boosters: set, name, series, release date, cards served / printed, pack size, art hints |
| `pokeshell pack odds <set> [--json]` | a set's slots: each outcome's published rate, printed cards, served cards and the odds we roll |
| `pokeshell pack odds random [--json]` | the set table of `pack open random`: each set's pack price, source and chance |
| `pokeshell pack open <set> [--json] [--free] [--seed N] [--export] [--delay ms]` | open one pack (below) |
| `pokeshell pack open random [--json] [...]` (or `--random`) | open a pack of a random set, weighted by pack price |
| `pokeshell pack grant <n> --reason <text> [--json]` | add `n` pack tokens (1-1000) |
| `pokeshell pack tokens [--json]` | the balance and the last changes |

`<set>` is a set id (`swsh7`), an alias (`evs`, `30th`, `cz`, `hf`, `base`, `brs`, `neo`, `lor`) or a word of its name
(`evolving`, `zenith`). `pokeshell pack <pack id>` still chooses the pack new tabs pull from; `open`, `sets`, `odds`,
`grant` and `tokens` are the booster subcommands.

`pack open` options:
- `--free`: open without spending a token (tests, demos). Without it, a pack costs one token, and with none it's
  refused (`code: "no-tokens"`, exit 1) and nothing is rolled or recorded.
- `--seed N`: a reproducible pack (System.Random; with `random`, the set is the first draw, then the pack). Without it every draw comes from the OS CSPRNG
  (`RandomNumberGenerator`), so a pack can't be predicted or replayed; the JSON says `"secure": true`.
- `--export`: after recording, update the web export so every `image` below exists, including shiny forms (the export
  only writes a shiny image once it has been pulled). It is incremental: `binder.exe --export-web <state>\web --only
  <this pack's card ids>` renders only those cards' images and rewrites `data.json` / `binder.html` (every other image
  is taken from the art cache as it is, nothing is pruned; `pokeshell binder --web` still does the full export).
- In a terminal (no `--json`): the cards are revealed one by one in their normal card rendering (the tier's frame,
  the shiny palette), rarest last, with a tease line before a big hit; any key shows the next card, `s` skips to the
  summary. `--delay <ms>` reveals on a timer instead; with output redirected there are no waits.

### `pack open --json`

stdout is one line of JSON with the conventions of the other JSON commands (README "For other tools",
`scripts/lib/jsonapi.ps1`, where `version --json` lists these commands): ASCII only (anything else as `\uXXXX`), and on
a failure `{"error": ...}` with exit code 1:

```json
{ "set": "swsh7", "setName": "Evolving Skies", "setChance": 0.106441, "setOneIn": 9.4, "setPrice": 43.97, "random": false,
  "packId": "01M3QTARN56Q9RD141B01M770D", "secure": true,
  "cards": [
    { "id": "swsh7-44", "name": "Bergmite", "number": "44/203", "rarity": "Common", "tier": "common", "tierLabel": "common",
      "slot": "common", "outcome": "common", "finish": "normal", "fx": "plain", "hit": 0, "shiny": false, "isNew": true,
      "oneIn": 1, "character": "bergmite", "setName": "Evolving Skies",
      "image": "img/pokemon/bergmite/swsh7-44.png", "pullId": "01M3QTARN5B0A9GMPGH4S41BSN" },
    ...
  ],
  "spent": 1, "tokens": 2, "imageRoot": "C:\\Users\\you\\AppData\\Local\\pokeshell\\web" }
```

- `set`, `setName`: the set opened. `setChance` / `setOneIn`: that set's chance to be the one `pack open random` opens
  (so a game can say "you got a Base Set pack! (1 in 60.7)"), `setPrice` its pack price in USD; `random`: true when
  the set was rolled (`pack open random`), false when it was chosen. `setChance` is 0 and `setOneIn` null for a set
  with no price.
- `cards` are in **reveal order, rarest last**: by `hit`, then by how rare that kind of hit is (`oneIn`), then the
  printed pack's order (commons first, the rare at the back).
- `rarity` is the printed rarity (the pokemontcg.io string), `tier` our tier id for it (`packs/pokemon/pack.json`).
- `slot` is the booster slot it came from (`common`, `uncommon`, `reverse`, `rare`, `illustration`, `pikachu`),
  `outcome` the slot's outcome that rolled (`reverse holo`, `galarian gallery`, `alternate art V`, `gold`, ...).
- `finish`: `normal`, `reverse` (a reverse-holo print of a non-foil card) or `foil` (30th Celebration: every card).
- `fx`: the effect family to show: `plain`, `reverse`, `holo`, `full-art`, `alt-art`, `rainbow`, `gold`, `radiant`,
  `shiny` (Shiny Vault / shiny rares). From the tier, overridden per outcome in boosters.json (alternate arts are
  `alt-art`, the Galarian Gallery / Trainer Gallery V cards `full-art`, Futuristic Rares `rainbow`); a non-normal
  finish turns `plain` into `reverse`.
- `hit` (0-5): how big the reveal is. plain 0; reverse and a plain rare 1; holo 2; full-art, radiant, shiny 3;
  alt-art, rainbow 4; gold 5; a shiny roll adds 1 (at most 5).
- `shiny`: our shiny roll (the pack's `shiny_chance`, 1 in 64, as for tab pulls; never on tiers that print the shiny
  Pokemon, and only when the card has shiny art).
- `isNew`: you had not caught this card before this pack (a second copy in the same pack isn't new).
- `oneIn`: the chance of this kind of hit in its slot, as "1 in N packs".
- `image`: the card's picture in the web export, relative to `imageRoot` (`<state>\web`, what `binder --web` writes;
  `img/<pack>/<character>/<card id>[-shiny].png`, 1 px per art pixel: scale it with `image-rendering: pixelated`). Run
  with `--export` (or `pokeshell binder --web`) to make sure it exists.
- `png`: the image's full path once the web export has it (as in `collection --json`), else `null`.
- `pullId`: the card's pull id in `pulls.log`. `card` and `pull` repeat `id` and `pullId` under the names the arena
  SPEC uses.
- Errors (with `--json`): `{ "error": "...", "message": "...", "code": "no-tokens" | "no-sets" | "error", "tokens": n }` and exit
  code 1 (`message`, `code` and `tokens` are added to the usual `{"error"}`; `message` repeats it).

`pack sets --json` is `{ pack, tokens, priceExponent, sets: [{ id, name, series, released, cardSets, cards, inPack,
printed, packSize, realPackSize, openable, price, priceSource: { site, url, date, variant, note? }, chance, oneIn,
odds: [{ tier, weight }], art: { colors, accent, hero, motif }, hero, slots: [{ id, count,
finish }] }] }`. `odds` is the expected number of cards of each tier in one pack (they add up to `packSize`).
`cards` counts the cards we serve (built art), `printed` the set's printed cards, `packSize` our pack (unserved slots
dropped), `realPackSize` the printed pack without the code card, `hero` the hero card's `image` path, `chance` /
`oneIn` the set's chance in `pack open random`.

`pack odds random --json` is `{ set: "random", priceExponent, sets: [{ set, name, price, priceSource, openable, chance,
oneIn }] }`.

### What gets recorded

One `pulls.log` line per card, in reveal order, in the normal format with no `pending` flag (so every binder counts
it as caught at once):

```
2026-09-29T17:09:48  pokemon  bergmite  common  swsh7-44    0  booster:swsh7  id=<ulid>  boot=<s>  card=swsh7-44  booster=<pack id>  slot=common  finish=normal
```

### Pack tokens

`<state>\tokens.log`, append-only TSV: `time  delta  reason  id=<ulid>  [set=<set>  pack=<pack id>  [random=1]]`.
`grant` appends `+n` with its reason, `open` appends `-1` with the set and the pack id (and `random=1` when the set was
rolled); the balance is the sum. A random open rolls the set inside the lock and spends exactly one token. Opens and grants run
under a per-state named mutex, so concurrent opens can't spend the same token twice (the test starts 4 opens at once
with 2 tokens: exactly 2 open). pokeshell has no idea what earns a token; that's up to whoever calls `grant`.

## Random packs, weighted by price

`pokeshell pack open random` (what the arena calls when you spend a token) doesn't let you pick: it rolls the set, then
the pack. Each set's weight is its sealed booster pack's market price to the power `-k`:

    weight(set) = price ^ -k        chance(set) = weight(set) / sum of the weights of the openable sets

`k` is `priceExponent` in boosters.json, one constant for the whole curve. k = 1 would make a pack exactly as likely as
it is affordable (a $700 Neo Genesis pack about 1 in 190 opens), which felt out of reach; k = 0.5 makes the vintage
packs 1 in 30 each, one vintage pack every 17 opens, which stops being special. **k = 0.7**: each vintage pack about 1
in 60-70 (one of the two every 32 opens), the cheap modern sets every 5 opens, the $45 chase sets every 10. Only sets
we can open (built cards) and that have a price are in the draw; the others' share is spread over the rest.

### Prices

One sealed booster pack, USD, PriceCharting's ungraded ("loose") price for the set's booster-pack product, seen
**2026-09-29** (PriceCharting shows no as-of date; its recent-sales lists run through late September 2026). The
TCGplayer market price PriceCharting shows beside it is within a few percent for every modern set. Stored per set in
boosters.json as `price` and `priceSource` (`site`, `url`, `date`, `variant`, `note`).

| set | pack price | print run / variant | source | notes |
|---|---:|---|---|---|
| Evolving Skies (swsh7) | $43.97 | English, any pack art | [PriceCharting](https://www.pricecharting.com/game/pokemon-evolving-skies/booster-pack) | TCGplayer $45.80; recent sales $35-56 |
| 30th Celebration (me55) | $16.91 | English | [PriceCharting](https://www.pricecharting.com/game/pokemon-30th-celebration/booster-pack) | released 2026-09-16: about two weeks of sales (27, $14.75-20.50), so the price may still move |
| Crown Zenith (swsh12pt5) | $25.98 | English loose pack | [PriceCharting](https://www.pricecharting.com/game/pokemon-crown-zenith/booster-pack) | no booster box: loose packs come from ETBs, tins and collections; TCGplayer $25.38 |
| Hidden Fates (sm115) | $47.98 | English, any pack art | [PriceCharting](https://www.pricecharting.com/game/pokemon-hidden-fates/booster-pack) | TCGplayer $49.15; recent sales $36-50 |
| Base Set (base1) | $632.50 | **Unlimited** (1999-2000), the Charizard / Blastoise / Venusaur arts averaged | [PriceCharting](https://www.pricecharting.com/game/pokemon-base-set/booster-pack) | a range in practice: sales $254-1,375 (light vs heavy packs). Shadowless $3,529.21, 1st Edition $6,468.68: we model Unlimited |
| Brilliant Stars (swsh9) | $16.24 | English, any pack art | [PriceCharting](https://www.pricecharting.com/game/pokemon-brilliant-stars/booster-pack) | TCGplayer $16.61; typical sales $15-18 |
| Neo Genesis (neo1) | $741.61 | **Unlimited** (2000), the four pack arts averaged | [PriceCharting](https://www.pricecharting.com/game/pokemon-neo-genesis/booster-pack) | a range in practice: sales $500-1,375 (heavy packs cost more; plain ones $550-700). 1st Edition $902.45 |
| Lost Origin (swsh11) | $19.68 | English, any pack art | [PriceCharting](https://www.pricecharting.com/game/pokemon-lost-origin/booster-pack) | TCGplayer $19.56; recent sales $17-22 |

The vintage prices are averages over packs that sell across a wide range (weighed "heavy" packs, likelier to hold the
holo, fetch double), so they are the least precise; with k = 0.7 a 20% error in one moves its chance by about 13%.

### The chances (k = 0.7, all eight sets openable)

| set | price | chance | 1 in |
|---|---:|---:|---:|
| Brilliant Stars | $16.24 | 21.38% | 4.7 |
| 30th Celebration | $16.91 | 20.78% | 4.8 |
| Lost Origin | $19.68 | 18.69% | 5.4 |
| Crown Zenith | $25.98 | 15.38% | 6.5 |
| Evolving Skies | $43.97 | 10.64% | 9.4 |
| Hidden Fates | $47.98 | 10.01% | 10.0 |
| Base Set | $632.50 | 1.65% | 60.7 |
| Neo Genesis | $741.61 | 1.47% | 67.9 |

A vintage pack (either) about 1 in 32 opens. `pokeshell pack odds random` prints this table from the live data (a set
whose cards aren't built yet drops out and the rest renormalise). The test rolls the set 200,000 times (seeded) and
50,000 times (CSPRNG) and checks every set's share within 4.5 sigma, then that `--seed` repeats the set and the pack
and that a random open spends exactly one token.

## How a pack is modelled

```json
{ "id": "swsh7", "name": "Evolving Skies", "cardSets": ["swsh7"], "realPackSize": 10, "art": { ... },
  "slots": [
    { "id": "common", "count": 5, "pick": [ { "label": "common", "rarity": ["Common"], "base": true, "printed": 42 } ] },
    { "id": "reverse", "finish": "reverse", "pick": [ { "label": "reverse holo", "rarity": ["Common", "Uncommon", "Rare", "Rare Holo"], "base": true, "printed": 132 } ] },
    { "id": "rare", "pick": [
      { "label": "rare", "rarity": ["Rare"], "base": true, "rate": 0.5141, "printed": 19 },
      { "label": "gold", "rarity": ["Rare Secret"], "rate": 0.0091, "printed": 12 },
      ... ] } ] }
```

- A **slot** gives `count` cards (different cards within one slot, as printed packs do). Each card: one **outcome**
  (`pick`) by weight, then one card of that outcome uniformly.
- An outcome's cards: `rarity` (printed rarities), `sets` (card set ids, default the booster's `cardSets`), `ids`
  (explicit card ids), `exclude`, `supertype` (`Pok` / `Tra`: to count Pokemon vs Trainer printed cards apart).
- `rate`: the published per-pack chance of that outcome in that slot (a slot's rates add up to 1).
  `finish` / `fx` override the slot's finish and the tier's effect.
- `printed`: how many printed cards the outcome covers, filled in by `tools/booster_printed.py` from the pokemontcg.io
  set lists (it also checks every slot's rates add up to 1 and has one base).
- `base`: the slot's default outcome (the plain common / rare / reverse holo).

### Cards we don't serve

We serve only Pokemon cards with a sprite (docs/SKIPPED.md): no Trainer or Energy cards, no TAG TEAMs, no Gen 9 Pokemon
without a colorscripts sprite. Rule: **every card we serve keeps its real per-pack odds.** An outcome's weight is
`rate x served / printed`; the share of the printed cards we don't serve goes to the slot's base outcome. So
Evolving Skies' golds roll at 0.91% x 3/12 (we serve the 3 Pokemon golds of 12): each gold is exactly as rare as in a
real pack (1 in 1,319), and a pack that "would have been" a gold Trainer is a plain Rare instead. An outcome with no
served card never rolls (Crown Zenith's full-art Trainers, Hidden Fates' Shiny Vault Trainers); its whole share goes
to the base. Inside an outcome, cards are uniform over the ones we serve, so a common slot is simply a random served
common (a Trainer common is replaced by a Pokemon common).

**Energy and code cards**: modern packs' basic Energy (and the VSTAR marker, the code card) have no Pokemon, and the
Base Set / Neo packs' 2 basic Energy likewise: those slots are left out, so our packs are one card (Base Set: two)
shorter than the printed ones (`packSize` vs `realPackSize`). They're filler in real packs too, and inventing a
Pokemon card in their place would change the odds of everything else.

## The sets

Rates are per pack. "est." marks what no source publishes (see each set's notes). Full data, with every outcome's
printed and served counts: `pokeshell pack odds <set>`.

### Evolving Skies (swsh7)
Printed pack: 10 cards + basic Energy + code card: **5 common, 3 uncommon, 1 reverse holo, 1 rare** (Bulbapedia;
pre-Scarlet & Violet packs guarantee one reverse holo: Pokemon Center support). Only the rare slot can hit.

| rare slot | rate | printed / served |
|---|---:|---:|
| Rare | 51.41% (est.) | 19 / 19 |
| Rare Holo | 26.50% (est.: DigitalTQ's Rare Holo share in Brilliant Stars / Lost Origin) | 20 / 20 |
| V | 10.56% | 18 / 18 |
| VMAX | 5.60% | 15 / 15 |
| full art (V + Supporters) | 2.78% | 27 / 22 |
| alternate art V | 1.10% | 11 / 11 |
| alternate art VMAX | 0.30% | 6 / 6 |
| rainbow | 0.84% | 16 / 11 |
| gold | 0.91% | 12 / 3 |

Source: TCGplayer, 8,000+ packs, 95% intervals (hits add up to 22.1%). The Rare / Rare Holo split isn't published.

### 30th Celebration (me55)
Printed pack (English): **5 foil cards + a foil basic Energy**; every card is holofoil (Bulbapedia). Slot 3 is the
Illustration Rare / Classic Collection slot, slot 4 the Double Rare / Special Illustration Rare / Futuristic Rare
slot, slot 5 always a Pikachu rare (TCGplayer).

| slot | outcome | rate |
|---|---|---:|
| 1-2 | foil common | 100% (est.: not published) |
| 3 | Illustration Rare | 19.72% |
| 3 | Classic Collection (me55c, not served: goes to the common) | 10.15% |
| 3 | foil common | 70.13% (est.) |
| 4 | Double Rare | 21.02% |
| 4 | Special Illustration Rare | 4.88% |
| 4 | Futuristic Rare | 0.83% |
| 4 | Rare | 73.27% (est.) |
| 5 | Pikachu rare (30, each by a different artist) | 100% |

Sources: TCGplayer, 3,000+ packs; tcgtalk, 652 packs (21.9% ex, 18.4% IR, 9.8% Classic Collection, 5.5% SIR, 1.2%
Futuristic, 43.1% Pikachu only: consistent). The 3 RGB Rare Mews appeared in none of 3,000+ packs and aren't in the
set list we serve. What fills slots 1-2 and the non-hits of slots 3-4 isn't published: commons and a Rare is our
reading (it fits the 43% of packs whose only hit is the Pikachu).

### Crown Zenith (swsh12pt5) + Galarian Gallery (swsh12pt5gg)
Printed pack: 10 cards + Energy + code: **5 common, 3 uncommon, the reverse-holo slot, 1 rare** (DigitalTQ). The
Galarian Gallery and Radiant cards come in the reverse-holo slot (TCGplayer); there is only one reverse slot.

| slot | outcome | rate | printed / served |
|---|---|---:|---:|
| reverse | reverse holo | 60.25% | 113 / 89 |
| reverse | Galarian Gallery (character art) | 22.40% | 34 / 34 |
| reverse | Galarian Gallery V / VMAX / VSTAR / Trainer | 12.00% | 32 / 22 |
| reverse | Galarian Gallery gold VSTAR | 0.80% | 4 / 4 |
| reverse | Radiant | 4.55% | 3 / 3 |
| rare | Rare | 44.70% (est.) | 22 / 22 |
| rare | Rare Holo | 26.40% (est.) | 13 / 13 |
| rare | signature Trainer holo | 7.65% | 7 / 0 |
| rare | V | 12.35% | 17 / 17 |
| rare | VMAX / VSTAR | 5.30% | 13 / 13 |
| rare | full-art Trainer / textured Energy | 2.85% | 13 / 0 |
| rare | secret rare (Pikachu 160/159) | 0.75% | 1 / 1 |

Source: TCGplayer, 1,900+ packs. The main set has no gold card; its golds are the 4 Galarian Gallery VSTARs.

### Hidden Fates (sm115) + Shiny Vault (sma)
Printed pack: 10 cards + basic Energy: **5 common, 3 uncommon, the reverse-holo slot, 1 rare** (the Sun & Moon
standard, inferred). The Shiny Vault card takes the reverse-holo slot (PokeBeach), so a pack can have a GX and a
Shiny Vault card together.

| slot | outcome | rate | printed / served |
|---|---|---:|---:|
| reverse | reverse holo | 66.51% | 56 / 41 |
| reverse | Shiny Vault baby shiny | 21.28% (1 in 4.7) | 45 / 45 |
| reverse | Shiny Vault GX | 9.43% (1 in 10.6) | 35 / 35 |
| reverse | Shiny Vault full-art Trainer | 1.19% (1 in 84) | 6 / 0 |
| reverse | Shiny Vault gold | 1.59% (1 in 63) | 8 / 4 |
| rare | Rare | 53.66% (est.) | 15 / 12 |
| rare | Rare Holo | 26.40% (est.) | 6 / 3 |
| rare | GX | 14.93% (1 in 6.7) | 9 / 8 |
| rare | full art | 3.91% (1 in 25.6) | 3 / 0 |
| rare | rainbow | 1.10% (1 in 90.9) | 1 / 0 |

Source: ThePriceDex (community estimates, sample not stated). There is no large published study for Hidden Fates;
their Shiny Vault rows add up to about 1 in 3, which a 1,000-pack community count agrees with. Treat these as the
weakest numbers here.

### Base Set (base1)
Printed pack: **11 cards: 5 common, 3 uncommon, 1 rare, 2 basic Energy**; no reverse holos yet (they began with
Legendary Collection). Rare slot: **holo rare 1 in 3** (CardGuide; long-standing hobby knowledge, no measured study),
Rare 2 in 3 (16 printed rares, 10 of them Trainers: their share goes to the 6 Pokemon rares). 1st Edition and
Unlimited packs have the same structure. Our pack: 9 cards (no Energy).

### Brilliant Stars (swsh9) + Trainer Gallery (swsh9tg)
Printed pack: 10 cards + code + basic Energy or VSTAR marker: **5 common, 3 uncommon, the reverse-holo slot, 1 rare**.
Trainer Gallery cards come in the reverse slot, independent of the rare slot (TCGplayer).

| slot | outcome | rate | printed / served |
|---|---|---:|---:|
| reverse | reverse holo | 81.94% | 124 / 101 |
| reverse | Trainer Gallery (character art) | 12.50% (1 in 8) | 12 / 12 |
| reverse | Trainer Gallery V / VMAX / Trainer / gold | 5.56% (1 in 18) | 18 / 12 |
| rare | Rare | 46.80% | 26 / 26 |
| rare | Rare Holo | 26.39% | 10 / 8 |
| rare | V | 14.94% | 20 / 20 |
| rare | VMAX | 1.89% | 3 / 3 |
| rare | VSTAR | 1.89% | 4 / 4 |
| rare | Pokemon full art / alternate art | 3.19% | 15 / 15 |
| rare | full-art Trainer | 1.85% (1 in 54) | 6 / 0 |
| rare | rainbow | 1.96% (1 in 51) | 8 / 4 |
| rare | gold | 1.09% (1 in 92) | 6 / 4 |

Sources: TCGplayer's infographic, 10,000+ packs (Trainer Gallery, gold, rainbow, full-art Trainer, and the single-card
rates: Charizard V full art 1 in 450, alternate art 1 in 490, so about 1 in 470 for each of the 15 Pokemon full /
alternate arts); DigitalTQ, 1,004 packs (V, VMAX, VSTAR, Rare Holo). No source gives the Trainer Gallery golds a
rate of their own; they're in TCGplayer's "V, VMAX or Trainer" group here. (pullrates.com's "Trainer Gallery gold
1 in 309" misreads the infographic: that is Marnie's Pride alone.)

### Neo Genesis (neo1)
Printed pack: **11 cards: 7 common, 3 uncommon, 1 rare**; no reverse holos. Rare slot: holo 1 in 3 (PSA; hobby
knowledge). Neo's basic Energy aren't served, and where they fell in the pack isn't documented.

### Lost Origin (swsh11) + Trainer Gallery (swsh11tg)
Printed pack: 10
cards + code + basic Energy or VSTAR marker: **5 common, 3 uncommon, the reverse-holo slot, 1 rare**.

| slot | outcome | rate |
|---|---|---:|
| reverse | reverse holo | 82.67% |
| reverse | Trainer Gallery (character art) | 8.29% |
| reverse | Trainer Gallery V / VMAX / Trainer | 3.17% |
| reverse | Trainer Gallery gold-and-black VMAX | 0.86% |
| reverse | Radiant | 5.01% |
| rare | Rare | 51.55% |
| rare | Rare Holo | 26.46% (DigitalTQ, 718 packs) |
| rare | V | 11.63% |
| rare | VMAX / VSTAR | 4.42% |
| rare | full art V | 1.98% |
| rare | full-art Trainer | 1.42% |
| rare | alternate art V | 0.50% |
| rare | rainbow | 1.28% |
| rare | gold | 0.76% |

Source: TCGplayer, 8,000+ packs. Its table and text disagree on rainbow (1 in 78 vs 1 in 70) and gold (1 in 131 vs 1
in 114); the table's figures are used.

## Speed: the booster index and the incremental export

`pack open` used to take 1.5 s without `--export` and 3 s with it (15 s the first time on a copied state): PowerShell
5.1 parsed pack.json (310 KB, half a second) and built the set's model card by card on every open, and `--export` ran the
whole web export. Now:

- **The booster index**, `<state>\booster-index-pokemon.tsv`: every set's model resolved once (the built cards, each
  slot's pools and weights, the outcome metadata, pack.json's retired map), written by `Get-PokeshellBoosterIndex`
  (`scripts/lib/booster.ps1`) and loaded by `Pokeshell.BoosterIndex` (`Booster.cs`). An open loads it (about 10 ms),
  and rolls, resolves NEW against pulls.log and sorts the reveal in C#; the dice draws are the same as before, so a
  seeded pack is the same pack. Its stamp is the root, pack.json, boosters.json, the art folder's time (a card's art
  built or removed) and the booster code: when any changes, the next open rebuilds it (about 2 s, once). `pokeshell
  install` builds it up front.
- **`--export` is incremental** (`binder.exe --export-web --only <card ids>`, `binder/src/webexport.rs`): only the pack's
  cards are rendered; data.json and binder.html are rewritten from the art cache. The export also reads each folder once
  (existence, mtime and size of thousands of art files from one listing instead of a stat each) and caches the card
  text (`img/.meta.json`) instead of parsing 1,500 `cards/<id>.json` files each time.
- **Why the first export was cold**: `img/.cache.json` keyed every source by its absolute path. A module install's
  export reads the art from `<state>\current\dist\...`; the same state copied elsewhere (or a source checkout, or a
  new module version) names other paths, so every entry missed and all ~1,200 images were decoded again (15 s). The
  cache now keys sources by their path relative to the root, and an entry of the old format still matches when its
  absolute path ends with the same relative path and the mtime and size agree, so existing caches stay warm.

Measured on the user's state (871 pulls, 1,235 web images; a copy in %TEMP%, a source checkout, Windows PowerShell 5.1,
bare `powershell.exe` start about 200 ms):

| `pack open swsh7 --json --free` | before | after |
|---|---:|---:|
| without `--export` | 1,360-1,400 ms | 575-665 ms |
| `--export`, warm | 1,780-2,160 ms | 860-1,000 ms (`random`: 715-1,000 ms) |
| `--export`, the first open on a copied state | 14,440 ms (art cache cold) | 2,970-3,190 ms (the index is built once; the art cache holds) |

## Monte Carlo

`tests/test-boosters.ps1` rolls **20,000 packs of each of the 8 sets** (seeded) plus 20,000 Evolving Skies packs from
the CSPRNG, and checks every outcome's frequency against the probability the model rolls, within 4.5 binomial
standard deviations (it writes every row to `%TEMP%\pokeshell-booster-montecarlo.tsv`). A 20,000-pack run takes
30-130 ms per set. The worst deviation per set on the last run: Evolving Skies 1.75 sigma, 30th Celebration 0.70,
Crown Zenith 2.46, Hidden Fates 0.92, Base Set 0.81, Brilliant Stars 2.42, Neo Genesis 0.25, Lost Origin 1.99; the
CSPRNG runs 0.8-2.1.
Some of the rare-slot rows (expected, observed over 20,000 packs):

| set | slot | outcome | expected | observed |
|---|---|---|---:|---:|
| swsh7 | rare | V | 10.560% | 10.735% |
| swsh7 | rare | alternate art V | 1.100% | 1.020% |
| swsh7 | rare | alternate art VMAX | 0.300% | 0.330% |
| swsh7 | rare | gold | 0.228% | 0.230% |
| me55 | rare | special illustration rare | 4.392% | 4.365% |
| me55 | rare | futuristic rare | 0.830% | 0.785% |
| swsh12pt5 | reverse | galarian gallery | 22.400% | 22.600% |
| swsh12pt5 | reverse | radiant | 4.550% | 4.665% |
| sm115 | reverse | shiny vault | 21.280% | 21.175% |
| swsh9 | reverse | trainer gallery | 12.500% | 12.650% |
| base1 | rare | holo rare | 33.330% | 33.060% |

The test also checks the model itself: every fully served outcome rolls exactly at its published rate, a partly served
one at `rate x served / printed`, and the base gets the rest.

## Sources

- TCGplayer, Evolving Skies pull rates (8,000+ packs): https://www.tcgplayer.com/content/article/Pok%C3%A9mon-TCG-Evolving-Skies-Pull-Rates/6a743d7b-e5ee-4fd6-9d18-64a636990e8c/
- TCGplayer, Crown Zenith pull rates (1,900+ packs): https://www.tcgplayer.com/content/article/Pok%C3%A9mon-TCG-Crown-Zenith-Pull-Rates/56af3032-cb34-4da1-92fb-9cf206d10c0f/
- TCGplayer, Lost Origin pull rates (8,000+ packs): https://www.tcgplayer.com/content/article/Pok%C3%A9mon-TCG-Lost-Origin-Pull-Rates/ba20ac4d-9448-45ce-b919-d856d107c744/
- TCGplayer, 30th Celebration pull rates (3,000+ packs): https://www.tcgplayer.com/content/article/Pok%C3%A9mon-TCG-30th-Celebration-Pull-Rates/587b3657-481a-4ab8-827c-68cd3ab585b0/
- TCGplayer Brilliant Stars infographic (10,000+ packs), via @PokemonTCGDrops: https://x.com/PokemonTCGDrops/status/1497328883695185921
- TCGplayer, Astral Radiance (restates Brilliant Stars' 44% hit rate): https://www.tcgplayer.com/content/article/Pok%C3%A9mon-TCG-Astral-Radiance-Pull-Rates/10da749f-9c8b-45c0-b80a-dbd86ca5dcde/
- DigitalTQ, Brilliant Stars (1,004 packs): https://www.digitaltq.com/brilliant-stars-pull-rates-pokemon-tcg
- DigitalTQ, Lost Origin (718 packs): https://www.digitaltq.com/lost-origin-pull-rates-pokemon-tcg
- DigitalTQ, Crown Zenith (pack layout): https://www.digitaltq.com/crown-zenith-pull-rates-pokemon-tcg
- tcgtalk, 30th Celebration (652 packs): https://tcgtalk.com/guides/30th-anniversary-pull-rates
- Bulbapedia, 30th Celebration: https://bulbapedia.bulbagarden.net/wiki/30th_Celebration_(TCG)
- Bulbapedia, Booster pack (TCG): https://bulbapedia.bulbagarden.net/wiki/Booster_pack_(TCG)
- Pokemon Center support, booster contents: https://support.pokemoncenter.com/hc/en-us/articles/360028979571
- ThePriceDex, Hidden Fates: https://www.thepricedex.com/set/sm115/hidden-fates/pull-rates
- PokeBeach, Hidden Fates set list (Shiny Vault in the reverse slot): https://www.pokebeach.com/2019/08/hidden-fates-leaking-nearly-complete-set-list
- PSA, Neo Genesis 1st Edition: https://www.psacard.com/articles/articleview/9409/psa-set-registry-collecting-2000-poke-mon-neo-genesis-1st-edition
- CardGuide wiki, Base Set: https://cardguide.fandom.com/wiki/Base_Set_(Pok%C3%A9mon_TCG)
- PokeMasterCenter, Base Set guide: https://www.pokemastercenter.com/pokemon-base-set-guide/

**Not published anywhere we found**: the Rare vs Rare Holo split of the Sword & Shield rare slots (DigitalTQ's measured
26.4% is used), what fills 30th Celebration's slots 1-4 when they don't hit, a rate for the RGB Rare Mews, a
large-sample Hidden Fates study, and a measured holo rate for Base Set and Neo Genesis.
