<#
Real booster packs (packs\pokemon\boosters.json, scripts\lib\booster.ps1 + Booster.cs, docs\BOOSTERS.md):
  1. the data: every set's slots add up, every outcome matches printed cards, fully served outcomes roll at their
     published rate and unserved shares go to the slot's base
  2. the structure: seeded packs of every openable set respect their slots (counts, rarities, sets, distinct cards,
     reveal order rarest last)
  3. a Monte Carlo of 20,000 packs per set matches the configured odds (4.5 sigma), plus 20,000 with the CSPRNG
  4. `pokeshell pack open --json`: the contract, every card recorded in pulls.log as a caught pull, NEW only once
  5. the token ledger: grant, spend, no tokens, --free, and concurrent opens never double-spend
  6. uncaught -> caught in the binder data (the web export, binder.exe --export-web --no-art), when the binder is built
  7. random packs: the set chances (price ^ -k), a Monte Carlo of the set choice, --seed, one token per open
  8. the booster index (<state>\booster-index-pokemon.tsv): reused, rebuilt when the data or the art changes
  9. the incremental export (--only), the art cache across root paths and old absolute stamps, a lenient timing check
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
$badOdds = @($ls.sets | Where-Object { $_.openable -and [math]::Abs((@($_.odds) | Measure-Object weight -Sum).Sum - $_.packSize) -gt 0.001 })
Assert (-not $badOdds) "pack sets --json odds: the expected cards per tier add up to the pack size$(if ($badOdds) { ': ' + ($badOdds.id -join ', ') })"

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
$bexe = Join-Path $RepoRoot 'binder\target\release\binder.exe'
if (Test-Path $bexe) {
  $s3 = Join-Path $fx 's3'; [void][IO.Directory]::CreateDirectory($s3)
  function Get-BinderData { $ErrorActionPreference = 'Continue'; & $bexe --export-web (Join-Path $s3 'web') --root $fx --state $s3 --no-art 2>&1 | Out-Null
                            [IO.File]::ReadAllText((Join-Path $s3 'web\data.json'), [Text.Encoding]::UTF8) | ConvertFrom-Json }
  $before = Get-BinderData
  $r = (Invoke-Cli $s3 'pack' 'open' 'swsh9' '--json' '--free' '--seed' '3') | ConvertFrom-Json
  $after = Get-BinderData
  $ids = @($r.cards.id | Select-Object -Unique)
  $caught = @($after.pulls | Where-Object { $_.status -eq 'collected' } | ForEach-Object card)
  Assert ($before.counts.caught -eq 0 -and $after.counts.caught -eq $ids.Count) "binder data: caught 0 -> $($after.counts.caught) ($($ids.Count) distinct cards in the pack)"
  Assert (-not @($ids | Where-Object { $caught -notcontains $_ })) "every card of the pack is a caught pull in the binder"
  $saved = $env:POKESHELL_BINDER; $env:POKESHELL_BINDER = $bexe   # (the fixture root has no bin\binder.exe)
  $x = (Invoke-Cli $s3 'pack' 'open' 'swsh11' '--json' '--free' '--export') | ConvertFrom-Json
  $env:POKESHELL_BINDER = $saved
  Assert ($x.exported -eq $true -and -not @($x.cards | Where-Object { -not $_.png -or -not (Test-Path $_.png) })) "--export: the web export is rebuilt, every card's png exists (the stub art's pixel)"
} else { Write-Host "  skip  binder.exe not built (binder\build.ps1)" -ForegroundColor Yellow }

Write-Host "7. random packs, weighted by pack price" -ForegroundColor Cyan
$k = [double]$boosters.priceExponent
$noPrice = @($sets | Where-Object { -not ($_.price -gt 0) -or -not $_.priceSource.url -or -not $_.priceSource.date })
Assert ($k -gt 0 -and -not $noPrice) "boosters.json: priceExponent $k, every set has a price and a priceSource (url, date)$(if ($noPrice) { ': missing ' + ($noPrice.id -join ', ') })"
$idx = Get-PokeshellBoosterIndex $fx $st -Pack $pack -Boosters $boosters
$ch = $idx.SetChances()
$w = @{}; $tw = 0.0; foreach ($s in $open) { if ($s.price -gt 0) { $w[$s.id] = [math]::Pow([double]$s.price, -$k); $tw += $w[$s.id] } }
$bad = @(for ($i = 0; $i -lt $idx.Sets.Count; $i++) { $id = $idx.Sets[$i].Id; $want = if ($w.ContainsKey($id)) { $w[$id] / $tw } else { 0 }; if ([math]::Abs($ch[$i] - $want) -gt 1e-12) { "$id $($ch[$i]) vs $want" } })
Assert (-not $bad -and [math]::Abs(($ch | Measure-Object -Sum).Sum - 1) -lt 1e-9) "each set's chance is price^-$k over the openable sets, summing to 1$(if ($bad) { ': ' + ($bad -join '; ') })"
$oneIn = @{}; for ($i = 0; $i -lt $idx.Sets.Count; $i++) { if ($ch[$i] -gt 0) { $oneIn[$idx.Sets[$i].Id] = 1 / $ch[$i] } }
$vintage = @('base1', 'neo1' | Where-Object { $oneIn[$_] })
$modern = @($oneIn.Keys | Where-Object { $vintage -notcontains $_ })
Assert ($vintage.Count -eq 2 -and -not @($vintage | Where-Object { $oneIn[$_] -lt 30 -or $oneIn[$_] -gt 100 })) "vintage packs are rare, not impossible: $(($vintage | ForEach-Object { "$_ 1 in $([math]::Round($oneIn[$_], 1))" }) -join ', ') (30-100)"
Assert (-not @($modern | Where-Object { $oneIn[$_] -gt 15 })) "modern packs are common: $(($modern | Sort-Object { $oneIn[$_] } | ForEach-Object { "$_ 1 in $([math]::Round($oneIn[$_], 1))" }) -join ', ')"
# Monte Carlo of the set choice: 200,000 seeded draws, then 50,000 from the CSPRNG
foreach ($run in @(@{ tag = 'seeded'; rng = [Pokeshell.BoosterRng]::new(20260929); n = 200000 }, @{ tag = 'CSPRNG'; rng = [Pokeshell.BoosterRng]::new(); n = 50000 })) {
  $cnt = [Pokeshell.Booster]::SimulateSets($idx, $run.n, $run.rng); $worst = 0.0; $bad = @()
  for ($i = 0; $i -lt $idx.Sets.Count; $i++) {
    $p = $ch[$i]; $f = $cnt[$i] / $run.n
    $z = if ($p -gt 0) { [math]::Abs($f - $p) / [math]::Sqrt($p * (1 - $p) / $run.n) } elseif ($cnt[$i] -eq 0) { 0 } else { 99 }
    if ($z -gt $worst) { $worst = $z }; if ($z -gt 4.5) { $bad += "$($idx.Sets[$i].Id) $f vs $p (z $([math]::Round($z, 1)))" }
  }
  Assert (-not $bad) ("set choice ({0}): {1:N0} draws match the chances within 4.5 sigma (worst {2:0.00}){3}" -f $run.tag, $run.n, $worst, $(if ($bad) { ': ' + ($bad -join '; ') }))
}
$s4 = Join-Path $fx 's4'; [void][IO.Directory]::CreateDirectory($s4)
$r1 = (Invoke-Cli $s4 'pack' 'open' 'random' '--json' '--free' '--seed' '77') | ConvertFrom-Json
$r2 = (Invoke-Cli $s4 'pack' 'open' '--random' '--json' '--free' '--seed' '77') | ConvertFrom-Json
$si = [array]::IndexOf([string[]]@($idx.Sets | ForEach-Object Id), [string]$r1.set)
Assert ($r1.random -eq $true -and $r1.set -and $r1.setName -eq $idx.Sets[$si].Name -and [math]::Abs($r1.setChance - $ch[$si]) -lt 1e-6 -and $r1.setOneIn -eq [math]::Round(1 / $ch[$si], 1) -and $r1.setPrice -gt 0) "open random --json: { set, setName, setChance, setOneIn, setPrice, random } ($($r1.setName), 1 in $($r1.setOneIn))"
Assert ($r2.set -eq $r1.set -and (@($r2.cards.id) -join ',') -eq (@($r1.cards.id) -join ',')) "--seed makes the set and the pack reproducible; --random is the same as random"
$e = [Pokeshell.BoosterRng]::new(77); $want = $idx.Sets[$idx.PickSet($e)].Id
Assert ($r1.set -eq $want) "the seeded set is the first draw ($want), then the pack"
$seen = @{}; foreach ($n in 1..12) { $seen[((Invoke-Cli $s4 'pack' 'open' 'random' '--json' '--free' '--seed' "$(500 + $n)") | ConvertFrom-Json).set] = 1 }
Assert ($seen.Count -ge 3) "different seeds open different sets ($($seen.Keys -join ', '))"
$x1 = (Invoke-Cli $s4 'pack' 'open' 'swsh7' '--json' '--free' '--seed' '5') | ConvertFrom-Json
Assert ($x1.set -eq 'swsh7' -and $x1.random -eq $false -and $x1.setChance -gt 0) "an explicit set still opens, with its random chance for reference"
$s5 = Join-Path $fx 's5'; [void][IO.Directory]::CreateDirectory($s5)
[void](Invoke-Cli $s5 'pack' 'grant' '2' '--reason' 'test' '--json')
$o1 = (Invoke-Cli $s5 'pack' 'open' 'random' '--json') | ConvertFrom-Json
$o2 = (Invoke-Cli $s5 'pack' 'open' 'random' '--json') | ConvertFrom-Json
$o3 = (Invoke-Cli $s5 'pack' 'open' 'random' '--json') | ConvertFrom-Json
$tl = @(Get-Content (Join-Path $s5 'tokens.log'))
$spentLines = @($tl | Where-Object { $_ -match "`t-1`topened (\S+)`tid=.*`tset=\1`tpack=.*`trandom=1$" })
Assert ($o1.spent -eq 1 -and $o1.tokens -eq 1 -and $o2.spent -eq 1 -and $o2.tokens -eq 0 -and $o3.code -eq 'no-tokens') "random opens spend one token each; with none left it's refused"
Assert ($tl.Count -eq 3 -and $spentLines.Count -eq 2 -and $spentLines[0] -match "set=$($o1.set)`t" -and $spentLines[1] -match "set=$($o2.set)`t") "tokens.log: exactly one -1 line per random open, naming the set it rolled"
$pl = @(Get-Content (Join-Path $s5 'pulls.log') -Encoding UTF8)
Assert ($pl.Count -eq @($o1.cards).Count + @($o2.cards).Count -and @($pl | Where-Object { $_ -match "`tbooster:$($o1.set)`t" }).Count -ge @($o1.cards).Count) "every card of the random packs is logged, tagged with its set"
$od = (Invoke-Cli $s5 'pack' 'odds' 'random' '--json') | ConvertFrom-Json
Assert ($od.set -eq 'random' -and @($od.sets).Count -eq $idx.Sets.Count -and [math]::Abs((@($od.sets) | Measure-Object chance -Sum).Sum - 1) -lt 1e-4 -and ($od.sets | Where-Object set -eq 'base1').priceSource.url) "pack odds random --json: every set's price, source and chance"
$ls2 = (Invoke-Cli $s5 'pack' 'sets' '--json') | ConvertFrom-Json
Assert ($ls2.priceExponent -eq $k -and -not @($ls2.sets | Where-Object { -not $_.price -or ($_.openable -and -not $_.chance) })) "pack sets --json: price and chance per set"
$txt = Invoke-Cli $s5 'pack' 'open' 'random' '--free' '--seed' '3'
$at = $txt.IndexOf('you got a '); $bt = $txt.IndexOf(' booster ')
Assert ($at -ge 0 -and $bt -gt $at -and $txt -match 'you got a .+ pack! \(1 in [\d.]+\)') "the terminal reveal announces the set first"
$v = (Invoke-Cli $s5 'version' '--json') | ConvertFrom-Json
Assert (@($v.commands) -contains 'pack open random --json' -and @($v.commands) -contains 'pack odds random --json') "version --json lists pack open random / pack odds random"

Write-Host "8. the booster index" -ForegroundColor Cyan
$if = Join-Path $s5 'booster-index-pokemon.tsv'
Assert ((Test-Path $if) -and (Get-Content $if -TotalCount 1) -like "stamp`tv1|*") "<state>\booster-index-pokemon.tsv is written once and reused"
$t0 = (Get-Item $if).LastWriteTimeUtc
[void](Invoke-Cli $s5 'pack' 'open' 'swsh7' '--json' '--free')
Assert ((Get-Item $if).LastWriteTimeUtc -eq $t0) "an open reuses the index (not rewritten)"
$bj = Join-Path $fx 'packs\pokemon\boosters.json'; [IO.File]::SetLastWriteTimeUtc($bj, [DateTime]::UtcNow.AddMinutes(1))
[void](Invoke-Cli $s5 'pack' 'open' 'swsh7' '--json' '--free')
Assert ((Get-Item $if).LastWriteTimeUtc -ne $t0) "boosters.json changed: the index is rebuilt"
$t1 = (Get-Item $if).LastWriteTimeUtc
[IO.File]::WriteAllText((Join-Path $fx 'dist\pokemon\zz-test-new.ans'), $art, $utf8)   # a card's art built or removed
[void](Invoke-Cli $s5 'pack' 'open' 'swsh7' '--json' '--free')
Remove-Item (Join-Path $fx 'dist\pokemon\zz-test-new.ans')
Assert ((Get-Item $if).LastWriteTimeUtc -ne $t1) "the art folder changed: the index is rebuilt"
[IO.File]::WriteAllText($if, "stamp`tgarbage`n")
$g = (Invoke-Cli $s5 'pack' 'open' 'swsh7' '--json' '--free' '--seed' '5') | ConvertFrom-Json
Assert ((@($g.cards.id) -join ',') -eq (@($x1.cards.id) -join ',')) "a damaged index is rebuilt; the same seed opens the same pack"

Write-Host "9. the incremental web export and its timing" -ForegroundColor Cyan
if (Test-Path $bexe) {
  $saved = $env:POKESHELL_BINDER; $env:POKESHELL_BINDER = $bexe
  $s6 = Join-Path $fx 's6'; [void][IO.Directory]::CreateDirectory($s6)
  [void](Invoke-Cli $s6 'pack' 'open' 'swsh7' '--json' '--free' '--seed' '1')
  $ErrorActionPreference = 'Continue'
  $full = (& $bexe --export-web (Join-Path $s6 'web') --root $fx --state $s6 2>$null) -join ' '
  $ErrorActionPreference = 'Stop'
  $img = Join-Path $s6 'web\img\pokemon'
  # an image of a card not in the pack goes missing: --only leaves it alone, a full export puts it back
  $other = @(Get-ChildItem $img -Recurse -Filter '*.png' | Where-Object { $_.Name -notmatch '^_' })[0]
  $j = (Invoke-Cli $s6 'pack' 'open' 'base' '--json' '--free' '--seed' '2' '--export') | ConvertFrom-Json
  $mine = @($j.cards | ForEach-Object { Join-Path $s6 ("web\" + $_.image.Replace('/', '\')) })
  Assert ($j.exported -eq $true -and -not @($mine | Where-Object { -not (Test-Path $_) })) "--export renders the pack's cards (and only needs them)"
  Remove-Item $other.FullName
  foreach ($m in $mine) { Remove-Item $m -ErrorAction SilentlyContinue }
  $ErrorActionPreference = 'Continue'
  $inc = (& $bexe --export-web (Join-Path $s6 'web') --root $fx --state $s6 --only (@($j.cards.id) -join ',') 2>$null) -join ' '
  $ErrorActionPreference = 'Stop'
  Assert (-not (Test-Path $other.FullName) -and -not @($mine | Where-Object { -not (Test-Path $_) }) -and $inc -match '\((\d+) decoded' -and [int]$Matches[1] -eq @($j.cards.id | Select-Object -Unique).Count) "--only re-renders just the named cards ($($Matches[1]) decoded), nothing else is touched or pruned"
  $d = [IO.File]::ReadAllText((Join-Path $s6 'web\data.json'), [Text.Encoding]::UTF8) | ConvertFrom-Json
  Assert (@($d.pulls | Where-Object { $_.status -eq 'collected' }).Count -eq @(Get-Content (Join-Path $s6 'pulls.log')).Count) "--only still rewrites data.json with every pull"
  $ErrorActionPreference = 'Continue'
  $back = (& $bexe --export-web (Join-Path $s6 'web') --root $fx --state $s6 2>$null) -join ' '
  $ErrorActionPreference = 'Stop'
  Assert ((Test-Path $other.FullName) -and $back -match '\(1 decoded') "a full export puts the missing image back (1 decoded, the rest cached)"
  # the art cache is keyed by paths relative to the root: the same checkout under another path (a module's
  # <state>\current, a copied state) keeps it
  $alias = Join-Path ([IO.Path]::GetTempPath()) "pokeshell-test-boosters-alias-$PID"
  Remove-Item $alias -Force -ErrorAction SilentlyContinue
  [void](New-Item -ItemType Junction -Path $alias -Target $fx)
  $ErrorActionPreference = 'Continue'
  $moved = (& $bexe --export-web (Join-Path $s6 'web') --root $alias --state $s6 2>$null) -join ' '
  $ErrorActionPreference = 'Stop'
  [IO.Directory]::Delete($alias)   # the junction only, never its target
  Assert ($moved -match '\(0 decoded') "another root path with the same files: the art cache still holds (0 decoded)"
  # an older cache that named absolute source paths still matches (the user's cache before this change)
  $cf = Join-Path $s6 'web\img\.cache.json'
  $c = [IO.File]::ReadAllText($cf) -replace '"src":\["dist\\\\', ('"src":["' + ($fx -replace '\\', '\\') + '\\dist\\')
  [IO.File]::WriteAllText($cf, $c)
  $ErrorActionPreference = 'Continue'
  $old = (& $bexe --export-web (Join-Path $s6 'web') --root $fx --state $s6 2>$null) -join ' '
  $ErrorActionPreference = 'Stop'
  Assert ($c.Contains(($fx -replace '\\', '\\')) -and $old -match '\(0 decoded') "a cache with absolute source paths (the old format) is still warm (0 decoded)"
  # timing (lenient: a loaded machine gets a wide margin). Warm: the index and the art cache exist.
  $ms = foreach ($n in 1..3) {
    $sw = [Diagnostics.Stopwatch]::StartNew(); $t = (Invoke-Cli $s6 'pack' 'open' 'random' '--json' '--free' '--export') | ConvertFrom-Json; $sw.Stop()
    if ($t.exported) { $sw.ElapsedMilliseconds } else { 99999 } }
  $med = @($ms | Sort-Object)[1]
  Assert ($med -lt 4000) "pack open random --json --export, warm: $(($ms | ForEach-Object { "$_ ms" }) -join ', ') (median under 4 s; about 1 s on an idle machine)"
  $env:POKESHELL_BINDER = $saved
} else { Write-Host "  skip  binder.exe not built (binder\build.ps1)" -ForegroundColor Yellow }

Remove-Item $fx -Recurse -Force -ErrorAction SilentlyContinue
if ($script:Failures) { Write-Host "`n$script:Failures FAILED" -ForegroundColor Red; exit 1 }
Write-Host "`nall booster tests passed" -ForegroundColor Green
