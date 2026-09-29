# 30th Celebration (me55) audit

Every built card (149: the 7 ladder cards + 142 from the six batches) was checked against its real scan on contact sheets (work/audit/sheets/, real | ours). A card is ok when its treatment matches the approved example of its rarity (FULLSET.md), the sprite is the right Pokémon and form and faces the way the card does, the scene is the card's own with the 30th stamp and all text painted out and no noticeable ghost, and the data, text half and animations are right.

Counts: ok 139, fixed 3, flagged 7, skipped 12 (setlist 161 = 149 built + 12 skipped)

Automated checks, all clean (work/audit/audit_meta.py, work/audit/verify_all.py): p30verify on all 149 (sprite shape, outline and colours exact apart from the allowed flip; the only recolour is the Futuristic tint on 157/158 at blend 0.3; card data verbatim from the API record; tier == API rarity); every art file's finish is its rarity's recipe and its text half carries the rarity's frame colour; 84 foil cards have 16-frame anims (normal + shiny) whose last frame equals the static art; the 65 commons have no background and no anim. Forms: Alolan / Galarian / Hisuian sprites on those cards, lycanroc-midnight (85, 138), zacian-crowned / zamazenta-crowned, cherrim-sunshine, vivillon-poke-ball, toxtricity-low-key on 59 and amped on 60 / 134 (read off the crests), minior-red.

Coverage: setlist.json has 161 cards; all 149 buildable ones are built. Skipped: 9 Gen 9 cards with no colorscripts sprite (Fuecoco ex 15 / 147, Miraidon 62, Gimmighoul 81, Koraidon 86, Gholdengo 108 / 142, Maushold 125 / 146) and 3 Trainers (Poké Pad 126, Switch 127, Ultra Ball 128).

Fixes are in batch_fixes.py (owning batch module loaded by path, one per-card setting overridden); before copies in work/audit/before/, real | before | after in audit/fixed.png.

| id | name | tier | status | reason |
|---|---|---|---|---|
| me55-B | Mew | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-G | Mew | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-R | Mew | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-1 | Exeggcute | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-2 | Alolan Exeggutor | Common | ok | plain sprite, no background, no anim, sprite exeggutor-alola; sprite, facing, scene, data OK |
| me55-3 | Volbeat | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-4 | Illumise | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-5 | Tropius | Common | flagged | Common: the card's Tropius faces right (head top right); the plain sprite faces left. Commons are never flipped (Vulpix rule), so left as is. |
| me55-6 | Cherubi | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-7 | Cherrim | Common | ok | plain sprite, no background, no anim, sprite cherrim-sunshine; sprite, facing, scene, data OK |
| me55-8 | Vivillon | Common | ok | plain sprite, no background, no anim, sprite vivillon-poke-ball; sprite, facing, scene, data OK |
| me55-9 | Vulpix | Common | ok | approved ladder card; plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-10 | Ninetales | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-11 | Moltres | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-12 | Ho-Oh | Rare | ok | ME rare holo (Mew 65 recipe), 16-frame holo anim; sprite, facing, scene, data OK |
| me55-13 | Victini | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-14 | Reshiram | Rare | ok | ME rare holo (Mew 65 recipe), 16-frame holo anim; sprite, facing, scene, data OK |
| me55-15 | Fuecoco ex | Double Rare | skipped | no colorscripts sprite (fuecoco, Gen 9) |
| me55-16 | Slowpoke | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-17 | Lapras | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-18 | Articuno | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-19 | Kyogre | Rare | ok | ME rare holo (Mew 65 recipe), 16-frame holo anim; sprite, facing, scene, data OK |
| me55-20 | Palkia | Rare | ok | ME rare holo (Mew 65 recipe), 16-frame holo anim; sprite, facing, scene, data OK |
| me55-21 | Greninja ex | Double Rare | ok | silver frame + sparkle grain (Umbreon 92), 16-frame ex anim; sprite, facing, scene, data OK |
| me55-22 | Wishiwashi | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-23 | Pikachu | Pikachu Rare | ok | approved ladder card; fireworks lattice + yellow bevel (Pikachu 23), 16-frame fireworks anim; sprite, facing, scene, data OK |
| me55-24 | Pikachu | Pikachu Rare | ok | fireworks lattice + yellow bevel (Pikachu 23), 16-frame fireworks anim; sprite, facing, scene, data OK |
| me55-25 | Pikachu | Pikachu Rare | ok | fireworks lattice + yellow bevel (Pikachu 23), 16-frame fireworks anim; sprite, facing, scene, data OK |
| me55-26 | Pikachu | Pikachu Rare | fixed | mask missed the lower tail zigzag and the right paw, left as a tan ghost at the art's right. Both added to the mask, re-rendered with Pikachu 23's recipe (batch_fixes.py), verified, imported. |
| me55-27 | Pikachu | Pikachu Rare | ok | fireworks lattice + yellow bevel (Pikachu 23), 16-frame fireworks anim; sprite, facing, scene, data OK |
| me55-28 | Pikachu | Pikachu Rare | ok | fireworks lattice + yellow bevel (Pikachu 23), 16-frame fireworks anim; sprite, facing, scene, data OK |
| me55-29 | Pikachu | Pikachu Rare | ok | fireworks lattice + yellow bevel (Pikachu 23), 16-frame fireworks anim; sprite, facing, scene, data OK |
| me55-30 | Pikachu | Pikachu Rare | ok | fireworks lattice + yellow bevel (Pikachu 23), 16-frame fireworks anim; sprite, facing, scene, data OK |
| me55-31 | Pikachu | Pikachu Rare | ok | fireworks lattice + yellow bevel (Pikachu 23), 16-frame fireworks anim; sprite, facing, scene, data OK |
| me55-32 | Pikachu | Pikachu Rare | ok | fireworks lattice + yellow bevel (Pikachu 23), 16-frame fireworks anim; sprite, facing, scene, data OK |
| me55-33 | Pikachu | Pikachu Rare | ok | fireworks lattice + yellow bevel (Pikachu 23), 16-frame fireworks anim; sprite, facing, scene, data OK |
| me55-34 | Pikachu | Pikachu Rare | ok | fireworks lattice + yellow bevel (Pikachu 23), 16-frame fireworks anim; sprite, facing, scene, data OK |
| me55-35 | Pikachu | Pikachu Rare | ok | fireworks lattice + yellow bevel (Pikachu 23), 16-frame fireworks anim; sprite, facing, scene, data OK |
| me55-36 | Pikachu | Pikachu Rare | ok | fireworks lattice + yellow bevel (Pikachu 23), 16-frame fireworks anim; sprite, facing, scene, data OK |
| me55-37 | Pikachu | Pikachu Rare | ok | fireworks lattice + yellow bevel (Pikachu 23), 16-frame fireworks anim; sprite, facing, scene, data OK |
| me55-38 | Pikachu | Pikachu Rare | ok | fireworks lattice + yellow bevel (Pikachu 23), 16-frame fireworks anim; sprite, facing, scene, data OK |
| me55-39 | Pikachu | Pikachu Rare | ok | fireworks lattice + yellow bevel (Pikachu 23), 16-frame fireworks anim; sprite, facing, scene, data OK |
| me55-40 | Pikachu | Pikachu Rare | ok | fireworks lattice + yellow bevel (Pikachu 23), 16-frame fireworks anim; sprite, facing, scene, data OK |
| me55-41 | Pikachu | Pikachu Rare | ok | fireworks lattice + yellow bevel (Pikachu 23), 16-frame fireworks anim; sprite, facing, scene, data OK |
| me55-42 | Pikachu | Pikachu Rare | ok | fireworks lattice + yellow bevel (Pikachu 23), 16-frame fireworks anim; sprite, facing, scene, data OK |
| me55-43 | Pikachu | Pikachu Rare | ok | fireworks lattice + yellow bevel (Pikachu 23), 16-frame fireworks anim; sprite, facing, scene, data OK |
| me55-44 | Pikachu | Pikachu Rare | flagged | the card's own after-image Pikachus stay in the fill as yellow blobs around the sprite. They are part of the scene, but they can read as ghosts. Taste call. |
| me55-45 | Pikachu | Pikachu Rare | ok | fireworks lattice + yellow bevel (Pikachu 23), 16-frame fireworks anim; sprite, facing, scene, data OK |
| me55-46 | Pikachu | Pikachu Rare | ok | fireworks lattice + yellow bevel (Pikachu 23), 16-frame fireworks anim; sprite, facing, scene, data OK |
| me55-47 | Pikachu | Pikachu Rare | ok | fireworks lattice + yellow bevel (Pikachu 23), 16-frame fireworks anim; sprite, facing, scene, data OK |
| me55-48 | Pikachu | Pikachu Rare | ok | fireworks lattice + yellow bevel (Pikachu 23), 16-frame fireworks anim; sprite, facing, scene, data OK |
| me55-49 | Pikachu | Pikachu Rare | ok | fireworks lattice + yellow bevel (Pikachu 23), 16-frame fireworks anim; sprite, facing, scene, data OK |
| me55-50 | Pikachu | Pikachu Rare | ok | fireworks lattice + yellow bevel (Pikachu 23), 16-frame fireworks anim; sprite, facing, scene, data OK |
| me55-51 | Pikachu | Pikachu Rare | ok | fireworks lattice + yellow bevel (Pikachu 23), 16-frame fireworks anim; sprite, facing, scene, data OK |
| me55-52 | Pikachu | Pikachu Rare | ok | fireworks lattice + yellow bevel (Pikachu 23), 16-frame fireworks anim; sprite, facing, scene, data OK |
| me55-53 | Pikachu ex | Double Rare | ok | silver frame + sparkle grain (Umbreon 92), 16-frame ex anim; sprite, facing, scene, data OK |
| me55-54 | Pikachu ex | Double Rare | ok | silver frame + sparkle grain (Umbreon 92), 16-frame ex anim; sprite, facing, scene, data OK |
| me55-55 | Zapdos | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-56 | Zekrom | Rare | ok | ME rare holo (Mew 65 recipe), 16-frame holo anim; sprite, facing, scene, data OK |
| me55-57 | Zeraora | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-58 | Toxel | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-59 | Toxtricity | Common | ok | plain sprite, no background, no anim, sprite toxtricity-low-key; sprite, facing, scene, data OK |
| me55-60 | Toxtricity | Common | ok | plain sprite, no background, no anim, sprite toxtricity; sprite, facing, scene, data OK |
| me55-61 | Morpeko | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-62 | Miraidon | Rare | skipped | no colorscripts sprite (miraidon, Gen 9) |
| me55-63 | Mewtwo | Rare | ok | ME rare holo (Mew 65 recipe), 16-frame holo anim; sprite, facing, scene, data OK |
| me55-64 | Mewtwo ex | Double Rare | ok | silver frame + sparkle grain (Umbreon 92), 16-frame ex anim; sprite, facing, scene, data OK |
| me55-65 | Mew | Rare | ok | approved ladder card; ME rare holo (Mew 65 recipe), 16-frame holo anim; sprite, facing, scene, data OK |
| me55-66 | Mew ex | Double Rare | fixed | faced right; the card's Mew faces left (head and eye lower left, tail up behind to the right). Re-rendered flipped with Umbreon 92's ex recipe (batch_fixes.py), verified, imported. |
| me55-67 | Marill | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-68 | Azumarill | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-69 | Espeon | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-70 | Espeon ex | Double Rare | ok | silver frame + sparkle grain (Umbreon 92), 16-frame ex anim; sprite, facing, scene, data OK |
| me55-71 | Sylveon ex | Double Rare | ok | silver frame + sparkle grain (Umbreon 92), 16-frame ex anim; sprite, facing, scene, data OK |
| me55-72 | Unown | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-73 | Drifloon | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-74 | Cresselia | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-75 | Chandelure | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-76 | Xerneas | Rare | ok | ME rare holo (Mew 65 recipe), 16-frame holo anim; sprite, facing, scene, data OK |
| me55-77 | Comfey | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-78 | Cosmog | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-79 | Cosmoem | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-80 | Lunala | Rare | ok | ME rare holo (Mew 65 recipe), 16-frame holo anim; sprite, facing, scene, data OK |
| me55-81 | Gimmighoul | Common | skipped | no colorscripts sprite (gimmighoul, Gen 9) |
| me55-82 | Groudon | Rare | ok | ME rare holo (Mew 65 recipe), 16-frame holo anim; sprite, facing, scene, data OK |
| me55-83 | Lucario | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-84 | Seismitoad | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-85 | Lycanroc | Common | ok | plain sprite, no background, no anim, sprite lycanroc-midnight; sprite, facing, scene, data OK |
| me55-86 | Koraidon | Rare | skipped | no colorscripts sprite (koraidon, Gen 9) |
| me55-87 | Nidoran ♀ | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-88 | Nidorina | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-89 | Alolan Meowth | Common | ok | plain sprite, no background, no anim, sprite meowth-alola; sprite, facing, scene, data OK |
| me55-90 | Gengar ex | Double Rare | ok | silver frame + sparkle grain (Umbreon 92), 16-frame ex anim; sprite, facing, scene, data OK |
| me55-91 | Umbreon | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-92 | Umbreon ex | Double Rare | ok | approved ladder card; silver frame + sparkle grain (Umbreon 92), 16-frame ex anim; sprite, facing, scene, data OK |
| me55-93 | Murkrow | Common | flagged | Common: the card's Murkrow faces right; the sprite faces left. Left unflipped (commons rule). |
| me55-94 | Scraggy | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-95 | Zorua | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-96 | Zoroark | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-97 | Deino | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-98 | Zweilous | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-99 | Hydreigon | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-100 | Yveltal | Rare | ok | ME rare holo (Mew 65 recipe), 16-frame holo anim; sprite, facing, scene, data OK |
| me55-101 | Galarian Meowth | Common | ok | plain sprite, no background, no anim, sprite meowth-galar; sprite, facing, scene, data OK |
| me55-102 | Jirachi ex | Double Rare | ok | silver frame + sparkle grain (Umbreon 92), 16-frame ex anim; sprite, facing, scene, data OK |
| me55-103 | Dialga | Rare | ok | ME rare holo (Mew 65 recipe), 16-frame holo anim; sprite, facing, scene, data OK |
| me55-104 | Ferrothorn | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-105 | Solgaleo | Rare | ok | ME rare holo (Mew 65 recipe), 16-frame holo anim; sprite, facing, scene, data OK |
| me55-106 | Zacian | Rare | ok | ME rare holo (Mew 65 recipe), 16-frame holo anim, sprite zacian-crowned; sprite, facing, scene, data OK |
| me55-107 | Zamazenta | Rare | ok | ME rare holo (Mew 65 recipe), 16-frame holo anim, sprite zamazenta-crowned; sprite, facing, scene, data OK |
| me55-108 | Gholdengo | Common | skipped | no colorscripts sprite (gholdengo, Gen 9) |
| me55-109 | Salamence ex | Double Rare | ok | silver frame + sparkle grain (Umbreon 92), 16-frame ex anim; sprite, facing, scene, data OK |
| me55-110 | Jangmo-o | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-111 | Hakamo-o | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-112 | Kommo-o | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-113 | Meowth | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-114 | Kangaskhan | Common | flagged | Common: the card's Kangaskhan faces right (head up right); the sprite faces left. Left unflipped (commons rule). |
| me55-115 | Ditto | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-116 | Eevee | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-117 | Eevee | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-118 | Eevee | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-119 | Snorlax | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-120 | Igglybuff | Common | ok | plain sprite, no background, no anim; sprite, facing, scene, data OK |
| me55-121 | Lugia | Rare | ok | ME rare holo (Mew 65 recipe), 16-frame holo anim; sprite, facing, scene, data OK |
| me55-122 | Hisuian Zorua | Common | ok | plain sprite, no background, no anim, sprite zorua-hisui; sprite, facing, scene, data OK |
| me55-123 | Hisuian Zoroark | Common | ok | plain sprite, no background, no anim, sprite zoroark-hisui; sprite, facing, scene, data OK |
| me55-124 | Minior | Common | ok | plain sprite, no background, no anim, sprite minior-red; sprite, facing, scene, data OK |
| me55-125 | Maushold | Common | skipped | no colorscripts sprite (maushold, Gen 9) |
| me55-126 | Poké Pad | Common | skipped | Trainer (no Pokemon) |
| me55-127 | Switch | Common | skipped | Trainer (no Pokemon) |
| me55-128 | Ultra Ball | Common | skipped | Trainer (no Pokemon) |
| me55-129 | Alolan Exeggutor | Illustration Rare | fixed | art was 57 lines (114 px), over the pack's 110 px art cap, so the import refused it. Same crop two sprite rows shorter (55 lines, sprite whole), Lapras 131's recipe (batch_fixes.py), verified, imported. |
| me55-130 | Moltres | Illustration Rare | ok | subtle etch, vivid painting (Lapras 131), 16-frame etch anim; sprite, facing, scene, data OK |
| me55-131 | Lapras | Illustration Rare | ok | approved ladder card; subtle etch, vivid painting (Lapras 131), 16-frame etch anim; sprite, facing, scene, data OK |
| me55-132 | Articuno | Illustration Rare | ok | subtle etch, vivid painting (Lapras 131), 16-frame etch anim; sprite, facing, scene, data OK |
| me55-133 | Zapdos | Illustration Rare | ok | subtle etch, vivid painting (Lapras 131), 16-frame etch anim; sprite, facing, scene, data OK |
| me55-134 | Toxtricity | Illustration Rare | ok | subtle etch, vivid painting (Lapras 131), 16-frame etch anim, sprite toxtricity; sprite, facing, scene, data OK |
| me55-135 | Morpeko | Illustration Rare | ok | subtle etch, vivid painting (Lapras 131), 16-frame etch anim; sprite, facing, scene, data OK |
| me55-136 | Drifloon | Illustration Rare | ok | subtle etch, vivid painting (Lapras 131), 16-frame etch anim; sprite, facing, scene, data OK |
| me55-137 | Chandelure | Illustration Rare | ok | subtle etch, vivid painting (Lapras 131), 16-frame etch anim; sprite, facing, scene, data OK |
| me55-138 | Lycanroc | Illustration Rare | ok | subtle etch, vivid painting (Lapras 131), 16-frame etch anim, sprite lycanroc-midnight; sprite, facing, scene, data OK |
| me55-139 | Alolan Meowth | Illustration Rare | ok | subtle etch, vivid painting (Lapras 131), 16-frame etch anim, sprite meowth-alola; sprite, facing, scene, data OK |
| me55-140 | Scraggy | Illustration Rare | flagged | the big Scraggy face fills the card, so the fill is smooth (texture=False) and the scene is a soft colour smear with the small cameo Scraggys as orange blobs. Weakest scene in the set. |
| me55-141 | Galarian Meowth | Illustration Rare | ok | subtle etch, vivid painting (Lapras 131), 16-frame etch anim, sprite meowth-galar; sprite, facing, scene, data OK |
| me55-142 | Gholdengo | Illustration Rare | skipped | no colorscripts sprite (gholdengo, Gen 9) |
| me55-143 | Kommo-o | Illustration Rare | ok | subtle etch, vivid painting (Lapras 131), 16-frame etch anim; sprite, facing, scene, data OK |
| me55-144 | Meowth | Illustration Rare | ok | subtle etch, vivid painting (Lapras 131), 16-frame etch anim; sprite, facing, scene, data OK |
| me55-145 | Hisuian Zorua | Illustration Rare | ok | subtle etch, vivid painting (Lapras 131), 16-frame etch anim, sprite zorua-hisui; sprite, facing, scene, data OK |
| me55-146 | Maushold | Illustration Rare | skipped | no colorscripts sprite (maushold, Gen 9) |
| me55-147 | Fuecoco ex | Special Illustration Rare | skipped | no colorscripts sprite (fuecoco, Gen 9) |
| me55-148 | Greninja ex | Special Illustration Rare | ok | textured painting + pearl lustre (Gengar 154), 16-frame sir anim; sprite, facing, scene, data OK |
| me55-149 | Pikachu ex | Special Illustration Rare | ok | textured painting + pearl lustre (Gengar 154), 16-frame sir anim; sprite, facing, scene, data OK |
| me55-150 | Pikachu ex | Special Illustration Rare | ok | textured painting + pearl lustre (Gengar 154), 16-frame sir anim; sprite, facing, scene, data OK |
| me55-151 | Mewtwo ex | Special Illustration Rare | ok | textured painting + pearl lustre (Gengar 154), 16-frame sir anim; sprite, facing, scene, data OK |
| me55-152 | Mew ex | Special Illustration Rare | flagged | the card's Mew is curled, facing ambiguous; ours is unflipped (faces right). Check. |
| me55-153 | Sylveon ex | Special Illustration Rare | ok | textured painting + pearl lustre (Gengar 154), 16-frame sir anim; sprite, facing, scene, data OK |
| me55-154 | Gengar ex | Special Illustration Rare | ok | approved ladder card; textured painting + pearl lustre (Gengar 154), 16-frame sir anim; sprite, facing, scene, data OK |
| me55-155 | Jirachi ex | Special Illustration Rare | ok | textured painting + pearl lustre (Gengar 154), 16-frame sir anim; sprite, facing, scene, data OK |
| me55-156 | Salamence ex | Special Illustration Rare | ok | textured painting + pearl lustre (Gengar 154), 16-frame sir anim; sprite, facing, scene, data OK |
| me55-157 | Mewtwo ex | Futuristic Rare | ok | approved ladder card; chrome + red-black sprite tint <=0.3 (Mewtwo 157), 16-frame chrome anim; sprite, facing, scene, data OK |
| me55-158 | Mew ex | Futuristic Rare | flagged | Futuristic tint falls back to the card's darkest tone (little red on the card). At blend 0.3 it barely reads: the sprite looks plain pink next to Mewtwo 157. Taste call on whether it should read more. |
