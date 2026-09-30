# Shared test setup: a throwaway state dir (never %LOCALAPPDATA%\pokeshell) with every skin "installed".
$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path $PSScriptRoot
. (Join-Path $RepoRoot 'scripts\lib\roll.ps1')
. (Join-Path $RepoRoot 'scripts\lib\common.ps1')
Import-PokeshellCore (Join-Path ([IO.Path]::GetTempPath()) 'pokeshell-test-core')

$PlainGuid = '{61c54bbd-c2c6-5271-96e7-009a87ff44bf}'
# child processes the tests start inherit this environment: drop a real tab's pull markers (run from a tab that
# already rolled, the hook probes would otherwise skip)
foreach ($k in 'POKESHELL_PULL', 'POKESHELL_ROLLED', 'CARDSHELL_ROLLED', 'OPSHELL_PULL', 'OPSHELL_ROLLED') { [Environment]::SetEnvironmentVariable($k, $null) }
# install never downloads the card art release in tests (child processes inherit this); test-art.ps1 turns it back on
$env:POKESHELL_ART = 'skip'
# ...and never writes the registry (the pokeshell:// handler): Set-PokeshellUrlHandler only reports what it would do
$env:POKESHELL_REGISTRY = 'dryrun'
# ...and never falls back to the real Windows Terminal settings.json (a command run without -SettingsPath throws
# instead). Every child process inherits it; the tests' own "was it touched" hash checks use $RealWtSettings.
$RealWtSettings = Get-PokeshellWtSettingsPath
$env:POKESHELL_REAL_WT = 'off'
$script:Failures = 0

function New-TestState([string]$Name) {
  $dir = Join-Path ([IO.Path]::GetTempPath()) "pokeshell-test-$Name-$PID"
  Remove-Item $dir -Recurse -Force -ErrorAction SilentlyContinue
  [void][IO.Directory]::CreateDirectory($dir)
  $tsv = @(Get-PokeshellSkins $RepoRoot | ForEach-Object { "$($_.pack)`t$($_.skin)`t$($_.guid)`ttest" })
  [IO.File]::WriteAllLines((Join-Path $dir 'installed.tsv'), [string[]]$tsv)
  $dir
}

function Assert([bool]$Cond, [string]$What) {
  if ($Cond) { Write-Host "  ok    $What" -ForegroundColor Green }
  else { Write-Host "  FAIL  $What" -ForegroundColor Red; $script:Failures++ }
}

# run a block with the pokeshell env markers cleared (a "fresh process"), then restore them
function Invoke-Fresh([scriptblock]$Block, [hashtable]$Env = @{}) {
  $saved = @{}
  foreach ($k in 'POKESHELL_PULL', 'POKESHELL_ROLLED', 'POKESHELL_DISABLE', 'POKESHELL_DRYRUN', 'CARDSHELL_ROLLED') { $saved[$k] = [Environment]::GetEnvironmentVariable($k); [Environment]::SetEnvironmentVariable($k, $null) }
  foreach ($k in $Env.Keys) { [Environment]::SetEnvironmentVariable($k, $Env[$k]) }
  try { & $Block } finally { foreach ($k in $saved.Keys) { [Environment]::SetEnvironmentVariable($k, $saved[$k]) } }
}
