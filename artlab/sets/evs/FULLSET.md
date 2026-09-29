> **Historical brief**, exactly as the batch agents got it. Since then the code has moved to `artlab/sets/evs/` (the data stays in `style-lab/evs/`, see `artlab/artpaths.py`), so run the modules from there with `..\..\..\.venv\Scripts\python`. The method, including how to write the next set's brief, is `docs/ART_METHOD.md`.

# Evolving Skies full set: brief for the batch agents

The user approved the 11-card ladder in this folder. That's one real card per rarity, and it's the quality bar and the look. Now we make every remaining Pokémon card in the set. Each agent owns one rarity group in `plan.json`: build exactly those cards, the same way the approved card of that rarity was built.

Repo: C:\Users\grego\repos\pokeshell (Windows). Python: `C:\Users\grego\repos\pokeshell\.venv\Scripts\python` (Pillow, numpy, rembg). Never read API keys or .env files. No image-generation APIs.

## Already in place
- `cards/<id>.json` (card data, CARD_FORMAT) and `ref/swsh7_<number>.png` (the real scan) for every card, fetched up front by the coordinator. Do not refetch unless a file is missing. The API is flaky: retry with backoff.
- The approved pipeline: `evlib.py`, `evcards.py` (batch 1), `evcards2.py` (batch 2), `masks.py`, `anim.py`, `bottom.py`, `verify.py`, `sheet.py`. Read how the approved card of your rarity was made and follow it exactly:

| Rarity | Approved example |
|---|---|
| Common | Eevee 125 |
| Uncommon | Shelgon 108 |
| Rare | Altaria 106 |
| Rare Holo | Salamence 109 |
| Rare Holo V | Sylveon V 74 |
| Rare Holo VMAX | Vaporeon VMAX 30 |
| Rare Ultra | Glaceon V 174 |
| Rare Rainbow (true rainbow) | Leafeon VMAX 204 (rainbow blended at 0.55 on the sprite) |
| Rare Rainbow (alt art) | Umbreon VMAX 215 (no sprite recolour) |
| Rare Secret | Froslass 226 (gold) |

Some API "Rare Rainbow" cards are alternate-art secrets (textured paintings), not true rainbows. Check the scan: a pastel rainbow wash means rainbow treatment; a full painted scene means the alt-art treatment.

## Rules (all decided by the user)
- **Real cards only.** Build exactly the ids in your group; never invent anything.
- **Sprite:** the Pokémon is the pokemon-colorscripts large sprite (`vendor/pokemon-colorscripts/colorscripts/large/regular/<name>`, `shiny/<name>`), unchanged. Only a horizontal flip is allowed, to face the way the card does. The two exceptions: Rare Rainbow true rainbows blend the rainbow at 0.55 (≤0.7), and Rare Secret uses the gold remap. Always keep the outline and eyes. Galarian forms: look for `<name>-galar` sprites. VMAX cards use the regular sprite unless the card shows Gigantamax and a `-gmax` sprite exists.
- **Commons** never get a background: plain sprite. The pack builder handles commons automatically, so the commons group only verifies that data and sprite names resolve.
- **Background:** the card's own scene, with the real Pokémon masked out and filled (rembg / hand polygons, as in masks.py), at the resolution and treatment of the approved example for that rarity.
- **No text or logos** in the art.
- **Text half:** every card gets its text half via `bottom.py`.
- **Animation:** every foil tier gets its 16-frame animation via `anim.py`, and the last frame must equal the static art.
- **Size:** fit to the card (the user decided against a standard size).

## Don't collide with the other agents
- Write your code in your own module, `batch_<group>.py`, which imports evlib/evcards/anim/bottom. Do not edit the shared files: `evlib.py`, `evcards*.py`, `anim.py`, `bottom.py`, `verify.py`, `sheet.py`, `masks.py`, `ladder.png`, `sheet.png`. If you need a shared fix, implement it locally in your module and note it in your report.
- Your outputs are per card id (`art/`, `out/`, `anim/<id>/`), which don't collide.
- Masks: per id.

## Deliverables per agent
1. Every card in your group built: art JSON, static renders (art, and art + text; normal and shiny), animation for foil tiers.
2. Verification: all pass for your ids. Run `verify.py`'s checks on your ids; if it only knows the original picks, call its check functions on yours from your module.
3. `sheets/<group>.png`: one row per card with **real card | ours | ours + text half**. The user always judges side by side against the source card.
4. A report covering:
   - cards done, and cards skipped with the reason
   - the weakest 3 cards and why
   - any shared-code fixes you needed

Iterate with the Read tool on your renders until each card holds up next to its real card, at the approved example's quality.
