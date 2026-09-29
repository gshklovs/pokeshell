# Brilliant Stars audit report

Set list: 216 cards (swsh9: 186, swsh9tg Trainer Gallery: 30). Built: **175** Pokemon cards;
skipped: 41 (Trainers / Energy, and Rapid Strike Urshifu V TG20: no sprite for its form).
Outcomes: fixed 16, flagged 20, ok 139, skipped 41.

## How the audit ran (ART_METHOD section 16)
- **Machine checks, every card** (`audit/verify_all.py` -> `work/audit/meta.json`): sprite pixel-exact against the
  vendor sprite in normal AND shiny (shape, outline, colours; the gold remap only at Rare Secret, the 0.55 rainbow
  re-tint only at Rare Rainbow), commons plain with no background and flipped exactly as `set.json` `flip_commons`,
  size <= 140 x 110 grid px, card data verbatim with tier == API rarity, the 16-frame anims (normal + shiny) with
  the final frame == the static art on every foil card, and the treatment (builder kind) allowed for the printed
  rarity (Rare Ultra: the four painted alt arts 154 / 156 / 162 / 166 = alt, the rest fullart; Trainer Gallery
  V / VMAX = alt). Result: 0 failures.
- **Visual review, every card**: three reviewers went through real | ours contact sheets (`work/audit/*.png`), with
  zooms and mask overlays, for facing, form, ghosts, text / logo residue and treatment.
- **Clear errors fixed** in `batch_fixes.py` (highest precedence): see "fixed" rows; before / after in
  `work/audit/fixed_*.png` (real | before | after).
- **Taste calls flagged** for the lookbook: see "flagged" rows.

## Treatment per rarity (printed rarity = kind (cards))
Common = common (42) | Rare = rare (26) | Rare Holo = holo (8) | Rare Holo V = alt (5) | Rare Holo V = v (20) | Rare Holo VMAX = alt (5) | Rare Holo VMAX = vmax (3) | Rare Holo VSTAR = vstar (4) | Rare Rainbow = rainbow (4) | Rare Secret = gold (6) | Rare Ultra = alt (4) | Rare Ultra = fullart (11) | Trainer Gallery Rare Holo = gallery (12) | Uncommon = uncommon (25)

## Forms read off the scans
shaymin-sky 13 14 152 173, wormadam 10 / wormadam-sandy 77 / wormadam-trash 98, burmy (plant) 9, morpeko-hangry 95,
zamazenta-crowned 105 163, eiscue-noice 44, kingler-gmax 29, urshifu 18 / urshifu-gmax TG19 TG29 /
urshifu-rapid-strike-gmax TG21 TG30, the Galarian birds 181-183, alcremie (vanilla cream strawberry) 71 TG08,
tornadus (Incarnate) 126, zarude (no cape) 16. The Dynamax VMAXes (Mimikyu 69 TG17, Aggron 97, Sylveon TG15,
Umbreon TG23) use the plain sprites.

## Every card
| id | name | printed rarity | kind | sprite | grid px | anim | outcome | note |
|---|---|---|---|---|---|---|---|---|
| swsh9-1 | Exeggcute | Common | common | exeggcute | 48x36 |  | ok |  |
| swsh9-2 | Exeggutor | Uncommon | uncommon | exeggutor | 140x90 |  | fixed | ghost: Exeggutor's outer leaf tips were left in the sky; mask grown |
| swsh9-3 | Shroomish | Common | common | shroomish | 36x30 |  | ok |  |
| swsh9-4 | Breloom | Rare | rare | breloom | 92x60 |  | flagged | facing: Breloom 3/4 turned right, near-frontal sprite kept unflipped; faint grey smear by the raised arm |
| swsh9-5 | Tropius | Uncommon | uncommon | tropius | 92x56 |  | fixed | ghost: a green sliver of Tropius's head leaf / wing at the left edge; mask grown |
| swsh9-6 | Turtwig | Common | common | turtwig | 36x44 |  | ok |  |
| swsh9-7 | Grotle | Uncommon | uncommon | grotle (flipped) | 78x48 |  | ok |  |
| swsh9-8 | Torterra | Rare Holo | holo | torterra | 94x60 | yes | ok |  |
| swsh9-9 | Burmy | Common | common | burmy | 34x44 |  | ok |  |
| swsh9-10 | Wormadam | Rare | rare | wormadam | 92x60 |  | ok |  |
| swsh9-11 | Mothim | Rare | rare | mothim | 92x60 |  | ok |  |
| swsh9-12 | Cherubi | Common | common | cherubi | 36x36 |  | flagged | facing: Cherubi's face slightly right; kept unflipped |
| swsh9-13 | Shaymin V | Rare Holo V | v | shaymin-sky (flipped) | 80x70 | yes | ok |  |
| swsh9-14 | Shaymin VSTAR | Rare Holo VSTAR | vstar | shaymin-sky | 70x50 | yes | ok |  |
| swsh9-15 | Karrablast | Common | common | karrablast | 24x34 |  | ok |  |
| swsh9-16 | Zarude V | Rare Holo V | v | zarude (flipped) | 118x94 | yes | ok |  |
| swsh9-17 | Charizard V | Rare Holo V | v | charizard (flipped) | 118x104 | yes | ok |  |
| swsh9-18 | Charizard VSTAR | Rare Holo VSTAR | vstar | charizard | 100x84 | yes | ok |  |
| swsh9-19 | Magmar | Common | common | magmar | 72x72 |  | ok |  |
| swsh9-20 | Magmortar | Rare | rare | magmortar | 102x66 |  | ok |  |
| swsh9-21 | Moltres | Rare Holo | holo | moltres | 112x90 | yes | ok |  |
| swsh9-22 | Entei V | Rare Holo V | v | entei (flipped) | 104x88 | yes | ok |  |
| swsh9-23 | Torkoal | Uncommon | uncommon | torkoal | 94x58 |  | ok |  |
| swsh9-24 | Chimchar | Common | common | chimchar | 38x44 |  | ok |  |
| swsh9-25 | Monferno | Uncommon | uncommon | monferno | 82x50 |  | fixed | ghost: Monferno's outstretched hand and forearm; mask grown |
| swsh9-26 | Infernape | Rare Holo | holo | infernape (flipped) | 94x60 | yes | ok |  |
| swsh9-27 | Simisear V | Rare Holo V | v | simisear | 80x68 | yes | ok |  |
| swsh9-28 | Kingler V | Rare Holo V | v | kingler (flipped) | 118x100 | yes | ok |  |
| swsh9-29 | Kingler VMAX | Rare Holo VMAX | vmax | kingler-gmax | 110x92 | yes | ok |  |
| swsh9-30 | Staryu | Common | common | staryu | 34x34 |  | ok |  |
| swsh9-31 | Lapras | Rare | rare | lapras | 116x76 |  | ok |  |
| swsh9-32 | Corphish | Common | common | corphish | 42x38 |  | ok |  |
| swsh9-33 | Crawdaunt | Uncommon | uncommon | crawdaunt | 110x68 |  | ok |  |
| swsh9-34 | Snorunt | Common | common | snorunt | 30x38 |  | ok |  |
| swsh9-35 | Piplup | Common | common | piplup | 26x38 |  | ok |  |
| swsh9-36 | Prinplup | Uncommon | uncommon | prinplup (flipped) | 78x48 |  | ok |  |
| swsh9-37 | Empoleon | Rare Holo | holo | empoleon | 94x60 | yes | ok |  |
| swsh9-38 | Buizel | Common | common | buizel | 42x40 |  | ok |  |
| swsh9-39 | Floatzel | Uncommon | uncommon | floatzel (flipped) | 78x48 |  | fixed | ghost: Floatzel's lower tail wisps; mask grown |
| swsh9-40 | Lumineon V | Rare Holo V | v | lumineon (flipped) | 80x64 | yes | ok |  |
| swsh9-41 | Manaphy | Rare | rare | manaphy (flipped) | 92x60 |  | flagged | facing: Manaphy frontal; flipped on the antenna's trail |
| swsh9-42 | Cubchoo | Common | common | cubchoo | 28x36 |  | ok |  |
| swsh9-43 | Beartic | Uncommon | uncommon | beartic | 108x66 |  | ok |  |
| swsh9-44 | Eiscue | Rare | rare | eiscue-noice | 114x74 |  | fixed | form: the card is Noice Face Eiscue (ice block shattered); sprite eiscue-noice |
| swsh9-45 | Raichu V | Rare Holo V | v | raichu | 104x78 | yes | ok |  |
| swsh9-46 | Electabuzz | Common | common | electabuzz | 66x70 |  | ok |  |
| swsh9-47 | Electivire | Rare | rare | electivire | 102x66 |  | ok |  |
| swsh9-48 | Raikou V | Rare Holo V | v | raikou (flipped) | 110x92 | yes | fixed | ghost: Raikou's zig-zag lightning tail top left; mask grown |
| swsh9-49 | Shinx | Common | common | shinx (flipped) | 48x42 |  | ok |  |
| swsh9-50 | Luxio | Uncommon | uncommon | luxio | 78x48 |  | ok |  |
| swsh9-51 | Luxray | Rare | rare | luxray (flipped) | 98x64 |  | ok |  |
| swsh9-52 | Pachirisu | Uncommon | uncommon | pachirisu (flipped) | 82x50 |  | ok |  |
| swsh9-53 | Clefairy | Common | common | clefairy (flipped) | 36x38 |  | ok |  |
| swsh9-54 | Clefable | Rare | rare | clefable | 102x66 |  | ok |  |
| swsh9-55 | Starmie | Uncommon | uncommon | starmie | 108x66 |  | fixed | ghost: Starmie's lower-left star point; mask grown |
| swsh9-56 | Mewtwo | Rare | rare | mewtwo (flipped) | 134x88 |  | ok |  |
| swsh9-57 | Granbull V | Rare Holo V | v | granbull | 80x70 | yes | ok |  |
| swsh9-58 | Baltoy | Common | common | baltoy | 32x42 |  | ok |  |
| swsh9-59 | Claydol | Uncommon | uncommon | claydol | 108x66 |  | ok |  |
| swsh9-60 | Duskull | Common | common | duskull (flipped) | 36x42 |  | ok |  |
| swsh9-61 | Dusclops | Uncommon | uncommon | dusclops | 84x52 |  | ok |  |
| swsh9-62 | Dusknoir | Rare Holo | holo | dusknoir | 112x72 | yes | ok |  |
| swsh9-63 | Chimecho | Common | common | chimecho (flipped) | 30x42 |  | ok |  |
| swsh9-64 | Whimsicott V | Rare Holo V | v | whimsicott (flipped) | 94x76 | yes | ok |  |
| swsh9-65 | Whimsicott VSTAR | Rare Holo VSTAR | vstar | whimsicott | 92x68 | yes | ok |  |
| swsh9-66 | Sigilyph | Uncommon | uncommon | sigilyph | 126x78 |  | ok |  |
| swsh9-67 | Dedenne | Common | common | dedenne (flipped) | 68x54 |  | ok |  |
| swsh9-68 | Mimikyu V | Rare Holo V | v | mimikyu | 92x70 | yes | ok |  |
| swsh9-69 | Mimikyu VMAX | Rare Holo VMAX | vmax | mimikyu (flipped) | 92x74 | yes | flagged | Mimikyu VMAX: a small dark smudge from the shadow-tail along the top edge |
| swsh9-70 | Milcery | Common | common | milcery | 32x34 |  | ok |  |
| swsh9-71 | Alcremie | Rare | rare | alcremie | 98x64 |  | flagged | vendor alcremie: see TG08 |
| swsh9-72 | Hitmontop | Uncommon | uncommon | hitmontop | 104x64 |  | ok |  |
| swsh9-73 | Nosepass | Common | common | nosepass | 34x36 |  | ok |  |
| swsh9-74 | Trapinch | Common | common | trapinch | 38x38 |  | ok |  |
| swsh9-75 | Vibrava | Uncommon | uncommon | vibrava (flipped) | 78x48 |  | ok |  |
| swsh9-76 | Flygon | Rare | rare | flygon (flipped) | 110x72 |  | flagged | facing: Flygon's head frontal / diving; flipped on the tail curl |
| swsh9-77 | Wormadam | Rare | rare | wormadam-sandy | 92x60 |  | ok |  |
| swsh9-78 | Riolu | Common | common | riolu | 36x36 |  | ok |  |
| swsh9-79 | Lucario | Rare Holo | holo | lucario | 118x76 | yes | flagged | facing: Lucario faces left (unflipped) but the sprite's snout can read right at pixel scale |
| swsh9-80 | Throh | Common | common | throh (flipped) | 90x64 |  | ok |  |
| swsh9-81 | Sawk | Common | common | sawk (flipped) | 64x64 |  | ok |  |
| swsh9-82 | Golett | Common | common | golett | 36x36 |  | ok |  |
| swsh9-83 | Golurk | Rare | rare | golurk | 98x64 |  | ok |  |
| swsh9-84 | Grimer | Common | common | grimer | 42x36 |  | flagged | facing: Grimer's head right, arm/body reaching left; kept unflipped |
| swsh9-85 | Muk | Rare | rare | muk | 92x60 |  | ok |  |
| swsh9-86 | Sneasel | Common | common | sneasel | 34x42 |  | ok |  |
| swsh9-87 | Weavile | Uncommon | uncommon | weavile | 124x76 |  | ok |  |
| swsh9-88 | Honchkrow V | Rare Holo V | v | honchkrow (flipped) | 80x68 | yes | ok |  |
| swsh9-89 | Spiritomb | Common | common | spiritomb | 58x54 |  | ok |  |
| swsh9-90 | Purrloin | Common | common | purrloin (flipped) | 42x44 |  | ok |  |
| swsh9-91 | Liepard | Rare | rare | liepard (flipped) | 114x74 |  | ok |  |
| swsh9-92 | Impidimp | Common | common | impidimp (flipped) | 34x40 |  | ok |  |
| swsh9-93 | Morgrem | Uncommon | uncommon | morgrem (flipped) | 82x50 |  | fixed | ghost: Morgrem's claws (left hand, lower right); mask grown; FLAG: facing: Morgrem crawls left in 3/4 view; flipped (the reviewer leans unflipped) -- decide |
| swsh9-94 | Grimmsnarl | Rare | rare | grimmsnarl | 108x70 |  | ok |  |
| swsh9-95 | Morpeko V | Rare Holo V | v | morpeko-hangry | 80x66 | yes | ok |  |
| swsh9-96 | Aggron V | Rare Holo V | v | aggron (flipped) | 112x90 | yes | ok |  |
| swsh9-97 | Aggron VMAX | Rare Holo VMAX | vmax | aggron (flipped) | 96x84 | yes | ok |  |
| swsh9-98 | Wormadam | Rare | rare | wormadam-trash | 92x60 |  | ok |  |
| swsh9-99 | Probopass | Uncommon | uncommon | probopass | 82x50 |  | ok |  |
| swsh9-100 | Heatran | Rare | rare | heatran (flipped) | 104x68 |  | ok |  |
| swsh9-101 | Escavalier | Rare | rare | escavalier | 116x76 |  | ok |  |
| swsh9-102 | Klink | Common | common | klink | 44x32 |  | ok |  |
| swsh9-103 | Klang | Uncommon | uncommon | klang | 78x48 |  | ok |  |
| swsh9-104 | Klinklang | Rare | rare | klinklang | 104x68 |  | ok |  |
| swsh9-105 | Zamazenta V | Rare Holo V | v | zamazenta-crowned (flipped) | 126x106 | yes | flagged | form: Zamazenta V drawn in the Crowned Shield armour; sprite zamazenta-crowned (as 163 and cz 98) |
| swsh9-106 | Flygon V | Rare Holo V | v | flygon | 100x88 | yes | ok |  |
| swsh9-107 | Gible | Common | common | gible (flipped) | 38x38 |  | ok |  |
| swsh9-108 | Gabite | Uncommon | uncommon | gabite (flipped) | 78x48 |  | ok |  |
| swsh9-109 | Garchomp | Rare Holo | holo | garchomp (flipped) | 104x66 | yes | ok |  |
| swsh9-110 | Axew | Common | common | axew | 36x40 |  | ok |  |
| swsh9-111 | Fraxure | Uncommon | uncommon | fraxure | 78x48 |  | ok |  |
| swsh9-112 | Haxorus | Rare | rare | haxorus (flipped) | 108x70 |  | ok |  |
| swsh9-113 | Druddigon | Rare | rare | druddigon | 114x74 |  | ok |  |
| swsh9-114 | Dracovish V | Rare Holo V | v | dracovish | 96x72 | yes | ok |  |
| swsh9-115 | Farfetch'd | Common | common | farfetchd | 52x44 |  | ok |  |
| swsh9-116 | Castform | Common | common | castform (flipped) | 26x40 |  | flagged | facing: Castform's eye/mouth on the right (flip_commons), but its tail curl then opposes the card |
| swsh9-117 | Starly | Common | common | starly (flipped) | 38x36 |  | ok |  |
| swsh9-118 | Staravia | Uncommon | uncommon | staravia | 82x50 |  | fixed | ghost: Staravia's right wing tip and left wing-tip feathers; mask grown |
| swsh9-119 | Staraptor | Rare | rare | staraptor | 92x60 |  | ok |  |
| swsh9-120 | Bidoof | Common | common | bidoof | 40x32 |  | ok |  |
| swsh9-121 | Bibarel | Rare Holo | holo | bibarel | 94x60 | yes | ok |  |
| swsh9-122 | Arceus V | Rare Holo V | v | arceus (flipped) | 80x70 | yes | ok |  |
| swsh9-123 | Arceus VSTAR | Rare Holo VSTAR | vstar | arceus (flipped) | 92x62 | yes | ok |  |
| swsh9-124 | Minccino | Common | common | minccino (flipped) | 44x38 |  | flagged | facing: Minccino looks left in 3/4 with the tail swept left; flipped (borderline) |
| swsh9-125 | Cinccino | Uncommon | uncommon | cinccino | 104x64 |  | flagged | Cinccino: white sprite on a pale snow fill (low contrast); a pale block left of the head may be scarf fur |
| swsh9-126 | Tornadus | Rare | rare | tornadus | 116x76 |  | ok |  |
| swsh9-127 | Hawlucha | Common | common | hawlucha | 70x60 |  | ok |  |
| swsh9-128 | Drampa V | Rare Holo V | v | drampa | 102x90 | yes | ok |  |
| swsh9-129 | Acerola's Premonition | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh9-130 | Barry | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh9-131 | Blunder Policy | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh9-132 | Boss's Orders | Rare Holo |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh9-133 | Café Master | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh9-134 | Cheren's Care | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh9-135 | Choice Belt | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh9-136 | Cleansing Gloves | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh9-137 | Collapsed Stadium | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh9-138 | Cynthia's Ambition | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh9-139 | Fresh Water Set | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh9-140 | Friends in Galar | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh9-141 | Gloria | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh9-142 | Hunting Gloves | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh9-143 | Kindler | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh9-144 | Magma Basin | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh9-145 | Marnie's Pride | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh9-146 | Pot Helmet | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh9-147 | Professor's Research | Rare Holo |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh9-148 | Roseanne's Backup | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh9-149 | Team Yell's Cheer | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh9-150 | Ultra Ball | Uncommon |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh9-151 | Double Turbo Energy | Uncommon |  |  |  |  | skipped | Energy (no Pokemon) |
| swsh9-152 | Shaymin V | Rare Ultra | fullart | shaymin-sky | 84x66 | yes | fixed | LADDER ghost: Shaymin's two white wing tips; mask grown |
| swsh9-153 | Charizard V | Rare Ultra | fullart | charizard | 100x84 | yes | ok |  |
| swsh9-154 | Charizard V | Rare Ultra | alt | charizard | 110x84 | yes | fixed | LADDER ghost: a Charizard wing-tip remnant by the head; mask grown |
| swsh9-155 | Lumineon V | Rare Ultra | fullart | lumineon (flipped) | 84x66 | yes | fixed | ghost: Lumineon's long tail fin, lower fin and top-right fin tip; mask grown |
| swsh9-156 | Lumineon V | Rare Ultra | alt | lumineon | 88x64 | yes | ok |  |
| swsh9-157 | Pikachu V | Rare Ultra | fullart | pikachu | 84x66 | yes | fixed | ghost: Pikachu's black ear tip and the tail corner; mask grown |
| swsh9-158 | Raichu V | Rare Ultra | fullart | raichu (flipped) | 90x76 | yes | ok |  |
| swsh9-159 | Granbull V | Rare Ultra | fullart | granbull | 84x66 | yes | ok |  |
| swsh9-160 | Whimsicott V | Rare Ultra | fullart | whimsicott | 84x68 | yes | ok |  |
| swsh9-161 | Honchkrow V | Rare Ultra | fullart | honchkrow | 84x66 | yes | fixed | ghost: the tips of Honchkrow's hat plume; mask grown |
| swsh9-162 | Honchkrow V | Rare Ultra | alt | honchkrow (flipped) | 84x64 | yes | ok |  |
| swsh9-163 | Zamazenta V | Rare Ultra | fullart | zamazenta-crowned (flipped) | 106x86 | yes | ok |  |
| swsh9-164 | Flygon V | Rare Ultra | fullart | flygon (flipped) | 86x74 | yes | ok |  |
| swsh9-165 | Arceus V | Rare Ultra | fullart | arceus (flipped) | 84x66 | yes | flagged | facing: Arceus V full art: head points left, body mirrored; flipped on the body |
| swsh9-166 | Arceus V | Rare Ultra | alt | arceus | 84x64 | yes | ok |  |
| swsh9-167 | Barry | Rare Ultra |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh9-168 | Cheren's Care | Rare Ultra |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh9-169 | Cynthia's Ambition | Rare Ultra |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh9-170 | Kindler | Rare Ultra |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh9-171 | Marnie's Pride | Rare Ultra |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh9-172 | Roseanne's Backup | Rare Ultra |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh9-173 | Shaymin VSTAR | Rare Rainbow | rainbow | shaymin-sky | 80x68 | yes | flagged | Shaymin VSTAR rainbow: an orange-brown smear at the top edge of the ground (maybe the head crest) |
| swsh9-174 | Charizard VSTAR | Rare Rainbow | rainbow | charizard | 100x84 | yes | ok |  |
| swsh9-175 | Whimsicott VSTAR | Rare Rainbow | rainbow | whimsicott (flipped) | 82x68 | yes | flagged | facing: Whimsicott near-frontal, flipped (barely shows) |
| swsh9-176 | Arceus VSTAR | Rare Rainbow | rainbow | arceus (flipped) | 80x68 | yes | flagged | facing: Arceus VSTAR rainbow flipped to match gold 184 (same illustration); snout points left/down |
| swsh9-177 | Cheren's Care | Rare Rainbow |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh9-178 | Cynthia's Ambition | Rare Rainbow |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh9-179 | Kindler | Rare Rainbow |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh9-180 | Roseanne's Backup | Rare Rainbow |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh9-181 | Galarian Articuno V | Rare Secret | gold | articuno-galar (flipped) | 100x92 | yes | ok |  |
| swsh9-182 | Galarian Zapdos V | Rare Secret | gold | zapdos-galar (flipped) | 96x86 | yes | ok |  |
| swsh9-183 | Galarian Moltres V | Rare Secret | gold | moltres-galar (flipped) | 98x90 | yes | ok |  |
| swsh9-184 | Arceus VSTAR | Rare Secret | gold | arceus (flipped) | 84x66 | yes | ok |  |
| swsh9-185 | Magma Basin | Rare Secret |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh9-186 | Ultra Ball | Rare Secret |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh9tg-TG01 | Flareon | Trainer Gallery Rare Holo | gallery | flareon (flipped) | 110x72 | yes | ok |  |
| swsh9tg-TG02 | Vaporeon | Trainer Gallery Rare Holo | gallery | vaporeon | 100x66 | yes | ok |  |
| swsh9tg-TG03 | Octillery | Trainer Gallery Rare Holo | gallery | octillery | 98x64 | yes | ok |  |
| swsh9tg-TG04 | Jolteon | Trainer Gallery Rare Holo | gallery | jolteon (flipped) | 104x68 | yes | ok |  |
| swsh9tg-TG05 | Zekrom | Trainer Gallery Rare Holo | gallery | zekrom | 120x86 | yes | flagged | Zekrom: N's green hair shows through a gap inside the sprite (scenery, N kept); right side a dark smooth fill |
| swsh9tg-TG06 | Dusknoir | Trainer Gallery Rare Holo | gallery | dusknoir | 112x74 | yes | ok |  |
| swsh9tg-TG07 | Dedenne | Trainer Gallery Rare Holo | gallery | dedenne | 84x64 | yes | ok |  |
| swsh9tg-TG08 | Alcremie | Trainer Gallery Rare Holo | gallery | alcremie | 100x66 | yes | flagged | vendor alcremie: the regular and shiny sprites differ by one pixel; batch_tg / batch_rare_a patch the SHINY load (the regular stays pixel-exact) |
| swsh9tg-TG09 | Ariados | Trainer Gallery Rare Holo | gallery | ariados | 98x64 | yes | ok |  |
| swsh9tg-TG10 | Houndoom | Trainer Gallery Rare Holo | gallery | houndoom | 98x64 | yes | flagged | Houndoom: faint grey smear above Grimsley where the horn was; small sprite |
| swsh9tg-TG11 | Eevee | Trainer Gallery Rare Holo | gallery | eevee | 88x64 | yes | ok |  |
| swsh9tg-TG12 | Oranguru | Trainer Gallery Rare Holo | gallery | oranguru | 106x64 | yes | ok |  |
| swsh9tg-TG13 | Boltund V | Rare Holo V | alt | boltund (flipped) | 90x64 | yes | ok |  |
| swsh9tg-TG14 | Sylveon V | Rare Holo V | alt | sylveon | 90x68 | yes | ok |  |
| swsh9tg-TG15 | Sylveon VMAX | Rare Holo VMAX | alt | sylveon | 94x68 | yes | ok |  |
| swsh9tg-TG16 | Mimikyu V | Rare Holo V | alt | mimikyu | 98x66 | yes | ok |  |
| swsh9tg-TG17 | Mimikyu VMAX | Rare Holo VMAX | alt | mimikyu | 88x66 | yes | ok |  |
| swsh9tg-TG18 | Single Strike Urshifu V | Rare Holo V | alt | urshifu (flipped) | 94x72 | yes | ok |  |
| swsh9tg-TG19 | Single Strike Urshifu VMAX | Rare Holo VMAX | alt | urshifu-gmax (flipped) | 134x102 | yes | fixed | ghost: red hair tips top left, kept by a scenery cut; the cut starts lower; FLAG: facing: G-Max Urshifu's fist goes right (flipped), the mask-face is frontal-to-left |
| swsh9tg-TG20 | Rapid Strike Urshifu V | Rare Holo V |  |  |  |  | skipped | no colorscripts sprite: the vendor has no non-Gigantamax Rapid Strike Urshifu (only urshifu-rapid-strike-gmax); the Single Strike form would be the wrong form |
| swsh9tg-TG21 | Rapid Strike Urshifu VMAX | Rare Holo VMAX | alt | urshifu-rapid-strike-gmax | 126x92 | yes | fixed | ghost: G-Max Urshifu's giant fist lower left; mask grown (Mustard kept) |
| swsh9tg-TG22 | Umbreon V | Rare Holo V | alt | umbreon | 84x64 | yes | flagged | LADDER facing: Umbreon's head turned left (kept), the body walks right |
| swsh9tg-TG23 | Umbreon VMAX | Rare Holo VMAX | alt | umbreon (flipped) | 84x64 | yes | ok |  |
| swsh9tg-TG24 | Acerola's Premonition | Rare Ultra |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh9tg-TG25 | Café Master | Rare Ultra |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh9tg-TG26 | Gloria | Rare Ultra |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh9tg-TG27 | Rapid Strike Style Mustard | Rare Ultra |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh9tg-TG28 | Single Strike Style Mustard | Rare Ultra |  |  |  |  | skipped | Trainer (no Pokemon) |
| swsh9tg-TG29 | Single Strike Urshifu VMAX | Rare Secret | gold | urshifu-gmax | 106x102 | yes | ok |  |
| swsh9tg-TG30 | Rapid Strike Urshifu VMAX | Rare Secret | gold | urshifu-rapid-strike-gmax | 106x92 | yes | ok |  |
