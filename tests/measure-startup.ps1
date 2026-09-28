<#
Measures what the $PROFILE hook adds to a new tab's startup, in fresh powershell.exe processes
(cold: nothing cached by an earlier call in the same process). Dry-run: no tab is opened.
  powershell -NoProfile -File tests\measure-startup.ps1 [-Runs 15]
Cases:
  skip    a tab that doesn't roll (skinned tab, Claude tab, `powershell -Command`): the guard checks
  common  a fresh plain tab that pulls a common: roll + read the prebuilt .ans + write it
  foil    a fresh plain tab that pulls a foil: roll + spawn gate, up to (not including) the wt.exe call
  cold    the first tab after a pack/art change: the roll cache is rebuilt (rare)
#>
param([int]$Runs = 15, [string]$HookRoot)   # -HookRoot: measure a deployed copy (e.g. <state>\current) instead of the repo
. (Join-Path $PSScriptRoot '_setup.ps1')
if (-not $HookRoot) { $HookRoot = $RepoRoot }
$st = New-TestState 'timing'
$probe = Join-Path $st 'probe.ps1'
@'
param($Case, $Root, $State)
$env:POKESHELL_HOME = $State
$plain = '{61c54bbd-c2c6-5271-96e7-009a87ff44bf}'
$env:WT_PROFILE_ID = $plain
if ($Case -eq 'cold') { [IO.File]::Delete("$State\roll.tsv") }
if ($Case -eq 'foil') { [IO.File]::Delete("$State\spawn-gate.txt") }
$sw = [Diagnostics.Stopwatch]::StartNew()
if ($Case -eq 'baseline') {
  # no pokeshell at all: the same probe with an empty profile line (PowerShell's own first-statement warm-up)
  & { $x = $env:WT_PROFILE_ID }
} elseif ($Case -eq 'skip') {
  # the real hook, as-is: this process has arguments, so it stops at the pre-filter
  . "$Root\scripts\pokeshell-profile.ps1"
} else {
  # the real hook's text with a fresh tab's argv (no arguments) and forced odds substituted in
  . "$State\hook-$Case.ps1"
}
$script:action = if ($env:POKESHELL_PULL) { 'foil' } elseif ($env:POKESHELL_ROLLED) { 'rolled' } else { 'skip' }
$ms = $sw.Elapsed.TotalMilliseconds
[Console]::Out.WriteLine("RESULT`t$Case`t$ms`t$script:action")
'@ | Set-Content $probe
$hookText = [IO.File]::ReadAllText("$HookRoot\scripts\pokeshell-profile.ps1").Replace('$PSScriptRoot', '$__hookDir').Replace('[Environment]::GetCommandLineArgs()', "@('powershell.exe')")
if (-not $hookText.Contains('$lib, -1)')) { throw 'measure-startup: hook layout changed; update the substitution' }
foreach ($c in @(@('common', '0'), @('foil', '1'), @('cold', '0'))) {
  $t = $hookText.Replace('$lib, -1)', '$lib, ' + $c[1] + ')')
  $t = "`$env:POKESHELL_DRYRUN = '1'`r`n" + $t     # never open a real tab, whatever the dice say
  $t = "`$__hookDir = '$HookRoot\scripts'`r`n" + $t
  [IO.File]::WriteAllText("$st\hook-$($c[0]).ps1", $t)
}
$env:POKESHELL_HOME = $st
[void](New-PokeshellCore $st)   # compile the core into the test state (a real install does this)
Update-PokeshellRollCache -Root $HookRoot -StateDir $st
Remove-Item Env:POKESHELL_HOME

$script:acts = @{}
function Measure-Case([string]$Case, [int]$N) {
  $vals = foreach ($i in 1..$N) {
    $err = & powershell.exe -NoProfile -File $probe $Case $HookRoot $st | Where-Object { "$_" -like 'RESULT*' }
    $f = "$err".Split("`t"); $script:acts[$Case] = $f[3]; [double]$f[2]
  }
  $s = $vals | Sort-Object
  [pscustomobject]@{ case = $Case; outcome = $script:acts[$Case]; runs = $N; median_ms = [math]::Round($s[[int]($s.Count / 2)], 1); min_ms = [math]::Round($s[0], 1); max_ms = [math]::Round($s[-1], 1) }
}

# warm the cache once, then measure
& powershell.exe -NoProfile -File $probe 'common' $HookRoot $st | Out-Null
$rows = @(
  Measure-Case 'baseline' $Runs
  Measure-Case 'skip' $Runs
  Measure-Case 'common' $Runs
  Measure-Case 'foil' $Runs
  Measure-Case 'cold' ([Math]::Max(3, [int]($Runs / 3)))
)
Write-Host ("(for scale: powershell.exe itself takes several hundred ms to start; our budget is ~50 ms)")
if (Test-Path "$st\errors.log") { Write-Host "errors.log:"; Get-Content "$st\errors.log" | Select-Object -Last 5 | Write-Host }
Remove-Item $st -Recurse -Force -ErrorAction SilentlyContinue
$want = @{ baseline = 'skip'; skip = 'skip'; common = 'rolled'; foil = 'foil'; cold = 'rolled' }
$wrong = @($rows | Where-Object { $_.outcome -ne $want[$_.case] })
if ($wrong) { Write-Host "unexpected outcome: $($wrong.case -join ', ')" -ForegroundColor Red; exit 1 }
$b = ($rows | Where-Object case -eq 'baseline').median_ms
foreach ($row in $rows) { $row | Add-Member added_ms ([math]::Round($row.median_ms - $b, 1)) }
$rows | Format-Table case, outcome, runs, median_ms, added_ms, min_ms, max_ms -AutoSize | Out-String | Write-Host
# budget: what a tab that doesn't roll, and a common pull, add on top of the baseline
$bad = @($rows | Where-Object { $_.case -in 'skip', 'common' -and $_.added_ms -gt 50 })
if ($bad) { Write-Host "startup budget exceeded: $($bad.case -join ', ')" -ForegroundColor Red; exit 1 }
Write-Host "startup: within the 50 ms budget" -ForegroundColor Green
