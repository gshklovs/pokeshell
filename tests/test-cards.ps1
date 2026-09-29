<#
Real-card packs (pack.json "cards"): the roll cache, the card-mode roll (tier by weight among the tiers that have
cards, then a card of that tier, then a skin of that tier), denied foils, the retired-pull rules the binders use,
and a 10k-roll dry run of the real pokemon pack when its art is built locally (tools\build_realcards.py).
Never opens a tab: rolls call the core directly; state goes to %TEMP%.
  powershell -NoProfile -File tests\test-cards.ps1
#>
. (Join-Path $PSScriptRoot '_setup.ps1')
$e = [char]27
function Strip([string]$s) { $s -replace "$e\[[0-9;]*m", '' }
function Clear-Markers { foreach ($k in 'POKESHELL_ROLLED', 'POKESHELL_PULL', 'CARDSHELL_ROLLED') { [Environment]::SetEnvironmentVariable($k, $null) } }

Write-Host "1. a throwaway real-card pack: roll cache" -ForegroundColor Cyan
$fx = Join-Path ([IO.Path]::GetTempPath()) "pokeshell-test-cards-$PID"
Remove-Item $fx -Recurse -Force -ErrorAction SilentlyContinue
foreach ($d in 'packs\cardy', 'dist\cardy', 'state') { [void][IO.Directory]::CreateDirectory((Join-Path $fx $d)) }
$utf8 = [Text.UTF8Encoding]::new($false)
[IO.File]::WriteAllText((Join-Path $fx 'packs\cardy\pack.json'), @'
{ "id": "cardy", "name": "Cardy", "shiny_chance": 0,
  "tiers": [
    { "id": "common", "label": "common", "rarity": "Common", "weight": 60, "skins": {}, "frame": "plain" },
    { "id": "uncommon", "label": "uncommon", "rarity": "Uncommon", "weight": 1000, "skins": {} },
    { "id": "rare-holo", "label": "rare holo", "rarity": "Rare Holo", "weight": 30, "skins": { "sk1": 3, "sk2": 1 }, "frame": "holo" },
    { "id": "rare-ultra", "label": "rare ultra", "rarity": "Rare Ultra", "weight": 10, "skins": { "sk3": 1 }, "frame": "rainbow" },
    { "id": "hyper-rare", "label": "hyper rare", "rarity": "Hyper Rare", "weight": 5000, "skins": { "sk4": 1 }, "frame": "gold" }
  ],
  "cards": {
    "set1-1":  { "character": "bob",  "tier": "common",     "name": "Bob",    "number": "1/9" },
    "set1-2":  { "character": "nido", "tier": "common",     "name": "Nido",   "number": "2/9" },
    "set1-5":  { "character": "bob",  "tier": "rare-holo",  "name": "Bob",    "number": "5/9" },
    "set2-70": { "character": "nido", "tier": "rare-ultra", "name": "Nido V", "number": "70/80" },
    "set3-99": { "character": "bob",  "tier": "hyper-rare", "name": "Bob ex", "number": "99/80" }
  },
  "retired": { "bob/common": "set1-1", "bob/holo": null, "nido/secret-rare": null }
}
'@, $utf8)
$art = "$e[0;38;2;10;20;30m" + [char]0x2580 + "$e[0m`n"
foreach ($n in 'bob-set1-1', 'nido-set1-2', 'bob-set1-5', 'nido-set2-70') { [IO.File]::WriteAllText((Join-Path $fx "dist\cardy\$n.ans"), $art, $utf8) }   # set3-99 is not built
$st = Join-Path $fx 'state'
[IO.File]::WriteAllLines((Join-Path $st 'installed.tsv'), [string[]]@(1..4 | ForEach-Object { "cardy`tsk$_`t{00000000-0000-0000-0000-00000000c0d$_}`ttest" }))
[IO.File]::WriteAllLines((Join-Path $st 'config.txt'), [string[]]@('pack=cardy'))
$p = Read-PokeshellPack $fx 'cardy'
Assert ($p.isCardPack -and @($p.cardList).Count -eq 5 -and (@($p.characters) -join ',') -eq 'bob,nido' -and $p.cardIndex['set2-70'].tier -eq 3 -and $p.cardIndex['set2-70'].tag -eq '70/80') "pack.json cards are normalized: characters, tier index, number as the frame tag"
Update-PokeshellRollCache -Root $fx -StateDir $st
$rt = @(Get-Content (Join-Path $st 'roll.tsv') -Encoding UTF8)
$odds = @($rt | Where-Object { $_ -like 'odds*' }); $crd = @($rt | Where-Object { $_ -like 'card*' })
Assert (($odds -join '|') -eq "odds`t0`t60|odds`t2`t30|odds`t3`t10") "odds rows only for tiers with a built card ($($odds -join ' | ' -replace "`t", ' '))"
Assert ($crd.Count -eq 4 -and -not ($crd -match 'set3-99') -and $crd -contains "card`t3`tnido`tNido V`tset2-70`t70/80") "card rows: every built card, the unbuilt one left out"
Assert (-not ($rt -match '^char')) "no char rows in card mode"

Write-Host "2. 10000 rolls: tier by weight, cards uniform in their tier, skins of that tier only" -ForegroundColor Cyan
Import-PokeshellCore $st
$tally = @{}; $tiers = @{}; $bad = @(); $spawnSkins = @{}
$t0 = [DateTime]::UtcNow.Ticks
for ($i = 0; $i -lt 10000; $i++) {
  Clear-Markers
  [IO.File]::Delete((Join-Path $st 'spawn-gate.txt'))
  $r = [Pokeshell.Core]::Roll($fx, $st, $PlainGuid, @('powershell.exe'), $t0 + $i * 50000000L, $i, -1, 'x', 'C:\', 'C:\')
  $tally[$r.Art]++; $tiers[$r.TierId]++
  $c = $p.cardIndex[$r.Art]
  if (-not $c -or $c.character -ne $r.Character -or $c.tierId -ne $r.TierId) { $bad += "$($r.Character)/$($r.TierId)/$($r.Art)" }
  if ($r.Action -eq 'foil') { $spawnSkins["$($r.TierId)/$($r.Skin)"]++ } elseif ($r.Skin) { $bad += "skin on a $($r.Action)" }
  if ($r.TierId -in 'common' -and $r.Action -eq 'foil') { $bad += 'common spawned' }
}
Clear-Markers
Remove-Item (Join-Path $st 'pulls.log') -ErrorAction SilentlyContinue
Assert (-not $bad) "every roll is a built card of this pack, in its own tier$(if ($bad) { ': ' + (($bad | Select-Object -First 5) -join ', ') })"
Assert (-not $tally['set3-99'] -and -not $tiers['uncommon'] -and -not $tiers['hyper-rare']) "empty tiers (uncommon, hyper rare: no built card) never roll, despite their big weights"
$pc = 100.0 * $tiers['common'] / 10000; $ph = 100.0 * $tiers['rare-holo'] / 10000; $pu = 100.0 * $tiers['rare-ultra'] / 10000
Assert ([Math]::Abs($pc - 60) -lt 2.5 -and [Math]::Abs($ph - 30) -lt 2.5 -and [Math]::Abs($pu - 10) -lt 1.5) ("tier odds follow the weights 60/30/10: {0:0.0}% / {1:0.0}% / {2:0.0}%" -f $pc, $ph, $pu)
Assert ([Math]::Abs($tally['set1-1'] - $tally['set1-2']) -lt 400) "the two commons are equally likely ($($tally['set1-1']) vs $($tally['set1-2']))"
$sk = ($spawnSkins.Keys | Sort-Object) -join ','
Assert ($sk -eq 'rare-holo/sk1,rare-holo/sk2,rare-ultra/sk3' -and $spawnSkins['rare-holo/sk1'] -gt 2 * $spawnSkins['rare-holo/sk2']) "skins only from the rolled tier, by weight ($(($spawnSkins.GetEnumerator() | Sort-Object Name | ForEach-Object { "$($_.Name) $($_.Value)" }) -join ', '))"

Write-Host "3. forced odds, denied foils, the fallback" -ForegroundColor Cyan
$r = Invoke-Fresh { [Pokeshell.Core]::Roll($fx, $st, $PlainGuid, @('powershell.exe'), [DateTime]::UtcNow.Ticks, 3, 0, 'x', 'C:\', 'C:\') }
Assert ($r.Action -eq 'common' -and $r.TierId -eq 'common' -and (Strip $r.Text).Contains([string][char]0x256d)) "foilChance 0: a plain-tab tier, framed ($($r.Art))"
[IO.File]::Delete((Join-Path $st 'spawn-gate.txt'))
$r = Invoke-Fresh { [Pokeshell.Core]::Roll($fx, $st, $PlainGuid, @('powershell.exe'), [DateTime]::UtcNow.Ticks, 3, 1, 'x', 'C:\', 'C:\') }
$cmd = if ($r.WtArgs) { [Text.Encoding]::Unicode.GetString([Convert]::FromBase64String($r.WtArgs[-1])) } else { '' }
$low = $p.cardList | Where-Object { $_.character -eq $r.Character } | Sort-Object tier | Select-Object -First 1
Assert ($r.Action -eq 'foil' -and $r.TierId -in 'rare-holo', 'rare-ultra' -and $cmd.Contains("-Art '$($r.Art)'") -and $cmd.Contains("-Character '$($r.Character)'")) "foilChance 1: a skinned tier; the tab prints that card (-Art $($r.Art))"
Assert ($r.FallbackLogLine.Split("`t")[4] -eq $low.id -and $r.FallbackLogLine.Split("`t")[3] -eq 'common') "its fallback (placement failed) is the same character's lowest card, $($low.id)"
$r2 = Invoke-Fresh { [Pokeshell.Core]::Roll($fx, $st, $PlainGuid, @('powershell.exe'), [DateTime]::UtcNow.Ticks, 3, 1, 'x', 'C:\', 'C:\') }   # the gate refuses: 3 s rate limit
Assert ($r2.Action -eq 'foil-denied' -and $r2.TierId -eq 'common' -and $r2.Art -eq $low.id -and $r2.LogLine -match 'denied:rate' -and -not $r2.WtArgs) "a denied foil shows (and logs) the character's lowest card instead, no spawn"
Remove-Item (Join-Path $st 'pulls.log') -ErrorAction SilentlyContinue

Write-Host "3b. printed-shiny tiers (Shiny Vault, Radiant: tier `"shiny`": `"printed`") never roll shiny" -ForegroundColor Cyan
foreach ($d in 'packs\vaulty', 'dist\vaulty', 'vstate') { [void][IO.Directory]::CreateDirectory((Join-Path $fx $d)) }
[IO.File]::WriteAllText((Join-Path $fx 'packs\vaulty\pack.json'), @'
{ "id": "vaulty", "name": "Vaulty", "shiny_chance": 1,
  "tiers": [
    { "id": "common", "label": "common", "rarity": "Common", "weight": 50, "skins": {}, "frame": "plain" },
    { "id": "rare-shiny", "label": "rare shiny", "rarity": "Rare Shiny", "weight": 50, "skins": {}, "frame": "silver", "shiny": "printed" }
  ],
  "cards": {
    "sm115-7": { "character": "bob", "tier": "common",     "name": "Bob", "number": "7/68" },
    "sma-SV6": { "character": "bob", "tier": "rare-shiny", "name": "Bob", "number": "SV6/SV94" }
  }
}
'@, $utf8)
$shinyArt = "$e[0;38;2;200;10;10m" + [char]0x2580 + "$e[0m`n"
[IO.File]::WriteAllText((Join-Path $fx 'dist\vaulty\bob-sm115-7.ans'), $art, $utf8)
[IO.File]::WriteAllText((Join-Path $fx 'dist\vaulty\bob-sm115-7-shiny.ans'), $shinyArt, $utf8)
[IO.File]::WriteAllText((Join-Path $fx 'dist\vaulty\bob-sma-SV6.ans'), $art, $utf8)   # printed shiny: no -shiny.ans
$vs = Join-Path $fx 'vstate'
[IO.File]::WriteAllLines((Join-Path $vs 'config.txt'), [string[]]@('pack=vaulty'))
Update-PokeshellRollCache -Root $fx -StateDir $vs
$vt = @(Get-Content (Join-Path $vs 'roll.tsv') -Encoding UTF8)
Assert ((@($vt | Where-Object { $_ -like 'printed*' }) -join '|') -eq "printed`t1") "roll.tsv marks the printed-shiny tier (printed 1) and only it"
$byT = @{}; $shinyBy = @{}
for ($i = 0; $i -lt 400; $i++) {
  Clear-Markers
  $r = [Pokeshell.Core]::Roll($fx, $vs, $PlainGuid, @('powershell.exe'), $t0 + $i * 50000000L, [int](((7L + $i) * 48271L) % 2147483647L), -1, 'x', 'C:\', 'C:\')
  $byT[$r.TierId]++; if ($r.Shiny) { $shinyBy[$r.TierId]++ }
  if ($r.TierId -eq 'rare-shiny' -and ((Strip $r.Text).Contains([string][char]0x2726) -or $r.LogLine.Split("`t")[6] -ne '0')) { $shinyBy['rare-shiny-text']++ }
}
Clear-Markers
Assert ($byT['common'] -gt 100 -and $byT['rare-shiny'] -gt 100) "both tiers roll ($($byT['common']) / $($byT['rare-shiny']))"
Assert ([int]$shinyBy['common'] -eq [int]$byT['common']) "shiny_chance 1: every regular-tier pull is shiny ($([int]$shinyBy['common']) of $($byT['common']))"
Assert (-not $shinyBy['rare-shiny'] -and -not $shinyBy['rare-shiny-text']) "a printed-shiny tier is never shiny: not in the pull, the banner or the log"
$txt = [Pokeshell.Core]::PullText($fx, 'vaulty', 'bob', 'Bob', 'sma-SV6', 'rare shiny', 1, $true)
Assert ($txt.Contains('10;20;30') -and -not $txt.Contains('200;10;10')) "a shiny request with no -shiny.ans falls back to the regular art (PullText)"
. (Join-Path $RepoRoot 'scripts\lib\anim.ps1'); Import-PokeshellAnimCore $st
$f = [Pokeshell.Anim]::Find($fx, 'vaulty', 'bob', 'sma-SV6', $true)
Assert ($f[0] -eq '' -and $f[1] -eq '') "the anim player looks for the regular art's loop (none here: no animation, no error)"
[IO.File]::WriteAllText((Join-Path $fx 'dist\vaulty\bob-sma-SV6.anim'), "{`"lines`":1,`"fps`":12,`"frames`":1,`"final`":0}`n`f$art", $utf8)
$f = [Pokeshell.Anim]::Find($fx, 'vaulty', 'bob', 'sma-SV6', $true)
Assert ($f[0] -like '*bob-sma-SV6.anim' -and $f[1] -like '*bob-sma-SV6.ans') "shiny with no -shiny.ans: the anim player plays the regular loop"
Remove-Item (Join-Path $fx 'dist\vaulty'), (Join-Path $fx 'packs\vaulty'), $vs -Recurse -Force

Write-Host "4. the binders' rule: what an old or new pulls.log line shows" -ForegroundColor Cyan
$c = Resolve-PokeshellPull $p 'nido' 'rare-ultra' 'set2-70'
Assert ($c -and $c.id -eq 'set2-70') "a new pull (art column = card id) is that card"
$c = Resolve-PokeshellPull $p 'bob' 'common' 'common'
Assert ($c -and $c.id -eq 'set1-1') "an old common maps to the character's real common (retired: bob/common -> set1-1)"
Assert ($null -eq (Resolve-PokeshellPull $p 'bob' 'holo' 'holo')) "retired art (null) is hidden"
Assert ($null -eq (Resolve-PokeshellPull $p 'nido' 'common' 'common')) "old art with no retired entry is hidden too"
Assert ($null -eq (Resolve-PokeshellPull $p 'bob' 'rare-ultra' 'set2-70')) "a card id with the wrong character is hidden"
Assert ($null -eq (Resolve-PokeshellPull $p 'bob' 'hyper-rare' 'set3-99')) "a card whose art isn't built (set3-99) is hidden, like retired art"
$legacy = Read-PokeshellPack $fx 'cardy'; $legacy.isCardPack = $false
Assert ((Resolve-PokeshellPull $legacy 'bob' 'holo' 'holo') -eq 'legacy') "packs without cards: every pull shows as logged"

Write-Host "5. a real-card pack with nothing built (a public checkout) rolls nothing" -ForegroundColor Cyan
Get-ChildItem (Join-Path $fx 'dist\cardy') | Remove-Item
Update-PokeshellRollCache -Root $fx -StateDir $st
$r = Invoke-Fresh { [Pokeshell.Core]::Roll($fx, $st, $PlainGuid, @('powershell.exe'), [DateTime]::UtcNow.Ticks, 3, -1, 'x', 'C:\', 'C:\') }
Assert ($r.Action -eq 'skip' -and $r.Reason -eq 'empty-pack' -and -not $r.Text) "skip: empty-pack (no text, no spawn)"
Clear-Markers
Remove-Item $fx -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "6. the real pokemon pack: 10000-roll dry run (local art)" -ForegroundColor Cyan
$pk = Read-PokeshellPack $RepoRoot 'pokemon'
$builtCards = @($pk.cardList | Where-Object { Test-PokeshellCardBuilt $RepoRoot 'pokemon' $_ })
if (-not $builtCards) {
  Write-Host "  (no pokemon card art built in this checkout: tools\build_realcards.py; skipped)" -ForegroundColor Yellow
} else {
  $rs = New-TestState 'cards-real'
  [IO.File]::WriteAllLines((Join-Path $rs 'config.txt'), [string[]]@('pack=pokemon'))
  Update-PokeshellRollCache -Root $RepoRoot -StateDir $rs
  $n = 10000; $byCard = @{}; $byTier = @{}; $bad = @(); $shinyN = 0; $foils = 0
  for ($i = 0; $i -lt $n; $i++) {
    Clear-Markers
    [IO.File]::Delete((Join-Path $rs 'spawn-gate.txt'))
    # scrambled seeds: System.Random's first draws are nearly linear in consecutive seeds, so 1000 + $i left runs
    # of a big tier's cards unreachable in this sample (it bit once Crown Zenith grew the rare tier)
    $r = [Pokeshell.Core]::Roll($RepoRoot, $rs, $PlainGuid, @('powershell.exe'), $t0 + $i * 50000000L, [int](((1000L + $i) * 48271L) % 2147483647L), -1, 'x', 'C:\', 'C:\')
    $byCard[$r.Art]++; $byTier[$r.TierId]++; if ($r.Shiny) { $shinyN++ }; if ($r.Action -eq 'foil') { $foils++ }
    $c = $pk.cardIndex[$r.Art]
    if (-not $c -or $c.character -ne $r.Character -or $c.tierId -ne $r.TierId -or -not (Test-PokeshellCardBuilt $RepoRoot 'pokemon' $c)) { $bad += "$($r.Character)/$($r.TierId)/$($r.Art)" }
  }
  Clear-Markers
  Assert (-not $bad) "all $n rolls are real cards listed in pack.json with built art$(if ($bad) { ': ' + (($bad | Select-Object -Unique -First 5) -join ', ') })"
  Assert (-not ($byCard.Keys | Where-Object { $_ -match '\*|invented|^(common|holo|fullart|gold|top)$' })) "no invented card and no old art variant ever rolls"
  # a fixed-seed sample can't reach the rarest cards (1 in ~6700), so only cards whose tier gives them >= 5 expected
  # rolls in this sample must turn up; the tier-frequency check below covers the rest
  $inTier = @{}; foreach ($c in $builtCards) { $inTier[$c.tierId]++ }
  $due = @($builtCards | Where-Object { ([double]$byTier[$_.tierId] / $inTier[$_.tierId]) -ge 5 })
  $missed = @($due | Where-Object { -not $byCard[$_.id] })
  Assert (-not $missed) "every built card that should appear in $n rolls turns up ($($due.Count - $missed.Count) of $($due.Count)$(if ($missed) { '; missing ' + (($missed | Select-Object -First 5 | ForEach-Object id) -join ', ') }))"
  $live = @($builtCards | ForEach-Object tier | Sort-Object -Unique)
  $tot = 0; foreach ($i in $live) { $tot += [int]$pk.tiers[$i].weight }
  Write-Host ("  {0,-20} {1,7} {2,8} {3,8}" -f 'tier', 'rolls', 'actual', 'expected')
  foreach ($i in $live) {
    $t = $pk.tiers[$i]; $k = [int]$byTier[$t.id]
    Write-Host ("  {0,-20} {1,7} {2,7:0.00}% {3,7:0.00}%" -f $t.label, $k, (100.0 * $k / $n), (100.0 * [int]$t.weight / $tot))
    foreach ($c in @($builtCards | Where-Object tier -eq $i)) { Write-Host ("      {0,-12} {1,-12} {2,-11} {3,6}" -f $c.id, $c.name, $c.character, [int]$byCard[$c.id]) }
  }
  Write-Host ("  shiny {0} ({1:0.00}%), skinned (foil) {2} ({3:0.00}%)" -f $shinyN, (100.0 * $shinyN / $n), $foils, (100.0 * $foils / $n))
  $worst = 0; foreach ($i in $live) { $d = [Math]::Abs(100.0 * [int]$byTier[$pk.tiers[$i].id] / $n - 100.0 * [int]$pk.tiers[$i].weight / $tot); if ($d -gt $worst) { $worst = $d } }
  Assert ($worst -lt 1.5) ("tier frequencies match pack.json weights (worst gap {0:0.00} points)" -f $worst)
  Remove-Item $rs -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host ''
if ($script:Failures) { Write-Host "cards: $script:Failures FAILED" -ForegroundColor Red; exit 1 }
Write-Host "cards: all passed" -ForegroundColor Green
