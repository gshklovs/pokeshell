> **Historical brief**, exactly as the batch agents got it. Since then the code has moved to `artlab/sets/p30/` (the data stays in `style-lab/p30/`, see `artlab/artpaths.py`), so run the modules from there with `..\..\..\.venv\Scripts\python`. The method, including how to write the next set's brief, is `docs/ART_METHOD.md`.

# 30th Celebration full set: brief for the batch agents

The user approved the 7-card ladder in this folder: one real card per rarity. It sets the quality bar and the look, the same way the Evolving Skies ladder did (`style-lab/evs/FULLSET.md`). Now we make every remaining Pokémon card in the main set, `me55` (30th Celebration). Each agent owns one group in `plan.json` and builds exactly those cards, the same way the approved card of that rarity was built.

Repo: `C:\Users\grego\repos\pokeshell` (Windows). Python: `C:\Users\grego\repos\pokeshell\.venv\Scripts\python` (Pillow, numpy, scipy, scikit-image, rembg). Never read API keys or .env files. No image-generation APIs.

## Already in place
- **Card data and scans.** `cards/<id>.json` (card data, CARD_FORMAT, `tier` = the API rarity) and `cards/api/<id>.json` (the cached API record) exist for all 161 cards. So do the hires scans, `ref/me55_<number>.png`. Do not refetch unless a file is missing. If one is, use `fetch_set.get()`: it retries with backoff and sends the User-Agent the API needs.
- **Pipeline.** The approved pipeline is the evs one, used unchanged through the p30 modules:
  - `p30lib.py` puts evs first on sys.path. It points evlib's scan, mask and output paths at p30 and loads evs `anim.py` / `build.py` by file path.
  - `p30cards.py` has the builders and the finish helpers.
  - `p30masks.py` has the mask method and helpers.
  - `p30build.py` has `render(cid)`.
  - `p30anim.py` has `KINDS` and `build(ids)`.
  - `p30verify.py` has `check(cid)`, with a `fails` counter.
  - `p30sheet.py` has `sheet(ids, path, sizes)`.
- **Approved examples.** Read how the approved card of your rarity was made, and follow it exactly:

| Group (plan.json) | Rarity | Approved example | Builder / anim |
|---|---|---|---|
| `commons` | Common | Vulpix 9 | `vulpix()`: plain sprite, no background, no animation |
| `rare` | Rare | Mew 65 | `mew()`: ME rares are holo, so the evs Rare Holo recipe (`tiers.holo_scene`) inside the ME art window `ME_WIN`, with the stamp box `STAMP_REG` painted out; anim `holo` |
| `pikachu_rare` | Pikachu Rare | Pikachu 23 | `pikachu()`: yellow bevel border plus the fireworks-burst foil over the art and the border (`fireworks`, `fireworks_paint`); anim `fireworks` |
| `double_rare` | Double Rare | Umbreon ex 92 | `umbreon()`: evs Rare Holo V frame and scene, fine sparkle grain (`ex_grain`); anim `ex` |
| `illustration_rare` | Illustration Rare | Lapras 131 | `lapras()`: evs Rare Ultra full-art pipeline with the lighter, art-following etch (period 4, amplitude 0.065, `f + 9 * lum`); anim `etch` |
| `sir_futuristic` | Special Illustration Rare | Gengar ex 154 | `gengar()`: evs alt-art textured painting plus the pearl lustre (`PEARL`); anim `sir` |
| `sir_futuristic` | Futuristic Rare | Mewtwo ex 157 | `mewtwo()`: `chrome()` over the card's own scene with a smooth fill, plus the Futuristic tint on the sprite (`futuristic_sprite(c, futuristic_tint(cid))`); anim `chrome` |

## Rules (all decided by the user)
- **Real cards only.** Build exactly the ids in your group; never invent anything. The 7 ladder cards are done; they are listed in `plan.json` `_ladder_done`. Trainers and the 9 Gen 9 cards with no colorscripts sprite are skipped (`_skipped`).
- **Sprite.** The Pokémon is the pokemon-colorscripts large sprite (`vendor/pokemon-colorscripts/colorscripts/large/regular/<name>`, `shiny/<name>`), unchanged. Only a horizontal flip is allowed, to face the way the card does.
  - `plan.json` gives the sprite name per card. Forms were read off the scans: Cherrim Sunshine, Vivillon Poké Ball, Toxtricity 59 Low Key, Lycanroc Midnight, Minior red core, Zacian and Zamazenta Crowned, and the Alolan / Galarian / Hisuian forms.
  - **The one allowed recolour is the Futuristic Rare tint.** It is a luminance-preserving blend of at most `FR_BLEND` (0.3; the user asked for 0.35 or less, and 0.55 is the cap) toward the card's own dominant red, or failing that its darkest tone (`futuristic_tint`). The outline, near-black strokes, white and the eye stay exact.
  - Each Futuristic card needs its sprite's eye in `EYE_PIN`. Mew and Mewtwo are already there.
  - No rarity in this set is gold or rainbow.
- **Commons** never get a background: plain sprite. This holds even though the real 30th Celebration commons are foil, and it includes the B / G / R monochrome Mews, which the API labels Common. The pack builder handles commons automatically, so the commons group only verifies that data and sprite names resolve.
- **Background.**
  - The card's own scene, with the real Pokémon masked out and filled (rembg or colour rule plus hand hull, as in `p30masks.py`), at the resolution and treatment of the approved example.
  - Every card has the 30th Pikachu-logo stamp in its art. Paint it out with a box: it is a logo. It sits at the art window's lower right on regular cards (`STAMP_REG`) and moves around on full arts, so read it off `work/grid_<n>.png`; `work/grid.py <n>` makes those.
  - When the Pokémon covers most of the card (ex, Futuristic), check the fill for ghost remnants of the real Pokémon. Grow the mask by colour rule inside a hull, as Umbreon 92 needed. Use `texture=False` when the hole is half the card, as Mewtwo 157 did.
- **No text or logos** in the art.
- **Text half.** Every card gets its text half via evs `bottom.py`, through `p30build.render()`. The frame colour comes from the builder's `meta["frame"]`:

| Rarity | Frame |
|---|---|
| Common | #9aa0aa |
| Rare | #6ea5ff |
| Pikachu Rare | #f6d02c |
| Double Rare | #c9d1da |
| Illustration Rare | #7fd6e6 |
| SIR | #f0c850 |
| Futuristic Rare | #c07cff |

- **Animation.** Every foil tier gets its 16-frame animation via `p30anim.build([ids])`. The last frame must equal the static art; `build` asserts this.
- **Size.** Fit to the card, not a standard size. Keep within about 100 cols.

## How to build (don't collide with the other agents)
- **Your own module.** Write your code in `batch_<group>.py`. It imports `p30lib`, `p30cards`, `p30masks`, `p30build`, `p30anim`, `p30verify` and `p30sheet`. Register your builders at runtime (`p30cards.BUILDERS.update({...})`), then call:
  - `p30build.render(cid)`, which returns `(ims, info)`
  - `p30anim.build(ids)`
  - `p30verify.check(cid)` for each id, then assert `p30verify.fails == 0`
  - `p30sheet.sheet(ids, P.HERE / "sheets" / f"{group}.png", sizes)`, with your own `sizes` dict
- **Don't run the ladder commands.** Do not run `p30build.py`, `p30sheet.py` or `p30verify.py` without ids: they rewrite the ladder's `sizes.json`, `sheet.png` and `ladder.png`.
- **Don't edit shared files.** That means the `p30*.py` modules, `style-lab/evs/*`, `ladder.png`, `sheet.png` and `sizes.json`. If you need a shared fix, implement it locally in your module and note it in your report.
- **Masks.** Write them per id to `masks/<id>.png` from your module, using `p30masks`' helpers (`rembg`, `poly`, `rect`, `largest`, `hsv`). The rembg cache lives in `work/rembg-<model>-<id>.png`, per id.
- **Outputs are per id** (`art/`, `out/`, `anim/<id>/`, `masks/`), so they don't collide.

## Group notes
- **commons (64):** verify `cards/<id>.json` loads and each `sprite` resolves (normal and shiny) with the same shape. There is no art to build.
- **rare (15):** all use the regular ME layout: art window `ME_WIN` (52, 88, 606, 432) and stamp at `STAMP_REG`. The Pokémon are mostly large legendaries; size the card so the sprite fits (Mew 65 is 86x27).
- **pikachu_rare (29):** 29 different artists, all Pikachu, and the same yellow-border layout. The main risk is the scenes: some are busy (40), cartoon (29, 34) or photo-like (26, 27). Keep the fireworks foil and yellow border identical. Mind which way Pikachu faces.
- **double_rare (10):** ex cards where the Pokémon fills the card, so masks are the main work (see Umbreon 92). Crop as 92 did: upper card, `x0 = 20`, `S` about 15.
- **illustration_rare (15):** full-bleed paintings. The text starts at about y 520; paint out the stamp, the header name/HP and the stage icon.
- **sir_futuristic (8 SIR + 1 Futuristic, Mew ex 158):** follow Gengar 154 for SIR and Mewtwo 157 for 158. 158's tint falls back to its darkest tone, since it has little red; check it reads.

## Deliverables per agent
1. Every card in your group built: art JSON, static renders (art, and art + text; normal and shiny), and the animation for foil tiers.
2. Verification: all pass for your ids.
3. `sheets/<group>.png`: one row per card, **real card | ours | ours + text half**. The user always judges side by side against the source card.
4. A report covering:
   - cards done, and cards skipped with the reason
   - the weakest 3 cards and why
   - any shared-code fixes you needed

Iterate with the Read tool on your renders until each card holds up next to its real card, at the approved example's quality.
