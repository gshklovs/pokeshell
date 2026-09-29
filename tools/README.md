# tools

## build_art.py: rebuild the card art

The runtime never needs Python: it prints the prebuilt ANSI files in `dist/` (for the `pokemon` pack, downloaded at
install from the art release `art.json` pins: see `publish_art.ps1` below).
You only need this when you add or change art in `packs/<pack>/art/*.json` (the real-card pokemon pack: see below).

```powershell
py -3 -m venv .venv
.venv\Scripts\python -m pip install pillow
.venv\Scripts\python tools\build_art.py            # rebuild everything
.venv\Scripts\python tools\build_art.py pikachu    # only art ids containing "pikachu"
```

Outputs:

- `dist/<pack>/<id>-<variant>.ans` and `...-shiny.ans`: truecolor half-block art, two pixels per text row. **Commit these** (not `dist/pokemon`: it is published as an art release, `publish_art.ps1`).
- `previews/<pack>/<id>-<variant>[-shiny].png`: 12x upscaled PNGs for eyeballing (git-ignored).

The art format and size limits are in `docs/ART_FORMAT.md`. After rebuilding, check the result in a terminal:

```powershell
pokeshell show pokemon/sv8-247 -shiny
```

New tabs pick up changed art on their own (the roll cache stamps the `art/` folders and rebuilds when they change).

## build_realcards.py / fetch_cards.py: the real-card pokemon pack

How each card's art is made (fetching a set, masks, the per-rarity effects, animations, the lookbook review, the
audit, then this import) is in [docs/ART_METHOD.md](../docs/ART_METHOD.md); the code for it is in `artlab/`.

`packs/pokemon` is a pack of real printed cards keyed by pokemontcg.io id (format: `docs/PACK_FORMAT.md`, "Real-card
packs"). Only `pack.json` is committed. The art (the pokemon-colorscripts sprite over each card's scene) and the
card text are Nintendo's / copyrighted, so they are built locally and git-ignored:
`packs/pokemon/art/`, `packs/pokemon/cards/`, `dist/pokemon/`. Users get `dist/pokemon/` from the
[pokeshell-art](https://github.com/gshklovs/pokeshell-art/releases) release that `art.json` pins (install downloads
it); after building new cards, publish them with `publish_art.ps1` (below). Install never overwrites a local build
unless asked (`install.ps1 -Art download`): a `dist/pokemon/` without the download's record (`.cardart.json`), or
with files newer than it, counts as local.

```powershell
.venv\Scripts\python -m pip install pillow
.venv\Scripts\python tools\build_realcards.py import suite3     # the last batch: style-lab/suite3 (12 real cards)
.venv\Scripts\python tools\build_realcards.py import evs        # the Evolving Skies batch, once style-lab/evs has its art
.venv\Scripts\python tools\build_realcards.py import p30        # the 30th Celebration batch (style-lab/p30)
.venv\Scripts\python tools\build_realcards.py                   # rebuild every card in pack.json from its source batch
.venv\Scripts\python tools\build_realcards.py import evs --dry-run    # what it would add, without writing
.venv\Scripts\python tools\fetch_cards.py --all                 # (re)fetch the card text only
```

Options: `--lab <folder>` / `--vendor <folder>` when `style-lab` and `vendor` aren't in this checkout (e.g. a git
worktree: `--lab ..\pokeshell\style-lab --vendor ..\pokeshell\vendor`), `--only <id,id>`, `--no-previews`.

What an import does, per card:

1. Finds the batch's real cards: every ART_FORMAT variant with a `"card": "<pokemontcg.io id>"`. Ids that aren't
   real (`invented`, `base1-44*`, a label saying "invented") are skipped, and so are the batch's `skip_variants`
   (suite3: `common_bg`; commons are the plain sprite). A batch's `cards/<id>.json` (style-lab/evs has them) are used
   instead of the API, and every card listed there is imported; a Common one without art gets the plain sprite
   from `vendor/pokemon-colorscripts`.
2. Fetches the card from the API (`fetch_cards.py`; retried, the API is flaky) into `packs/pokemon/cards/<id>.json`,
   and maps its printed `rarity` to the pack tier with that `rarity`. An unknown rarity stops the import: add the tier.
3. Checks the card's name contains the character (a wrong id in a batch fails loudly).
4. Writes `packs/pokemon/art/<id>.json`, builds `dist/pokemon/<character>-<id>[-shiny].ans` (+ `previews/`), and
   records the card in `pack.json` `cards`. Art of cards no longer in `pack.json` is removed.

New tabs pick up new cards on their own (the roll cache stamps `dist/pokemon`). `pokeshell odds` shows the result.

- `build_realcards.py tiers` copies label / family / weight / rarity / skins / frame from
  `artlab/rarities/rarities.json` into the `pack.json` tiers (matching ids; new ids appended).
- `--effects` renders each card through `artlab/rarities/effects.py`: it must define
  `render_card(card=<CARD_FORMAT dict>, art=<the ART_FORMAT dict from the batch>, rarity=<its rarities.json entry or None>)`
  returning an ART_FORMAT dict of the same shape. Without the flag the batch art is used as-is.

## make_media.py: showcase images

```powershell
.venv\Scripts\python -m pip install pillow fonttools
.venv\Scripts\python tools\make_media.py                    # -> previews\media (git-ignored)
```

Renders `hero.png` (every built card), `tiers.png` (Pikachu's cards with their odds) and `pull.gif` from the locally
built real cards: the card text comes from the real engine (`[Pokeshell.Core]::PullText`), drawn at terminal
proportions by `tools/render_ansi.py`. It writes to `previews/media` because the images show Nintendo sprites;
`--out docs/media` once it's settled that the README may show them.

## publish_art.ps1: publish the card art as a release of the art repo

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools\publish_art.ps1                          # dry run
powershell -NoProfile -ExecutionPolicy Bypass -File tools\publish_art.ps1 -Publish                 # release + pin
powershell -NoProfile -ExecutionPolicy Bypass -File tools\publish_art.ps1 -Source ..\pokeshell -Publish   # art built in another checkout
```

For every pack and part `art.json` lists (`pokemon`: `still` = `dist/pokemon/*.ans`, `anim` = `dist/pokemon/*.anim`,
optional), it writes `<pack>-<part>-<tag>.zip` with a `manifest.json` (pack, part, version = the tag, the source
commit, card count, each file's sha256 and size), then checks that every zip holds only `manifest.json` and that
pack's files of that extension (the rule install enforces too). The dry run stops there and prints the sizes.
`-Publish` runs `gh release create <tag>` on the art repo (`gshklovs/pokeshell-art`) with the zips and rewrites
`art.json` to pin the new tag, names, sizes and sha256s: commit `art.json` and push, and every install / update
fetches it. Tags default to `art-<yyyy-MM-dd>` (`-2`, `-3`... when taken; `-Tag` to choose); a release is never
replaced. It warns when `packs/` has uncommitted changes, since the art should match a committed `pack.json`.
It needs the GitHub CLI logged in (`gh auth login`). The format and the install side are in `docs/ART_RELEASES.md`;
`tests\test-art.ps1` covers both.

## publish.ps1: publish the PowerShell Gallery module

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools\publish.ps1                     # dry run (stage, Test-ModuleManifest, Publish-Module -WhatIf)
powershell -NoProfile -ExecutionPolicy Bypass -File tools\publish.ps1 -StageOnly -OutDir <dir>\pokeshell\0.1.0
$env:PSGALLERY_API_KEY = '<key>'; powershell -NoProfile -ExecutionPolicy Bypass -File tools\publish.ps1 -Publish
```

It stages only the files the module ships (see the header of the script); `tests\test-module.ps1` checks the staged module.
The module doesn't ship the binder app yet (`binder.exe` and its link launcher `binder-link.exe` are built from
`binder\`, never committed): a Gallery install gets the text binder, and `pokeshell install` skips the Ctrl+Shift+B
hotkey and the card's Ctrl+click link (it says so). A package that carries `bin\binder.exe` and `bin\binder-link.exe`
gets both: install copies them into `<state>\current` with the rest of the runtime, and points the hotkey and the
`pokeshell://` handler there.

## binder_web.py: the web binder

`pokeshell binder --web` runs it (Python with Pillow: `POKESHELL_PYTHON`, the repo's `.venv`, or `py -3`). It reads
`pulls.log` with the earned rule, the packs, card data and the prebuilt art, and writes `data.json`, `img/` and the baked
`binder.html` (`tools/binder-web/index.html` with the data inlined) into `<state>\web`:

```powershell
.venv\Scripts\python tools\binder_web.py [--state <dir>] [--out <dir>] [--root <checkout>] [--no-art]
```

Decoded art is cached in `img\.cache.json` (source mtime and size -> PNG size and tint): a rerun decodes nothing that
hasn't changed and prunes PNGs no card needs any more. `--no-art` decodes and writes no art at all. Lines of
`pulls.log` that aren't UTF-8 (an ANSI append from PowerShell 5) or have a bad time are skipped with a warning; cards
without built art or without card text are warned about. Every file is written to a temp name and swapped in.
