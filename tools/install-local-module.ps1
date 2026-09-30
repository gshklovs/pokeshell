<#
Install this checkout as the pokeshell module, the way the PowerShell Gallery would, without the Gallery: for a
developer who wants their own tabs on the module stack (or to update that module after repo changes).

  powershell -NoProfile -ExecutionPolicy Bypass -File tools\install-local-module.ps1 [-SwitchProfile]
             [-Art auto|download|local|skip] [-NoLocalPacks] [-NoInstall]

  1. checks binder\target\release\binder.exe and binder-link.exe are newer than binder\src (else binder\build.ps1),
  2. stages the module exactly as tools\publish.ps1 would publish it, into
     <Documents>\WindowsPowerShell\Modules\pokeshell\<ModuleVersion from pokeshell.psd1> (the per-user folder
     Install-Module -Scope CurrentUser uses; OneDrive-redirected Documents are followed),
  3. adds this checkout's local-only packs and built art (packs\<id> and dist\<id> that git doesn't track: the
     Gallery module ships no Pokemon art, and a download would replace a newer local build) unless -NoLocalPacks,
  4. backs up $PROFILE and Windows Terminal's settings.json to %LOCALAPPDATA%\pokeshell\backups, then runs
     `Import-Module pokeshell; pokeshell install -Art <Art>` in a fresh Windows PowerShell (no profile), as a
     Gallery user would after Install-Module (install -Art auto keeps a local build),
  5. with -SwitchProfile: replaces the source checkout's line in $PROFILE (". <repo>\scripts\pokeshell-profile.ps1")
     with the module's (". $env:LOCALAPPDATA\pokeshell\current\scripts\pokeshell-profile.ps1").

Your state in %LOCALAPPDATA%\pokeshell (pulls.log, config, viewed.txt, backups) is never deleted. Back to the source
checkout: README.md, "Developing: source checkout or module".
#>
param(
  [ValidateSet('auto', 'download', 'local', 'skip')][string]$Art = 'auto',
  [switch]$SwitchProfile,   # also point $PROFILE at the module's hook (replacing the source checkout's line)
  [switch]$NoLocalPacks,    # stage only what the Gallery package ships (no local-only packs, no local art)
  [switch]$NoInstall        # stage only; don't run pokeshell install
)
$ErrorActionPreference = 'Stop'
$Root = Split-Path $PSScriptRoot
if ($env:POKESHELL_HOME) { throw 'POKESHELL_HOME is set: unset it first (this installs for your real %LOCALAPPDATA%\pokeshell)' }

# ---- 1. the binder app is current (publish.ps1 refuses stale ones)
$rel = Join-Path $Root 'binder\target\release'
$newest = Get-ChildItem (Join-Path $Root 'binder\src'), (Join-Path $Root 'binder\Cargo.toml') -Recurse -File | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1
$stale = @('binder.exe', 'binder-link.exe' | Where-Object { $p = Join-Path $rel $_; -not [IO.File]::Exists($p) -or $newest.LastWriteTimeUtc -gt [IO.File]::GetLastWriteTimeUtc($p) })
if ($stale) {
  Write-Host "binder: $($stale -join ', ') missing or older than $($newest.Name): building" -ForegroundColor Yellow
  & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root 'binder\build.ps1')
  if ($LASTEXITCODE) { throw 'binder\build.ps1 failed' }
}

# ---- 2. stage into the per-user modules folder, at the manifest's version
$ver = (Import-PowerShellDataFile (Join-Path $Root 'pokeshell.psd1')).ModuleVersion
$mods = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'WindowsPowerShell\Modules'
if (@($env:PSModulePath -split ';' | Where-Object { $_ -and $_.TrimEnd('\') -ieq $mods }).Count -eq 0) {
  throw "$mods is not on PSModulePath ($env:PSModulePath); Install-Module would not use it either"
}
$dest = Join-Path $mods "pokeshell\$ver"
$null = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root 'tools\publish.ps1') -StageOnly -OutDir $dest
if ($LASTEXITCODE -or -not (Test-Path (Join-Path $dest 'packaged.txt'))) { throw "tools\publish.ps1 -StageOnly failed for $dest" }
Write-Host "staged pokeshell $ver -> $dest" -ForegroundColor Green

# ---- 3. local-only packs and built art, as packs a user dropped into the module folder
if (-not $NoLocalPacks) {
  foreach ($pd in Get-ChildItem (Join-Path $Root 'packs') -Directory) {
    if (-not (Test-Path (Join-Path $pd.FullName 'pack.json'))) { continue }
    $to = Join-Path $dest "packs\$($pd.Name)"
    $n = 0
    foreach ($sub in @(@('.', 'pack.json'), @('art', '*.json'), @('shaders', '*.hlsl'))) {
      foreach ($f in Get-ChildItem (Join-Path $pd.FullName $sub[0]) -Filter $sub[1] -File -ErrorAction SilentlyContinue) {
        $t = Join-Path $to "$($sub[0])\$($f.Name)"
        if (-not (Test-Path $t)) { [void][IO.Directory]::CreateDirectory((Split-Path $t)); Copy-Item -LiteralPath $f.FullName $t; $n++ }
      }
    }
    $dd = Join-Path $Root "dist\$($pd.Name)"; $a = 0
    foreach ($f in Get-ChildItem $dd -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -in '.ans', '.anim' -or $_.Name -eq '.cardart.json' }) {
      $t = Join-Path $dest "dist\$($pd.Name)\$($f.Name)"
      if (-not (Test-Path $t)) {
        [void][IO.Directory]::CreateDirectory((Split-Path $t)); Copy-Item -LiteralPath $f.FullName $t
        [IO.File]::SetLastWriteTimeUtc($t, $f.LastWriteTimeUtc); $a++   # cardart.ps1 compares mtimes with its record
      }
    }
    if ($n -or $a) { Write-Host "  + $($pd.Name): $n pack files, $a art files from this checkout" }
  }
}
if ($NoInstall) { return }

# ---- 4. back up, then install as a Gallery user would
$state = Join-Path $env:LOCALAPPDATA 'pokeshell'
$bk = Join-Path $state 'backups'; [void][IO.Directory]::CreateDirectory($bk)
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
. (Join-Path $Root 'scripts\lib\common.ps1')
$wt = Get-PokeshellWtSettingsPath
if ($wt) { Copy-Item -LiteralPath $wt (Join-Path $bk "settings-$stamp-before-module.json"); Write-Host "  backup: $bk\settings-$stamp-before-module.json" }
if (Test-Path $PROFILE) { Copy-Item -LiteralPath $PROFILE (Join-Path $bk "profile-$stamp-before-module.ps1"); Write-Host "  backup: $bk\profile-$stamp-before-module.ps1" }
$cmd = "Import-Module pokeshell -RequiredVersion $ver -ErrorAction Stop; pokeshell install -Art $Art"
& powershell.exe -NoProfile -ExecutionPolicy Bypass -Command $cmd
if ($LASTEXITCODE) { throw 'pokeshell install failed (the backups above are untouched)' }

# ---- 5. $PROFILE: the module's hook instead of the checkout's
$line = '. "$env:LOCALAPPDATA\pokeshell\current\scripts\pokeshell-profile.ps1"   # pokeshell: pack pulls on new tabs (module)'
if ($SwitchProfile) {
  $text = if (Test-Path $PROFILE) { [IO.File]::ReadAllText($PROFILE) } else { '' }
  $srcRx = '(?m)^[ \t]*\.[ \t]+"?[^"\r\n]*\\scripts\\pokeshell-profile\.ps1"?[^\r\n]*$'
  if ($text -match [regex]::Escape('pokeshell\current\scripts\pokeshell-profile.ps1')) { Write-Host "`$PROFILE already runs the module's hook" }
  elseif ($text -match $srcRx) {
    $new = [regex]::new($srcRx).Replace($text, $line.Replace('$', '$$'), 1)
    $enc = if ([IO.File]::ReadAllBytes($PROFILE)[0] -eq 0xEF) { [Text.UTF8Encoding]::new($true) } else { [Text.UTF8Encoding]::new($false) }
    [IO.File]::WriteAllText($PROFILE, $new, $enc)
    Write-Host "`$PROFILE: the source checkout's line now runs the module's hook" -ForegroundColor Green
  } else { Write-Host "`$PROFILE has no pokeshell line; add: $line" -ForegroundColor Yellow }
} else { Write-Host "(-SwitchProfile not given: `$PROFILE unchanged; for the module stack its pokeshell line is: $line)" }
