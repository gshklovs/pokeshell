<#
Uninstall pokeshell: removes exactly the profiles install.ps1 added to Windows Terminal's settings.json
(backed up first) and tells you which $PROFILE line to delete.
  .\uninstall.ps1                        # keeps your pull log / collection
  .\uninstall.ps1 -Purge                 # also deletes %LOCALAPPDATA%\pokeshell
  .\uninstall.ps1 -SettingsPath <file>
#>
param([string]$SettingsPath, [switch]$Purge)
$a = @('uninstall')
if ($SettingsPath) { $a += '-SettingsPath', $SettingsPath }
if ($Purge) { $a += '-Purge' }
& (Join-Path $PSScriptRoot 'scripts\pokeshell.ps1') @a
