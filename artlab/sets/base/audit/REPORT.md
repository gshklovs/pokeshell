# Base Set (base1) audit

Every built card (69: the 4 ladder cards + 65 from the four group batches) was checked against its real scan on contact sheets (work/audit/sheets/, real | ours). A card is ok when its treatment is the ladder card of its printed rarity (FULLSET.md), the sprite is the right Pokemon and faces the way the card does, the scene is the card's own with all text, logos and the Stage badge painted out and no noticeable ghost, and the data, text half and animations are right. Frontal Pokemon (Diglett, Gastly, Koffing, Magnemite, Staryu, Starmie, Tangela, Voltorb, Pikachu 58 ...) have no facing to match and are ok unflipped; the near-frontal ones a reader could argue are flagged.

Counts: ok 46, fixed 1, flagged 22, skipped 33 (set list 102)

Automated checks, all clean: audit/verify_all.py (baseverify on all 69: sprite shape, outline and colours exact apart from the flip, no recolour at any Base Set rarity; card data verbatim from the API record, tier == API rarity; size <= 140 x 110 grid px; 16-frame loops whose final frame is the static art; 0 failures) and audit/audit_meta.py (finish = the rarity's recipe, sprite = plan.json's, commons flipped exactly as set.json flip_commons, text half with the rarity's frame colour, renders normal + shiny, 16-frame 12 fps anims normal + shiny on the 16 Rare Holos and none on the 53 non-foil cards, commons plain). The biggest card is 104 x 88 grid px (Mewtwo 10: 104 cols x 44 lines).

Coverage: 102 cards in the set list; 69 built (16 Rare Holo, 6 Rare, 20 Uncommon, 27 Common), 33 skipped: the 26 Trainers (70-95) and 7 Energy (96-102), no Pokemon.

| id | name | tier | status | reason |
|---|---|---|---|---|
| base1-1 | Alakazam | Rare Holo | flagged | WotC starlight holo in the art box, 16-frame wotc anim (Charizard 4); facing ambiguous (near-frontal, head a touch left): not flipped; a very faint trace of the purple halo is left, mostly under the sprite |
| base1-2 | Blastoise | Rare Holo | ok | WotC starlight holo in the art box, 16-frame wotc anim (Charizard 4); sprite, facing, scene, data OK |
| base1-3 | Chansey | Rare Holo | flagged | WotC starlight holo in the art box, 16-frame wotc anim (Charizard 4); facing ambiguous (frontal): not flipped |
| base1-4 | Charizard | Rare Holo | ok | approved ladder card; WotC starlight holo in the art box, 16-frame wotc anim (Charizard 4); sprite, facing, scene, data OK |
| base1-5 | Clefairy | Rare Holo | ok | WotC starlight holo in the art box, 16-frame wotc anim (Charizard 4); sprite, facing, scene, data OK |
| base1-6 | Gyarados | Rare Holo | ok | WotC starlight holo in the art box, 16-frame wotc anim (Charizard 4); sprite, facing, scene, data OK |
| base1-7 | Hitmonchan | Rare Holo | flagged | WotC starlight holo in the art box, 16-frame wotc anim (Charizard 4); facing ambiguous (frontal): not flipped |
| base1-8 | Machamp | Rare Holo | flagged | WotC starlight holo in the art box, 16-frame wotc anim (Charizard 4); facing ambiguous (frontal): not flipped; the rainbow ring behind him is scene, mostly under the sprite |
| base1-9 | Magneton | Rare Holo | flagged | WotC starlight holo in the art box, 16-frame wotc anim (Charizard 4); facing ambiguous (frontal): not flipped |
| base1-10 | Mewtwo | Rare Holo | ok | WotC starlight holo in the art box, 16-frame wotc anim (Charizard 4); sprite, facing, scene, data OK |
| base1-11 | Nidoking | Rare Holo | ok | WotC starlight holo in the art box, 16-frame wotc anim (Charizard 4); sprite, facing, scene, data OK |
| base1-12 | Ninetales | Rare Holo | ok | WotC starlight holo in the art box, 16-frame wotc anim (Charizard 4), flipped to the card's facing; sprite, facing, scene, data OK |
| base1-13 | Poliwrath | Rare Holo | flagged | WotC starlight holo in the art box, 16-frame wotc anim (Charizard 4); facing ambiguous (frontal): not flipped |
| base1-14 | Raichu | Rare Holo | ok | WotC starlight holo in the art box, 16-frame wotc anim (Charizard 4); sprite, facing, scene, data OK |
| base1-15 | Venusaur | Rare Holo | ok | WotC starlight holo in the art box, 16-frame wotc anim (Charizard 4); sprite, facing, scene, data OK |
| base1-16 | Zapdos | Rare Holo | flagged | WotC starlight holo in the art box, 16-frame wotc anim (Charizard 4); facing ambiguous (near-frontal, beak down-left): not flipped; the lightning rays are scene |
| base1-17 | Beedrill | Rare | flagged | grid-scale matte scene, 16 colours, non-foil (Dragonair 18); facing ambiguous (near-frontal, head a little left): not flipped |
| base1-18 | Dragonair | Rare | ok | approved ladder card; grid-scale matte scene, 16 colours, non-foil (Dragonair 18), flipped to the card's facing; sprite, facing, scene, data OK |
| base1-19 | Dugtrio | Rare | flagged | grid-scale matte scene, 16 colours, non-foil (Dragonair 18); facing ambiguous (three near-frontal heads): not flipped; the mound is scene |
| base1-20 | Electabuzz | Rare | flagged | grid-scale matte scene, 16 colours, non-foil (Dragonair 18); facing ambiguous (frontal): not flipped; the glow halo is painted out with him (smooth fill), the lightning bolts turn into soft glow streaks near his hands |
| base1-21 | Electrode | Rare | flagged | grid-scale matte scene, 16 colours, non-foil (Dragonair 18); facing ambiguous (frontal ball): not flipped; the default layout makes the sprite larger than the real ball, so the burst's white centre is mostly hidden |
| base1-22 | Pidgeotto | Rare | ok | grid-scale matte scene, 16 colours, non-foil (Dragonair 18); sprite, facing, scene, data OK |
| base1-23 | Arcanine | Uncommon | ok | sprite-scale matte scene, 12 colours (Charmeleon 24); sprite, facing, scene, data OK |
| base1-24 | Charmeleon | Uncommon | ok | approved ladder card; sprite-scale matte scene, 12 colours (Charmeleon 24); sprite, facing, scene, data OK |
| base1-25 | Dewgong | Uncommon | flagged | sprite-scale matte scene, 12 colours (Charmeleon 24); a small dark-blue patch of water left in the fill between the tail and the body (scene colour, not the Pokemon) |
| base1-26 | Dratini | Uncommon | flagged | sprite-scale matte scene, 12 colours (Charmeleon 24), flipped to the card's facing; facing a judgement call: the tail curls out to the left and the head turns right / to the viewer; flipped |
| base1-27 | Farfetch'd | Uncommon | ok | sprite-scale matte scene, 12 colours (Charmeleon 24), sprite farfetchd; sprite, facing, scene, data OK |
| base1-28 | Growlithe | Uncommon | ok | sprite-scale matte scene, 12 colours (Charmeleon 24); sprite, facing, scene, data OK |
| base1-29 | Haunter | Uncommon | ok | sprite-scale matte scene, 12 colours (Charmeleon 24); sprite, facing, scene, data OK |
| base1-30 | Ivysaur | Uncommon | ok | sprite-scale matte scene, 12 colours (Charmeleon 24); sprite, facing, scene, data OK |
| base1-31 | Jynx | Uncommon | flagged | sprite-scale matte scene, 12 colours (Charmeleon 24); facing ambiguous (near-frontal): not flipped |
| base1-32 | Kadabra | Uncommon | fixed | sprite-scale matte scene, 12 colours (Charmeleon 24); the Uncommon matte's light rim picked the red of the psychic orbs on the black scene: a red outline ran round the whole sprite; the rim is now a neutral grey (batch_fixes.py, audit/fixed.png) |
| base1-33 | Kakuna | Uncommon | flagged | sprite-scale matte scene, 12 colours (Charmeleon 24); facing ambiguous: not flipped; the glowing oval goes with Kakuna (else a halo ghost), so most of the white rays are lost |
| base1-34 | Machoke | Uncommon | flagged | sprite-scale matte scene, 12 colours (Charmeleon 24); facing ambiguous (frontal flex): not flipped |
| base1-35 | Magikarp | Uncommon | ok | sprite-scale matte scene, 12 colours (Charmeleon 24); sprite, facing, scene, data OK |
| base1-36 | Magmar | Uncommon | ok | sprite-scale matte scene, 12 colours (Charmeleon 24); sprite, facing, scene, data OK |
| base1-37 | Nidorino | Uncommon | ok | sprite-scale matte scene, 12 colours (Charmeleon 24); sprite, facing, scene, data OK |
| base1-38 | Poliwhirl | Uncommon | flagged | sprite-scale matte scene, 12 colours (Charmeleon 24); facing ambiguous (frontal): not flipped |
| base1-39 | Porygon | Uncommon | ok | sprite-scale matte scene, 12 colours (Charmeleon 24); sprite, facing, scene, data OK |
| base1-40 | Raticate | Uncommon | ok | sprite-scale matte scene, 12 colours (Charmeleon 24); sprite, facing, scene, data OK |
| base1-41 | Seel | Uncommon | flagged | sprite-scale matte scene, 12 colours (Charmeleon 24); facing ambiguous (head toward the viewer): not flipped |
| base1-42 | Wartortle | Uncommon | flagged | sprite-scale matte scene, 12 colours (Charmeleon 24); facing ambiguous (frontal): not flipped |
| base1-43 | Abra | Common | flagged | plain sprite, no background, no anim (Charmander 46); Common facing ambiguous: Abra sits frontal, head down; not flipped |
| base1-44 | Bulbasaur | Common | flagged | plain sprite, no background, no anim (Charmander 46); Common facing ambiguous: Bulbasaur lies near-frontal, head down; not flipped |
| base1-45 | Caterpie | Common | ok | plain sprite, no background, no anim (Charmander 46); sprite, facing, scene, data OK |
| base1-46 | Charmander | Common | ok | approved ladder card; plain sprite, no background, no anim (Charmander 46), flipped to the card's facing; sprite, facing, scene, data OK |
| base1-47 | Diglett | Common | ok | plain sprite, no background, no anim (Charmander 46); sprite, facing, scene, data OK |
| base1-48 | Doduo | Common | ok | plain sprite, no background, no anim (Charmander 46); sprite, facing, scene, data OK |
| base1-49 | Drowzee | Common | ok | plain sprite, no background, no anim (Charmander 46); sprite, facing, scene, data OK |
| base1-50 | Gastly | Common | ok | plain sprite, no background, no anim (Charmander 46); sprite, facing, scene, data OK |
| base1-51 | Koffing | Common | ok | plain sprite, no background, no anim (Charmander 46); sprite, facing, scene, data OK |
| base1-52 | Machop | Common | ok | plain sprite, no background, no anim (Charmander 46); sprite, facing, scene, data OK |
| base1-53 | Magnemite | Common | ok | plain sprite, no background, no anim (Charmander 46); sprite, facing, scene, data OK |
| base1-54 | Metapod | Common | ok | plain sprite, no background, no anim (Charmander 46); sprite, facing, scene, data OK |
| base1-55 | Nidoran ♂ | Common | ok | plain sprite, no background, no anim (Charmander 46), sprite nidoran-m; sprite, facing, scene, data OK |
| base1-56 | Onix | Common | ok | plain sprite, no background, no anim (Charmander 46); sprite, facing, scene, data OK |
| base1-57 | Pidgey | Common | ok | plain sprite, no background, no anim (Charmander 46); sprite, facing, scene, data OK |
| base1-58 | Pikachu | Common | ok | plain sprite, no background, no anim (Charmander 46); sprite, facing, scene, data OK |
| base1-59 | Poliwag | Common | flagged | plain sprite, no background, no anim (Charmander 46), flipped to the card's facing; Common facing: near-frontal Poliwag, flipped (set.json flip_commons) because the body turns so the tail sweeps out to the left |
| base1-60 | Ponyta | Common | ok | plain sprite, no background, no anim (Charmander 46); sprite, facing, scene, data OK |
| base1-61 | Rattata | Common | ok | plain sprite, no background, no anim (Charmander 46); sprite, facing, scene, data OK |
| base1-62 | Sandshrew | Common | ok | plain sprite, no background, no anim (Charmander 46); sprite, facing, scene, data OK |
| base1-63 | Squirtle | Common | ok | plain sprite, no background, no anim (Charmander 46); sprite, facing, scene, data OK |
| base1-64 | Starmie | Common | ok | plain sprite, no background, no anim (Charmander 46); sprite, facing, scene, data OK |
| base1-65 | Staryu | Common | ok | plain sprite, no background, no anim (Charmander 46); sprite, facing, scene, data OK |
| base1-66 | Tangela | Common | ok | plain sprite, no background, no anim (Charmander 46); sprite, facing, scene, data OK |
| base1-67 | Voltorb | Common | ok | plain sprite, no background, no anim (Charmander 46); sprite, facing, scene, data OK |
| base1-68 | Vulpix | Common | ok | plain sprite, no background, no anim (Charmander 46); sprite, facing, scene, data OK |
| base1-69 | Weedle | Common | ok | plain sprite, no background, no anim (Charmander 46); sprite, facing, scene, data OK |
| base1-70 | Clefairy Doll | Rare | skipped | Trainer (no Pokemon) |
| base1-71 | Computer Search | Rare | skipped | Trainer (no Pokemon) |
| base1-72 | Devolution Spray | Rare | skipped | Trainer (no Pokemon) |
| base1-73 | Impostor Professor Oak | Rare | skipped | Trainer (no Pokemon) |
| base1-74 | Item Finder | Rare | skipped | Trainer (no Pokemon) |
| base1-75 | Lass | Rare | skipped | Trainer (no Pokemon) |
| base1-76 | Pokémon Breeder | Rare | skipped | Trainer (no Pokemon) |
| base1-77 | Pokémon Trader | Rare | skipped | Trainer (no Pokemon) |
| base1-78 | Scoop Up | Rare | skipped | Trainer (no Pokemon) |
| base1-79 | Super Energy Removal | Rare | skipped | Trainer (no Pokemon) |
| base1-80 | Defender | Uncommon | skipped | Trainer (no Pokemon) |
| base1-81 | Energy Retrieval | Uncommon | skipped | Trainer (no Pokemon) |
| base1-82 | Full Heal | Uncommon | skipped | Trainer (no Pokemon) |
| base1-83 | Maintenance | Uncommon | skipped | Trainer (no Pokemon) |
| base1-84 | PlusPower | Uncommon | skipped | Trainer (no Pokemon) |
| base1-85 | Pokémon Center | Uncommon | skipped | Trainer (no Pokemon) |
| base1-86 | Pokémon Flute | Uncommon | skipped | Trainer (no Pokemon) |
| base1-87 | Pokédex | Uncommon | skipped | Trainer (no Pokemon) |
| base1-88 | Professor Oak | Uncommon | skipped | Trainer (no Pokemon) |
| base1-89 | Revive | Uncommon | skipped | Trainer (no Pokemon) |
| base1-90 | Super Potion | Uncommon | skipped | Trainer (no Pokemon) |
| base1-91 | Bill | Common | skipped | Trainer (no Pokemon) |
| base1-92 | Energy Removal | Common | skipped | Trainer (no Pokemon) |
| base1-93 | Gust of Wind | Common | skipped | Trainer (no Pokemon) |
| base1-94 | Potion | Common | skipped | Trainer (no Pokemon) |
| base1-95 | Switch | Common | skipped | Trainer (no Pokemon) |
| base1-96 | Double Colorless Energy | Uncommon | skipped | Energy (no Pokemon) |
| base1-97 | Fighting Energy |  | skipped | Energy (no Pokemon) |
| base1-98 | Fire Energy |  | skipped | Energy (no Pokemon) |
| base1-99 | Grass Energy |  | skipped | Energy (no Pokemon) |
| base1-100 | Lightning Energy |  | skipped | Energy (no Pokemon) |
| base1-101 | Psychic Energy |  | skipped | Energy (no Pokemon) |
| base1-102 | Water Energy |  | skipped | Energy (no Pokemon) |
