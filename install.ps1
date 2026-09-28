<#
Install pokeshell: adds one hidden Windows Terminal profile per shader of every pack to WT's settings.json
(backed up first to %LOCALAPPDATA%\pokeshell\backups) and prints the line to add to your $PROFILE.
  .\install.ps1                          # auto-detects WT (Store, Preview, or unpackaged)
  .\install.ps1 -SettingsPath <file>     # a specific settings.json
  .\install.ps1 -Shell pwsh              # skinned tabs run PowerShell 7 instead of Windows PowerShell
Safe to re-run (e.g. after adding a pack): it replaces its own profiles and leaves everything else alone.
#>
param([string]$SettingsPath, [ValidateSet('powershell', 'pwsh')][string]$Shell)
$a = @('install')
if ($SettingsPath) { $a += '-SettingsPath', $SettingsPath }
if ($Shell) { $a += '-Shell', $Shell }
& (Join-Path $PSScriptRoot 'scripts\pokeshell.ps1') @a
