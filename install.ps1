<#
Install pokeshell: adds one hidden Windows Terminal profile per shader of every pack to WT's settings.json
(backed up first to %LOCALAPPDATA%\pokeshell\backups) and prints the line to add to your $PROFILE.
  .\install.ps1                          # auto-detects WT (Store, Preview, or unpackaged)
  .\install.ps1 -SettingsPath <file>     # a specific settings.json
  .\install.ps1 -Shell pwsh              # skinned tabs run PowerShell 7 instead of Windows PowerShell
  .\install.ps1 -Art auto                # (default) download the card art release art.json pins, if missing or older
  .\install.ps1 -Art download            # download it even over a local build (tools\build_realcards.py)
  .\install.ps1 -Art local               # never download: use the art built in dist\ (skip: don't touch the art)
  .\install.ps1 -ArtStillOnly            # skip the optional card animations (.anim, the big download)
Safe to re-run (e.g. after adding a pack): it replaces its own profiles and leaves everything else alone, and
downloads the art only when the installed art doesn't already match art.json.
#>
param([string]$SettingsPath, [ValidateSet('powershell', 'pwsh')][string]$Shell,
      [ValidateSet('auto', 'download', 'local', 'skip')][string]$Art, [switch]$ArtStillOnly)
$a = @('install')
if ($SettingsPath) { $a += '-SettingsPath', $SettingsPath }
if ($Shell) { $a += '-Shell', $Shell }
if ($Art) { $a += '-Art', $Art }
if ($ArtStillOnly) { $a += '-ArtStillOnly' }
& (Join-Path $PSScriptRoot 'scripts\pokeshell.ps1') @a
