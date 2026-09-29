# Crown Zenith audit report

Set list: 230 cards (swsh12pt5: 160, swsh12pt5gg Galarian Gallery: 70). Built: **183** Pokemon cards;
skipped: 47 (Trainers / Energy; no Pokemon lacks a sprite once Perrserker 85 took `perrserker`).
Outcomes: fixed 10, flagged 19, ok 154, skipped 47.

## How the audit ran (ART_METHOD section 16)
- **Machine checks, every card** (`audit/verify_all.py` -> `work/audit/meta.json`): sprite pixel-exact against the
  vendor sprite in normal AND shiny (shape, outline, colours; the gold remap only at Rare Secret gold), commons plain
  with no background and flipped exactly as `set.json` `flip_commons`, size <= 140 x 110 grid px (widest 138, GG44 Mewtwo VSTAR;
  tallest 108, Zamazenta V 98), card data verbatim with tier == API rarity, the 16-frame anims (normal + shiny) with the
  final frame == the static art on every foil card, and the treatment (builder kind) allowed for the printed rarity.
  Result: 0 failures.
- **Visual review, every card**: three reviewers went through real | ours contact sheets (`work/audit/*.png`) for
  facing, form (regional / Gigantamax / Crowned / Origin / Unbound / Sky / Resolute / Low Key / Midnight), ghosts,
  text / logo residue and treatment.
- **Clear errors fixed** in `batch_fixes.py` (highest precedence): see "fixed" rows. All uncommon / rare / holo / radiant cards and ladder 2, 3, 36, 20 were rebuilt after two shared fixes in czcards: the SWSH window's own silver border (a pale strip down the right edge of the art) and the stage icon's plate below STAGE_BOX (a pale blob top-left on evolved rares: 9, 25, 43, 78, 80, 82, 118) are now boxed out, and everything outside the art window is boxed out before the texture fill (the holo batch had found name-bar / stat-line letters mirrored into the fill).
- **Taste calls flagged** for the lookbook: see "flagged" rows.

## Treatment per rarity
Common = plain sprite (37) | Uncommon = Shelgon matte (17) | Rare = Altaria matte (22) | Rare Holo = Salamence holo (13) |
Rare Holo V = Sylveon V (17) | Rare Holo VMAX = Vaporeon VMAX (5) | Rare Holo VSTAR = NEW vstar (8) |
Radiant Rare = NEW radiant (3) | Trainer Gallery Rare Holo = NEW gallery (34) | Galarian Gallery V / VMAX / VSTAR =
Umbreon 215 alt-art painting at the printed tier (9 + 3 + 10) | Rare Secret = gold remap (GG67-70) and the painted
alt art (Pikachu 160).

## Forms read off the scans
lycanroc-midnight 74, shaymin-sky 115, zacian-crowned 94 95 96, zamazenta-crowned 97 98 99 (Hero on GG48 / GG54),
hoopa-unbound 83 GG53, giratina-origin GG69, palkia-origin GG67, dialga-origin GG68, keldeo-resolute GG07,
toxtricity-low-key GG09, hatterene-gmax 66 GG47, duraludon-gmax 104, the Hisuian / Galarian regionals, perrserker 85.
Frontal poses were kept unflipped and are listed as ambiguous in the batch reports, not flagged.

## Every card
| id | name | printed rarity | kind | sprite | grid px | anim | outcome | note |
|---|---|---|---|---|---|---|---|---|
| swsh12pt5-1 | Oddish | Common | common | oddish (flipped) | 34x38 |  | ok |  |
| swsh12pt5-2 | Gloom | Uncommon | uncommon | gloom (flipped) | 78x48 |  | ok |  |
| swsh12pt5-3 | Bellossom | Rare | rare | bellossom | 92x60 |  | ok |  |
| swsh12pt5-4 | Tangela | Common | common | tangela | 38x36 |  | ok |  |
| swsh12pt5-5 | Tangrowth | Rare | rare | tangrowth | 100x66 |  | ok |  |
| swsh12pt5-6 | Scyther | Common | common | scyther (flipped) | 74x78 |  | ok |  |
| swsh12pt5-7 | Sunkern | Common | common | sunkern (flipped) | 26x36 |  | ok |  |
| swsh12pt5-8 | Yanma | Common | common | yanma (flipped) | 56x32 |  | ok |  |
| swsh12pt5-9 | Yanmega | Rare | rare | yanmega (flipped) | 92x60 |  | ok |  |
| swsh12pt5-10 | Kricketot | Common | common | kricketot | 34x44 |  | ok |  |
| swsh12pt5-11 | Cherubi | Common | common | cherubi | 36x36 |  | ok |  |
| swsh12pt5-12 | Carnivine | Uncommon | uncommon | carnivine | 82x50 |  | ok |  |
| swsh12pt5-13 | Leafeon V | Rare Holo V | v | leafeon | 98x70 | yes | ok |  |
| swsh12pt5-14 | Leafeon VSTAR | Rare Holo VSTAR | vstar | leafeon | 92x68 | yes | ok |  |
| swsh12pt5-15 | Grubbin | Common | common | grubbin (flipped) | 34x26 |  | ok |  |
| swsh12pt5-16 | Zarude | Rare Holo | holo | zarude | 98x62 | yes | ok |  |
| swsh12pt5-17 | Calyrex | Rare Holo | holo | calyrex | 118x76 | yes | ok |  |
| swsh12pt5-18 | Charizard V | Rare Holo V | v | charizard (flipped) | 118x104 | yes | ok |  |
| swsh12pt5-19 | Charizard VSTAR | Rare Holo VSTAR | vstar | charizard (flipped) | 116x84 | yes | ok |  |
| swsh12pt5-20 | Radiant Charizard | Radiant Rare | radiant | charizard | 132x82 | yes | flagged | Radiant: the real print is the SHINY Pokemon (all three Radiants); we serve the regular sprite, shiny on the shiny roll (decide) |
| swsh12pt5-21 | Entei | Rare Holo | holo | entei (flipped) | 116x74 | yes | ok |  |
| swsh12pt5-22 | Simisear V | Rare Holo V | v | simisear | 80x68 | yes | ok |  |
| swsh12pt5-23 | Simisear VSTAR | Rare Holo VSTAR | vstar | simisear | 92x62 | yes | ok |  |
| swsh12pt5-24 | Larvesta | Common | common | larvesta | 40x38 |  | ok |  |
| swsh12pt5-25 | Volcarona | Rare | rare | volcarona (flipped) | 98x64 |  | ok |  |
| swsh12pt5-26 | Volcanion | Rare Holo | holo | volcanion | 134x86 | yes | ok |  |
| swsh12pt5-27 | Salandit | Common | common | salandit | 38x36 |  | ok |  |
| swsh12pt5-28 | Salazzle | Uncommon | uncommon | salazzle | 108x66 |  | ok |  |
| swsh12pt5-29 | Seel | Common | common | seel (flipped) | 50x46 |  | ok |  |
| swsh12pt5-30 | Galarian Mr. Mime | Common | common | mr-mime-galar | 66x64 |  | ok |  |
| swsh12pt5-31 | Wailmer | Common | common | wailmer | 66x48 |  | ok |  |
| swsh12pt5-32 | Wailord | Rare | rare | wailord | 110x72 |  | ok |  |
| swsh12pt5-33 | Corphish | Common | common | corphish | 42x38 |  | ok |  |
| swsh12pt5-34 | Snorunt | Common | common | snorunt | 30x38 |  | ok |  |
| swsh12pt5-35 | Luvdisc | Common | common | luvdisc | 24x34 |  | ok |  |
| swsh12pt5-36 | Kyogre | Rare Holo | holo | kyogre (flipped) | 124x80 | yes | flagged | LADDER Kyogre: small blue remnants of the back and left fin in the fill |
| swsh12pt5-37 | Kyogre V | Rare Holo V | v | kyogre | 132x106 | yes | flagged | Kyogre V: smooth fill shows a dark band where the dorsal fin was, and a blue streak at the right fin |
| swsh12pt5-38 | Glaceon V | Rare Holo V | v | glaceon (flipped) | 96x84 | yes | fixed | ghosts: Glaceon's front paw and head ribbon were left in the fill; mask grown over both |
| swsh12pt5-39 | Shinx | Common | common | shinx | 48x42 |  | ok |  |
| swsh12pt5-40 | Shinx | Common | common | shinx | 48x42 |  | ok |  |
| swsh12pt5-41 | Luxio | Uncommon | uncommon | luxio | 78x48 |  | ok |  |
| swsh12pt5-42 | Luxio | Uncommon | uncommon | luxio (flipped) | 78x48 |  | ok |  |
| swsh12pt5-43 | Luxray | Rare | rare | luxray (flipped) | 98x64 |  | ok |  |
| swsh12pt5-44 | Luxray | Rare | rare | luxray (flipped) | 98x64 |  | fixed | facing: Luxray's head and open mouth point right; flip=True |
| swsh12pt5-45 | Rotom V | Rare Holo V | v | rotom | 80x64 | yes | flagged | Rotom V: the filled hole reads as a flat cyan diamond; small sprite on a card-filling Rotom |
| swsh12pt5-46 | Rotom VSTAR | Rare Holo VSTAR | vstar | rotom | 92x62 | yes | ok |  |
| swsh12pt5-47 | Emolga | Common | common | emolga | 76x52 |  | ok |  |
| swsh12pt5-48 | Eelektrik | Uncommon | uncommon | eelektrik | 78x48 |  | ok |  |
| swsh12pt5-49 | Helioptile | Common | common | helioptile | 36x34 |  | ok |  |
| swsh12pt5-50 | Heliolisk | Rare | rare | heliolisk | 98x64 |  | ok |  |
| swsh12pt5-51 | Radiant Charjabug | Radiant Rare | radiant | charjabug (flipped) | 98x60 | yes | flagged | Radiant: shiny on the real print (see 20) |
| swsh12pt5-52 | Zeraora | Rare | rare | zeraora | 104x68 |  | ok |  |
| swsh12pt5-53 | Zeraora V | Rare Holo V | v | zeraora | 102x90 | yes | ok |  |
| swsh12pt5-54 | Zeraora VMAX | Rare Holo VMAX | vmax | zeraora | 92x78 | yes | ok |  |
| swsh12pt5-55 | Zeraora VSTAR | Rare Holo VSTAR | vstar | zeraora | 104x70 | yes | ok |  |
| swsh12pt5-56 | Pincurchin | Uncommon | uncommon | pincurchin | 78x48 |  | ok |  |
| swsh12pt5-57 | Exeggcute | Common | common | exeggcute | 48x36 |  | ok |  |
| swsh12pt5-58 | Exeggutor | Rare | rare | exeggutor | 116x90 |  | flagged | Exeggutor's heads look up-right on the card; the sprite is near-frontal (kept) |
| swsh12pt5-59 | Mewtwo | Rare Holo | holo | mewtwo | 138x88 | yes | ok |  |
| swsh12pt5-60 | Mew V | Rare Holo V | v | mew (flipped) | 80x70 | yes | fixed | ghost: Mew's foot was left in the fill; mask grown |
| swsh12pt5-61 | Girafarig | Uncommon | uncommon | girafarig | 82x50 |  | ok |  |
| swsh12pt5-62 | Lunatone | Uncommon | uncommon | lunatone (flipped) | 84x52 |  | ok |  |
| swsh12pt5-63 | Dusclops | Uncommon | uncommon | dusclops | 84x52 |  | ok |  |
| swsh12pt5-64 | Tapu Lele | Rare Holo | holo | tapu-lele | 122x78 | yes | ok |  |
| swsh12pt5-65 | Hatterene V | Rare Holo V | v | hatterene | 88x76 | yes | ok |  |
| swsh12pt5-66 | Hatterene VMAX | Rare Holo VMAX | vmax | hatterene-gmax | 92x92 | yes | ok |  |
| swsh12pt5-67 | Enamorus | Rare | rare | enamorus | 126x82 |  | ok |  |
| swsh12pt5-68 | Graveler | Uncommon | uncommon | graveler | 78x48 |  | ok |  |
| swsh12pt5-69 | Solrock | Uncommon | uncommon | solrock | 108x66 |  | ok |  |
| swsh12pt5-70 | Baltoy | Common | common | baltoy | 32x42 |  | ok |  |
| swsh12pt5-71 | Riolu | Common | common | riolu | 36x36 |  | ok |  |
| swsh12pt5-72 | Pancham | Common | common | pancham | 30x38 |  | ok |  |
| swsh12pt5-73 | Rockruff | Common | common | rockruff | 38x44 |  | ok |  |
| swsh12pt5-74 | Lycanroc | Rare | rare | lycanroc-midnight | 108x70 |  | ok |  |
| swsh12pt5-75 | Koffing | Common | common | koffing | 50x52 |  | ok |  |
| swsh12pt5-76 | Absol | Rare Holo | holo | absol | 116x74 | yes | ok |  |
| swsh12pt5-77 | Purrloin | Common | common | purrloin | 42x44 |  | ok |  |
| swsh12pt5-78 | Liepard | Rare | rare | liepard (flipped) | 114x74 |  | ok |  |
| swsh12pt5-79 | Krokorok | Uncommon | uncommon | krokorok (flipped) | 78x48 |  | ok |  |
| swsh12pt5-80 | Pangoro | Rare | rare | pangoro (flipped) | 108x70 |  | ok |  |
| swsh12pt5-81 | Skrelp | Common | common | skrelp | 36x42 |  | flagged | facing ambiguous (near-frontal Skrelp, snout down); kept unflipped, reviewers lean flip |
| swsh12pt5-82 | Dragalge | Rare | rare | dragalge | 104x68 |  | ok |  |
| swsh12pt5-83 | Hoopa | Rare Holo | holo | hoopa-unbound | 94x60 | yes | flagged | Hoopa is drawn as Hoopa Unbound; sprite hoopa-unbound (confirm) |
| swsh12pt5-84 | Galarian Meowth | Common | common | meowth-galar | 42x42 |  | ok |  |
| swsh12pt5-85 | Galarian Perrserker | Rare | rare | perrserker | 102x66 |  | ok |  |
| swsh12pt5-86 | Scizor | Rare | rare | scizor | 114x74 |  | ok |  |
| swsh12pt5-87 | Aron | Common | common | aron | 32x24 |  | ok |  |
| swsh12pt5-88 | Lairon | Uncommon | uncommon | lairon (flipped) | 78x48 |  | ok |  |
| swsh12pt5-89 | Aggron | Rare Holo | holo | aggron | 110x70 | yes | ok |  |
| swsh12pt5-90 | Metang | Uncommon | uncommon | metang | 78x48 |  | ok |  |
| swsh12pt5-91 | Pawniard | Common | common | pawniard | 28x40 |  | ok |  |
| swsh12pt5-92 | Pawniard | Common | common | pawniard (flipped) | 28x40 |  | flagged | facing: the two reviewers disagreed (face turned right vs blade pointing left); kept flipped (flip_commons) |
| swsh12pt5-93 | Bisharp | Uncommon | uncommon | bisharp (flipped) | 110x68 |  | fixed | facing: Bisharp lunges left on the card; flip=True |
| swsh12pt5-94 | Zacian | Rare Holo | holo | zacian-crowned | 136x96 | yes | ok |  |
| swsh12pt5-95 | Zacian V | Rare Holo V | v | zacian-crowned (flipped) | 122x100 | yes | ok |  |
| swsh12pt5-96 | Zacian VSTAR | Rare Holo VSTAR | vstar | zacian-crowned (flipped) | 104x76 | yes | fixed | form: the card is Crowned Sword Zacian; sprite zacian-crowned (flip=True), crop refit to the sprite |
| swsh12pt5-97 | Zamazenta | Rare Holo | holo | zamazenta-crowned | 132x84 | yes | ok |  |
| swsh12pt5-98 | Zamazenta V | Rare Holo V | v | zamazenta-crowned | 126x108 | yes | ok |  |
| swsh12pt5-99 | Zamazenta VSTAR | Rare Holo VSTAR | vstar | zamazenta-crowned | 122x82 | yes | fixed | form + facing: Crowned Shield Zamazenta, head left; sprite zamazenta-crowned, flip=False, crop refit |
| swsh12pt5-100 | Rayquaza V | Rare Holo V | v | rayquaza | 124x108 | yes | flagged | Rayquaza V: small dark-teal patch where the body was (x 115-180, y 465-520) |
| swsh12pt5-101 | Rayquaza VMAX | Rare Holo VMAX | vmax | rayquaza | 102x104 | yes | flagged | Rayquaza VMAX: texture=False leaves a muddy green-grey haze over the right half |
| swsh12pt5-102 | Rayquaza VMAX | Rare Holo VMAX | vmax | rayquaza | 102x104 | yes | flagged | Rayquaza VMAX: as 101 |
| swsh12pt5-103 | Duraludon V | Rare Holo V | v | duraludon | 90x78 | yes | ok |  |
| swsh12pt5-104 | Duraludon VMAX | Rare Holo VMAX | vmax | duraludon-gmax | 92x102 | yes | ok |  |
| swsh12pt5-105 | Radiant Eternatus | Radiant Rare | radiant | eternatus | 136x102 | yes | flagged | Radiant: shiny on the real print (see 20) |
| swsh12pt5-106 | Tauros | Rare | rare | tauros | 122x80 |  | ok |  |
| swsh12pt5-107 | Ditto | Rare Holo | holo | ditto | 58x36 | yes | ok |  |
| swsh12pt5-108 | Eevee V | Rare Holo V | v | eevee | 80x70 | yes | ok |  |
| swsh12pt5-109 | Snorlax | Rare | rare | snorlax | 128x84 |  | ok |  |
| swsh12pt5-110 | Starly | Common | common | starly | 38x36 |  | ok |  |
| swsh12pt5-111 | Bidoof | Common | common | bidoof | 40x32 |  | ok |  |
| swsh12pt5-112 | Chatot | Common | common | chatot | 40x44 |  | ok |  |
| swsh12pt5-113 | Regigigas V | Rare Holo V | v | regigigas | 124x108 | yes | ok |  |
| swsh12pt5-114 | Regigigas VSTAR | Rare Holo VSTAR | vstar | regigigas | 114x76 | yes | ok |  |
| swsh12pt5-115 | Shaymin | Uncommon | uncommon | shaymin-sky | 78x48 |  | ok |  |
| swsh12pt5-116 | Stoutland V | Rare Holo V | v | stoutland (flipped) | 86x76 | yes | fixed | ghosts: Stoutland's right ear, neck fur and moustache were left in the fill; mask grown |
| swsh12pt5-117 | Yungoos | Common | common | yungoos | 50x32 |  | ok |  |
| swsh12pt5-118 | Gumshoos | Rare | rare | gumshoos (flipped) | 92x60 |  | fixed | facing: Gumshoos faces right; flip=True |
| swsh12pt5-119 | Oranguru | Rare | rare | oranguru (flipped) | 102x66 |  | ok |  |
| swsh12pt5-120 | Greedent V | Rare Holo V | v | greedent (flipped) | 82x72 | yes | ok |  |
| swsh12pt5-121 | Wooloo | Common | common | wooloo | 40x38 |  | ok |  |
| swsh12pt5-122 | Dubwool | Rare | rare | dubwool | 98x64 |  | ok |  |
| swsh12pt5-123 | Bea | Rare Holo |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh12pt5-124 | Bede | Rare Holo |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh12pt5-125 | Crushing Hammer | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh12pt5-126 | Digging Duo | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh12pt5-127 | Energy Retrieval | Common |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh12pt5-128 | Energy Search | Common |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh12pt5-129 | Energy Switch | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh12pt5-130 | Friends in Hisui | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh12pt5-131 | Friends in Sinnoh | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh12pt5-132 | Great Ball | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh12pt5-133 | Hop | Rare Holo |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh12pt5-134 | Leon | Rare Holo |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh12pt5-135 | Lost Vacuum | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh12pt5-136 | Nessa | Rare Holo |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh12pt5-137 | Poké Ball | Common |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh12pt5-138 | Pokémon Catcher | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh12pt5-139 | Potion | Common |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh12pt5-140 | Raihan | Rare Holo |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh12pt5-141 | Rare Candy | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh12pt5-142 | Rescue Carrier | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh12pt5-143 | Sky Seal Stone | Rare Holo |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh12pt5-144 | Switch | Common |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh12pt5-145 | Trekking Shoes | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh12pt5-146 | Ultra Ball | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh12pt5-147 | Elesa's Sparkle | Rare Ultra |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh12pt5-148 | Friends in Hisui | Rare Ultra |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh12pt5-149 | Friends in Sinnoh | Rare Ultra |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh12pt5-150 | Professor's Research | Rare Ultra |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh12pt5-151 | Volo | Rare Ultra |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh12pt5-152 | Grass Energy | Rare Ultra |  |  |  |  | skipped | Energy (no Pokemon) |
| swsh12pt5-153 | Fire Energy | Rare Ultra |  |  |  |  | skipped | Energy (no Pokemon) |
| swsh12pt5-154 | Water Energy | Rare Ultra |  |  |  |  | skipped | Energy (no Pokemon) |
| swsh12pt5-155 | Lightning Energy | Rare Ultra |  |  |  |  | skipped | Energy (no Pokemon) |
| swsh12pt5-156 | Psychic Energy | Rare Ultra |  |  |  |  | skipped | Energy (no Pokemon) |
| swsh12pt5-157 | Fighting Energy | Rare Ultra |  |  |  |  | skipped | Energy (no Pokemon) |
| swsh12pt5-158 | Darkness Energy | Rare Ultra |  |  |  |  | skipped | Energy (no Pokemon) |
| swsh12pt5-159 | Metal Energy | Rare Ultra |  |  |  |  | skipped | Energy (no Pokemon) |
| swsh12pt5-160 | Pikachu | Rare Secret | alt | pikachu | 88x64 | yes | ok |  |
| swsh12pt5gg-GG01 | Hisuian Voltorb | Trainer Gallery Rare Holo | gallery | voltorb-hisui | 92x64 | yes | ok |  |
| swsh12pt5gg-GG02 | Kricketune | Trainer Gallery Rare Holo | gallery | kricketune | 98x64 | yes | ok |  |
| swsh12pt5gg-GG03 | Magmortar | Trainer Gallery Rare Holo | gallery | magmortar (flipped) | 96x68 | yes | fixed | facing: Magmortar aims left at the campfire; flip=True |
| swsh12pt5gg-GG04 | Oricorio | Trainer Gallery Rare Holo | gallery | oricorio | 98x64 | yes | ok |  |
| swsh12pt5gg-GG05 | Lapras | Trainer Gallery Rare Holo | gallery | lapras | 102x78 | yes | ok |  |
| swsh12pt5gg-GG06 | Manaphy | Trainer Gallery Rare Holo | gallery | manaphy | 98x64 | yes | ok |  |
| swsh12pt5gg-GG07 | Keldeo | Trainer Gallery Rare Holo | gallery | keldeo-resolute (flipped) | 104x74 | yes | ok |  |
| swsh12pt5gg-GG08 | Electivire | Trainer Gallery Rare Holo | gallery | electivire | 98x68 | yes | ok |  |
| swsh12pt5gg-GG09 | Toxtricity | Trainer Gallery Rare Holo | gallery | toxtricity-low-key (flipped) | 120x78 | yes | ok |  |
| swsh12pt5gg-GG10 | Mew | Trainer Gallery Rare Holo | gallery | mew (flipped) | 98x64 | yes | ok |  |
| swsh12pt5gg-GG11 | Lunatone | Trainer Gallery Rare Holo | gallery | lunatone (flipped) | 90x64 | yes | ok |  |
| swsh12pt5gg-GG12 | Deoxys | Trainer Gallery Rare Holo | gallery | deoxys | 84x64 | yes | ok |  |
| swsh12pt5gg-GG13 | Diancie | Trainer Gallery Rare Holo | gallery | diancie | 128x84 | yes | ok |  |
| swsh12pt5gg-GG14 | Comfey | Trainer Gallery Rare Holo | gallery | comfey | 114x74 | yes | ok |  |
| swsh12pt5gg-GG15 | Solrock | Trainer Gallery Rare Holo | gallery | solrock | 104x68 | yes | ok |  |
| swsh12pt5gg-GG16 | Absol | Trainer Gallery Rare Holo | gallery | absol | 110x76 | yes | ok |  |
| swsh12pt5gg-GG17 | Thievul | Trainer Gallery Rare Holo | gallery | thievul (flipped) | 108x70 | yes | ok |  |
| swsh12pt5gg-GG18 | Magnezone | Trainer Gallery Rare Holo | gallery | magnezone (flipped) | 108x70 | yes | ok |  |
| swsh12pt5gg-GG19 | Altaria | Trainer Gallery Rare Holo | gallery | altaria | 100x66 | yes | ok |  |
| swsh12pt5gg-GG20 | Latias | Trainer Gallery Rare Holo | gallery | latias (flipped) | 96x64 | yes | ok |  |
| swsh12pt5gg-GG21 | Hisuian Goodra | Trainer Gallery Rare Holo | gallery | goodra-hisui | 100x66 | yes | ok |  |
| swsh12pt5gg-GG22 | Ditto | Trainer Gallery Rare Holo | gallery | ditto | 86x64 | yes | ok |  |
| swsh12pt5gg-GG23 | Dunsparce | Trainer Gallery Rare Holo | gallery | dunsparce | 96x64 | yes | flagged | Dunsparce: two more Dunsparce on the shelves stay as scenery (the card's own is the one in bed) |
| swsh12pt5gg-GG24 | Miltank | Trainer Gallery Rare Holo | gallery | miltank | 108x72 | yes | ok |  |
| swsh12pt5gg-GG25 | Bibarel | Trainer Gallery Rare Holo | gallery | bibarel (flipped) | 96x64 | yes | ok |  |
| swsh12pt5gg-GG26 | Riolu | Trainer Gallery Rare Holo | gallery | riolu (flipped) | 84x64 | yes | ok |  |
| swsh12pt5gg-GG27 | Swablu | Trainer Gallery Rare Holo | gallery | swablu (flipped) | 84x64 | yes | ok |  |
| swsh12pt5gg-GG28 | Duskull | Trainer Gallery Rare Holo | gallery | duskull | 84x64 | yes | ok |  |
| swsh12pt5gg-GG29 | Bidoof | Trainer Gallery Rare Holo | gallery | bidoof (flipped) | 98x64 | yes | ok |  |
| swsh12pt5gg-GG30 | Pikachu | Trainer Gallery Rare Holo | gallery | pikachu | 98x64 | yes | ok |  |
| swsh12pt5gg-GG31 | Turtwig | Trainer Gallery Rare Holo | gallery | turtwig | 86x64 | yes | ok |  |
| swsh12pt5gg-GG32 | Paras | Trainer Gallery Rare Holo | gallery | paras | 84x64 | yes | ok |  |
| swsh12pt5gg-GG33 | Poochyena | Trainer Gallery Rare Holo | gallery | poochyena | 86x64 | yes | ok |  |
| swsh12pt5gg-GG34 | Mareep | Trainer Gallery Rare Holo | gallery | mareep | 86x64 | yes | ok |  |
| swsh12pt5gg-GG35 | Leafeon VSTAR | Rare Holo VSTAR | alt | leafeon | 106x68 | yes | ok |  |
| swsh12pt5gg-GG36 | Entei V | Rare Holo V | alt | entei | 102x76 | yes | ok |  |
| swsh12pt5gg-GG37 | Simisear VSTAR | Rare Holo VSTAR | alt | simisear | 104x64 | yes | ok |  |
| swsh12pt5gg-GG38 | Suicune V | Rare Holo V | alt | suicune (flipped) | 108x82 | yes | ok |  |
| swsh12pt5gg-GG39 | Lumineon V | Rare Holo V | alt | lumineon | 88x64 | yes | ok |  |
| swsh12pt5gg-GG40 | Glaceon VSTAR | Rare Holo VSTAR | alt | glaceon | 100x66 | yes | ok |  |
| swsh12pt5gg-GG41 | Raikou V | Rare Holo V | alt | raikou | 100x76 | yes | ok |  |
| swsh12pt5gg-GG42 | Zeraora VMAX | Rare Holo VMAX | alt | zeraora | 92x70 | yes | flagged | Zeraora VMAX: sprite hides the sleeping Pachirisu; the fill is flat (Zeraora covers 43% of the art) |
| swsh12pt5gg-GG43 | Zeraora VSTAR | Rare Holo VSTAR | alt | zeraora | 112x70 | yes | ok |  |
| swsh12pt5gg-GG44 | Mewtwo VSTAR | Rare Holo VSTAR | alt | mewtwo (flipped) | 136x90 | yes | fixed | facing: Mewtwo lunges right at Charizard; flip=True |
| swsh12pt5gg-GG45 | Deoxys VMAX | Rare Holo VMAX | alt | deoxys | 84x64 | yes | flagged | Deoxys VMAX: the saucer above has a Deoxys-like face (kept as scenery) |
| swsh12pt5gg-GG46 | Deoxys VSTAR | Rare Holo VSTAR | alt | deoxys (flipped) | 102x64 | yes | ok |  |
| swsh12pt5gg-GG47 | Hatterene VMAX | Rare Holo VMAX | alt | hatterene-gmax (flipped) | 120x92 | yes | ok |  |
| swsh12pt5gg-GG48 | Zacian V | Rare Holo V | alt | zacian | 106x76 | yes | ok |  |
| swsh12pt5gg-GG49 | Drapion V | Rare Holo V | alt | drapion (flipped) | 116x64 | yes | flagged | Drapion V: the sprite hides the left Skorupi (a clay-figure photo card, given the painting treatment) |
| swsh12pt5gg-GG50 | Darkrai VSTAR | Rare Holo VSTAR | alt | darkrai | 98x64 | yes | ok |  |
| swsh12pt5gg-GG51 | Hisuian Samurott V | Rare Holo V | alt | samurott-hisui | 100x76 | yes | ok |  |
| swsh12pt5gg-GG52 | Hisuian Samurott VSTAR | Rare Holo VSTAR | alt | samurott-hisui | 114x76 | yes | ok |  |
| swsh12pt5gg-GG53 | Hoopa V | Rare Holo V | alt | hoopa-unbound | 88x64 | yes | flagged | Hoopa V is drawn as Hoopa Unbound; sprite hoopa-unbound (confirm) |
| swsh12pt5gg-GG54 | Zamazenta V | Rare Holo V | alt | zamazenta (flipped) | 108x82 | yes | ok |  |
| swsh12pt5gg-GG55 | Regigigas VSTAR | Rare Holo VSTAR | alt | regigigas | 114x66 | yes | ok |  |
| swsh12pt5gg-GG56 | Hisuian Zoroark VSTAR | Rare Holo VSTAR | alt | zoroark-hisui | 106x70 | yes | ok |  |
| swsh12pt5gg-GG57 | Adaman | Rare Ultra |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh12pt5gg-GG58 | Cheren's Care | Rare Ultra |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh12pt5gg-GG59 | Colress's Experiment | Rare Ultra |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh12pt5gg-GG60 | Cynthia's Ambition | Rare Ultra |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh12pt5gg-GG61 | Gardenia's Vigor | Rare Ultra |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh12pt5gg-GG62 | Grant | Rare Ultra |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh12pt5gg-GG63 | Irida | Rare Ultra |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh12pt5gg-GG64 | Melony | Rare Ultra |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh12pt5gg-GG65 | Raihan | Rare Ultra |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh12pt5gg-GG66 | Roxanne | Rare Ultra |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh12pt5gg-GG67 | Origin Forme Palkia VSTAR | Rare Secret | gold | palkia-origin | 112x92 | yes | ok |  |
| swsh12pt5gg-GG68 | Origin Forme Dialga VSTAR | Rare Secret | gold | dialga-origin | 128x106 | yes | flagged | vendor dialga-origin: one px (row 20, col 33) is set in the regular sprite but empty in the shiny; batch_secret patches the SHINY to the regular colour there (the regular stays pixel-exact) |
| swsh12pt5gg-GG69 | Giratina VSTAR | Rare Secret | gold | giratina-origin | 108x84 | yes | ok |  |
| swsh12pt5gg-GG70 | Arceus VSTAR | Rare Secret | gold | arceus | 76x66 | yes | ok |  |
