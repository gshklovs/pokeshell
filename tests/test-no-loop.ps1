<#
Proves the startup pull can't turn into a tab-spawning loop.
Simulates tabs in-process (fake clock, forced 100% foil odds, dry-run spawns: no real tab is ever opened),
then checks the gate with real concurrent processes and the real hook in real child processes.
  powershell -NoProfile -File tests\test-no-loop.ps1
#>
. (Join-Path $PSScriptRoot '_setup.ps1')
$tps = 10000000L
$t0 = [DateTime]::UtcNow.Ticks

# one simulated tab startup; returns the roll result
function Start-SimTab([string]$StateDir, [string]$ProfileId, [string[]]$Argv, [long]$Now, [hashtable]$Env = @{}) {
  Invoke-Fresh -Env $Env { Invoke-PokeshellRoll -Root $RepoRoot -StateDir $StateDir -ProfileId $ProfileId -Argv $Argv -Now $Now -FoilChance 1 -DryRun -Quiet }
}

# what the tab that WT opens from a dry-run spawn looks like: its profile GUID and its argv
function Get-ChildTab($Result) {
  $a = $Result.wtArgs
  $exeAt = [array]::IndexOf($a, ($a | Where-Object { $_ -match '(powershell|pwsh)\.exe$' } | Select-Object -First 1))
  @{ profile = $a[4]; argv = @($a[$exeAt..($a.Count - 1)]) }
}

Write-Host "1. a foil pull's own tab never rolls" -ForegroundColor Cyan
$st = New-TestState 'chain'
$r = Start-SimTab $st $PlainGuid @('powershell.exe') $t0
Assert ($r.action -eq 'foil') "fresh plain tab with forced foil odds spawns a skinned tab ($($r.Pack)/$($r.Skin))"
$child = Get-ChildTab $r
Assert ($child.profile -ne $PlainGuid) "the child tab uses the skin's own profile $($child.profile)"
$c1 = Start-SimTab $st $child.profile $child.argv ($t0 + 5 * $tps) @{ POKESHELL_PULL = '1' }
Assert ($c1.action -eq 'skip') "child as WT would really start it: skipped ($($c1.reason))"

Write-Host "2. each identity layer stops the child on its own" -ForegroundColor Cyan
$now = $t0 + 100 * $tps
$c = Start-SimTab $st $child.profile @('powershell.exe') $now
Assert ($c.action -eq 'skip' -and $c.reason -eq 'profile') "profile layer alone (no args, no marker): $($c.reason)"
$c = Start-SimTab $st $PlainGuid $child.argv $now
Assert ($c.action -eq 'skip' -and $c.reason -eq 'args') "argv layer alone (plain profile, no marker): $($c.reason) [argv: $($child.argv[1..3] -join ' ') ...]"
$c = Start-SimTab $st $PlainGuid @('powershell.exe') $now @{ POKESHELL_PULL = '1' }
Assert ($c.action -eq 'skip' -and $c.reason -like 'marker*') "POKESHELL_PULL marker alone: $($c.reason)"
$c = Start-SimTab $st $PlainGuid @('powershell.exe') $now @{ POKESHELL_ROLLED = '1' }
Assert ($c.action -eq 'skip' -and $c.reason -like 'marker*') "POKESHELL_ROLLED marker alone (a nested 'powershell' typed in a tab): $($c.reason)"
$c = Start-SimTab $st $PlainGuid @('powershell.exe', '-NoLogo') $now
Assert ($c.action -ne 'skip') "-NoLogo alone still counts as a fresh tab ($($c.action))"
foreach ($bad in @(@('-Command', 'x'), @('-NoExit'), @('-File', 'a.ps1'), @('-NonInteractive'), @('-EncodedCommand', 'AA=='))) {
  $c = Start-SimTab $st $PlainGuid (@('powershell.exe') + $bad) ($now + 1000 * $tps)
  Assert ($c.reason -eq 'args') "argv '$($bad -join ' ')' never rolls"
}
$c = Start-SimTab $st $PlainGuid @('powershell.exe') $now @{ POKESHELL_DISABLE = '1' }
Assert ($c.reason -eq 'disabled') "POKESHELL_DISABLE=1 kill switch"
$c = Start-SimTab $st '' @('powershell.exe') $now
Assert ($c.reason -eq 'not-windows-terminal') "outside Windows Terminal (no WT_PROFILE_ID)"

Write-Host "3. worst case: every identity layer defeated, the child looks exactly like a fresh plain tab" -ForegroundColor Cyan
# 3a. the chain: each spawned tab immediately starts again 50 ms later
$st = New-TestState 'worst-chain'
$now = $t0; $spawns = 0; $gen = 0
while ($gen -lt 1000) {
  $r = Start-SimTab $st $PlainGuid @('powershell.exe') $now
  $gen++
  if ($r.action -ne 'foil') { break }
  $spawns++; $now += [long](0.05 * $tps)
}
Assert ($spawns -eq 1) "chain dies after $spawns spawn (tab $gen was refused: $($r.action))"

# 3b. a flood: a new plain-looking tab every 50 ms for 2 minutes, every one a forced foil
$st = New-TestState 'worst-flood'
$times = [Collections.Generic.List[long]]::new(); $now = $t0
for ($i = 0; $i -lt 2400; $i++) {
  $r = Start-SimTab $st $PlainGuid @('powershell.exe') $now
  if ($r.action -eq 'foil') { $times.Add($now) }
  $now += [long](0.05 * $tps)
}
$gaps = @(for ($k = 1; $k -lt $times.Count; $k++) { ($times[$k] - $times[$k - 1]) / $tps })
Assert ($times.Count -le [Pokeshell.Core]::Burst) "2400 startups in 120 s -> $($times.Count) spawns (limit $([Pokeshell.Core]::Burst), then the breaker trips)"
Assert (-not ($gaps | Where-Object { $_ -lt [Pokeshell.Core]::MinGapSec })) "spawns at least $([Pokeshell.Core]::MinGapSec) s apart (gaps: $(($gaps | ForEach-Object { '{0:0.00}' -f $_ }) -join ', ') s)"
$gate = Get-Content (Join-Path $st 'spawn-gate.txt') | Where-Object { $_ -like 'trip *' }
Assert ([bool]$gate) "breaker tripped ($gate)"

# 3c. one startup per second for an hour
$st = New-TestState 'worst-hour'
$times = [Collections.Generic.List[long]]::new(); $now = $t0
for ($i = 0; $i -lt 3600; $i++) {
  $r = Start-SimTab $st $PlainGuid @('powershell.exe') $now
  if ($r.action -eq 'foil') { $times.Add($now) }
  $now += $tps
}
$maxWin = 0; foreach ($t in $times) { $w = @($times | Where-Object { $_ -ge $t -and $_ -lt $t + 60 * $tps }).Count; if ($w -gt $maxWin) { $maxWin = $w } }
Assert ($times.Count -le 35) "3600 startups over an hour -> $($times.Count) spawns total"
Assert ($maxWin -le [Pokeshell.Core]::Burst) "never more than $([Pokeshell.Core]::Burst) spawns in any 60 s window (max $maxWin)"

Write-Host "4. the gate holds under real concurrency (separate processes, same instant)" -ForegroundColor Cyan
$st = New-TestState 'concurrent'
$worker = Join-Path $st 'worker.ps1'
@"
. '$RepoRoot\scripts\lib\roll.ps1'; Import-PokeshellCore '$st'
`$go = [long]`$args[0]
while ([DateTime]::UtcNow.Ticks -lt `$go) { }
[Pokeshell.Core]::EnterSpawnGate('$st', [DateTime]::UtcNow.Ticks)
"@ | Set-Content $worker
$go = [DateTime]::UtcNow.AddSeconds(3).Ticks
$procs = 1..12 | ForEach-Object {
  Start-Process powershell.exe -ArgumentList '-NoProfile', '-File', $worker, $go -NoNewWindow -PassThru -RedirectStandardOutput (Join-Path $st "out$_.txt")
}
$procs | Wait-Process -Timeout 60
$answers = 1..12 | ForEach-Object { (Get-Content (Join-Path $st "out$_.txt") -Raw).Trim() }
$ok = @($answers | Where-Object { $_ -eq 'ok' }).Count
Assert ($ok -eq 1) "12 simultaneous spawn attempts -> $ok allowed ($(($answers | Group-Object | ForEach-Object { "$($_.Name) x$($_.Count)" }) -join ', '))"

Write-Host "5. the real hook in real child processes" -ForegroundColor Cyan
$st = New-TestState 'hook'
$hook = Join-Path $RepoRoot 'scripts\pokeshell-profile.ps1'
$probe = Join-Path $st 'probe.ps1'
"`$env:WT_PROFILE_ID = '$PlainGuid'; . '$hook'; if (`$env:POKESHELL_ROLLED) { 'rolled' } else { 'skipped' }" | Set-Content $probe
$env:POKESHELL_HOME = $st; $env:POKESHELL_DRYRUN = '1'
try {
  $out = & powershell.exe -NoProfile -File $probe
  Assert ($out -contains 'skipped') "powershell -File <script> with the plain profile id: hook skipped ($out)"
  $out = & powershell.exe -NoProfile -Command ". '$probe'"
  Assert ($out -contains 'skipped') "powershell -Command: hook skipped ($out)"
} finally { Remove-Item Env:POKESHELL_HOME, Env:POKESHELL_DRYRUN -ErrorAction SilentlyContinue }
Assert (-not (Test-Path (Join-Path $st 'dryrun-spawns.log')) -and -not (Test-Path (Join-Path $st 'pulls.log'))) "no pulls, no spawns recorded"

# the pulled tab's command really prints the pull (decode the dry-run spawn and run it)
$st = New-TestState 'pulled'
$r = Start-SimTab $st $PlainGuid @('powershell.exe') $t0
$enc = $r.wtArgs[$r.wtArgs.Count - 1]
$env:POKESHELL_HOME = $st; try { $out = (& powershell.exe -NoProfile -EncodedCommand $enc | Out-String) } finally { Remove-Item Env:POKESHELL_HOME }
$e = [char]27; $plainOut = $out -replace "$e\[[0-9;]*m", ''
Assert ($plainOut -match (' : |' + [char]0x256d)) "the pulled tab's -EncodedCommand prints the card (banner or frame): '$(($plainOut -split "`n" | Where-Object { $_ -match (' : |' + [char]0x256d) } | Select-Object -First 1).Trim())'"

Write-Host "6. a foil that can't find its own tab in the foreground Windows Terminal window stays here" -ForegroundColor Cyan
# this test process isn't a pane of the foreground WT window, so placement must refuse (no tab replaced)
$st = New-TestState 'placement'
$env:POKESHELL_PLACEMENT = '1'
try { $r = Start-SimTab $st $PlainGuid @('powershell.exe') $t0 } finally { Remove-Item Env:POKESHELL_PLACEMENT }
Assert ($r.Action -eq 'foil-denied' -and $r.Reason -like 'placement:*') "foil refused: $($r.Reason)"
Assert (-not (Test-Path (Join-Path $st 'dryrun-spawns.log'))) "no tab opened"
$logged = (Get-Content (Join-Path $st 'pulls.log') | Select-Object -Last 1).Split("`t")
Assert ($logged[3] -eq 'common' -and $logged[7] -like 'foil-not-placed:*') "logged as the common it showed ($($logged[3]), $($logged[7]))"

Get-ChildItem ([IO.Path]::GetTempPath()) -Directory -Filter "pokeshell-test-*-$PID" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Host ''
if ($script:Failures) { Write-Host "no-loop: $script:Failures FAILED" -ForegroundColor Red; exit 1 }
Write-Host "no-loop: all passed" -ForegroundColor Green
