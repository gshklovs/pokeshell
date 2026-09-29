# Evolving Skies audit

All 193 Pokémon cards were checked against their real scans on contact sheets (work/audit/sheets/). A card is ok when its treatment matches its real finish, the sprite is the right Pokémon and form, the scene is the card's own, and the data, text half and animations are right. The live pack was checked too: tier, dist .ans/.anim and art rows.

Counts: ok 172, fixed 1, flagged 9, out of scope 11

Checks that passed for every card: every batch verify run was clean (sprite shape, outline and colours exact apart from the allowed flip, rainbow or gold; card data verbatim; 16 frames with the last equal to the static art). Commons have no background and no anim. Non-foil cards have no anim. Foil cards have both .anim files in dist/. Every card is in pack.json at its printed-rarity tier (Pikachu 49 is the one to look at). Gigantamax sprites appear only on cards that say Gigantamax (101, 123, 216, 219, 220). The Galarian birds use -galar sprites, and every Lycanroc uses lycanroc-dusk.

Alt-art check: the 11 painted Rare Ultras (167, 175, 180, 182, 184, 186, 189, 192, 194, 196, 198) are the complete list. Every other Rare Ultra is a plain full art. The five painted Rare Rainbows (205, 209, 212, 218, 220) already use the Umbreon 215 recipe. The other 10 Rare Rainbows are true rainbows.

| id | name | tier | status | reason |
|---|---|---|---|---|
| swsh7-1 | Pinsir | Rare | ok | matte grid-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-2 | Hoppip | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data and pack OK |
| swsh7-3 | Skiploom | Uncommon | ok | matte sprite-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-4 | Jumpluff | Rare Holo | ok | holo foil in the scene, 16-frame anim; sprite, facing, scene, data and pack OK |
| swsh7-5 | Seedot | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data and pack OK |
| swsh7-6 | Tropius | Rare | ok | matte grid-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-7 | Leafeon V | Rare Holo V | ok | silver frame + sunpillar, anim; sprite, facing, scene, data and pack OK |
| swsh7-8 | Leafeon VMAX | Rare Holo VMAX | ok | gunmetal frame + sunpillar, anim; sprite, facing, scene, data and pack OK |
| swsh7-9 | Petilil | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data and pack OK |
| swsh7-10 | Lilligant | Rare | ok | matte grid-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-11 | Dwebble | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data and pack OK |
| swsh7-12 | Crustle | Uncommon | ok | matte sprite-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-13 | Trevenant V | Rare Holo V | ok | silver frame + sunpillar, anim; sprite, facing, scene, data and pack OK |
| swsh7-14 | Trevenant VMAX | Rare Holo VMAX | ok | gunmetal frame + sunpillar, anim; sprite, facing, scene, data and pack OK |
| swsh7-15 | Gossifleur | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data and pack OK |
| swsh7-16 | Eldegoss | Rare Holo | ok | holo foil in the scene, 16-frame anim; sprite, facing, scene, data and pack OK |
| swsh7-17 | Applin | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data and pack OK |
| swsh7-18 | Flareon VMAX | Rare Holo VMAX | ok | gunmetal frame + sunpillar, anim; sprite, facing, scene, data and pack OK |
| swsh7-19 | Entei | Rare Holo | ok | holo foil in the scene, 16-frame anim; sprite, facing, scene, data and pack OK |
| swsh7-20 | Victini | Rare Holo | ok | holo foil in the scene, 16-frame anim; sprite, facing, scene, data and pack OK |
| swsh7-21 | Volcarona V | Rare Holo V | ok | silver frame + sunpillar, anim; sprite, facing, scene, data and pack OK |
| swsh7-22 | Litleo | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data and pack OK |
| swsh7-23 | Pyroar | Uncommon | ok | matte sprite-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-24 | Psyduck | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data and pack OK |
| swsh7-25 | Golduck | Uncommon | ok | matte sprite-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-26 | Tentacool | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data and pack OK |
| swsh7-27 | Tentacruel | Uncommon | ok | matte sprite-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-28 | Gyarados V | Rare Holo V | ok | silver frame + sunpillar, anim; sprite, facing, scene, data and pack OK |
| swsh7-29 | Gyarados VMAX | Rare Holo VMAX | ok | gunmetal frame + sunpillar, anim; sprite, facing, scene, data and pack OK |
| swsh7-30 | Vaporeon VMAX | Rare Holo VMAX | ok | gunmetal frame + sunpillar, anim; sprite, facing, scene, data and pack OK |
| swsh7-31 | Suicune V | Rare Holo V | ok | silver frame + sunpillar, anim; sprite, facing, scene, data and pack OK |
| swsh7-32 | Lotad | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data and pack OK |
| swsh7-33 | Lombre | Uncommon | ok | matte sprite-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-34 | Ludicolo | Rare Holo | ok | holo foil in the scene, 16-frame anim; sprite, facing, scene, data and pack OK |
| swsh7-35 | Carvanha | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data and pack OK |
| swsh7-36 | Sharpedo | Rare | ok | matte grid-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-37 | Feebas | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data and pack OK |
| swsh7-38 | Milotic | Rare | ok | matte grid-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-39 | Luvdisc | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data and pack OK |
| swsh7-40 | Glaceon V | Rare Holo V | ok | silver frame + sunpillar, anim; sprite, facing, scene, data and pack OK |
| swsh7-41 | Glaceon VMAX | Rare Holo VMAX | ok | gunmetal frame + sunpillar, anim; sprite, facing, scene, data and pack OK |
| swsh7-42 | Tympole | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data and pack OK |
| swsh7-43 | Cryogonal | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data and pack OK |
| swsh7-44 | Bergmite | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data and pack OK |
| swsh7-45 | Avalugg | Uncommon | ok | matte sprite-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-46 | Wishiwashi | Rare | ok | matte grid-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-47 | Eiscue | Uncommon | ok | matte sprite-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-48 | Arctovish V | Rare Holo V | ok | silver frame + sunpillar, anim; sprite, facing, scene, data and pack OK |
| swsh7-49 | Pikachu | Reverse Holo | flagged | ladder built it as a Reverse Holo (foil ring + anim), but the live pack imports it as its printed rarity, Common (plain sprite, no .anim). Pack is consistent with the real card; decide which you want. |
| swsh7-50 | Raichu | Rare Holo | ok | holo foil in the scene, 16-frame anim; sprite, facing, scene, data and pack OK |
| swsh7-51 | Jolteon VMAX | Rare Holo VMAX | ok | gunmetal frame + sunpillar, anim; sprite, facing, scene, data and pack OK |
| swsh7-52 | Chinchou | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data and pack OK |
| swsh7-53 | Lanturn | Uncommon | ok | matte sprite-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-54 | Mareep | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data and pack OK |
| swsh7-55 | Flaaffy | Uncommon | ok | matte sprite-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-56 | Ampharos | Rare | ok | matte grid-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-57 | Emolga | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data and pack OK |
| swsh7-58 | Dracozolt V | Rare Holo V | ok | silver frame + sunpillar, anim; sprite, facing, scene, data and pack OK |
| swsh7-59 | Dracozolt VMAX | Rare Holo VMAX | ok | gunmetal frame + sunpillar, anim; sprite, facing, scene, data and pack OK |
| swsh7-60 | Regieleki | Rare Holo | ok | holo foil in the scene, 16-frame anim; sprite, facing, scene, data and pack OK |
| swsh7-61 | Drowzee | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data and pack OK |
| swsh7-62 | Hypno | Uncommon | ok | matte sprite-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-63 | Galarian Articuno | Rare Holo | ok | holo foil in the scene, 16-frame anim (sprite articuno-galar); sprite, facing, scene, data and pack OK |
| swsh7-64 | Espeon V | Rare Holo V | ok | silver frame + sunpillar, anim; sprite, facing, scene, data and pack OK |
| swsh7-65 | Espeon VMAX | Rare Holo VMAX | ok | gunmetal frame + sunpillar, anim; sprite, facing, scene, data and pack OK |
| swsh7-66 | Wobbuffet | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data and pack OK |
| swsh7-67 | Sableye | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data and pack OK |
| swsh7-68 | Woobat | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data and pack OK |
| swsh7-69 | Swoobat | Uncommon | ok | matte sprite-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-70 | Golurk V | Rare Holo V | ok | silver frame + sunpillar, anim; sprite, facing, scene, data and pack OK |
| swsh7-71 | Flabébé | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data and pack OK |
| swsh7-72 | Floette | Uncommon | ok | matte sprite-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-73 | Florges | Rare Holo | ok | holo foil in the scene, 16-frame anim; sprite, facing, scene, data and pack OK |
| swsh7-74 | Sylveon V | Rare Holo V | ok | silver frame + sunpillar, anim; sprite, facing, scene, data and pack OK |
| swsh7-75 | Sylveon VMAX | Rare Holo VMAX | ok | gunmetal frame + sunpillar, anim; sprite, facing, scene, data and pack OK |
| swsh7-76 | Pumpkaboo | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data and pack OK |
| swsh7-77 | Gourgeist | Rare | ok | matte grid-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-78 | Cutiefly | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data and pack OK |
| swsh7-79 | Ribombee | Uncommon | ok | matte sprite-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-80 | Marshadow | Rare Holo | flagged | a dark smudge right of the sprite: the card's own black shadow wisps, part of Marshadow's move. Could read as a ghost of the Pokémon. |
| swsh7-81 | Hitmonchan | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data and pack OK |
| swsh7-82 | Galarian Zapdos | Rare Holo | ok | holo foil in the scene, 16-frame anim (sprite zapdos-galar); sprite, facing, scene, data and pack OK |
| swsh7-83 | Medicham V | Rare Holo V | ok | silver frame + sunpillar, anim; sprite, facing, scene, data and pack OK |
| swsh7-84 | Hippopotas | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data and pack OK |
| swsh7-85 | Hippowdon | Uncommon | flagged | card Hippowdon's head is on the left; the sprite's facing is hard to read at this size. Check whether it should be flipped. |
| swsh7-86 | Roggenrola | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data and pack OK |
| swsh7-87 | Boldore | Uncommon | ok | matte sprite-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-88 | Gigalith | Rare | ok | matte grid-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-89 | Palpitoad | Uncommon | ok | matte sprite-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-90 | Seismitoad | Rare | ok | matte grid-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-91 | Lycanroc V | Rare Holo V | ok | silver frame + sunpillar, anim (sprite lycanroc-dusk); sprite, facing, scene, data and pack OK |
| swsh7-92 | Lycanroc VMAX | Rare Holo VMAX | ok | gunmetal frame + sunpillar, anim (sprite lycanroc-dusk); sprite, facing, scene, data and pack OK |
| swsh7-93 | Galarian Moltres | Rare Holo | ok | holo foil in the scene, 16-frame anim (sprite moltres-galar); sprite, facing, scene, data and pack OK |
| swsh7-94 | Umbreon V | Rare Holo V | flagged | card Umbreon lunges near-frontal, slightly right; ours faces left. Ambiguous. |
| swsh7-95 | Umbreon VMAX | Rare Holo VMAX | flagged | card's Umbreon looks right (head three-quarter to the right); ours faces left. Same pose as Umbreon 215 (approved unflipped), so left as is. |
| swsh7-96 | Nuzleaf | Uncommon | ok | matte sprite-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-97 | Shiftry | Rare | ok | matte grid-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-98 | Scraggy | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data and pack OK |
| swsh7-99 | Scrafty | Uncommon | ok | matte sprite-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-100 | Garbodor V | Rare Holo V | ok | silver frame + sunpillar, anim; sprite, facing, scene, data and pack OK |
| swsh7-101 | Garbodor VMAX | Rare Holo VMAX | ok | gunmetal frame + sunpillar, anim (sprite garbodor-gmax); sprite, facing, scene, data and pack OK |
| swsh7-102 | Zorua | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data and pack OK |
| swsh7-103 | Zoroark | Rare Holo | ok | holo foil in the scene, 16-frame anim; sprite, facing, scene, data and pack OK |
| swsh7-104 | Nickit | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data and pack OK |
| swsh7-105 | Thievul | Rare | ok | matte grid-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-106 | Altaria | Rare | ok | matte grid-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-107 | Bagon | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data and pack OK |
| swsh7-108 | Shelgon | Uncommon | ok | matte sprite-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-109 | Salamence | Rare Holo | ok | holo foil in the scene, 16-frame anim; sprite, facing, scene, data and pack OK |
| swsh7-110 | Rayquaza V | Rare Holo V | ok | silver frame + sunpillar, anim; sprite, facing, scene, data and pack OK |
| swsh7-111 | Rayquaza VMAX | Rare Holo VMAX | ok | gunmetal frame + sunpillar, anim; sprite, facing, scene, data and pack OK |
| swsh7-112 | Dialga | Rare Holo | ok | holo foil in the scene, 16-frame anim; sprite, facing, scene, data and pack OK |
| swsh7-113 | Deino | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data and pack OK |
| swsh7-114 | Zweilous | Uncommon | ok | matte sprite-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-115 | Hydreigon | Rare Holo | ok | holo foil in the scene, 16-frame anim; sprite, facing, scene, data and pack OK |
| swsh7-116 | Kyurem | Rare Holo | ok | holo foil in the scene, 16-frame anim; sprite, facing, scene, data and pack OK |
| swsh7-117 | Noivern V | Rare Holo V | ok | silver frame + sunpillar, anim; sprite, facing, scene, data and pack OK |
| swsh7-118 | Zygarde | Rare Holo | ok | holo foil in the scene, 16-frame anim; sprite, facing, scene, data and pack OK |
| swsh7-119 | Drampa | Rare | ok | matte grid-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-120 | Flapple | Rare | flagged | card Flapple's head sits right of the apple; the sprite's head is left. The pose is ambiguous. |
| swsh7-121 | Appletun | Rare | ok | matte grid-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-122 | Duraludon V | Rare Holo V | ok | silver frame + sunpillar, anim; sprite, facing, scene, data and pack OK |
| swsh7-123 | Duraludon VMAX | Rare Holo VMAX | ok | gunmetal frame + sunpillar, anim (sprite duraludon-gmax); sprite, facing, scene, data and pack OK |
| swsh7-124 | Regidrago | Rare Holo | ok | holo foil in the scene, 16-frame anim; sprite, facing, scene, data and pack OK |
| swsh7-125 | Eevee | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data and pack OK |
| swsh7-126 | Teddiursa | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data and pack OK |
| swsh7-127 | Ursaring | Uncommon | ok | matte sprite-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-128 | Smeargle | Rare | ok | matte grid-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-129 | Slakoth | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data and pack OK |
| swsh7-130 | Vigoroth | Uncommon | ok | matte sprite-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-131 | Slaking | Rare Holo | ok | holo foil in the scene, 16-frame anim; sprite, facing, scene, data and pack OK |
| swsh7-132 | Swablu | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data and pack OK |
| swsh7-133 | Lillipup | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data and pack OK |
| swsh7-134 | Herdier | Uncommon | ok | matte sprite-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-135 | Stoutland | Rare | ok | matte grid-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-136 | Rufflet | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data and pack OK |
| swsh7-137 | Braviary | Uncommon | ok | matte sprite-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-138 | Fletchling | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data and pack OK |
| swsh7-139 | Fletchinder | Uncommon | ok | matte sprite-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-140 | Talonflame | Rare | ok | matte grid-scale scene, no anim; sprite, facing, scene, data and pack OK |
| swsh7-166 | Leafeon V | Rare Ultra | ok | plain full art, fingerprint etch, anim; sprite, facing, scene, data and pack OK |
| swsh7-167 | Leafeon V | Rare Ultra | out of scope | painted alt-art Rare Ultra, being redone with the Umbreon 215 treatment in batch_altart.py by the other agent (it currently has the full-art etch; art/ is newer than the live pack) |
| swsh7-168 | Trevenant V | Rare Ultra | ok | plain full art, fingerprint etch, anim; sprite, facing, scene, data and pack OK |
| swsh7-169 | Flareon V | Rare Ultra | ok | plain full art, fingerprint etch, anim; sprite, facing, scene, data and pack OK |
| swsh7-170 | Volcarona V | Rare Ultra | ok | plain full art, fingerprint etch, anim; sprite, facing, scene, data and pack OK |
| swsh7-171 | Gyarados V | Rare Ultra | flagged | card Gyarados' head turns right (mouth lower right); ours faces left. Three-quarter pose, arguable. |
| swsh7-172 | Vaporeon V | Rare Ultra | ok | plain full art, fingerprint etch, anim; sprite, facing, scene, data and pack OK |
| swsh7-173 | Suicune V | Rare Ultra | ok | plain full art, fingerprint etch, anim; sprite, facing, scene, data and pack OK |
| swsh7-174 | Glaceon V | Rare Ultra | ok | plain full art, fingerprint etch, anim; sprite, facing, scene, data and pack OK |
| swsh7-175 | Glaceon V | Rare Ultra | out of scope | painted alt-art Rare Ultra, being redone with the Umbreon 215 treatment in batch_altart.py by the other agent (it currently has the full-art etch; art/ is newer than the live pack) |
| swsh7-176 | Arctovish V | Rare Ultra | ok | plain full art, fingerprint etch, anim; sprite, facing, scene, data and pack OK |
| swsh7-177 | Jolteon V | Rare Ultra | ok | plain full art, fingerprint etch, anim; sprite, facing, scene, data and pack OK |
| swsh7-178 | Dracozolt V | Rare Ultra | ok | plain full art, fingerprint etch, anim; sprite, facing, scene, data and pack OK |
| swsh7-179 | Espeon V | Rare Ultra | ok | plain full art, fingerprint etch, anim; sprite, facing, scene, data and pack OK |
| swsh7-180 | Espeon V | Rare Ultra | out of scope | painted alt-art Rare Ultra, being redone with the Umbreon 215 treatment in batch_altart.py by the other agent (it currently has the full-art etch; art/ is newer than the live pack) |
| swsh7-181 | Golurk V | Rare Ultra | ok | plain full art, fingerprint etch, anim; sprite, facing, scene, data and pack OK |
| swsh7-182 | Golurk V | Rare Ultra | out of scope | painted alt-art Rare Ultra, being redone with the Umbreon 215 treatment in batch_altart.py by the other agent (it currently has the full-art etch; art/ is newer than the live pack) |
| swsh7-183 | Sylveon V | Rare Ultra | ok | plain full art, fingerprint etch, anim; sprite, facing, scene, data and pack OK |
| swsh7-184 | Sylveon V | Rare Ultra | out of scope | painted alt-art Rare Ultra, being redone with the Umbreon 215 treatment in batch_altart.py by the other agent (it currently has the full-art etch; art/ is newer than the live pack) |
| swsh7-185 | Medicham V | Rare Ultra | ok | plain full art, fingerprint etch, anim; sprite, facing, scene, data and pack OK |
| swsh7-186 | Medicham V | Rare Ultra | out of scope | painted alt-art Rare Ultra, being redone with the Umbreon 215 treatment in batch_altart.py by the other agent (it currently has the full-art etch; art/ is newer than the live pack) |
| swsh7-187 | Lycanroc V | Rare Ultra | ok | plain full art, fingerprint etch, anim (sprite lycanroc-dusk); sprite, facing, scene, data and pack OK |
| swsh7-188 | Umbreon V | Rare Ultra | ok | plain full art, fingerprint etch, anim; sprite, facing, scene, data and pack OK |
| swsh7-189 | Umbreon V | Rare Ultra | out of scope | painted alt-art Rare Ultra, being redone with the Umbreon 215 treatment in batch_altart.py by the other agent (it currently has the full-art etch; art/ is newer than the live pack) |
| swsh7-190 | Garbodor V | Rare Ultra | ok | plain full art, fingerprint etch, anim; sprite, facing, scene, data and pack OK |
| swsh7-191 | Dragonite V | Rare Ultra | ok | plain full art, fingerprint etch, anim; sprite, facing, scene, data and pack OK |
| swsh7-192 | Dragonite V | Rare Ultra | out of scope | painted alt-art Rare Ultra, being redone with the Umbreon 215 treatment in batch_altart.py by the other agent (it currently has the full-art etch; art/ is newer than the live pack) |
| swsh7-193 | Rayquaza V | Rare Ultra | ok | plain full art, fingerprint etch, anim; sprite, facing, scene, data and pack OK |
| swsh7-194 | Rayquaza V | Rare Ultra | out of scope | painted alt-art Rare Ultra, being redone with the Umbreon 215 treatment in batch_altart.py by the other agent (it currently has the full-art etch; art/ is newer than the live pack) |
| swsh7-195 | Noivern V | Rare Ultra | ok | plain full art, fingerprint etch, anim; sprite, facing, scene, data and pack OK |
| swsh7-196 | Noivern V | Rare Ultra | out of scope | painted alt-art Rare Ultra, being redone with the Umbreon 215 treatment in batch_altart.py by the other agent (it currently has the full-art etch; art/ is newer than the live pack) |
| swsh7-197 | Duraludon V | Rare Ultra | flagged | card Duraludon is near-frontal, head top-right; ours unflipped. Ambiguous. |
| swsh7-198 | Duraludon V | Rare Ultra | out of scope | painted alt-art Rare Ultra, being redone with the Umbreon 215 treatment in batch_altart.py by the other agent (it currently has the full-art etch; art/ is newer than the live pack) |
| swsh7-204 | Leafeon VMAX | Rare Rainbow | ok | true rainbow, Leafeon 204 recipe, sprite blend 0.55; sprite, facing, scene, data and pack OK |
| swsh7-205 | Leafeon VMAX | Rare Rainbow | ok | painted alt-art secret, Umbreon 215 recipe; sprite, facing, scene, data and pack OK |
| swsh7-206 | Trevenant VMAX | Rare Rainbow | ok | true rainbow, Leafeon 204 recipe, sprite blend 0.55; sprite, facing, scene, data and pack OK |
| swsh7-207 | Gyarados VMAX | Rare Rainbow | ok | true rainbow, Leafeon 204 recipe, sprite blend 0.55; sprite, facing, scene, data and pack OK |
| swsh7-208 | Glaceon VMAX | Rare Rainbow | ok | true rainbow, Leafeon 204 recipe, sprite blend 0.55; sprite, facing, scene, data and pack OK |
| swsh7-209 | Glaceon VMAX | Rare Rainbow | ok | painted alt-art secret, Umbreon 215 recipe; sprite, facing, scene, data and pack OK |
| swsh7-210 | Dracozolt VMAX | Rare Rainbow | fixed | was facing left; the card's Dracozolt faces right (head top-right, as on VMAX 59). Re-rendered flipped with Leafeon 204's rainbow recipe (batch_fixes.py), verified, re-imported. |
| swsh7-211 | Sylveon VMAX | Rare Rainbow | ok | true rainbow, Leafeon 204 recipe, sprite blend 0.55; sprite, facing, scene, data and pack OK |
| swsh7-212 | Sylveon VMAX | Rare Rainbow | ok | painted alt-art secret, Umbreon 215 recipe; sprite, facing, scene, data and pack OK |
| swsh7-213 | Lycanroc VMAX | Rare Rainbow | ok | true rainbow, Leafeon 204 recipe, sprite blend 0.55 (sprite lycanroc-dusk); sprite, facing, scene, data and pack OK |
| swsh7-214 | Umbreon VMAX | Rare Rainbow | flagged | same pose as 95/215: card looks right, ours faces left. Left as is for consistency with the approved 215. |
| swsh7-215 | Umbreon VMAX | Rare Rainbow | ok | painted alt-art secret, Umbreon 215 recipe; sprite, facing, scene, data and pack OK |
| swsh7-216 | Garbodor VMAX | Rare Rainbow | ok | true rainbow, Leafeon 204 recipe, sprite blend 0.55 (sprite garbodor-gmax); sprite, facing, scene, data and pack OK |
| swsh7-217 | Rayquaza VMAX | Rare Rainbow | ok | true rainbow, Leafeon 204 recipe, sprite blend 0.55; sprite, facing, scene, data and pack OK |
| swsh7-218 | Rayquaza VMAX | Rare Rainbow | ok | painted alt-art secret, Umbreon 215 recipe; sprite, facing, scene, data and pack OK |
| swsh7-219 | Duraludon VMAX | Rare Rainbow | ok | true rainbow, Leafeon 204 recipe, sprite blend 0.55 (sprite duraludon-gmax); sprite, facing, scene, data and pack OK |
| swsh7-220 | Duraludon VMAX | Rare Rainbow | ok | painted alt-art secret, Umbreon 215 recipe (sprite duraludon-gmax); sprite, facing, scene, data and pack OK |
| swsh7-226 | Froslass | Rare Secret | ok | gold remap + gold scene, anim; sprite, facing, scene, data and pack OK |
| swsh7-227 | Inteleon | Rare Secret | ok | gold remap + gold scene, anim; sprite, facing, scene, data and pack OK |
| swsh7-228 | Cresselia | Rare Secret | ok | gold remap + gold scene, anim; sprite, facing, scene, data and pack OK |
