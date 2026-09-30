# Lost Origin audit report

Set list: 247 cards (swsh11: 217, swsh11tg Trainer Gallery: 30). Built: **200** Pokemon cards;
skipped: 47 (every Trainer / Energy, and Eternatus VMAX TG22: its Eternamax sprite is 56 rows = 112 grid px,
over the 110 cap, and the plain Eternatus would be the wrong form).
Outcomes: fixed 18, flagged 25, ok 157, skipped 47.

## How the audit ran (ART_METHOD section 16)
- **Machine checks, every card** (`audit/verify_all.py` -> `work/audit/meta.json`): sprite pixel-exact against the
  vendor sprite in normal AND shiny (shape, outline, colours; the gold remap only at Rare Secret, the 0.55 rainbow
  re-tint only at Rare Rainbow; Radiant Rare = the vendor SHINY sprite on both rolls, no shiny overrides), commons
  plain with no background and flipped exactly as `set.json` `flip_commons`, size <= 140 x 110 grid px, card data
  verbatim with tier == API rarity, the 16-frame anims (normal + shiny) with the final frame == the static art on
  every foil card, and the treatment (builder kind) allowed for the printed rarity (Rare Ultra: the four painted alt
  arts 177 / 180 / 184 / 186 = alt, the rest fullart; Trainer Gallery V / VMAX = alt). Result: 0 failures.
- **Visual review, every card**: three reviewers went through real | ours contact sheets (`work/audit/auditA_*`,
  `auditB_*`, `auditC_*`), with zooms and mask overlays, for facing, form, ghosts, text / logo residue and treatment.
- **Clear errors fixed** in `batch_fixes.py` (highest precedence): see "fixed" rows; before / after in
  `work/audit/fixed_*.png` (real | before | after, `audit/fixed_sheet.py`).
- **Taste calls flagged** for the lookbook: see "flagged" rows.
- **Set-wide fill fix:** `s3lib.pushpull` stops its pyramid at 2 x 2, so a top-level cell with no known pixel came
  out black (dark bleeds in the smooth fills of big-Pokemon cards). `lorlib.pushpull_1x1` runs it to 1 x 1 in every
  Lost Origin process (identical wherever every cell had known pixels); the 53 cards it changed were rebuilt.

## Treatment per rarity (printed rarity = kind (cards))
Common = common (49) | Radiant Rare = radiant (3) | Rare = rare (28) | Rare Holo = holo (21) | Rare Holo V = alt (7) | Rare Holo V = v (12) | Rare Holo VMAX = alt (3) | Rare Holo VMAX = vmax (1) | Rare Holo VSTAR = vstar (6) | Rare Rainbow = rainbow (7) | Rare Secret = gold (4) | Rare Ultra = alt (4) | Rare Ultra = fullart (13) | Trainer Gallery Rare Holo = gallery (11) | Uncommon = uncommon (31)

## Forms read off the scans
giratina-origin 130 131 185 186 201 212 (Origin Forme on every Giratina card), shellos-east 39, gastrodon (West) 102,
basculin-white-striped 44, basculegion (male) 45, enamorus (Incarnate) 82 178 TG18, landorus (Incarnate) 105,
hoopa-unbound 122, perrserker (the species, 129 183 184), stunfisk-galar 127, the Hisuian forms (-hisui: Zorua 75,
Growlithe 83, Zoroark 76 146 147 203 213, Arcanine 84 TG08, Sliggoo 133, Goodra 134 135 136 187 202, Electrode 172),
sneasler 123 and gardevoir 69 / steelix 124 (Radiant: the SHINY sprites), Gigantamax orbeetle-gmax TG13,
centiskorch-gmax TG15, pikachu-gmax TG17 TG29; the Dynamax VMAXes (Kyurem 49 197, Mew TG30) use the plain sprites.
Eternamax Eternatus TG22 is skipped (see above). Pyroar 29 is the female on the card (no vendor sprite): flagged.

## Every card
| id | name | printed rarity | kind | sprite | grid px | anim | outcome | note |
|---|---|---|---|---|---|---|---|---|
| swsh11-1 | Oddish | Common | common | oddish | 34x38 |  | ok |  |
| swsh11-2 | Gloom | Uncommon | uncommon | gloom | 78x48 |  | fixed | LADDER text: the 'Evolves from' plate (STAGE_BOX stops at x 312, the plate at ~x 420) smeared into the top of the art; plate boxed out |
| swsh11-3 | Vileplume | Rare Holo | holo | vileplume | 106x68 | yes | ok |  |
| swsh11-4 | Paras | Common | common | paras | 44x40 |  | ok |  |
| swsh11-5 | Parasect | Rare | rare | parasect | 92x60 |  | fixed | text: the 'Evolves from' plate (STAGE_BOX stops at x 312, the plate at ~x 420) smeared into the top of the art; plate boxed out |
| swsh11-6 | Wurmple | Common | common | wurmple (flipped) | 36x34 |  | ok |  |
| swsh11-7 | Silcoon | Uncommon | uncommon | silcoon (flipped) | 78x48 |  | flagged | facing: Silcoon flipped on the eye right of centre; unflipped arguably matches better |
| swsh11-8 | Beautifly | Rare Holo | holo | beautifly | 94x60 | yes | ok |  |
| swsh11-9 | Cascoon | Uncommon | uncommon | cascoon (flipped) | 78x48 |  | flagged | facing: Cascoon flipped on the eye right of centre; unflipped arguably matches better |
| swsh11-10 | Dustox | Rare | rare | dustox | 92x60 |  | fixed | text: the 'Evolves from' plate (STAGE_BOX stops at x 312, the plate at ~x 420) smeared into the top of the art; plate boxed out |
| swsh11-11 | Seedot | Common | common | seedot | 30x34 |  | ok |  |
| swsh11-12 | Nuzleaf | Uncommon | uncommon | nuzleaf | 82x50 |  | ok |  |
| swsh11-13 | Shiftry | Rare Holo | holo | shiftry | 110x70 | yes | ok |  |
| swsh11-14 | Roselia | Common | common | roselia | 50x44 |  | ok |  |
| swsh11-15 | Roserade | Uncommon | uncommon | roserade | 104x64 |  | ok |  |
| swsh11-16 | Phantump | Common | common | phantump | 50x42 |  | ok |  |
| swsh11-17 | Trevenant | Rare Holo | holo | trevenant | 106x68 | yes | ok |  |
| swsh11-18 | Blipbug | Common | common | blipbug | 36x54 |  | ok |  |
| swsh11-19 | Dottler | Uncommon | uncommon | dottler | 78x48 |  | ok |  |
| swsh11-20 | Orbeetle | Rare Holo | holo | orbeetle | 110x70 | yes | ok |  |
| swsh11-21 | Slugma | Common | common | slugma | 34x42 |  | ok |  |
| swsh11-22 | Magcargo | Rare | rare | magcargo (flipped) | 92x60 |  | fixed | text: the 'Evolves from' plate (STAGE_BOX stops at x 312, the plate at ~x 420) smeared into the top of the art; plate boxed out |
| swsh11-23 | Torkoal | Uncommon | uncommon | torkoal (flipped) | 94x58 |  | ok |  |
| swsh11-24 | Litwick | Common | common | litwick | 26x36 |  | ok |  |
| swsh11-25 | Lampent | Uncommon | uncommon | lampent | 78x48 |  | ok |  |
| swsh11-26 | Chandelure | Rare Holo | holo | chandelure | 112x72 | yes | ok |  |
| swsh11-27 | Delphox V | Rare Holo V | v | delphox | 80x60 | yes | flagged | facing: Delphox V three-quarter, snout turned right; kept unflipped (near-frontal), flip=True arguable |
| swsh11-28 | Litleo | Common | common | litleo (flipped) | 42x40 |  | ok |  |
| swsh11-29 | Pyroar | Rare Holo | holo | pyroar | 94x60 | yes | flagged | form: the card is the FEMALE Pyroar (no mane); the vendor only has the male pyroar sprite |
| swsh11-30 | Poliwag | Common | common | poliwag | 40x30 |  | ok |  |
| swsh11-31 | Poliwhirl | Uncommon | uncommon | poliwhirl | 78x48 |  | ok |  |
| swsh11-32 | Politoed | Rare | rare | politoed (flipped) | 108x70 |  | fixed | text: the 'Evolves from' plate (STAGE_BOX stops at x 312, the plate at ~x 420) smeared into the top of the art; plate boxed out |
| swsh11-33 | Seel | Common | common | seel | 50x46 |  | ok |  |
| swsh11-34 | Dewgong | Rare | rare | dewgong (flipped) | 120x78 |  | fixed | text: the 'Evolves from' plate (STAGE_BOX stops at x 312, the plate at ~x 420) smeared into the top of the art; plate boxed out; FLAG: facing: Dewgong flipped on the face (head and mouth right), but the body layout matches the unflipped sprite |
| swsh11-35 | Horsea | Common | common | horsea | 36x34 |  | ok |  |
| swsh11-36 | Seadra | Uncommon | uncommon | seadra (flipped) | 78x48 |  | ok |  |
| swsh11-37 | Kingdra | Rare Holo | holo | kingdra (flipped) | 112x72 | yes | ok |  |
| swsh11-38 | Luvdisc | Common | common | luvdisc | 24x34 |  | ok |  |
| swsh11-39 | Shellos | Common | common | shellos-east (flipped) | 38x40 |  | fixed | facing: both Shellos on the card face right; added to set.json flip_commons |
| swsh11-40 | Finneon | Common | common | finneon | 40x36 |  | ok |  |
| swsh11-41 | Lumineon | Uncommon | uncommon | lumineon (flipped) | 82x50 |  | ok |  |
| swsh11-42 | Snover | Common | common | snover | 42x40 |  | ok |  |
| swsh11-43 | Abomasnow | Uncommon | uncommon | abomasnow | 104x64 |  | ok |  |
| swsh11-44 | Hisuian Basculin | Common | common | basculin-white-striped | 54x46 |  | ok |  |
| swsh11-45 | Hisuian Basculegion | Rare Holo | holo | basculegion | 94x60 | yes | ok |  |
| swsh11-46 | Ducklett | Common | common | ducklett | 32x38 |  | ok |  |
| swsh11-47 | Swanna | Uncommon | uncommon | swanna | 78x48 |  | ok |  |
| swsh11-48 | Kyurem V | Rare Holo V | v | kyurem (flipped) | 126x110 | yes | ok |  |
| swsh11-49 | Kyurem VMAX | Rare Holo VMAX | vmax | kyurem (flipped) | 106x78 | yes | ok |  |
| swsh11-50 | Cramorant | Rare | rare | cramorant (flipped) | 96x62 |  | ok |  |
| swsh11-51 | Glastrier | Rare Holo | holo | glastrier | 122x78 | yes | ok |  |
| swsh11-52 | Pikachu | Common | common | pikachu | 42x40 |  | ok |  |
| swsh11-53 | Raichu | Rare | rare | raichu | 114x74 |  | fixed | LADDER text: the 'Evolves from' plate (STAGE_BOX stops at x 312, the plate at ~x 420) smeared into the top of the art; plate boxed out |
| swsh11-54 | Electrike | Common | common | electrike | 38x30 |  | ok |  |
| swsh11-55 | Manectric | Rare | rare | manectric (flipped) | 108x70 |  | fixed | text: the 'Evolves from' plate (STAGE_BOX stops at x 312, the plate at ~x 420) smeared into the top of the art; plate boxed out; FLAG: facing: Manectric frontal, flipped on the body trailing left |
| swsh11-56 | Magnezone V | Rare Holo V | v | magnezone | 104x78 | yes | ok |  |
| swsh11-57 | Magnezone VSTAR | Rare Holo VSTAR | vstar | magnezone | 92x70 | yes | ok |  |
| swsh11-58 | Rotom V | Rare Holo V | v | rotom | 80x64 | yes | fixed | ghost: the tip of Rotom's orange head spike and its plasma rim; mask grown |
| swsh11-59 | Tynamo | Common | common | tynamo | 28x22 |  | ok |  |
| swsh11-60 | Eelektrik | Uncommon | uncommon | eelektrik (flipped) | 78x48 |  | ok |  |
| swsh11-61 | Eelektross | Rare | rare | eelektross | 92x60 |  | fixed | text: the 'Evolves from' plate (STAGE_BOX stops at x 312, the plate at ~x 420) smeared into the top of the art; plate boxed out |
| swsh11-62 | Clefairy | Common | common | clefairy | 36x38 |  | ok |  |
| swsh11-63 | Clefable | Rare | rare | clefable | 102x66 |  | fixed | text: the 'Evolves from' plate (STAGE_BOX stops at x 312, the plate at ~x 420) smeared into the top of the art; plate boxed out |
| swsh11-64 | Gastly | Common | common | gastly | 46x42 |  | ok |  |
| swsh11-65 | Haunter | Uncommon | uncommon | haunter (flipped) | 92x56 |  | ok |  |
| swsh11-66 | Gengar | Rare Holo | holo | gengar | 116x74 | yes | fixed | LADDER text: the 'Evolves from' plate (STAGE_BOX stops at x 312, the plate at ~x 420) smeared into the top of the art; plate boxed out |
| swsh11-67 | Mr. Mime | Rare | rare | mr-mime | 110x72 |  | ok |  |
| swsh11-68 | Jynx | Common | common | jynx | 88x66 |  | ok |  |
| swsh11-69 | Radiant Gardevoir | Radiant Rare | radiant | gardevoir | 120x74 | yes | ok |  |
| swsh11-70 | Sableye | Rare Holo | holo | sableye | 100x64 | yes | ok |  |
| swsh11-71 | Mawile | Common | common | mawile | 68x54 |  | ok |  |
| swsh11-72 | Shuppet | Common | common | shuppet | 30x38 |  | ok |  |
| swsh11-73 | Banette | Rare | rare | banette (flipped) | 92x60 |  | fixed | text: the 'Evolves from' plate (STAGE_BOX stops at x 312, the plate at ~x 420) smeared into the top of the art; plate boxed out |
| swsh11-74 | Cresselia | Rare Holo | holo | cresselia | 112x72 | yes | ok |  |
| swsh11-75 | Hisuian Zorua | Common | common | zorua-hisui | 38x44 |  | ok |  |
| swsh11-76 | Hisuian Zoroark | Rare Holo | holo | zoroark-hisui | 106x68 | yes | ok |  |
| swsh11-77 | Inkay | Common | common | inkay | 36x40 |  | ok |  |
| swsh11-78 | Malamar | Rare | rare | malamar | 110x72 |  | fixed | text: the 'Evolves from' plate (STAGE_BOX stops at x 312, the plate at ~x 420) smeared into the top of the art; plate boxed out; FLAG: pose: Malamar is upside down on the card; the upright sprite is used |
| swsh11-79 | Comfey | Rare | rare | comfey | 110x72 |  | ok |  |
| swsh11-80 | Mimikyu | Rare | rare | mimikyu | 98x64 |  | ok |  |
| swsh11-81 | Spectrier | Rare Holo | holo | spectrier | 112x72 | yes | ok |  |
| swsh11-82 | Enamorus V | Rare Holo V | v | enamorus | 108x86 | yes | fixed | ghost: Enamorus's heart-ribbon tail (upper-left arc, lower-right band); mask grown |
| swsh11-83 | Hisuian Growlithe | Common | common | growlithe-hisui (flipped) | 42x44 |  | ok |  |
| swsh11-84 | Hisuian Arcanine | Rare Holo | holo | arcanine-hisui | 128x82 | yes | ok |  |
| swsh11-85 | Poliwrath | Rare | rare | poliwrath | 102x66 |  | ok |  |
| swsh11-86 | Machop | Common | common | machop | 32x40 |  | ok |  |
| swsh11-87 | Machoke | Uncommon | uncommon | machoke | 78x48 |  | ok |  |
| swsh11-88 | Machamp | Rare Holo | holo | machamp | 118x76 | yes | ok |  |
| swsh11-89 | Rhyhorn | Common | common | rhyhorn | 48x40 |  | ok |  |
| swsh11-90 | Rhydon | Uncommon | uncommon | rhydon (flipped) | 130x80 |  | ok |  |
| swsh11-91 | Rhyperior | Rare | rare | rhyperior | 102x66 |  | ok |  |
| swsh11-92 | Aerodactyl V | Rare Holo V | v | aerodactyl | 126x110 | yes | ok |  |
| swsh11-93 | Aerodactyl VSTAR | Rare Holo VSTAR | vstar | aerodactyl (flipped) | 106x70 | yes | ok |  |
| swsh11-94 | Sudowoodo | Common | common | sudowoodo | 60x68 |  | ok |  |
| swsh11-95 | Gligar | Common | common | gligar | 48x48 |  | ok |  |
| swsh11-96 | Gliscor | Rare | rare | gliscor | 92x60 |  | ok |  |
| swsh11-97 | Makuhita | Common | common | makuhita | 36x38 |  | ok |  |
| swsh11-98 | Hariyama | Uncommon | uncommon | hariyama (flipped) | 82x50 |  | ok |  |
| swsh11-99 | Meditite | Common | common | meditite | 34x40 |  | ok |  |
| swsh11-100 | Medicham | Uncommon | uncommon | medicham | 88x54 |  | ok |  |
| swsh11-101 | Relicanth | Uncommon | uncommon | relicanth (flipped) | 88x54 |  | ok |  |
| swsh11-102 | Gastrodon | Uncommon | uncommon | gastrodon | 104x64 |  | flagged | the card shows BOTH Gastrodon (West left, East right): both painted out, the West sprite on the left one |
| swsh11-103 | Mienfoo | Common | common | mienfoo | 36x38 |  | ok |  |
| swsh11-104 | Mienshao | Uncommon | uncommon | mienshao (flipped) | 114x70 |  | ok |  |
| swsh11-105 | Landorus | Rare | rare | landorus | 114x74 |  | ok |  |
| swsh11-106 | Binacle | Common | common | binacle | 32x48 |  | ok |  |
| swsh11-107 | Barbaracle | Rare Holo | holo | barbaracle | 104x66 | yes | ok |  |
| swsh11-108 | Carbink | Uncommon | uncommon | carbink | 78x48 |  | ok |  |
| swsh11-109 | Rockruff | Common | common | rockruff (flipped) | 38x44 |  | ok |  |
| swsh11-110 | Falinks | Common | common | falinks | 62x46 |  | ok |  |
| swsh11-111 | Stonjourner | Rare | rare | stonjourner | 110x72 |  | ok |  |
| swsh11-112 | Spinarak | Common | common | spinarak (flipped) | 36x28 |  | ok |  |
| swsh11-113 | Ariados | Rare | rare | ariados | 92x60 |  | ok |  |
| swsh11-114 | Murkrow | Common | common | murkrow | 38x42 |  | ok |  |
| swsh11-115 | Honchkrow | Rare | rare | honchkrow | 92x60 |  | flagged | facing: Honchkrow three-quarter frontal, kept unflipped |
| swsh11-116 | Seviper | Uncommon | uncommon | seviper (flipped) | 78x48 |  | ok |  |
| swsh11-117 | Spiritomb | Rare | rare | spiritomb | 92x60 |  | ok |  |
| swsh11-118 | Drapion V | Rare Holo V | v | drapion | 140x110 | yes | flagged | facing: Drapion V frontal, unflipped (182, another illustration, is flipped) |
| swsh11-119 | Drapion VSTAR | Rare Holo VSTAR | vstar | drapion | 116x72 | yes | ok |  |
| swsh11-120 | Darkrai | Rare Holo | holo | darkrai | 94x60 | yes | ok |  |
| swsh11-121 | Inkay | Common | common | inkay | 36x40 |  | ok |  |
| swsh11-122 | Hoopa | Rare | rare | hoopa-unbound | 92x60 |  | ok |  |
| swsh11-123 | Radiant Hisuian Sneasler | Radiant Rare | radiant | sneasler | 130x80 | yes | flagged | Radiant Hisuian Sneasler: the colorscripts SHINY sprite (olive, dark head) does not match the card's printed cream / purple shiny |
| swsh11-124 | Radiant Steelix | Radiant Rare | radiant | steelix (flipped) | 132x82 | yes | ok |  |
| swsh11-125 | Bronzor | Common | common | bronzor | 26x32 |  | ok |  |
| swsh11-126 | Bronzong | Uncommon | uncommon | bronzong | 94x58 |  | ok |  |
| swsh11-127 | Galarian Stunfisk | Uncommon | uncommon | stunfisk-galar | 78x48 |  | ok |  |
| swsh11-128 | Magearna | Rare | rare | magearna | 126x82 |  | ok |  |
| swsh11-129 | Galarian Perrserker V | Rare Holo V | v | perrserker | 82x72 | yes | ok |  |
| swsh11-130 | Giratina V | Rare Holo V | v | giratina-origin | 118x100 | yes | ok |  |
| swsh11-131 | Giratina VSTAR | Rare Holo VSTAR | vstar | giratina-origin (flipped) | 100x84 | yes | flagged | LADDER facing: Giratina VSTAR head on the right, body trailing left, face near-frontal; flipped (201 / 212 follow) |
| swsh11-132 | Goomy | Common | common | goomy | 24x28 |  | ok |  |
| swsh11-133 | Hisuian Sliggoo | Uncommon | uncommon | sliggoo-hisui (flipped) | 78x48 |  | fixed | ghost: Hisuian Sliggoo's second horn (a lavender block over the ears); mask grown |
| swsh11-134 | Hisuian Goodra | Rare Holo | holo | goodra-hisui (flipped) | 100x64 | yes | ok |  |
| swsh11-135 | Hisuian Goodra V | Rare Holo V | v | goodra-hisui (flipped) | 88x70 | yes | flagged | facing: Hisuian Goodra V shell left / head right but looking left-down; flipped on the body |
| swsh11-136 | Hisuian Goodra VSTAR | Rare Holo VSTAR | vstar | goodra-hisui (flipped) | 92x66 | yes | ok |  |
| swsh11-137 | Pidgeot V | Rare Holo V | v | pidgeot (flipped) | 94x78 | yes | ok |  |
| swsh11-138 | Lickitung | Common | common | lickitung (flipped) | 46x36 |  | flagged | facing: Lickitung sprawled, flipped on the tongue reaching right (flip_commons, judgement call) |
| swsh11-139 | Lickilicky | Uncommon | uncommon | lickilicky (flipped) | 110x68 |  | ok |  |
| swsh11-140 | Porygon | Common | common | porygon | 38x36 |  | ok |  |
| swsh11-141 | Porygon2 | Uncommon | uncommon | porygon2 (flipped) | 94x58 |  | ok |  |
| swsh11-142 | Porygon-Z | Rare | rare | porygon-z (flipped) | 116x76 |  | flagged | facing: Porygon-Z flipped on the eye / beak, the body layout is mirrored |
| swsh11-143 | Snorlax | Rare Holo | holo | snorlax | 132x84 | yes | flagged | pose: Snorlax lies asleep on the card; the vendor sprite sits frontal |
| swsh11-144 | Aipom | Common | common | aipom | 48x38 |  | flagged | facing: Aipom frontal, leaning right, kept unflipped |
| swsh11-145 | Ambipom | Uncommon | uncommon | ambipom | 88x54 |  | ok |  |
| swsh11-146 | Hisuian Zoroark V | Rare Holo V | v | zoroark-hisui | 92x76 | yes | ok |  |
| swsh11-147 | Hisuian Zoroark VSTAR | Rare Holo VSTAR | vstar | zoroark-hisui | 92x70 | yes | ok |  |
| swsh11-148 | Bouffalant | Rare | rare | bouffalant | 96x62 |  | ok |  |
| swsh11-149 | Komala | Uncommon | uncommon | komala | 78x48 |  | ok |  |
| swsh11-150 | Skwovet | Common | common | skwovet (flipped) | 44x42 |  | flagged | facing: Skwovet frontal, flipped on the tail rising on the left (flip_commons, judgement call) |
| swsh11-151 | Greedent | Rare | rare | greedent | 102x66 |  | ok |  |
| swsh11-152 | Arc Phone | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11-153 | Arezu | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11-154 | Box of Disaster | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11-155 | Colress's Experiment | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11-156 | Damage Pump | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11-157 | Fantina | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11-158 | Iscan | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11-159 | Lady | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11-160 | Lake Acuity | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11-161 | Lost City | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11-162 | Lost Vacuum | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11-163 | Mirage Gate | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11-164 | Miss Fortune Sisters | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11-165 | Panic Mask | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11-166 | Riley | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11-167 | Thorton | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11-168 | Tool Box | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11-169 | Volo | Rare Holo |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11-170 | Windup Arm | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11-171 | Gift Energy | Uncommon |  |  |  |  | skipped | Energy (no Pokemon) |
| swsh11-172 | Hisuian Electrode V | Rare Ultra | fullart | electrode-hisui | 84x66 | yes | flagged | Hisuian Electrode V: one giant ball face on the card; the small sprite sits in a mostly smooth lightning fill |
| swsh11-173 | Delphox V | Rare Ultra | fullart | delphox | 84x66 | yes | ok |  |
| swsh11-174 | Kyurem V | Rare Ultra | fullart | kyurem | 106x68 | yes | ok |  |
| swsh11-175 | Magnezone V | Rare Ultra | fullart | magnezone | 90x70 | yes | ok |  |
| swsh11-176 | Rotom V | Rare Ultra | fullart | rotom | 84x66 | yes | ok |  |
| swsh11-177 | Rotom V | Rare Ultra | alt | rotom | 88x64 | yes | flagged | facing: Rotom V alt art, the face turned right on the card, the frontal sprite kept unflipped; the true-size sprite covers much of the junk-pile painting |
| swsh11-178 | Enamorus V | Rare Ultra | fullart | enamorus | 84x84 | yes | ok |  |
| swsh11-179 | Aerodactyl V | Rare Ultra | fullart | aerodactyl (flipped) | 106x68 | yes | ok |  |
| swsh11-180 | Aerodactyl V | Rare Ultra | alt | aerodactyl (flipped) | 106x68 | yes | ok |  |
| swsh11-181 | Gallade V | Rare Ultra | fullart | gallade (flipped) | 84x72 | yes | ok |  |
| swsh11-182 | Drapion V | Rare Ultra | fullart | drapion (flipped) | 116x66 | yes | flagged | facing: Drapion V full art frontal, flipped on the tail alone |
| swsh11-183 | Galarian Perrserker V | Rare Ultra | fullart | perrserker | 84x68 | yes | ok |  |
| swsh11-184 | Galarian Perrserker V | Rare Ultra | alt | perrserker | 90x68 | yes | ok |  |
| swsh11-185 | Giratina V | Rare Ultra | fullart | giratina-origin | 100x84 | yes | ok |  |
| swsh11-186 | Giratina V | Rare Ultra | alt | giratina-origin (flipped) | 112x84 | yes | ok |  |
| swsh11-187 | Hisuian Goodra V | Rare Ultra | fullart | goodra-hisui | 84x66 | yes | ok |  |
| swsh11-188 | Pidgeot V | Rare Ultra | fullart | pidgeot | 84x74 | yes | ok |  |
| swsh11-189 | Arezu | Rare Ultra |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11-190 | Colress's Experiment | Rare Ultra |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11-191 | Fantina | Rare Ultra |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11-192 | Iscan | Rare Ultra |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11-193 | Lady | Rare Ultra |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11-194 | Miss Fortune Sisters | Rare Ultra |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11-195 | Thorton | Rare Ultra |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11-196 | Volo | Rare Ultra |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11-197 | Kyurem VMAX | Rare Rainbow | rainbow | kyurem (flipped) | 106x68 | yes | ok |  |
| swsh11-198 | Magnezone VSTAR | Rare Rainbow | rainbow | magnezone | 90x70 | yes | ok |  |
| swsh11-199 | Aerodactyl VSTAR | Rare Rainbow | rainbow | aerodactyl (flipped) | 106x68 | yes | ok |  |
| swsh11-200 | Drapion VSTAR | Rare Rainbow | rainbow | drapion | 116x68 | yes | ok |  |
| swsh11-201 | Giratina VSTAR | Rare Rainbow | rainbow | giratina-origin (flipped) | 100x84 | yes | ok |  |
| swsh11-202 | Hisuian Goodra VSTAR | Rare Rainbow | rainbow | goodra-hisui (flipped) | 80x68 | yes | ok |  |
| swsh11-203 | Hisuian Zoroark VSTAR | Rare Rainbow | rainbow | zoroark-hisui | 82x70 | yes | ok |  |
| swsh11-204 | Arezu | Rare Rainbow |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11-205 | Colress's Experiment | Rare Rainbow |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11-206 | Fantina | Rare Rainbow |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11-207 | Iscan | Rare Rainbow |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11-208 | Lady | Rare Rainbow |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11-209 | Miss Fortune Sisters | Rare Rainbow |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11-210 | Thorton | Rare Rainbow |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11-211 | Volo | Rare Rainbow |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11-212 | Giratina VSTAR | Rare Secret | gold | giratina-origin (flipped) | 110x84 | yes | ok |  |
| swsh11-213 | Hisuian Zoroark VSTAR | Rare Secret | gold | zoroark-hisui | 86x70 | yes | flagged | Hisuian Zoroark VSTAR gold: a mostly white / red / grey sprite, the gold remap gives many close mid-golds (lower contrast than 212) |
| swsh11-214 | Box of Disaster | Rare Secret |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11-215 | Collapsed Stadium | Rare Secret |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11-216 | Dark Patch | Rare Secret |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11-217 | Lost Vacuum | Rare Secret |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11tg-TG01 | Parasect | Trainer Gallery Rare Holo | gallery | parasect | 96x64 | yes | ok |  |
| swsh11tg-TG02 | Roserade | Trainer Gallery Rare Holo | gallery | roserade | 96x66 | yes | ok |  |
| swsh11tg-TG03 | Charizard | Trainer Gallery Rare Holo | gallery | charizard (flipped) | 126x84 | yes | ok |  |
| swsh11tg-TG04 | Chandelure | Trainer Gallery Rare Holo | gallery | chandelure | 112x74 | yes | ok |  |
| swsh11tg-TG05 | Pikachu | Trainer Gallery Rare Holo | gallery | pikachu (flipped) | 96x64 | yes | ok |  |
| swsh11tg-TG06 | Gengar | Trainer Gallery Rare Holo | gallery | gengar (flipped) | 114x76 | yes | flagged | facing: Gengar near-frontal, flipped on the face right of the body |
| swsh11tg-TG07 | Banette | Trainer Gallery Rare Holo | gallery | banette (flipped) | 92x64 | yes | ok |  |
| swsh11tg-TG08 | Hisuian Arcanine | Trainer Gallery Rare Holo | gallery | arcanine-hisui | 120x84 | yes | ok |  |
| swsh11tg-TG09 | Spiritomb | Trainer Gallery Rare Holo | gallery | spiritomb | 96x64 | yes | ok |  |
| swsh11tg-TG10 | Snorlax | Trainer Gallery Rare Holo | gallery | snorlax | 130x86 | yes | ok |  |
| swsh11tg-TG11 | Castform | Trainer Gallery Rare Holo | gallery | castform (flipped) | 96x64 | yes | ok |  |
| swsh11tg-TG12 | Orbeetle V | Rare Holo V | alt | orbeetle (flipped) | 96x72 | yes | ok |  |
| swsh11tg-TG13 | Orbeetle VMAX | Rare Holo VMAX | alt | orbeetle-gmax (flipped) | 120x86 | yes | flagged | Orbeetle VMAX: the pink tube / beam kept as G-Max energy (cut_after); a ghost if they are the Pokemon's body |
| swsh11tg-TG14 | Centiskorch V | Rare Holo V | alt | centiskorch (flipped) | 86x66 | yes | ok |  |
| swsh11tg-TG15 | Centiskorch VMAX | Rare Holo VMAX | alt | centiskorch-gmax | 126x96 | yes | ok |  |
| swsh11tg-TG16 | Pikachu V | Rare Holo V | alt | pikachu | 84x64 | yes | fixed | LADDER ghost: the real Pikachu's ear tips (a yellow / black streak by the head); mask grown |
| swsh11tg-TG17 | Pikachu VMAX | Rare Holo VMAX | alt | pikachu-gmax | 140x110 | yes | ok |  |
| swsh11tg-TG18 | Enamorus V | Rare Holo V | alt | enamorus (flipped) | 116x84 | yes | flagged | facing: Enamorus V near-frontal, flipped on the raised arm; the fill round the trainer is busy |
| swsh11tg-TG19 | Gallade V | Rare Holo V | alt | gallade | 94x72 | yes | ok |  |
| swsh11tg-TG20 | Crobat V | Rare Holo V | alt | crobat | 104x66 | yes | ok |  |
| swsh11tg-TG21 | Eternatus V | Rare Holo V | alt | eternatus (flipped) | 136x104 | yes | flagged | facing: Eternatus V near-frontal, flipped on the head right |
| swsh11tg-TG22 | Eternatus VMAX | Rare Holo VMAX |  |  |  |  | skipped | Eternatus VMAX is Eternamax on the card: the eternatus-eternamax sprite is 56 sprite rows = 112 grid px, over the 110 grid-px cap, and it can only be served pixel-exact; the plain eternatus sprite would be the wrong form |
| swsh11tg-TG23 | Adventurer's Discovery | Rare Ultra |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11tg-TG24 | Boss's Orders | Rare Ultra |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11tg-TG25 | Cook | Rare Ultra |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11tg-TG26 | Kabu | Rare Ultra |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11tg-TG27 | Nessa | Rare Ultra |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11tg-TG28 | Opal | Rare Ultra |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh11tg-TG29 | Pikachu VMAX | Rare Secret | gold | pikachu-gmax | 104x108 | yes | flagged | facing: G-Max Pikachu VMAX gold, unflipped (head in profile left) |
| swsh11tg-TG30 | Mew VMAX | Rare Secret | gold | mew (flipped) | 72x66 | yes | flagged | LADDER facing: Mew VMAX head top right, body / tail curling left; flipped |
