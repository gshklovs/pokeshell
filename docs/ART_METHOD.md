# Art method: how pokeshell's real-card art is made

This is the playbook for building a new set of card art the way the two finished sets were built:
Evolving Skies (`swsh7`, 193 Pokémon cards, `artlab/sets/evs`) and 30th Celebration (`me55`, 149 cards,
`artlab/sets/p30`). It covers another Pokémon TCG set step by step. The last sections cover a One Piece TCG set
and a Magic: The Gathering Marvel set in a sibling repo.

Read it top to bottom once. After that, the checklist in `.claude/skills/new-card-set/SKILL.md` is enough to follow.
The file formats are in [ART_FORMAT.md](ART_FORMAT.md) (the art), [CARD_FORMAT.md](CARD_FORMAT.md) (the text half),
[PACK_FORMAT.md](PACK_FORMAT.md) (pack.json) and [SHADER_SPEC.md](SHADER_SPEC.md) (tab skins).

## Contents

1. [The art direction](#1-the-art-direction-the-users-rules): the rules the user approved
2. [Code and data](#2-code-and-data): what is tracked in `artlab/`, what stays in `style-lab/`, and the environment
3. [The pipeline at a glance](#3-the-pipeline-at-a-glance)
4. [Card data and scans](#4-card-data-and-scans)
5. [The plan](#5-the-plan-planjson)
6. [Masks](#6-masks-the-real-pokémon-white)
7. [Painting the Pokémon out](#7-painting-the-pokémon-out)
8. [Sprite, forms, facing, placement, size](#8-sprite-forms-facing-placement-size)
9. [The per-rarity effect catalogue](#9-the-per-rarity-effect-catalogue)
10. [Recolours](#10-recolours-rainbow-gold-futuristic)
11. [Alt-art paintings](#11-alt-art-paintings-the-umbreon-215-treatment)
12. [Animations](#12-animations)
13. [The text half](#13-the-text-half)
14. [Batch modules](#14-batch-modules-how-a-sets-code-is-organised)
15. [Review in the lookbook](#15-review-the-lookbook-side-by-sides)
16. [The audit](#16-the-audit)
17. [Import](#17-import)
18. [Tiers, weights and tab skins](#18-tiers-weights-and-tab-skins-packspokemonpackjson)
19. [Tests and the definition of done](#19-tests-and-the-definition-of-done)
20. [Worked example: Leafeon V, swsh7-7](#20-worked-example-leafeon-v-swsh7-7-rare-holo-v)
21. [Reproducibility check](#21-reproducibility-check)
22. [Known pitfalls](#22-known-pitfalls)
23. [Adapting to other card games](#23-adapting-to-other-card-games)
24. [Known gaps in the method](#24-known-gaps-in-the-method)

---

## 1. The art direction (the user's rules)

These rules were decided by the user. Do not change them without asking.

- **The sprite.** Each Pokémon is the pokemon-colorscripts sprite (`vendor/pokemon-colorscripts/colorscripts/large/regular/<name>`, and `shiny/<name>`), pixel-exact and unchanged.
  - The only change allowed is a horizontal flip, plus the approved recolours for high rarities (below).
  - Keep the black outline and the eyes exact, always.
  - Redrawing Pokémon into card poses was rejected twice. AI clean-up of card art was also rejected. OpenAI edits of card scans are always safety-rejected, so don't try them.
- **The scene.** The sprite sits over the real card's own scene, with the real Pokémon painted out: reference scan → mask → texture fill. No text and no logos go in the art: no name, HP, V / VMAX / ex logo, stage icon, strike badge, 30th stamp or rarity star.
- **Only real printed cards are served.** Never invent a card, a tier for a Pokémon, or a variation. Every card is keyed by its pokemontcg.io id.
- **Every real printed rarity gets its own tier and a distinct effect.**
  - The tier *is* the printed rarity: the API's `rarity` string.
  - Similar rarities are variations of one effect family (see `artlab/rarities/CATALOG.md`: 60 rarities in 14 families).
  - Effects escalate with rarity: plain → matte scene → holo foil → framed V-family foil → full-art etch → painting → rainbow / gold / chrome.
- **Commons** are the plain sprite with no background, no foil and no animation. This holds even when the real print is foil, as with the 30th Celebration commons and the B / G / R monochrome Mews.
- **Recolours**, only at these rarities:
  - **Rainbow Rare:** a pastel rainbow blend of **0.55** (cap **0.7**), luminance-preserving, so the Pokémon's own colours read through. It is animated: the rainbow flows over the body.
  - **Gold / Secret:** a gold palette remap.
  - **Futuristic Rare:** a low-opacity, animated red-black tint of **≤ 0.35**. It is **0.3** in use. Mew ex 158 was suggested at 0.45 (still open, see section 24).
- **Alt-art paintings** get the Umbreon VMAX 215 treatment: the vivid painting, its brushwork embossed, and a swinging light. They do *not* get the full-art fingerprint etch. The tier stays the printed rarity.
- **Size:** each card is sized to its art, with no standard card size (the user decided against one). The hard cap is `MAX_W, MAX_H = 140, 110` grid px in `tools/build_art.py`, which is 140 columns × 55 lines.
- **Facing:** match the real card's facing, flipping the sprite when needed.
- **The text half** is generated for every card from the API, per CARD_FORMAT: HP, abilities, attacks, weakness, resistance, retreat, set, number, rarity and artist. It is hidden in tabs and shown with `v` in the binder.
- **Animations:** 16 frames at 12 fps, looping in the tab until a key is pressed (30 s cap). The last frame is exactly the static art. Each foil tier also leads with its own tab-skin shader.
- **Tests:** real cards are keyed by pokemontcg id. A card counts as built when `dist/pokemon/<character>-<id>.ans` exists.
- **Review workflow:**
  1. Build one card per rarity first (the "ladder") and show it in the lookbook for sign-off, **always as real card | ours | ours + text half, side by side**.
  2. Then build the whole set with agents, one agent per rarity group.
  3. Then run an audit agent over every card: right treatment, facing, and Gigantamax / regional forms.
  4. Import with `build_realcards.py import <batch> --only <ids>`, and only after approval.
  5. Every new result goes into the lookbook. Decided questions are removed from it and listed under "Decided".

## 2. Code and data

### Code: tracked, in `artlab/`

```
artlab/
  artpaths.py            where the data lives: DATA (default <repo>/style-lab, $ARTLAB_DATA), VENDOR ($POKESHELL_VENDOR)
  requirements.txt       the pinned Python packages (the output bytes depend on them)
  lib/                   the shared engine
    s3lib.py             Card (the composite), Sprite, keyed() palette keys, pushpull fill, sample, tone, kmeans_q /
                         median_q, focus_halo, radial_glow, vignette, rim, sparkle, gold_ramp / gold_remap, term_png
    sprites.py           parses a colorscripts sprite into an RGB grid
    tiers.py             holo_scene (Rare Holo), gold_foil / facet_height / emboss (gold), RAMP gold ramps, suite3's recipes
    crowns.py            overlays used by tiers.py
    s3anim.py            the 16-frame exporter (.anim bundle, gifs, contact sheet); anim_holo, anim_gold
    anim_lib.py          ANSI + preview helpers for the exporter
    bottom.py            the text half (render_text)
    maskkit.py           mask helpers: rembg_cached, poly, rect, largest, stroke, hsv_planes, overlay
    setlib.py            the per-set lib pattern: use_set() points evlib at another set's data
    play.ps1             plays an exported .anim in a terminal
  sets/evs/              Evolving Skies: the REFERENCE set (its modules are the approved recipes every set reuses)
    evlib.py             set paths + tex_fill / clean / anchor / region + the extended Sprite
    evcards.py           ladder batch 1 + recipe helpers: silver_frame, fingerprint, rainbow_sprite, colour_blend ...
    evcards2.py          ladder batch 2: window_rgb, matte, reverse_ring, vmax_texture, froslass (gold)
    masks.py             the ladder's mask recipes + rembg(cid, model) through maskkit
    anim.py              the effect loops: sunpillar, etch, paint, rainbow, reverse (+ holo, gold)
    build.py             art_json / render: ART_FORMAT JSON + terminal renders (art, art + text half)
    verify.py, sheet.py  sprite-exactness / card-data / animation checks; the ladder sheet
    batch_<group>.py     one module per plan.json group, plus batch_altart.py (alt-art redo) and batch_fixes.py (audit fixes)
    fetch_cards.py, fetch_rest.py   how evs's data was fetched (superseded by artlab/tools/fetch_set.py)
    plan.json, set.json, FULLSET.md (the brief the batch agents got), audit/ (audit scripts + REPORT.md)
  sets/p30/              30th Celebration, built ON evs through setlib (p30lib, p30cards, p30masks, p30build, p30anim,
                         p30verify, p30sheet, batch_*.py, make_plan.py, fetch_*.py, plan.json, set.json, FULLSET.md, audit/)
  sets/suite3/           build.py / verify.py of the first 12 real cards (their recipes are lib/tiers.py)
  rarities/              effects.py (the 60-rarity family engine), rarities.json, CATALOG.md, catalog.py, scenes.py, demo.py
  tools/                 fetch_set.py, make_plan.py, grid.py, lb_set.py, sprite_sheet.py, pixelize.py
  lookbook/template.html the lookbook page (grid sections, choices saved to the Artifact db)
```

### Data: git-ignored, in the data root

The data is copyrighted or generated, so it is never committed. The data root is `style-lab/` by default: it is
listed in `.git/info/exclude`, and it is also where `tools/build_realcards.py` imports batches from (`--lab`).
Each set has its own folder, `<DATA>/<set>/`:

| folder | what | made by |
|---|---|---|
| `ref/<prefix>_<number>.png` | the real card scans (hires) | `fetch_set.py` |
| `setlist.json` | every card of the set, full API records | `fetch_set.py` |
| `cards/<id>.json`, `cards/api/<id>.json` | CARD_FORMAT (with the card text), and the raw API record | `fetch_set.py` |
| `masks/<id>.png` (+ `masks/altart/`) | the real Pokémon's mask, card px, white = Pokémon | the batch's `masks` step |
| `work/` | `rembg-<model>-<id>.png` caches, `grid_<n>.png`, size logs, audit scratch | various |
| `art/<id>.json` | the ART_FORMAT art (what the importer reads) | the batch's `build` step |
| `out/<id>-art[-shiny].ans/.png`, `out/<id>-card[-shiny].ans/.png` | terminal renders: the art alone, and the art over its text half | `build` |
| `anim/<id>[_shiny]/` | the 16-frame loop: `<id>.anim` (what ships), `.json`, gifs, contact sheet | the batch's `anim` step |
| `sheets/<group>.png` | review sheets: real card, ours, and ours + text half | `sheet` |

The masks are derived from the scans, so they stay in the data root too. Every mask can be regenerated from its
recipe (section 6). The `rembg` caches in `work/` make that regeneration exact.

The old `style-lab/<set>/*.py` files are the pre-`artlab` copies of this code. `artlab/` is the source now. Keep
running the code from `artlab/`, and once this branch is merged, the `.py` files in style-lab can be deleted
(style-lab keeps only the data).

### Environment

- Windows, repo at `C:\Users\grego\repos\pokeshell`. Python 3.12 venv at `.venv`. Never install packages globally.
  ```powershell
  py -3.12 -m venv .venv
  .venv\Scripts\python -m pip install -r artlab\requirements.txt
  ```
- rembg runs local ONNX models (no API, no key). On first use it downloads `isnet-general-use`, `isnet-anime` and `u2net` to `~\.rembg\models\`.
- The sprites come from `vendor/pokemon-colorscripts` (git-excluded). In a worktree, point at the main checkout's copies: `$env:POKESHELL_VENDOR = 'C:\Users\grego\repos\pokeshell\vendor'`, and `$env:ARTLAB_DATA = 'C:\Users\grego\repos\pokeshell\style-lab'` (or an isolated copy, section 21).
- No image-generation APIs, and never read API keys or `.env` files.
- Run the set modules from their folder (they import their siblings), for example `cd artlab\sets\evs; ..\..\..\.venv\Scripts\python batch_v.py build swsh7-7`. The tools in `artlab\tools` run from anywhere.

## 3. The pipeline at a glance

```
fetch_set.py      setlist.json, cards/<id>.json, ref/<prefix>_<n>.png          (section 4)
make_plan.py      plan.json: groups by rarity, sprite per card, _skipped             (5)
ladder            ONE card per printed rarity, each with its effect  ->  lookbook sign-off   (9-13, 15)
FULLSET.md        the brief for the batch agents: approved example per rarity, rules, file ownership   (14)
batch agents      one batch_<group>.py per group: masks -> build -> anim -> verify -> sheet   (6-14)
lookbook          one side-by-side section per group; user approves or names fixes    (15)
audit agent       every card vs its scan: treatment, facing, forms, ghosts, data  -> audit/REPORT.md, batch_fixes.py   (16)
import            build_realcards.py import <batch> --only <approved ids>   -> dist/pokemon, pack.json   (17)
tiers + skins     pack.json tier per rarity, weight, its own shader first  (18)
tests             tests\test-cards.ps1 (PowerShell)  (19)
```

## 4. Card data and scans

**Choosing a set.** Use pokemontcg.io v2 set ids. For example, `swsh7` is Evolving Skies and `me55` is 30th Celebration. The Classic Collection subset `me55c` is a separate set id, deferred by the user. List sets with `https://api.pokemontcg.io/v2/sets`.

**Fetching.** Create `artlab/sets/<folder>/set.json` first, with `name`, `set_id`, `prefix` (the scan file prefix, usually the set id) and `printed_total`. Section 5 lists the other keys. Then run:

```powershell
.venv\Scripts\python artlab\tools\fetch_set.py <folder>                  # the whole set
.venv\Scripts\python artlab\tools\fetch_set.py <folder> --ids me55-9     # some cards
```

The script works like this:

- **Set list.** One paged query (`/v2/cards?q=set.id:<id>&pageSize=250`) goes to `setlist.json` as full records, sorted by number.
- **Cards.** Each card is written twice: `cards/api/<id>.json` holds the raw record, and `cards/<id>.json` holds CARD_FORMAT. Every field is copied verbatim; `tier` is the API `rarity`.
- **Scans.** `images.large` (the `_hires.png`) goes to `ref/<prefix>_<number>.png`.
- **Retries.** The API **refuses requests without a User-Agent** and is **flaky** (resets, 5xx, timeouts). Every request sends `User-Agent: pokeshell-fetch-cards/1` and retries with backoff. Files already on disk are kept, and scans are fetched in up to 6 passes, so just re-run it if it stops.
- **Old set lists.** A reduced set list (evs's) is upgraded to full records automatically.

**Scan geometry, measured in card px:**

| era | scan size | art window | furniture to paint out |
|---|---|---|---|
| Sword & Shield regular card | 734 × 1024 | `SWSH_WIN = (66, 106, 680, 476)`; holo crop `(64, 96, 684, 492)` | `STAGE_BOX (0, 58, 312, 136)` or `BASIC_BOX (0, 58, 250, 110)`, strike badge `(462, 96, 712, 168)`, frame edges |
| SWSH V / VMAX | 734 × 1024 | the V window `37..697 × 92..669` (Sylveon V 74) | name bar `(0, 0, 734, 96)`, V corner swoosh, VMAX logo `(0, 30, 112, 150)`, strike logo, everything below `text_y` |
| SWSH full art / alt art / rainbow | 734 × 1024 | the whole card above `text_y` (per card, where the text starts) | top bar, V logo arm polygon `V_ARM`, the attack text |
| Mega Evolution (30th Celebration) regular | 652 × 914 | `ME_WIN = (52, 88, 606, 432)` | the 30th Pikachu stamp `STAMP_REG (484, 334, 652, 468)` |
| ME ex / IR / SIR / Futuristic | 652 × 914 (SIR 634 × 888) | upper card to about y 520 | the header, stage icon, and the stamp (it moves on full arts: read it off the grid) |

**Reverse holo** is not an API rarity. It is a parallel print of a Common, Uncommon or Rare with the same id. The
evs ladder built Pikachu 49 as one (`TIER_OVERRIDE` in `sets/evs/fetch_cards.py`, plus `evcards2.reverse_ring`).
The live pack imports it as its printed rarity (Common), because the `reverse-holo` tier has no `rarity`. That is
still an open question (section 24).

## 5. The plan (`plan.json`)

`plan.json` assigns every buildable card to the build agent (group) that owns it. Write `set.json` first:

```json
{ "name": "30th Celebration", "set_id": "me55", "prefix": "me55", "printed_total": "128",
  "lookbook": {"section_prefix": "p30set_", "anchor": "p30", "place": "after"},
  "groups": {"Common": "commons", "Rare": "rare", "Pikachu Rare": "pikachu_rare", "Double Rare": "double_rare", "...": "..."},
  "split": {"ultra": ["ultra_a", "ultra_b"]},
  "labels": {"commons": "Common", "...": "..."},
  "ladder": ["me55-9", "me55-65", "..."],
  "forms": {"me55-85": "lycanroc-midnight", "me55-106": "zacian-crowned", "...": "..."},
  "notes": {"me55-B": "monochrome Mew the API labels Common: commons rule, plain sprite"} }
```

Then run:

```powershell
.venv\Scripts\python artlab\tools\make_plan.py <folder>            # writes artlab/sets/<folder>/plan.json
.venv\Scripts\python artlab\tools\make_plan.py <folder> --check    # compare with the existing plan.json
```

- **Groups.** There is one group per rarity. Rarities that share a recipe family may share a group: evs's `rainbow_secret` holds both Rare Rainbow and Rare Secret. Split a group of more than about 20 cards in two (`split`).
- **Skipped cards.** Trainers, Energy and cards with no colorscripts sprite (every Gen 9 Pokémon: Fuecoco, Miraidon, Koraidon, Gimmighoul, Gholdengo, Maushold ...) go to `_skipped` with the reason. The ladder ids go to `_ladder_done`.
- **Sprite name**, in this order (`make_plan.sprite`):
  1. `forms[id]`
  2. `<name>-gmax` for a Gigantamax card (its attack is named "G-Max …") when the vendor has that sprite
  3. a regional prefix: Alolan → `-alola`, Galarian → `-galar`, Hisuian → `-hisui`, Paldean → `-paldea`
  4. special names: `nidoran-f`, `mr-mime`, `farfetchd` …
  5. otherwise the lower-cased name with the badge (V, VMAX, VSTAR, ex, GX …) removed and accents folded (Flabébé → `flabebe`)
- **Forms must be read off the scans.** The API name does not say Dusk / Midday / Midnight Lycanroc, Crowned Zacian, Sunshine Cherrim, Poké Ball Vivillon, Low Key Toxtricity or Minior's core colour. Evolving Skies' Lycanrocs are all `lycanroc-dusk`. Vendor forms are the folder names in `vendor/pokemon-colorscripts/colorscripts/large/regular/`.
- **Checks.** `--check` reproduces 30th Celebration's plan exactly (142 of 142 cards). On evs it also fills in the sprites the first plan got wrong, which the batches had fixed by hand: the Galarian birds, Lycanroc and the five Gigantamax cards.

Last, write `artlab/sets/<folder>/FULLSET.md`: the brief each batch agent gets. Copy `sets/p30/FULLSET.md` and change:

- the table of approved examples: group, rarity, the example card, and its builder / anim kind
- the frame colour per rarity
- the per-group notes (geometry, known risks)

## 6. Masks (the real Pokémon, white)

A mask is a boolean image in card pixels (the scan's size), saved as `masks/<id>.png`. Recipes live in code:

- the ladder: `sets/evs/masks.py`, `sets/p30/p30masks.py`
- the full set: each batch's `CFG` / `SPEC` / `MASKS` table plus its `make_mask()`

Run the `masks` step of the batch (for example `batch_v.py masks <ids>`). It writes the masks plus a review sheet in
`work/`: the Pokémon in colour and the rest darkened green. **Look at that sheet** before building.

**Tools, from cheapest to most manual:**

1. **rembg.** Use `M.rembg(cid, model)`, with `maskkit.MODELS = ("isnet-general-use", "isnet-anime", "u2net")`. Results are cached as `work/rembg-<model>-<id>.png`. Try all three side by side (the 30th Celebration agents made a 3-model contact sheet per card with a one-off `work/rembg_all.py`), and keep the one that caught the Pokémon best.
   - `isnet-general-use` is the default.
   - `isnet-anime` suits flat anime-style Pokémon.
   - `u2net` suits big full arts, but it tends to take props with the Pokémon (Umbreon 215's tower had to be cut back out).
2. **Windowed.** Intersect the rembg mask with the art window's `rect`. This is `masks.windowed(cid, model, win, cut, keep, close)`.
3. **Hand geometry, in card px**, read off a coordinate grid:
   ```powershell
   .venv\Scripts\python artlab\tools\grid.py <folder> 7                          # whole card, lines every 50 px
   .venv\Scripts\python artlab\tools\grid.py <folder> 7 --crop 150 150 600 650 --step 25   # zoomed
   ```
   Open `work/grid_<n>.png` with the Read tool, then:
   - `poly(sh, pts)` as a hull, intersected (`&`) to keep only the Pokémon
   - `cut` rects or `cutpoly`, subtracted to remove scenery or logos the model grabbed
   - `add` polygons, OR-ed in for parts the model missed (tails, paws)
   - `poly_only` / `model=None`: the mask is just the hand polygon. Use this when every segmenter takes the whole window. Leafeon V 7, Dracozolt V 58 and Jumpluff 4 are built this way.
4. **Colour rule** inside a hand hull, when rembg takes the scene. Use hue, saturation and value thresholds of the Pokémon's own colours (`maskkit.hsv_planes`). Examples: Salamence 109 (cyan body, crimson wings, orange flame), Glaceon V 174 (cyan / white on a magenta field), Mew 65 (soft pink), Umbreon ex 92 (near-black fur, yellow rings, red eye).
5. **Clean-up.**
   - `largest(m, keep)` keeps the `keep` biggest blobs.
   - `ndimage.binary_closing(iterations=n)` closes gaps, and `binary_opening` removes specks.
   - `binary_fill_holes` fills the inside.

**Rules of thumb:**

- Mask generously: section 7's `grow` dilates it again.
- When the Pokémon covers most of the card (ex, Futuristic), check the fill for **ghosts**: bits of the real Pokémon left in the scene read as blobs next to the sprite. Grow the mask by a colour rule inside the hull, as Umbreon 92 needed.
- Never edit another agent's or batch's mask. A redo writes its own folder (`masks/altart/<id>.png`, `batch_altart.MASK_FIX`), and the shared file is left alone.

## 7. Painting the Pokémon out

`evlib.clean(cid, grow, boxes, texture, sigma, tex_src, detail, extra)` returns the scan with the mask (dilated by
`grow` px, 4 to 6 usually, 14 for a smooth rainbow ground) and every `boxes` rect painted out. There are two fills:

- **`texture=True`** (the default) uses `tex_fill`: a push-pull membrane carries the low frequencies, and the scene's own high-pass detail is reflected across the nearest hole edge. Where the mirror lands in the hole as well, the detail comes from `tex_src`, a known textured rectangle `(x0, y0, x1, y1)` that is mirror-tiled. Pick `tex_src` on the scan: a patch of the same material (foliage, sky, brushwork) away from text. It keeps big holes from turning into a blurry blob.
- **`texture=False`** uses `s3lib.pushpull`, a smooth membrane. Use it when the ground is a smooth gradient (the rainbow rares), or when the hole is half the card and mirrored texture would echo the Pokémon (Mewtwo ex 157, Scraggy IR 140).

**`boxes`** are everything that must not appear:

- the frame edges `EDGES`
- the name / HP bar
- the stage icon, the V / VMAX logo and the strike badge
- the 30th stamp
- everything below the text start `(0, text_y, W, H)`

For the regular-window layouts (common, uncommon, rare, holo, ME rare), `window_rgb()` (evs `evcards2`, p30
`p30cards`) also replaces everything outside the art window with a membrane of the window. The crop can run past
the window without the card frame bleeding in.

## 8. Sprite, forms, facing, placement, size

- **Sprite.** `evlib.Sprite(name, flip)` holds the vendor sprite's rows at sprite scale. Each sprite px is a 2 × 2 block of grid px, which is 2 columns × 1 line.
  - It carries both palettes, normal and shiny, keyed by (normal, shiny) colour pairs. Black is always key `k`.
  - Busy sprites (the Eeveelutions have more than 24 colours) use the extended key alphabet `SPRITE_KEYS_EXT`.
  - Shiny comes free: the same rows with the shiny palette, `out/<id>-*-shiny.*` and `dist/pokemon/<character>-<id>-shiny.ans`.
- **Facing.** Match the real card:
  - Read which way the Pokémon's head or body points on the scan, and flip the sprite if the vendor sprite faces the other way.
  - Ambiguous (near-frontal, three-quarter) poses are flagged in the audit rather than guessed.
  - Keep one choice for one pose across a set's reprints. Umbreon VMAX 95 / 214 follow the approved 215, unflipped.
  - **Commons are never flipped** by the importer: its plain sprite has no flip (section 24).
- **Crop and scale.** A card's art is the scan region `(x0, y0)` to `(x0 + W·S, y0 + H·S)`, where `W × H` is in sprite px and `S` is card px per sprite px. The scene is sampled at grid scale (`L.sample(rgb, x0, y0, S/2, 2W, 2H, ...)`): BOX resampling for matte and holo scenes, LANCZOS for paintings and full arts. Each batch derives `(x0, y0, S, W, H)` from its approved example:

  | batch | how the crop is derived |
  |---|---|
  | holo | Salamence's window `(64, 96, 684, 492)`, H = sprite height + 2 (min 30), S = 396 / H, narrowed to ≥ 1.3:1 around the Pokémon when the sprite is tall |
  | V | the fixed window, S following the sprite with Sylveon's proportions |
  | alt art | y 100 down to the text, full card width, S ≤ 17, H = max(32, sprite h + 3), W = max(42, sprite w + 6, 714 / S) |
  | rainbow / alt / gold | the geometry in `batch_rainbow_secret.GEO` |
  | p30 ex | the upper card, x0 = 20, S about 15 |

- **Placement.** `E.anchor(cid, x0, y0, S, spr, dx, dy)` puts the sprite's bottom centre on the real Pokémon's bottom centre (the mask's bbox). You can nudge it with `dx` / `dy`, or give an explicit `off=(A, B)` in sprite px. `evcards.place(..., margin=n)` keeps it inside the art.
- **Size.**
  - Fit the card to the art. There is no standard size.
  - Keep within `build_art.MAX_W × MAX_H = 140 × 110` grid px, and in practice about 100 columns.
  - The biggest cards are Rayquaza V and Duraludon V, at about 136 × 106.
  - A card over the cap is refused by the importer. Alolan Exeggutor 129 was fixed by a crop two sprite rows shorter.
- **Region crops** (`evlib.region`) are only used for the review sheets (the real card's matching region).

## 9. The per-rarity effect catalogue

Each tier's builder returns an `s3lib.Card`:

- `c.bg` / `c.bgq`: the float scene, and its quantised uint8 version
- `c.cells`: the keyed layers (the sprite, deco sparkles, frame cells)
- `c.meta`: `card`, `rarity`, `finish`, `label`, `variant`, `anim` (the loop kind), `frame` (the text-half colour), `stars`, and what the loop needs

Every recipe finishes with a colour budget (`L.finish(c, a, n, method)`, or k-means / median cut) so the palette
stays within ART_FORMAT's keys.

### Evolving Skies (Sword & Shield era)

| printed rarity (tier id) | approved example | builder | scene and effect (key parameters) | anim kind | text-half frame | tab skin (first) |
|---|---|---|---|---|---|---|
| Common (`common`) | Eevee 125 | importer `sprite_rows` (ladder `evcards.eevee`) | the plain sprite, no background | none | `#9aa0aa` | none (plain tab) |
| Uncommon (`uncommon`) | Shelgon 108 | `evcards2.shelgon` → `matte(scale=2)` | sprite-scale scene (one 2×2 block per 3×3 samples' mode), k-means **12** colours, sat 0.84, bright 0.88, orphan clean-up, light rim where dark scenery touches the outline; `window_rgb(texture=False)` | none | `#8fc4a8` | none |
| Rare (`rare`) | Altaria 106 | `evcards2.altaria` → `matte(scale=1)` | grid-scale scene (2× finer), k-means **16**, sat 0.95, bright 0.95, texture fill | none | `#6ea5ff` | none |
| Reverse Holo (not a tier in use) | Pikachu 49 | `evcards2.pikachu` + `reverse_ring` | the Common's plain art with a 3-px pastel rainbow foil ring outside it (grain) | `reverse` | `#b9d7eb` | `reverse` |
| Rare Holo (`rare-holo`) | Salamence 109 | `tiers.holo_scene(ncol=12, foil=0.22, bright=1.0, sparkles=4)` in `window_rgb` | grid scene, 12 colours, static diagonal rainbow foil bands blended **0.22** at the scene's luminance, starlight specks, 1-px rim, 4 sparkles | `holo`: a wide rainbow band sweeps the art box, starlight glitters | `#56d0e0` | `classic-holo` |
| Rare Holo V (`rare-holo-v`) | Sylveon V 74 | `evcards.sylveon` | texture fill; sat 1.4; focus halo r3; k-means 24; V "sunpillar" stripes `rainbow_rgb((0.9x+0.35y)/9, s=0.7)` blended **0.10 + 0.10·lum**; median cut 72; rim 0.45; `silver_frame(width=2, SILVER)` (brushed gradient, bevel, etch every 5 px, inner hairline) | `sunpillar`: 45° rainbow beam + fainter counter-beam over window and frame | `#c9d1da` | `v-beam` |
| Rare Holo VMAX (`rare-holo-vmax`) | Vaporeon VMAX 30 | `evcards2.vaporeon` | as V but k-means 40, `vmax_texture` (grooves along 7 iso-luminance contours), stripes 0.14 + 0.10·lum, median 110, `silver_frame(width=3, GUNMETAL, groove=True)` | `sunpillar` (the grooves catch the beam) | `#8f9cff` | `vmax-lattice` |
| Rare Ultra, full art (`rare-ultra`) | Glaceon V 174 | `evcards.glaceon` | LANCZOS full-res painting; sat 1.12; focus halo r5; `radial_glow` 0.36 with **12 rays**; tinted vignette 0.5; **fingerprint etch** `fingerprint(period=2.6)`: raised lines +0.11, between −0.025; median 170; rim 0.34 | `etch`: the lines light up in a rainbow wave along the contours | `#e178e6` | `fingerprint` |
| Rare Ultra, alt art | Umbreon VMAX 215's recipe | `batch_altart.build_alt` | section 11 | `paint` | per card (`SPEC[...]["frame"]`) | `fingerprint` (the tier's) |
| Rare Rainbow, true rainbow (`rare-rainbow`) | Leafeon VMAX 204 | `evcards.leafeon` / `batch_rainbow_secret.build_rainbow` | smooth fill (grow 14); the **sprite re-tinted** (section 10); ground `colour_blend(a·0.9+0.12, rainbow(−0.04 + 0.5x/W + 0.42y/H, s=0.45), 0.5)`; `rainbow_etch` diagonal lines every 3rd px (−0.07 / +0.025); 3 % glitter; median 150; white rim 0.5 | `rainbow`: the hue flows along the diagonal over ground AND sprite, lines flash, glitter sparks | `rainbow` (hue around the box) | `rainbow-flow` |
| Rare Rainbow, alt-art secret | Umbreon VMAX 215 | `evcards.umbreon` / `batch_rainbow_secret.build_alt` | section 11 | `paint` | `#f0c850` | `rainbow-flow` |
| Rare Secret, gold (`rare-secret`) | Froslass 226 | `evcards2.froslass` | the **gold remap** (section 10); the scene's luminance engraved into faceted gold (`tiers.facet_height(n=70)`, `gold_foil(... glow=0.3, glints=26)`), `GOLD_SPARK` sparkles | `gold`: 45° metallic sheen, glitter, star flares | `#f0c850` | `gold-facet` |

"Rare Rainbow" in the API covers both true rainbows and painted alt-art secrets. **Decide per card from the scan**:
a pastel rainbow wash means the rainbow treatment, and a full painted scene means the alt-art treatment. In
Evolving Skies the alt arts are 205, 209, 212, 218 and 220. Among the Rare Ultras, 167, 175, 180, 182, 184, 186, 189,
192, 194, 196 and 198 are paintings. All the others are plain full arts.

### 30th Celebration (Mega Evolution era): the evs recipes, plus the new rarities

| printed rarity (tier id) | approved example | builder (`sets/p30/p30cards.py`) | scene and effect | anim kind | frame | tab skin |
|---|---|---|---|---|---|---|
| Common | Vulpix 9 | importer (`vulpix` for the ladder) | plain sprite, even though the print is foil | none | `#9aa0aa` | none |
| Rare (`rare`) | Mew 65 | `mew`: `tiers.holo_scene` in `ME_WIN`, `STAMP_REG` painted out | ME rares are always holo, so this is evs Rare Holo | `holo` | `#6ea5ff` | none: the `rare` tier is non-foil (section 24) |
| Pikachu Rare (`pikachu-rare`) | Pikachu 23 | `pikachu` | k-means 14, rainbow sheen 0.12, a **yellow bevel border** (`silver_frame(width=2, YELLOW)`), rim 0.4, median 90, **fireworks bursts** (`fireworks()` staggered 9×7 lattice, `BURST_LIFE`, `fireworks_paint` over art AND border, never on the sprite) | `fireworks`: the bursts go off in turn, a soft light bar sweeps | `#f6d02c` | `fireworks` |
| Double Rare, ex (`double-rare`) | Umbreon ex 92 | `umbreon` | the V frame and scene: k-means 24, diagonal rainbow 0.16, median 72, `silver_frame`, **sparkle grain** `ex_grain(dens=0.07)` (`GRAIN_LIFE`) instead of stripes | `ex`: the sunpillar beam pair + grain flicker | `#c9d1da` | `ex-grain` |
| Illustration Rare (`illustration-rare`) | Lapras 131 | `lapras` | the Rare Ultra full-art pipeline, lighter: glow 0.22 without rays, vignette 0.3, a **wider, art-following etch** `fingerprint(period=4) + 9·lum`, lift 0.065, median 170, rim 0.3 | `etch` | `#7fd6e6` | `ir-glow` |
| Special Illustration Rare (`special-illustration-rare`) | Gengar ex 154 | `gengar` | the alt-art textured painting (section 11) + a **pearl lustre** `PEARL = (0.83, 0.5)` (pink → cyan, s 0.3, peak 0.36 at 26 % of the diagonal) | `sir`: the paint light swing + a pearl sweep | `#f0c850` | `pearl` |
| Futuristic Rare (`futuristic-rare`) | Mewtwo ex 157 | `mewtwo` | smooth fill (`texture=False`); **liquid chrome** `chrome()`: luminance → `PLATINUM` ramp, the scene colour laid back at 0.72, cyan / magenta reflection bands 0.22; a hard specular line; median 180; rim 0.45; plus the **Futuristic tint** on the sprite (section 10) | `chrome`: the reflections roll, the tint flows with them, the specular line crosses | `#c07cff` | `liquid-chrome` |

The other printed rarities, 60 in all, each have a family and recipe in `artlab/rarities/rarities.json` and
`CATALOG.md`. Examples: Hyper Rare, Shiny Rare, Radiant, Amazing, ACE SPEC, the old-era holos. `effects.py` is a
prototype engine for them (one function per family, `apply(rarity_id, scene, sprite, off)`). It was never used to
build a shipped card. When a new set has a rarity the two sets above don't, build its ladder card from the closest
family recipe in this table, check CATALOG.md for what the real finish does, and get it signed off like any
other ladder card.

## 10. Recolours (rainbow, gold, futuristic)

Every recolour keeps the sprite's shape and its shading structure. Black `k`, near-black strokes (luminance < 62),
pure white (the eye shine) and the eye itself are **pinned**: they are never recoloured. `verify` checks this for
every card.

- **Rainbow** (`evcards.rainbow_sprite`):
  - Each sprite colour keeps its **luminance** and moves toward a pastel rainbow hue picked by where the pixel sits on the body.
  - The hue comes from `RAINBOW_STOPS`: warm ears, a green / teal face, a blue / violet body, pink-red legs. A small left-right drift is added, and the hue is quantised to 48 steps.
  - The blend is `RAINBOW_BLEND = 0.55` (user cap 0.7), a luminance-preserving "colour" blend (`colour_blend`).
  - The eye box is pinned per sprite in `EYE_BOX`.
  - The new keys come from Hangul (`RAINBOW_KEYS`). The animation re-tints the sprite every frame with the ground's flowing hue shift.
- **Gold** (`s3lib.gold_remap(spr, gold_ramp(tiers.RAMP, 24), gold_ramp(tiers.RAMP_AMBER, 24))`):
  - This is a pure palette remap: every vendor colour maps to one gold colour.
  - The level is a blend of luminance and luminance rank, so similar shades stay apart.
  - Black stays black, white goes to the top of the ramp, and the dark greys go to the bottom.
  - The shiny palette uses the amber ramp.
- **Futuristic** (`p30cards.futuristic_sprite`, `futuristic_tint`, `fr_amt`):
  - The tint colour is the card's dominant red: the median of the saturated mid-dark reds, when they cover ≥ 1.5 % of the art. Otherwise it is the mean of the art's darkest 10 %. Either way it is pushed to value 0.25.
  - Each sprite colour gets a luminance-preserving blend toward that colour of at most `FR_BLEND = 0.3` (user: ≤ 0.35; 0.55 is the hard cap).
  - The blend strength follows the chrome reflection wave plus a slow pulse, in `FR_STEPS = 8` levels.
  - Each Futuristic sprite needs its eye in `EYE_PIN`. Mew and Mewtwo are there.
  - The static art is the phase-0 state.

## 11. Alt-art paintings (the Umbreon 215 treatment)

Painted alt-art cards keep their painting. They get a vivid painting, embossed brushwork and a swinging light. They
do not get the full-art fingerprint etch. The recipe (`evcards.umbreon`, `batch_altart.build_alt`,
`batch_rainbow_secret.build_alt`, and `p30cards.gengar` for the SIR base):

1. Texture fill with a per-card `tex_src`, and every box painted out down to `text_y`.
2. The crop spans the card width from y 100 down to the text. The sprite is placed at its true size, so the canvas grows with it.
3. LANCZOS sampling at full grid resolution, `tone(sat=1.15, bright=1.02)` (per card: Dragonite 1.35 with `clarity` 0.6 against the mist; Noivern 1.3 / 1.1), and `focus_halo(r=4, dark=0.8)`.
4. **Emboss:** `h = gaussian(lum, 0.6)`, `relief = clip(-(gx·(−1) + gy·(−1.3))·2.4, ±0.3)`, `a += relief·(0.35 + 0.65·a)`. This is the painting's own brushwork, lit from the top-left.
5. A tinted vignette of 0.4, median cut to 200 colours, and a rim of 0.45 in the card's aura colour (per card).
6. Four sparkles in the card's palette.
7. Anim `paint`: the light direction swings ±1.6 rad, so the brushwork catches and loses the light, and a soft sheen drifts.

The tier stays the printed rarity (Rare Ultra, Rare Rainbow, Special Illustration Rare). Only the finish changes.

## 12. Animations

- **Format.**
  - `N = 16` frames at `FPS = 12` (`lib/s3anim.py`), composed at grid resolution from the same Card as the static art.
  - Frame values are stepped by 4 so the palette stays small. `batch_sir_futuristic.fit_pool` coarsens the moving frames to 6, 8 … when a busy painting overruns the 21 792-key pool; the last frame stays exact.
  - The **last frame is asserted identical to the static render**, for both normal and shiny.
- **Kinds.** `sets/evs/anim.py` `KINDS` has `sunpillar`, `etch`, `paint`, `rainbow`, `reverse`, `holo` and `gold`. `sets/p30/p30anim.py` adds `fireworks`, `ex`, `sir` and `chrome`.
- **What may move.** Only the background and the foil animate. The sprite may take a light gloss on its non-outline pixels; it never gets a colour change, except the rainbow and Futuristic flows.
- **Build.** The batch's `anim` step (or `p30anim.build(ids)`) writes `anim/<id>/` and `anim/<id>_shiny/`. The bundle is `<id>.anim`: a JSON header line (`lines`, `fps`, `frames`, `final`), then the frames' ANSI separated by form feeds. There are also gifs (`-term.gif`), a contact sheet and the final-frame PNG, for review.
- **Import.** The importer copies `<id>.anim` to `dist/pokemon/<character>-<id>[-shiny].anim` **only if its final frame equals the card's .ans byte for byte**.
- **At runtime,** `scripts/lib/anim.ps1` plays the loop until a key is pressed (`anim=untilkey`, at most 30 s).
- **Preview** in a terminal: `.\anim\play.ps1 <id>` from the data folder (`play.ps1` is copied there).
- **Non-foil tiers** (Common, Uncommon, Rare) have no animation.

## 13. The text half

- **Data.** Every card has a text half: the CARD_FORMAT JSON from the API, written to the set's `cards/<id>.json` by `fetch_set.py`, then copied into the pack by the importer.
- **Rendering for review.** `lib/bottom.py` `render_text(card, width, frame)` renders it for the review renders:
  - It is exactly the art's width, boxed in the rarity's frame colour, and `"rainbow"` gives a hue running around the box.
  - The rows are the header (name, V/VMAX/ex badge, HP, type glyph), abilities, attacks, and the footer (weakness / resistance / retreat, then set, number, rarity symbol and artist).
  - Energy is a one-cell `●` in the type colour, never emoji.
- **Frame colour.** For evs it comes from `bottom.RARITY_FRAME`. For later sets it comes from the builder's `meta["frame"]` (`p30build.render`). **Add a frame colour for every new rarity.**
- **In the product,** the binder (`binder/src/cardtext.rs`, `tools/binder_web.py`) draws the text half from `packs/pokemon/cards/<id>.json` and shows it with `v`. It stays hidden in tabs.
- `out/<id>-card[-shiny].png` (the art over its text half) is the third panel of every side-by-side.

## 14. Batch modules: how a set's code is organised

**A new Pokémon set** follows the p30 pattern:

1. **Copy the p30 modules.** Copy `artlab/sets/p30/p30{lib,cards,masks,build,anim,verify,sheet}.py` to `artlab/sets/<folder>/<x>{lib,cards,...}.py`.
2. **Point the set lib at the new data.** In `<x>lib.py`, set `SET` and `DATA = setlib.use_set(E, "<folder>", "<prefix>")`. This points evlib's `REF / MASKS / OUT / WORK / CARDS / ART` and `ref_path` at the new data folder. It also loads evs's `anim.py` / `build.py` **by file path** (`load_evs`): a plain `import anim` / `build` / `verify` can pick up another module of the same name.
3. **Write the ladder.** `<x>cards.py` holds the ladder builders, one per printed rarity, `BUILDERS = {id: fn}` and `ORDER`. Reuse the evs recipes wherever the finish matches: `tiers.holo_scene`, `silver_frame`, `fingerprint`, `rainbow_sprite`, `vmax_texture`, `window_rgb`, `matte`, and the alt-art emboss.
4. **Wire up anim and verify.** `<x>anim.py` holds `KINDS = {**A.KINDS, <new kinds>}` and `build(ids)`. `<x>verify.py` holds `check(cid)`: sprite pixel-exact apart from the allowed flip and recolour, card data verbatim with `tier == API rarity`, 16 frames, last frame == static art. It keeps a `fails` counter.

**Group modules.** There is one module per group, `batch_<group>.py`, owned by one agent. It has:

- `GROUP`, `PLAN = plan.json[GROUP]`, and `IDS`
- a per-card table (`CFG` / `SPEC` / `MASKS`): sprite, flip, mask recipe, `text_y`, extra boxes, `tex_src`, crop overrides, rim, vignette and star colours, frame colour, and a scene note
- `make_mask(cid)` and a mask review sheet
- `builder(cid)`, the approved example's recipe parameterised by that table
- `register(ids)`, which puts the builders into `evcards.BUILDERS` / `p30cards.BUILDERS` **in memory**. The shared modules are never edited.
- a CLI, `masks | build | anim | verify | sheet | all [ids]` (the exact verbs are in each module's docstring). It writes `sheets/<group>.png` and `sheets/<group>-sizes.json`.

**Agents never edit shared files:**

- evs: `evlib`, `evcards*`, `anim`, `build`, `verify`, `sheet`, `masks`
- p30: the `p30*` modules
- `lib/`
- the ladder's `sizes.json`, `sheet.png` and `ladder.png`

If an agent needs a shared fix, it implements it locally and notes it in its report. Example: `batch_sir_futuristic.fit_pool`.

**Precedence.** `art/<id>.json` holds whatever ran last. The approved version of a card comes from, lowest to highest:

1. the ladder (`evcards` / `p30cards`)
2. the group batch
3. **batch_rainbow_secret** (evs alt-art Rare Rainbows 205, 209, 212, 218, 220)
4. **batch_altart** (the 11 evs alt-art Rare Ultras, which replaced batch_ultra_a / _b's etch versions)
5. **batch_fixes** (the audit fixes: evs 210; p30 66, 26, 129). These apply their override in memory, so re-running the group batch alone would undo them.

To rebuild a card, run the highest module that lists it.

## 15. Review: the lookbook side-by-sides

The user judges every result in the **lookbook**. It is an Artifact page built from `artlab/lookbook/template.html`:

- It has sections with a `grid` (rows of images) and questions, and a **Decided** list at the top.
- Choices and notes save to the Artifact's db doc `lookbook/choices` (the page needs the `db` capability).
- The current page is https://claude.ai/artifact/LuEjHHYVQMumEPADwHwuJG. Its source was kept in the session's scratchpad as `lookbook/index.html`.
- A version holds at most 512 files and a publish sends at most 255. When the page is nearly full, prune decided sections' images or start a new page from the template.

**Always real card | ours | ours + text half, side by side, one row per card.** Build the sections with:

```powershell
.venv\Scripts\python artlab\tools\lb_set.py <folder> <group> [<group> ...] --lookbook <lookbook dir>
.venv\Scripts\python artlab\tools\lb_set.py evs altart --ids swsh7-175,swsh7-167 --lookbook <dir>   # an ad-hoc section
```

Each card becomes one jpg: the scan, `out/<id>-art.png` and `out/<id>-card.png` at 460 px high. The script
replaces the group's section (or inserts it next to the set's anchor section) and lists the new images in
`files-last.json` for the publish's `files`. Where a card has an effect, also show the animation
(`anim/<id>/<id>-term.gif`) in a figure.

Before every publish:

1. **Read the db choices.** Prune the answered questions and move them to Decided.
2. **Syntax-check the page script** (`node --check` on the extracted `<script>`). A broken script blanks the whole page.

Order of review:

1. **The ladder:** one card per printed rarity, each with its effect and animation. Nothing else is built until it is signed off.
2. **Each group,** as its agent finishes: the section's `ok` / `fix` question plus notes.
3. **The audit's flags,** as their own sections.

## 16. The audit

When every group is done, one audit agent checks **every** card against its scan on contact sheets. The tools are
`artlab/sets/<set>/audit/`:

- `contact.py`: real | ours sheets, several cards each
- `audit_meta.py`: the per-card metadata check. It reads the built outputs and `packs/pokemon` / `dist/pokemon`, and writes `work/audit/meta.json`.
- `verify_all.py`: the verify checks over every built card
- `report.py`: writes `audit/REPORT.md`
- `fixed_sheet.py`: real | before | after for each fix

**Checklist per card:**

- [ ] Treatment = the approved example of its printed rarity. Check the alt-art / true-rainbow split, and that Rare Ultra paintings are alt art.
- [ ] Sprite = the right Pokémon **and form**:
  - Gigantamax only on cards that are Gigantamax (G-Max attack)
  - regional forms (`-galar`, `-alola`, `-hisui`)
  - Lycanroc form, Crowned, Sunshine, Minior core
- [ ] **Facing** matches the card. Flag ambiguous poses instead of guessing.
- [ ] Scene is the card's own. No text, logos or stamp left. **No ghost** of the real Pokémon.
- [ ] Sprite pixel-exact (verify): outline and eyes exact; only the flip and the allowed recolour at its rarity.
- [ ] Data verbatim from the API; tier = printed rarity; text half present with the right frame colour.
- [ ] Commons: plain sprite, no background, no anim. Foil tiers: 16-frame anims (normal + shiny) whose last frame = the static art.
- [ ] Size ≤ 140 × 110 grid px.
- [ ] Coverage: every buildable card in the set list is built; skipped cards have a reason (Trainer / Energy / no sprite).

**Outcomes.** Each card ends up `ok`, `fixed`, `flagged` or `skipped` in `audit/REPORT.md` (see the two reports in
`artlab/sets/*/audit/`):

- **Clear errors** are fixed in `batch_fixes.py`: the owning batch module is loaded by path, the one faulty per-card setting is overridden in memory, and the card is re-rendered, verified and shown before / after.
- **Taste calls** (ambiguous facing, busy scenes) are flagged into the lookbook, not changed.

## 17. Import

`tools/build_realcards.py` turns a batch's `art/*.json` (and `anim/`, `cards/`) into the pack. For each card it does
the following:

1. **Real ids only.** It takes only real ids: variants named `invented`, containing `*`, or in `skip_variants` are skipped.
2. **Card data.** It copies `cards/<id>.json` into `packs/pokemon/cards/<id>.json`, and maps the printed rarity to the pack tier whose `rarity` equals it. **An unknown rarity stops the import:** add the tier first (section 18).
3. **Name check.** It checks that the card's name contains the sprite's Pokémon (`name_matches`): accents folded, and form suffixes stripped (`-gmax`, `-galar`, `-alola`, `-hisui`, `-paldea`, `-dusk`, `-midday`, `-midnight`, `-mega…`, `-sunshine`, `-poke-ball`, `-low-key`, `-crowned`, Minior's colours). **A new form suffix must be added to that regex.**
4. **Commons.** A card whose rarity is Common is built from the plain vendor sprite (`sprite_rows`) whatever the batch holds. Commons that are Trainers or have no sprite are skipped and reported.
5. **Palette.** It trims the palette to the keys the rows use. Rows using a key with no colour abort the import ("missing palette keys"). Busy sprites need the extended key alphabets (`sprite_rows` keys, `SPRITE_KEYS_EXT`).
6. **Build.** It writes `packs/pokemon/art/<id>.json` and builds `dist/pokemon/<character>-<id>[-shiny].ans` (`build_art`, cap 140 × 110). It copies the `.anim` files if their last frame equals the `.ans`, and records the card in `pack.json` `cards`.

```powershell
.venv\Scripts\python tools\build_realcards.py import evs --only swsh7-7,swsh7-8 --dry-run   # what would change
.venv\Scripts\python tools\build_realcards.py import evs --only swsh7-7,swsh7-8             # after the user approved them
git diff --stat packs\pokemon\pack.json
```

- **Use `--only` with the approved ids.** A full `import <batch>` imports *everything* in the batch's `art/`, including redos the user has not approved yet (the alt-art redo sat in `style-lab/evs/art/` before its approval).
- **The importer rewrites `pack.json` with LF line endings.** If `git diff` shows only line-ending changes, `git checkout packs\pokemon\pack.json`. If there are real changes, commit only those.
- A full import without `--only` also **prunes** art of cards no longer in pack.json.
- A new batch needs a `BATCHES` entry in `build_realcards.py`: the folder under `--lab`, the art globs and `skip_variants`. You can also pass a folder path.
- **Never import from a test or worktree run into the main checkout's live `dist/pokemon`.** The importer writes into the checkout it runs from.

## 18. Tiers, weights and tab skins (`packs/pokemon/pack.json`)

- **One tier per printed rarity.** A tier needs:
  - `id` (kebab-case), `label`, and `rarity` (exactly the API string)
  - `family` (non-foil, holo, ultra, full-art, secret, special)
  - `weight`: relative odds
  - `frame`: the card frame style
  - `skins`: tab shaders, by weight
  `build_realcards.py tiers` can sync these from `artlab/rarities/rarities.json`, but check its diff by hand.
- **Weights** are relative pull odds among the tiers that have built cards. Tiers with no built card never roll. The current values:

  | tier | weight |
  |---|---|
  | Common | 50000 |
  | Uncommon | 20000 |
  | Pikachu Rare | 10000 |
  | Rare | 8000 |
  | Rare Holo | 5000 |
  | Rare Holo V | 1500 |
  | Double Rare | 1400 |
  | Rare Holo VMAX | 800 |
  | Illustration Rare | 750 |
  | Rare Ultra | 650 |
  | Special Illustration Rare | 300 |
  | Rare Rainbow | 250 |
  | Rare Secret | 250 |
  | Futuristic Rare | 120 |

  Rarer printed rarities get smaller weights. Take the real pull rate from CATALOG.md.
- **Tab skins.** Each foil tier **leads with its own shader**, weight 10, then fallbacks. For example, Rare Holo `{"classic-holo": 10, "starlight": 4, "cosmos": 3}` and Futuristic `{"liquid-chrome": 10, "sheen": 4, "sunpillar": 2}`. The own-shader map is the last column of the tables in section 9.
  - A new rarity gets a new `packs/pokemon/shaders/<name>.hlsl`, written to `docs/SHADER_SPEC.md`: it imitates that finish, has a card-border frame, is lean, and compiles with fxc.
  - The shaders reach Windows Terminal through `install.ps1`, which the user runs. Never write WT `settings.json`, `$PROFILE` or the registry yourself.
- **Retired art.** The `retired` map (old art keys → the real card id, or `null`) keeps old pulls resolving in the binders. Add an entry when a card's art key changes.

## 19. Tests and the definition of done

Run the tests from a **PowerShell host**. Bash mangles the box characters.

```powershell
powershell -NoProfile -File tests\test-cards.ps1      # roll cache, card-mode odds, denied foils, retired pulls, 10k real-pack rolls
powershell -NoProfile -File tests\test-anim.ps1       # the effect-loop player
powershell -NoProfile -File tests\run-all.ps1         # everything
```

Every test is isolated: state goes to `%TEMP%`, and no tab is opened. `test-cards.ps1` section 6 rolls the real
pack 10 000 times against the locally built art. Every roll must be a pack.json card with built art, and the tier
frequencies must match the weights.

**A set is done when:**

1. Every buildable card in `plan.json` (plus the ladder) has `art/<id>.json`, `out/` renders (art, and art + text half; normal and shiny) and, for foil tiers, both anims. Every batch's `verify` reports 0 failures.
2. The lookbook has a side-by-side section per group, and the user approved each one (db choices). Fixes asked for are done and re-shown.
3. `audit/REPORT.md` covers every card of the set list (ok / fixed / flagged / skipped with a reason). Flags are in the lookbook.
4. The approved ids are imported with `--only`. Each one has `dist/pokemon/<character>-<id>.ans` and `-shiny.ans`, plus the two `.anim` files for foil tiers, and a `pack.json` `cards` entry at its printed-rarity tier. `pack.json`'s diff is only the new cards and tiers.
5. Each new rarity has a tier with a weight, a text-half frame colour and its own tab skin first.
6. `tests\test-cards.ps1` passes.
7. The lookbook's Decided list is updated.

## 20. Worked example: Leafeon V, swsh7-7 (Rare Holo V)

This is exactly how the live card was made, from the tracked code. Its mask is a pure hand polygon, so every step
reruns without rembg. Run it first in an **isolated** data root (as section 21 did), so nothing in `style-lab/` or
`dist/` changes. Drop the two `$env:` lines to work in the real data root.

```powershell
cd C:\Users\grego\repos\pokeshell
$env:ARTLAB_DATA = "$env:TEMP\artlab-try"                       # isolated data root (created by fetch_set)
$env:POKESHELL_VENDOR = "$PWD\vendor"                           # needed in a worktree; the default otherwise
```

1. **Data: the card, its API record and its scan.** Writes `setlist.json`, `cards\swsh7-7.json`, `cards\api\swsh7-7.json` and `ref\swsh7_7.png` under `$env:ARTLAB_DATA\evs`:
   ```powershell
   .venv\Scripts\python artlab\tools\fetch_set.py evs --ids swsh7-7
   ```
2. **Plan.** Leafeon V is in `artlab\sets\evs\plan.json`, group `v` (Rare Holo V). The approved example for the rarity is Sylveon V 74 (`evcards.sylveon`), and the group module is `batch_v.py`.
3. **Read the scan.** Look at the card: Leafeon faces left, which is the vendor sprite's own facing, so `flip=False`. It sits in the V window. The Ability starts at y 620, so `text_y=620`. Every segmenter takes the leafy background, so the mask is a hand polygon:
   ```powershell
   .venv\Scripts\python artlab\tools\grid.py evs 7
   ```
   The result is `batch_v.CFG["swsh7-7"] = dict(sprite="leafeon", flip=False, text_y=620, model=None, keep=1, add=([(210, 420), (235, 380), ...],))`.
4. **Mask, build, animation, checks, sheet:**
   ```powershell
   cd artlab\sets\evs
   ..\..\..\.venv\Scripts\python batch_v.py masks swsh7-7    # masks\swsh7-7.png (+ work\ review tile)
   ..\..\..\.venv\Scripts\python batch_v.py build swsh7-7    # art\swsh7-7.json, out\swsh7-7-{art,card}[-shiny].{ans,png}
   ..\..\..\.venv\Scripts\python batch_v.py anim swsh7-7     # anim\swsh7-7\swsh7-7.anim, anim\swsh7-7_shiny\...
   ..\..\..\.venv\Scripts\python batch_v.py verify swsh7-7   # VERIFY ALL PASS
   ..\..\..\.venv\Scripts\python batch_v.py sheet swsh7-7    # sheets\v.png: real | ours | ours + text half
   cd ..\..\..
   ```
   What `build_v` did (the Sylveon V 74 recipe):
   - `E.clean` with the mask grown 5 px, and the name bar, V corner swoosh and text region boxed out, texture fill
   - the unflipped sprite anchored on the real Leafeon's feet
   - the scene at grid scale, sat 1.4, focus halo, 24 k-means colours, sunpillar stripes, a 72-colour median cut, a light rim, the silver frame and 4 sparkles
   - `meta(anim="sunpillar", frame="#c9d1da")`
   The result is 88 columns × 37 lines.
5. **Look.** Open `sheets\v.png` (or `out\swsh7-7-card.png`) with the Read tool, next to the scan. Iterate on the CFG row until it holds up next to the real card at the approved example's quality.
6. **Lookbook** (start from `artlab\lookbook\template.html` if there's no page):
   ```powershell
   .venv\Scripts\python artlab\tools\lb_set.py evs v --ids swsh7-7 --lookbook <lookbook dir>
   ```
   Publish the page with the new `files-last.json` images, and wait for the user's `ok`.
7. **Import** (only after approval, and only into the checkout that should get it):
   ```powershell
   .venv\Scripts\python tools\build_realcards.py import evs --lab $env:ARTLAB_DATA --only swsh7-7 --dry-run
   .venv\Scripts\python tools\build_realcards.py import evs --lab $env:ARTLAB_DATA --only swsh7-7
   #   built swsh7-7  leafeon  rare-holo-v  88x74px  87.9 KB  Leafeon V [evs:swsh7-7.json#rare-holo-v]  + anim, anim-shiny
   git diff --stat packs\pokemon\pack.json      # line endings only -> git checkout packs\pokemon\pack.json
   powershell -NoProfile -File tests\test-cards.ps1
   ```
   This writes `dist\pokemon\leafeon-swsh7-7.ans`, `-shiny.ans`, `.anim` and `-shiny.anim`, the art JSON and the text JSON.

Run in an isolated data root on 2026-09-29, every file in this chain was byte-identical to the live card: the mask,
`art\swsh7-7.json`, both `.anim` files, and all four `dist\pokemon\leafeon-swsh7-7*` files.

## 21. Reproducibility check

Proof that the tracked code rebuilds the live cards: run the batch in an isolated data root, import it in a
**worktree** (the importer writes into the checkout it runs from), and byte-compare with the live files.

```powershell
# in a worktree of the repo (git worktree add ..\pokeshell-x -b x), with the main checkout's venv and vendor
$py = 'C:\Users\grego\repos\pokeshell\.venv\Scripts\python'
$env:ARTLAB_DATA = "<scratch>\data"      # holds only ref\, masks\, cards\ (+ cards\api\) of the chosen ids, copied in
$env:POKESHELL_VENDOR = 'C:\Users\grego\repos\pokeshell\vendor'
cd artlab\sets\evs
& $py batch_holo.py build swsh7-19; & $py batch_holo.py anim swsh7-19
& $py batch_altart.py build swsh7-175
cd ..\p30; & $py batch_sir_futuristic.py me55-158
cd ..\..\..
& $py tools\build_realcards.py import evs --lab $env:ARTLAB_DATA --vendor $env:POKESHELL_VENDOR --only swsh7-125,swsh7-19,swsh7-175 --no-previews
& $py tools\build_realcards.py import p30 --lab $env:ARTLAB_DATA --vendor $env:POKESHELL_VENDOR --only me55-158 --no-previews
fc.exe /b dist\pokemon\entei-swsh7-19.ans C:\Users\grego\repos\pokeshell\dist\pokemon\entei-swsh7-19.ans   # ... every file
git checkout packs\pokemon\pack.json; Remove-Item -Recurse dist\pokemon, packs\pokemon\art, packs\pokemon\cards
```

Result on 2026-09-29: every one of these files was byte-identical to the live ones:

| card | rarity | route |
|---|---|---|
| Eevee swsh7-125 | Common | importer plain sprite |
| Entei swsh7-19 | Rare Holo | batch_holo |
| Glaceon V swsh7-175 | Rare Ultra alt art | batch_altart |
| Leafeon V swsh7-7 | Rare Holo V | batch_v, mask included |
| Mew ex me55-158 | Futuristic Rare | batch_sir_futuristic through p30lib / setlib |

The files compared were `.ans`, `-shiny.ans`, `.anim`, `-shiny.anim` and the art JSON.

## 22. Known pitfalls

- **The pokemontcg.io API.** It needs a User-Agent (plain `requests.get` without one gets refused) and it is flaky. Retry with backoff, fetch in several passes, and keep what's already on disk.
- **`pack.json` line endings.** The importer rewrites `pack.json` with LF. If only line endings changed, restore it (`git checkout packs\pokemon\pack.json`).
- **Name matching.** It must fold accents (Flabébé) and strip form suffixes. A new form (`-origin`, `-therian`, `-bloodmoon` …) fails the import until it is added to `name_matches`.
- **Missing palette keys.** Rows with a key that has no colour abort the import. Sprites with many colours need the extended key alphabets. The rainbow and Futuristic re-keys use Hangul.
- **A full `import` can make unapproved redos live.** Always pass `--only` with approved ids.
- **Tests must run from a PowerShell host,** not bash.
- **Same-named modules.** `anim`, `build` and `verify` exist in several folders (and `build` is a pip package). Load a set's own by file path, as the batch modules do (`evs_module`, `_local`, `load_evs`).
- **Ladder files.** Don't run the ladder scripts (`build.py`, `sheet.py`, `p30build.py`, `p30sheet.py`, `p30verify.py`) without ids: they rewrite the ladder's `sizes.json`, `sheet.png` and `ladder.png`.
- **Audit fixes live in memory.** Re-running a group batch undoes an audit fix, so rebuild fixed ids through `batch_fixes.py` (section 14).
- **Ghosts.** Full-card Pokémon (ex, Futuristic, IR) leave remnants in the fill. Grow the mask with a colour rule, or use `texture=False`.
- **The size cap.** A card over 140 × 110 is refused at import. Shorten the crop by whole sprite rows.
- **API "Rare Rainbow" includes alt-art paintings.** Decide per scan.
- **The rembg first run** downloads the models. Keep the `work/rembg-*` caches: they make masks reproducible.
- **The key pool.** Busy 16-frame paintings can overrun the anim key pool. Coarsen the moving frames (`fit_pool`), never the last.
- **Console encoding.** Piped output (from bash, or captured) is cp1252 on Windows, and printing "Nidoran ♀" crashes the importer mid-run. Set `PYTHONIOENCODING=utf-8`.
- **Isolation.** Never write to `%LOCALAPPDATA%\pokeshell`, WT `settings.json`, `$PROFILE` or the registry. Never write to the live `dist\pokemon` or `packs\pokemon\art` from a test run. Never spawn WT tabs.

## 23. Adapting to other card games

The method carries over. What changes is where the sprite, the card data and the scene come from.

**What stays the same:**

- the ART_FORMAT grid: a 2 × 2 block per sprite px, over a scene at grid resolution, the palette keys, the 140 × 110 cap
- real cards only, keyed by the source's card id; each printed rarity gets its own tier and effect, escalating
- the ladder → sign-off → batch agents → audit → `--only` import flow, with the lookbook side-by-sides (real | ours | ours + text half)
- the effect engine: `lib/` plus the evs recipes (holo bands, V-style frames, etch, painting emboss, rainbow, gold, chrome) and the 16-frame loops at 12 fps with the last frame = static
- the text half as a boxed block under the art, and per-tier tab skins

### One Piece TCG (opshell)

- **Sprites.** The sources are *Gigant Battle! 1 and 2* (DS pixel sprites: 31 of OP-01's 92 characters, pre-Wano) and *Treasure Cruise* (mobile chibi art: 82 of 92). The research samples, URLs and rippers' credits are in `style-lab/op-sprites/SOURCES.md` (local-only).
  - Cut the idle frame from a sheet with `artlab/tools/sprite_sheet.py label|cut`.
  - Treasure Cruise art is HD: turn it into pixels with `artlab/tools/pixelize.py` (LANCZOS to about 96 px tall, sat 1.25, 48-colour median cut).
  - Keep the cut sprites in a vendor-like folder: git-excluded, never published.
  - The sprite is still unchanged apart from the flip. A near-black outline may need lifting to read on a black terminal (the research's `-lift` renders).
  - **What changes:** `sprites.load` / `Sprite` read a PNG instead of a colorscripts file. There is no shiny palette unless the game has one, so shiny = normal, or make shiny rolls impossible for that pack.
- **Card data.** It comes from optcgapi.com (`https://optcgapi.com/api/sets/OP-01/`); artists from Limitless and the official-site fields from punk-records. **What changes:**
  - a new fetcher and a new CARD_FORMAT: cost, power, counter, colour, attribute, type, effect text, trigger
  - a new text half (`bottom.py` rows for those fields)
  - the rarity list: C, UC, R, SR, SEC, L (Leader), SP, TR, manga / alt art. Each needs its own tier, effect family (map it to the closest Pokémon finish: SR ≈ holo, SEC ≈ gold / rainbow, alt art = the painting treatment, manga = its own) and shader.
- **Scenes.** The card's own scene, with the character painted out, the same way (rembg does well on anime art). The card layouts, art windows and furniture boxes (cost circle, power, counter, name bar) need measuring per era.
- **opshell's current wanted-poster frame and foil backgrounds** (`style-lab/op-crew`) are a different, older pipeline. The user picks between them and this method in the lookbook.

### Magic: The Gathering Marvel (a new sibling repo, likely "mtgshell")

- **Card data.** Scryfall: sets `spm` (Spider-Man) and `msh`, `https://api.scryfall.com/cards/<set>/<number>`. Send a User-Agent and Accept header, and keep to their rate limit. **What changes:**
  - CARD_FORMAT becomes mana cost, type line, oracle text, P/T or loyalty, flavour and artist, with a new text half.
  - The rarities are common, uncommon, rare and mythic, plus the treatments: foil, showcase / borderless, extended art, surge / galaxy foils, serialized. Each printed treatment the set has gets its own tier and effect.
- **Scenes.** **Scryfall's image policy forbids altering card images** (no colour-shifting, no cropping into new art). The "real scene, Pokémon painted out" step cannot be used, so **the scenes must be our own**. This is the biggest change:
  - Keep the treatment escalation (matte → foil → frame → full art), but compose original backgrounds: procedural skylines and webs, the effect engine's foils, or scenes drawn to the card's mood.
  - Show the real card only in the review side-by-side (read-only), never in the art.
- **Sprites.** The 90s games: the SNES *Spider-Man* (1995) roster, which covers 23 of 72 characters, and Marvel vs. Capcom (CPS2). Marvel Cosmic Invasion covers MSH. Research samples and credits are in `style-lab/mtg-marvel/SOURCES.md`; `lab.py` builds its compare sheets.
  - Characters without a sprite become **recolours** of an existing one: Spider-Man → symbiote-suit or Miles-style palettes, Venom → Carnage or Anti-Venom palettes. The games' own palette slots are the model.
  - A recolour is a palette remap that keeps the shape, outline and eyes, the same kind as the gold / rainbow remaps. Get each one approved in the lookbook like a ladder card.
  - Oversized sprites (MvC Venom is 148 × 112) exceed the 140 × 110 cap: downscale by an integer factor, or pick another frame.
- **Code.** Copy `artlab/` into the new repo (it is self-contained apart from `tools/build_art.py` and `tools/render_ansi.py`, which it also needs). Write `sets/<set>/` the p30 way, and give it its own importer modelled on `build_realcards.py` with its own name matching and tiers.

## 24. Known gaps in the method

These are things a fresh agent can't just rerun. Decide them with the user, or fix them.

- **Commons are never flipped.** The rule says match the card's facing, but the importer's plain sprite has no flip. Three 30th Celebration commons face the wrong way (Tropius 5, Murkrow 93, Kangaskhan 114, flagged). Fixing it means a per-card flip for commons in `build_realcards.sprite_rows` (for example from the batch's `plan.json`).
- **Reverse Holo** has a ladder recipe (Pikachu 49) but no importable tier: the tier lacks `rarity`, and the API has no reverse-holo printing id. It is live as a Common. Open question.
- **The 30th Celebration Rare tier.** ME rares are holo and have an animation, but the pack's `rare` tier is non-foil with no skin. Their `.anim` plays, but they get no tab shader.
- **Mew ex 158's Futuristic tint** barely reads at 0.3 (it falls back to the darkest tone). 0.45 was suggested, which would exceed the 0.35 the user asked for. This needs the user's call.
- **The last writer wins in `art/`.** There is no manifest of which module produced each live card, so the precedence in section 14 has to be followed by hand. A rebuild that runs the group batch for a fixed or redone id silently reverts it.
- **Hand-read inputs.** The per-card tables were read off the scans by agents and are not derivable: crops, `text_y`, polygons, `tex_src`, rim and star colours, flips and the alt-art / rainbow split. They are tracked in the batch modules, but a new set needs the same judgement per card.
- **rembg caches are data.** Masks that start from rembg are exact only with the cached `work/rembg-*.png` (or the pinned rembg / onnxruntime and the same model files). They are not tracked, because they are derived from the scans.
- **The lookbook lived in a session scratchpad.** `lb_set.py` used to hard-code that path. The page shell is now `artlab/lookbook/template.html`, but the live page's content (its sections, Decided list and published files) exists only as the published Artifact.
- **One-off scripts not carried over:** evs `work/*` comparisons (`v_cmp`, `mcmp`, `sprsheet`), `std/std.py` (the rejected standard-size mockup), p30 `work/rembg_all.py`, `contact.py`, `dr_view.py` and `sf_cmp.py`. They are exploration aids; the method doesn't depend on them.
- **`effects.py`** (the 60-rarity engine) has no `render_card()`, so `build_realcards.py --effects` has never worked. The shipped cards all come from the batch recipes.
- **Fonts.** The contact sheets and lookbook images use `C:/Windows/Fonts/consola.ttf`, which ties them to Windows.
