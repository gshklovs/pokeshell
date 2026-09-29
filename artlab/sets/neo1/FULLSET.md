# Neo Genesis full set: brief for the batch agents

The ladder in this folder is one real card per printed rarity (`neocards.py`, `ORDER`). It sets the quality bar and
the look. Neo Genesis (`neo1`, 2000) has the same WotC scan layout and the same four printed rarities as Base Set,
so every recipe is the approved Base Set recipe (`artlab/sets/base`, copied unchanged into `neocards.py`). Now every
remaining Pokémon card is built. Each agent owns one group in `plan.json` and builds exactly those cards, the way the
ladder card of that rarity was built. The method is `docs/ART_METHOD.md`: read sections 1 and 6-14 before starting.
The Base Set batch modules (`artlab/sets/base/batch_*.py`) are worked examples of the same job on the same layout:
read the one for your rarity first.

## Environment

- Code: the worktree `C:\Users\grego\repos\pokeshell-neo`, folder `artlab\sets\neo1` (run the modules from there).
- Data: `C:\Users\grego\repos\pokeshell\style-lab\neo1` (scans `ref\neo1_<number>.png`, 600 x 825; `cards\<id>.json`,
  `cards\api\<id>.json`; `masks\`, `work\`, `art\`, `out\`, `anim\`, `sheets\`).
- Every command needs, in bash:
  `export ARTLAB_DATA='C:\Users\grego\repos\pokeshell\style-lab' POKESHELL_VENDOR='C:\Users\grego\repos\pokeshell\vendor' PYTHONIOENCODING=utf-8`
  and the Python `C:\Users\grego\repos\pokeshell\.venv\Scripts\python.exe` (Pillow, numpy, scipy, scikit-image, rembg).
- Never read API keys or `.env` files. No image-generation APIs. Never write to `C:\Users\grego\repos\pokeshell\dist`,
  `packs\pokemon\art`, `%LOCALAPPDATA%\pokeshell`, Windows Terminal settings, `$PROFILE` or the registry. Never
  spawn WT tabs. Do not import, commit or touch git: the lead does that. Other agents are building other sets
  (`lor`) and the other neo1 groups: never touch their folders or files.
- Coordinate grids: `..\..\tools\grid.py neo1 <number> [--crop x0 y0 x1 y1 --step 20]` writes `work\grid_<number>.png`.
  The grid lines are card px, but the label text is cramped: compute positions from the crop instead (with
  `--crop 60 90 540 430` the image is 900 px wide: card x = 60 + img_x / 1.875, card y = 90 + img_y / 1.875).
  Open it (and every review sheet) with the Read tool.
- Ready-made review images in `work\`: `rembg-holoA/holoB/rare/uncA/uncB/uncC.png` (the three rembg models side by
  side on each card's art window; the masks are cached as `work\rembg-<model>-<id>.png`) and
  `facing-holoA/holoB/rare/uncA/uncB/uncC.png` (the art window next to the unflipped vendor sprite).
  `zoom.py <name> <ids>` writes `work\zoom-<name>.png`: the art window at 1.5x with the saved mask bright and the rest
  dimmed green, the best way to check a mask (zoom px -> card px: x = 60 + zx / 1.5, y = 90 + zy / 1.5).

## Approved examples (the ladder) and what each group copies

| Group | Rarity | Ladder card | Recipe (neocards.py) | anim | frame |
|---|---|---|---|---|---|
| `commons` | Common | Totodile 81 | plain sprite, no background (`batch_commons.py`, done) | none | #9aa0aa |
| `uncommon_a` / `uncommon_b` (13 + 13) | Uncommon | Quilava 46 | `uncommon_card(cid, spr, crop=None, boxes=(STAGE,) or (), dx, dy, scene)`: `window_rgb(texture=False)` + evs `matte(scale=2)`, 12 colours, sat .84 / bright .88 | none | #8fc4a8 |
| `rare` (5) | Rare | Murkrow 24 | `rare_card(cid, spr, crop=None, boxes, tex_src, grow=8, texture=True, dx, dy, scene)`: WotC rares are NON-foil: `window_rgb` + `matte(scale=1)`, 16 colours, sat .95 / bright .95 | none | #6ea5ff |
| `holo` (17) | Rare Holo | Lugia 9 | `holo_card(cid, spr, crop=None, boxes, tex_src, grow=5, texture=True, dx, dy, seed, scene)`: the approved Rare Holo scene (grid, 12 colours, rim, 4 sparkles) with the WotC starlight foil (nebula + starbursts + faint cosmos swirl) | `wotc` | #56d0e0 |

The recipe functions set the rarity, finish, anim kind and frame colour themselves: call them, don't copy them.
`crop=None` uses `C.layout(cid, spr)` (sized to the art: the largest scale that fits the sprite + 1 px in the art
window, cropped to <= 52 sprite px wide around the real Pokémon). Pass an explicit `crop=(x0, y0, S, W, H)` only when
the default is wrong.

## Rules (decided by the user; not up for change)

- **Real cards only.** Build exactly the ids of your group in `plan.json`. The ladder ids are in `set.json` `ladder`
  (neo1-81, 46, 24 and 9 are already done: skip them); Trainers and Energy are `_skipped`.
- **The sprite** is the pokemon-colorscripts large sprite, pixel-exact and unchanged. Only a horizontal flip is
  allowed. `plan.json` gives the sprite name per card. Use `Sprite(name, flip)` (neolib).
- **Facing:** match the real card. Read which way the head / body points on the scan and flip if the vendor sprite
  faces the other way (nearly every vendor sprite faces LEFT; the `work\facing-*.png` sheets show each card next to
  its sprite, and `facing.py` makes more). Near-frontal poses: don't flip, and list them as ambiguous in your report.
- **The scene** is the card's own, with the real Pokémon masked out and filled. No text or logos in the art:
  `window_rgb` already replaces everything outside `NEO_WIN = (68, 99, 532, 420)` (the yellow border, name / HP,
  1st Edition stamp, length / weight bar); Stage 1 / 2 cards need `STAGE = (10, 18, 114, 138)` in `boxes` (the
  evolution badge hangs over the window's top-left corner) and `stage=True` in the mask.
- **Keep the painted and CGI backgrounds faithful**: pick a `tex_src` patch of the same material (sky, grass,
  starfield, CGI gradient) away from the Pokémon, so the fill carries the scene's texture.
- **Size:** each card is sized to its art (`C.layout`), at most 140 x 110 grid px, in practice <= 104 cols.
  `neoverify` checks the cap.
- **No ghosts:** check the fill for remnants of the real Pokémon (a tail tip, a flame, a glow halo, a shadow).
  Grow the mask (`grow=` in `HM.base_window`, or the recipe's `grow`) or add a hand polygon.
- **Text half, anim, verify** are done by the runner. Every foil card needs its 16-frame loop whose last frame is
  the static art (normal and shiny); `neoverify` must report 0 failures.

## How to build (without colliding with the other agents)

- Write ONE module, `batch_<group>.py`, in `artlab\sets\neo1`. Pattern:
  ```python
  import sys
  import neolib as P; from neolib import E, Sprite
  import neocards as C, neomasks as HM, neobatch as HB
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
- **Never edit shared files:** `neolib.py`, `neocards.py`, `neomasks.py`, `neobatch.py`, `neobuild.py`,
  `neoanim.py`, `neoverify.py`, `neosheet.py`, `facing.py`, `rembg_all.py`, `zoom.py`, `set.json`, `plan.json`, other agents'
  `batch_*.py`, anything in `artlab\lib`, `artlab\sets\evs|p30|hf|cz|base|brs|lor`, `tools\`. Don't run `neobuild.py`,
  `neosheet.py`, `neoverify.py`, `neoanim.py` without ids (they rewrite the ladder's `sizes.json`, `sheet.png`,
  `ladder.png`). If you need a shared fix, do it locally in your module and say so in your report.
- Masks, art, out, anim are per id, so agents don't collide. rembg caches: `work\rembg-<model>-<id>.png`.

## Group notes

- **All:** the WotC layout: art window `NEO_WIN`, the gold bevel frame round it, the Stage badge `STAGE` over its
  top-left corner on Stage 1 / 2 cards (`cards\<id>.json` `subtypes`: Stage 1 / Stage 2 need it; Basic and Baby
  don't). rembg struggles on these 2000 scans: expect to need hand hulls (`HM.poly(sh, pts)` in card px) and colour
  rules (`HM.hsv(cid)`), as the ladder's Quilava 46 / Murkrow 24 hulls and Lugia 9's colour rule did (`neomasks.py`).
  A Pokémon in two parts is `keep=2`. Some cards show MORE than one Pokémon. Prominent copies are painted out too,
  so no real-art Pokémon sits next to the sprite (Bellossom 3's second Bellossom, Ledian 39's two smaller Ledian
  behind): one sprite goes on the main one. Tiny ones far in the distance (Furret 35's, Miltank 41's herd) stay as
  scene. List every such case in your report.
- **Facing** (the lead's first read off the facing sheets; check it): flip Feraligatr 4 (snout right), Typhlosion 17
  (seen from behind, head turned right), Croconaw 32 (snout right), Quilava 47 (snout right), Xatu 52 (beak right).
  Ambiguous / near-frontal (keep unflipped, list as ambiguous): Azumarill 2, Bellossom 3, Jumpluff 7, Meganium 11,
  Pichu 12, Slowking 14, Cleffa 20, Elekid 22, Magby 23, Sneasel 25, Aipom 26, Clefairy 30, Croconaw 31, Electabuzz 33,
  Furret 35, Gloom 36, Granbull 37, Ledian 39, Miltank 41 (head turned right: judge it), Noctowl 42, Skiploom 49,
  Sunflora 50, Togepi 51. Everything else faces left like its sprite.
- **holo (17):** every holo art is the Pokémon over the WotC holo starfield (dark blue / red / green with star
  sparkles, sometimes light rays). rembg mostly takes the starfield: hand hulls or colour rules like Lugia 9.
  `tex_src` a starfield patch away from the Pokémon and the Stage badge. Two Feraligatr, two Meganium, two
  Typhlosion: each is its own card with its own pose. Big sprites (Steelix, Feraligatr, Kingdra): the default
  `C.layout` handles them (<= 104 cols). The anim is `wotc`, built by the runner.
- **rare (5):** Cleffa 20 (a room with yarn balls, Baby), Donphan 21 (the huge trunk is Donphan's), Elekid 22 (on a
  cloud with lightning: the bolts and clouds are scene), Magby 23 (fire background), Sneasel 25 (the pink psychic
  glow at the raised claw is scene). `tex_src` for the fill. Non-foil, no anim.
- **uncommon_a / uncommon_b (13 each):** painted and CGI scenes. Ghosts to watch: flames (Quilava 47, Magmar 40),
  shadows under the feet (copy `shadow()` from `artlab/sets/base/batch_uncommon.py`), Lanturn's glowing lures and
  Flaaffy's glowing tail orb (the Pokémon's own: mask them), Clefairy 30's swing (scene), Togepi 51 in a tree
  hollow. Non-foil, no anim. The two uncommon agents each write their own module (`batch_uncommon_a.py`,
  `batch_uncommon_b.py`) with GROUP = "uncommon_a" / "uncommon_b".

## Deliverables per agent

1. Every card in your group built: `art\<id>.json`, `out\` renders (art, art + text; normal and shiny), anims for
   foil tiers, `sheets\<group>.png`, `neoverify` 0 failures.
2. A short report: per card anything notable (mask method, flip and why, ambiguous facing, known ghosts or
   compromises), and any shared fix you needed.
