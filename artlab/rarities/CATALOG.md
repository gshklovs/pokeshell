# Pokemon TCG rarity catalog

60 rarities / finishes, in ladder order (least to most rare within the escalation of effects). Every one of the pokemontcg.io API's 44 distinct `rarity` values maps onto at least one entry. Pattern variants the API folds into one value (reverse patterns, era holo patterns, Crystal, Radiant Collection) get their own entries. JP-only finishes are flagged.

Machine-readable: `rarities.json` (id, label, api_rarity, family, era, finish, frame, odds, weight, jp_only, recipe). **weight** = expected copies per booster pack in the rarity's home era (1 / packs-per-hit); use it as the relative odds weight. **EST** = estimate. Source keys are listed at the bottom.

## Families

- **no-foil** (3): Common = the bare sprite, no background (user rule); Uncommon / Rare = muted matte scene (sprite-scale blocks / grid scale), plain frame, rarity symbol. `common`, `uncommon`, `rare`
- **reverse** (4): the art stays matte; a 5px foil ring outside it carries the pattern. `reverse_holo`, `reverse_fireworks`, `reverse_pokeball`, `reverse_masterball`
- **holo-in-art** (14): matte frame, foil pattern inside the art window, vertical light bar. `rare_holo_starlight`, `rare_holo_cosmos`, `rare_holo_swirl`, `rare_holo_tinsel`, `rare_holo_mirror`, `rare_holo_waterweb`, `rare_holo_swsh`, `rare_holo_sv`, `rare_holo_crackedice`, `rare_holo_crosshatch`, `classic_collection`, `promo`, `radiant_collection`, `pikachu_rare`
- **V-family** (7): framed art with textured foil and a diagonal rainbow beam pair (sunpillar). `rare_holo_ex_old`, `rare_holo_ex_bwxy`, `rare_holo_gx`, `rare_holo_v`, `rare_holo_vmax`, `rare_holo_vstar`, `double_rare`
- **old-era** (4): LV.X streaks, Prime spiked window, LEGEND split card, BREAK gold square prism. `rare_holo_lvx`, `rare_prime`, `legend`, `rare_break`
- **prism-star** (6): crystal / prism facets, star emblems, shiny sprites for Shining and Gold Star. `rare_shining`, `rare_holo_star`, `crystal`, `rare_prism_star`, `rare_ace`, `ace_spec_rare`
- **shiny** (4): the colorscripts SHINY sprite on sparkle / glitter foil. `rare_shiny`, `rare_shiny_gx`, `shiny_rare`, `shiny_ultra_rare`
- **amazing** (1): rainbow paint splash bursting out through the frame. `amazing_rare`
- **radiant** (1): radial crosshatch burst from the Pokemon, shiny sprite. `radiant_rare`
- **etched-full-art** (4): full bleed, fingerprint contour lines, rainbow wave along the lines. `trainer_gallery`, `character_rare_jp`, `ultra_rare`, `illustration_rare`
- **special-illustration** (5): full painting with a pearlescent sweep (and the new pop-art / chrome specials). `alternate_art`, `special_illustration_rare`, `character_super_rare_jp`, `mega_attack_rare`, `futuristic_rare`
- **rainbow** (1): pastel rainbow gradient + etched lines, rainbow frame. `rare_rainbow`
- **gold** (4): gold ramp foil (engraved / studs / crystalline / dense etch) + glitter, gold frame. `secret_rare_gold_bwxy`, `secret_rare_gold`, `hyper_rare`, `mega_hyper_rare`
- **monochrome** (2): black or white embossed card, colour only in the moving holo. `black_white_rare_black`, `black_white_rare_white`

## Catalog

| # | id | rarity | API value | family | era / sets | finish (what you see tilting it) | frame | pull rate | recipe |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `common` | Common | Common | no-foil | every era | no foil: flat matte print. pokeshell rule: the bare colorscripts sprite, no background at all | none (no background) | 3-5 per pack | `bare_common` |
| 2 | `uncommon` | Uncommon | Uncommon | no-foil | every era | no foil: flat matte print | plain | 3 per pack | `nofoil_uncommon` |
| 3 | `rare` | Rare (non-holo) | Rare | no-foil | WotC to SWSH (in SV the rare slot is always holo) | no foil; the rare star is the only tell | plain | about 2 in 3 packs (WotC-HGSS) [PD][DTQ-SV] | `nofoil_rare` |
| 4 | `reverse_holo` | Reverse Holo | (parallel print of C/U/R) | reverse | Legendary Collection (2002) to today | the whole card is foil EXCEPT the art window, which stays matte; flat foil (DP-BW), faint tile (SWSH), fine sparkle tile (SV) | plain (foiled) | about 1 per pack (1-2 in SV) [CV] | `reverse_classic` |
| 5 | `reverse_fireworks` | Reverse Holo: Legendary Collection fireworks | (parallel) | reverse | Legendary Collection (2002) | dense exploding starbursts in pale rainbow on the frame and background; the art is matte | plain (foiled) | about 1 per pack EST [CV] | `reverse_fireworks` |
| 6 | `reverse_pokeball` | Reverse Holo: Poke Ball pattern | (parallel) | reverse | JP sv2a 151 (2023) first; English Prismatic Evolutions, Black Bolt / White Flare | a repeating grid of Poke Ball icons in the foil outside the art | plain (foiled) | about 1 in 3 packs in Prismatic Evolutions [PB-PRE] | `reverse_pokeball` |
| 7 | `reverse_masterball` | Reverse Holo: Master Ball pattern | (parallel) | reverse | JP sv2a 151 (2023) first; English Prismatic Evolutions, Black Bolt / White Flare | denser, purple-tinted Master Ball icon grid outside the art | plain (foiled) | about 1 in 20 packs (1 per JP 151 box; 5% of Prismatic Evolutions packs) [SNKR-151][PB-PRE] | `reverse_masterball` |
| 8 | `rare_holo_starlight` | Rare Holo: starlight (WotC) | Rare Holo | holo-in-art | Base Set, Jungle, Fossil | soft starbursts and specks scattered across the art window; frame matte yellow | plain (yellow) | 1 in 3 packs [PD][FS] | `holo_starlight` |
| 9 | `rare_holo_cosmos` | Rare Holo: cosmos | Rare Holo | holo-in-art | Base Set 2 to Call of Legends, many promos | dots, circles and orbs of rainbow foil in the art window | plain (yellow) | 1 in 3 packs [PD][FS] | `holo_cosmos` |
| 10 | `rare_holo_swirl` | Rare Holo: cosmos swirl | Rare Holo | holo-in-art | cosmos-era cards where the sheet's spiral landed on the art | a large rainbow spiral arcing through the cosmos foil | plain (yellow) | a cosmos holo placement, rarer than plain cosmos EST | `holo_swirl` |
| 11 | `rare_holo_tinsel` | Rare Holo: tinsel (BW) | Rare Holo | holo-in-art | Black & White to Legendary Treasures | fine horizontal lines of foil across the art | plain (yellow) | about 1 in 3 packs [PD] | `holo_tinsel` |
| 12 | `rare_holo_mirror` | Rare Holo: sheen / mirror (XY) | Rare Holo | holo-in-art | XY | a smooth mirror shine with no pattern: one broad diagonal highlight | plain (yellow) | about 1 in 3 packs [PD] | `holo_mirror` |
| 13 | `rare_holo_waterweb` | Rare Holo: water web (SM) | Rare Holo | holo-in-art | Sun & Moon | a wavy web of bright foil lines, like caustics on a pool floor | plain (yellow) | about 1 in 3 packs [PD] | `holo_waterweb` |
| 14 | `rare_holo_swsh` | Rare Holo: vertical sheen (SWSH) | Rare Holo | holo-in-art | Sword & Shield | vertical-stripe rainbow sheen across the art | plain (yellow) | about 1 in 3-5 packs [DTQ-ASR] | `holo_stripes` |
| 15 | `rare_holo_sv` | Rare Holo: wave (SV) | Rare Holo | holo-in-art | Scarlet & Violet, Mega Evolution | a soft wavy sheen in the art; silver-grey border | plain (silver-grey) | 1 per pack (the SV rare slot is always holo) [DTQ-SV] | `holo_wave` |
| 16 | `rare_holo_crackedice` | Rare Holo: cracked ice | Rare Holo, Promo | holo-in-art | theme-deck exclusives from Platinum on, many promos | large angular shards like shattered glass, each its own tint, bright seams | plain (yellow) | not in boosters (theme decks, promos) | `holo_crackedice` |
| 17 | `rare_holo_crosshatch` | Rare Holo: crosshatch | Promo | holo-in-art | Play! Pokemon prize and staff promos | a crosshatch grid of foil lines over the art background | plain (yellow) | event prize only | `holo_crosshatch` |
| 18 | `classic_collection` | Classic Collection | Classic Collection | holo-in-art | Celebrations (2021), 30th Celebration (2026) | vintage reprint: yellow frame, cosmos holo in the art, anniversary stamp | plain (yellow) | about 1 in 2.5 packs (Celebrations) [PD] | `holo_classic_collection` |
| 19 | `promo` | Promo (black star) | Promo | holo-in-art | every era | varies (often cosmos / swirl or cracked ice, sometimes non-holo) | plain | not in boosters | `holo_promo` |
| 20 | `radiant_collection` | Radiant Collection | (RC numbers; API: Rare Holo / Uncommon) | holo-in-art | Legendary Treasures (2013), Generations (2016) | full-art style card with sparkly cosmos holo over the WHOLE card, yellow border | plain (yellow, foiled) | RC C/U about 1 per pack, RC rares about 1 in 20 EST [PD] | `holo_radiant_collection` |
| 21 | `pikachu_rare` | Pikachu Rare | Pikachu Rare | holo-in-art | 30th Celebration (2026) | fireworks holo over the whole card, no plain border | none (full bleed) | guaranteed 1 per pack [PP-30] | `holo_pikachu_fireworks` |
| 22 | `rare_holo_ex_old` | Rare Holo ex (EX era) | Rare Holo EX | V-family | Ruby & Sapphire to Power Keepers | holo art window and a holographic silver border | silver (foiled) | about 1 in 12-18 packs [FS] | `vbeam_ex_old` |
| 23 | `rare_holo_ex_bwxy` | Rare Holo Pokemon-EX (BW/XY) | Rare Holo EX | V-family | Next Destinies to Evolutions | holo art plus an etched line sheen over the face; yellow frame | plain (yellow) | 1 in 18 (Next Destinies) improving to about 1 in 6 [FS][PD] | `vbeam_ex_bw` |
| 24 | `rare_holo_gx` | Rare Holo GX | Rare Holo GX | V-family | Sun & Moon | water-web / sheen holo in the art, light texture, yellow frame | plain (yellow) | about 1 in 9-12 packs [PD] | `vbeam_gx` |
| 25 | `rare_holo_v` | Rare Holo V | Rare Holo V, Holo Rare V | V-family | Sword & Shield | etched diagonal-line holo over big art; rainbow bands that move in opposite directions | silver | about 1 in 7-10 packs [DTQ-VV][DTQ-ASR] | `vbeam_v` |
| 26 | `rare_holo_vmax` | Rare Holo VMAX | Rare Holo VMAX, Holo Rare VMAX | V-family | Sword & Shield | full-bleed art under the frame, bold etched texture, strong beam | silver (dark) | about 1 in 18-23 packs [DTQ-VV][PD] | `vbeam_vmax` |
| 27 | `rare_holo_vstar` | Rare Holo VSTAR | Rare Holo VSTAR, Holo Rare VSTAR | V-family | Brilliant Stars to Crown Zenith | full-bleed textured holo like VMAX with a gold/silver crest: gold-tinged | silver-gold | about 1 in 30-38 packs [DTQ-BRS][DTQ-ASR] | `vbeam_vstar` |
| 28 | `double_rare` | Double Rare (ex) | Double Rare, Rare Holo ex | V-family | Scarlet & Violet, Mega Evolution | the regular ex: art to the frame, textured sparkle holo, silver frame, two black stars | silver | about 1 in 6-7 packs (SV), 1 in 5 (ME1) [CY-SV][DTQ-SV][RC-ME] | `vbeam_ex_sv` |
| 29 | `rare_holo_lvx` | Rare Holo LV.X | Rare Holo LV.X | old-era | Diamond & Pearl, Platinum | galaxy foil background, holographic silver border, bright light streaks | silver | 1 in 36 packs early DP, later 1 in 18 [FS][PD] | `old_lvx` |
| 30 | `rare_prime` | Rare Prime | Rare Prime | old-era | HeartGold SoulSilver | spiked art-window edge; the border AND the background are holo | silver (foiled, spiked window) | about 1 in 6 packs [PD] | `old_prime` |
| 31 | `legend` | LEGEND | LEGEND | old-era | HeartGold SoulSilver to Call of Legends | two-card horizontal puzzle, whole surface galaxy holo, little border | thin, split down the middle | about 1 in 12 packs per half [PD] | `old_legend` |
| 32 | `rare_break` | Rare BREAK | Rare BREAK | old-era | XY BREAKpoint to Evolutions | the Pokemon in trophy gold; gold 'square prism' foil | silver | about 1 in 12-13 packs [FS][PD] | `old_break` |
| 33 | `rare_shining` | Rare Shining (Neo) | Rare Shining | prism-star | Neo Revelation, Neo Destiny | shiny-coloured Pokemon in cosmos holo, big starbursts; yellow frame | plain (yellow) | 1 in 18 (Neo Revelation), 1 in 12 (Neo Destiny) [FS] | `shiny_shining` |
| 34 | `rare_holo_star` | Rare Holo Star (Gold Star) | Rare Holo Star | prism-star | Team Rocket Returns to Power Keepers, POP | shiny Pokemon with a gold star emblem, cosmos holo art | plain (yellow) | about 1 in 72 packs (some estimates 1 in 30) [FS] | `prism_goldstar` |
| 35 | `crystal` | Crystal | (API: Rare Holo) | prism-star | Aquapolis, Skyridge | a translucent crystal-textured Pokemon in a holo window: facets refracting around it | plain (yellow) | 1 in 36 (Aquapolis), 1 in 12-18 (Skyridge) [FS] | `prism_crystal` |
| 36 | `rare_prism_star` | Rare Prism Star | Rare Prism Star | prism-star | Ultra Prism to Cosmic Eclipse | prismatic kaleidoscope holo, a big prism-star emblem, BLACK border | plain (black) | about 1 in 12 packs [PD] | `prism_star` |
| 37 | `rare_ace` | Rare ACE (ACE SPEC, BW) | Rare ACE | prism-star | Boundaries Crossed to Plasma Blast | holo Trainer with an ACE SPEC banner; pink-violet facet foil EST | silver | about 1 in 18 packs [PD] | `prism_ace_bw` |
| 38 | `ace_spec_rare` | ACE SPEC Rare (SV) | ACE SPEC Rare | prism-star | Temporal Forces to Prismatic Evolutions | whole-card iridescent textured foil, magenta-gold prism; pink rarity star | silver-pink | 1 in 20 packs [PB-SV] | `prism_ace_sv` |
| 39 | `rare_shiny` | Rare Shiny (Shiny Vault) | Rare Shiny | shiny | Hidden Fates, Shining Fates, Shining Legends | silver-toned card, white window with embossed sparkle/glitter foil, 4-point stars | silver | about 1 in 4.4-4.7 packs [PD] | `shiny_vault` |
| 40 | `rare_shiny_gx` | Rare Shiny GX / Shiny V | Rare Shiny GX | shiny | Hidden Fates, Shining Fates | full-art shiny with black/silver textured foil and sparkle | none (full bleed) | about 1 in 10.6 packs (HIF), 1 in 20 (Shiny V) [PD] | `shiny_vault_gx` |
| 41 | `shiny_rare` | Shiny Rare (SV) | Shiny Rare | shiny | Paldean Fates (and later SV specials) | the scene kept, glitter-sparkle foil all over, silver frame | silver | 1 in 4 packs [PB-PAF] | `shiny_sv` |
| 42 | `shiny_ultra_rare` | Shiny Ultra Rare | Shiny Ultra Rare | shiny | Paldean Fates | textured full-art shiny ex, dense sparkle | none (full bleed) | 1 in 13 packs [PB-PAF] | `shiny_sv_ultra` |
| 43 | `amazing_rare` | Amazing Rare | Amazing Rare | amazing | Vivid Voltage, Shining Fates, Battle Styles, Evolving Skies | textured rainbow paint splash bursting OUT of the art window across the card; yellow frame | plain (yellow, broken by the splash) | about 1 in 17.5 packs [DTQ-VV][PD] | `amazing_splash` |
| 44 | `radiant_rare` | Radiant Rare | Radiant Rare | radiant | Astral Radiance to Crown Zenith | shiny Pokemon on a whole-card radial crosshatch burst holo; art spills past a light frame | silver (thin) | about 1 in 20 packs [DTQ-ASR] | `radiant_burst` |
| 45 | `trainer_gallery` | Trainer Gallery Rare Holo | Trainer Gallery Rare Holo | etched-full-art | Brilliant Stars to Silver Tempest; Crown Zenith Galarian Gallery | full-bleed trainer-and-Pokemon art with a pastel holo sheen and light texture | none (full bleed) | about 1 in 8 packs EST [DTQ-BRS] | `etched_gallery` |
| 46 | `character_rare_jp` | Character Rare (CHR) **(JP only)** | (JP only) | etched-full-art | JP VMAX Climax (s8b) on | Japanese counterpart of Trainer Gallery: full-bleed trainer art, holo sheen, finer texture | none (full bleed) | about 1 in 5 JP packs EST [CHR] | `etched_chr_jp` |
| 47 | `ultra_rare` | Ultra Rare / Rare Ultra (full art) | Rare Ultra, Ultra Rare | etched-full-art | BW to ME (full-art V/GX/EX/ex and Supporters) | full bleed, heavy etched fingerprint texture everywhere, rainbow sheen along the lines | none (full bleed) | 1 in 15 (SV) [PB-SV]; 1 in 18-25 (SWSH) [DTQ-VV] | `etched_ultra` |
| 48 | `illustration_rare` | Illustration Rare | Illustration Rare | etched-full-art | SV, ME (JP: Art Rare, AR) | the full painting, full bleed, with a light holo texture | none (full bleed) | 1 in 13 packs (SV) [PB-SV][CY-SV]; 1 in 9 (ME1) [RC-ME] | `etched_illustration` |
| 49 | `alternate_art` | Alternate Art (SWSH alt art) | (API: Rare Ultra / Rare Secret / Rare Rainbow) | special-illustration | Sword & Shield (Evolving Skies, Fusion Strike, Brilliant Stars...) | a full storybook painting instead of the stock pose; the brushwork itself is embossed and catches the light | none (full bleed) | about 1 in 70-300+ packs depending on set EST [DTQ-VV] | `sir_altart` |
| 50 | `special_illustration_rare` | Special Illustration Rare | Special Illustration Rare | special-illustration | SV, ME (JP: Special Art Rare, SAR) | a full story painting, strong texture following the art, pearlescent sheen | none (full bleed) | 1 in 32 (SV base) to 1 in 86 (Temporal Forces) [CY-SV][PB-SV] | `sir_special` |
| 51 | `character_super_rare_jp` | Character Super Rare (CSR) **(JP only)** | (JP only) | special-illustration | JP VMAX Climax (s8b) on | glossier, textured trainer + V/VMAX art, warm pearl sheen | none (full bleed) | about 1 in 20 JP packs EST [CHR] | `sir_csr_jp` |
| 52 | `mega_attack_rare` | Mega Attack Rare | MEGA_ATTACK_RARE | special-illustration | ME Ascended Heroes (2026) | pop-art full art of a Mega ex (halftone, ink lines, action lines), enhanced foil; pink + green stars | none (full bleed) | about 1 in 29 packs (reported) [PPT-ME][BULB-MAR] | `popart_mega_attack` |
| 53 | `futuristic_rare` | Futuristic Rare | Futuristic Rare | special-illustration | 30th Celebration (2026) | chrome-stylised metallic Pokemon ex over a burst of energy symbols; coloured rarity star | none (full bleed) | about 1 in 50-120 packs [PP-30] | `chrome_futuristic` |
| 54 | `rare_rainbow` | Rainbow Rare | Rare Rainbow | rainbow | Sun & Moon to Sword & Shield | pastel rainbow gradient over the whole card plus dense etched lines and glitter; the Pokemon itself is rainbow | none (full bleed) | about 1 in 80-90 packs [PD][DTQ-VV] | `rainbow_rare` |
| 55 | `secret_rare_gold_bwxy` | Secret Rare: gold Trainer (BW/XY) | Rare Secret | gold | Black & White to XY | gold Trainer/item with an engraved guilloche pattern | gold | about 1 in 72-125 packs [FS][PD] | `gold_engraved` |
| 56 | `secret_rare_gold` | Secret Rare: gold (SM/SWSH) | Rare Secret | gold | Sun & Moon, Sword & Shield | whole-card gold foil, embossed stud texture, gold border | gold | about 1 in 94 (SM) to 1 in 130 (SWSH) [PD][BC-ASR] | `gold_secret` |
| 57 | `hyper_rare` | Hyper Rare (gold) | Hyper Rare | gold | Scarlet & Violet (JP: UR) | the whole card in gold, the Pokemon too, with crystalline etched texture and glitter; three gold stars | gold | 1 in 54 (SV base) to 1 in 139 (Temporal Forces) [CY-SV][PB-SV] | `gold_hyper` |
| 58 | `black_white_rare_black` | Black White Rare (Black Bolt) | Black White Rare | monochrome | Black Bolt (2025) | monochrome: black-and-grey art on black foil, colour only in the holo | plain (black) | about 1 in 496 packs [PP-BLK] | `mono_black` |
| 59 | `black_white_rare_white` | Black White Rare (White Flare) | Black White Rare | monochrome | White Flare (2025) | monochrome: embossed white foil, colour only through the holo | plain (white) | about 1 in 496 packs [PP-BLK] | `mono_white` |
| 60 | `mega_hyper_rare` | Mega Hyper Rare | Mega Hyper Rare | gold | ME1 Mega Evolution (2025) | all-gold monochrome card, dense textured gold, gold border | gold | about 1 in 1,260 packs [TCGP-ME] | `gold_mega_hyper` |

## Japanese-only and Japan-first

- **Character Rare (CHR)** and **Character Super Rare (CSR)**: JP-only, from s8b VMAX Climax (Dec 2021). The English equivalents are Trainer Gallery and TG Ultra Rare.
- **Poke Ball / Master Ball mirror** reverse: Japan-first (sv2a 151, 2023). English sets got them from Prismatic Evolutions on. English 151 has only the standard reverse.
- Naming only (same finishes as the English entries): Art Rare (AR) = Illustration Rare, Special Art Rare (SAR) = SIR, SR = full art (Ultra Rare), UR = gold (Hyper Rare), HR = rainbow in SM, S / SSR = Shiny Rare / Shiny Ultra Rare, 'A' = ACE SPEC.
- Japanese sets have no English-style reverse set; they use 'mirror' parallels instead.

## Not given their own entry

- EX-era pattern reverses (energy symbols in Hidden Legends and FRLG, the Deoxys pinwheel, Emerald's Poke Balls and stars) and the XY / SM type-symbol reverses. These are all `reverse_holo` with a different print (the engine's `reverse_pokeball` code path takes any 3x3 icon).
- Older secret rares that are just alternate holos (for example EX Dragon 98/97, which is cosmos): use their holo pattern's entry.
- Galarian Gallery (Crown Zenith) = `trainer_gallery`. TG gold cards = `secret_rare_gold`.

## API coverage (pokemontcg.io, fetched 2026-09-28/29)

| API rarity | cards | first set | latest set |
|---|---|---|---|
| ACE SPEC Rare | 33 | Temporal Forces (2024/03/22) | Prismatic Evolutions (2025/01/17) |
| Amazing Rare | 10 | Vivid Voltage (2020/11/13) | 30th Celebration: Classic Collection (2026/09/16) |
| Black White Rare | 2 | Black Bolt (2025/07/18) | White Flare (2025/07/18) |
| Classic Collection | 25 | Celebrations: Classic Collection (2021/10/08) | Celebrations: Classic Collection (2021/10/08) |
| Common | 5399 | Base (1999/01/09) | 30th Celebration: Classic Collection (2026/09/16) |
| Double Rare | 329 | Scarlet & Violet (2023/03/31) | 30th Celebration (2026/09/16) |
| Futuristic Rare | 2 | 30th Celebration (2026/09/16) | 30th Celebration (2026/09/16) |
| Holo Rare V | 1 | 30th Celebration: Classic Collection (2026/09/16) | 30th Celebration: Classic Collection (2026/09/16) |
| Holo Rare VMAX | 1 | 30th Celebration: Classic Collection (2026/09/16) | 30th Celebration: Classic Collection (2026/09/16) |
| Holo Rare VSTAR | 1 | 30th Celebration: Classic Collection (2026/09/16) | 30th Celebration: Classic Collection (2026/09/16) |
| Hyper Rare | 82 | Scarlet & Violet (2023/03/31) | Pitch Black (2026/07/17) |
| Illustration Rare | 743 | Scarlet & Violet (2023/03/31) | 30th Celebration: Classic Collection (2026/09/16) |
| LEGEND | 20 | HeartGold & SoulSilver (2010/02/10) | 30th Celebration: Classic Collection (2026/09/16) |
| MEGA_ATTACK_RARE | 7 | Ascended Heroes (2026/01/30) | Ascended Heroes (2026/01/30) |
| Mega Hyper Rare | 8 | Mega Evolution (2025/09/26) | Pitch Black (2026/07/17) |
| Pikachu Rare | 30 | 30th Celebration (2026/09/16) | 30th Celebration (2026/09/16) |
| Promo | 1255 | Wizards Black Star Promos (1999/07/01) | Scarlet & Violet Black Star Promos (2023/01/01) |
| Radiant Rare | 15 | Astral Radiance (2022/05/27) | Crown Zenith (2023/01/20) |
| Rare | 8772 | Base (1999/01/09) | 30th Celebration: Classic Collection (2026/09/16) |
| Rare ACE | 13 | Boundaries Crossed (2012/11/07) | Plasma Blast (2013/08/14) |
| Rare BREAK | 28 | BREAKthrough (2015/11/04) | 30th Celebration: Classic Collection (2026/09/16) |
| Rare Holo | 2707 | Base (1999/01/09) | 30th Celebration: Classic Collection (2026/09/16) |
| Rare Holo EX | 322 | Ruby & Sapphire (2003/07/01) | 30th Celebration: Classic Collection (2026/09/16) |
| Rare Holo GX | 168 | Sun & Moon (2017/02/03) | 30th Celebration: Classic Collection (2026/09/16) |
| Rare Holo LV.X | 57 | Diamond & Pearl (2007/05/01) | 30th Celebration: Classic Collection (2026/09/16) |
| Rare Holo Star | 25 | Team Rocket Returns (2004/11/01) | Power Keepers (2007/02/02) |
| Rare Holo V | 281 | Sword & Shield (2020/02/07) | Crown Zenith (2023/01/20) |
| Rare Holo VMAX | 110 | Sword & Shield (2020/02/07) | Crown Zenith (2023/01/20) |
| Rare Holo VSTAR | 43 | Brilliant Stars (2022/02/25) | Crown Zenith (2023/01/20) |
| Rare Holo ex | 322 | Ruby & Sapphire (2003/07/01) | 30th Celebration: Classic Collection (2026/09/16) |
| Rare Prime | 27 | HeartGold & SoulSilver (2010/02/10) | 30th Celebration: Classic Collection (2026/09/16) |
| Rare Prism Star | 0 | None (None) | None (None) |
| Rare Rainbow | 324 | Sun & Moon (2017/02/03) | Silver Tempest (2022/11/11) |
| Rare Secret | 327 | Team Rocket (2000/04/24) | 30th Celebration: Classic Collection (2026/09/16) |
| Rare Shining | 16 | Neo Revelation (2001/09/21) | Shining Legends (2017/10/06) |
| Rare Shiny | 184 | Hidden Fates Shiny Vault (2019/08/23) | Shining Fates Shiny Vault (2021/02/19) |
| Rare Shiny GX | 35 | Hidden Fates Shiny Vault (2019/08/23) | Hidden Fates Shiny Vault (2019/08/23) |
| Rare Ultra | 799 | Black & White (2011/04/25) | 30th Celebration: Classic Collection (2026/09/16) |
| Shiny Rare | 120 | Paldean Fates (2024/01/26) | Paldean Fates (2024/01/26) |
| Shiny Ultra Rare | 12 | Paldean Fates (2024/01/26) | Paldean Fates (2024/01/26) |
| Special Illustration Rare | 232 | Scarlet & Violet (2023/03/31) | 30th Celebration (2026/09/16) |
| Trainer Gallery Rare Holo | 80 | Brilliant Stars Trainer Gallery (2022/02/25) | Crown Zenith Galarian Gallery (2023/01/20) |
| Ultra Rare | 368 | Scarlet & Violet (2023/03/31) | Pitch Black (2026/07/17) |
| Uncommon | 4889 | Base (1999/01/09) | 30th Celebration: Classic Collection (2026/09/16) |

Caveats: the API's `q=rarity:"..."` search is case-insensitive, so `Rare Holo EX` and `Rare Holo ex` return the same 322 cards (EX-era ex, BW/XY EX and SV ex together). `Rare Prism Star` is listed by `/v2/rarities` but its search returns 0 cards (an API quirk). The `Holo Rare V/VMAX/VSTAR` spellings are single 30th Celebration Classic Collection reprints. Per-rarity set lists are in `work/rarity_sets.json`.

## Sources

- [PB-SV] https://www.pokebeach.com/2024/03/temporal-forces-has-hardest-pull-rates-of-scarlet-violet-sets-for-highest-rarities
- [PB-PAF] https://www.pokebeach.com/2024/01/paldean-fates-pull-rates-revealed
- [PB-PRE] https://www.pokebeach.com/2025/01/prismatic-evolutions-pull-rates-revealed-special-illustration-rares-twice-as-easy-to-pull
- [CY-SV] https://www.codedyellow.com/scarlet-and-violet-base-set-pull-rate/
- [DTQ-SV] https://www.digitaltq.com/scarlet-violet-pull-rates-pokemon-tcg
- [DTQ-VV] https://www.digitaltq.com/vivid-voltage-booster-pull-rates-pokemon-tcg
- [DTQ-ASR] https://www.digitaltq.com/astral-radiance-pull-rates-pokemon-tcg
- [DTQ-BRS] https://www.digitaltq.com/brilliant-stars-pull-rates-pokemon-tcg
- [BC-ASR] https://bleedingcool.com/games/pokemon-tcg-pull-rate-quest-astral-radiance-part-six/
- [PD] https://www.thepricedex.com/set/<code>/<name>/pull-rates
- [FS] https://flipsidegaming.com/blogs/pokemon-blog/a-comprehensive-review-of-rarity-in-the-pokemon-tcg
- [CV] https://www.cardveil.com/resources/pokemon-holo-patterns
- [BULB] https://bulbapedia.bulbagarden.net/wiki/Holofoil
- [BC-HIST] https://bleedingcool.com/games/a-holographic-history-of-the-pokemon-tcg-pokemon-legend/
- [RC-ME] https://rarecandy.com/blog/rarities-pokemon-mega-evolution-era
- [TCGP-ME] https://www.tcgplayer.com/content/article/Pok%C3%A9mon-TCG-Mega-Evolution-Pull-Rates/40cbeedc-21ce-473b-aef1-74e3969d9f91/
- [PP-BLK] https://pokepatch.com/2025/07/20/black-bolt-white-flare-pull-rates-in-pokemon-tcg-sets/
- [PP-30] https://pokepatch.com/2026/09/24/30th-celebration-pull-rates-real-odds-top-chase-cards/
- [PPT-ME] https://www.pokemonpricetracker.com/blog/posts/mega-evolution-set-pull-rates-ev-guide-2026
- [BULB-MAR] https://bulbapedia.bulbagarden.net/wiki/Mega_attack_rare_card_(TCG)
- [SNKR-151] https://snkrdunk.com/en/magazine/2023/06/16/japanese-pokemon-151-where-to-buy-full-card-set-list-and-pull-rate/
- [CHR] https://pokemoncard.io/article/new-csr-chr-cards-from-s8b-vmax-climax-122
- Full per-rarity research notes: `work/research.md`. The finishes are cross-checked against `../source/SOURCES.md`.
