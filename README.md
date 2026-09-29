# pokeshell

Every new Windows Terminal PowerShell tab is a trading-card pack pull.

Most tabs are a plain **common** pull: the pulled character's pixel art prints at the top of the tab with a banner
like `common : Squirtle`. Some tabs are **foil** pulls: the tab reopens (same folder) wearing an animated holofoil
pixel-shader skin (cracked ice, cosmos, rainbow rare, gold, ...) and prints the rarer art with a banner like
`secret rare : Pikachu` or `ultra rare : Charmander (shiny)`. Every pull goes into your binder (`pokeshell collection`).

It's a fan project: all the art is original pixel art, and nothing here is affiliated with the owners of the
characters (see [Disclaimer](#disclaimer)).

## Packs and odds

### Pokemon (`pokemon`): 4 characters, 18 foil skins

| tier | odds | about 1 tab in | art | skins |
|---|---:|---:|---|---|
| common | 80.00% | 1.25 | common | none (plain tab) |
| holo | 10.81% | 9 | holo | starlight, reverse, sheen, tinsel, water-web, crosshatch |
| rare holo | 4.86% | 21 | holo | cracked-ice, cosmos, pokeball, galaxy-reverse |
| ultra rare | 3.42% | 29 | fullart | radiant, sunpillar, illustration-rare, shiny-vault, masterball |
| secret rare | 0.90% | 111 | gold | rainbow-rare, amazing-rare, gold |

Any pull, of any tier, is **shiny** (alternate palette) 1 time in 64.

`pokeshell odds` always prints the live numbers from each `pack.json`, down to each skin and
"1 in N" for one specific card. More packs can be added under `packs/`; with several installed,
`pokeshell pack all` makes each tab first pick a pack at random.

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
| `pokeshell collection` | your binder: per pack, every character x tier you've pulled, shiny counts, completion, best pulls |
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
(`shiny_chance`).

- **common**: print `dist/<pack>/<character>-<art>[-shiny].ans` and the banner, right there.
- **foil**: open a new tab (or a split pane, if this is a pane) with the skin's hidden profile, in the same folder,
  which prints the art and banner; then this tab exits with code 0, so Windows Terminal closes it and the skinned
  tab takes its place.

Every pull is logged to `%LOCALAPPDATA%\pokeshell\pulls.log`.

It's fast: Windows PowerShell 5.1 pays about a millisecond the first time each line of script runs, so the
decision logic is C# (`scripts/lib/Pokeshell.cs`, compiled once to `%LOCALAPPDATA%\pokeshell\pokeshell-core-*.dll`),
the roll table is a prebuilt TSV cache, and the art is a prebuilt ANSI file. A tab adds ~20 ms when it doesn't
roll and ~25-50 ms for a common pull (`tests/measure-startup.ps1` measures it on your machine).

**Why pulled tabs take about half a second:** Windows Terminal compiles a profile's pixel shader when a tab with
that profile opens. The foil tab appears, compiles its skin, then prints. That's also why a foil tab starts a
beat after the plain one closes.

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
   (set in every tab once it has rolled, so a `powershell` you start inside a tab never rolls).
4. **Machine-wide rate limit**: a lock file (`spawn-gate.txt`) allows at most one foil spawn every 3 seconds
   across all tabs; a sixth spawn within 60 seconds trips a 10-minute breaker during which every pull is a common.
   Tested with 12 processes racing for the lock at the same instant: exactly one wins.
5. **Placement**: a foil only replaces a tab it has positively found in the foreground window (above).
6. **Installed skins only**: skins that `pokeshell install` hasn't registered never drop; before install, every
   pull is a common.
7. **Kill switch**: `pokeshell off`, or `POKESHELL_DISABLE=1` in the environment.

If opening the tab fails for any reason, the pull prints in place and the tab stays open.

### Packs, art and shaders

A pack is a folder `packs/<id>/`:

- `pack.json`: odds, tiers, characters (format: `docs/PACK_FORMAT.md`)
- `art/<character>.json`: pixel art as palette-indexed rows, one variant per tier art name, optional shiny
  palette (format and size limits: `docs/ART_FORMAT.md`)
- `shaders/<skin>.hlsl`: Windows Terminal pixel shaders, one per foil skin (spec: `docs/SHADER_SPEC.md`)

`tools/build_art.py` renders the art to `dist/<pack>/<character>-<variant>[-shiny].ans` (24-bit color, two
pixels per character cell with half blocks). `dist/` is committed, so users never need Python.

### Adding a pack

1. Create `packs/<id>/pack.json` (copy `packs/pokemon/pack.json`): `foil_chance`, `shiny_chance`, `characters`,
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
| `config.txt` | `key=value`: `pack`, `enabled`, `display` (`card` or `picture`), and `plain_profiles` (comma-separated profile GUIDs that roll; default: the built-in Windows PowerShell and PowerShell 7 profiles. Add yours if you use a custom profile.) |
| `pulls.log` | one tab-separated line per pull: time, pack, character, tier, art, skin, shiny, note |
| `color-misses.log` | color names that weren't in the table |
| `installed.tsv` | the skin profiles install added (what uninstall removes) |
| `roll.tsv` | the roll table cache (rebuilt automatically when a pack, its art, or the install changes) |
| `spawn-gate.txt` | recent foil spawns for the rate limit |
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
profiles format), `test-cli`, `test-module` (stages the Gallery module, imports it, installs, simulates an
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
used here only to identify the characters. All pixel art in this repository is original fan art drawn for this
project; no game sprites or official artwork are included. If you are a rights holder and want something changed
or removed, please open an issue.

## License

MIT, see [LICENSE](LICENSE). The license covers the code and this project's original art; it grants no rights in
the characters themselves.
