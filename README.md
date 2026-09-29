# pokeshell

Every new Windows Terminal PowerShell tab is a trading-card pack pull.

[![pokeshell: every new tab is a pack (32 s video)](docs/media/promo-poster.png)](docs/media/promo.mp4)

*Click for the 32 s video: real Windows Terminal pulls from Evolving Skies, the foil shaders, the card animations,
the earn line and both binders.*

Every pull is a **real printed card**: the Pokemon's pixel sprite over that card's scene, framed like a card with
its name, printed number and rarity. Most tabs pull a common, which prints right there. Rarer cards (rare holo,
rare ultra, illustration rare, rare secret, hyper rare, ...) reopen the tab (same folder) wearing an animated
holofoil pixel-shader skin that matches the rarity (cosmos, sunpillar, illustration rare, gold, ...). A card with an
approved effect animation (its `.anim`, built with the card) then plays it over its art while the tab is idle: the
card prints at once, the effect loops at 12 fps until you type (at most 30 s), and the key you pressed is the first
character at the prompt. Every pull goes into your binder (`pokeshell binder`).

It's a fan project, not affiliated with the owners of the characters (see [Disclaimer](#disclaimer)).

> **The Pokemon card art is built locally and is not in this repository.** It embeds the
> [pokemon-colorscripts](https://gitlab.com/phoneybadger/pokemon-colorscripts) sprites (Nintendo artwork), and the
> card text is copyrighted, so `tools/build_realcards.py` assembles it on your machine and git ignores the output.
> A plain clone (or the Gallery module) has the `pokemon` pack's odds, tiers, card list and shaders, but no card
> art: until it is built, the pack has nothing to pull and new tabs print nothing. How the public version will get
> its cards (built at install, or a local-only pack) is still open.

## Packs and odds

### Pokemon (`pokemon`): real cards, one tier per printed rarity, 18 foil skins

The pack is a list of real cards keyed by their [pokemontcg.io](https://pokemontcg.io) id (`swsh4-170` is Pikachu V,
Vivid Voltage 170/185). A card's tier is its **printed rarity**: `pack.json` has one tier per real rarity (common,
uncommon, rare, reverse holo, rare holo, rare holo V / VMAX / VSTAR, double rare, rare shiny, amazing rare, radiant
rare, rare ultra, illustration rare, rare rainbow, rare secret, special illustration rare, hyper rare, ...), each with
an odds weight, its holofoil skins and its card frame. A pull picks a tier by weight among the tiers that have a card,
then one of that tier's cards; nothing invented is ever shown. With the cards built so far:

| tier | odds | about 1 tab in | cards | skins |
|---|---:|---:|---|---|
| common | 87.20% | 1.1 | base1-44 Bulbasaur, base1-46 Charmander, base1-58 Pikachu, base1-63 Squirtle | none (plain tab) |
| rare holo | 8.72% | 11 | cel25-5 Pikachu | starlight, cosmos, cracked-ice, sheen, tinsel, water-web, crosshatch |
| rare shiny | 0.87% | 115 | sma-SV6 Charmander | shiny-vault |
| rare ultra | 1.13% | 88 | swsh4-170 Pikachu V | sunpillar, illustration-rare |
| illustration rare | 1.31% | 76 | sv3pt5-166 Bulbasaur, sv3pt5-168 Charmander, sv3pt5-170 Squirtle | illustration-rare |
| rare secret | 0.44% | 229 | ex3-98 Charmander | gold, rainbow-rare |
| hyper rare | 0.33% | 302 | sv8-247 Pikachu ex | gold |

Any pull, of any tier, is **shiny** (alternate palette) 1 time in 64. The odds and skins are data in
`packs/pokemon/pack.json` (format: `docs/PACK_FORMAT.md`); `pokeshell odds` always prints the live numbers, down to
"1 in N" for one specific card. New cards are added with `tools/build_realcards.py import <batch>`
(`tools/README.md`). More packs can be added under `packs/`; with several installed, `pokeshell pack all` makes each
tab first pick a pack at random.

## Requirements

- Windows 10/11 with **Windows Terminal 1.19 or newer** (pixel shaders, `WT_PROFILE_ID`)
- **Windows PowerShell 5.1** (built in) or **PowerShell 7**
- Nothing else. No Python, no other modules. The startup code is compiled once at install time with the C# compiler
  that ships with Windows / PowerShell. (Python is only needed to rebuild the art, see `tools/README.md`.)

## Install

From the [PowerShell Gallery](https://www.powershellgallery.com/packages/pokeshell):

```powershell
Install-Module pokeshell -Scope CurrentUser
pokeshell install
```

(On a fresh Windows PowerShell 5.1, `Install-Module` may first ask to install the NuGet provider: answer `Y`.)

`pokeshell install`:

1. copies what new tabs need (the profile hook, the startup core's source, the packs' shaders and art) into
   `%LOCALAPPDATA%\pokeshell\current`, a folder that stays put when the module is updated,
2. backs up Windows Terminal's `settings.json` to `%LOCALAPPDATA%\pokeshell\backups\`,
3. adds one **hidden** profile per shader of every pack (`pokeshell: pokemon/cosmos`, ...) to `settings.json`,
   pointing at the shaders in that folder. It edits only that list, as text, so your comments, formatting and
   every other setting stay byte-for-byte intact; it verifies the result (it parses, every skin is there, and
   removing them again gives back exactly the other settings) before writing anything. Windows Terminal reloads
   the file live. (Profiles go into `settings.json` rather than a settings fragment because fragments only load
   when Windows Terminal restarts.)
4. compiles the startup core, and
5. prints the one line to add to your PowerShell profile. It does not edit `$PROFILE` for you:

```powershell
notepad $PROFILE     # add the printed line:
. "$env:LOCALAPPDATA\pokeshell\current\scripts\pokeshell-profile.ps1"
```

Put it near the top so the art is the first thing in the tab. Open a new tab.

The line runs a small script, not the module: importing a module costs 50-100 ms per tab, the hook's budget is
~50 ms. It also defines `pokeshell` for that shell, which always runs the newest installed version of the module.

Options: `pokeshell install -SettingsPath <file>` for a specific `settings.json` (the default finds the Store,
Preview or unpackaged install), `-Shell pwsh` to run the skinned tabs with PowerShell 7. Safe to re-run.

Note: `Install-Module` from PowerShell 7 installs into `Documents\PowerShell\Modules`, which Windows PowerShell
doesn't search (and vice versa). Tabs don't care (they run from `%LOCALAPPDATA%\pokeshell\current`, and the
`pokeshell` the profile line defines finds the module in either folder); only a shell without the profile line
needs the module installed for its own edition.

### From source

```powershell
git clone https://github.com/gshklovs/pokeshell
cd pokeshell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

Same steps, except tabs run straight from the checkout (nothing is copied), so edits to shaders and packs show up
in new tabs right away. The printed line points into the repo, e.g. `. "C:\path\to\pokeshell\scripts\pokeshell-profile.ps1"`.
Re-run the installer after adding a pack or a shader, or after moving the repo folder.

## Update

```powershell
pokeshell update          # Update-Module pokeshell, then pokeshell install from the new version
```

or by hand: `Update-Module pokeshell`, then `pokeshell install`. Until you re-run install, new tabs keep using
the previous version's copy in `%LOCALAPPDATA%\pokeshell\current` (and `pokeshell` reminds you). Your `$PROFILE`
line and the Windows Terminal profiles don't change, and old module versions can be removed at any time
(`Uninstall-Module pokeshell -RequiredVersion <old>`). From source: `git pull`, then `.\install.ps1`.
`pokeshell version` shows which version is running and which one new tabs use.

## Uninstall

```powershell
pokeshell uninstall            # removes exactly the profiles install added (backs up first); keeps your binder
pokeshell uninstall -Purge     # also deletes %LOCALAPPDATA%\pokeshell (pull log, settings, backups, current)
Uninstall-Module pokeshell -AllVersions
```

Then delete the line from `$PROFILE` (until you do, tabs keep printing common pulls from
`%LOCALAPPDATA%\pokeshell\current`; after `-Purge` the line fails, so remove it first). From source:
`.\uninstall.ps1 [-Purge]`. To just pause it: `pokeshell off` (and `pokeshell on`).
## Commands

| command | what it does |
|---|---|
| `pokeshell pack [<pack>\|all]` | show or choose the pack new tabs pull from |
| `pokeshell odds [pack]` | the odds, per tier and per skin |
| `pokeshell binder` (or just `binder`) | the binder app, full screen in this tab; `q` gives the prompt back as it was. Opens on your newest pull; `--pull <id>`, `--card <pack/character/tier>` or `--card pokemon/<card id>`, `--set <set id>` (a set's checklist), `--search <query>`. Without the app built (`binder\build.ps1`) it prints the text binder |
| `pokeshell binder --web` | rebuilds the static web binder into `%LOCALAPPDATA%\pokeshell\web` (about a second; needs Python with Pillow) and opens it |
| `pokeshell collection` | the text binder: per pack, every character x tier you've earned, shiny counts, completion, best pulls, how many are pending; pulls of retired art, or of cards whose art isn't built, are left out |
| `pokeshell earn [first-command\|minutes:N\|off]` | what earns a pull: the first command you run in its tab (default), its tab staying open N minutes, or nothing (`off`: every pull counts at once) |
| `pokeshell hotkey [on\|off] [-Keys ctrl+shift+b]` | a Windows Terminal key that opens the binder in a split pane next to your work (added to `settings.json` like the skins, backed up first; `off` or `pokeshell uninstall` removes it) |
| `pokeshell urlhandler [on\|off] [-DryRun]` | registers `pokeshell://` links (under `HKCU\Software\Classes`) so the `binder ⏎` link under a pulled card opens the binder on that card; `-DryRun` only lists the registry changes |
| `pokeshell show <pack>/<character> [variant] [-shiny] [-picture\|-card]` | print a card (`pokeshell show` lists everything built); `-picture` / `-card` override the display setting |
| `pokeshell display [card\|picture]` | how pulls print: `card` (default) is the full card (a framed card for packs with tier frames, otherwise the art plus the `label : name` line); `picture` is just the art. Saved in `config.txt`; `$env:POKESHELL_DISPLAY = 'picture'` overrides it for one shell (and the foil tabs it opens) |
| `pokeshell holo [<skin>\|plain] [-s] [-r]` | open a skinned tab here; `-s` splits a pane instead; `-r` moves the Claude Code session running in this tab into the new one (`claude --resume`), e.g. from inside Claude Code: `! pokeshell holo -r cosmos` |
| `pokeshell color <name\|#hex\|reset>` | tint this tab (35 named colors; other CSS color names work too and are logged to `color-misses.log`) |
| `pokeshell colorwatch [on\|off]` | optional: tint each tab to match the `/color` of the Claude Code session running in it |
| `pokeshell on` / `off` | enable / disable startup pulls |
| `pokeshell install` / `uninstall` / `update` / `version` | see [Install](#install), [Update](#update), [Uninstall](#uninstall) |

`scripts\pokeshell.cmd` runs the same command from cmd, bash or Claude Code's `!` if you put its folder on your PATH:
`%LOCALAPPDATA%\pokeshell\current\scripts` for a module install (it survives updates), `scripts\` in a checkout.

## How it works

### The startup pull

`scripts/pokeshell-profile.ps1` runs from your profile in every new shell. For a fresh tab of your plain
PowerShell profile it rolls: pick a pack, then foil or not (`foil_chance`), then a skin weighted across the foil
tiers (the tier it belongs to sets the label and which art variant shows), a character uniformly, and shiny
(`shiny_chance`). A real-card pack (like `pokemon`) instead picks a rarity tier by its weight, one of that tier's
cards, and one of the tier's skins (tiers without skins print in the plain tab).

- **common**: print `dist/<pack>/<character>-<art>[-shiny].ans` and the banner, right there (a real card's art is
  `dist/<pack>/<character>-<card id>[-shiny].ans`).
- **foil**: open a new tab (or a split pane, if this is a pane) with the skin's hidden profile, in the same folder,
  which prints the art and banner; then this tab exits with code 0, so Windows Terminal closes it and the skinned
  tab takes its place.

Every pull is logged to `%LOCALAPPDATA%\pokeshell\pulls.log`, with a pull id, as **pending**: you earn the card by
using its tab (below). A small `binder ⏎` link under the card opens the binder on it.

It's fast: Windows PowerShell 5.1 pays about a millisecond the first time each line of script runs, so the
decision logic is C# (`scripts/lib/Pokeshell.cs`, compiled once to `%LOCALAPPDATA%\pokeshell\pokeshell-core-*.dll`),
the roll table is a prebuilt TSV cache, and the art is a prebuilt ANSI file. A tab adds ~20 ms when it doesn't
roll and ~25-50 ms for a common pull (`tests/measure-startup.ps1` measures it on your machine).

**Why pulled tabs take about half a second:** Windows Terminal compiles a profile's pixel shader when a tab with
that profile opens. The foil tab appears, compiles its skin, then prints. That's also why a foil tab starts a
beat after the plain one closes.

### The binder and the earned rule

A card only goes into your binder once you use the tab it was pulled in:

1. **Roll**: every pull gets an id (a ULID) and is logged `pending`; the tab carries it as `POKESHELL_PULL` (a foil's
   skinned tab too).
2. **First use**: the tab's first real command (anything that lands in the history; an empty Enter doesn't count)
   appends `earned:<id>` to `pulls.log` and prints one dim line: `✦ Pikachu holo added to your binder`. The hook is a
   few lines in the compiled core (a `PreCommandLookupAction` that wraps whatever `prompt` you have, so prompt themes
   and a `function prompt` later in `$PROFILE` keep working); it removes itself once the pull is earned.
3. **Closed unused**: a pending pull expires after 24 hours or when the machine restarts (the log then gets
   `expired:<id>`). Expired pulls never show.
4. **In the binder**: a card you haven't looked at yet has a **NEW** sticker (`viewed.txt` remembers what you've seen);
   pending cards show greyed out.

Four ways in: `binder` / `pokeshell binder` (the app, full screen; `q` returns), the `pokeshell hotkey` key (a split
pane), the `binder ⏎` link under a pulled card (`pokeshell urlhandler on`; Windows Terminal may only open http(s) links,
in which case the hint tells you what to type), and `binder --web` (a static page). In the app: arrows / `hjkl` move,
`1`-`9` switch packs, `S` cycles a pack's sets (a set page is that set's whole checklist, with empty pockets for the
cards you haven't pulled), `/` searches, `v` shows the card's text half (HP, attacks, weakness) under the art when
`packs/<pack>/cards/<card id>.json` exists, `d` toggles one-slot-per-character, `?` lists the rest.

**Tags and search** (the app and the web page): every card is tagged with its set (id and name), printed rarity and
tier, subtypes (V, VMAX...), types (Grass, Water...), character, artist and pack, plus `shiny`, `foil`, `new` and
`pending` from your pulls. Search with words and tag filters, e.g. `evolving skies`, `set:swsh7`,
`rarity:"rare rainbow"`, `type:water vmax`, `artist:"PLANETA Tsuji"`, `shiny`. In the web binder, the tag chips on a
card's page run that search, and each set has its own divider tab.

The app is Rust (`binder/`, ratatui): `powershell -File binder\build.ps1` builds it into
`binder\target\release\binder.exe` with the MSVC toolchain (`cargo +stable-x86_64-pc-windows-msvc`).

### Where a foil opens

`wt.exe -w 0` means "the most recently used window", which is only this tab's window if that window is in the
foreground. So before replacing itself, a foil pull briefly sets a unique tab title and looks for it with UI
Automation in the foreground Windows Terminal window (~150 ms, foil pulls only). Found as the only pane of the
selected tab: new tab. Found as one pane of a split: new split pane in its place. Not found (the tab opened in a
background window, focus moved away, or your profile sets `suppressApplicationTitle`): the pull shows here as a
common instead, and nothing else is opened.

New tabs open at the end of the tab row unless you set `"newTabPosition": "afterCurrentTab"` in Windows Terminal;
since a new tab is normally the last one anyway, the skinned tab lands where the plain one was either way.

### Safety: it can't spawn tabs in a loop

A tab that opens a tab is one bug away from a fork bomb, so there are independent layers, and each one alone
stops it (`tests/test-no-loop.ps1` checks every one of them, plus the worst case where all identity checks fail):

1. **Profile identity**: only rolls when `WT_PROFILE_ID` is one of your plain profiles. Skinned tabs have their
   own profile GUIDs.
2. **No arguments**: only rolls when the shell was started with no command-line arguments (`-NoLogo` is allowed).
   The pulled tab is started with `-NoExit -EncodedCommand`; scripts, `-Command`, Claude tabs never roll.
3. **Environment markers**: `POKESHELL_PULL` (set before spawning, and in the pulled tab) and `POKESHELL_ROLLED`
   (set in every tab once it has rolled, so a `powershell` you start inside a tab never rolls), and `CARDSHELL_ROLLED`,
   shared with [opshell](#coexistence-with-opshell) (see below).
4. **Machine-wide rate limit**: a lock file (`spawn-gate.txt`) allows at most one foil spawn every 3 seconds
   across all tabs; a sixth spawn within 60 seconds trips a 10-minute breaker during which every pull is a common.
   Tested with 12 processes racing for the lock at the same instant: exactly one wins.
5. **Placement**: a foil only replaces a tab it has positively found in the foreground window (above).
6. **Installed skins only**: skins that `pokeshell install` hasn't registered never drop; before install, every
   pull is a common.
7. **Kill switch**: `pokeshell off`, or `POKESHELL_DISABLE=1` in the environment.

If opening the tab fails for any reason, the pull prints in place and the tab stays open.

### Coexistence with opshell

[opshell](https://github.com/gshklovs/opshell) is the One Piece sister project on the same engine (its own
command, module, state folder, Windows Terminal profiles and compiled core, so both install side by side). If your
`$PROFILE` has both hook lines, only one of them pulls per tab: whichever hook rolls first sets
`CARDSHELL_ROLLED=1` in the tab's environment, and both hooks skip when it is set. So the hook listed first in
`$PROFILE` pulls in every tab; to alternate, keep only one line, or switch with `pokeshell off` / `opshell off`.
(opshell also skips when `POKESHELL_ROLLED` is set, so this holds with pokeshell 0.1.0 too, as long as the
pokeshell line comes first.)

### Packs, art and shaders

A pack is a folder `packs/<id>/`:

- `pack.json`: odds, tiers, characters (format: `docs/PACK_FORMAT.md`)
- `art/<character>.json`: pixel art as palette-indexed rows, one variant per tier art name, optional shiny
  palette (format and size limits: `docs/ART_FORMAT.md`)
- `shaders/<skin>.hlsl`: Windows Terminal pixel shaders, one per foil skin (spec: `docs/SHADER_SPEC.md`)

`tools/build_art.py` renders the art to `dist/<pack>/<character>-<variant>[-shiny].ans` (24-bit color, two
pixels per character cell with half blocks). `dist/` is committed, so users never need Python, except for the
real-card `pokemon` pack: its `art/<card id>.json`, `cards/<card id>.json` (the card text) and `dist/pokemon/` are
built locally by `tools/build_realcards.py` and never committed (see the note at the top).

### Adding a pack

1. Create `packs/<id>/pack.json` (format: `docs/PACK_FORMAT.md`): `foil_chance`, `shiny_chance`, `characters`,
   and `tiers` (tier 0 is the plain, non-foil tier; each foil tier names its `art` variant and its skins with
   relative weights).
2. Draw `packs/<id>/art/<character>.json` for every character, with every art variant the tiers name.
3. Write `packs/<id>/shaders/<skin>.hlsl` for every skin; compile-check them with `fxc` (see the shader spec).
4. Build the art (`tools/README.md`) and commit `dist/<id>/`.
5. Re-run `install.ps1` (`pokeshell install`), then `pokeshell pack <id>` and `pokeshell odds`.

## Settings and files

Everything lives in `%LOCALAPPDATA%\pokeshell` (or `$env:POKESHELL_HOME`):

| file | |
|---|---|
| `config.txt` | `key=value`: `pack`, `enabled`, `display` (`card` or `picture`), `earn` (`first-command`, `minutes:N` or `off`), `anim` (`untilkey`, the default: a card's effect loops until you type, at most 30 s; `intro`: one loop; `off`: the static card only; `$env:POKESHELL_NO_ANIM = 1` turns it off for one shell), `plain_profiles` (comma-separated profile GUIDs that roll; default: the built-in Windows PowerShell and PowerShell 7 profiles. Add yours if you use a custom profile.), and `best_since` (where the binders' best pulls start: a local date or time like `2026-09-29` or `2026-09-29T00:40`, or `all`; default: your first pull of a real card, so older pulls don't crowd them out) |
| `pulls.log` | one tab-separated line per pull: time, pack, character, tier, art, skin, shiny, flags (`pending`, notes), `id=<ulid>`, `boot=<n>` (for a real card, tier is its rarity tier and art its card id); plus `earned:<id>` / `expired:<id>` lines. Append-only: older lines without an id count as earned, and pulls of art that no longer exists stay in it (the binders hide them: `retired` in `docs/PACK_FORMAT.md`) |
| `viewed.txt` | pull ids the binder has shown (no more NEW sticker) |
| `web/` | the web binder (`binder --web`) |
| `hotkey.tsv`, `urlhandler.txt` | what `pokeshell hotkey on` / `urlhandler on` installed, so uninstall removes exactly that |
| `color-misses.log` | color names that weren't in the table |
| `installed.tsv` | the skin profiles install added (what uninstall removes) |
| `roll.tsv` | the roll table cache (rebuilt automatically when a pack, its art, or the install changes) |
| `spawn-gate.txt` | recent foil spawns for the rate limit |
| `pokeshell-core-*.dll`, `pokeshell-anim-*.dll` | the compiled roll core and card-animation player (`scripts/lib/Pokeshell.cs`, `scripts/lib/Anim.cs`), built by install or the first tab that needs them |
| `backups/` | `settings.json` copies taken before every install/uninstall |
| `errors.log` | anything that went wrong at startup (the hook never throws into your profile) |
| `current/` | module installs only: the runtime new tabs use (hook, core source, shaders, art), refreshed by `pokeshell install` |
| `pokeshell-core-*.dll` | the compiled startup core |

## Tests

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tests\run-all.ps1
```

`test-no-loop` (the loop-safety layers, in simulation and with real processes), `test-install` (install /
uninstall round trips on copies of `settings.json`, including comments, trailing commas, BOM and the legacy
profiles format), `test-cli`, `test-cards`, `test-earned` (pull ids, the first-command hook in child processes,
expiry, NEW, the binder app's `--pull` / `--card` / `--set` / `--search`, `binder --web`, the hotkey on settings copies,
the URL handler as a dry run), `test-module` (stages the Gallery module, imports it, installs, simulates an
`Update-Module` and the removal of the old version, with a temp `LOCALAPPDATA`), and `measure-startup`
(`-HookRoot <folder>` measures a deployed copy such as `%LOCALAPPDATA%\pokeshell\current`). They never touch your
real Windows Terminal settings, `$PROFILE`, or `%LOCALAPPDATA%\pokeshell`, and never open a tab.

## Publishing (maintainers)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools\publish.ps1            # dry run: stage + Test-ModuleManifest + Publish-Module -WhatIf
$env:PSGALLERY_API_KEY = '<key>'
powershell -NoProfile -ExecutionPolicy Bypass -File tools\publish.ps1 -Publish   # really publish
```

`tools\publish.ps1` stages exactly what the module ships (manifest, `scripts\`, `packs\` json + shaders, `dist\`
art, docs, README, LICENSE; files git ignores never ship) into a temp folder. Bump `ModuleVersion` in
`pokeshell.psd1` before each release.

## Disclaimer

pokeshell is an unofficial, non-commercial fan project. It is not affiliated with, endorsed by, or sponsored by
Nintendo, Game Freak, Creatures Inc., or The Pokemon Company. Pokemon character names and related marks belong to their respective owners and are
used here only to identify the characters. This repository contains no game sprites, official artwork or card
text: the `pokemon` pack's cards are assembled on the user's own machine by `tools/build_realcards.py` from the
[pokemon-colorscripts](https://gitlab.com/phoneybadger/pokemon-colorscripts) sprites and the pokemontcg.io API, and
are never committed. If you are a rights holder and want something changed or removed, please open an issue.

## License

MIT, see [LICENSE](LICENSE). The license covers the code; it grants no rights in
the characters themselves.
