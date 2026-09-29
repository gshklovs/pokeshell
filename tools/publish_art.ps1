<#
Publish the built card art as a release of the art repo that art.json names, and pin it in art.json.
Shared with the sister projects (opshell, ...): copy it as is. Design: docs/ART_RELEASES.md (in pokeshell).

Dry run by default: packs every part of every pack art.json lists into <OutDir>\<pack>-<part>-<tag>.zip (with a
manifest: pack, part, version, source commit, card count, each file's sha256), then lists and checks each archive's
contents. Nothing is uploaded and art.json is not changed without -Publish.

  powershell -NoProfile -ExecutionPolicy Bypass -File tools\publish_art.ps1                       # dry run
  powershell -NoProfile -ExecutionPolicy Bypass -File tools\publish_art.ps1 -Publish              # gh release create + art.json
  tools\publish_art.ps1 -Source ..\pokeshell -Publish      # art built in another checkout (e.g. from a git worktree)
  tools\publish_art.ps1 -Tag art-2026-10-01b -Publish      # an explicit tag (default: art-<yyyy-MM-dd>, -2, -3... if taken)

-Publish needs the GitHub CLI (gh auth login) and the art repo (gh repo create <owner>/<name>-art --public).
Afterwards commit art.json: installs fetch the release it pins.
#>
param(
  [string]$Source,     # the checkout whose dist\<pack> holds the built art (default: this repo)
  [string]$Tag,        # the release tag (default: art-<today>, suffixed if it already exists)
  [string]$OutDir,     # where the zips go (default: %TEMP%\cardart-publish-<pid>)
  [string[]]$Packs,    # dry run only: just these packs (a release always carries every pack: art.json pins one tag)
  [switch]$Publish     # really create the release and update art.json
)
$ErrorActionPreference = 'Stop'
$Root = Split-Path $PSScriptRoot
. (Join-Path $Root 'scripts\lib\cardart.ps1')
$artJson = Join-Path $Root 'art.json'
$cfg = Read-CardArtConfig $artJson
if ($Packs -and $Publish) { throw '-Packs is for dry runs: a release carries every pack art.json lists (art.json pins one tag)' }
if (-not $Source) { $Source = $Root }
$Source = (Resolve-Path $Source).ProviderPath
if (-not $OutDir) { $OutDir = Join-Path ([IO.Path]::GetTempPath()) "cardart-publish-$PID" }

$gh = Get-Command gh -ErrorAction SilentlyContinue
if ($Publish -and -not $gh) { throw 'publishing needs the GitHub CLI (gh)' }
# Windows PowerShell 5.1 turns a native command's stderr into an error record: under 'Stop' that would throw
function Invoke-Quiet([scriptblock]$Block) { $ErrorActionPreference = 'Continue'; $null = & $Block 2>&1; $LASTEXITCODE -eq 0 }
function Test-Tag([string]$T) {
  if (-not $gh) { return $false }
  Invoke-Quiet { gh release view $T --repo $cfg.repo }
}
if (-not $Tag) {
  $Tag = 'art-' + (Get-Date -Format 'yyyy-MM-dd'); $n = 2; $base = $Tag
  while (Test-Tag $Tag) { $Tag = "$base-$n"; $n++ }
} elseif ($Publish -and (Test-Tag $Tag)) { throw "$($cfg.repo) already has a release $Tag (releases are never replaced: pick another tag)" }

$commit = ''; $dirty = @()
if (Get-Command git -ErrorAction SilentlyContinue) {
  $ErrorActionPreference = 'Continue'
  $commit = [string](& git -C $Source rev-parse HEAD 2>$null)
  $dirty = @(& git -C $Source status --porcelain -- packs 2>$null)
  $ErrorActionPreference = 'Stop'
}
if ($dirty) { Write-Warning "uncommitted changes under $Source\packs (the art should match a committed pack.json):`n  $($dirty -join "`n  ")" }

Write-Host "art release $Tag for $($cfg.repo) from $Source (commit $commit)" -ForegroundColor Cyan
$assets = @()
foreach ($p in @($cfg.packs)) {
  if ($Packs -and $Packs -notcontains $p.id) { continue }
  foreach ($part in @($p.parts)) {
    $a = New-CardArtAsset -Source $Source -Pack $p.id -Part $part.part -Ext $part.ext -Tag $Tag -OutDir $OutDir `
                          -SourceCommit $commit -SourceRepo ([string]$cfg.code_repo) -Optional ([bool]$part.optional)
    $chk = Test-CardArtAssetContents $a.path $p.id $part.ext
    if (-not $chk.ok) { throw "$($a.name) failed the contents check: unexpected $($chk.unexpected -join ', ')" }
    Write-Host ("  {0}: {1} files ({2} cards), {3:N1} MB raw -> {4:N1} MB zip  [manifest.json + dist/{5}/*.{6} only]" -f `
      $a.name, $a.files, $a.cards, ($a.raw_bytes / 1MB), ($a.size / 1MB), $p.id, $part.ext)
    $assets += $a
  }
}
if (-not $assets) { throw 'nothing to publish' }

if (-not $Publish) {
  Write-Host "dry run: archives in $OutDir; nothing uploaded, art.json unchanged. Add -Publish to release them." -ForegroundColor Yellow
  return
}

if (-not (Invoke-Quiet { gh repo view $cfg.repo })) { throw "$($cfg.repo) not found: gh repo create $($cfg.repo) --public (then its README), and run this again" }
$notes = @"
Built card art for [$($cfg.code_repo)](https://github.com/$($cfg.code_repo)), installed by its install.ps1 / ``install`` command.
Source commit: $($cfg.code_repo)@$commit

$(($assets | ForEach-Object { "- ``$($_.name)``: $($_.files) files, $($_.cards) cards, sha256 ``$($_.sha256)``" }) -join "`n")

Fan art of characters that belong to their owners; free and non-commercial; taken down on request (see the README).
"@
$notesFile = Join-Path $OutDir 'notes.md'
[IO.File]::WriteAllText($notesFile, $notes, [Text.UTF8Encoding]::new($false))
$ErrorActionPreference = 'Continue'
& gh release create $Tag @($assets | ForEach-Object path) --repo $cfg.repo --title $Tag --notes-file $notesFile 2>&1 | ForEach-Object { "$_" }
$ok = $LASTEXITCODE -eq 0
$ErrorActionPreference = 'Stop'
if (-not $ok) { throw 'gh release create failed' }

# pin it: art.json keeps its packs spec; tag, base_url and assets are replaced by what was just published
$out = [ordered]@{}
foreach ($prop in $cfg.PSObject.Properties) { if ($prop.Name -notin 'tag', 'base_url', 'assets') { $out[$prop.Name] = $prop.Value } }
$out.tag = $Tag
$out.base_url = "https://github.com/$($cfg.repo)/releases/download"
$out.assets = @($assets | ForEach-Object {
  [ordered]@{ pack = $_.pack; part = $_.part; name = $_.name; sha256 = $_.sha256; size = $_.size; files = $_.files; cards = $_.cards; optional = $_.optional }
})
Write-CardArtJson $artJson $out
Write-Host "published ${Tag}: https://github.com/$($cfg.repo)/releases/tag/$Tag" -ForegroundColor Green
Write-Host "art.json now pins it: commit art.json so installs fetch it." -ForegroundColor Green
