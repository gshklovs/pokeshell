# Hidden Fates (sm115) + Shiny Vault (sma) audit

Every built card (133: the 8 ladder cards + 125 from the ten group batches) was checked against its real scan on contact sheets (work/audit/sheets/, real | ours). A card is ok when its treatment is the ladder card's of its printed rarity (FULLSET.md), the sprite is the right Pokemon and form (SHINY sprite on every Shiny Vault card) and faces the way the card does, the scene is the card's own with all text and logos painted out and no noticeable ghost, and the data, text half and animations are right. Near-frontal Pokemon (Voltorb, Staryu, Starmie, Electrode 22, the Tapus, Nihilego, Xurkitree ...) have no facing to match and are ok unflipped.

Counts: ok 111, fixed 2, flagged 20, skipped 30 (set list 163)

Automated checks, all clean: audit/verify_all.py (hfverify on all 133: sprite shape, outline and colours exact apart from the flip; the SHINY vendor colours on both rolls of every Rare Shiny / Rare Shiny GX card; the only recolour is the gold remap on the 4 Rare Secret Tapus; card data verbatim from the API record, tier == API rarity; size <= 140 x 110; 0 failures, 877 checks) and audit/audit_meta.py (finish = the rarity's recipe, sprite = plan.json's, text half with the rarity's frame colour, renders normal + shiny, 16-frame 12 fps anims normal + shiny on the 95 foil cards (Rare Holo, Rare Holo GX, Rare Shiny, Rare Shiny GX, Rare Secret) and none on the 38 non-foil ones, commons plain). Forms: vulpix-alola, ninetales-alola, lycanroc-midnight (SV66), lycanroc-dusk (SV67), zygarde-complete (SV65, read off the scan).

Coverage: 163 cards in the set list (sm115 69 + sma 94); 133 built, 30 skipped: 27 Trainers and the three Moltres & Zapdos & Articuno-GX TAG TEAM cards (44, 66, 69: three Pokemon, no single colorscripts sprite; three ~45x40 sprites cannot fit the 70x55 sprite-px cap without covering each other).

| id | name | tier | status | reason |
|---|---|---|---|---|
| sm115-1 | Caterpie | Common | flagged | plain sprite, no background, no anim (Charmander 7); Common facing: the card's Caterpie faces left, the plain sprite right. Listed in set.json flip_commons; the importer builds it unflipped until the per-set flip_commons change (Crown Zenith branch) lands |
| sm115-2 | Metapod | Uncommon | ok | sprite-scale matte scene, 12 colours (Charmeleon 8), flipped to the card's facing; sprite, facing, scene, data OK |
| sm115-3 | Butterfree | Rare | ok | grid-scale matte scene, 16 colours, non-foil (Mew 32); sprite, facing, scene, data OK |
| sm115-4 | Paras | Common | ok | plain sprite, no background, no anim (Charmander 7); sprite, facing, scene, data OK |
| sm115-5 | Scyther | Uncommon | ok | sprite-scale matte scene, 12 colours (Charmeleon 8); sprite, facing, scene, data OK |
| sm115-6 | Pinsir-GX | Rare Holo GX | ok | silver frame + GX web foil, 16-frame gxweb anim (Charizard-GX 9), sprite pinsir, flipped to the card's facing; sprite, facing, scene, data OK |
| sm115-7 | Charmander | Common | ok | approved ladder card; plain sprite, no background, no anim (Charmander 7); sprite, facing, scene, data OK |
| sm115-8 | Charmeleon | Uncommon | fixed | approved ladder card; sprite-scale matte scene, 12 colours (Charmeleon 8), flipped to the card's facing; the stage icon ran past ICON and left a tan ghost top-left: paint-out boxes grown (batch_fixes.py, audit/fixed.png) |
| sm115-9 | Charizard-GX | Rare Holo GX | ok | approved ladder card; silver frame + GX web foil, 16-frame gxweb anim (Charizard-GX 9), sprite charizard; sprite, facing, scene, data OK |
| sm115-10 | Magmar | Uncommon | ok | sprite-scale matte scene, 12 colours (Charmeleon 8); sprite, facing, scene, data OK |
| sm115-11 | Psyduck | Common | ok | plain sprite, no background, no anim (Charmander 7); sprite, facing, scene, data OK |
| sm115-12 | Slowpoke | Common | flagged | plain sprite, no background, no anim (Charmander 7); Common facing: the card's Slowpoke faces right, the plain sprite left. Listed in set.json flip_commons (as sm115-1) |
| sm115-13 | Staryu | Common | ok | plain sprite, no background, no anim (Charmander 7); sprite, facing, scene, data OK |
| sm115-14 | Starmie-GX | Rare Holo GX | ok | silver frame + GX web foil, 16-frame gxweb anim (Charizard-GX 9), sprite starmie; sprite, facing, scene, data OK |
| sm115-15 | Magikarp | Common | ok | plain sprite, no background, no anim (Charmander 7); sprite, facing, scene, data OK |
| sm115-16 | Gyarados-GX | Rare Holo GX | ok | silver frame + GX web foil, 16-frame gxweb anim (Charizard-GX 9), sprite gyarados; sprite, facing, scene, data OK |
| sm115-17 | Lapras | Rare | flagged | grid-scale matte scene, 16 colours, non-foil (Mew 32), flipped to the card's facing; facing arguable: flipped because the body swims right, but the head bends down toward the ball |
| sm115-18 | Vaporeon | Rare Holo | fixed | approved ladder card; holo bands + starlight in the art box, 16-frame holo anim (Vaporeon 18); the Evolves-from bar's lower edge left a dark strip along the top: paint-out box grown (batch_fixes.py, audit/fixed.png) |
| sm115-19 | Pikachu | Common | ok | plain sprite, no background, no anim (Charmander 7); sprite, facing, scene, data OK |
| sm115-20 | Raichu-GX | Rare Holo GX | ok | silver frame + GX web foil, 16-frame gxweb anim (Charizard-GX 9), sprite raichu, flipped to the card's facing; sprite, facing, scene, data OK |
| sm115-21 | Voltorb | Common | ok | plain sprite, no background, no anim (Charmander 7); sprite, facing, scene, data OK |
| sm115-22 | Electrode | Rare | ok | grid-scale matte scene, 16 colours, non-foil (Mew 32); sprite, facing, scene, data OK |
| sm115-23 | Jolteon | Rare | ok | grid-scale matte scene, 16 colours, non-foil (Mew 32); sprite, facing, scene, data OK |
| sm115-24 | Zapdos | Rare Holo | ok | holo bands + starlight in the art box, 16-frame holo anim (Vaporeon 18); sprite, facing, scene, data OK |
| sm115-25 | Ekans | Common | ok | plain sprite, no background, no anim (Charmander 7); sprite, facing, scene, data OK |
| sm115-26 | Ekans | Common | flagged | plain sprite, no background, no anim (Charmander 7); Common facing ambiguous: head turned up and back, mouth open; not flipped |
| sm115-27 | Arbok | Rare | ok | grid-scale matte scene, 16 colours, non-foil (Mew 32); sprite, facing, scene, data OK |
| sm115-28 | Koffing | Common | ok | plain sprite, no background, no anim (Charmander 7); sprite, facing, scene, data OK |
| sm115-29 | Weezing | Rare | ok | grid-scale matte scene, 16 colours, non-foil (Mew 32); sprite, facing, scene, data OK |
| sm115-30 | Jynx | Uncommon | ok | sprite-scale matte scene, 12 colours (Charmeleon 8); sprite, facing, scene, data OK |
| sm115-31 | Mewtwo-GX | Rare Holo GX | ok | silver frame + GX web foil, 16-frame gxweb anim (Charizard-GX 9), sprite mewtwo, flipped to the card's facing; sprite, facing, scene, data OK |
| sm115-32 | Mew | Rare | ok | approved ladder card; grid-scale matte scene, 16 colours, non-foil (Mew 32), flipped to the card's facing; sprite, facing, scene, data OK |
| sm115-33 | Geodude | Common | ok | plain sprite, no background, no anim (Charmander 7); sprite, facing, scene, data OK |
| sm115-34 | Graveler | Uncommon | ok | sprite-scale matte scene, 12 colours (Charmeleon 8); sprite, facing, scene, data OK |
| sm115-35 | Golem | Rare | ok | grid-scale matte scene, 16 colours, non-foil (Mew 32); sprite, facing, scene, data OK |
| sm115-36 | Onix-GX | Rare Holo GX | flagged | silver frame + GX web foil, 16-frame gxweb anim (Charizard-GX 9), sprite onix; faint warm-orange streaks in the fill from the scan's red stadium seats (scene, not a ghost of Onix) |
| sm115-37 | Cubone | Common | ok | plain sprite, no background, no anim (Charmander 7); sprite, facing, scene, data OK |
| sm115-38 | Clefairy | Common | ok | plain sprite, no background, no anim (Charmander 7); sprite, facing, scene, data OK |
| sm115-39 | Clefairy | Common | ok | plain sprite, no background, no anim (Charmander 7); sprite, facing, scene, data OK |
| sm115-40 | Clefable | Rare | ok | grid-scale matte scene, 16 colours, non-foil (Mew 32); sprite, facing, scene, data OK |
| sm115-41 | Jigglypuff | Common | ok | plain sprite, no background, no anim (Charmander 7); sprite, facing, scene, data OK |
| sm115-42 | Wigglytuff-GX | Rare Holo GX | flagged | silver frame + GX web foil, 16-frame gxweb anim (Charizard-GX 9), sprite wigglytuff, flipped to the card's facing; near-frontal; flipped because the head is turned slightly right |
| sm115-43 | Mr. Mime | Rare | ok | grid-scale matte scene, 16 colours, non-foil (Mew 32), sprite mr-mime; sprite, facing, scene, data OK |
| sm115-44 | Moltres & Zapdos & Articuno-GX | Rare Holo GX | skipped | no colorscripts sprite (moltres-zapdos-articuno-gx) |
| sm115-45 | Farfetch'd | Uncommon | ok | sprite-scale matte scene, 12 colours (Charmeleon 8), sprite farfetchd; sprite, facing, scene, data OK |
| sm115-46 | Chansey | Uncommon | ok | sprite-scale matte scene, 12 colours (Charmeleon 8); sprite, facing, scene, data OK |
| sm115-47 | Kangaskhan | Rare | flagged | grid-scale matte scene, 16 colours, non-foil (Mew 32), flipped to the card's facing; Kangaskhan covers most of the window: the fill is a soft orange blur of the explosion (the weakest scene of the set) |
| sm115-48 | Eevee | Rare Holo | ok | holo bands + starlight in the art box, 16-frame holo anim (Vaporeon 18), flipped to the card's facing; sprite, facing, scene, data OK |
| sm115-49 | Eevee | Common | ok | plain sprite, no background, no anim (Charmander 7); sprite, facing, scene, data OK |
| sm115-50 | Snorlax | Rare | ok | grid-scale matte scene, 16 colours, non-foil (Mew 32); sprite, facing, scene, data OK |
| sm115-51 | Bill's Analysis | Rare | skipped | Trainer (no Pokemon) |
| sm115-52 | Blaine's Last Stand | Rare | skipped | Trainer (no Pokemon) |
| sm115-53 | Brock's Grit | Uncommon | skipped | Trainer (no Pokemon) |
| sm115-54 | Brock's Pewter City Gym | Uncommon | skipped | Trainer (no Pokemon) |
| sm115-55 | Brock's Training | Rare Holo | skipped | Trainer (no Pokemon) |
| sm115-56 | Erika's Hospitality | Rare | skipped | Trainer (no Pokemon) |
| sm115-57 | Giovanni's Exile | Uncommon | skipped | Trainer (no Pokemon) |
| sm115-58 | Jessie & James | Rare Holo | skipped | Trainer (no Pokemon) |
| sm115-59 | Koga's Trap | Uncommon | skipped | Trainer (no Pokemon) |
| sm115-60 | Lt. Surge's Strategy | Uncommon | skipped | Trainer (no Pokemon) |
| sm115-61 | Misty's Cerulean City Gym | Uncommon | skipped | Trainer (no Pokemon) |
| sm115-62 | Misty's Determination | Uncommon | skipped | Trainer (no Pokemon) |
| sm115-63 | Misty's Water Command | Rare Holo | skipped | Trainer (no Pokemon) |
| sm115-64 | Pokémon Center Lady | Uncommon | skipped | Trainer (no Pokemon) |
| sm115-65 | Sabrina's Suggestion | Uncommon | skipped | Trainer (no Pokemon) |
| sm115-66 | Moltres & Zapdos & Articuno-GX | Rare Ultra | skipped | no colorscripts sprite (moltres-zapdos-articuno-gx) |
| sm115-67 | Giovanni's Exile | Rare Ultra | skipped | Trainer (no Pokemon) |
| sm115-68 | Jessie & James | Rare Ultra | skipped | Trainer (no Pokemon) |
| sm115-69 | Moltres & Zapdos & Articuno-GX | Rare Rainbow | skipped | no colorscripts sprite (moltres-zapdos-articuno-gx) |
| sma-SV1 | Scyther | Rare Shiny | ok | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6), flipped to the card's facing; sprite, facing, scene, data OK |
| sma-SV2 | Rowlet | Rare Shiny | flagged | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6); every segmenter took the window: hand hull; a broken printed-star fragment near the top |
| sma-SV3 | Dartrix | Rare Shiny | ok | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6), flipped to the card's facing; sprite, facing, scene, data OK |
| sma-SV4 | Wimpod | Rare Shiny | ok | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6), flipped to the card's facing; sprite, facing, scene, data OK |
| sma-SV5 | Pheromosa | Rare Shiny | flagged | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6); hand hull; Pheromosa is huge and faint, about 60% of the window is fill; the sprite is frontal, the card faces left |
| sma-SV6 | Charmander | Rare Shiny | ok | approved ladder card; SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6), flipped to the card's facing; sprite, facing, scene, data OK |
| sma-SV7 | Charmeleon | Rare Shiny | ok | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6); sprite, facing, scene, data OK |
| sma-SV8 | Alolan Vulpix | Rare Shiny | ok | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6), sprite vulpix-alola; sprite, facing, scene, data OK |
| sma-SV9 | Wooper | Rare Shiny | ok | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6), flipped to the card's facing; sprite, facing, scene, data OK |
| sma-SV10 | Quagsire | Rare Shiny | ok | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6), flipped to the card's facing; sprite, facing, scene, data OK |
| sma-SV11 | Froakie | Rare Shiny | ok | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6); sprite, facing, scene, data OK |
| sma-SV12 | Frogadier | Rare Shiny | ok | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6); sprite, facing, scene, data OK |
| sma-SV13 | Voltorb | Rare Shiny | ok | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6); sprite, facing, scene, data OK |
| sma-SV14 | Xurkitree | Rare Shiny | ok | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6); sprite, facing, scene, data OK |
| sma-SV15 | Seviper | Rare Shiny | ok | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6); sprite, facing, scene, data OK |
| sma-SV16 | Shuppet | Rare Shiny | ok | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6); sprite, facing, scene, data OK |
| sma-SV17 | Inkay | Rare Shiny | ok | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6); sprite, facing, scene, data OK |
| sma-SV18 | Malamar | Rare Shiny | ok | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6); sprite, facing, scene, data OK |
| sma-SV19 | Poipole | Rare Shiny | flagged | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6), flipped to the card's facing; flipped so the tail curls left as on the card; the body is near-frontal |
| sma-SV20 | Sudowoodo | Rare Shiny | ok | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6); sprite, facing, scene, data OK |
| sma-SV21 | Riolu | Rare Shiny | ok | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6); sprite, facing, scene, data OK |
| sma-SV22 | Lucario | Rare Shiny | ok | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6), flipped to the card's facing; sprite, facing, scene, data OK |
| sma-SV23 | Rockruff | Rare Shiny | ok | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6), flipped to the card's facing; sprite, facing, scene, data OK |
| sma-SV24 | Buzzwole | Rare Shiny | flagged | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6); printed stars half-hidden behind the real Buzzwole come out as scribbly silver fragments |
| sma-SV25 | Zorua | Rare Shiny | ok | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6); sprite, facing, scene, data OK |
| sma-SV26 | Guzzlord | Rare Shiny | flagged | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6); printed stars half-hidden behind the real Guzzlord come out as scribbly silver fragments |
| sma-SV27 | Magnemite | Rare Shiny | ok | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6); sprite, facing, scene, data OK |
| sma-SV28 | Magneton | Rare Shiny | ok | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6); sprite, facing, scene, data OK |
| sma-SV29 | Magnezone | Rare Shiny | ok | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6); sprite, facing, scene, data OK |
| sma-SV30 | Beldum | Rare Shiny | ok | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6), flipped to the card's facing; sprite, facing, scene, data OK |
| sma-SV31 | Metang | Rare Shiny | ok | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6); sprite, facing, scene, data OK |
| sma-SV32 | Celesteela | Rare Shiny | ok | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6); sprite, facing, scene, data OK |
| sma-SV33 | Kartana | Rare Shiny | ok | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6); sprite, facing, scene, data OK |
| sma-SV34 | Ralts | Rare Shiny | flagged | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6); facing ambiguous: the card's Ralts looks right, the near-frontal sprite is not flipped |
| sma-SV35 | Kirlia | Rare Shiny | ok | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6); sprite, facing, scene, data OK |
| sma-SV36 | Diancie | Rare Shiny | flagged | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6); facing ambiguous: the card's Diancie faces left, the near-frontal sprite is not flipped |
| sma-SV37 | Altaria | Rare Shiny | ok | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6); sprite, facing, scene, data OK |
| sma-SV38 | Gible | Rare Shiny | ok | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6); sprite, facing, scene, data OK |
| sma-SV39 | Gabite | Rare Shiny | ok | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6), flipped to the card's facing; sprite, facing, scene, data OK |
| sma-SV40 | Garchomp | Rare Shiny | ok | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6); sprite, facing, scene, data OK |
| sma-SV41 | Eevee | Rare Shiny | ok | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6); sprite, facing, scene, data OK |
| sma-SV42 | Swablu | Rare Shiny | ok | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6), flipped to the card's facing; sprite, facing, scene, data OK |
| sma-SV43 | Noibat | Rare Shiny | ok | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6); sprite, facing, scene, data OK |
| sma-SV44 | Oranguru | Rare Shiny | ok | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6); sprite, facing, scene, data OK |
| sma-SV45 | Type: Null | Rare Shiny | ok | SHINY sprite, vault foil + embossed stars + glitter, 16-frame vault anim (Charmander SV6), sprite type-null, flipped to the card's facing; sprite, facing, scene, data OK |
| sma-SV46 | Leafeon-GX | Rare Shiny GX | ok | SHINY sprite, etched vault foil + flares + silver frame, 16-frame vaultgx anim (Charizard-GX SV49), sprite leafeon; sprite, facing, scene, data OK |
| sma-SV47 | Decidueye-GX | Rare Shiny GX | ok | SHINY sprite, etched vault foil + flares + silver frame, 16-frame vaultgx anim (Charizard-GX SV49), sprite decidueye; sprite, facing, scene, data OK |
| sma-SV48 | Golisopod-GX | Rare Shiny GX | ok | SHINY sprite, etched vault foil + flares + silver frame, 16-frame vaultgx anim (Charizard-GX SV49), sprite golisopod; sprite, facing, scene, data OK |
| sma-SV49 | Charizard-GX | Rare Shiny GX | ok | approved ladder card; SHINY sprite, etched vault foil + flares + silver frame, 16-frame vaultgx anim (Charizard-GX SV49), sprite charizard; sprite, facing, scene, data OK |
| sma-SV50 | Ho-Oh-GX | Rare Shiny GX | ok | SHINY sprite, etched vault foil + flares + silver frame, 16-frame vaultgx anim (Charizard-GX SV49), sprite ho-oh, flipped to the card's facing; sprite, facing, scene, data OK |
| sma-SV51 | Reshiram-GX | Rare Shiny GX | ok | SHINY sprite, etched vault foil + flares + silver frame, 16-frame vaultgx anim (Charizard-GX SV49), sprite reshiram; sprite, facing, scene, data OK |
| sma-SV52 | Turtonator-GX | Rare Shiny GX | ok | SHINY sprite, etched vault foil + flares + silver frame, 16-frame vaultgx anim (Charizard-GX SV49), sprite turtonator; sprite, facing, scene, data OK |
| sma-SV53 | Alolan Ninetales-GX | Rare Shiny GX | flagged | SHINY sprite, etched vault foil + flares + silver frame, 16-frame vaultgx anim (Charizard-GX SV49), sprite ninetales-alola, flipped to the card's facing; facing ambiguous: head on the left but the snout points right; flipped |
| sma-SV54 | Articuno-GX | Rare Shiny GX | ok | SHINY sprite, etched vault foil + flares + silver frame, 16-frame vaultgx anim (Charizard-GX SV49), sprite articuno; sprite, facing, scene, data OK |
| sma-SV55 | Glaceon-GX | Rare Shiny GX | ok | SHINY sprite, etched vault foil + flares + silver frame, 16-frame vaultgx anim (Charizard-GX SV49), sprite glaceon, flipped to the card's facing; sprite, facing, scene, data OK |
| sma-SV56 | Greninja-GX | Rare Shiny GX | flagged | SHINY sprite, etched vault foil + flares + silver frame, 16-frame vaultgx anim (Charizard-GX SV49), sprite greninja; facing ambiguous: near-frontal Greninja, looks left; not flipped |
| sma-SV57 | Electrode-GX | Rare Shiny GX | flagged | SHINY sprite, etched vault foil + flares + silver frame, 16-frame vaultgx anim (Charizard-GX SV49), sprite electrode, flipped to the card's facing; a front-facing ball; flipped because the face sits right of centre on the card |
| sma-SV58 | Xurkitree-GX | Rare Shiny GX | ok | SHINY sprite, etched vault foil + flares + silver frame, 16-frame vaultgx anim (Charizard-GX SV49), sprite xurkitree; sprite, facing, scene, data OK |
| sma-SV59 | Mewtwo-GX | Rare Shiny GX | ok | SHINY sprite, etched vault foil + flares + silver frame, 16-frame vaultgx anim (Charizard-GX SV49), sprite mewtwo, flipped to the card's facing; sprite, facing, scene, data OK |
| sma-SV60 | Espeon-GX | Rare Shiny GX | ok | SHINY sprite, etched vault foil + flares + silver frame, 16-frame vaultgx anim (Charizard-GX SV49), sprite espeon, flipped to the card's facing; sprite, facing, scene, data OK |
| sma-SV61 | Banette-GX | Rare Shiny GX | ok | SHINY sprite, etched vault foil + flares + silver frame, 16-frame vaultgx anim (Charizard-GX SV49), sprite banette; sprite, facing, scene, data OK |
| sma-SV62 | Nihilego-GX | Rare Shiny GX | ok | SHINY sprite, etched vault foil + flares + silver frame, 16-frame vaultgx anim (Charizard-GX SV49), sprite nihilego; sprite, facing, scene, data OK |
| sma-SV63 | Naganadel-GX | Rare Shiny GX | ok | SHINY sprite, etched vault foil + flares + silver frame, 16-frame vaultgx anim (Charizard-GX SV49), sprite naganadel; sprite, facing, scene, data OK |
| sma-SV64 | Lucario-GX | Rare Shiny GX | ok | SHINY sprite, etched vault foil + flares + silver frame, 16-frame vaultgx anim (Charizard-GX SV49), sprite lucario; sprite, facing, scene, data OK |
| sma-SV65 | Zygarde-GX | Rare Shiny GX | flagged | SHINY sprite, etched vault foil + flares + silver frame, 16-frame vaultgx anim (Charizard-GX SV49), sprite zygarde-complete; a few faint specks left from the thin cyan cape outline lines |
| sma-SV66 | Lycanroc-GX | Rare Shiny GX | ok | SHINY sprite, etched vault foil + flares + silver frame, 16-frame vaultgx anim (Charizard-GX SV49), sprite lycanroc-midnight, flipped to the card's facing; sprite, facing, scene, data OK |
| sma-SV67 | Lycanroc-GX | Rare Shiny GX | ok | SHINY sprite, etched vault foil + flares + silver frame, 16-frame vaultgx anim (Charizard-GX SV49), sprite lycanroc-dusk, flipped to the card's facing; sprite, facing, scene, data OK |
| sma-SV68 | Buzzwole-GX | Rare Shiny GX | ok | SHINY sprite, etched vault foil + flares + silver frame, 16-frame vaultgx anim (Charizard-GX SV49), sprite buzzwole; sprite, facing, scene, data OK |
| sma-SV69 | Umbreon-GX | Rare Shiny GX | ok | SHINY sprite, etched vault foil + flares + silver frame, 16-frame vaultgx anim (Charizard-GX SV49), sprite umbreon; sprite, facing, scene, data OK |
| sma-SV70 | Darkrai-GX | Rare Shiny GX | ok | SHINY sprite, etched vault foil + flares + silver frame, 16-frame vaultgx anim (Charizard-GX SV49), sprite darkrai; sprite, facing, scene, data OK |
| sma-SV71 | Guzzlord-GX | Rare Shiny GX | ok | SHINY sprite, etched vault foil + flares + silver frame, 16-frame vaultgx anim (Charizard-GX SV49), sprite guzzlord; sprite, facing, scene, data OK |
| sma-SV72 | Scizor-GX | Rare Shiny GX | ok | SHINY sprite, etched vault foil + flares + silver frame, 16-frame vaultgx anim (Charizard-GX SV49), sprite scizor; sprite, facing, scene, data OK |
| sma-SV73 | Kartana-GX | Rare Shiny GX | ok | SHINY sprite, etched vault foil + flares + silver frame, 16-frame vaultgx anim (Charizard-GX SV49), sprite kartana; sprite, facing, scene, data OK |
| sma-SV74 | Stakataka-GX | Rare Shiny GX | ok | SHINY sprite, etched vault foil + flares + silver frame, 16-frame vaultgx anim (Charizard-GX SV49), sprite stakataka; sprite, facing, scene, data OK |
| sma-SV75 | Gardevoir-GX | Rare Shiny GX | ok | SHINY sprite, etched vault foil + flares + silver frame, 16-frame vaultgx anim (Charizard-GX SV49), sprite gardevoir; sprite, facing, scene, data OK |
| sma-SV76 | Sylveon-GX | Rare Shiny GX | ok | SHINY sprite, etched vault foil + flares + silver frame, 16-frame vaultgx anim (Charizard-GX SV49), sprite sylveon; sprite, facing, scene, data OK |
| sma-SV77 | Altaria-GX | Rare Shiny GX | flagged | SHINY sprite, etched vault foil + flares + silver frame, 16-frame vaultgx anim (Charizard-GX SV49), sprite altaria, flipped to the card's facing; flipped on the head's position (right of the cloud body); the face itself is frontal |
| sma-SV78 | Noivern-GX | Rare Shiny GX | flagged | SHINY sprite, etched vault foil + flares + silver frame, 16-frame vaultgx anim (Charizard-GX SV49), sprite noivern, flipped to the card's facing; three-quarter pose, head turned right: flipped |
| sma-SV79 | Silvally-GX | Rare Shiny GX | ok | SHINY sprite, etched vault foil + flares + silver frame, 16-frame vaultgx anim (Charizard-GX SV49), sprite silvally; sprite, facing, scene, data OK |
| sma-SV80 | Drampa-GX | Rare Shiny GX | ok | SHINY sprite, etched vault foil + flares + silver frame, 16-frame vaultgx anim (Charizard-GX SV49), sprite drampa; sprite, facing, scene, data OK |
| sma-SV81 | Aether Foundation Employee | Rare Ultra | skipped | Trainer (no Pokemon) |
| sma-SV82 | Cynthia | Rare Ultra | skipped | Trainer (no Pokemon) |
| sma-SV83 | Fisherman | Rare Ultra | skipped | Trainer (no Pokemon) |
| sma-SV84 | Guzma | Rare Ultra | skipped | Trainer (no Pokemon) |
| sma-SV85 | Hiker | Rare Ultra | skipped | Trainer (no Pokemon) |
| sma-SV86 | Lady | Rare Ultra | skipped | Trainer (no Pokemon) |
| sma-SV87 | Aether Paradise Conservation Area | Rare Secret | skipped | Trainer (no Pokemon) |
| sma-SV88 | Brooklet Hill | Rare Secret | skipped | Trainer (no Pokemon) |
| sma-SV89 | Mt. Coronet | Rare Secret | skipped | Trainer (no Pokemon) |
| sma-SV90 | Shrine of Punishment | Rare Secret | skipped | Trainer (no Pokemon) |
| sma-SV91 | Tapu Bulu-GX | Rare Secret | ok | gold remap + faceted gold, 16-frame gold anim (Tapu Koko-GX SV93), sprite tapu-bulu; sprite, facing, scene, data OK |
| sma-SV92 | Tapu Fini-GX | Rare Secret | ok | gold remap + faceted gold, 16-frame gold anim (Tapu Koko-GX SV93), sprite tapu-fini; sprite, facing, scene, data OK |
| sma-SV93 | Tapu Koko-GX | Rare Secret | ok | approved ladder card; gold remap + faceted gold, 16-frame gold anim (Tapu Koko-GX SV93), sprite tapu-koko; sprite, facing, scene, data OK |
| sma-SV94 | Tapu Lele-GX | Rare Secret | ok | gold remap + faceted gold, 16-frame gold anim (Tapu Koko-GX SV93), sprite tapu-lele; sprite, facing, scene, data OK |
