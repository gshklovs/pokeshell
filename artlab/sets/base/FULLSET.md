# Base Set full set: brief for the batch agents

The ladder in this folder is one real card per printed rarity (`basecards.py`, `ORDER`). It sets the quality bar
and the look, as the Evolving Skies, 30th Celebration and Hidden Fates ladders did. Now every remaining Pokémon
card of the Base Set (`base1`, 1999) is built. Each agent owns one group in `plan.json` and builds exactly those
cards, the way the ladder card of that rarity was built. The method is `docs/ART_METHOD.md`: read sections 1 and
6-14 before starting.

## Environment

- Code: the worktree `C:\Users\grego\repos\pokeshell-base`, folder `artlab\sets\base` (run the modules from there).
- Data: `C:\Users\grego\repos\pokeshell\style-lab\base` (scans `ref\base1_<number>.png`, 600 x 825; `cards\<id>.json`,
  `cards\api\<id>.json`; `masks\`, `work\`, `art\`, `out\`, `anim\`, `sheets\`).
- Every command needs, in bash:
  `export ARTLAB_DATA='C:\Users\grego\repos\pokeshell\style-lab' POKESHELL_VENDOR='C:\Users\grego\repos\pokeshell\vendor' PYTHONIOENCODING=utf-8`
  and the Python `C:\Users\grego\repos\pokeshell\.venv\Scripts\python.exe` (Pillow, numpy, scipy, scikit-image, rembg).
- Never read API keys or `.env` files. No image-generation APIs. Never write to `C:\Users\grego\repos\pokeshell\dist`,
  `packs\pokemon\art`, `%LOCALAPPDATA%\pokeshell`, Windows Terminal settings, `$PROFILE` or the registry. Never
  spawn WT tabs. Do not import, commit or touch git: the lead does that. Other agents are building other sets
  (`brs`, `cz`, `hf`): never touch their folders.
- Coordinate grids: `..\..\tools\grid.py base <number> [--crop x0 y0 x1 y1 --step 25]` writes `work\grid_<number>.png`;
  the labels are card px. `--crop 40 80 560 445 --step 25` zooms onto the art window. Open it (and every review sheet)
  with the Read tool.
- `rembg_all.py <out.png> <ids>`: the three rembg models side by side on the art window. `facing.py <name> <ids>`:
  the art window next to the vendor sprite (unflipped), for reading the facing.

## Approved examples (the ladder) and what each group copies

| Group | Rarity | Ladder card | Recipe (basecards.py) | anim | frame |
|---|---|---|---|---|---|
| `commons` | Common | Charmander 46 | plain sprite, no background (`batch_commons.py`, done) | none | #9aa0aa |
| `uncommon` (20) | Uncommon | Charmeleon 24 | `uncommon_card(cid, spr, crop=None, boxes=(STAGE,) or (), dx, dy, scene)`: `window_rgb(texture=False)` + evs `matte(scale=2)`, 12 colours, sat .84 / bright .88 | none | #8fc4a8 |
| `rare` (6) | Rare | Dragonair 18 | `rare_card(cid, spr, crop=None, boxes, tex_src, grow=8, texture=True, dx, dy, scene)`: WotC rares are NON-foil: `window_rgb` + `matte(scale=1)`, 16 colours, sat .95 / bright .95 | none | #6ea5ff |
| `holo` (16) | Rare Holo | Charizard 4 | `holo_card(cid, spr, crop=None, boxes, tex_src, grow=5, texture=True, dx, dy, seed, scene)`: the approved Rare Holo scene (grid, 12 colours, rim, 4 sparkles) with the WotC starlight foil (nebula + starbursts + faint cosmos swirl) | `wotc` | #56d0e0 |

The recipe functions set the rarity, finish, anim kind and frame colour themselves: call them, don't copy them.
`crop=None` uses `C.layout(cid, spr)` (sized to the art: the largest scale that fits the sprite + 1 px in the art
window, cropped to <= 52 sprite px wide around the real Pokémon). Pass an explicit `crop=(x0, y0, S, W, H)` only when
the default is wrong.

## Rules (decided by the user; not up for change)

- **Real cards only.** Build exactly the ids of your group in `plan.json`. The ladder ids are in `set.json` `ladder`
  (base1-24 and base1-18 and base1-4 are already done: skip them); Trainers and Energy are `_skipped`.
- **The sprite** is the pokemon-colorscripts large sprite, pixel-exact and unchanged. Only a horizontal flip is
  allowed. `plan.json` gives the sprite name per card. Use `Sprite(name, flip)` (baselib).
- **Facing:** match the real card. Read which way the head / body points on the scan and flip if the vendor sprite
  faces the other way (nearly every vendor sprite faces LEFT; `work\allsprites.png` shows every sprite of the set,
  `facing.py` makes a side-by-side). Near-frontal poses: don't flip, and list them as ambiguous in your report.
- **The scene** is the card's own, with the real Pokémon masked out and filled. No text or logos in the art:
  `window_rgb` already replaces everything outside `BASE_WIN = (66, 100, 534, 424)` (the yellow border, name / HP,
  1st Edition stamp, length / weight bar); Stage 1 / 2 cards need `STAGE = (18, 18, 150, 148)` in `boxes` (the
  evolution badge hangs over the window's top-left corner) and `stage=True` in the mask.
- **Keep the painted and CGI backgrounds faithful**: pick a `tex_src` patch of the same material (sky, grass,
  starfield, CGI gradient) away from the Pokémon, so the fill carries the scene's texture.
- **Size:** each card is sized to its art (`C.layout`), at most 140 x 110 grid px, in practice <= 104 cols.
  `baseverify` checks the cap.
- **No ghosts:** check the fill for remnants of the real Pokémon (a tail tip, a flame, a glow halo, a shadow).
  Grow the mask (`grow=` in `HM.base_window`, or the recipe's `grow`) or add a hand polygon.
- **Text half, anim, verify** are done by the runner. Every foil card needs its 16-frame loop whose last frame is
  the static art (normal and shiny); `baseverify` must report 0 failures.

## How to build (without colliding with the other agents)

- Write ONE module, `batch_<group>.py`, in `artlab\sets\base`. Pattern:
  ```python
  import sys
  import baselib as P; from baselib import E, Sprite
  import basecards as C, basemasks as HM, basebatch as HB
  GROUP = "holo"; PLAN = HB.plan(GROUP)
  LADDER = set(P.META["ladder"])
  CFG = {cid: dict(flip=..., stage=..., tex_src=..., dx=0, dy=0, scene="...")}   # per card, read off the scans
  def m_<n>(): ...                                                               # mask recipes
  MASKS = {cid: fn}
  def make(cid):
      k = CFG[cid]; spr = Sprite(PLAN[cid]["sprite"], k["flip"])
      return C.holo_card(cid, spr, crop=k.get("crop"), boxes=(C.STAGE,) if k["stage"] else (), tex_src=k["tex_src"],
                         dx=k.get("dx", 0), dy=k.get("dy", 0), scene=k["scene"])
  BUILDERS = {cid: (lambda cid=cid: make(cid)) for cid in PLAN if cid not in LADDER}
  if __name__ == "__main__": HB.run(GROUP, BUILDERS, MASKS, sys.argv[1:])
  ```
  Then: `python batch_<group>.py masks` (look at `work\masks-<group>.png`), `python batch_<group>.py build <ids>` to
  iterate, and finally `python batch_<group>.py all` (build + anim + verify + `sheets\<group>.png`).
- **Look at your results.** Open `sheets\<group>.png` (real | ours | ours + text) in slices (crop / resize it with
  PIL into images of 2-3 cards) and compare each card with its scan: right Pokémon, facing, no ghost, no text.
  Iterate on the CFG row until each holds up next to the ladder card of its rarity.
- **Never edit shared files:** `baselib.py`, `basecards.py`, `basemasks.py`, `basebatch.py`, `basebuild.py`,
  `baseanim.py`, `baseverify.py`, `basesheet.py`, `facing.py`, `rembg_all.py`, `set.json`, `plan.json`, other agents'
  `batch_*.py`, anything in `artlab\lib`, `artlab\sets\evs|p30|hf|cz`, `tools\`. Don't run `basebuild.py`,
  `basesheet.py`, `baseverify.py`, `baseanim.py` without ids (they rewrite the ladder's `sizes.json`, `sheet.png`,
  `ladder.png`). If you need a shared fix, do it locally in your module and say so in your report.
- Masks, art, out, anim are per id, so agents don't collide. rembg caches: `work\rembg-<model>-<id>.png`.

## Group notes

- **All:** the WotC layout: art window `BASE_WIN`, the gold bevel frame round it, the Stage badge `STAGE` over its
  top-left corner on Stage 1 / 2 cards (`plan.json` has no stage; read it off the card or `cards\<id>.json`
  `subtypes`). rembg struggles on these 1999 scans: expect to need hand hulls (`HM.poly(sh, pts)` in card px read off
  the zoomed grid) and colour rules (`HM.hsv(cid)`), as the ladder's Charmeleon tail / flame, Dragonair's tail tip
  and Charizard's full hull did (`basemasks.py`). A Pokémon in two parts (a tail rising out of water) is `keep=2`.
- **uncommon (20):** painted scenes (Arcanine's grass, Dewgong's bubbles, Haunter's dark cave, Kakuna's radial
  lines, Magmar's fire, Nidorino's canyon, Porygon's CGI hills, Raticate's grass). Ghosts to watch: flames (Magmar,
  Arcanine?), Haunter's shadow, Kakuna's glow ring.
- **rare (6):** Beedrill (forest), Dugtrio (only the three heads are Dugtrio; the mound they rise from is the
  scene), Electabuzz (a big yellow glow + lightning
  round him: the glow is part of the Pokémon's figure, paint it out with him, the lightning bolts are scene),
  Electrode (radial rainbow burst: the burst is scene), Pidgeotto (sky). `tex_src` for the fill.
- **holo (16):** every holo art is the Pokémon over the Base Set holo starfield (dark blue / red / green with star
  sparkles). rembg mostly takes the starfield: hand hulls like Charizard 4. `tex_src` a starfield patch away from
  the Pokémon and the Stage badge. Big sprites (Venusaur 43x39, Zapdos 46x38, Nidoking 42x33, Poliwrath 41x31):
  `C.layout` handles them (<= 104 cols). The anim is `wotc`, built by the runner.

## Deliverables per agent

1. Every card in your group built: `art\<id>.json`, `out\` renders (art, art + text; normal and shiny), anims for
   foil tiers, `sheets\<group>.png`, `baseverify` 0 failures.
2. A short report: per card anything notable (mask method, flip and why, ambiguous facing, known ghosts or
   compromises), and any shared fix you needed.
