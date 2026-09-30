<#
Stage the pokeshell module (exactly the files it ships) into a temp folder and publish it to the PowerShell Gallery.
Dry run by default: stages, runs Test-ModuleManifest, then Publish-Module -WhatIf. Nothing is uploaded without -Publish.

  powershell -NoProfile -ExecutionPolicy Bypass -File tools\publish.ps1              # dry run
  $env:PSGALLERY_API_KEY = '<key>'; powershell -NoProfile -File tools\publish.ps1 -Publish
  tools\publish.ps1 -StageOnly -OutDir <dir>\pokeshell\0.1.0 [-Version 0.2.0]         # stage only (the tests use this)

What ships: pokeshell.psd1/.psm1, LICENSE, README.md, art.json (which art release install downloads), docs\*.md, scripts\** , packs\<id>\pack.json + carddata.json (the cards' gameplay data, tools\build_carddata.py) + boosters.json (the real booster packs) + art\*.json +
shaders\*.hlsl, dist\<id>\*.ans, plus a generated packaged.txt (it tells the CLI it runs from an installed module,
so `pokeshell install` copies the runtime into %LOCALAPPDATA%\pokeshell\current). Not shipped: tests, tools, .venv,
previews. Files come from git: tracked files once the repo has a commit (before the first commit: every file git
doesn't ignore), so local-only packs listed in .gitignore or .git/info/exclude never ship.
#>
param(
  [string]$OutDir,          # the folder the module files go into (default: %TEMP%\pokeshell-publish-<pid>\pokeshell)
  [string]$Version,         # override ModuleVersion in the staged copy (tests: simulate an update)
  [switch]$StageOnly,       # stage + Test-ModuleManifest, don't call Publish-Module; returns the staged folder
  [switch]$Publish          # really publish (needs $env:PSGALLERY_API_KEY); without it Publish-Module runs with -WhatIf
)
$ErrorActionPreference = 'Stop'
$Root = Split-Path $PSScriptRoot

# ---- which files
$include = '^(pokeshell\.psd1|pokeshell\.psm1|LICENSE|README\.md|art\.json|docs/[^/]+\.md|scripts/.+|' +
           'packs/[^/]+/(pack|carddata|boosters)\.json|packs/[^/]+/art/[^/]+\.json|packs/[^/]+/shaders/[^/]+\.hlsl|dist/[^/]+/[^/]+\.(ans|anim))$'
$git = Get-Command git -ErrorAction SilentlyContinue
if ($git -and (Test-Path (Join-Path $Root '.git'))) {
  & git -C $Root rev-parse --verify -q HEAD *> $null
  if ($LASTEXITCODE -eq 0) { $list = @(& git -C $Root ls-files) }
  else {
    Write-Warning 'no commits yet: shipping every file git does not ignore (.gitignore, .git/info/exclude)'
    $list = @(& git -C $Root ls-files --cached --others --exclude-standard)
  }
  if ($LASTEXITCODE -ne 0) { throw 'git ls-files failed' }
} else {
  Write-Warning "$Root is not a git checkout: shipping by the include rules alone"
  $list = @(Get-ChildItem $Root -Recurse -File | ForEach-Object { $_.FullName.Substring($Root.Length + 1).Replace('\', '/') })
}
$files = @($list | Where-Object { $_ -match $include -and $_ -notmatch '(^|/)(\.venv|previews|__pycache__)/' } | Sort-Object -Unique)
foreach ($must in 'pokeshell.psd1', 'pokeshell.psm1', 'scripts/pokeshell.ps1', 'scripts/pokeshell-profile.ps1', 'scripts/lib/Pokeshell.cs', 'scripts/lib/pokeshell-shim.ps1') {
  if ($files -notcontains $must) { throw "staging: $must is missing from the file list" }
}

# ---- stage
if (-not $OutDir) { $OutDir = Join-Path ([IO.Path]::GetTempPath()) "pokeshell-publish-$PID\pokeshell" }
if (Test-Path $OutDir) { Remove-Item $OutDir -Recurse -Force }
foreach ($f in $files) {
  $to = Join-Path $OutDir $f
  [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($to))
  Copy-Item -LiteralPath (Join-Path $Root $f) -Destination $to
}
# the binder app and its windowless link launcher (no art in them): built by binder\build.ps1, shipped in bin\ so a
# module install gets the binder, its Ctrl+Shift+B pane, the card's Ctrl+click link (common.ps1 looks there first) and
# `binder --web` (binder.exe --export-web, the page built in: no Python needed)
$rel = Join-Path $Root 'binder\target\release'
foreach ($exe in 'binder.exe', 'binder-link.exe') {
  $src = Join-Path $rel $exe
  if (-not [IO.File]::Exists($src)) { throw "staging: $exe isn't built (powershell -File binder\build.ps1)" }
  # stale when a file it is built from is newer: cargo's dep-info (<exe>.d) lists them (binder.exe also embeds
  # tools\binder-web\index.html; binder-link.exe is only link.rs + linkurl.rs), plus Cargo.toml; without it, all of src
  $dep = [IO.Path]::ChangeExtension($src, '.d')
  $inputs = @((Join-Path $Root 'binder\Cargo.toml'))
  if ([IO.File]::Exists($dep)) {
    $body = ([IO.File]::ReadAllText($dep) -split ':\s', 2)[1]
    $inputs += @([regex]::Split("$body".Trim(), '(?<!\\)\s+') | Where-Object { $_ } | ForEach-Object { $_ -replace '\\ ', ' ' })
  } else { $inputs += @(Get-ChildItem (Join-Path $Root 'binder\src') -Recurse -File | ForEach-Object FullName) }
  $newest = @($inputs | Where-Object { [IO.File]::Exists($_) } | ForEach-Object { Get-Item -LiteralPath $_ }) | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1
  if ($newest.LastWriteTimeUtc -gt (Get-Item $src).LastWriteTimeUtc) { throw "staging: $exe is older than $($newest.Name) (rebuild: powershell -File binder\build.ps1)" }
  [void][IO.Directory]::CreateDirectory((Join-Path $OutDir 'bin'))
  Copy-Item -LiteralPath $src -Destination (Join-Path $OutDir "bin\$exe")
}
$psd1 = Join-Path $OutDir 'pokeshell.psd1'
if ($Version) {
  $t = [IO.File]::ReadAllText($psd1)
  $t = [regex]::Replace($t, "(?m)^(\s*ModuleVersion\s*=\s*)'[^']*'", "`${1}'$Version'")
  [IO.File]::WriteAllText($psd1, $t, [Text.UTF8Encoding]::new($false))
}
$manifest = Test-ModuleManifest $psd1   # throws if the manifest is invalid
$ver = "$($manifest.Version)"
[IO.File]::WriteAllLines((Join-Path $OutDir 'packaged.txt'), [string[]]@(
  '# written by tools/publish.ps1: this folder is an installed pokeshell module (pokeshell install copies the',
  '# runtime into %LOCALAPPDATA%\pokeshell\current). A source checkout has no packaged.txt.',
  "version=$ver"))
$packs = @($files | Where-Object { $_ -match '^packs/([^/]+)/pack\.json$' } | ForEach-Object { $_.Split('/')[1] })
$bytes = (Get-ChildItem $OutDir -Recurse -File | Measure-Object Length -Sum).Sum
Write-Host ("staged pokeshell {0}: {1} files, {2:N0} KB, packs: {3}  ->  {4}" -f $ver, ($files.Count + 1), ($bytes / 1KB), ($packs -join ', '), $OutDir)
Write-Host ("  exports: {0}" -f ((@($manifest.ExportedFunctions.Keys) + @($manifest.ExportedCmdlets.Keys) + @($manifest.ExportedAliases.Keys)) -join ', '))
if ($StageOnly) { return $OutDir }

# ---- publish (PSResourceGet if present, else PowerShellGet)
$key = $env:PSGALLERY_API_KEY
if ($Publish -and -not $key) { throw 'set $env:PSGALLERY_API_KEY to your PowerShell Gallery API key first' }
if (-not $Publish) { $key = 'dry-run-no-key' }   # a dry run never carries a real key, so it can't upload even if -WhatIf were ignored
$dry = -not $Publish
$psget = Get-Module PowerShellGet -ListAvailable | Sort-Object Version -Descending | Select-Object -First 1
if (-not (Get-Command Publish-PSResource -ErrorAction SilentlyContinue) -and (-not $psget -or $psget.Version -lt [version]'2.2.5')) {
  # Windows PowerShell ships PowerShellGet 1.0.0.1, whose Publish-Module needs nuget.exe and prompts to download it
  throw ("publishing needs PowerShellGet 2.2.5+ or PSResourceGet (found PowerShellGet $(if ($psget) { $psget.Version } else { 'none' })). Once, then open a new shell:`n" +
         "  Install-PackageProvider NuGet -MinimumVersion 2.8.5.201 -Scope CurrentUser -Force`n" +
         "  Install-Module PowerShellGet -MinimumVersion 2.2.5 -Scope CurrentUser -Force -AllowClobber")
}
if (Get-Command Publish-PSResource -ErrorAction SilentlyContinue) {
  Publish-PSResource -Path $OutDir -ApiKey $key -Repository PSGallery -WhatIf:$dry -Verbose:$Publish
} else {
  Publish-Module -Path $OutDir -NuGetApiKey $key -Repository PSGallery -WhatIf:$dry -Verbose:$Publish
}
if ($dry) { Write-Host "dry run: nothing was published. To publish: `$env:PSGALLERY_API_KEY = '<key>'; tools\publish.ps1 -Publish" -ForegroundColor Yellow }
else { Write-Host "published pokeshell ${ver}: Install-Module pokeshell -Scope CurrentUser" -ForegroundColor Green }
