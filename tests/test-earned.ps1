<#
The earned rule and the binder entry points (docs/BINDER_SPEC.md), against throwaway state dirs and settings copies:
pull ids + pending in pulls.log, the tab's first command earning it (the prompt / OnIdle hook, in child processes),
expiry (24 h, another boot session), viewed.txt / NEW, the earn setting, the binder footer link, `binder` (app,
text fallback, --web), the Windows Terminal hotkey on settings.json COPIES, and the pokeshell:// handler as a dry run.
Never opens a tab, a window or a browser; never touches the real settings.json, registry, $PROFILE or state.
  powershell -NoProfile -File tests\test-earned.ps1
#>
. (Join-Path $PSScriptRoot '_setup.ps1')
. (Join-Path $RepoRoot 'scripts\lib\wtsettings.ps1')
$tps = 10000000L
$e = [char]27
function Strip([string]$s) { $s -replace "$e\[[0-9;]*m", '' -replace "$e\][^$e]*$e\\", '' }
$cli = Join-Path $RepoRoot 'scripts\pokeshell.ps1'
# Invoke-Cli <state> <cli args...> [@{ ENV = value }]
function Invoke-Cli {
  $State = $args[0]; $rest = @($args | Select-Object -Skip 1); $Env = @{}
  if ($rest.Count -and $rest[-1] -is [hashtable]) { $Env = $rest[-1]; $rest = @($rest | Select-Object -SkipLast 1) }
  $saved = @{}; $Env['POKESHELL_HOME'] = $State
  foreach ($k in $Env.Keys) { $saved[$k] = [Environment]::GetEnvironmentVariable($k); [Environment]::SetEnvironmentVariable($k, $Env[$k]) }
  $ErrorActionPreference = 'Continue'   # warnings on stderr (e.g. the web export's) are output, not failures
  try { & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $cli @rest 2>&1 | ForEach-Object { "$_" } | Out-String -Width 300 }
  finally { foreach ($k in $saved.Keys) { [Environment]::SetEnvironmentVariable($k, $saved[$k]) } }
}
function Roll-Common([string]$State, [long]$Now = [DateTime]::UtcNow.Ticks, [double]$Foil = 0) {
  Invoke-Fresh { [Pokeshell.Core]::Roll($RepoRoot, $State, $PlainGuid, @('powershell.exe'), $Now, 7, $Foil, 'x', $env:TEMP, (Join-Path $RepoRoot 'scripts\lib')) }
}
$real = Get-PokeshellWtSettingsPath
$realHash = if ($real) { (Get-FileHash $real).Hash }
$regKey = 'HKCU:\Software\Classes\pokeshell'
$regBefore = Test-Path $regKey

Write-Host "1. every roll gets a pull id, is logged pending, and the tab carries it" -ForegroundColor Cyan
$st = New-TestState 'earn-roll'
Update-PokeshellRollCache -Root $RepoRoot -StateDir $st
$saved = $env:POKESHELL_PULL
$r = Invoke-Fresh { $x = [Pokeshell.Core]::Roll($RepoRoot, $st, $PlainGuid, @('powershell.exe'), [DateTime]::UtcNow.Ticks, 7, 0, 'x', $env:TEMP, $env:TEMP); [pscustomobject]@{ r = $x; env = $env:POKESHELL_PULL } }
$line = @(Get-Content (Join-Path $st 'pulls.log'))[-1].Split("`t")
Assert ($r.r.Action -eq 'common' -and $r.r.Id -match '^[0-9A-HJKMNP-TV-Z]{26}$') "a common pull gets a ULID ($($r.r.Id))"
Assert ($r.env -eq $r.r.Id) "POKESHELL_PULL = the pull id in the tab that rolled"
Assert ($line[7] -eq 'pending' -and $line[8] -eq "id=$($r.r.Id)" -and $line[9] -match '^boot=\d+$') "logged: flags 'pending', id=, boot= ($($line[7..9] -join ' '))"
Assert ([Math]::Abs([Pokeshell.Core]::PullIdTicks($r.r.Id) - $r.r.PullTicks) -lt 10000) "the id encodes the roll time"
$t1 = [DateTime]::UtcNow.Ticks
$ids = @(1..50 | ForEach-Object { [Pokeshell.Core]::NewPullId($t1 + $_ * 10000) })
Assert (@($ids | Sort-Object -Unique).Count -eq 50 -and (($ids | Sort-Object) -join ',') -eq ($ids -join ',')) "ids are unique and sort by time"
$text = Strip $r.r.Text
Assert ($text.Contains("binder $([char]0x23ce)") -and $r.r.Text.Contains("$e]8;;pokeshell://binder?pull=$($r.r.Id)$e\")) "the card's footer: 'binder ⏎', an OSC 8 link to pokeshell://binder?pull=<id>"
Assert ($r.r.Text.LastIndexOf([char]0x2570) -lt $r.r.Text.IndexOf("$e]8;;")) "the art itself is not inside the link (it opens after the card's bottom edge)"
$f = Roll-Common $st ([DateTime]::UtcNow.Ticks + 3600 * $tps) 1
$cmd = [Text.Encoding]::Unicode.GetString([Convert]::FromBase64String($f.WtArgs[-1]))
Assert ($f.Action -eq 'foil' -and $cmd.StartsWith("`$env:POKESHELL_PULL='$($f.Id)';") -and $cmd.Contains("-PullId '$($f.Id)'") -and $cmd.Contains("-StateDir '$st'")) "a foil's skinned tab carries the id (POKESHELL_PULL + Show-PokeshellPull -PullId)"
Assert ($f.Line('dryrun') -match "`tdryrun,pending`tid=$($f.Id)`tboot=\d+$" -and $f.FallbackLine('foil-not-placed:x') -match "`tfoil-not-placed:x,pending`tid=") "foil log lines: notes first, then pending, then the id"
Assert ($f.FallbackText.Contains("pull=$($f.Id)")) "a foil shown here as a common links the same pull"
# the skinned tab's command, run in a child process (dry run: it only prints and registers the hook)
$out = Invoke-Fresh { $env:POKESHELL_HOME = $st; try { & powershell.exe -NoProfile -EncodedCommand $f.WtArgs[-1] 2>&1 | Out-String } finally { Remove-Item Env:POKESHELL_HOME } }
Assert ((Strip $out).Contains("binder $([char]0x23ce)") -and -not (Test-Path (Join-Path $st 'errors.log'))) "the skinned tab prints the card with the footer (no errors)"
$env:POKESHELL_PULL = $saved

Write-Host "2. the tab's first real command earns it (the prompt hook, in child processes)" -ForegroundColor Cyan
$hookProbe = Join-Path $st 'hook.ps1'
function Invoke-Hook([string]$Body, [string]$Mode = 'first-command', [long]$Ticks = [DateTime]::UtcNow.Ticks, [string]$Id = [Pokeshell.Core]::NewPullId([DateTime]::UtcNow.Ticks), [string]$Before = '') {
  @"
`$ErrorActionPreference = 'Stop'
. '$RepoRoot\scripts\lib\roll.ps1'; Import-PokeshellCore '$st'
function global:prompt { 'ORIG> ' }
$Before
[Pokeshell.Earn]::Register(`$ExecutionContext, '$Id', '$st', '$Mode', $Ticks, 'Pikachu', 'holo', `$true)
function Hooked { [Pokeshell.Earn]::Active -and `$null -ne `$ExecutionContext.InvokeCommand.PreCommandLookupAction }
function Cmd { Add-History -InputObject ([pscustomobject]@{ CommandLine = 'git status'; ExecutionStatus = [Management.Automation.Runspaces.PipelineState]::Completed; StartExecutionTime = [datetime]::Now; EndExecutionTime = [datetime]::Now }) }
$Body
"@ | Set-Content $hookProbe -Encoding UTF8
  & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $hookProbe 2>&1 | Out-String
}
function Earned([string]$Id) { @(Get-Content (Join-Path $st 'pulls.log') | Where-Object { $_ -match "`tearned:$Id$" }).Count }
$id = [Pokeshell.Core]::NewPullId([DateTime]::UtcNow.Ticks)
$out = Invoke-Hook -Id $id @'
"hooked=$(Hooked)"
"p1=$(prompt)"                     # the first prompt: no command yet (an empty Enter looks the same)
"p2=$(prompt)"
Cmd                                # the first real command
"p3=$(prompt)"
"p4=$(prompt)"
"hooked=$(Hooked)"
'@
$plain = Strip $out
Assert ($plain -match 'hooked=True') "registering hooks the prompt (a PreCommandLookupAction)"
Assert ($plain -match 'p1=ORIG> ' -and $plain -match 'p2=ORIG> ' -and $plain -match 'p4=ORIG> ') "the prompt itself still prints as before"
Assert ((($plain -split "`n") | Where-Object { $_ -match 'added to your binder' }).Count -eq 1) "one line, once: '$((($plain -split "`n") | Where-Object { $_ -match 'added to your binder' } | Select-Object -First 1).Trim())'"
Assert ($plain -match "$([char]0x2726) Pikachu holo \(shiny\) added to your binder" -and $out.Contains("$e[2m")) "the line is dim and names the card"
Assert ($plain.IndexOf('added to your binder') -gt $plain.IndexOf('p2=') -and $plain.IndexOf('added to your binder') -lt $plain.IndexOf('p3=')) "printed at the prompt right after the first command, not before"
Assert ((Earned $id) -eq 1) "exactly one earned:<id> line"
Assert ($plain -match 'hooked=False') "then the hook is gone"
# a $PROFILE line after ours defines its own prompt: still hooked, and that prompt is the one shown
$id = [Pokeshell.Core]::NewPullId([DateTime]::UtcNow.Ticks)
$out = Strip (Invoke-Hook -Id $id @'
function global:prompt { 'MINE> ' }          # the user's own prompt, defined later in $PROFILE
"p1=$(prompt)"
Cmd
"p2=$(prompt)"
"p3=$(prompt)"
'@)
Assert ($out -match 'p1=MINE> ' -and $out -match 'added to your binder' -and $out -match 'p3=MINE> ' -and (Earned $id) -eq 1) "a prompt defined later in `$PROFILE: shown as is, and the pull is still earned"
# nothing but empty Enters: stays pending
$id = [Pokeshell.Core]::NewPullId([DateTime]::UtcNow.Ticks)
$out = Strip (Invoke-Hook -Id $id @'
1..5 | ForEach-Object { $null = prompt }
"hooked=$(Hooked)"
'@)
Assert ($out -notmatch 'added to your binder' -and $out -match 'hooked=True' -and (Earned $id) -eq 0) "empty Enters don't earn it"
# another tool's PreCommandLookupAction keeps working, and is put back afterwards
$id = [Pokeshell.Core]::NewPullId([DateTime]::UtcNow.Ticks)
$out = Strip (Invoke-Hook -Id $id -Before '$global:seen = 0; $ExecutionContext.InvokeCommand.PreCommandLookupAction = { param($n, $a) $global:seen++ }' @'
$null = prompt; $null = Get-Date
Cmd; "p=$(prompt)"
"seen=$([int]($global:seen -ge 3)) back=$($null -ne $ExecutionContext.InvokeCommand.PreCommandLookupAction -and -not [Pokeshell.Earn]::Active)"
'@)
Assert ($out -match 'seen=1 back=True' -and (Earned $id) -eq 1) "chains an existing PreCommandLookupAction and restores it"
# minutes:N: the tab open N minutes
$id = [Pokeshell.Core]::NewPullId([DateTime]::UtcNow.Ticks)
$out = Strip (Invoke-Hook -Id $id -Mode 'minutes:2' -Ticks ([DateTime]::UtcNow.AddMinutes(-3).Ticks) '"p=$(prompt)"')
Assert ($out -match 'added to your binder' -and (Earned $id) -eq 1) "earn=minutes:2: a tab open 3 minutes earns at its next prompt, no command needed"
$id = [Pokeshell.Core]::NewPullId([DateTime]::UtcNow.Ticks)
$out = Strip (Invoke-Hook -Id $id -Mode 'minutes:10' 'Cmd; "p=$(prompt)"')
Assert ($out -notmatch 'added to your binder' -and (Earned $id) -eq 0) "earn=minutes:10: a command alone doesn't (yet)"
# a tab left open over 24 h: expired, not earned
$id = [Pokeshell.Core]::NewPullId([DateTime]::UtcNow.AddHours(-25).Ticks)
$out = Strip (Invoke-Hook -Id $id -Ticks ([DateTime]::UtcNow.AddHours(-25).Ticks) 'Cmd; "p=$(prompt)"')
Assert ($out -notmatch 'added to your binder' -and (Earned $id) -eq 0 -and @(Get-Content (Join-Path $st 'pulls.log') | Where-Object { $_ -match "`texpired:$id$" }).Count -eq 1) "used after 24 h: logged expired:<id>, no line"
# earn=off: nothing to hook
$out = Strip (Invoke-Hook -Mode 'off' '"hooked=$(Hooked)"')
Assert ($out -match 'hooked=False') "earn=off: no hook at all"
Assert (-not (Test-Path (Join-Path $st 'errors.log')) -and $out -notmatch 'Exception') "no hook errors"

Write-Host "3. the real `$PROFILE hook registers it for the pull it prints" -ForegroundColor Cyan
$hs = New-TestState 'earn-hook'
Update-PokeshellRollCache -Root $RepoRoot -StateDir $hs
$h = [IO.File]::ReadAllText((Join-Path $RepoRoot 'scripts\pokeshell-profile.ps1'))
if (-not $h.Contains('$lib, -1)')) { throw 'hook layout changed' }
[void](New-PokeshellCore $hs)   # the fast path needs the compiled core
# forced to a common on both paths, and a dry run: whatever happens, no tab is opened
$hook = "`$__hookDir = '$RepoRoot\scripts'`r`n" + $h.Replace('$PSScriptRoot', '$__hookDir').Replace('[Environment]::GetCommandLineArgs()', "@('powershell.exe')").Replace('$lib, -1)', '$lib, 0)').Replace('-Argv $a)', '-Argv $a -FoilChance 0)')
$probe = Join-Path $hs 'probe.ps1'
[IO.File]::WriteAllText($probe, "`$env:WT_PROFILE_ID = '$PlainGuid'; `$env:POKESHELL_HOME = '$hs'; `$env:POKESHELL_DRYRUN = '1'`r`n$hook`r`n" +
  "'PULL=' + `$env:POKESHELL_PULL; 'EARN=' + [Pokeshell.Earn]::Active; 'HOOK=' + (`$null -ne `$ExecutionContext.InvokeCommand.PreCommandLookupAction); 'BINDER=' + [bool](Get-Command binder -ErrorAction SilentlyContinue)")
$out = Invoke-Fresh { & powershell.exe -NoProfile -File $probe 2>&1 | Out-String }
$logged = (@(Get-Content (Join-Path $hs 'pulls.log'))[-1].Split("`t") | Where-Object { $_ -like 'id=*' }) -replace '^id=', ''
Assert ($logged -and $out -match "PULL=$logged" -and $out -match 'EARN=True' -and $out -match 'HOOK=True') "a fresh tab's pull $logged : POKESHELL_PULL set, the earn hook registered"
Assert ($out -match 'BINDER=True') "the hook defines the binder command"
Assert (-not (Test-Path (Join-Path $hs 'errors.log'))) "no hook errors"

Write-Host "4. reading the log: earned / pending / expired, legacy lines, viewed.txt, retired art" -ForegroundColor Cyan
# the pokemon pack is a real-card pack (pack.json "cards"): the art column holds the card id; older lines resolve
# through pack.json "retired" (an old common -> its base-set card; an old holo -> hidden). A card whose art isn't built
# is muted: pulls resolving to it are hidden too. So sections 4-7 run the CLI and the binders on a fixture root (the
# scripts, the web export and pokemon's pack.json copied, fake art for the cards below), whatever is built locally.
$fx = Join-Path ([IO.Path]::GetTempPath()) "pokeshell-test-earned-root-$PID"
Remove-Item $fx -Recurse -Force -ErrorAction SilentlyContinue
foreach ($d in 'packs\pokemon', 'dist\pokemon', 'tools\binder-web') { [void][IO.Directory]::CreateDirectory((Join-Path $fx $d)) }
Copy-Item -Recurse (Join-Path $RepoRoot 'scripts') $fx
Copy-Item (Join-Path $RepoRoot 'tools\binder_web.py') (Join-Path $fx 'tools')
Copy-Item (Join-Path $RepoRoot 'tools\binder-web\index.html') (Join-Path $fx 'tools\binder-web')
Copy-Item (Join-Path $RepoRoot 'packs\pokemon\pack.json') (Join-Path $fx 'packs\pokemon')
$fxArt = "$e[0;38;2;10;20;30m" + [char]0x2580 + "$e[0m`n"
$fxBuilt = 'bulbasaur-base1-44', 'charmander-base1-46', 'pikachu-base1-58', 'squirtle-base1-63', 'bulbasaur-sv3pt5-166', 'charmander-sv3pt5-168',
  'squirtle-sv3pt5-170', 'charmander-sma-SV6', 'glaceon-swsh7-40', 'glaceon-swsh7-41', 'glaceon-swsh7-174', 'glaceon-swsh7-175'   # 12 built; e.g. swsh4-170 is not
foreach ($n in $fxBuilt) { [IO.File]::WriteAllText((Join-Path $fx "dist\pokemon\$n.ans"), $fxArt, [Text.UTF8Encoding]::new($false)) }
$cli = Join-Path $fx 'scripts\pokeshell.ps1'
$rs = New-TestState 'earn-read'
$now = [DateTime]::UtcNow; $boot = [Pokeshell.Core]::BootId()
function L($ago, $ch, $tier, $card, $flags, $idTicks, $b = $boot) {
  $id = [Pokeshell.Core]::NewPullId($idTicks)
  @{ id = $id; line = "$($now.AddMinutes(-$ago).ToLocalTime().ToString('s'))`tpokemon`t$ch`t$tier`t$card`t`t0`t$flags`tid=$id`tboot=$b" }
}
$a = L 50 'pikachu' 'common' 'base1-58' 'pending' $now.AddMinutes(-50).Ticks
$b = L 40 'squirtle' 'illustration-rare' 'sv3pt5-170' 'pending' $now.AddMinutes(-40).Ticks
$c = L 1600 'charmander' 'rare-shiny' 'sma-SV6' 'pending' $now.AddHours(-26).Ticks
$d = L 30 'bulbasaur' 'common' 'base1-44' 'denied:rate,pending' $now.AddMinutes(-30).Ticks ($boot - 7200)
$v = L 20 'bulbasaur' 'illustration-rare' 'sv3pt5-166' 'pending' $now.AddMinutes(-20).Ticks
$old = $now.AddDays(-3).ToLocalTime().ToString('s'); $realT = $now.AddDays(-2).ToLocalTime()
function RealLine($min, $ch, $tier, $card) { "$($realT.AddMinutes($min).ToString('s'))`tpokemon`t$ch`t$tier`t$card`t`t0`t" }
$lines = @(
  "$old`tpokemon`tsquirtle`tcommon`tcommon`t`t1`t",   # before the earned rule (and real cards): -> base1-63; a shiny, but older than the best pulls' start
  (RealLine -10 'pikachu' 'rare-ultra' 'swsh4-170'),          # a real card whose art isn't built: hidden (and not the best pulls' start)
  (RealLine 0 'glaceon' 'rare-holo-v' 'swsh7-40'), (RealLine 1 'glaceon' 'rare-ultra' 'swsh7-174'), (RealLine 2 'glaceon' 'rare-ultra' 'swsh7-175'),
  (RealLine 3 'glaceon' 'rare-holo-vmax' 'swsh7-41'),         # four Glaceon cards, two of them in one rarity: four slots
  $a.line, "x`tearned:$($a.id)", $b.line, $c.line, $d.line, $v.line, "x`tearned:$($v.id)",
  "$old`tpokemon`tpikachu`tholo`tholo`tsheen`t0`t",     # retired art: hidden
  "$($now.ToLocalTime().ToString('s'))`tpokemon`tpikachu`tcommon`tbase1-58`t`t0`tdryrun,pending`tid=X`tboot=$boot")
[IO.File]::WriteAllLines((Join-Path $rs 'pulls.log'), [string[]]$lines)
[IO.File]::WriteAllLines((Join-Path $rs 'viewed.txt'), [string[]]@($v.id))
$recs = @([Pokeshell.Core]::ReadPulls($rs, $now.Ticks, $boot))
$got = ($recs | ForEach-Object { "$($_.Character)/$($_.Status)$(if ($_.New) { '+new' })" }) -join ' '
Assert ($got -eq 'squirtle/earned pikachu/earned glaceon/earned glaceon/earned glaceon/earned glaceon/earned pikachu/earned+new squirtle/pending charmander/expired bulbasaur/expired bulbasaur/earned pikachu/earned') "statuses: $got"
Assert (($recs | Where-Object Status -eq 'expired' | ForEach-Object Derived) -notcontains $false) "expired by age / boot: derived, no event yet"
$out = Strip (Invoke-Cli $rs 'collection')
Assert ($out -match 'BINDER\s+7 pulls' -and $out -match '1 pending' -and $out -match '1 new' -and $out -match '2 pulls of retired art not shown') "pokeshell collection counts earned pulls only, shows pending, new and retired (+ unbuilt): '$((($out -split "`n") | Where-Object { $_ -match 'BINDER' }).Trim())'"
Assert ($out -match '7/12 card slots filled') "every built card is a slot, unbuilt ones are not; two Glaceon cards of one rarity are two slots (7/12)"
Assert ($out -match 'Glaceon\s.*2 \(2/2\)' -and $out -notmatch 'Vivid Voltage|Pikachu V') "the Glaceon row: 2 pulls of its 2 rare-ultra cards"
$sinceLabel = $realT.ToString('MMM d', [Globalization.CultureInfo]::InvariantCulture)
Assert ($out -match "best pulls \(since $sinceLabel\):" -and $out -match 'rare ultra : Glaceon' -and $out -notmatch 'Squirtle \(shiny\)') "best pulls start when the real cards went live (the first built real-card pull, $sinceLabel); the old shiny is left out"
$day = $now.AddDays(-1).ToLocalTime()
[IO.File]::WriteAllLines((Join-Path $rs 'config.txt'), [string[]]@("best_since=$($day.ToString('yyyy-MM-dd'))"))
$outDay = Strip (Invoke-Cli $rs 'collection')
Assert ($outDay -match "best pulls \(since $($day.ToString('MMM d', [Globalization.CultureInfo]::InvariantCulture))\):" -and $outDay -match 'illustration rare : Bulbasaur' -and $outDay -notmatch ': Glaceon') "config best_since=<date>: from that day on"
[IO.File]::WriteAllLines((Join-Path $rs 'config.txt'), [string[]]@('best_since=all'))
$outAll = Strip (Invoke-Cli $rs 'collection')
Assert ($outAll -match '  best pulls:' -and $outAll -match 'rare ultra : Glaceon') "config best_since=all: every pull, no cutoff label"
Remove-Item (Join-Path $rs 'config.txt')
$exp = @(Get-Content (Join-Path $rs 'pulls.log') | Where-Object { $_ -match "`texpired:" })
Assert ($exp.Count -eq 2 -and ($exp -join ' ') -match $c.id -and ($exp -join ' ') -match $d.id) "reading writes the expired:<id> lines (append-only)"
$null = Invoke-Cli $rs 'collection'
Assert (@(Get-Content (Join-Path $rs 'pulls.log') | Where-Object { $_ -match "`texpired:" }).Count -eq 2) "... once"

Write-Host "5. the earn setting" -ForegroundColor Cyan
$cs = New-TestState 'earn-cfg'
$out = Strip (Invoke-Cli $cs 'earn')
Assert ($out -match 'earn: first-command') "default: first-command"
$null = Invoke-Cli $cs 'earn' 'minutes:2'
Assert ((Get-Content (Join-Path $cs 'config.txt')) -contains 'earn=minutes:2') "earn minutes:2 saved"
$out = Strip (Invoke-Cli $cs 'earn' 'sometimes')
Assert ($out -match 'first-command, minutes:N or off' -and (Get-Content (Join-Path $cs 'config.txt')) -contains 'earn=minutes:2') "a bad value is refused, setting kept"
$null = Invoke-Cli $cs 'earn' 'off'
$r = Roll-Common $cs
$line = @(Get-Content (Join-Path $cs 'pulls.log'))[-1].Split("`t")
Assert ($r.Earn -eq 'off' -and $line[7] -eq '' -and $line[8] -eq "id=$($r.Id)") "earn off: the pull still gets an id but is logged earned (no pending flag)"
Assert ([Pokeshell.Core]::EarnMode('MINUTES:1.5') -eq 'minutes:1.5' -and [Pokeshell.Core]::EarnMode('junk') -eq 'first-command') "EarnMode normalizes"

Write-Host "6. binder: the app, the text fallback, --pull / --card" -ForegroundColor Cyan
$out = Strip (Invoke-Cli $rs 'binder' @{ POKESHELL_BINDER = (Join-Path $rs 'no-such-binder.exe') })
Assert ($out -match "binder app isn't built" -and $out -match 'BINDER\s+7 pulls') "no exe: the text table"
$exe = Join-Path $RepoRoot 'binder\target\release\binder.exe'
if (Test-Path $exe) {
  $viewedBefore = (Get-FileHash (Join-Path $rs 'viewed.txt')).Hash
  $frame = Strip (& $exe --root $fx --state $rs --first-frame | Out-String)
  Assert ($frame -match 'last Bulbasaur illustration rare' -and $frame -match '1 pending' -and $frame -match '1 new') "the app opens on the newest pull (bulbasaur illustration rare); header counts pending and new"
  Assert ($frame -match '\b8 pulls' -and $frame -match 'best pulls' -and $frame -match "since $sinceLabel") "unbuilt and retired pulls are left out (8 shown); best pulls since ${sinceLabel} (on the panel's bottom border): $((($frame -split "`n") | Select-Object -First 1).Trim()) / $((($frame -split "`n") | Where-Object { $_ -match 'since' }) -replace '.*(since)', '$1')"
  $frame = Strip (& $exe --root $fx --state $rs --pull $a.id --first-frame | Out-String)
  Assert ($frame -match 'Pikachu' -and $frame -match 'NEW' -and $frame -match 'collected') "--pull <id> opens that pull, with its NEW sticker"
  $frame = Strip (& $exe --root $fx --state $rs --card 'pokemon/charmander/rare shiny' --first-frame | Out-String)
  Assert ($frame -match 'Charmander' -and $frame -match 'SV6/SV94' -and $frame -match 'not pulled yet') "--card pack/character/tier (tier by label) opens that card"
  $frame = Strip (& $exe --root $fx --state $rs --card 'pokemon/sv3pt5-170' --first-frame | Out-String)
  Assert ($frame -match 'Squirtle' -and $frame -match 'pending') "--card pack/<card id> opens that real card"
  $frame = Strip (& $exe --root $fx --state $rs --url "pokeshell://binder?pull=$($a.id)" --first-frame | Out-String)
  Assert ($frame -match 'Pikachu' -and $frame -match 'NEW') "--url pokeshell://binder?pull=<id> (what the link handler runs)"
  Assert ((Get-FileHash (Join-Path $rs 'viewed.txt')).Hash -eq $viewedBefore) "headless frames don't mark anything viewed"
  # tags and sets: a set's checklist (every pack.json card of the set, pulled or not) and a tag search
  $frame = Strip (& $exe --root $fx --state $rs --set sv3pt5 --first-frame | Out-String)
  Assert ($frame -match 'set 151' -and $frame -match '1/3' -and $frame -match '\+1 pending' -and $frame -match 'Bulbasaur') "--set sv3pt5: that set's checklist (2 of its 3 cards pulled: 1 earned, and 1 pending, which isn't done yet)"
  $frame = Strip (& $exe --root $fx --state $rs --set '151' --first-frame | Out-String)
  Assert ($frame -match 'set 151' -and $frame -match '1/3') "--set by name (fuzzy): 151"
  $frame = Strip (& $exe --root $fx --state $rs --set 'zzz' --first-frame | Out-String)
  Assert ($frame -match 'no set matches') "--set with no match says so"
  $frame = Strip (& $exe --root $fx --state $rs --search 'set:base1 owned' --first-frame | Out-String)
  Assert ($frame -match '/set:base1 owned 2') "--search 'set:base1 owned': tag filter + state word (2 cards)"
  $frame = Strip (& $exe --root $fx --state $rs --search 'rarity:\"illustration rare\" pending' --first-frame | Out-String)
  Assert ($frame -match 'pending 1') "--search with a quoted tag value and a state word"
  $frame = Strip (& $exe --root $fx --state $rs --search 'glaceon owned' --first-frame | Out-String)
  Assert ($frame -match '/glaceon owned 4') "four Glaceon cards pulled (two of one rarity): four slots"
  $frame = Strip (& $exe --root $fx --state $rs --card 'pokemon/swsh4-170' --first-frame | Out-String)
  Assert ($frame -notmatch 'Pikachu V') "an unbuilt card is no slot (--card pokemon/swsh4-170 doesn't land on it)"
  [IO.File]::WriteAllLines((Join-Path $rs 'config.txt'), [string[]]@('best_since=all'))
  $frame = Strip (& $exe --root $fx --state $rs --first-frame | Out-String)
  Assert ($frame -match 'rarest' -and $frame -notmatch 'since [A-Z][a-z][a-z] \d') "config best_since=all: every pull, no cutoff label"
  Remove-Item (Join-Path $rs 'config.txt')
  $out = & $exe --root $fx --state $rs --selftest | Out-String
  Assert ($out -match 'selftest ok') "binder --selftest (keys incl. v / d, mouse, resizes): $($out.Trim())"
} else { Write-Host "  skip  binder.exe not built (binder\build.ps1)" -ForegroundColor Yellow }

Write-Host "7. binder --web (static page into <state>\web; not opened)" -ForegroundColor Cyan
$py = @($env:POKESHELL_PYTHON, (Join-Path $RepoRoot '.venv\Scripts\python.exe'), (Join-Path (Split-Path $RepoRoot) 'pokeshell\.venv\Scripts\python.exe')) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
if ($py) {
  $out = Strip (Invoke-Cli $rs 'binder' '--web' @{ POKESHELL_PYTHON = $py; POKESHELL_NO_OPEN = '1' })
  $data = Get-Content (Join-Path $rs 'web\data.json') -Raw -Encoding UTF8 | ConvertFrom-Json
  $st2 = ($data.pulls | ForEach-Object { "$($_.char)/$($_.status)$(if ($_.new) { '+new' })" }) -join ' '
  Assert ($st2 -eq 'squirtle/collected glaceon/collected glaceon/collected glaceon/collected glaceon/collected pikachu/collected+new squirtle/pending bulbasaur/collected' -and $data.hidden -eq 2) "data.json marks earned vs pending (expired left out, retired art and unbuilt cards hidden): $st2"
  Assert (@($data.pulls | Where-Object char -eq 'glaceon' | ForEach-Object card | Sort-Object -Unique).Count -eq 4) "each Glaceon pull keeps its own card (four slots)"
  Assert ($data.best_since -eq $realT.ToString('s')) "best pulls start at the first built real-card pull ($($data.best_since))"
  Assert ($data.earned.enforced -and (Test-Path (Join-Path $rs 'web\binder.html')) -and $out -match 'web binder at') "binder.html written, not opened ($(($out -split "`n" | Where-Object { $_ -match 'earned' } | Select-Object -First 1).Trim()))"
  Assert ((Get-Content (Join-Path $rs 'web\binder.html') -Raw -Encoding UTF8).Contains('badge-new')) "the page has the NEW sticker"
  $pk = $data.packs | Where-Object id -eq 'pokemon'
  Assert ($pk.layout -eq 'cards' -and @($pk.cards).Count -eq 12 -and -not @($pk.cards | Where-Object id -eq 'swsh4-170') -and (@($pk.sets | ForEach-Object id) -join ',') -match 'base1' -and @($pk.cards | Where-Object set_id -eq 'sv3pt5').Count -eq 3) "real cards: every built card with its set (the checklists) in data.json; unbuilt ones left out"
  $html = Get-Content (Join-Path $rs 'web\binder.html') -Raw -Encoding UTF8
  Assert ($html.Contains('id="setTabs"') -and $html.Contains('id="search"') -and $html.Contains('tagchip')) "the page has set tabs, the search box and tag chips"
  # search: the page's matcher (the block between search:begin / search:end, the rules of binder/src/query.rs) run in
  # node on the real pack.json; the results stay binder pockets, and a click opens the real page
  Assert ($html.Contains('function openResult') -and $html.Contains('pocket--flash') -and $html.Contains('function goBack') -and $html.Contains('pikchu')) "the page opens a result on its real page (glowing), Esc goes back, and the search box names the forgiving syntax"
  $node = Get-Command node -ErrorAction SilentlyContinue
  if ($node) {
    $js = Join-Path $fx 'search-check.js'
    [IO.File]::WriteAllText($js, @'
const fs = require('fs');
const [html, packJson] = process.argv.slice(2);
const src = fs.readFileSync(html, 'utf8');
const block = src.slice(src.indexOf('/* search:begin */'), src.indexOf('/* search:end */'));
const api = new Function(block + '; return { parseQuery, resolveSets, matchHay, field, bestSets };')();
const pk = JSON.parse(fs.readFileSync(packJson, 'utf8').replace(/^\uFEFF/, ''));
const sets = [];
const cards = Object.entries(pk.cards).map(([id, c]) => {
  const sid = id.replace(/-[^-]*$/, '');
  if (!sets.some(s => s.id === sid)) sets.push({ id: sid, name: c.set });
  const tags = [['pack', 'pokemon'], ['char', c.character], ['name', c.name], ['tier', c.tier], ['id', id], ['number', c.number], ['rarity', c.rarity], ['set', sid], ['set', c.set]];
  return { id, c, hay: tags.map(([k, v]) => [k, api.field(v)]) };
});
const find = q => { const p = api.parseQuery(q); api.resolveSets(p.terms, { sets }); return cards.filter(x => api.matchHay(p.terms, x.hay, () => ({ owned: x.id === 'swsh7-92' }))).map(x => x.id); };
const out = { cases: {} };
for (const q of ['pikachu', 'pikchu', 'lyc vmax', 'lycvmax', 'evs rainbow', 'set:30th', 'number:17', 'id:"swsh7-9"', 'id:swsh7-9', '-pikachu set:30th', 'lyc owned', 'rarity:"rare rainbow"', 'rarity:rare rainbow', 'flabebe']) out.cases[q] = find(q);
out.pika = cards.filter(x => x.c.name.includes('Pikachu')).map(x => x.id);
out.rainbows = cards.filter(x => x.id.startsWith('swsh7-') && x.c.rarity === 'Rare Rainbow').map(x => x.id);
out.c30 = cards.filter(x => x.c.set.includes('30th')).map(x => x.id);
out.lycV = cards.filter(x => x.c.name === 'Lycanroc V').map(x => x.id);
out.sets = ['swsh1', 'swsh', 'evsk', 'celebration', 'SWSH7'].map(q => api.bestSets([{ id: 'swsh7', name: 'Evolving Skies' }, { id: 'me55', name: '30th Celebration' }, { id: 'swsh1', name: 'Sword & Shield' }, { id: 'swsh10', name: 'Astral Radiance' }, { id: 'cel25', name: 'Celebrations' }], q).map(s => s.id).join(','));
console.log(JSON.stringify(out));
'@, [Text.UTF8Encoding]::new($false))
    $r = (& $node.Source $js (Join-Path $fx 'tools\binder-web\index.html') (Join-Path $fx 'packs\pokemon\pack.json') | Out-String) | ConvertFrom-Json
    $c = $r.cases
    $has = { param($got, $want) @($want | Where-Object { @($got) -notcontains $_ }).Count -eq 0 }
    Assert ((& $has $c.pikachu $r.pika) -and @($c.pikachu).Count -eq @($r.pika).Count -and (& $has $c.pikchu $r.pika) -and @($c.pikchu).Count -eq @($r.pika).Count) "web search: pikachu and pikchu list every Pikachu card and nothing else ($(@($r.pika).Count))"
    Assert (@($c.'lyc vmax') -contains 'swsh7-92' -and -not @($r.lycV | Where-Object { @($c.'lyc vmax') -contains $_ }) -and @($c.lycvmax) -contains 'swsh7-92') "web search: lyc vmax / lycvmax find Lycanroc VMAX swsh7-92, not Lycanroc V ($(@($c.'lyc vmax') -join ' '))"
    Assert ((& $has $c.'evs rainbow' $r.rainbows) -and @($c.'evs rainbow').Count -eq @($r.rainbows).Count) "web search: evs rainbow is the Evolving Skies rare rainbows ($(@($r.rainbows).Count))"
    Assert ((& $has $c.'set:30th' $r.c30) -and @($c.'set:30th').Count -eq @($r.c30).Count) "web search: set:30th is the 30th Celebration ($(@($r.c30).Count) cards)"
    Assert (@($c.'number:17').Count -gt 0 -and -not @($c.'number:17' | Where-Object { $_ -notmatch '-0*17$' })) "web search: number:17 is the numerator (17/..., not 117 or 170)"
    Assert ((@($c.'id:"swsh7-9"') -join ',') -eq 'swsh7-9' -and (@($c.'id:swsh7-9') -join ',') -eq 'swsh7-9') "web search: id: is the whole id, quoted or not (the app does the same)"
    Assert (@($c.'-pikachu set:30th').Count -eq @($r.c30).Count - @($r.pika | Where-Object { @($r.c30) -contains $_ }).Count) "web search: -pikachu leaves the Pikachu cards out"
    Assert ((@($c.'lyc owned') -join ',') -eq 'swsh7-92') "web search: a state word tests the card (lyc owned)"
    Assert ((& $has $c.'rarity:"rare rainbow"' $r.rainbows) -and @($c.'rarity:rare rainbow').Count -ge @($c.'rarity:"rare rainbow"').Count) "web search: a quoted value keeps its spaces"
    Assert (($r.sets -join ' ') -eq 'swsh1 swsh7,swsh1,swsh10 swsh7 me55,cel25 swsh7') "web search: set: names the best-matching sets like the app (swsh1 is not swsh10; swsh = every swsh; evsk; celebration is both): $($r.sets -join ' / ')"
  } else { Write-Host "  skip  node not found: the page's matcher is not run" -ForegroundColor Yellow }
  Assert ($data.counts.kept -eq 7 -and $data.counts.pending -eq 1) "data.json counts kept pulls only; pending apart ($($data.counts.kept) kept, $($data.counts.pending) pending)"

  # tools\binder_web.py on its own: the text half, pending not counted, unreadable lines, checklist order, the art cache
  $cardsDir = Join-Path $fx 'packs\pokemon\cards'; [void][IO.Directory]::CreateDirectory($cardsDir)
  $cardJson = '{"id":"swsh7-40","name":"Glaceon V","supertype":"Pokémon","subtypes":["Basic","V"],"hp":"210","types":["Water"],"evolvesFrom":"",' +
    '"abilities":[{"name":"Test Ability","text":"Does a thing.","type":"Ability"}],' +
    '"attacks":[{"name":"Frozen Awakening","cost":["Water"],"text":"Search your deck."},{"name":"Heavy Snow","cost":["Water","Colorless","Colorless"],"damage":"120","text":""}],' +
    '"weaknesses":[{"type":"Metal","value":"×2"}],"resistances":[],"retreatCost":["Colorless","Colorless"],"rules":["V rule: two Prize cards."],"flavorText":"",' +
    '"set":{"id":"swsh7","name":"Evolving Skies","printedTotal":203},"number":"40","rarity":"Rare Holo V","artist":"5ban Graphics","tier":"rare-holo-v"}'
  [IO.File]::WriteAllText((Join-Path $cardsDir 'swsh7-40.json'), $cardJson, [Text.UTF8Encoding]::new($false))
  $ws = New-TestState 'earn-web'
  $wout = Join-Path $ws 'web'
  $pid1 = [Pokeshell.Core]::NewPullId($now.AddMinutes(-5).Ticks)
  $wl = @((RealLine 0 'glaceon' 'rare-holo-v' 'swsh7-40'),
    ((RealLine 1 'glaceon' 'rare-ultra' 'swsh7-174') -replace "`t0`t$", "`t1`t"),                                # a kept shiny
    "$($now.AddMinutes(-5).ToLocalTime().ToString('s'))`tpokemon`tglaceon`trare-ultra`tswsh7-175`t`t1`tpending`tid=$pid1`tboot=$boot",   # a pending shiny
    "not-a-time`tpokemon`tglaceon`trare-holo-v`tswsh7-40`t`t0`t")                                                  # a corrupt time
  $bytes = [Text.Encoding]::UTF8.GetBytes(($wl -join "`r`n") + "`r`n") +
    [Text.Encoding]::GetEncoding(28591).GetBytes("$($realT.ToString('s'))`tpokemon`tfl$([char]0xe9)b$([char]0xe9)b$([char]0xe9)`tcommon`tcommon`t`t0`t`r`n")   # PowerShell 5 ANSI bytes
  [IO.File]::WriteAllBytes((Join-Path $ws 'pulls.log'), $bytes)
  $webPy = Join-Path $fx 'tools\binder_web.py'
  function Invoke-WebPy { $ErrorActionPreference = 'Continue'; & $py $webPy @args 2>&1 | ForEach-Object { "$_" } | Out-String -Width 300 }
  $o1 = Invoke-WebPy --root $fx --state $ws --out $wout
  Assert ($LASTEXITCODE -eq 0 -and $o1 -match '2 lines of pulls.log couldn''t be read') "invalid UTF-8 and a corrupt time: skipped with a warning, no crash ($(($o1 -split "`n" | Where-Object { $_ -match 'read' } | Select-Object -First 1).Trim()))"
  $wd = Get-Content (Join-Path $wout 'data.json') -Raw -Encoding UTF8 | ConvertFrom-Json
  Assert ($wd.counts.kept -eq 2 -and $wd.counts.pending -eq 1 -and $wd.counts.shiny -eq 1 -and $wd.bad_lines -eq 2) "a pending shiny is shown but not counted: kept $($wd.counts.kept), pending $($wd.counts.pending), shiny $($wd.counts.shiny)"
  $wpk = $wd.packs | Where-Object id -eq 'pokemon'
  $c40 = $wpk.cards | Where-Object id -eq 'swsh7-40'
  $atk = @($c40.text.attacks)
  Assert ($c40.text.hp -eq '210' -and $atk.Count -eq 2 -and (@($atk[1].cost) -join ',') -eq 'Water,Colorless,Colorless' -and $atk[1].damage -eq '120' -and @($c40.text.abilities)[0].name -eq 'Test Ability' -and @($c40.text.weak)[0].type -eq 'Metal' -and $c40.text.retreat -eq 2 -and @($c40.text.rules).Count -eq 1 -and $c40.artist -eq '5ban Graphics') "the text half is exported: HP, ability, attacks with energy costs and damage, weakness, retreat, rules, artist"
  Assert (-not ($wpk.cards | Where-Object id -eq 'swsh7-41').text -and $o1 -match 'have no card text') "a card without cards\<id>.json exports no text half (the page shows a placeholder) and is warned about"
  Assert ($o1 -match 'no built art' -and $wpk.unbuilt -gt 0) "cards without built art are warned about ($($wpk.unbuilt) unbuilt)"
  $wh = Get-Content (Join-Path $wout 'binder.html') -Raw -Encoding UTF8
  Assert ($wh.Contains('card__text') -and $wh.Contains('tx-cost') -and $wh.Contains('card__wrr') -and -not $wh.Contains('ODDS FROM PACK.JSON')) "the page renders the text half (costs, weakness / resistance / retreat); odds are 'Pull odds'"
  $order = (& $py -c "import sys; sys.path.insert(0, r'$(Join-Path $fx 'tools')'); import binder_web as b; print(','.join(sorted(['TG10', 'B/128', '2', 'SV6a', '100', '', 'GG01', '25a', '215/203', 'SV10', '1/203', 'TG01', 'SV6', '25', 'GG10', '9', '10'], key=b.number_key)))" 2>&1 | Out-String).Trim()
  Assert ($order -eq '1/203,2,9,10,25,25a,100,215/203,GG01,GG10,SV6,SV6a,SV10,TG01,TG10,B/128,') "checklist order: numbers, then each prefix group in numeric order, then letters alone ($order)"
  $stale = Join-Path $wout 'img\pokemon\gone\old-card.png'; [void][IO.Directory]::CreateDirectory((Split-Path $stale)); [IO.File]::WriteAllBytes($stale, [byte[]](1, 2, 3))
  $sw = [Diagnostics.Stopwatch]::StartNew(); $o2 = Invoke-WebPy --root $fx --state $ws --out $wout; $sw.Stop()
  Assert ($o2 -match '[(]0 decoded' -and $o2 -match 'cached' -and $o2 -match 'stale removed' -and -not (Test-Path $stale)) "a rerun reuses the decoded art (img\.cache.json) and prunes stale PNGs ($([int]$sw.Elapsed.TotalMilliseconds) ms)"
  $nPng = @(Get-ChildItem (Join-Path $wout 'img') -Recurse -Filter *.png).Count
  Remove-Item -Recurse -Force (Join-Path $ws 'noart') -ErrorAction SilentlyContinue
  $o3 = Invoke-WebPy --root $fx --state $ws --out (Join-Path $ws 'noart') --no-art
  Assert ($o3 -match 'art skipped' -and -not (Test-Path (Join-Path $ws 'noart\img')) -and (Test-Path (Join-Path $ws 'noart\binder.html'))) "--no-art decodes and writes no art (still data.json + binder.html; $nPng PNGs in the full export)"
  Assert (-not @(Get-ChildItem $wout -Recurse -Filter '*.tmp')) "writes are atomic (no temp files left)"
} else { Write-Host "  skip  no Python with Pillow (set POKESHELL_PYTHON)" -ForegroundColor Yellow }

$cli = Join-Path $RepoRoot 'scripts\pokeshell.ps1'   # sections 8-9: the repo's CLI again
Remove-Item $fx -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "8. the Ctrl+Shift+B hotkey, on settings.json copies" -ForegroundColor Cyan
$fakeExe = Join-Path $rs 'binder.exe'; Set-Content $fakeExe 'not a real exe'
$utf8 = [Text.UTF8Encoding]::new($false)
$cases = [ordered]@{
  'WT 1.21+ (actions + keybindings)' = "{`r`n    `"actions`": [`r`n        { `"command`": { `"action`": `"copy`" }, `"id`": `"User.copy`" }`r`n    ],`r`n    `"keybindings`": [`r`n        { `"id`": `"User.copy`", `"keys`": `"ctrl+c`" }`r`n    ],`r`n    `"profiles`": { `"list`": [] }`r`n}`r`n"
  'older (keys inside actions)'      = "{`n  `"profiles`": { `"list`": [] },`n  `"actions`": [ { `"command`": `"paste`", `"keys`": `"ctrl+v`" }, ]`n}`n"
  'no actions at all'                = "// comment`n{`n    `"profiles`": { `"list`": [] }`n}`n"
}
# read only: the test edits a copy, minus its pokeshell profiles (uninstall would remove those too)
if ($real) { $cases['your settings.json (a copy)'] = Remove-PokeshellProfilesText (Read-WtSettingsFile $real).text @() }
$i = 0
foreach ($name in $cases.Keys) {
  $i++; $hsState = Join-Path $rs "hk$i"; [void][IO.Directory]::CreateDirectory($hsState)
  $file = Join-Path $hsState 'settings.json'; [IO.File]::WriteAllText($file, $cases[$name], $utf8)
  $orig = [IO.File]::ReadAllBytes($file)
  $out = Strip (Invoke-Cli $hsState 'hotkey' 'on' '-SettingsPath' $file @{ POKESHELL_BINDER = $fakeExe })
  $tree = ConvertFrom-Jsonc (Read-WtSettingsFile $file).text
  $act = @((Get-JsoncMember $tree 'actions').items | Where-Object { Test-PokeshellHotkeyNode $_ })
  $cmdNode = Get-JsoncMember $act[0] 'command'
  $kb = Get-JsoncMember $tree 'keybindings'
  $keys = if ($kb) { (Get-JsoncMember @($kb.items | Where-Object { Test-PokeshellHotkeyNode $_ })[0] 'keys').value } else { (Get-JsoncMember $act[0] 'keys').value }
  Assert ($act.Count -eq 1 -and (Get-JsoncMember $cmdNode 'action').value -eq 'splitPane' -and (Get-JsoncMember $cmdNode 'split').value -eq 'vertical' -and
          (Get-JsoncMember $cmdNode 'commandline').value.StartsWith("`"$fakeExe`"") -and $keys -eq 'ctrl+shift+b') "${name}: splitPane vertical -> binder.exe on ctrl+shift+b"
  Assert (@(Get-ChildItem (Join-Path $hsState 'backups') -Filter *.json).Count -ge 1) "${name}: backup written first"
  $once = [IO.File]::ReadAllBytes($file)
  $null = Invoke-Cli $hsState 'hotkey' 'on' '-SettingsPath' $file @{ POKESHELL_BINDER = $fakeExe }
  Assert ([Convert]::ToBase64String([IO.File]::ReadAllBytes($file)) -eq [Convert]::ToBase64String($once)) "${name}: re-running is idempotent"
  $null = Invoke-Cli $hsState 'uninstall' '-SettingsPath' $file
  Assert ([Convert]::ToBase64String([IO.File]::ReadAllBytes($file)) -eq [Convert]::ToBase64String($orig)) "${name}: pokeshell uninstall restores the file byte for byte"
}
$file = Join-Path $rs 'hk1\settings.json'
[IO.File]::WriteAllText($file, '{ "actions": [ { "command": "find", "id": "User.find" } ], "keybindings": [ { "id": "User.find", "keys": "Shift+Ctrl+B" } ] }', $utf8)
$before = [IO.File]::ReadAllBytes($file)
$out = Strip (Invoke-Cli (Join-Path $rs 'hk1') 'hotkey' 'on' '-SettingsPath' $file @{ POKESHELL_BINDER = $fakeExe })
Assert ($out -match 'already bound' -and [Convert]::ToBase64String([IO.File]::ReadAllBytes($file)) -eq [Convert]::ToBase64String($before)) "keys already taken (Shift+Ctrl+B = ctrl+shift+b): refused, file untouched"
$null = Invoke-Cli (Join-Path $rs 'hk1') 'hotkey' 'on' '-SettingsPath' $file '-Keys' 'ctrl+alt+b' @{ POKESHELL_BINDER = $fakeExe }
Assert ((Read-WtSettingsFile $file).text -match '"keys": "ctrl\+alt\+b"') "-Keys picks other keys"
$null = Invoke-Cli (Join-Path $rs 'hk1') 'hotkey' 'off'
Assert ([Convert]::ToBase64String([IO.File]::ReadAllBytes($file)) -eq [Convert]::ToBase64String($before)) "hotkey off: exactly as before"
$out = Strip (Invoke-Cli (Join-Path $rs 'hk2') 'hotkey' 'on' '-SettingsPath' (Join-Path $rs 'hk2\settings.json') @{ POKESHELL_BINDER = (Join-Path $rs 'missing.exe') })
Assert ($out -match "binder app isn't built") "no binder app: no hotkey"

Write-Host "9. the pokeshell:// handler (dry run only)" -ForegroundColor Cyan
$us = Join-Path $rs 'url'; [void][IO.Directory]::CreateDirectory($us)
$out = Strip (Invoke-Cli $us 'urlhandler' 'on' '-DryRun' @{ POKESHELL_BINDER = $fakeExe })
Assert ($out -match [regex]::Escape("would set $regKey [(default)] = URL:pokeshell binder") -and $out -match [regex]::Escape("would set $regKey [URL Protocol] = ")) "registers HKCU\Software\Classes\pokeshell as a URL protocol"
Assert ($out -match [regex]::Escape("would set $regKey\shell\open\command [(default)] = `"$fakeExe`" --root `"$RepoRoot`" --state `"$us`" --url `"%1`"")) "the open command runs the binder with --url `"%1`""
Assert (-not (Test-Path (Join-Path $us 'urlhandler.txt'))) "dry run: nothing recorded"
$out = Strip (Invoke-Cli $us 'urlhandler' 'off' '-DryRun')
Assert ($out -match [regex]::Escape("would remove $regKey")) "off removes the key"
$ops = @(Set-PokeshellUrlHandler -Exe 'C:\b\binder.exe' -Root 'C:\r' -StateDir 'C:\s' -DryRun -Key 'HKCU:\Software\Classes\pokeshell-test')
Assert ($ops.Count -eq 4 -and ($ops -join "`n") -match 'DefaultIcon') "Set-PokeshellUrlHandler -DryRun lists 4 operations"
Assert ((Test-Path $regKey) -eq $regBefore -and -not (Test-Path 'HKCU:\Software\Classes\pokeshell-test')) "the registry was not touched"

if ($real) { Assert ((Get-FileHash $real).Hash -eq $realHash) "the real Windows Terminal settings.json was not touched" }
Get-ChildItem ([IO.Path]::GetTempPath()) -Directory -Filter "pokeshell-test-*-$PID" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Host ''
if ($script:Failures) { Write-Host "earned: $script:Failures FAILED" -ForegroundColor Red; exit 1 }
Write-Host "earned: all passed" -ForegroundColor Green
