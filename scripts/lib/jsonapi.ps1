<#
pokeshell's JSON commands, for other tools (README "For other tools"): `pokeshell version --json` and
`pokeshell collection --json [--pack <id>]`. Dot-sourced by scripts\pokeshell.ps1, which provides $Root, $State,
$RuntimeRoot, $Version, $Packaged, Read-Pulls and Get-ShownPulls (the binders' earned rule and card resolution).

Output: one JSON document on stdout, ASCII only (every other character is a \uXXXX escape, so the console code page
can't mangle it). `api` is bumped when a shape changes incompatibly; fields are only ever added.

Empty / seen / caught are the binders' (docs/BINDER_SPEC.md "Empty, seen, caught"): a card is caught once one of its
pulls is earned; seen when it was pulled but every pull is pending or expired; empty (left out) when never pulled.
Pulls of retired art or of cards whose art isn't built are left out, as in the binders (Get-ShownPulls). Gameplay
data (packs\<pack>\carddata.json, tools\build_carddata.py) is given for caught cards only: like the binder's text
half, an uncaught card's moveset stays hidden.
#>

$PokeshellJsonApi = 1
# the JSON commands this pokeshell answers (version --json lists them; add new ones here)
$PokeshellJsonCommands = [Collections.Generic.List[string]]::new()
foreach ($c in 'version --json', 'collection --json') { $PokeshellJsonCommands.Add($c) }

# a JSON string literal (null for $null). HttpUtility.JavaScriptStringEncode is in .NET Framework (System.Web) and in
# .NET (System.Web.HttpUtility), so in both editions; a .NET call is cheap in a loop, a PowerShell function isn't. It
# also escapes ' < > & as \u00xx, which is still JSON.
Add-Type -AssemblyName System.Web
function ConvertTo-PokeshellJsonString($s) {
  if ($null -eq $s) { 'null' } else { [Web.HttpUtility]::JavaScriptStringEncode([string]$s, $true) }
}function ConvertTo-PokeshellJsonList($Items) {
  $parts = foreach ($x in @($Items)) { ConvertTo-PokeshellJsonString $x }
  '[' + (@($parts) -join ',') + ']'
}

# every non-ASCII character as \uXXXX (UTF-16 units: a surrogate pair becomes two escapes, which is valid JSON)
function ConvertTo-PokeshellAsciiJson([string]$Text) {
  $seen = [Collections.Generic.HashSet[char]]::new()
  foreach ($m in [regex]::Matches($Text, '[^\x00-\x7f]')) { [void]$seen.Add($m.Value[0]) }
  foreach ($c in $seen) { $Text = $Text.Replace([string]$c, ('\u{0:x4}' -f [int]$c)) }
  $Text
}

function Write-PokeshellJson([string]$Text) {
  [Console]::Out.Write((ConvertTo-PokeshellAsciiJson $Text) + "`n")
  [Console]::Out.Flush()
}

# packs\<pack>\carddata.json as { card id -> the card's raw JSON object text }. The file keeps one card per line
# (tools\build_carddata.py), so nothing is parsed here: the caught cards' lines are copied into the output as they are.
function Read-PokeshellCardData([string]$Root, [string]$Pack) {
  $map = [Collections.Generic.Dictionary[string, string]]::new([StringComparer]::Ordinal)
  $f = Join-Path $Root "packs\$Pack\carddata.json"
  if (-not [IO.File]::Exists($f)) { return , $map }
  $rx = [regex]'^"((?:[^"\\]|\\.)+)":(\{.*\}),?$'
  foreach ($line in [IO.File]::ReadAllLines($f, [Text.Encoding]::UTF8)) {
    $m = $rx.Match($line)
    if ($m.Success) { $map[$m.Groups[1].Value] = $m.Groups[2].Value }
  }
  , $map
}

function Invoke-PokeshellVersionJson {
  $packs = @(Get-PokeshellPackIds $Root)
  $withData = @($packs | Where-Object { [IO.File]::Exists((Join-Path $Root "packs\$_\carddata.json")) })
  $web = Join-Path $State 'web'
  $features = [Collections.Generic.List[string]]::new()
  foreach ($x in 'collection.caught', 'collection.seen', 'collection.art') { $features.Add($x) }
  if ($withData) { $features.Add('collection.data') }
  $cur = Get-CurrentVersion
  $j = '{"name":"pokeshell"' +
    ',"version":' + (ConvertTo-PokeshellJsonString $Version) +
    ',"api":' + $PokeshellJsonApi +
    ',"root":' + (ConvertTo-PokeshellJsonString $Root) +
    ',"runtimeRoot":' + (ConvertTo-PokeshellJsonString $RuntimeRoot) +
    ',"state":' + (ConvertTo-PokeshellJsonString $State) +
    ',"packaged":' + $(if ($Packaged) { 'true' } else { 'false' }) +
    ',"installedVersion":' + $(if ($cur) { ConvertTo-PokeshellJsonString $cur } else { 'null' }) +
    ',"packs":' + (ConvertTo-PokeshellJsonList $packs) +
    ',"carddata":' + (ConvertTo-PokeshellJsonList $withData) +
    ',"webExport":' + $(if ([IO.File]::Exists((Join-Path $web 'data.json'))) { ConvertTo-PokeshellJsonString $web } else { 'null' }) +
    ',"commands":' + (ConvertTo-PokeshellJsonList $PokeshellJsonCommands) +
    ',"features":' + (ConvertTo-PokeshellJsonList $features) + '}'
  Write-PokeshellJson $j
}

function Invoke-PokeshellCollectionJson([string]$PackFilter) {
  $all = @(Get-PokeshellPackIds $Root)
  if ($PackFilter -and $all -notcontains $PackFilter) { throw "no pack '$PackFilter' (packs: $($all -join ', '))" }
  $shown = @(Get-ShownPulls @(Read-Pulls -All))   # earned, pending and expired; retired / unbuilt art left out
  $packs = $script:ShownPacks                       # the packs Get-ShownPulls read (pack id -> Read-PokeshellPack)
  $slots = [Collections.Generic.Dictionary[string, object]]::new(); $order = [Collections.Generic.List[string]]::new()
  foreach ($x in $shown) {
    if ($PackFilter -and $x.pack -ne $PackFilter) { continue }
    $pk = $packs[$x.pack]
    if (-not $pk -or -not $pk.isCardPack) { continue }   # only real-card packs have cards
    $k = "$($x.pack)/$($x.art)"
    $s = $null
    if (-not $slots.TryGetValue($k, [ref]$s)) {
      $s = @{ pack = $x.pack; id = $x.art; character = $x.character; tier = $x.tier; caught = 0; shiny = 0; new = $false
              first = $null; last = $null; seen = 0; pending = $false; sfirst = $null; slast = $null }
      $slots[$k] = $s; $order.Add($k)
    }
    $t = $x.time
    if ($x.status -eq 'earned') {
      $s.caught++; if ($x.shiny) { $s.shiny++ }; if ($x.new) { $s.new = $true }
      if ($null -eq $s.first -or [string]::CompareOrdinal($t, $s.first) -lt 0) { $s.first = $t }
      if ($null -eq $s.last -or [string]::CompareOrdinal($t, $s.last) -gt 0) { $s.last = $t }
    } else {
      $s.seen++; if ($x.status -eq 'pending') { $s.pending = $true }
      if ($null -eq $s.sfirst -or [string]::CompareOrdinal($t, $s.sfirst) -lt 0) { $s.sfirst = $t }
      if ($null -eq $s.slast -or [string]::CompareOrdinal($t, $s.slast) -gt 0) { $s.slast = $t }
    }
  }
  $J = [Web.HttpUtility]
  # pack.json's card entries by id: a dictionary (looking a property up by name on the parsed JSON costs ~1 ms)
  $raws = @{}
  foreach ($p in $packs.Keys) {
    $m = [Collections.Generic.Dictionary[string, object]]::new([StringComparer]::Ordinal)
    if ($packs[$p] -and $packs[$p].isCardPack -and $packs[$p].cards) { foreach ($c in $packs[$p].cards.PSObject.Properties) { $m[$c.Name] = $c.Value } }
    $raws[$p] = $m
  }
  $data = @{}
  $web = [IO.Path]::Combine($State, 'web\img')
  $caught = [Collections.Generic.List[string]]::new(); $seen = [Collections.Generic.List[string]]::new()
  $nPulls = 0; $nShiny = 0
  foreach ($k in $order) {
    $s = $slots[$k]; $pk = $packs[$s.pack]; $raw = $raws[$s.pack][$s.id]; $ti = $pk.tierIndex[$s.tier]
    $label = if ($null -ne $ti) { [string]$pk.tiers[$ti].label } else { $s.tier }
    $set = $s.id; $dash = $set.LastIndexOf('-'); $set = if ($dash -gt 0) { $set.Substring(0, $dash) } else { '' }
    $head = '{"card":' + $J::JavaScriptStringEncode($s.id, $true) +
      ',"pack":' + $J::JavaScriptStringEncode($s.pack, $true) +
      ',"character":' + $J::JavaScriptStringEncode($s.character, $true) +
      ',"name":' + $J::JavaScriptStringEncode([string]$raw.name, $true) +
      ',"set":' + $J::JavaScriptStringEncode($set, $true) +
      ',"setName":' + $J::JavaScriptStringEncode([string]$raw.set, $true) +
      ',"number":' + $J::JavaScriptStringEncode([string]$raw.number, $true) +
      ',"rarity":' + $J::JavaScriptStringEncode([string]$raw.rarity, $true) +
      ',"tier":' + $J::JavaScriptStringEncode($s.tier, $true) +
      ',"tierLabel":' + $J::JavaScriptStringEncode($label, $true) +
      ',"tierRank":' + $(if ($null -ne $ti) { $ti } else { 'null' })
    if (-not $s.caught) {
      $seen.Add($head + ',"caught":false,"count":' + $s.seen + ',"pending":' + $(if ($s.pending) { 'true' } else { 'false' }) +
        ',"firstSeen":' + $J::JavaScriptStringEncode($s.sfirst, $true) + ',"lastSeen":' + $J::JavaScriptStringEncode($s.slast, $true) + '}')
      continue
    }
    $nPulls += $s.caught; $nShiny += $s.shiny
    if (-not $data.ContainsKey($s.pack)) { $data[$s.pack] = Read-PokeshellCardData $Root $s.pack }
    $d = $null; [void]$data[$s.pack].TryGetValue($s.id, [ref]$d)
    $stem = "$($s.character)-$($s.id)"
    $ans = [IO.Path]::Combine($Root, "dist\$($s.pack)\$stem.ans"); $ansS = [IO.Path]::Combine($Root, "dist\$($s.pack)\$stem-shiny.ans")
    $png = [IO.Path]::Combine($web, "$($s.pack)\$($s.character)\$($s.id).png"); $pngS = [IO.Path]::Combine($web, "$($s.pack)\$($s.character)\$($s.id)-shiny.png")
    $rel = "$($s.pack)/$($s.character)/$($s.id)"
    $hasPng = [IO.File]::Exists($png); $hasPngS = [IO.File]::Exists($pngS)
    $art = '{"ans":' + $(if ([IO.File]::Exists($ans)) { $J::JavaScriptStringEncode($ans, $true) } else { 'null' }) +
      ',"ansShiny":' + $(if ([IO.File]::Exists($ansS)) { $J::JavaScriptStringEncode($ansS, $true) } else { 'null' }) +
      ',"png":' + $(if ($hasPng) { $J::JavaScriptStringEncode($png, $true) } else { 'null' }) +
      ',"pngShiny":' + $(if ($hasPngS) { $J::JavaScriptStringEncode($pngS, $true) } else { 'null' }) +
      ',"img":' + $(if ($hasPng) { $J::JavaScriptStringEncode("$rel.png", $true) } else { 'null' }) +
      ',"imgShiny":' + $(if ($hasPngS) { $J::JavaScriptStringEncode("$rel-shiny.png", $true) } else { 'null' }) + '}'
    $caught.Add($head + ',"caught":true' +
      ',"count":' + $s.caught + ',"shinyCount":' + $s.shiny + ',"shiny":' + $(if ($s.shiny) { 'true' } else { 'false' }) +
      ',"new":' + $(if ($s.new) { 'true' } else { 'false' }) +
      ',"firstCaught":' + $J::JavaScriptStringEncode($s.first, $true) + ',"lastCaught":' + $J::JavaScriptStringEncode($s.last, $true) +
      ',"art":' + $art + ',"data":' + $(if ($d) { $d } else { 'null' }) + '}')
  }
  $sb = [Text.StringBuilder]::new()
  [void]$sb.Append('{"api":').Append($PokeshellJsonApi)
  [void]$sb.Append(',"version":').Append((ConvertTo-PokeshellJsonString $Version))
  [void]$sb.Append(',"state":').Append((ConvertTo-PokeshellJsonString $State))
  [void]$sb.Append(',"pack":').Append($(if ($PackFilter) { ConvertTo-PokeshellJsonString $PackFilter } else { 'null' }))
  [void]$sb.Append(',"counts":{"caught":').Append($caught.Count).Append(',"seen":').Append($seen.Count)
  [void]$sb.Append(',"pulls":').Append($nPulls).Append(',"shiny":').Append($nShiny).Append('}')
  [void]$sb.Append(",`n`"cards`":[`n").Append(($caught -join ",`n")).Append("`n]")
  [void]$sb.Append(",`n`"seen`":[`n").Append(($seen -join ",`n")).Append("`n]}")
  Write-PokeshellJson $sb.ToString()
}