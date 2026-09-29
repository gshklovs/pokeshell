# tools

## build_art.py: rebuild the card art

The runtime never needs Python: it prints the prebuilt ANSI files committed in `dist/`.
You only need this when you add or change art in `packs/<pack>/art/*.json`.

```powershell
py -3 -m venv .venv
.venv\Scripts\python -m pip install pillow
.venv\Scripts\python tools\build_art.py            # rebuild everything
.venv\Scripts\python tools\build_art.py pikachu    # only art ids containing "pikachu"
```

Outputs:

- `dist/<pack>/<id>-<variant>.ans` and `...-shiny.ans`: truecolor half-block art, two pixels per text row. **Commit these.**
- `previews/<pack>/<id>-<variant>[-shiny].png`: 12x upscaled PNGs for eyeballing (git-ignored).

The art format and size limits are in `docs/ART_FORMAT.md`. After rebuilding, check the result in a terminal:

```powershell
pokeshell show pokemon/pikachu gold -shiny
```

New tabs pick up changed art on their own (the roll cache stamps the `art/` folders and rebuilds when they change).

## make_media.py: regenerate the README images

```powershell
.venv\Scripts\python -m pip install pillow fonttools
.venv\Scripts\python tools\make_media.py
```

Rebuilds `docs/media/hero.png`, `tiers.png` and `pull.gif` from the current `dist/pokemon` art: the card text
comes from the real engine (`[Pokeshell.Core]::PullText`), drawn at terminal proportions by `tools/render_ansi.py`.
Run it after rebuilding the art. `foil.png` / `foil-gold.png` are real Windows Terminal screenshots and are not
regenerated.

## publish.ps1: publish the PowerShell Gallery module

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools\publish.ps1                     # dry run (stage, Test-ModuleManifest, Publish-Module -WhatIf)
powershell -NoProfile -ExecutionPolicy Bypass -File tools\publish.ps1 -StageOnly -OutDir <dir>\pokeshell\0.1.0
$env:PSGALLERY_API_KEY = '<key>'; powershell -NoProfile -ExecutionPolicy Bypass -File tools\publish.ps1 -Publish
```

It stages only the files the module ships (see the header of the script); `tests\test-module.ps1` checks the staged module.
