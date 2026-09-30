<#
pokeshell booster packs (docs/BOOSTERS.md): real booster structures from packs/<pack>/boosters.json, rolled with a
CSPRNG (Booster.cs), recorded into pulls.log as caught pulls, and the pack-token ledger (tokens.log).
Dot-sourced by scripts\pokeshell.ps1 after roll.ps1 and common.ps1.
#>

# ---------------------------------------------------------------- the dice (Booster.cs, compiled once like the core)
function Import-PokeshellBooster([string]$StateDir) {
  if ('Pokeshell.Booster' -as [type]) { return }
  if (-not $StateDir) { $StateDir = Get-PokeshellStateDir }
  $src = Join-Path $PSScriptRoot 'Booster.cs'
  $dll = "$StateDir\pokeshell-booster-" + [IO.File]::GetLastWriteTimeUtc($src).Ticks + "-$PSEdition.dll"
  if (-not [IO.File]::Exists($dll)) {
    [void][IO.Directory]::CreateDirectory($StateDir)
    $tmp = "$dll.$PID.tmp"
    Add-Type -Path $src -OutputAssembly $tmp -OutputType Library
    try { [IO.File]::Move($tmp, $dll) } catch { [IO.File]::Delete($tmp) }
  }
  [void][Reflection.Assembly]::LoadFile($dll)
}

# ---------------------------------------------------------------- the data
function Read-PokeshellBoosters([string]$Root, [string]$PackId = 'pokemon') {
  $f = Join-Path $Root "packs\$PackId\boosters.json"
  if (-not [IO.File]::Exists($f)) { throw "no booster data for pack '$PackId' ($f)" }
  [IO.File]::ReadAllText($f, [Text.Encoding]::UTF8) | ConvertFrom-Json
}

# the set a card belongs to: its pokemontcg.io id without the number ("swsh12pt5gg-GG01" -> "swsh12pt5gg")
function Get-PokeshellCardSet([string]$Id) { $i = $Id.LastIndexOf('-'); if ($i -gt 0) { $Id.Substring(0, $i) } else { $Id } }

# a set by id, or by a word of its name ("evolving", "zenith", "base")
function Find-PokeshellBoosterSet($Boosters, [string]$Want) {
  $w = "$Want".Trim().ToLower()
  $sets = @($Boosters.sets)
  $hit = @($sets | Where-Object { $_.id.ToLower() -eq $w -or @($_.aliases) -contains $w })
  if (-not $hit) { $hit = @($sets | Where-Object { $_.name.ToLower() -eq $w }) }
  if (-not $hit) { $hit = @($sets | Where-Object { $_.name.ToLower().Contains($w) }) }
  if ($hit.Count -eq 1) { return $hit[0] }
  if ($hit.Count -gt 1) { throw "'$Want' matches several sets: $(($hit | ForEach-Object { "$($_.id) ($($_.name))" }) -join ', ')" }
  throw "no booster '$Want' (pokeshell pack sets lists them: $(($sets | ForEach-Object id) -join ', '))"
}

# The effect family the opening scene (and the terminal reveal) shows for a card and how big the reveal is ("hit",
# 0-5) are Booster.cs's (Booster.Fx / Booster.Hit): a tier's default, an outcome's "fx" overrides it, a reverse-holo
# slot makes a non-foil card "reverse".

function Test-PokeshellCardMatch($Card, $Pick, [string[]]$DefaultSets) {
  $sets = if ($Pick.sets) { @($Pick.sets) } else { $DefaultSets }
  if ($Pick.ids) { return @($Pick.ids) -contains $Card.id }
  if ($sets -notcontains (Get-PokeshellCardSet $Card.id)) { return $false }
  if ($Pick.exclude -and @($Pick.exclude) -contains $Card.id) { return $false }
  if ($Pick.rarity -and @($Pick.rarity) -notcontains $Card.rarity) { return $false }
  if ($Pick.supertype -and $Pick.supertype -ne 'Pok') { return $false }   # every card we serve is a Pokemon card
  $true
}

<#
One set's booster, resolved against the cards we serve (pack.json cards whose art is built): the slots as Booster.cs
objects and the card table their pools index. Every outcome's weight is its published per-pack rate times
served/printed (the share of that outcome's printed cards we serve), then each slot renormalises over what's left,
so every served card keeps its real odds relative to every other (docs/BOOSTERS.md, "Cards we don't serve").
#>
function Get-PokeshellBoosterModel([string]$Root, $Pack, $Set) {
  if ($script:BoosterRawPack -and $script:BoosterRawPack[0] -eq $Pack.dir) { $raw = $script:BoosterRawPack[1] }
  else { $raw = [IO.File]::ReadAllText((Join-Path $Pack.dir 'pack.json'), [Text.Encoding]::UTF8) | ConvertFrom-Json; $script:BoosterRawPack = @($Pack.dir, $raw) }
  $cardSets = @($Set.cardSets)
  $want = [Collections.Generic.HashSet[string]]::new([string[]]$cardSets)
  $dist = Join-Path $Root "dist\$($Pack.id)"
  $cards = [Collections.Generic.List[object]]::new()
  foreach ($c in $Pack.cardList) {
    $cs = $c.id.Substring(0, [Math]::Max(0, $c.id.LastIndexOf('-')))   # Get-PokeshellCardSet, inlined
    if (-not $want.Contains($cs)) { continue }
    if (-not [IO.File]::Exists("$dist\$($c.character)-$($c.id).ans")) { continue }   # Test-PokeshellCardBuilt
    $e = $raw.cards.($c.id)
    $cards.Add([pscustomobject]@{ id = $c.id; character = $c.character; name = $c.name; number = $c.tag; tier = $c.tier; tierId = $c.tierId
                                  rarity = [string]$e.rarity; set = [string]$e.set; cset = $cs })
  }
  $slots = [Collections.Generic.List[Pokeshell.BoosterSlot]]::new(); $meta = @()
  foreach ($s in @($Set.slots)) {
    $slot = [Pokeshell.BoosterSlot]::new()
    $slot.Id = [string]$s.id; $slot.Count = [int]$(if ($s.count) { $s.count } else { 1 })
    $slot.Finish = [string]$(if ($s.finish) { $s.finish } else { 'normal' })
    $om = @(); $missing = 0.0; $baseAt = -1
    foreach ($pk in @($s.pick)) {
      # Test-PokeshellCardMatch, inlined (a function call per card costs seconds over every set in PowerShell 5.1)
      # (the unary comma keeps `if` from unrolling a set into its strings, whose .Contains would be a substring test)
      $ids = if ($pk.ids) { , [Collections.Generic.HashSet[string]]::new([string[]]@($pk.ids)) } else { $null }
      $inSets = [Collections.Generic.HashSet[string]]::new([string[]]@(if ($pk.sets) { $pk.sets } else { $cardSets }))
      $rar = if ($pk.rarity) { , [Collections.Generic.HashSet[string]]::new([string[]]@($pk.rarity)) } else { $null }
      $exc = if ($pk.exclude) { , [Collections.Generic.HashSet[string]]::new([string[]]@($pk.exclude)) } else { $null }
      $noPok = $pk.supertype -and $pk.supertype -ne 'Pok'
      $pool = [int[]]@(if (-not $noPok) { for ($i = 0; $i -lt $cards.Count; $i++) {
        $c = $cards[$i]
        if ($null -ne $ids) { if ($ids.Contains($c.id)) { $i }; continue }
        if (-not $inSets.Contains($c.cset) -or ($null -ne $exc -and $exc.Contains($c.id)) -or ($null -ne $rar -and -not $rar.Contains($c.rarity))) { continue }
        $i
      } })
      $rate = [double]$(if ($null -ne $pk.rate) { $pk.rate } else { 1 })
      $printed = [int]$(if ($pk.printed) { $pk.printed } else { 0 })
      $share = if ($printed -gt 0) { [math]::Min(1.0, $pool.Count / $printed) } else { [double]($pool.Count -gt 0) }
      $w = $rate
      if ($pk.base -and $baseAt -lt 0) { $baseAt = $slot.Outcomes.Count }
      else { $w = $rate * $share; $missing += $rate - $w }   # the printed cards we don't serve: their share goes to the base
      $slot.Add([string]$pk.label, $w, $pool, [string]$pk.finish)
      $om += [pscustomobject]@{ label = [string]$pk.label; rate = $rate; printed = $printed; served = $pool.Count; fx = [string]$pk.fx; base = [bool]$pk.base }
    }
    # every served card keeps its real per-pack odds; the base outcome (a plain common / rare / reverse holo) takes the
    # rest. Without a (served) base, the slot just renormalises over what's left.
    if ($baseAt -ge 0 -and $slot.Outcomes[$baseAt].Pool.Length -gt 0) { $slot.Outcomes[$baseAt].Weight += $missing }
    $slots.Add($slot); $meta += , $om
  }
  [pscustomobject]@{ set = $Set; cards = $cards; slots = $slots.ToArray(); meta = $meta }
}

# ---------------------------------------------------------------- the booster index (Booster.cs BoosterIndex)
<#
Every set's model, resolved once into <state>\booster-index-<pack>.tsv, so `pack open` never parses pack.json (half a
second in PowerShell 5.1): an open loads the index and rolls in C#. The stamp is what the models depend on: the root,
pack.json, boosters.json, the art folder (a card whose art is built or removed changes its time) and this code. A
stale or missing index is rebuilt here, once (a second or two), then reused.
#>
function Get-PokeshellBoosterIndexStamp([string]$Root, [string]$PackId = 'pokemon') {
  $p = @('v1', $Root.TrimEnd('\').ToLowerInvariant())
  foreach ($f in (Join-Path $Root "packs\$PackId\pack.json"), (Join-Path $Root "packs\$PackId\boosters.json"), (Join-Path $PSScriptRoot 'booster.ps1'), (Join-Path $PSScriptRoot 'Booster.cs')) {
    $fi = [IO.FileInfo]::new($f); $p += $(if ($fi.Exists) { "$($fi.LastWriteTimeUtc.Ticks),$($fi.Length)" } else { '-' })
  }
  $d = Join-Path $Root "dist\$PackId"
  $p += $(if ([IO.Directory]::Exists($d)) { [IO.Directory]::GetLastWriteTimeUtc($d).Ticks } else { '-' })
  $p -join '|'
}

function Get-PokeshellBoosterIndex([string]$Root, [string]$StateDir, $Pack, $Boosters, [string]$PackId = 'pokemon') {
  Import-PokeshellBooster $StateDir
  $stamp = Get-PokeshellBoosterIndexStamp $Root $PackId
  if ($script:BoosterIndex -and $script:BoosterIndex.Stamp -eq $stamp) { return , $script:BoosterIndex }
  $file = Join-Path $StateDir "booster-index-$PackId.tsv"
  $x = [Pokeshell.BoosterIndex]::Load($file, $stamp)
  if (-not $x) {
    if (-not $Pack) { $Pack = Read-PokeshellPack $Root $PackId }
    if (-not $Boosters) { $Boosters = Read-PokeshellBoosters $Root $PackId }
    $x = New-PokeshellBoosterIndex $Root $Pack $Boosters
    $x.Stamp = $stamp
    try { [void][IO.Directory]::CreateDirectory($StateDir); $x.Save($file) } catch { }   # (can't write it: rebuilt next time)
  }
  $script:BoosterIndex = $x
  , $x
}

function New-PokeshellBoosterIndex([string]$Root, $Pack, $Boosters) {
  $x = [Pokeshell.BoosterIndex]::new()
  $x.Pack = $Pack.id; $x.ShinyChance = [double]$Pack.shiny_chance
  $x.PriceExponent = [double]$(if ($null -ne $Boosters.priceExponent) { $Boosters.priceExponent } else { 1 })
  $tiers = @($Pack.tiers)
  for ($i = 0; $i -lt $tiers.Count; $i++) { if ($tiers[$i].shiny -eq 'printed') { [void]$x.PrintedShinyTiers.Add($i) } }
  # every built card (one folder listing, not a test per card): pull resolution sees them all
  $files = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
  $dist = Join-Path $Root "dist\$($Pack.id)"
  if ([IO.Directory]::Exists($dist)) { foreach ($f in [IO.Directory]::GetFiles($dist, '*.ans')) { [void]$files.Add([IO.Path]::GetFileName($f)) } }
  foreach ($c in $Pack.cardList) {
    if (-not $files.Contains("$($c.character)-$($c.id).ans")) { continue }
    $bc = [Pokeshell.BoosterCard]::new()
    $bc.Id = $c.id; $bc.Character = $c.character; $bc.Name = $c.name; $bc.Number = $c.tag; $bc.Tier = $c.tier; $bc.TierId = $c.tierId
    $bc.TierLabel = [string]$tiers[$c.tier].label; $bc.ShinyArt = $files.Contains("$($c.character)-$($c.id)-shiny.ans")
    [void]$x.AddCard($bc)
  }
  foreach ($k in $Pack.retired.Keys) { if ($Pack.retired[$k]) { $x.Retired[$k] = $Pack.retired[$k] } }
  foreach ($s in @($Boosters.sets)) {
    $m = Get-PokeshellBoosterModel $Root $Pack $s
    $bs = [Pokeshell.BoosterSet]::new()
    $bs.Id = $s.id; $bs.Name = $s.name; $bs.Aliases = [string[]]@(@($s.aliases) | Where-Object { $_ } | ForEach-Object { "$_".ToLowerInvariant() })
    $bs.Price = [double]$(if ($s.price) { $s.price } else { 0 }); $bs.Cards = $m.cards.Count
    # the model's pools index its own card list: point them at the index's table (and give those cards their rarity)
    $map = [int[]]::new($m.cards.Count)
    for ($i = 0; $i -lt $m.cards.Count; $i++) {
      $c = $m.cards[$i]; $g = $x.ById[$c.id]
      $x.Cards[$g].Rarity = $c.rarity; $x.Cards[$g].SetName = $c.set; $map[$i] = $g
    }
    $meta = [Pokeshell.BoosterOutcomeMeta[][]]::new($m.slots.Count)
    for ($i = 0; $i -lt $m.slots.Count; $i++) {
      foreach ($o in $m.slots[$i].Outcomes) { $o.Pool = [int[]]@(foreach ($p in $o.Pool) { $map[$p] }) }
      $meta[$i] = [Pokeshell.BoosterOutcomeMeta[]]@(foreach ($om in $m.meta[$i]) {
        $bm = [Pokeshell.BoosterOutcomeMeta]::new()
        $bm.Label = $om.label; $bm.Fx = $om.fx; $bm.Rate = $om.rate; $bm.Printed = $om.printed; $bm.Served = $om.served; $bm.Base = $om.base
        $bm })
    }
    $bs.Slots = $m.slots; $bs.Meta = $meta
    $x.Sets.Add($bs)
  }
  , $x
}

# a set of the index by id, alias or name (Find-PokeshellBoosterSet's rule): its index; the error is the message alone
function Find-PokeshellBoosterSetIndex($Index, [string]$Want) {
  try { $Index.FindSet($Want) } catch { throw $(if ($_.Exception.InnerException) { $_.Exception.InnerException.Message } else { $_.Exception.Message }) }
}

# ---------------------------------------------------------------- the ledger: pack tokens (tokens.log)
<#
<state>\tokens.log, append-only TSV, one line per change:  time  delta  reason  id=<ulid>  [set=<set> pack=<pack id>]
  +N  pokeshell pack grant N --reason <text>   (whoever awards packs: the arena, a script, you)
  -1  pokeshell pack open <set>                (spent; --free opens without spending)
The balance is the sum of the deltas. A named mutex keeps concurrent grants/opens from double-spending.
#>
function Get-PokeshellTokenLines([string]$StateDir) {
  $f = Join-Path $StateDir 'tokens.log'
  if (-not [IO.File]::Exists($f)) { return @() }
  @(foreach ($l in [IO.File]::ReadAllLines($f, [Text.Encoding]::UTF8)) {
    $x = $l.Split("`t"); $d = 0
    if ($x.Count -lt 3 -or -not [int]::TryParse($x[1], [ref]$d)) { continue }
    $kv = @{}; foreach ($y in $x[3..($x.Count - 1)]) { $i = $y.IndexOf('='); if ($i -gt 0) { $kv[$y.Substring(0, $i)] = $y.Substring($i + 1) } }
    [pscustomobject]@{ time = $x[0]; delta = $d; reason = $x[2]; id = $kv['id']; set = $kv['set']; pack = $kv['pack'] }
  })
}
# (Get-PokeshellTokenLines' rule, without building the line objects: pack open asks twice)
function Get-PokeshellTokenBalance([string]$StateDir) {
  $f = Join-Path $StateDir 'tokens.log'
  if (-not [IO.File]::Exists($f)) { return 0 }
  $b = 0; $d = 0
  foreach ($l in [IO.File]::ReadAllLines($f, [Text.Encoding]::UTF8)) { $x = $l.Split("`t"); if ($x.Count -ge 3 -and [int]::TryParse($x[1], [ref]$d)) { $b += $d } }
  $b
}

function Invoke-PokeshellTokenLocked([string]$StateDir, [scriptblock]$Block) {
  $h = [BitConverter]::ToString([Security.Cryptography.MD5]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($StateDir.ToLower()))).Replace('-', '')
  $m = [Threading.Mutex]::new($false, "Local\pokeshell-tokens-$h")
  $got = $false
  try { try { $got = $m.WaitOne(10000) } catch [Threading.AbandonedMutexException] { $got = $true }
        if (-not $got) { throw 'pokeshell: the token ledger is busy (another pack is opening)' }
        & $Block }
  finally { if ($got) { $m.ReleaseMutex() }; $m.Dispose() }
}

function Add-PokeshellTokens([string]$StateDir, [int]$Delta, [string]$Reason, [string]$Extra = '') {
  $now = [DateTime]::UtcNow
  $id = [Pokeshell.Core]::NewPullId($now.Ticks)
  $r = ("$Reason" -replace '[\t\r\n]+', ' ').Trim(); if (-not $r) { $r = '-' }
  $line = $now.ToLocalTime().ToString('s', [Globalization.CultureInfo]::InvariantCulture) + "`t" + $Delta.ToString('+0;-0;0', [Globalization.CultureInfo]::InvariantCulture) + "`t$r`tid=$id" + $(if ($Extra) { "`t$Extra" })
  [void][IO.Directory]::CreateDirectory($StateDir)
  [IO.File]::AppendAllText((Join-Path $StateDir 'tokens.log'), $line + "`r`n", [Text.UTF8Encoding]::new($false))
  $id
}

# ---------------------------------------------------------------- opening one pack
<#
Roll one pack of $Set (a set object, its id / alias / name, or its index in the booster index), record every card into
pulls.log (caught at once: a pack is already earned) and return the result: { set, setName, setChance, setOneIn,
random, packId, secure, cards: [...] } with the cards in reveal order (rarest last). -NoRecord: roll only. The roll is
Booster.cs's (BoosterIndex + Booster.Open); -Random marks a set that `pack open random` chose.
#>
function Open-PokeshellBooster([string]$Root, [string]$StateDir, $Pack, $Set, $Rng, [switch]$NoRecord, $Index, [switch]$Random) {
  Import-PokeshellBooster $StateDir
  $packId = if ($Pack -is [string]) { $Pack } elseif ($Pack) { $Pack.id } else { 'pokemon' }
  if (-not $Index) { $Index = Get-PokeshellBoosterIndex $Root $StateDir -Pack $(if ($Pack -isnot [string]) { $Pack }) -PackId $packId }
  $si = if ($Set -is [int]) { $Set } else { Find-PokeshellBoosterSetIndex $Index $(if ($Set -is [string]) { $Set } else { [string]$Set.id }) }
  $bs = $Index.Sets[$si]
  if (-not $bs.Openable) { throw "no cards of $($bs.Name) are served yet (its art isn't built), so it can't be opened" }
  if (-not $Rng) { $Rng = [Pokeshell.BoosterRng]::new() }
  $now = [DateTime]::UtcNow.Ticks
  $caught = [Pokeshell.Booster]::Caught($Index, [Pokeshell.Core]::ReadPulls($StateDir, $now, [Pokeshell.Core]::BootId()))
  $picks = [Pokeshell.Booster]::Open($Index, $si, $Rng, $caught)
  $packUid = [Pokeshell.Core]::NewPullId($now)
  $cards = foreach ($c in $picks) {
    [pscustomobject][ordered]@{
      id = $c.Id; name = $c.Name; number = $c.Number; rarity = $c.Rarity; tier = $c.Tier; tierLabel = $c.TierLabel
      slot = $c.Slot; outcome = $c.Outcome; finish = $c.Finish; fx = $c.Fx; hit = $c.Hit; shiny = $c.Shiny; isNew = $c.IsNew
      oneIn = $c.OneIn; character = $c.Character; setName = $c.SetName; image = $c.Image; pullId = ''
      card = $c.Id; pull = ''   # the arena SPEC's names for id / pullId (docs/arena SPEC: pokeshell pack open)
    }
  }
  if (-not $NoRecord) {
    $stamp = [DateTime]::new($now, [DateTimeKind]::Utc).ToLocalTime().ToString('s', [Globalization.CultureInfo]::InvariantCulture)
    $boot = [Pokeshell.Core]::BootId()
    $lines = foreach ($x in $cards) {
      $x.pullId = [Pokeshell.Core]::NewPullId($now); $x.pull = $x.pullId
      # a caught pull (no "pending" flag): pulls.log's columns, plus where it came from
      "$stamp`t$($Index.Pack)`t$($x.character)`t$($x.tier)`t$($x.id)`t`t$(if ($x.shiny) { '1' } else { '0' })`tbooster:$($bs.Id)`tid=$($x.pullId)`tboot=$boot`tcard=$($x.id)`tbooster=$packUid`tslot=$($x.slot)`tfinish=$($x.finish)"
    }
    [void][IO.Directory]::CreateDirectory($StateDir)
    [IO.File]::AppendAllText((Join-Path $StateDir 'pulls.log'), (($lines -join "`r`n") + "`r`n"), [Text.UTF8Encoding]::new($false))
  }
  $chance = $Index.SetChances()[$si]
  [pscustomobject][ordered]@{
    set = $bs.Id; setName = $bs.Name
    setChance = [math]::Round($chance, 6); setOneIn = $(if ($chance -gt 0) { [math]::Round(1 / $chance, 1) } else { $null })
    setPrice = $(if ($bs.Price -gt 0) { $bs.Price } else { $null }); random = [bool]$Random
    packId = $packUid; secure = $Rng.Secure; cards = @($cards)
  }
}

# ---------------------------------------------------------------- listing
# (with the booster index: each set's price and its chance to be the pack `pack open random` opens)
function Get-PokeshellBoosterSets([string]$Root, $Pack, $Boosters, $Index) {
  $chances = if ($Index) { $Index.SetChances() }
  foreach ($s in @($Boosters.sets)) {
    $ch = $null; if ($Index) { for ($i = 0; $i -lt $Index.Sets.Count; $i++) { if ($Index.Sets[$i].Id -eq $s.id) { $ch = $chances[$i] } } }
    $cardSets = @($s.cardSets)
    $all = @($Pack.cardList | Where-Object { $cardSets -contains (Get-PokeshellCardSet $_.id) })
    $built = @($all | Where-Object { Test-PokeshellCardBuilt $Root $Pack.id $_ })
    $slots = @($s.slots); $size = 0
    # odds: the expected number of cards of each tier in one pack (slot count x outcome chance, spread over its pool)
    $odds = [ordered]@{}
    if ($built.Count) {
      $m = Get-PokeshellBoosterModel $Root $Pack $s
      foreach ($sl in $m.slots) {
        $live = $false
        for ($o = 0; $o -lt $sl.Outcomes.Count; $o++) {
          $pr = $sl.Probability($o); $pool = $sl.Outcomes[$o].Pool
          if ($pr -le 0) { continue }
          $live = $true
          foreach ($ci in $pool) { $t = $m.cards[$ci].tierId; $odds[$t] = [double]$odds[$t] + $sl.Count * $pr / $pool.Length }
        }
        if ($live) { $size += $sl.Count }
      }
    }
    [pscustomobject][ordered]@{
      id = $s.id; name = $s.name; series = $s.series; released = $s.released; cardSets = $cardSets
      cards = $built.Count; inPack = $all.Count; printed = [int]$s.printed; packSize = $size; realPackSize = [int]$s.realPackSize
      openable = $built.Count -gt 0
      price = $(if ($s.price) { [double]$s.price } else { $null }); priceSource = $s.priceSource
      chance = $(if ($null -ne $ch) { [math]::Round($ch, 6) } else { $null }); oneIn = $(if ($ch -gt 0) { [math]::Round(1 / $ch, 1) } else { $null })
      odds = @(foreach ($k in $odds.Keys) { [ordered]@{ tier = $k; weight = [math]::Round($odds[$k], 5) } })
      art = $s.art
      hero = $(if ($s.art.hero) { $h = $Pack.cardIndex[$s.art.hero]; if ($h) { "img/$($Pack.id)/$($h.character)/$($h.id).png" } })
      slots = @($slots | ForEach-Object { [ordered]@{ id = $_.id; count = [int]$(if ($_.count) { $_.count } else { 1 }); finish = $(if ($_.finish) { $_.finish } else { 'normal' }) } })
    }
  }
}
