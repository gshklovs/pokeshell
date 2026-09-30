<#
The JSON commands for other tools (README "For other tools"): `pokeshell version --json` and
`pokeshell collection --json [--pack <id>]`, and the shipped gameplay data packs\pokemon\carddata.json
(tools\build_carddata.py): its coverage of pack.json, the tool's gap report, caught vs seen (the binders' rule, checked
against the web export when Python with Pillow is there), gameplay data for caught cards only, and the speed on a
1000-pull state. Runs the CLI of a fixture root (the scripts, pokemon's pack.json and carddata.json, fake art) against
throwaway state dirs. Never opens a tab or a window; never touches the real settings.json, $PROFILE or state.
  powershell -NoProfile -File tests\test-json.ps1
#>
. (Join-Path $PSScriptRoot '_setup.ps1')
$e = [char]27
$utf8 = [Text.UTF8Encoding]::new($false)
$carddata = Join-Path $RepoRoot 'packs\pokemon\carddata.json'
$pack = [IO.File]::ReadAllText((Join-Path $RepoRoot 'packs\pokemon\pack.json'), [Text.Encoding]::UTF8) | ConvertFrom-Json
$packIds = @($pack.cards.PSObject.Properties | ForEach-Object Name)
$py = @($env:POKESHELL_PYTHON, (Join-Path $RepoRoot '.venv\Scripts\python.exe'), (Join-Path (Split-Path $RepoRoot) 'pokeshell\.venv\Scripts\python.exe')) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
if (-not $py) { foreach ($c in 'python', 'py') { $g = Get-Command $c -ErrorAction SilentlyContinue; if ($g) { $py = $g.Source; break } } }

# the fixture root: every card of the real pack "built" (a one-cell .ans), so the binders' unbuilt-art rule doesn't
# depend on what is built locally; one card left unbuilt on purpose
$fx = Join-Path ([IO.Path]::GetTempPath()) "pokeshell-test-json-root-$PID"
Remove-Item $fx -Recurse -Force -ErrorAction SilentlyContinue
foreach ($d in 'packs\pokemon', 'dist\pokemon', 'tools\binder-web') { [void][IO.Directory]::CreateDirectory((Join-Path $fx $d)) }
Copy-Item -Recurse (Join-Path $RepoRoot 'scripts') $fx
Copy-Item (Join-Path $RepoRoot 'tools\binder_web.py'), (Join-Path $RepoRoot 'tools\build_carddata.py') (Join-Path $fx 'tools')
Copy-Item (Join-Path $RepoRoot 'tools\binder-web\index.html') (Join-Path $fx 'tools\binder-web')
Copy-Item (Join-Path $RepoRoot 'packs\pokemon\pack.json'), $carddata (Join-Path $fx 'packs\pokemon')
$fxArt = "$e[0;38;2;10;20;30m" + [char]0x2588 + [char]0x2588 + "$e[0m`n"
$unbuilt = 'swsh4-170'
foreach ($p in $pack.cards.PSObject.Properties) {
  if ($p.Name -eq $unbuilt) { continue }
  [IO.File]::WriteAllText((Join-Path $fx "dist\pokemon\$($p.Value.character)-$($p.Name).ans"), $fxArt, $utf8)
}
[IO.File]::WriteAllText((Join-Path $fx 'dist\pokemon\charizard-base1-4-shiny.ans'), $fxArt, $utf8)
$cli = Join-Path $fx 'scripts\pokeshell.ps1'

# stdout only (what another tool parses), with POKESHELL_HOME = the state; returns @{ out; code; ms }
function Invoke-Json {
  $State = $args[0]; $rest = @($args | Select-Object -Skip 1)
  $saved = $env:POKESHELL_HOME; $env:POKESHELL_HOME = $State
  try {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $o = & powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $cli @rest 2>$null
    $ms = $sw.ElapsedMilliseconds
    @{ out = (@($o) -join "`n"); code = $LASTEXITCODE; ms = $ms }
  } finally { $env:POKESHELL_HOME = $saved }
}
# python with its stderr as output, not an error (warnings are expected); $LASTEXITCODE is the tool's
function Invoke-Py {
  $ErrorActionPreference = 'Continue'
  & $py @args 2>&1 | ForEach-Object { "$_" } | Out-String -Width 400
}
function Parse([string]$s) { try { $s | ConvertFrom-Json } catch { $null } }

$now = [DateTime]::UtcNow; $boot = [Pokeshell.Core]::BootId()
function PullLine([int]$Ago, [string]$Card, [string]$Flags = '', [int]$Shiny = 0, [switch]$Id) {
  $c = $pack.cards.$Card
  $ch = if ($c) { $c.character } else { 'missingno' }; $tier = if ($c) { $c.tier } else { 'common' }
  $t = $now.AddMinutes(-$Ago)
  $line = "$($t.ToLocalTime().ToString('s'))`tpokemon`t$ch`t$tier`t$Card`t`t$Shiny`t$Flags"
  if ($Id) { $pid_ = [Pokeshell.Core]::NewPullId($t.Ticks); return @{ id = $pid_; line = "$line`tid=$pid_`tboot=$boot" } }
  @{ id = ''; line = $line }
}

Write-Host "1. version --json" -ForegroundColor Cyan
$vs = New-TestState 'json-version'
$r = Invoke-Json $vs 'version' '--json'
$v = Parse $r.out
Assert ($r.code -eq 0 -and $v) "version --json is one JSON document (exit $($r.code))"
$want = 'name', 'version', 'api', 'root', 'runtimeRoot', 'state', 'packaged', 'packs', 'carddata', 'commands', 'features'
$have = @($v.PSObject.Properties | ForEach-Object Name)
Assert (-not @($want | Where-Object { $have -notcontains $_ })) "has $($want -join ', ')"
Assert ($v.api -is [int] -and $v.api -ge 1 -and $v.version -eq 'source' -and $v.packaged -eq $false) "api $($v.api), version '$($v.version)', packaged false (a checkout)"
Assert ($v.root -eq $fx -and $v.state -eq $vs -and @($v.packs) -contains 'pokemon' -and @($v.carddata) -contains 'pokemon') "root, state, packs and carddata packs"
Assert (@($v.commands) -contains 'version --json' -and @($v.commands) -contains 'collection --json' -and @($v.features) -contains 'collection.data') "commands: $(@($v.commands) -join ', '); features: $(@($v.features) -join ', ')"

Write-Host "2. collection --json: caught vs seen (the binders' empty / seen / caught)" -ForegroundColor Cyan
$cs = New-TestState 'json-coll'
$pend = PullLine 30 'base1-2' 'pending' -Id                      # Blastoise: pending, its tab unused -> seen
$exp = PullLine 60 'base1-15' 'pending' -Id                      # Venusaur: expired:<id> -> seen
$both = PullLine 45 'swsh7-215' 'pending' -Id                    # Umbreon VMAX: pending, then earned -> caught
$both2 = PullLine 40 'swsh7-215' 'pending' -Id                   # ... and a second pull still pending: still caught
$lines = @(
  (PullLine 3000 'base1-4').line,                                # Charizard: earned (no id: before the earned rule)
  (PullLine 2000 'base1-4' '' 1).line,                           # ... again, shiny
  $pend.line, $exp.line, $both.line, $both2.line,
  "$($now.AddMinutes(-44).ToLocalTime().ToString('s'))`tearned:$($both.id)",
  "$($now.AddMinutes(-59).ToLocalTime().ToString('s'))`texpired:$($exp.id)",
  (PullLine 20 $unbuilt).line,                                   # a card whose art isn't built: hidden, as in the binders
  (PullLine 10 'zzz9-1').line                                    # not a card of the pack: hidden
)
[IO.File]::WriteAllLines((Join-Path $cs 'pulls.log'), [string[]]$lines, $utf8)
# a web export's image for Charizard (the art paths point at it when it exists)
$img = Join-Path $cs 'web\img\pokemon\charizard'; [void][IO.Directory]::CreateDirectory($img)
[IO.File]::WriteAllBytes((Join-Path $img 'base1-4.png'), [byte[]](137, 80, 78, 71))
$r = Invoke-Json $cs 'collection' '--json'
$j = Parse $r.out
Assert ($r.code -eq 0 -and $j) "collection --json is one JSON document (exit $($r.code), $($r.out.Length) chars)"
Assert (-not [regex]::IsMatch($r.out, '[^\x00-\x7f]')) "the output is ASCII only (\u escapes), so no code page can mangle it"
Assert ($j.api -ge 1 -and $j.state -eq $cs -and $null -ne $j.counts -and $j.cards -is [array] -and $j.seen -is [array]) "top level: api, state, counts, cards[], seen[]"
$ids = @($j.cards | ForEach-Object card); $seenIds = @($j.seen | ForEach-Object card)
Assert ((($ids | Sort-Object) -join ',') -eq 'base1-4,swsh7-215') "caught: Charizard (earned) and Umbreon VMAX (earned:<id>) ($($ids -join ', '))"
Assert ((($seenIds | Sort-Object) -join ',') -eq 'base1-15,base1-2') "seen: the pending and the expired pull, never in cards ($($seenIds -join ', '))"
Assert ($j.counts.caught -eq 2 -and $j.counts.seen -eq 2 -and $j.counts.pulls -eq 3 -and $j.counts.shiny -eq 1) "counts: caught 2, seen 2, 3 earned pulls, 1 shiny ($($j.counts | ConvertTo-Json -Compress))"
Assert ($ids -notcontains $unbuilt -and $seenIds -notcontains $unbuilt -and $ids -notcontains 'zzz9-1') "unbuilt and unknown cards are left out (as the binders do)"
$cz = $j.cards | Where-Object card -eq 'base1-4'
$fields = 'card', 'pack', 'character', 'name', 'set', 'setName', 'number', 'rarity', 'tier', 'tierLabel', 'count', 'shinyCount', 'shiny', 'caught', 'new', 'firstCaught', 'lastCaught', 'art', 'data'
$have = @($cz.PSObject.Properties | ForEach-Object Name)
Assert (-not @($fields | Where-Object { $have -notcontains $_ })) "a caught card has $($fields -join ', ')"
Assert ($cz.character -eq 'charizard' -and $cz.name -eq 'Charizard' -and $cz.set -eq 'base1' -and $cz.number -eq '4/102' -and $cz.rarity -eq 'Rare Holo' -and $cz.tier -eq 'rare-holo') "Charizard: character, name, set, number, rarity, tier ($($cz.set) $($cz.number) $($cz.rarity) / $($cz.tier))"
Assert ($cz.caught -eq $true -and $cz.count -eq 2 -and $cz.shinyCount -eq 1 -and $cz.shiny -eq $true) "counts: 2 caught, 1 shiny"
Assert ($cz.firstCaught -lt $cz.lastCaught -and $cz.firstCaught -match '^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d$') "first / last caught times ($($cz.firstCaught) .. $($cz.lastCaught))"
Assert ($cz.art.ans -eq (Join-Path $fx 'dist\pokemon\charizard-base1-4.ans') -and $cz.art.ansShiny -like '*charizard-base1-4-shiny.ans' -and (Test-Path $cz.art.ans)) "art: the .ans paths ($($cz.art.ans))"
Assert ($cz.art.png -eq (Join-Path $img 'base1-4.png') -and $cz.art.img -eq 'pokemon/charizard/base1-4.png' -and $null -eq $cz.art.pngShiny) "art: the web export's PNG, absolute and relative to web\img (none for the shiny: not exported)"
$um = $j.cards | Where-Object card -eq 'swsh7-215'
Assert ($um.count -eq 1 -and $null -eq $um.art.png -and $null -eq $um.art.ansShiny) "Umbreon VMAX: 1 caught (the still-pending pull doesn't count), no PNG exported"
$bl = $j.seen | Where-Object card -eq 'base1-2'; $vn = $j.seen | Where-Object card -eq 'base1-15'
Assert ($bl.caught -eq $false -and $bl.pending -eq $true -and $vn.pending -eq $false -and $bl.count -eq 1) "seen cards: caught false; pending while the tab can still catch it"
Assert (-not $bl.PSObject.Properties['data'] -and -not $bl.PSObject.Properties['art']) "seen cards carry no gameplay data and no art (the binder's rule: uncaught movesets stay hidden)"

Write-Host "3. gameplay data for a caught card: Base Set Charizard" -ForegroundColor Cyan
$d = $cz.data
Assert ($null -ne $d) "data is there"
Assert ($d.hp -eq 120 -and (@($d.types) -join ',') -eq 'Fire' -and (@($d.subtypes) -join ',') -eq 'Stage 2' -and $d.evolvesFrom -eq 'Charmeleon' -and $d.supertype -eq "Pok$([char]0xe9)mon") "hp 120, Fire, Stage 2, evolves from Charmeleon"
$fs = @($d.attacks)[0]
Assert (@($d.attacks).Count -eq 1 -and $fs.name -eq 'Fire Spin' -and (@($fs.cost) -join ',') -eq 'Fire,Fire,Fire,Fire' -and $fs.convertedEnergyCost -eq 4 -and $fs.damage -eq '100' -and $fs.text -like 'Discard 2 Energy*') "attack: Fire Spin, 4 Fire, 100, its text"
Assert (@($d.abilities)[0].name -eq 'Energy Burn' -and @($d.abilities)[0].type -eq "Pok$([char]0xe9)mon Power") "ability: Energy Burn (Pokemon Power)"
Assert (@($d.weaknesses)[0].type -eq 'Water' -and @($d.weaknesses)[0].value -eq "$([char]0xd7)2" -and @($d.resistances)[0].type -eq 'Fighting' -and @($d.resistances)[0].value -eq '-30') "weakness Water x2, resistance Fighting -30"
Assert (@($d.retreatCost).Count -eq 3 -and @($d.rules).Count -eq 0) "retreat cost 3, no rules"
Assert ($um.data.hp -eq 310 -and @($um.data.rules)[0] -like 'VMAX rule:*' -and (@($um.data.subtypes) -contains 'VMAX')) "Umbreon VMAX: hp 310 and its VMAX rule text"
$r2 = Invoke-Json $cs 'collection' '--json' '--pack' 'pokemon'
$r3 = Invoke-Json $cs 'collection' '--json' '--pack=pokemon'
Assert ($r2.code -eq 0 -and (Parse $r2.out).pack -eq 'pokemon' -and @((Parse $r2.out).cards).Count -eq 2 -and @((Parse $r3.out).cards).Count -eq 2) "--pack pokemon / --pack=pokemon: the same cards"
$r4 = Invoke-Json $cs 'collection' '--json' '--pack' 'nope'
Assert ($r4.code -ne 0 -and (Parse $r4.out).error -match "no pack 'nope'") "--pack nope: non-zero exit and {error} ($((Parse $r4.out).error))"
$es = New-TestState 'json-empty'
$r5 = Invoke-Json $es 'collection' '--json'
Assert ($r5.code -eq 0 -and @((Parse $r5.out).cards).Count -eq 0 -and (Parse $r5.out).counts.caught -eq 0) "no pulls yet: empty lists, exit 0"
if ($py) {
  # the web export (tools\binder_web.py) on the same state counts the same caught / seen cards
  $null = Invoke-Py (Join-Path $fx 'tools\binder_web.py') --root $fx --state $cs --out (Join-Path $cs 'webx') --no-art
  $wd = [IO.File]::ReadAllText((Join-Path $cs 'webx\data.json'), [Text.Encoding]::UTF8) | ConvertFrom-Json
  Assert ($wd.counts.caught -eq $j.counts.caught -and $wd.counts.seen -eq $j.counts.seen -and $wd.counts.pulls -eq $j.counts.pulls) "the web export agrees: caught $($wd.counts.caught), seen $($wd.counts.seen), pulls $($wd.counts.pulls)"
} else { Write-Host "  skip  no Python (the web export cross-check)" -ForegroundColor Yellow }

Write-Host "4. carddata.json: coverage and the tool's gap report" -ForegroundColor Cyan
$cdText = [IO.File]::ReadAllText($carddata, [Text.Encoding]::UTF8)
$cd = $cdText | ConvertFrom-Json
$cdIds = @($cd.cards.PSObject.Properties | ForEach-Object Name); $missing = @($cd.missing)
Assert ($cd.format -eq 'pokeshell-carddata/1' -and $cd.pack -eq 'pokemon') "format pokeshell-carddata/1"
$absent = @($packIds | Where-Object { $cdIds -notcontains $_ -and $missing -notcontains $_ })
Assert (-not $absent) "every pack.json card is in it, or listed as missing (no API data): $($cdIds.Count) of $($packIds.Count), missing $($missing.Count)$(if ($absent) { '; absent: ' + ($absent -join ' ') })"
Assert (-not @($cdIds | Where-Object { $packIds -notcontains $_ })) "only pack.json cards"
$keys = 'supertype', 'hp', 'types', 'subtypes', 'evolvesFrom', 'abilities', 'attacks', 'weaknesses', 'resistances', 'retreatCost', 'rules'
$bad = @($cd.cards.PSObject.Properties | Where-Object { $n = @($_.Value.PSObject.Properties | ForEach-Object Name); @($keys | Where-Object { $n -notcontains $_ }).Count -or $n.Count -ne $keys.Count })
Assert (-not $bad) "every entry has exactly the gameplay fields ($($keys -join ', '))"
Assert (@([IO.File]::ReadAllLines($carddata) | Where-Object { $_ -match '^"[^"]+":\{' }).Count -eq $cdIds.Count) "one card per line (a reader can pick lines without parsing the file)"
$kb = [math]::Round((Get-Item $carddata).Length / 1KB)
Assert ($kb -lt 1024) "size: $kb KB"
if ($py) {
  $o = Invoke-Py (Join-Path $RepoRoot 'tools\build_carddata.py') --check
  Assert ($LASTEXITCODE -eq 0 -and $o -match 'carddata: ok') "build_carddata.py --check: $($o.Trim())"
  # a fixture checkout with a card that has no data anywhere: --check names it, an offline build reports the gap
  $gx = Join-Path ([IO.Path]::GetTempPath()) "pokeshell-test-json-gap-$PID"
  Remove-Item $gx -Recurse -Force -ErrorAction SilentlyContinue
  [void][IO.Directory]::CreateDirectory((Join-Path $gx 'packs\pokemon'))
  Copy-Item $carddata (Join-Path $gx 'packs\pokemon')
  $pj = [IO.File]::ReadAllText((Join-Path $RepoRoot 'packs\pokemon\pack.json'), [Text.Encoding]::UTF8)
  $pj = $pj.Replace('"cards": {', "`"cards`": {`n    `"zzz9-1`": { `"character`": `"pikachu`", `"tier`": `"common`", `"name`": `"Pikachu`" },")
  [IO.File]::WriteAllText((Join-Path $gx 'packs\pokemon\pack.json'), $pj, $utf8)
  $o = Invoke-Py (Join-Path $RepoRoot 'tools\build_carddata.py') --root $gx --check
  Assert ($LASTEXITCODE -eq 1 -and $o -match 'not in carddata.json.*zzz9-1') "--check with a new pack.json card: exit 1, names it"
  $o = Invoke-Py (Join-Path $RepoRoot 'tools\build_carddata.py') --root $gx --lab (Join-Path $gx 'none') --offline
  $g = [IO.File]::ReadAllText((Join-Path $gx 'packs\pokemon\carddata.json'), [Text.Encoding]::UTF8) | ConvertFrom-Json
  Assert ($LASTEXITCODE -eq 2 -and $o -match 'GAPS.*zzz9-1' -and @($g.missing) -contains 'zzz9-1') "an offline build: exit 2, the gap printed and listed in missing ($(($o -split "`n" | Where-Object { $_ -match 'GAPS' }).Trim()))"
  Assert (@($g.cards.PSObject.Properties).Count -eq $cdIds.Count -and $g.cards.'base1-4'.hp -eq 120) "... every other card kept from the existing file (incremental: a new set only needs its own data)"
  $o = Invoke-Py (Join-Path $RepoRoot 'tools\build_carddata.py') --root $gx --check
  Assert ($LASTEXITCODE -eq 0 -and $o -match 'no API data for 1: zzz9-1') "--check then passes and reports the gap: $($o.Trim())"
  Remove-Item $gx -Recurse -Force -ErrorAction SilentlyContinue
} else { Write-Host "  skip  no Python (tools\build_carddata.py)" -ForegroundColor Yellow }

Write-Host "5. speed: collection --json on a 1000-pull state" -ForegroundColor Cyan
$ss = New-TestState 'json-speed'
$rng = [Random]::new(7); $big = [Collections.Generic.List[string]]::new()
for ($i = 0; $i -lt 1000; $i++) {
  $cid = $packIds[$rng.Next($packIds.Count)]
  if ($cid -eq $unbuilt) { $cid = 'base1-4' }
  if ($i % 5 -eq 0) { $big.Add((PullLine (1000 - $i) $cid 'pending' -Id).line) }   # a fifth still pending (seen)
  else { $big.Add((PullLine (100000 - $i * 60) $cid '' ($(if ($i % 50 -eq 0) { 1 } else { 0 }))).line) }
}
[IO.File]::WriteAllLines((Join-Path $ss 'pulls.log'), [string[]]$big, $utf8)
$w = Invoke-Json $ss 'collection' '--json'   # the first run compiles the core into the state dir (install does that)
$times = @(1..3 | ForEach-Object { (Invoke-Json $ss 'collection' '--json').ms })
$jb = Parse $w.out
$best = ($times | Measure-Object -Minimum).Minimum
Assert ($w.code -eq 0 -and $jb -and $jb.counts.pulls -eq 800) "1000 pulls: $($jb.counts.caught) caught cards (800 pulls), $($jb.counts.seen) seen"
if ($py) {
  $null = Invoke-Py (Join-Path $fx 'tools\binder_web.py') --root $fx --state $ss --out (Join-Path $ss 'webx') --no-art
  $wd = [IO.File]::ReadAllText((Join-Path $ss 'webx\data.json'), [Text.Encoding]::UTF8) | ConvertFrom-Json
  Assert ($wd.counts.caught -eq $jb.counts.caught -and $wd.counts.seen -eq $jb.counts.seen -and $wd.counts.pulls -eq $jb.counts.pulls) "the web export agrees on the 1000 pulls: caught $($wd.counts.caught), seen $($wd.counts.seen), pulls $($wd.counts.pulls)"
}
Assert ($best -lt 1500) "collection --json: $best ms (runs: $($times -join ', ') ms; whole process, PowerShell start included; limit 1500)"

Remove-Item $fx -Recurse -Force -ErrorAction SilentlyContinue
foreach ($s in $vs, $cs, $es, $ss) { Remove-Item $s -Recurse -Force -ErrorAction SilentlyContinue }
Write-Host ''
if ($script:Failures) { Write-Host "$script:Failures FAILED" -ForegroundColor Red; exit 1 }
Write-Host 'test-json: all passed' -ForegroundColor Green
