<#
Real booster packs (packs\pokemon\boosters.json, scripts\lib\booster.ps1 + Booster.cs, docs\BOOSTERS.md):
  1. the data: every set's slots add up, every outcome matches printed cards, fully served outcomes roll at their
     published rate and unserved shares go to the slot's base
  2. the structure: seeded packs of every openable set respect their slots (counts, rarities, sets, distinct cards,
     reveal order rarest last)
  3. a Monte Carlo of 20,000 packs per set matches the configured odds (4.5 sigma), plus 20,000 with the CSPRNG
  4. `pokeshell pack open --json`: the contract, every card recorded in pulls.log as a caught pull, NEW only once
  5. the token ledger: grant, spend, no tokens, --free, and concurrent opens never double-spend
  6. uncaught -> caught in the binder data (tools\binder_web.py --no-art), when Python with Pillow is around
Isolated: a temp checkout copy (the real pack.json + boosters.json, stub art for every card), POKESHELL_HOME in %TEMP%,
POKESHELL_REAL_WT=off. Never touches %LOCALAPPDATA%\pokeshell, settings.json or $PROFILE; never opens a tab.
  powershell -NoProfile -File tests\test-boosters.ps1
#>
. (Join-Path $PSScriptRoot '_setup.ps1')
. (Join-Path $RepoRoot 'scripts\lib\booster.ps1')
$env:POKESHELL_REAL_WT = 'off'
$utf8 = [Text.UTF8Encoding]::new($false)

# a checkout copy: scripts, tools, the real pack.json + boosters.json, and a stub .ans (and -shiny.ans) for every card
$fx = Join-Path ([IO.Path]::GetTempPath()) "pokeshell-test-boosters-$PID"
Remove-Item $fx -Recurse -Force -ErrorAction SilentlyContinue
foreach ($d in 'packs\pokemon', 'dist\pokemon', 'tools', 'state') { [void][IO.Directory]::CreateDirectory((Join-Path $fx $d)) }
Copy-Item (Join-Path $RepoRoot 'scripts') $fx -Recurse
Copy-Item (Join-Path $RepoRoot 'tools\binder_web.py') (Join-Path $fx 'tools')
Copy-Item (Join-Path $RepoRoot 'tools\binder-web') (Join-Path $fx 'tools') -Recurse
foreach ($f in 'pack.json', 'boosters.json') { Copy-Item (Join-Path $RepoRoot "packs\pokemon\$f") (Join-Path $fx "packs\pokemon\$f") }
$e = [char]27
$art = "$e[0;38;2;10;20;30m" + [char]0x2580 + "$e[0m`n"
$pack = Read-PokeshellPack $fx 'pokemon'
foreach ($c in $pack.cardList) {
  [IO.File]::WriteAllText((Join-Path $fx "dist\pokemon\$($c.character)-$($c.id).ans"), $art, $utf8)
  [IO.File]::WriteAllText((Join-Path $fx "dist\pokemon\$($c.character)-$($c.id)-shiny.ans"), $art, $utf8)
}
$st = Join-Path $fx 'state'
$cli = Join-Path $fx 'scripts\pokeshell.ps1'
Import-PokeshellBooster $st
$boosters = Read-PokeshellBoosters $fx 'pokemon'
$sets = @($boosters.sets)
$models = @{}; foreach ($s in $sets) { $models[$s.id] = Get-PokeshellBoosterModel $fx $pack $s }
$open = @($sets | Where-Object { $models[$_.id].cards.Count -gt 0 })

function Invoke-Cli {
  $state = $args[0]; $rest = @($args | Select-Object -Skip 1)
  $saved = $env:POKESHELL_HOME; $env:POKESHELL_HOME = $state
  $ErrorActionPreference = 'Continue'
  try { $o = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $cli @rest 2>&1 | ForEach-Object { "$_" }; $script:LastExit = $LASTEXITCODE; ($o -join "`n") }
  finally { $env:POKESHELL_HOME = $saved }
}

Write-Host "1. the data: slots, printed counts, rates" -ForegroundColor Cyan
Assert ($sets.Count -ge 8) "boosters.json has the $($sets.Count) sets"
$bad = @()
foreach ($s in $sets) {
  foreach ($sl in @($s.slots)) {
    $sum = 0.0; foreach ($p in @($sl.pick)) { $sum += [double]$(if ($null -ne $p.rate) { $p.rate } else { 1 }) }
    if ([math]::Abs($sum - 1) -gt 0.00005) { $bad += "$($s.id)/$($sl.id) rates add up to $sum" }
    if (@($sl.pick | Where-Object base).Count -ne 1) { $bad += "$($s.id)/$($sl.id) needs one base outcome" }
    foreach ($p in @($sl.pick)) { if (-not $p.printed) { $bad += "$($s.id)/$($sl.id)/$($p.label) has no printed count" } }
  }
  if (-not $s.art.hero -or -not $pack.cardIndex[$s.art.hero] -and $models[$s.id].cards.Count) { $bad += "$($s.id): hero card $($s.art.hero) isn't in pack.json" }
}
Assert (-not $bad) "every slot's rates add up to 1, has one base, every outcome a printed count$(if ($bad) { ': ' + ($bad -join '; ') })"
$bad = @()
foreach ($s in $open) {
  $m = $models[$s.id]
  for ($i = 0; $i -lt $m.slots.Count; $i++) {
    $sl = $m.slots[$i]; $missing = 0.0; $baseP = 0.0
    for ($o = 0; $o -lt $sl.Outcomes.Count; $o++) {
      $om = $m.meta[$i][$o]; $p = $sl.Probability($o)
      if ($om.base) { $baseP = $p; continue }
      $share = if ($om.printed) { [math]::Min(1.0, $om.served / $om.printed) } else { 1 }
      if ([math]::Abs($p - $om.rate * $share) -gt 1e-9) { $bad += "$($s.id)/$($sl.Id)/$($om.label): rolls $p, not rate x served/printed = $($om.rate * $share)" }
      $missing += $om.rate * (1 - $share)
    }
    $bm = @($m.meta[$i] | Where-Object base)[0]
    if ($bm -and $bm.served -and [math]::Abs($baseP - ($bm.rate + $missing)) -gt 1e-9) { $bad += "$($s.id)/$($sl.Id): the base rolls $baseP, not $($bm.rate + $missing)" }
  }
}
Assert (-not $bad) "each served card keeps its published per-pack odds; the unserved share goes to the base$(if ($bad) { ': ' + ($bad -join '; ') })"
$evs = $models['swsh7']
$gold = @(for ($o = 0; $o -lt $evs.slots[3].Outcomes.Count; $o++) { if ($evs.meta[3][$o].label -eq 'gold') { $evs.slots[3].Probability($o) } })[0]
Assert ([math]::Abs($gold - 0.0091 * 3 / 12) -lt 1e-9) "Evolving Skies gold: 0.91% a pack x 3 of 12 printed golds served = $([math]::Round(100 * $gold, 3))%"
Assert ($models['swsh11'].cards.Count -gt 150) "Lost Origin + Trainer Gallery can be opened ($($models['swsh11'].cards.Count) served cards)"

Write-Host "2. the structure: 200 seeded packs of each openable set" -ForegroundColor Cyan
foreach ($s in $open) {
  $m = $models[$s.id]; $rng = [Pokeshell.BoosterRng]::new(42); $bad = @()
  $size = 0; foreach ($sl in $m.slots) { if (@($sl.Outcomes | Where-Object { $_.Pool.Length -gt 0 -and $_.Weight -gt 0 }).Count) { $size += $sl.Count } }
  for ($n = 0; $n -lt 200; $n++) {
    $picks = [Pokeshell.Booster]::Roll($m.slots, $rng)
    if ($picks.Count -ne $size) { $bad += "pack $n has $($picks.Count) cards, not $size"; continue }
    for ($i = 0; $i -lt $m.slots.Count; $i++) {
      $mine = @($picks | Where-Object Slot -eq $i)
      if ($mine.Count -and $mine.Count -ne $m.slots[$i].Count) { $bad += "pack $n slot $($m.slots[$i].Id): $($mine.Count) cards" }
      if (@($mine.Card | Select-Object -Unique).Count -ne $mine.Count) { $bad += "pack $n slot $($m.slots[$i].Id): a card twice" }
      foreach ($p in $mine) {
        $c = $m.cards[$p.Card]; $spec = @($s.slots)[$i].pick[$p.Outcome]
        if (-not (Test-PokeshellCardMatch $c $spec @($s.cardSets))) { $bad += "pack $n slot $($m.slots[$i].Id): $($c.id) ($($c.rarity)) isn't a '$($spec.label)'" }
        if (@($s.cardSets) -notcontains (Get-PokeshellCardSet $c.id)) { $bad += "$($c.id) isn't from $($s.name)" }
      }
    }
  }
  $slotsDesc = (@($s.slots) | ForEach-Object { "$(if ($_.count -gt 1) { "$($_.count) " })$($_.id)" }) -join ' + '
  Assert (-not $bad) "$($s.name): $size cards a pack ($slotsDesc), every card from its slot's pool, none twice in a slot$(if ($bad) { ': ' + (($bad | Select-Object -First 4) -join '; ') })"
}
$bad = @()
foreach ($s in $open) {
  for ($n = 0; $n -lt 30; $n++) {
    $r = Open-PokeshellBooster $fx $st $pack $s ([Pokeshell.BoosterRng]::new(1000 + $n)) -NoRecord
    $h = @($r.cards | ForEach-Object { $_.hit + $(if ($_.shiny) { 0.5 } else { 0 }) })
    for ($i = 1; $i -lt $h.Count; $i++) { if ($h[$i] -lt $h[$i - 1]) { $bad += "$($s.id) pack $n"; break } }
  }
}
Assert (-not $bad) "the reveal order puts the rarest last (30 packs a set)$(if ($bad) { ': ' + ($bad -join ', ') })"
Assert ((Get-Content (Join-Path $st 'pulls.log') -ErrorAction SilentlyContinue).Count -eq 0) "-NoRecord rolls don't touch pulls.log"
$a = (Open-PokeshellBooster $fx $st $pack $sets[0] ([Pokeshell.BoosterRng]::new(5)) -NoRecord).cards.id -join ','
$b = (Open-PokeshellBooster $fx $st $pack $sets[0] ([Pokeshell.BoosterRng]::new(5)) -NoRecord).cards.id -join ','
Assert ($a -eq $b) "a seeded pack is reproducible"

Write-Host "3. Monte Carlo: 20,000 packs per set against the configured odds" -ForegroundColor Cyan
$script:McRows = @()
function Test-MonteCarlo($s, $m, $rng, [int]$N, [string]$Tag) {
  $sw = [Diagnostics.Stopwatch]::StartNew()
  $cnt = [Pokeshell.Booster]::Simulate($m.slots, $N, $rng)
  $sw.Stop()
  $worst = 0.0; $bad = @()
  for ($i = 0; $i -lt $m.slots.Count; $i++) {
    $sl = $m.slots[$i]; $draws = [double]$N * $sl.Count
    for ($o = 0; $o -lt $sl.Outcomes.Count; $o++) {
      $p = $sl.Probability($o); $k = [double]$(if ($cnt.ContainsKey("$i/$o")) { $cnt["$i/$o"] } else { 0 })
      $f = $k / $draws
      $sd = [math]::Sqrt([math]::Max($p * (1 - $p), 1e-12) / $draws)
      $z = if ($p -gt 0 -and $p -lt 1) { [math]::Abs($f - $p) / $sd } elseif ($f -eq $p) { 0 } else { 99 }
      if ($z -gt $worst) { $worst = $z }
      if ($z -gt 4.5) { $bad += "$($sl.Id)/$($m.meta[$i][$o].label): $([math]::Round(100 * $f, 3))% vs $([math]::Round(100 * $p, 3))% (z $([math]::Round($z, 1)))" }
      if ($p -lt 1 -and $p -gt 0) { $script:McRows += [pscustomobject]@{ run = $Tag; set = $s.id; slot = $sl.Id; outcome = $m.meta[$i][$o].label; expected = $p; observed = $f; z = [math]::Round($z, 2) } }
    }
  }
  Assert (-not $bad) ("{0} ({1}): {2:N0} packs in {3} ms, every outcome within 4.5 sigma (worst {4:0.00} sigma){5}" -f $s.name, $Tag, $N, $sw.ElapsedMilliseconds, $worst, $(if ($bad) { ': ' + ($bad -join '; ') }))
}
foreach ($s in $open) { Test-MonteCarlo $s $models[$s.id] ([Pokeshell.BoosterRng]::new(20260929)) 20000 'seeded' }
Test-MonteCarlo $sets[0] $models[$sets[0].id] ([Pokeshell.BoosterRng]::new()) 20000 'CSPRNG'
$mcOut = Join-Path ([IO.Path]::GetTempPath()) 'pokeshell-booster-montecarlo.tsv'
$script:McRows | ForEach-Object { "{0}`t{1}`t{2}`t{3}`t{4:0.000000}`t{5:0.000000}`t{6}" -f $_.run, $_.set, $_.slot, $_.outcome, $_.expected, $_.observed, $_.z } | Set-Content -Encoding UTF8 $mcOut
Write-Host "        (every outcome's expected vs observed: $mcOut)" -ForegroundColor DarkGray

Write-Host "4. pokeshell pack open --json: the contract and the pulls it records" -ForegroundColor Cyan
$s1 = Join-Path $fx 's1'; [void][IO.Directory]::CreateDirectory($s1)
$out = Invoke-Cli $s1 'pack' 'open' 'evolving' '--json' '--free' '--seed' '11'
$j = try { $out | ConvertFrom-Json } catch { $null }
Assert ($j -and $j.set -eq 'swsh7' -and $j.packId -match '^[0-9A-Z]{26}$' -and @($j.cards).Count -eq 10) "open evolving --json: { set, packId, cards } with 10 cards$(if (-not $j) { ": $out" })"
$keys = 'id', 'name', 'rarity', 'tier', 'slot', 'shiny', 'isNew', 'image'
$missing = @(foreach ($c in @($j.cards)) { foreach ($k in $keys) { if (-not $c.PSObject.Properties[$k]) { "$($c.id).$k" } } })
Assert (-not $missing) "every card has id, name, rarity, tier, slot, shiny, isNew, image$(if ($missing) { ': missing ' + ($missing -join ', ') })"
Assert (@($j.cards | Where-Object { $_.image -ne "img/pokemon/$($_.character)/$($_.id)$(if ($_.shiny) { '-shiny' }).png" }).Count -eq 0) "image is the web export's path (img/pokemon/<character>/<card id>[-shiny].png)"
Assert (@($j.cards | Where-Object isNew).Count -eq @($j.cards.id | Select-Object -Unique).Count) "a first pack: every distinct card is NEW"
$log = @(Get-Content (Join-Path $s1 'pulls.log') -Encoding UTF8)
$logged = @($log | ForEach-Object { $_.Split("`t")[4] })
Assert ($log.Count -eq 10 -and (($logged -join ',') -eq (@($j.cards.id) -join ','))) "all 10 cards logged to pulls.log, in reveal order"
Assert (-not ($log -match 'pending') -and @($log | Where-Object { $_ -match "`tbooster:swsh7`t" -and $_ -match "`tbooster=$($j.packId)" }).Count -eq 10) "logged caught (no pending flag), tagged booster:swsh7 and the pack id"
$recs = @([Pokeshell.Core]::ReadPulls($s1, [DateTime]::UtcNow.Ticks, [Pokeshell.Core]::BootId()))
Assert ($recs.Count -eq 10 -and -not @($recs | Where-Object Status -ne 'earned')) "the core reads them as 10 earned (caught) pulls"
$j2 = (Invoke-Cli $s1 'pack' 'open' 'swsh7' '--json' '--free' '--seed' '11') | ConvertFrom-Json
Assert ((@($j2.cards.id) -join ',') -eq (@($j.cards.id) -join ',') -and -not @($j2.cards | Where-Object isNew)) "the same pack again: nothing is NEW any more"
$txt = Invoke-Cli $s1 'pack' 'open' 'base' '--free'
Assert ($txt -match 'Base Set booster' -and $txt -match 'in this pack' -and ([regex]::Matches($txt, [string][char]0x2580)).Count -ge 9) "open base in a terminal: every card rendered, then the summary"
$err = (Invoke-Cli $s1 'pack' 'open' 'nosuchset' '--json' '--free') | ConvertFrom-Json
Assert ($script:LastExit -eq 1 -and $err.error -match 'no booster') "an unknown set: a JSON error, exit 1"
$v = (Invoke-Cli $s1 'version' '--json') | ConvertFrom-Json
Assert (@('pack sets --json', 'pack odds --json', 'pack open --json', 'pack grant --json', 'pack tokens --json' | Where-Object { @($v.commands) -notcontains $_ }).Count -eq 0) "version --json lists the pack commands"
$ls = (Invoke-Cli $s1 'pack' 'sets' '--json') | ConvertFrom-Json
Assert (@($ls.sets).Count -eq $sets.Count -and ($ls.sets | Where-Object id -eq 'swsh7').cards -eq 193 -and ($ls.sets | Where-Object id -eq 'swsh11').openable -and ($ls.sets | Where-Object id -eq 'swsh7').hero -like 'img/pokemon/*') "pack sets --json: every set, card counts, openable, art hints"

Write-Host "5. pack tokens" -ForegroundColor Cyan
$s2 = Join-Path $fx 's2'; [void][IO.Directory]::CreateDirectory($s2)
$none = (Invoke-Cli $s2 'pack' 'open' 'swsh7' '--json') | ConvertFrom-Json
Assert ($script:LastExit -eq 1 -and $none.code -eq 'no-tokens' -and -not (Test-Path (Join-Path $s2 'pulls.log'))) "no tokens: refused (code no-tokens, exit 1), nothing recorded"
$g = (Invoke-Cli $s2 'pack' 'grant' '3' '--reason' 'won a battle' '--json') | ConvertFrom-Json
Assert ($g.granted -eq 3 -and $g.balance -eq 3 -and $g.reason -eq 'won a battle') "grant 3 --reason: balance 3"
$o1 = (Invoke-Cli $s2 'pack' 'open' 'swsh7' '--json') | ConvertFrom-Json
Assert ($o1.spent -eq 1 -and $o1.tokens -eq 2) "open spends one (2 left)"
$o2 = (Invoke-Cli $s2 'pack' 'open' 'swsh7' '--json' '--free') | ConvertFrom-Json
Assert ($o2.spent -eq 0 -and $o2.tokens -eq 2) "--free spends none"
# 4 opens at once for 2 tokens: exactly 2 win
$ps = @(1..4 | ForEach-Object {
  $psi = [Diagnostics.ProcessStartInfo]::new('powershell.exe', "-NoProfile -ExecutionPolicy Bypass -File `"$cli`" pack open swsh7 --json")
  $psi.UseShellExecute = $false; $psi.RedirectStandardOutput = $true; $psi.CreateNoWindow = $true
  $psi.EnvironmentVariables['POKESHELL_HOME'] = $s2
  [Diagnostics.Process]::Start($psi) })
$res = @($ps | ForEach-Object { $o = $_.StandardOutput.ReadToEnd(); $_.WaitForExit(); try { $o | ConvertFrom-Json } catch { $null } })
$won = @($res | Where-Object { $_.spent -eq 1 }).Count; $lost = @($res | Where-Object { $_.code -eq 'no-tokens' }).Count
$t = (Invoke-Cli $s2 'pack' 'tokens' '--json') | ConvertFrom-Json
Assert ($won -eq 2 -and $lost -eq 2 -and $t.balance -eq 0) "4 concurrent opens for 2 tokens: $won opened, $lost refused, balance $($t.balance)"
$lines = @(Get-Content (Join-Path $s2 'tokens.log'))
Assert ($lines.Count -eq 4 -and $lines[0] -match "`t\+3`twon a battle`tid=" -and @($lines | Where-Object { $_ -match "`t-1`topened swsh7`tid=.*`tset=swsh7`tpack=" }).Count -eq 3) "tokens.log: +3 then three -1 lines with the set and pack id"
$bad = Invoke-Cli $s2 'pack' 'grant' 'x' '--json'
Assert ($script:LastExit -eq 1 -and ($bad | ConvertFrom-Json).error -match 'usage') "grant needs a count"

Write-Host "6. uncaught -> caught in the binder data" -ForegroundColor Cyan
$py = @($env:POKESHELL_PYTHON, (Join-Path $RepoRoot '.venv\Scripts\python.exe'), (Join-Path (Split-Path $RepoRoot) 'pokeshell\.venv\Scripts\python.exe'), 'python') |
  Where-Object { $_ -and ((Test-Path $_) -or (Get-Command $_ -ErrorAction SilentlyContinue)) } |
  Where-Object { & $_ -c 'import PIL' 2>$null; $LASTEXITCODE -eq 0 } | Select-Object -First 1
if ($py) {
  $s3 = Join-Path $fx 's3'; [void][IO.Directory]::CreateDirectory($s3)
  function Get-BinderData { $ErrorActionPreference = 'Continue'; & $py (Join-Path $fx 'tools\binder_web.py') --root $fx --state $s3 --out (Join-Path $s3 'web') --no-art 2>&1 | Out-Null
                            [IO.File]::ReadAllText((Join-Path $s3 'web\data.json'), [Text.Encoding]::UTF8) | ConvertFrom-Json }
  $before = Get-BinderData
  $r = (Invoke-Cli $s3 'pack' 'open' 'swsh9' '--json' '--free' '--seed' '3') | ConvertFrom-Json
  $after = Get-BinderData
  $ids = @($r.cards.id | Select-Object -Unique)
  $caught = @($after.pulls | Where-Object { $_.status -eq 'collected' } | ForEach-Object card)
  Assert ($before.counts.caught -eq 0 -and $after.counts.caught -eq $ids.Count) "binder data: caught 0 -> $($after.counts.caught) ($($ids.Count) distinct cards in the pack)"
  Assert (-not @($ids | Where-Object { $caught -notcontains $_ })) "every card of the pack is a caught pull in the binder"
  $saved = $env:POKESHELL_PYTHON; $env:POKESHELL_PYTHON = $py
  $x = (Invoke-Cli $s3 'pack' 'open' 'swsh11' '--json' '--free' '--export') | ConvertFrom-Json
  $env:POKESHELL_PYTHON = $saved
  Assert ($x.exported -eq $true -and -not @($x.cards | Where-Object { -not $_.png -or -not (Test-Path $_.png) })) "--export: the web export is rebuilt, every card's png exists (the stub art's pixel)"
} else { Write-Host "  skip  no Python with Pillow (set POKESHELL_PYTHON)" -ForegroundColor Yellow }

Remove-Item $fx -Recurse -Force -ErrorAction SilentlyContinue
if ($script:Failures) { Write-Host "`n$script:Failures FAILED" -ForegroundColor Red; exit 1 }
Write-Host "`nall booster tests passed" -ForegroundColor Green
