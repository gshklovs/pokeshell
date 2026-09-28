<#
The pokeshell command against a throwaway state dir: show every built card, odds, pack, collection, color.
  powershell -NoProfile -File tests\test-cli.ps1
#>
. (Join-Path $PSScriptRoot '_setup.ps1')
$st = New-TestState 'cli'
$cli = Join-Path $RepoRoot 'scripts\pokeshell.ps1'
function Invoke-Cli { $env:POKESHELL_HOME = $st; try { & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $cli @args 2>&1 | Out-String -Width 300 } finally { Remove-Item Env:POKESHELL_HOME } }
$e = [char]27
function Strip([string]$s) { $s -replace "$e\[[0-9;]*m", '' -replace "$e\][^$e]*$e\\", '' }

Write-Host "1. show: every built card prints its art and banner" -ForegroundColor Cyan
$ans = @(Get-ChildItem (Join-Path $RepoRoot 'dist') -Recurse -Filter *.ans)
$bad = @()
foreach ($f in $ans) {
  $pack = $f.Directory.Name
  $packObj = Read-PokeshellPack $RepoRoot $pack
  $char = @($packObj.characters | Where-Object { $f.BaseName.StartsWith("$_-") } | Sort-Object Length -Descending)[0]
  if (-not $char) { continue }
  $variant = $f.BaseName.Substring($char.Length + 1); $shiny = $variant.EndsWith('-shiny'); if ($shiny) { $variant = $variant.Substring(0, $variant.Length - 6) }
  $a = @('show', "$pack/$char", $variant); if ($shiny) { $a += '-shiny' }
  $out = Invoke-Cli @a
  $lines = @((Strip $out) -split "`r?`n" | Where-Object { $_.Trim() })
  $banner = $lines[-1].Trim()
  $want = " : $($packObj.names[$char])$(if ($shiny) { ' (shiny)' })"
  if (-not $banner.EndsWith($want) -or $lines.Count -lt 3) { $bad += "$pack/$char $variant$(if ($shiny) { ' shiny' }): '$banner'" }
}
Assert ($ans.Count -gt 0) "$($ans.Count) built .ans files found in dist/"
Assert ($bad.Count -eq 0) "all of them show with the right banner$(if ($bad) { ': ' + ($bad -join '; ') })"
$out = Strip (Invoke-Cli show pokemon/nobody)
Assert ($out -match "has no character 'nobody'") "unknown character: one clear error line"

Write-Host "2. pack / odds" -ForegroundColor Cyan
$out = Invoke-Cli pack all
Assert ((Get-Content (Join-Path $st 'config.txt')) -contains 'pack=all') "pack all saved"
$out = Strip (Invoke-Cli odds)
foreach ($id in Get-PokeshellPackIds $RepoRoot) { $n = (Read-PokeshellPack $RepoRoot $id).name; Assert ($out -match [regex]::Escape($n)) "odds lists $n" }
$out = Strip (Invoke-Cli pack bogus)
Assert ($out -match "no pack 'bogus'" -and (Get-Content (Join-Path $st 'config.txt')) -contains 'pack=all') "bad pack refused, setting kept"
$null = Invoke-Cli pack pokemon
$roll = Get-Content (Join-Path $st 'roll.tsv')
Assert ($roll[1] -eq "select`tpokemon" -and @($roll | Where-Object { $_ -like 'skin*' }).Count -gt 0) "roll cache rebuilt for pokemon with its installed skins"

Write-Host "3. collection" -ForegroundColor Cyan
Import-PokeshellCore $st
$lines = foreach ($i in 1..300) {
  $env:POKESHELL_ROLLED = $null; $env:POKESHELL_PULL = $null
  $r = [Pokeshell.Core]::Roll($RepoRoot, $st, $PlainGuid, @('powershell.exe'), [DateTime]::UtcNow.AddMinutes(-1000 + $i * 3).Ticks, $i, -1, 'x', 'C:\', 'C:\')
  if ($r.Action -eq 'foil') { $r.LogLine }   # commons log themselves; foils are logged by PowerShell after the tab opens
}
Remove-Item Env:POKESHELL_ROLLED, Env:POKESHELL_PULL -ErrorAction SilentlyContinue
[IO.File]::AppendAllLines((Join-Path $st 'pulls.log'), [string[]]@($lines))
$total = @(Get-Content (Join-Path $st 'pulls.log')).Count
$out = Strip (Invoke-Cli collection)
Assert ($out -match "BINDER\s+$total pulls") "binder counts all $total pulls"
Assert ($out -match 'Pikachu' -and $out -match 'card slots filled') "per-character rows and completion"
Assert ($out -match 'best pulls:') "best pulls listed"
Write-Host ($out -split "`n" | Select-Object -First 16 | Out-String)

Write-Host "4. color" -ForegroundColor Cyan
$out = Invoke-Cli color blue
Assert ($out.Contains("$e]4;264;rgb:2f/6f/d6$e\")) "named color -> OSC 4;264"
$out = Invoke-Cli color '#f80'
Assert ($out.Contains("$e]4;264;rgb:ff/88/00$e\")) "3-digit hex"
$out = Invoke-Cli color reset
Assert ($out.Contains("$e]104;264$e\")) "reset -> OSC 104;264"
$null = Invoke-Cli color papaya whip
Assert ((Get-Content (Join-Path $st 'color-misses.log')) -match "papaya whip`tcss:ffefd5") "unknown name: CSS fallback + miss log"

Remove-Item $st -Recurse -Force -ErrorAction SilentlyContinue
Write-Host ''
if ($script:Failures) { Write-Host "cli: $script:Failures FAILED" -ForegroundColor Red; exit 1 }
Write-Host "cli: all passed" -ForegroundColor Green
