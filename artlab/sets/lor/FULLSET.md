# Lost Origin full set: brief for the batch agents

The method is `docs/ART_METHOD.md` (read sections 1, 6-8, 11, 14, 16 at least). The 16-card ladder in `lorcards.py`
(`LADDER`, one real card per printed rarity and finish) sets the quality bar and the look, as the evs, p30 and cz
ladders did. Every remaining Pokémon card of Lost Origin (`swsh11`) and its Trainer Gallery (`swsh11tg`) gets
built now. Each agent owns the group(s) named in its task and builds exactly those cards, the way the ladder card of
that finish was built. Every finish is an approved recipe (evs / cz / brs); nothing new is invented for this set.

- **Code:** `C:\Users\grego\repos\pokeshell-lor\artlab\sets\lor` (a git worktree, branch `set-lost-origin`). Run
  from that folder with `C:\Users\grego\repos\pokeshell\.venv\Scripts\python`.
- **Environment, every command:**
  `$env:ARTLAB_DATA='C:\Users\grego\repos\pokeshell\style-lab'; $env:POKESHELL_VENDOR='C:\Users\grego\repos\pokeshell\vendor'; $env:PYTHONIOENCODING='utf-8'`
  (bash: `export ARTLAB_DATA='C:\Users\grego\repos\pokeshell\style-lab' POKESHELL_VENDOR='C:\Users\grego\repos\pokeshell\vendor' PYTHONIOENCODING=utf-8`).
- **Data:** `C:\Users\grego\repos\pokeshell\style-lab\lor\`: `cards/<id>.json` (+ `cards/api/`), scans
  `ref/swsh11_<number>.png` for BOTH sets (Trainer Gallery: `swsh11_TG03.png`). Outputs go to `art/ out/ anim/ masks/
  sheets/ work/`, per id. Never refetch. Never read API keys or `.env` files. No image-generation APIs.
- **Grids:** `..\..\tools\grid.py lor <number>` (e.g. `grid.py lor TG03`, `--crop x0 y0 x1 y1 --step 25` to zoom)
  writes `work/grid_<number>.png` for reading card-px coordinates. Open images with the Read tool.
- **Vendor sprite facing:** the colorscripts sprites face LEFT (head on the viewer's left). A Pokémon whose head /
  body points right on the card gets `flip=True`.

## How a group module works

Write ONE file per group, `batch_<group>.py`, holding only a per-card table and the call to the shared runner:

```python
import lorbatch
GROUP = "holo"
TABLE = {
    "swsh11-3": dict(kind="holo", sprite="vileplume", flip=False,
                     mask=dict(model=None, add=[[(x, y), ...]])),     # hand hull, card px
    ...
}
if __name__ == "__main__":
    lorbatch.main(GROUP, TABLE)
```

Steps: `batch_<group>.py rembg` (3-model contact sheet, `work/<group>_rembg.png`), `masks` (writes masks +
`work/<group>_masks.png`: the Pokémon in colour, the rest green; LOOK at it), `quick` (renders + `work/<group>_pairs.png`,
real | ours), then `all` (masks, build, anim, verify, `sheets/<group>.png` = real | ours | ours + text half).
Iterate with `quick` until every card holds up next to its real card at the ladder's quality, then `all`.
Big PNGs: crop them (PIL) into parts before reading, a part of ~1700 x 1600 px reads well.

Row keys (all optional except `kind`, `sprite`; see `lorcards.DEFAULTS` and the builders):
- `kind`: `common uncommon rare holo v vmax vstar radiant fullart alt rainbow gallery gold` (table below)
- `sprite`, `flip` (face the way the real card does), `off=(A, B)` or `dx`/`dy` (sprite px nudges of the anchor)
- `text_y`: card-px y where the text starts (the first attack / ability row); everything below is painted out
  (for v / vmax / vstar / fullart / alt / rainbow / gallery / gold; the window kinds use the art window)
- `mask`: lormasks spec: `model` (`isnet-general-use`, `isnet-anime`, `u2net` or None), `win`, `hull` (AND polygon),
  `colour` (lambda h, s, v: bool map, OR-ed inside the hull), `cut`, `add` (rect or polygon), `cut_after`, `open`,
  `close`, `keep`, `fill`, or `fn(cid)` for a custom mask. Mask generously: the fill grows it again by `grow` (5).
- `boxes` (extra rects to paint out: logos, stray text), `polys` (extra polygons to paint out), `strike=True` (a
  Single / Rapid Strike badge under the HP; `STRIKE = (440, 84, 712, 170)`), `tex_src=(x0, y0, x1, y1)` (a patch of
  the same material for the texture fill; auto-picked when omitted), `texture=False` (smooth fill: use it when the
  Pokémon covers most of the art, to avoid ghosts), `grow`
- tone / look: `sat`, `bright`, `clarity`, `rim` / `rim_col`, `vig` / `vign` (alt), `star` (sparkle palette dict
  `{"L","l","j"}`), `frame` (text-half colour, alt / gallery), `scene` (a few words for the label), geometry
  overrides `x0 y0 S W H ch`; fullart also `glow` (RGB 0..1, the light behind the Pokémon), `glow_amt`, `tint`
  (the vignette's deep colour)
- `top`: which header boxes the alt / gallery / gold kinds paint out: `v`, `vmax`, `vstar`, `basic`, `stage`
  (auto from the card name and evolvesFrom). rainbow: `top="vstar"` (default) or anything else for the VMAX header.

## Finishes (the ladder)

| group | printed rarity | kind | ladder example | notes |
|---|---|---|---|---|
| commons_a / commons_b | Common | `common` | Pikachu 52 | plain sprite, no background, no anim. Flip is set.json `flip_commons`, NOT the table: report the list of ids that need a flip |
| uncommon_a / uncommon_b | Uncommon | `uncommon` | Gloom 2 | evs Shelgon: matte, sprite-scale, 12 colours, SWSH window |
| rare_a / rare_b | Rare | `rare` | Raichu 53 | evs Altaria: matte, grid scale, 16 colours |
| holo | Rare Holo | `holo` | Gengar 66 | evs Salamence: holo_scene in the window; anim holo |
| v | Rare Holo V | `v` | Giratina V 130 | evs Sylveon V: silver frame, sunpillar; anim sunpillar |
| v | Rare Holo VMAX | `vmax` | Kyurem VMAX 49 (Dynamax: plain sprite) | evs Vaporeon: gunmetal grooved frame, contour grooves |
| vstar | Rare Holo VSTAR | `vstar` | Giratina VSTAR 131 | cz Leafeon VSTAR 14: VMAX scene + platinum-gold frame + gold star-crest rays; anim vstar |
| radiant | Radiant Rare | `radiant` | Radiant Gardevoir 69 | cz Radiant Charizard 20: the SHINY sprite (automatic in the kind), silver log-spiral crosshatch, RAD_WIN window; anim radiant |
| ultra | Rare Ultra, full art | `fullart` | Giratina V 185 | evs Glaceon V 174: painting, glow + 12 rays, vignette, fingerprint etch; anim etch |
| ultra | Rare Ultra, alt-art painting | `alt` | Giratina V 186 | evs Umbreon VMAX 215 painting treatment; anim paint. In this set: 177, 180, 184, 186 (all others are plain full arts) |
| rainbow | Rare Rainbow | `rainbow` | Giratina VSTAR 201 | evs Leafeon VMAX 204: smooth fill, rainbow sprite 0.55, rainbow ground, etch, glitter; anim rainbow. Kyurem VMAX 197 has the VMAX header: `top="vmax"` |
| secret | Rare Secret (gold) | `gold` | Giratina VSTAR 212, Mew VMAX TG30 | evs Froslass gold remap, faceted gold; anim gold |
| tg | Trainer Gallery Rare Holo | `gallery` | Charizard TG03 | cz Lapras GG05: painting, soft emboss, linen weave, pastel sheen; anim gallery |
| tg_v | Rare Holo V / VMAX (Trainer Gallery) | `alt` | Pikachu V TG16, Pikachu VMAX TG17 | the Umbreon VMAX 215 painting treatment; tier stays V / VMAX |

Decide per card from the scan: if a Rare Ultra is a painted scene it is `alt`, a plain full art is `fullart`; say in
your report if you find a card that doesn't fit its group's finish (don't invent a treatment).

## Rules (the user's; not negotiable)
- **Real cards only.** Build exactly your group's ids from `plan.json` (the ladder ids are done). Never invent anything.
- **Sprite:** the pokemon-colorscripts sprite, pixel-exact. Only a horizontal flip; the gold remap only at Rare Secret
  gold, the rainbow re-tint only at Rare Rainbow (both built into the kinds). `plan.json` has a first-guess sprite
  name; check the FORM on the scan (Giratina Origin Forme on every Giratina card, Hisuian forms (-hisui), Galarian
  Stunfisk (-galar) vs Galarian Perrserker (the species `perrserker`), Hisuian Basculin = `basculin-white-striped`,
  Shellos / Gastrodon East (blue-green, `-east`) vs West (pink-brown, plain), Enamorus / Landorus Incarnate (plain)
  vs Therian, Hoopa Unbound, Rotom forms, Castform weather forms, Cramorant, Magearna, Gigantamax on G-Max cards
  (TG13 / TG15 / TG29 `-gmax`), Eternamax Eternatus TG22 (`eternatus-eternamax`), Dynamax VMAX = the plain sprite). Vendor forms are the folder names in
  `C:\Users\grego\repos\pokeshell\vendor\pokemon-colorscripts\colorscripts\large\regular\`. Report every sprite you
  changed from the plan.
- **Facing:** match the real card: flip when the vendor sprite faces the other way. Ambiguous (frontal) poses: keep
  unflipped and list them in the report. One pose, one choice across reprints of the same Pokémon.
- **Scene:** the card's own, with the real Pokémon painted out. No text, logos, HP, V / VMAX / VSTAR logos, stage
  icons, strike badges or rule boxes in the art. Other Pokémon / people in the painting stay as scenery. Look for
  **ghosts** (remnants of the real Pokémon) and fix them (grow the mask, colour rule, `texture=False`).
- **Size:** fit to the card; hard cap 140 x 110 grid px (the build asserts it), about 100 cols in practice.
- **Text half:** automatic (lorbuild). **Anims:** automatic, 16 frames, last frame == static (asserted).

## Don't collide
- Edit only your own `batch_<group>.py`. Never edit `lorcards.py`, `lorlib.py`, `lorbuild.py`, `loranim.py`,
  `lorverify.py`, `lormasks.py`, `lorsheet.py`, `lorbatch.py`, `ladder.py`, `set.json`, `plan.json`, or anything
  outside `artlab/sets/lor`. Need a shared fix? Do it locally in your module (e.g. a custom `mask=dict(fn=...)`, or a
  monkeypatch as cz `batch_secret.py` / brs `batch_tg.py` do for a vendor sprite quirk) and report it.
- Never run `lorbuild.py` / `lorverify.py` / `loranim.py` / `lormasks.py` / `ladder.py` directly (they rebuild the
  ladder).
- Never touch `C:\Users\grego\repos\pokeshell\dist`, `packs\`, `%LOCALAPPDATA%\pokeshell`, WT settings, `$PROFILE`,
  the registry; never open terminal tabs; never kill processes you didn't start. No git commands (the lead commits).
- Other agents work at the same time: another builds Neo Genesis in `style-lab/neo1` / `artlab/sets/neo*` (never touch
  those), and the other Lost Origin group agents own the other `batch_*.py` files. Never touch `artlab/sets/brs`, `cz`,
  `evs`, `hf`, `base`, `p30` or their data. Write only under `style-lab/lor` (your ids, your group's `work/<group>_*`
  and `sheets/<group>*` files) and your batch module(s).

## Deliverables
1. Every card of your group built and `all` passing (`0 failures`).
2. `sheets/<group>.png` (real | ours | ours + text half).
3. Your report: cards done; skipped with reason; every sprite / form change from the plan; the flip choice per
   card and which were ambiguous; the weakest 3 cards and why; any shared-code workaround.
