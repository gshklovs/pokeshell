# Neo Genesis (neo1) audit

Every built card (81: the 4 ladder cards + 77 from the five group batches) was checked against its real scan on contact sheets (work/audit/sheets/, real | ours). A card is ok when its treatment is the ladder card of its printed rarity (FULLSET.md), the sprite is the right Pokemon and faces the way the card does, the scene is the card's own with all text, logos and the Stage badge painted out and no noticeable ghost, and the data, text half and animations are right. Frontal Pokemon (Chinchou, Hoothoot, Sentret, Snubbull, Spinarak, Sudowoodo, Sunkern, Wooper, Noctowl ...) have no facing to match and are ok unflipped; the near-frontal ones a reader could argue are flagged. No clear error was found, so batch_fixes.py has no fixes; every flag is a taste call for the lookbook.

Counts: ok 50, fixed 0, flagged 31, skipped 30 (set list 111)

Automated checks, all clean: audit/verify_all.py (neoverify on all 81: sprite shape, outline and colours exact apart from the flip, no recolour at any Neo Genesis rarity; card data verbatim from the API record, tier == API rarity; size <= 140 x 110 grid px; 16-frame loops whose final frame is the static art; 0 failures) and audit/audit_meta.py (finish = the rarity's recipe, sprite = plan.json's, commons flipped exactly as set.json flip_commons, text half with the rarity's frame colour, renders normal + shiny, 16-frame 12 fps anims normal + shiny on the 18 Rare Holos and none on the 63 non-foil cards, commons plain).

Coverage: 111 cards in the set list; 81 built (18 Rare Holo, 6 Rare, 27 Uncommon, 30 Common), 30 skipped, none of them a Pokemon: 21 Trainers (83-103), 3 special Energy (Metal 19, a Rare Holo; Darkness 104; Recycle 105) and 6 basic Energy (106-111, which have no API rarity).

| id | name | tier | status | reason |
|---|---|---|---|---|
| neo1-1 | Ampharos | Rare Holo | ok | WotC starlight holo in the art box, 16-frame wotc anim (Lugia 9); sprite, facing, scene, data OK |
| neo1-2 | Azumarill | Rare Holo | flagged | WotC starlight holo in the art box, 16-frame wotc anim (Lugia 9); facing ambiguous (frontal): not flipped |
| neo1-3 | Bellossom | Rare Holo | flagged | WotC starlight holo in the art box, 16-frame wotc anim (Lugia 9); facing ambiguous (two frontal Bellossom): not flipped; the second Bellossom (top right) is painted out too, one sprite on the big one |
| neo1-4 | Feraligatr | Rare Holo | ok | WotC starlight holo in the art box, 16-frame wotc anim (Lugia 9), flipped to the card's facing; sprite, facing, scene, data OK |
| neo1-5 | Feraligatr | Rare Holo | flagged | WotC starlight holo in the art box, 16-frame wotc anim (Lugia 9); a faint pale streak of the white halo is left near the tail tip, barely visible at grid scale |
| neo1-6 | Heracross | Rare Holo | ok | WotC starlight holo in the art box, 16-frame wotc anim (Lugia 9); sprite, facing, scene, data OK |
| neo1-7 | Jumpluff | Rare Holo | flagged | WotC starlight holo in the art box, 16-frame wotc anim (Lugia 9); facing ambiguous (floating, face to the viewer): not flipped |
| neo1-8 | Kingdra | Rare Holo | ok | WotC starlight holo in the art box, 16-frame wotc anim (Lugia 9); sprite, facing, scene, data OK |
| neo1-9 | Lugia | Rare Holo | ok | approved ladder card; WotC starlight holo in the art box, 16-frame wotc anim (Lugia 9); sprite, facing, scene, data OK |
| neo1-10 | Meganium | Rare Holo | ok | WotC starlight holo in the art box, 16-frame wotc anim (Lugia 9); sprite, facing, scene, data OK |
| neo1-11 | Meganium | Rare Holo | flagged | WotC starlight holo in the art box, 16-frame wotc anim (Lugia 9); facing ambiguous (frontal, looking up): not flipped |
| neo1-12 | Pichu | Rare Holo | flagged | WotC starlight holo in the art box, 16-frame wotc anim (Lugia 9); facing ambiguous (frontal): not flipped |
| neo1-13 | Skarmory | Rare Holo | ok | WotC starlight holo in the art box, 16-frame wotc anim (Lugia 9); sprite, facing, scene, data OK |
| neo1-14 | Slowking | Rare Holo | flagged | WotC starlight holo in the art box, 16-frame wotc anim (Lugia 9); facing ambiguous (frontal): not flipped; the fill mirrors the dark rock a little blockily at the right edge |
| neo1-15 | Steelix | Rare Holo | ok | WotC starlight holo in the art box, 16-frame wotc anim (Lugia 9); sprite, facing, scene, data OK |
| neo1-16 | Togetic | Rare Holo | flagged | WotC starlight holo in the art box, 16-frame wotc anim (Lugia 9); the glow-orb background leaves a slightly lighter, seam-edged patch where Togetic was (the smooth fill was worse) |
| neo1-17 | Typhlosion | Rare Holo | ok | WotC starlight holo in the art box, 16-frame wotc anim (Lugia 9), flipped to the card's facing; sprite, facing, scene, data OK |
| neo1-18 | Typhlosion | Rare Holo | ok | WotC starlight holo in the art box, 16-frame wotc anim (Lugia 9); sprite, facing, scene, data OK |
| neo1-19 | Metal Energy | Rare Holo | skipped | Energy (no Pokemon) |
| neo1-20 | Cleffa | Rare | flagged | grid-scale matte scene, 16 colours, non-foil (Murkrow 24), flipped to the card's facing; facing a judgement call: the head turns three-quarter to the right and the body leans right into the yarn; flipped (the brief's first read was ambiguous / unflipped) |
| neo1-21 | Donphan | Rare | ok | grid-scale matte scene, 16 colours, non-foil (Murkrow 24); the sky fill is a per-row blend of the visible strip (batch_rare rowfill), so it reads sky / horizon / hills like the card |
| neo1-22 | Elekid | Rare | flagged | grid-scale matte scene, 16 colours, non-foil (Murkrow 24); facing ambiguous (frontal, leaning): not flipped; the lightning bolts and clouds are scene |
| neo1-23 | Magby | Rare | flagged | grid-scale matte scene, 16 colours, non-foil (Murkrow 24); facing ambiguous (frontal, beak a touch left): not flipped |
| neo1-24 | Murkrow | Rare | ok | approved ladder card; grid-scale matte scene, 16 colours, non-foil (Murkrow 24); sprite, facing, scene, data OK |
| neo1-25 | Sneasel | Rare | ok | grid-scale matte scene, 16 colours, non-foil (Murkrow 24); sprite, facing, scene, data OK |
| neo1-26 | Aipom | Uncommon | flagged | sprite-scale matte scene, 12 colours (Quilava 46); facing ambiguous (hangs upside down, face to the viewer): not flipped |
| neo1-27 | Ariados | Uncommon | ok | sprite-scale matte scene, 12 colours (Quilava 46); the second Ariados behind and the blurred one in the foreground are painted out too; most of the fill is the dark deck |
| neo1-28 | Bayleef | Uncommon | ok | sprite-scale matte scene, 12 colours (Quilava 46); sprite, facing, scene, data OK |
| neo1-29 | Bayleef | Uncommon | flagged | sprite-scale matte scene, 12 colours (Quilava 46); a faint pale-green patch near the front foot (probably the ground's own colour) |
| neo1-30 | Clefairy | Uncommon | flagged | sprite-scale matte scene, 12 colours (Quilava 46); facing ambiguous (frontal, on a swing): not flipped; the swing is scene |
| neo1-31 | Croconaw | Uncommon | flagged | sprite-scale matte scene, 12 colours (Quilava 46); facing ambiguous (frontal body, snout up-left): not flipped |
| neo1-32 | Croconaw | Uncommon | ok | sprite-scale matte scene, 12 colours (Quilava 46), flipped to the card's facing; sprite, facing, scene, data OK |
| neo1-33 | Electabuzz | Uncommon | flagged | sprite-scale matte scene, 12 colours (Quilava 46); facing ambiguous (frontal): not flipped; he fills most of the window, so the fill is a smooth blend, mostly under the sprite |
| neo1-34 | Flaaffy | Uncommon | ok | sprite-scale matte scene, 12 colours (Quilava 46); sprite, facing, scene, data OK |
| neo1-35 | Furret | Uncommon | flagged | sprite-scale matte scene, 12 colours (Quilava 46); facing ambiguous (head turned slightly left, tail curls out at the left): not flipped; the tiny Furret far off at the right stays as scene |
| neo1-36 | Gloom | Uncommon | flagged | sprite-scale matte scene, 12 colours (Quilava 46); facing ambiguous (lying on its back, face to the viewer): not flipped |
| neo1-37 | Granbull | Uncommon | flagged | sprite-scale matte scene, 12 colours (Quilava 46); facing ambiguous (frontal): not flipped; a large smooth fill, mostly under the sprite |
| neo1-38 | Lanturn | Uncommon | flagged | sprite-scale matte scene, 12 colours (Quilava 46); the left lure's faint teal haze partly stays, blending into the dark sea |
| neo1-39 | Ledian | Uncommon | flagged | sprite-scale matte scene, 12 colours (Quilava 46); facing ambiguous (frontal): not flipped; the two smaller Ledian behind are painted out too; the matte's light rim is olive on the dark sky |
| neo1-40 | Magmar | Uncommon | ok | sprite-scale matte scene, 12 colours (Quilava 46); sprite, facing, scene, data OK |
| neo1-41 | Miltank | Uncommon | flagged | sprite-scale matte scene, 12 colours (Quilava 46); facing ambiguous (body turned left, head three-quarter to the right): not flipped; the herd far off at the right stays as scene; a slightly flat green patch where the tail shadow was |
| neo1-42 | Noctowl | Uncommon | flagged | sprite-scale matte scene, 12 colours (Quilava 46); facing ambiguous (frontal): not flipped; the tiny Hoothoot in the trees stay as scene |
| neo1-43 | Phanpy | Uncommon | ok | sprite-scale matte scene, 12 colours (Quilava 46); sprite, facing, scene, data OK |
| neo1-44 | Piloswine | Uncommon | ok | sprite-scale matte scene, 12 colours (Quilava 46); sprite, facing, scene, data OK |
| neo1-45 | Quagsire | Uncommon | ok | sprite-scale matte scene, 12 colours (Quilava 46); sprite, facing, scene, data OK |
| neo1-46 | Quilava | Uncommon | ok | approved ladder card; sprite-scale matte scene, 12 colours (Quilava 46); sprite, facing, scene, data OK |
| neo1-47 | Quilava | Uncommon | ok | sprite-scale matte scene, 12 colours (Quilava 46), flipped to the card's facing; sprite, facing, scene, data OK |
| neo1-48 | Seadra | Uncommon | ok | sprite-scale matte scene, 12 colours (Quilava 46); sprite, facing, scene, data OK |
| neo1-49 | Skiploom | Uncommon | flagged | sprite-scale matte scene, 12 colours (Quilava 46); facing ambiguous (near-frontal, face a little right): not flipped |
| neo1-50 | Sunflora | Uncommon | flagged | sprite-scale matte scene, 12 colours (Quilava 46); facing ambiguous (frontal): not flipped |
| neo1-51 | Togepi | Uncommon | flagged | sprite-scale matte scene, 12 colours (Quilava 46); facing ambiguous (frontal, in a tree hollow): not flipped |
| neo1-52 | Xatu | Uncommon | ok | sprite-scale matte scene, 12 colours (Quilava 46), flipped to the card's facing; sprite, facing, scene, data OK |
| neo1-53 | Chikorita | Common | flagged | plain sprite, no background, no anim (Totodile 81); Common facing ambiguous: Chikorita stands frontal; not flipped |
| neo1-54 | Chikorita | Common | flagged | plain sprite, no background, no anim (Totodile 81); Common facing ambiguous: Chikorita frontal; not flipped |
| neo1-55 | Chinchou | Common | ok | plain sprite, no background, no anim (Totodile 81); sprite, facing, scene, data OK |
| neo1-56 | Cyndaquil | Common | ok | plain sprite, no background, no anim (Totodile 81); sprite, facing, scene, data OK |
| neo1-57 | Cyndaquil | Common | ok | plain sprite, no background, no anim (Totodile 81); sprite, facing, scene, data OK |
| neo1-58 | Girafarig | Common | ok | plain sprite, no background, no anim (Totodile 81); sprite, facing, scene, data OK |
| neo1-59 | Gligar | Common | ok | plain sprite, no background, no anim (Totodile 81); sprite, facing, scene, data OK |
| neo1-60 | Hoothoot | Common | ok | plain sprite, no background, no anim (Totodile 81); sprite, facing, scene, data OK |
| neo1-61 | Hoppip | Common | flagged | plain sprite, no background, no anim (Totodile 81); Common facing ambiguous: Hoppip frontal, face a little right; not flipped |
| neo1-62 | Horsea | Common | ok | plain sprite, no background, no anim (Totodile 81); sprite, facing, scene, data OK |
| neo1-63 | Ledyba | Common | flagged | plain sprite, no background, no anim (Totodile 81); Common facing ambiguous: Ledyba flies toward the viewer; not flipped |
| neo1-64 | Mantine | Common | ok | plain sprite, no background, no anim (Totodile 81); sprite, facing, scene, data OK |
| neo1-65 | Mareep | Common | ok | plain sprite, no background, no anim (Totodile 81); sprite, facing, scene, data OK |
| neo1-66 | Marill | Common | ok | plain sprite, no background, no anim (Totodile 81); sprite, facing, scene, data OK |
| neo1-67 | Natu | Common | ok | plain sprite, no background, no anim (Totodile 81); sprite, facing, scene, data OK |
| neo1-68 | Oddish | Common | flagged | plain sprite, no background, no anim (Totodile 81); Common facing ambiguous: Oddish lies on its back; not flipped |
| neo1-69 | Onix | Common | ok | plain sprite, no background, no anim (Totodile 81); sprite, facing, scene, data OK |
| neo1-70 | Pikachu | Common | ok | plain sprite, no background, no anim (Totodile 81); sprite, facing, scene, data OK |
| neo1-71 | Sentret | Common | ok | plain sprite, no background, no anim (Totodile 81); sprite, facing, scene, data OK |
| neo1-72 | Shuckle | Common | ok | plain sprite, no background, no anim (Totodile 81); sprite, facing, scene, data OK |
| neo1-73 | Slowpoke | Common | ok | plain sprite, no background, no anim (Totodile 81); sprite, facing, scene, data OK |
| neo1-74 | Snubbull | Common | ok | plain sprite, no background, no anim (Totodile 81); sprite, facing, scene, data OK |
| neo1-75 | Spinarak | Common | ok | plain sprite, no background, no anim (Totodile 81); sprite, facing, scene, data OK |
| neo1-76 | Stantler | Common | ok | plain sprite, no background, no anim (Totodile 81); sprite, facing, scene, data OK |
| neo1-77 | Sudowoodo | Common | ok | plain sprite, no background, no anim (Totodile 81); sprite, facing, scene, data OK |
| neo1-78 | Sunkern | Common | ok | plain sprite, no background, no anim (Totodile 81); sprite, facing, scene, data OK |
| neo1-79 | Swinub | Common | ok | plain sprite, no background, no anim (Totodile 81); sprite, facing, scene, data OK |
| neo1-80 | Totodile | Common | ok | plain sprite, no background, no anim (Totodile 81), flipped to the card's facing; sprite, facing, scene, data OK |
| neo1-81 | Totodile | Common | ok | approved ladder card; plain sprite, no background, no anim (Totodile 81); sprite, facing, scene, data OK |
| neo1-82 | Wooper | Common | ok | plain sprite, no background, no anim (Totodile 81); sprite, facing, scene, data OK |
| neo1-83 | Arcade Game | Rare | skipped | Trainer (no Pokemon) |
| neo1-84 | Ecogym | Rare | skipped | Trainer (no Pokemon) |
| neo1-85 | Energy Charge | Rare | skipped | Trainer (no Pokemon) |
| neo1-86 | Focus Band | Rare | skipped | Trainer (no Pokemon) |
| neo1-87 | Mary | Rare | skipped | Trainer (no Pokemon) |
| neo1-88 | PokéGear | Rare | skipped | Trainer (no Pokemon) |
| neo1-89 | Super Energy Retrieval | Rare | skipped | Trainer (no Pokemon) |
| neo1-90 | Time Capsule | Rare | skipped | Trainer (no Pokemon) |
| neo1-91 | Bill's Teleporter | Uncommon | skipped | Trainer (no Pokemon) |
| neo1-92 | Card-Flip Game | Uncommon | skipped | Trainer (no Pokemon) |
| neo1-93 | Gold Berry | Uncommon | skipped | Trainer (no Pokemon) |
| neo1-94 | Miracle Berry | Uncommon | skipped | Trainer (no Pokemon) |
| neo1-95 | New Pokédex | Uncommon | skipped | Trainer (no Pokemon) |
| neo1-96 | Professor Elm | Uncommon | skipped | Trainer (no Pokemon) |
| neo1-97 | Sprout Tower | Uncommon | skipped | Trainer (no Pokemon) |
| neo1-98 | Super Scoop Up | Uncommon | skipped | Trainer (no Pokemon) |
| neo1-99 | Berry | Common | skipped | Trainer (no Pokemon) |
| neo1-100 | Double Gust | Common | skipped | Trainer (no Pokemon) |
| neo1-101 | Moo-Moo Milk | Common | skipped | Trainer (no Pokemon) |
| neo1-102 | Pokémon March | Common | skipped | Trainer (no Pokemon) |
| neo1-103 | Super Rod | Common | skipped | Trainer (no Pokemon) |
| neo1-104 | Darkness Energy | Rare | skipped | Energy (no Pokemon) |
| neo1-105 | Recycle Energy | Rare | skipped | Energy (no Pokemon) |
| neo1-106 | Fighting Energy |  | skipped | Energy (no Pokemon) |
| neo1-107 | Fire Energy |  | skipped | Energy (no Pokemon) |
| neo1-108 | Grass Energy |  | skipped | Energy (no Pokemon) |
| neo1-109 | Lightning Energy |  | skipped | Energy (no Pokemon) |
| neo1-110 | Psychic Energy |  | skipped | Energy (no Pokemon) |
| neo1-111 | Water Energy |  | skipped | Energy (no Pokemon) |
