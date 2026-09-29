# Hidden Fates full set: brief for the batch agents

The ladder in this folder is one real card per printed rarity (`hfcards.py`, `ORDER`). It sets the quality bar and the
look, as the Evolving Skies and 30th Celebration ladders did. Now every remaining Pokémon card of Hidden Fates
(`sm115`) and its Shiny Vault (`sma`) is built. Each agent owns one or more groups in `plan.json` and builds exactly
those cards, the way the ladder card of that rarity was built. The method is `docs/ART_METHOD.md`: read sections 1
and 6-14 before starting.

## Environment

- Code: the worktree `C:\Users\grego\repos\pokeshell-hf`, folder `artlab\sets\hf` (run the modules from there).
- Data: `C:\Users\grego\repos\pokeshell\style-lab\hf` (scans `ref\hf_<number>.png`: sm115 numbers `1..69`, Shiny
  Vault numbers `SV1..SV94`; `cards\<id>.json`, `cards\api\<id>.json`; `masks\`, `work\`, `art\`, `out\`, `anim\`,
  `sheets\`).
- Every command needs, in bash:
  `export ARTLAB_DATA='C:\Users\grego\repos\pokeshell\style-lab' POKESHELL_VENDOR='C:\Users\grego\repos\pokeshell\vendor' PYTHONIOENCODING=utf-8`
  and the Python `C:\Users\grego\repos\pokeshell\.venv\Scripts\python.exe` (Pillow, numpy, scipy, scikit-image, rembg).
- Never read API keys or `.env` files. No image-generation APIs. Never write to `C:\Users\grego\repos\pokeshell\dist`,
  `packs\pokemon\art`, `%LOCALAPPDATA%\pokeshell`, Windows Terminal settings, `$PROFILE` or the registry. Never
  spawn WT tabs. Do not import, commit or touch git: the lead does that.
- Coordinate grids: `artlab\tools\grid.py hf <number> [--crop x0 y0 x1 y1 --step 25]` writes `work\grid_<number>.png`.
  Open it (and every review sheet) with the Read tool.

## Approved examples (the ladder) and what each group copies

| Group | Rarity | Ladder card | Recipe (hfcards.py) | anim | frame |
|---|---|---|---|---|---|
| `commons` | Common | Charmander 7 | plain sprite, no background (`batch_commons.py`, done) | none | #9aa0aa |
| `uncommon` | Uncommon | Charmeleon 8 | `charmeleon()`: `window_rgb(texture=False)` + evs `matte(scale=2)`, 12 colours, sat .84 / bright .88 | none | #8fc4a8 |
| `rare` | Rare | Mew 32 | `mew()`: SM rares are NON-foil: `window_rgb` + `matte(scale=1)`, 16 colours, sat .95 / bright .95 | none | #6ea5ff |
| `holo` | Rare Holo | Vaporeon 18 | `vaporeon()`: `tiers.holo_scene(ncol=12, foil=0.22)` in `SM_WIN` | `holo` | #56d0e0 |
| `holo_gx` | Rare Holo GX | Charizard-GX 9 | `gx_card(cid, spr, x0, y0, S, W, H, boxes, tex_src=...)`: art frame to frame, silver frame, GX web foil | `gxweb` | #6fa8dc |
| `shiny_a`, `shiny_b` | Rare Shiny | Charmander SV6 | `vault_card(cid, ShinySprite(name, flip), x0, y0, S, W, H, tex_src=...)` | `vault` | #b4c0ce |
| `shiny_gx_a`, `shiny_gx_b` | Rare Shiny GX | Charizard-GX SV49 | `vault_gx_card(cid, ShinySprite(name, flip), x0, y0, S, W, H, boxes, texture=False)` | `vaultgx` | #e6ecf5 |
| `secret` | Rare Secret | Tapu Koko-GX SV93 | `gold_card(cid, Sprite(name), x0, y0, S, W, H, boxes)` (evs Froslass gold) | `gold` | #f0c850 |

The recipe functions set the rarity, finish, anim kind and frame colour themselves: call them, don't copy them.

## Rules (decided by the user; not up for change)

- **Real cards only.** Build exactly the ids of your group in `plan.json`. The ladder ids are `_ladder_done`;
  Trainers and the three Moltres & Zapdos & Articuno TAG TEAM cards are `_skipped`.
- **The sprite** is the pokemon-colorscripts large sprite, pixel-exact and unchanged. Only a horizontal flip is
  allowed (plus the gold remap at Rare Secret, done by `gold_card`). `plan.json` gives the sprite name per card
  (forms: Alolan Vulpix / Ninetales, Lycanroc SV66 Midnight and SV67 Dusk, Zygarde SV65 Complete).
- **Shiny Vault (every `sma` Rare Shiny / Rare Shiny GX card) shows the SHINY Pokémon**: always `ShinySprite(name,
  flip)` (hflib). Regular cards and the gold Tapu use `Sprite(name, flip)`. `hfverify` checks this.
- **Facing:** match the real card. Read which way the head / body points on the scan and flip if the vendor sprite
  faces the other way (most vendor sprites face LEFT; `work\sprites_all.png` shows every sprite of the set).
  Near-frontal poses: don't flip, and list them as ambiguous in your report.
- **The scene** is the card's own, with the real Pokémon masked out and filled. No text or logos in the art: box
  out the name bar `TOP`, the stage `ICON` and `EVOLVES` bar (Stage 1 / 2), the "Ultra Beast" banner (top right of
  UB cards, read it off the grid), everything from the card text down (`(0, text_y, 734, 1024)`), the frame edges.
- **Size:** each card is sized to its art (`HB.layout_window` / `HB.layout_full` give the default crop), at most
  140 x 110 grid px and in practice about 104 cols. `hfverify` checks the cap.
- **No ghosts:** when the Pokémon covers most of the card (GX, Shiny GX, gold), check the fill for remnants of the
  real Pokémon (its coloured outline on the Shiny GX cards: `hfmasks.outline_halo`). Grow the mask or use
  `texture=False`.
- **Text half, anim, verify** are done by the runner. Every foil card needs its 16-frame loop whose last frame is
  the static art (normal and shiny); `hfverify` must report 0 failures.

## How to build (without colliding with the other agents)

- Write ONE module per group, `batch_<group>.py`, in `artlab\sets\hf`. Pattern (see `batch_commons.py`):
  ```python
  import hflib as P; from hflib import E, L, Sprite, ShinySprite
  import hfcards as C, hfmasks as HM, hfbatch as HB
  GROUP = "shiny_a"; PLAN = HB.plan(GROUP)
  CFG = {cid: dict(flip=..., tex_src=..., boxes=..., dx=0, dy=0, ...)}     # per card, read off the scans
  def m_<n>(): ...                                                             # mask recipes (HM.sm_window, HM.poly ...)
  MASKS = {cid: fn}
  def make(cid): spr = ShinySprite(PLAN[cid]["sprite"], CFG[cid]["flip"]); x0, y0, S, W, H = HB.layout_window(cid, spr); return C.vault_card(...)
  BUILDERS = {cid: (lambda cid=cid: make(cid)) for cid in PLAN}
  if __name__ == "__main__": HB.run(GROUP, BUILDERS, MASKS, sys.argv[1:])
  ```
  Then: `python batch_<group>.py masks` (look at `work\masks-<group>.png`), `python batch_<group>.py build <ids>` to
  iterate, and finally `python batch_<group>.py all` (build + anim + verify + `sheets\<group>.png`).
- **Look at your results.** Open `sheets\<group>.png` (real | ours | ours + text) in slices (crop it with PIL into
  a few images) and compare each card with its scan: right Pokémon and form, facing, no ghost, no text. Iterate
  on the CFG row until each holds up next to the ladder card of its rarity.
- **Never edit shared files:** `hflib.py`, `hfcards.py`, `hfmasks.py`, `hfbatch.py`, `hfbuild.py`, `hfanim.py`,
  `hfverify.py`, `hfsheet.py`, `set.json`, `plan.json`, other agents' `batch_*.py`, anything in `artlab\lib`,
  `artlab\sets\evs|p30`, `tools\`. Don't run `hfbuild.py`, `hfsheet.py`, `hfverify.py`, `hfanim.py` without ids
  (they rewrite the ladder's `sizes.json`, `sheet.png`, `ladder.png`). If you need a shared fix, do it locally in your
  module and say so in your report.
- Masks, art, out, anim are per id, so agents don't collide. rembg caches: `work\rembg-<model>-<id>.png`.

## Group notes

- **uncommon (7), rare (11), holo (2):** the regular SM layout, art window `SM_WIN = (58, 100, 676, 482)`; Stage 1 /
  2 cards need `ICON` and `EVOLVES` boxed (`HM.sm_window(..., stage=True)` for the mask, and pass them in
  `window_rgb` boxes). rembg (`isnet-general-use`, `isnet-anime`, `u2net`) usually catches these Pokémon; busy
  scenes need a hull (`HM.poly`). Big sprites (Butterfree 41x38, Weezing 47x43, Zapdos 46x38): `HB.layout_window`.
- **holo_gx (7):** Pinsir, Starmie, Gyarados, Raichu, Mewtwo, Onix, Wigglytuff. The Pokémon fills the card: masks
  are the main work (Charizard 9 needed a hand hull on top of rembg). Art from y 92 to where the attacks start
  (read `text_y` per card), boxes `C.EDGES + (C.TOP, HM.ICON, HM.EVOLVES, (0, text_y, 734, 1024))`. Crop:
  `HB.layout_full(cid, spr, top=92, text_y=...)`. A `tex_src` patch of clean scenery keeps the fill textured.
- **shiny_a / shiny_b (22 + 22):** the Shiny Vault layout is the regular SM window, a WHITE window with pale gold
  sparkle stars; the Pokémon on white is easy for rembg (`HM.sm_window(cid)`; `stage=True` for Stage 1 / 2). Use a
  `tex_src` patch of the star pattern away from the Pokémon so the fill carries the stars. Ultra Beasts carry an
  "Ultra Beast" banner at the window's top right (about `(470, 96, 700, 130)`): box it (window_rgb boxes) and keep
  it out of the mask. The vault foil keeps stars only where the real card shows them (`hole_map`).
- **shiny_gx_a / shiny_gx_b (17 + 17):** full art on white with the shiny Pokémon drawn with a thick coloured
  outline and big sparkles. Mask = rembg (u2net often best) plus `HM.outline_halo(cid, m)` so the outline leaves no
  ghost; box the text from where the first ability / attack starts (`text_y`, often 480-600), plus TOP, ICON,
  EVOLVES and the Ultra Beast banner. `texture=False` (the white ground). Crop `HB.layout_full`. Very wide sprites
  (Zygarde Complete 50x45, Guzzlord 55x38, Reshiram 52x41) must stay within 140 x 110 grid px.
- **secret (3):** Tapu Bulu SV91, Fini SV92, Lele SV94 as Tapu Koko SV93: `HM.tapu_mask(cid)` (everything that is
  not the gold field), boxes `C.EDGES + (C.TOP, (0, text_y, 734, 1024))` with `text_y` where the ability / first
  attack starts, crop `HB.layout_full`.

## Deliverables per agent

1. Every card in your group(s) built: `art\<id>.json`, `out\` renders (art, art + text; normal and shiny), anims
   for foil tiers, `sheets\<group>.png`, `hfverify` 0 failures.
2. A short report: per card anything notable (mask method, flip and why, ambiguous facing, known ghosts or
   compromises), and any shared fix you needed.
