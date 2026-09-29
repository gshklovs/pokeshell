# Art releases

The built card art (`dist/<pack>/*.ans`, `*.anim`) is not in the code repos. Each project publishes it as release
assets of its own **art repo**, and install downloads it:

| code repo | art repo | packs |
|---|---|---|
| [gshklovs/pokeshell](https://github.com/gshklovs/pokeshell) | [gshklovs/pokeshell-art](https://github.com/gshklovs/pokeshell-art/releases) | `pokemon` (`still` + optional `anim`) |
| [gshklovs/opshell](https://github.com/gshklovs/opshell) | [gshklovs/opshell-art](https://github.com/gshklovs/opshell-art/releases) | `onepiece` (`still`) |

Why a separate repo: the art depicts characters that belong to their owners (pokeshell's embeds Nintendo sprites
over backgrounds painted from real card scenes). If a takedown ever hits the art, it hits the art repo: the code repo
stays up, and the art can be re-hosted anywhere by changing `base_url` in `art.json`. Users still get a one-command
install, because install fetches the art itself.

## The pieces

| file | where | what |
|---|---|---|
| `scripts/lib/cardart.ps1` | every code repo, **byte-identical** | the install side (download, verify, unpack, record) and the archive builder. Names no product: callers pass the root, the `art.json` path, a cache folder and a message prefix |
| `tools/publish_art.ps1` | every code repo, **byte-identical** | the maintainer step: builds the zips, checks them, `gh release create`, rewrites `art.json` |
| `art.json` | code repo root, tracked, shipped in the Gallery module | which art repo, which packs and parts, and the pinned release (tag, asset names, sizes, sha256s) |
| `dist/<pack>/.cardart.json` | written by install, git-ignored with `dist/<pack>/` | which release and parts are installed there, and their files |
| `<state>/art-cache/` | e.g. `%LOCALAPPDATA%\pokeshell\art-cache` | the verified zips `art.json` pins (others pruned), so a module update re-installs without downloading |
| `tests/test-art.ps1` | every code repo (product names differ) | offline tests from `file://` fixture releases; `-Online` also installs the real release into a temp folder |

The product's CLI (`scripts/<product>.ps1`) adds only a few lines: `-Art <mode>` / `-ArtStillOnly` options, an
`<PRODUCT>_ART` environment default (the tests set it to `skip`), an `<PRODUCT>_ART_JSON` override (tests), and one
call to `Install-CardArt` at the start of `install`, before the runtime is copied into `<state>\current`.

## art.json

```json
{
  "repo": "gshklovs/pokeshell-art",
  "code_repo": "gshklovs/pokeshell",
  "packs": [ { "id": "pokemon", "parts": [ { "part": "still", "ext": "ans" },
                                         { "part": "anim", "ext": "anim", "optional": true } ] } ],
  "tag": "art-2026-09-29",
  "base_url": "https://github.com/gshklovs/pokeshell-art/releases/download",
  "assets": [
    { "pack": "pokemon", "part": "still", "name": "pokemon-still-art-2026-09-29.zip", "sha256": "8b22...",
      "size": 3806993, "files": 684, "cards": 342, "optional": false },
    { "pack": "pokemon", "part": "anim", "name": "pokemon-anim-art-2026-09-29.zip", "sha256": "4a5c...",
      "size": 63388475, "files": 380, "cards": 190, "optional": true }
  ]
}
```

- `packs` is the publish side's spec (hand-edited): which extensions of `dist/<pack>/` form which part.
  An `optional` part is skipped by `install -ArtStillOnly`.
- `tag`, `base_url` and `assets` are written by `publish_art.ps1 -Publish`. An asset's URL is
  `<base_url>/<tag>/<name>` (`CARDART_BASE_URL` overrides `base_url`, e.g. for a mirror or a test).
- `cards` counts the non-shiny files (`*-shiny.*` are the same card's alternate palette).

## The archive

`<pack>-<part>-<tag>.zip`, deflate (the only compression Windows PowerShell 5.1 can unpack with nothing
installed; `.NET`'s `System.IO.Compression`), holding exactly:

- `manifest.json`: `format` (1), `pack`, `part`, `version` (the tag), `extension`, `source_repo`,
  `source_commit` (the commit of the checkout the art was built in), `created`, `cards`, `file_count`, and
  `files`: `[{ "path": "dist/pokemon/pikachu-swsh4-170.ans", "sha256": "...", "size": 44774 }, ...]`
- `dist/<pack>/<name>.<ext>`: the art, names matching `[A-Za-z0-9][A-Za-z0-9._-]*`.

Nothing else: no card scans, no card text, no user state. The publisher checks every zip against that rule before
uploading, and install refuses any zip that breaks it (an entry outside `dist/<its pack>/`, another extension, a
`..`, a file its manifest doesn't list, a count mismatch).

Sizes for the first release (2026-09-29): the `.anim` loops are 524.5 MB of escape-sequence text and zip to
60.5 MB; the `.ans` cards are 36.8 MB and zip to 3.6 MB. xz would get the loops to about 15 MB, but can't be unpacked
by PowerShell 5.1 alone (Windows' `tar.exe` only reads xz on recent Windows 11 builds), so the animations are a
separate, optional asset instead. opshell's 108 posters zip to 0.1 MB.

## Install

`Install-CardArt -Root <checkout or module version folder> -ConfigPath art.json -Mode <mode> -CacheDir <state>\art-cache`

For each pack in `art.json` whose `packs/<pack>/pack.json` exists under the root, and each of its assets:

1. **Decide.** Look at `dist/<pack>/`: no art (`none`); art without a record (`local`: a local build); exactly the
   recorded files, none newer than the record (`release`); or recorded files plus newer or unlisted ones
   (`modified`: a local build on top of a release).
   - `-Mode auto` (default): `local` / `modified` are kept, with a message naming `-Art download`. Otherwise a
     part whose recorded sha256 matches `art.json` and whose files all exist is **current** (nothing downloaded).
     Anything else is downloaded.
   - `-Mode download`: like `auto`, but local builds are replaced too (same-named files; other files stay).
   - `-Mode local`: never download. `-Mode skip`: nothing at all.
   - `-StillOnly`: optional parts are skipped (and left as they are if already installed).
2. **Fetch.** A zip in the cache with the right sha256 is reused. Otherwise it is downloaded (TLS 1.2,
   `HttpWebRequest`, 30 s connect / 60 s read timeouts, a progress line) to a temp name, its sha256 compared with
   `art.json`, and only then moved into the cache. A **mismatch is refused**: the file is deleted and nothing is
   unpacked. A **failed download** (offline, DNS, HTTP error) returns a message; it never throws.
3. **Unpack.** Entries are validated (above), unpacked next to the pack folder, then moved in, each replaced file
   deleted first (so nothing is written in place and a hard link elsewhere is never modified). Files the previous
   release of the same part installed that the new one lacks are removed; files the record doesn't list are never
   touched.
4. **Record.** `dist/<pack>/.cardart.json`: `{ repo, tag, installed, parts: { <part>: { name, sha256, files } } }`.
   Unpacked files get the unpack time as mtime and the record is written after them, which is what makes a later
   local build (newer files) recognisable.

Failures print in yellow (red for a checksum or unpack error) with one closing line: the code is installed, packs
without art don't roll (a real-card pack only rolls cards whose `.ans` exists), re-run install when online. Install
itself still succeeds.

Where the art goes: into the **root** install runs from. For a source checkout that is the checkout's `dist/`
(ignored by git). For a Gallery module it is the module version folder's `dist/`; `install` then copies the runtime,
art included, into `<state>\current` as before. After `Update-Module`, the new version folder has no art: install
unpacks it again from the cache (no download unless `art.json` changed).

## Publishing (maintainers)

```powershell
tools\publish_art.ps1                       # dry run: zips in %TEMP%\cardart-publish-<pid>, sizes, contents check
tools\publish_art.ps1 -Publish              # gh release create art-<date> on the art repo; art.json rewritten
git commit art.json; git push               # installs and updates fetch what art.json pins
```

Options: `-Source <checkout>` (the art was built elsewhere, e.g. the main checkout while committing from a
worktree), `-Tag <tag>` (default `art-<yyyy-MM-dd>`, suffixed `-2`, `-3`... when taken; releases are never replaced),
`-OutDir`, `-Packs` (dry runs only: a release always carries every pack, since `art.json` pins one tag).

Before the first release: `gh repo create <owner>/<name>-art --public` with a README that carries the project's
disclaimer, says the art belongs to its owners, that it is free and non-commercial, and that it will be taken down
on request, and points back to the code repo.

## Taking the art down, or moving it

- To remove the art: delete the releases (or the art repo). Installs then report a failed download and still install
  the code; nothing in the code repo has to change.
- To re-host: upload the same zips anywhere that serves `<base>/<tag>/<name>`, and change `base_url` in `art.json`
  (the sha256s stay valid).
- Old commits of opshell still contain `dist/onepiece/` (it was tracked until the move to art releases; history was
  not rewritten).

## A new sister project (e.g. mtgshell)

1. Copy `scripts/lib/cardart.ps1` and `tools/publish_art.ps1` unchanged.
2. Write `art.json` with `repo`, `code_repo`, `packs` (and empty `tag`/`assets`); ignore `dist/<pack>/` in
   `.gitignore`; add `art\.json` to the module's include list in `tools/publish.ps1`.
3. In `scripts/<product>.ps1`: accept `-Art` / `-ArtStillOnly` (and pass them on in the update's re-install), and at
   the start of `install`, after the settings path is resolved and before the runtime sync:
   ```powershell
   . (Join-Path $PSScriptRoot 'lib\cardart.ps1')
   $null = Install-CardArt -Root $Root -ConfigPath (Join-Path $Root 'art.json') -Mode $mode `
             -CacheDir (Join-Path $State 'art-cache') -StillOnly:$stillOnly -Prefix '<product>'
   ```
   Pass `-Art` through `install.ps1`, set `$env:<PRODUCT>_ART = 'skip'` in the tests' setup, and copy
   `tests/test-art.ps1` with the product's names (opshell's is the template for a character pack, pokeshell's for a
   real-card pack).
4. `gh repo create <owner>/<product>-art --public` with its README, then `tools\publish_art.ps1 -Publish` and commit
   `art.json`.
