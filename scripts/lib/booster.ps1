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

# The effect family the opening scene (and the terminal reveal) shows for a card: a tier's default, an outcome's
# "fx" overrides it, a reverse-holo slot makes a non-foil card "reverse". "hit" (0-5) is how big the reveal is.
$script:BoosterFx = @{
  'common' = 'plain'; 'uncommon' = 'plain'; 'rare' = 'plain'
  'rare-holo' = 'holo'; 'promo' = 'holo'; 'trainer-gallery-rare-holo' = 'holo'; 'pikachu-rare' = 'holo'
  'rare-holo-v' = 'holo'; 'rare-holo-vmax' = 'holo'; 'rare-holo-vstar' = 'holo'; 'rare-holo-gx' = 'holo'; 'rare-holo-ex' = 'holo'
  'double-rare' = 'holo'; 'rare-holo-lv-x' = 'holo'; 'rare-prime' = 'holo'; 'rare-break' = 'holo'; 'legend' = 'holo'
  'rare-holo-star' = 'holo'; 'rare-prism-star' = 'holo'; 'ace-spec-rare' = 'holo'; 'futuristic-rare' = 'holo'
  'rare-ultra' = 'full-art'; 'ultra-rare' = 'full-art'; 'illustration-rare' = 'full-art'
  'special-illustration-rare' = 'alt-art'
  'rare-rainbow' = 'rainbow'; 'shiny-ultra-rare' = 'rainbow'
  'rare-secret' = 'gold'; 'hyper-rare' = 'gold'
  'radiant-rare' = 'radiant'; 'amazing-rare' = 'radiant'; 'rare-shining' = 'radiant'
  'rare-shiny' = 'shiny'; 'rare-shiny-gx' = 'shiny'; 'shiny-rare' = 'shiny'
}
$script:BoosterHit = @{ plain = 0; reverse = 1; holo = 2; 'full-art' = 3; radiant = 3; shiny = 3; 'alt-art' = 4; rainbow = 4; gold = 5 }

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
  $raw = [IO.File]::ReadAllText((Join-Path $Pack.dir 'pack.json'), [Text.Encoding]::UTF8) | ConvertFrom-Json
  $cardSets = @($Set.cardSets)
  $cards = [Collections.Generic.List[object]]::new()
  foreach ($c in $Pack.cardList) {
    if ($cardSets -notcontains (Get-PokeshellCardSet $c.id)) { continue }
    if (-not (Test-PokeshellCardBuilt $Root $Pack.id $c)) { continue }
    $e = $raw.cards.($c.id)
    $cards.Add([pscustomobject]@{ id = $c.id; character = $c.character; name = $c.name; number = $c.tag; tier = $c.tier; tierId = $c.tierId
                                  rarity = [string]$e.rarity; set = [string]$e.set })
  }
  $slots = [Collections.Generic.List[Pokeshell.BoosterSlot]]::new(); $meta = @()
  foreach ($s in @($Set.slots)) {
    $slot = [Pokeshell.BoosterSlot]::new()
    $slot.Id = [string]$s.id; $slot.Count = [int]$(if ($s.count) { $s.count } else { 1 })
    $slot.Finish = [string]$(if ($s.finish) { $s.finish } else { 'normal' })
    $om = @(); $missing = 0.0; $baseAt = -1
    foreach ($pk in @($s.pick)) {
      $pool = [int[]]@(for ($i = 0; $i -lt $cards.Count; $i++) { if (Test-PokeshellCardMatch $cards[$i] $pk $cardSets) { $i } })
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
function Get-PokeshellTokenBalance([string]$StateDir) { $b = 0; foreach ($t in Get-PokeshellTokenLines $StateDir) { $b += $t.delta }; $b }

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
# card ids you have caught (earned pulls, resolved the way the binders do)
function Get-PokeshellCaughtCards([string]$StateDir, $Pack) {
  $set = @{}
  foreach ($r in [Pokeshell.Core]::ReadPulls($StateDir, [DateTime]::UtcNow.Ticks, [Pokeshell.Core]::BootId())) {
    if ($r.Status -ne 'earned' -or $r.Pack -ne $Pack.id) { continue }
    $c = Resolve-PokeshellPull $Pack $r.Character $r.Tier $r.Art
    if ($c -and $c -ne 'legacy') { $set[$c.id] = $true }
  }
  $set
}

<#
Roll one pack of $Set, record every card into pulls.log (caught at once: a pack is already earned) and return the
result: { set, packId, cards: [...] } with the cards in reveal order (rarest last). -NoRecord: roll only.
#>
function Open-PokeshellBooster([string]$Root, [string]$StateDir, $Pack, $Set, $Rng, [switch]$NoRecord) {
  Import-PokeshellBooster $StateDir
  $m = Get-PokeshellBoosterModel $Root $Pack $Set
  if (-not $m.cards.Count) { throw "no cards of $($Set.name) are served yet (its art isn't built), so it can't be opened" }
  if (-not $Rng) { $Rng = [Pokeshell.BoosterRng]::new() }
  $picks = [Pokeshell.Booster]::Roll($m.slots, $Rng)
  $caught = Get-PokeshellCaughtCards $StateDir $Pack
  $shinyChance = [double]$Pack.shiny_chance
  $printedShiny = @{}; for ($i = 0; $i -lt @($Pack.tiers).Count; $i++) { if ($Pack.tiers[$i].shiny -eq 'printed') { $printedShiny[$i] = $true } }
  $now = [DateTime]::UtcNow.Ticks
  $packId = [Pokeshell.Core]::NewPullId($now)
  $stamp = [DateTime]::new($now, [DateTimeKind]::Utc).ToLocalTime().ToString('s', [Globalization.CultureInfo]::InvariantCulture)
  $boot = [Pokeshell.Core]::BootId()
  $n = 0
  $out = foreach ($p in $picks) {
    $c = $m.cards[$p.Card]; $om = $m.meta[$p.Slot][$p.Outcome]
    $roll = $Rng.NextDouble()   # always drawn, so a seeded pack stays in step
    $shiny = $roll -lt $shinyChance -and -not $printedShiny[$c.tier] -and [IO.File]::Exists((Join-Path $Root "dist\$($Pack.id)\$($c.character)-$($c.id)-shiny.ans"))
    $fx = if ($om.fx) { $om.fx } elseif ($script:BoosterFx.ContainsKey($c.tierId)) { $script:BoosterFx[$c.tierId] } else { 'holo' }
    if ($p.Finish -ne 'normal' -and $fx -eq 'plain') { $fx = 'reverse' }   # a foil print of a non-foil card (reverse holo, 30th's foil commons)
    $hit = $script:BoosterHit[$fx]; if ($fx -eq 'plain' -and $c.tierId -eq 'rare') { $hit = 1 }   # the rare slot's floor still comes last
    if ($shiny) { $hit = [math]::Min(5, $hit + 1) }
    $prob = $m.slots[$p.Slot].Probability($p.Outcome)
    $isNew = -not $caught[$c.id]; $caught[$c.id] = $true   # a second copy in the same pack isn't new
    [pscustomobject][ordered]@{
      id = $c.id; name = $c.name; number = $c.number; rarity = $c.rarity; tier = $c.tierId; tierLabel = $Pack.tiers[$c.tier].label
      slot = $p.SlotId; outcome = $p.Label; finish = $p.Finish; fx = $fx; hit = $hit; shiny = [bool]$shiny; isNew = $isNew
      oneIn = $(if ($prob -gt 0) { [math]::Round(1 / $prob, 1) } else { 0 })
      character = $c.character; setName = $c.set
      image = "img/$($Pack.id)/$($c.character)/$($c.id)$(if ($shiny) { '-shiny' }).png"
      order = $n++; tierIndex = $c.tier; pullId = ''
    }
  }
  # reveal order, rarest last: by the odds of the kind of hit (the outcome's per-pack chance, lower = later), then
  # the effect, then the slot order printed packs have (commons first, rare at the back)
  $sorted = @($out | Sort-Object @{ e = { $_.hit + $(if ($_.shiny) { 0.5 } else { 0 }) } }, @{ e = { $_.oneIn } }, @{ e = { $_.order } })
  if (-not $NoRecord) {
    $lines = foreach ($x in $sorted) {
      $x.pullId = [Pokeshell.Core]::NewPullId($now)
      # a caught pull (no "pending" flag): pulls.log's columns, plus where it came from
      "$stamp`t$($Pack.id)`t$($x.character)`t$($x.tier)`t$($x.id)`t`t$(if ($x.shiny) { '1' } else { '0' })`tbooster:$($Set.id)`tid=$($x.pullId)`tboot=$boot`tcard=$($x.id)`tbooster=$packId`tslot=$($x.slot)`tfinish=$($x.finish)"
    }
    [void][IO.Directory]::CreateDirectory($StateDir)
    [IO.File]::AppendAllText((Join-Path $StateDir 'pulls.log'), (($lines -join "`r`n") + "`r`n"), [Text.UTF8Encoding]::new($false))
  }
  foreach ($x in $sorted) { $x.PSObject.Properties.Remove('order'); $x.PSObject.Properties.Remove('tierIndex') }
  [pscustomobject][ordered]@{ set = $Set.id; setName = $Set.name; packId = $packId; secure = $Rng.Secure; cards = $sorted }
}

# ---------------------------------------------------------------- listing
function Get-PokeshellBoosterSets([string]$Root, $Pack, $Boosters) {
  foreach ($s in @($Boosters.sets)) {
    $cardSets = @($s.cardSets)
    $all = @($Pack.cardList | Where-Object { $cardSets -contains (Get-PokeshellCardSet $_.id) })
    $built = @($all | Where-Object { Test-PokeshellCardBuilt $Root $Pack.id $_ })
    $slots = @($s.slots); $size = 0; foreach ($x in $slots) { $size += [int]$(if ($x.count) { $x.count } else { 1 }) }
    [pscustomobject][ordered]@{
      id = $s.id; name = $s.name; series = $s.series; released = $s.released; cardSets = $cardSets
      cards = $built.Count; inPack = $all.Count; printed = [int]$s.printed; packSize = $size; realPackSize = [int]$s.realPackSize
      openable = $built.Count -gt 0
      art = $s.art
      hero = $(if ($s.art.hero) { $h = $Pack.cardIndex[$s.art.hero]; if ($h) { "img/$($Pack.id)/$($h.character)/$($h.id).png" } })
      slots = @($slots | ForEach-Object { [ordered]@{ id = $_.id; count = [int]$(if ($_.count) { $_.count } else { 1 }); finish = $(if ($_.finish) { $_.finish } else { 'normal' }) } })
    }
  }
}
