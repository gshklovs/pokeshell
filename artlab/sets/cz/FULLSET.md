# Crown Zenith full set: brief for the batch agents

The method is `docs/ART_METHOD.md` (read sections 1, 6-8, 11, 14, 16 at least). The 13-card ladder in `czcards.py`
(`LADDER`, one real card per printed rarity and finish) sets the quality bar and the look, as the evs and p30 ladders
did. Now every remaining Pokémon card of Crown Zenith (`swsh12pt5`) and its Galarian Gallery (`swsh12pt5gg`) gets
built. Each agent owns the group(s) named in its task and builds exactly those cards, the way the ladder card of
that finish was built.

- **Code:** `C:\Users\grego\repos\pokeshell-cz\artlab\sets\cz` (a git worktree, branch `set-crown-zenith`). Run from
  that folder with `C:\Users\grego\repos\pokeshell\.venv\Scripts\python`.
- **Environment, every command:**
  `$env:ARTLAB_DATA='C:\Users\grego\repos\pokeshell\style-lab'; $env:POKESHELL_VENDOR='C:\Users\grego\repos\pokeshell\vendor'; $env:PYTHONIOENCODING='utf-8'`
  (bash: `export ARTLAB_DATA='C:\Users\grego\repos\pokeshell\style-lab' POKESHELL_VENDOR='C:\Users\grego\repos\pokeshell\vendor' PYTHONIOENCODING=utf-8`).
- **Data:** `C:\Users\grego\repos\pokeshell\style-lab\cz\`: `cards/<id>.json` (+ `cards/api/`), scans
  `ref/swsh12pt5_<number>.png` for BOTH sets (gallery: `swsh12pt5_GG05.png`). Outputs go to `art/ out/ anim/ masks/
  sheets/ work/`, per id. Never refetch. Never read API keys or `.env` files. No image-generation APIs.
- **Grids:** `..\..\tools\grid.py cz <number>` (e.g. `grid.py cz GG05`, `--crop x0 y0 x1 y1 --step 25` to zoom) writes
  `work/grid_<number>.png` for reading card-px coordinates. Open images with the Read tool.

## How a group module works

Write ONE file, `batch_<group>.py`, holding only a per-card table and the call to the shared runner:

```python
import czbatch
GROUP = "holo"
TABLE = {
    "swsh12pt5-21": dict(kind="holo", sprite="entei", flip=False,
                         mask=dict(model=None, add=[[(x, y), ...]])),     # hand hull, card px
    ...
}
if __name__ == "__main__":
    czbatch.main(GROUP, TABLE)
```

Steps: `batch_<group>.py rembg` (3-model contact sheet, `work/<group>_rembg.png`), `masks` (writes masks +
`work/<group>_masks.png`: the Pokémon in colour, the rest green; LOOK at it), `quick` (renders + `work/<group>_pairs.png`,
real | ours), then `all` (masks, build, anim, verify, `sheets/<group>.png` = real | ours | ours + text half).
Iterate with `quick` until every card holds up next to its real card at the ladder's quality, then `all`.

Row keys (all optional except `kind`, `sprite`; see `czcards.DEFAULTS` and the builders):
- `kind`: `common uncommon rare holo v vmax vstar radiant alt gallery gold` (table below)
- `sprite`, `flip` (face the way the real card does), `off=(A, B)` or `dx`/`dy` (sprite px nudges of the anchor)
- `text_y`: card-px y where the text starts (the first attack / ability row); everything below is painted out
  (for v / vmax / vstar / alt / gallery / gold; the window kinds use the art window)
- `mask`: czmasks spec: `model` (`isnet-general-use`, `isnet-anime`, `u2net` or None), `win`, `hull` (AND polygon),
  `colour` (lambda h, s, v: bool map, OR-ed inside the hull), `cut`, `add` (rect or polygon), `open`, `close`, `keep`,
  or `fn(cid)` for a custom mask. Mask generously: the fill grows it again by `grow` (5).
- `boxes` (extra rects to paint out: logos, stray text), `polys` (extra polygons to paint out), `strike=True` (a
  Single / Rapid Strike badge under the HP), `tex_src=(x0, y0, x1, y1)` (a patch of the same material for the
  texture fill; auto-picked when omitted), `texture=False` (smooth fill: use it when the Pokémon covers most of the
  art, to avoid ghosts), `grow`
- tone / look: `sat`, `bright`, `clarity`, `rim` / `rim_col`, `vig` / `vign` (alt), `star` (sparkle palette),
  `frame` (text-half colour, alt / gallery), `scene` (a few words for the label), geometry overrides `x0 y0 S W H ch`
- `top`: which header boxes the alt / gallery / gold kinds paint out: `v`, `vmax`, `vstar`, `basic`, `stage`
  (auto from the card name and evolvesFrom)

## Finishes (the ladder)

| group | printed rarity | kind | ladder example | notes |
|---|---|---|---|---|
| commons | Common | `common` | Oddish 1 | plain sprite, no background, no anim. Flip is set.json `flip_commons`, NOT the table: report the list |
| uncommon | Uncommon | `uncommon` | Gloom 2 | evs Shelgon: matte, sprite-scale, 12 colours, SWSH window |
| rare | Rare | `rare` | Bellossom 3 | evs Altaria: matte, grid scale, 16 colours |
| holo | Rare Holo | `holo` | Kyogre 36 | evs Salamence: holo_scene in the window; anim holo |
| v | Rare Holo V | `v` | Leafeon V 13 | evs Sylveon V: silver frame, sunpillar; anim sunpillar |
| v | Rare Holo VMAX | `vmax` | Zeraora VMAX 54 | evs Vaporeon: gunmetal grooved frame, contour grooves |
| vstar | Rare Holo VSTAR | `vstar` | Leafeon VSTAR 14 | NEW: VMAX scene + platinum-gold frame + gold star-crest rays; anim vstar |
| radiant | Radiant Rare | `radiant` | Radiant Charizard 20 | NEW: silver log-spiral crosshatch burst, glints; anim radiant. Window `RAD_WIN` |
| secret (GG67-69) | Rare Secret | `gold` | Arceus VSTAR GG70 | evs Froslass gold remap. (Main-set Pikachu 160 is an alt-art painting: `alt`) |
| gg_v | Rare Holo V / VMAX (gallery) | `alt` | Entei V GG36 | the Umbreon VMAX 215 painting treatment; tier stays V / VMAX |
| gg_vstar | Rare Holo VSTAR (gallery) | `alt` | Leafeon VSTAR GG35 | same, tier VSTAR |
| gg_tg_a / gg_tg_b | Trainer Gallery Rare Holo | `gallery` | Lapras GG05 | NEW: painting, soft emboss, linen weave, pastel sheen; anim gallery |

Decide per card from the scan: if a gallery V / VSTAR is a plain full art rather than a painted scene, say so in
your report (don't invent a treatment).

## Rules (the user's; not negotiable)
- **Real cards only.** Build exactly your group's ids from `plan.json` (the ladder ids are done). Never invent anything.
- **Sprite:** the pokemon-colorscripts sprite, pixel-exact. Only a horizontal flip; the gold remap only at Rare Secret gold.
  `plan.json` has a first-guess sprite name; check the FORM on the scan (Midnight / Dusk Lycanroc, Crowned Zacian /
  Zamazenta, Origin Giratina, Oricorio style, Low Key Toxtricity, Deoxys forme, Resolute Keldeo, Gigantamax on
  G-Max cards, Hisuian / Galarian forms). Vendor forms are the folder names in
  `C:\Users\grego\repos\pokeshell\vendor\pokemon-colorscripts\colorscripts\large\regular\`. Report every sprite you
  changed from the plan.
- **Facing:** match the real card: flip when the vendor sprite faces the other way. Ambiguous (frontal) poses: keep
  unflipped and list them in the report. One pose, one choice across reprints of the same Pokémon.
- **Scene:** the card's own, with the real Pokémon painted out. No text, logos, HP, V / VMAX / VSTAR logos, stage
  icons, strike badges or rule boxes in the art. Look for **ghosts** (remnants of the real Pokémon) and fix them
  (grow the mask, colour rule, `texture=False`).
- **Size:** fit to the card; hard cap 140 x 110 grid px (the build asserts it), about 100 cols in practice.
- **Text half:** automatic (czbuild). **Anims:** automatic, 16 frames, last frame == static (asserted).

## Don't collide
- Edit only your own `batch_<group>.py`. Never edit `czcards.py`, `czlib.py`, `czbuild.py`, `czanim.py`,
  `czverify.py`, `czmasks.py`, `czsheet.py`, `czbatch.py`, `set.json`, `plan.json`, or anything outside `artlab/sets/cz`.
  Need a shared fix? Do it locally in your module (e.g. a custom `mask=dict(fn=...)`) and report it.
- Never run `czbuild.py` / `czverify.py` / `czanim.py` / `czmasks.py` directly (they rebuild the ladder).
- Never touch `C:\Users\grego\repos\pokeshell\dist`, `packs\`, `%LOCALAPPDATA%\pokeshell`, WT settings, `$PROFILE`,
  the registry; never open terminal tabs; never kill processes you didn't start. No git commands (the lead commits).
- Another agent builds Hidden Fates in `style-lab/hf`: never touch it.

## Deliverables
1. Every card of your group built and `all` passing (`0 failures`).
2. `sheets/<group>.png` (real | ours | ours + text half).
3. Your report: cards done; skipped with reason; every sprite / form change from the plan; the flip choice per
   card and which were ambiguous; the weakest 3 cards and why; any shared-code workaround.
