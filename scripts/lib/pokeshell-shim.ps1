<#
pokeshell command shim. `pokeshell install` (from the PowerShell Gallery module) copies this file to
%LOCALAPPDATA%\pokeshell\current\scripts\pokeshell.ps1, next to the $PROFILE hook, so the `pokeshell`
function the hook defines keeps working across Update-Module / Uninstall-Module of old versions: it runs
the CLI of the newest installed pokeshell module, looked up on every call (never on the tab-open path).
Looks in PSModulePath plus both editions' per-user and machine module folders, so a module installed from
PowerShell 7 also serves Windows PowerShell tabs and vice versa.
#>
$dirs = [Collections.Generic.List[string]]::new()
foreach ($p in @($env:PSModulePath -split ';')) { if ($p) { $dirs.Add($p) } }
# (POKESHELL_REAL_MODULES=off, set by the tests: PSModulePath only, never the real per-user / machine folders)
if ($env:POKESHELL_REAL_MODULES -ne 'off') {
  $docs = [Environment]::GetFolderPath('MyDocuments')
  foreach ($p in "$docs\WindowsPowerShell\Modules", "$docs\PowerShell\Modules", "$env:ProgramFiles\WindowsPowerShell\Modules", "$env:ProgramFiles\PowerShell\Modules") { $dirs.Add($p) }
}
$best = $null; $bestVer = $null
foreach ($d in ($dirs | Select-Object -Unique)) {
  foreach ($v in @(Get-ChildItem -LiteralPath (Join-Path $d 'pokeshell') -Directory -ErrorAction SilentlyContinue)) {
    $ver = $null
    if (-not [version]::TryParse($v.Name, [ref]$ver)) { continue }
    if (-not (Test-Path -LiteralPath (Join-Path $v.FullName 'scripts\pokeshell.ps1'))) { continue }
    if (-not $bestVer -or $ver -gt $bestVer) { $best = $v.FullName; $bestVer = $ver }
  }
}
if (-not $best) {
  # e.g. Save-Module to a custom folder: the module folder the last install ran from
  $f = Join-Path (Split-Path $PSScriptRoot) 'module-base.txt'
  if (Test-Path -LiteralPath $f) {
    $b = [IO.File]::ReadAllText($f).Trim()
    if ($b -and (Test-Path -LiteralPath (Join-Path $b 'scripts\pokeshell.ps1'))) { $best = $b }
  }
}
if (-not $best) {
  Write-Host 'pokeshell: the pokeshell module is not installed (Install-Module pokeshell -Scope CurrentUser).' -ForegroundColor Red
  Write-Host "  new tabs still run from $(Split-Path $PSScriptRoot); to remove pokeshell, delete the pokeshell line from `$PROFILE"
  exit 1
}
& (Join-Path $best 'scripts\pokeshell.ps1') @args
