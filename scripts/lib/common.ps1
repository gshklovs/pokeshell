<#
pokeshell shared helpers (not on the startup hot path): pack loading, the roll cache, skin GUIDs, config.
Loads roll.ps1 (state dir, the compiled core) if it isn't loaded yet.
#>
if (-not (Get-Command Import-PokeshellCore -ErrorAction SilentlyContinue)) { . (Join-Path $PSScriptRoot 'roll.ps1') }

function Read-PokeshellConfig([string]$StateDir) { Import-PokeshellCore $StateDir; , [Pokeshell.Core]::ReadConfig($StateDir) }   # , = don't unroll the dictionary
function Write-PokeshellLog([string]$StateDir, [string]$File, [string]$Line) { Import-PokeshellCore $StateDir; [Pokeshell.Core]::Log($StateDir, $File, $Line) }

$PokeshellProfilePrefix = 'pokeshell: '

function Get-PokeshellPackIds([string]$Root) {
  Get-ChildItem (Join-Path $Root 'packs') -Directory -ErrorAction SilentlyContinue |
    Where-Object { Test-Path (Join-Path $_.FullName 'pack.json') } | ForEach-Object Name | Sort-Object
}

function ConvertTo-PokeshellTitle([string]$Id) {
  (($Id -split '[-_]') | ForEach-Object { if ($_) { $_.Substring(0, 1).ToUpper() + $_.Substring(1) } }) -join ' '
}

# pack.json + display names: pack.json "names" {id: name}, else art/<id>.json, else a title-cased id.
# Optional pack.json "tags" {id: text} (shown on a card frame's top edge, e.g. a dex number), the frame-style
# texts "poster_names" and "bounties" {id: text} (the wanted style's full name and bounty) and per-tier
# "frame" are normalized to .tags, .posterNames, .bounties and .frames. A frame is a preset name or a list of
# #rrggbb gradient stops (kept as "a,b,..."), or a style object ({ "style": "wanted", "palette": "manga" },
# kept as "wanted;palette=manga;seed=<tier id>": the one string the roll cache and the core pass around).
#
# Real-card packs (pack.json "cards": { "<pokemontcg.io id>": { character, tier, name, number, ... } }) are normalized
# too: .isCardPack, .cardList ({ id, character, tier (index), tierId, name, tag } in pack.json order), .cardIndex
# (id -> card), .tierIndex (tier id -> index), .retired (old "character/tier" -> card id or $null), and .characters
# (the cards' characters, when pack.json doesn't list them). A card is built when its dist .ans exists (Test-PokeshellCardBuilt).
function Read-PokeshellPack([string]$Root, [string]$Id) {
  $dir = Join-Path $Root "packs\$Id"
  $pack = [IO.File]::ReadAllText((Join-Path $dir 'pack.json'), [Text.Encoding]::UTF8) | ConvertFrom-Json
  $isCards = [bool]$pack.PSObject.Properties['cards']
  $tierIx = @{}; $tl = @($pack.tiers); for ($i = 0; $i -lt $tl.Count; $i++) { $tierIx[[string]$tl[$i].id] = $i }
  $cardList = @(); $cardIndex = @{}; $retired = @{}
  if ($isCards) {
    $order = [Collections.Generic.List[string]]::new()
    if ($pack.cards) {
      foreach ($p in $pack.cards.PSObject.Properties) {
        $c = $p.Value; $ti = $tierIx[[string]$c.tier]
        if ($null -eq $ti) { throw "pack $Id, card $($p.Name): no tier '$($c.tier)' in pack.json" }
        $card = [pscustomobject]@{ id = $p.Name; character = [string]$c.character; tier = $ti; tierId = [string]$c.tier
                                  name = [string]$c.name; tag = [string]$c.number }
        $cardList += $card; $cardIndex[$p.Name] = $card
        if (-not $order.Contains($card.character)) { $order.Add($card.character) }
      }
    }
    if (-not $pack.characters) { $pack | Add-Member -NotePropertyName characters -NotePropertyValue @($order) -Force }
    if ($pack.retired) { foreach ($p in $pack.retired.PSObject.Properties) { $retired[$p.Name] = $(if ($p.Value) { [string]$p.Value } else { $null }) } }
  }
  $given = @{}; if ($pack.names) { foreach ($p in $pack.names.PSObject.Properties) { $given[$p.Name] = [string]$p.Value } }
  $tags = @{}; if ($pack.tags) { foreach ($p in $pack.tags.PSObject.Properties) { $tags[$p.Name] = [string]$p.Value } }
  $posters = @{}; if ($pack.poster_names) { foreach ($p in $pack.poster_names.PSObject.Properties) { $posters[$p.Name] = [string]$p.Value } }
  $bounties = @{}; if ($pack.bounties) { foreach ($p in $pack.bounties.PSObject.Properties) { $bounties[$p.Name] = [string]$p.Value } }
  $names = [ordered]@{}
  foreach ($c in $pack.characters) {
    $name = $given[$c]
    if (-not $name) {
      $artFile = Join-Path $dir "art\$c.json"
      if (Test-Path $artFile) { try { $name = (Get-Content $artFile -Raw -Encoding UTF8 | ConvertFrom-Json).name } catch { } }
    }
    $names[$c] = if ($name) { $name } else { ConvertTo-PokeshellTitle $c }
  }
  $frames = @(foreach ($t in @($pack.tiers)) {
    $f = $t.frame
    if (-not $f) { '' }
    elseif ($f -is [Management.Automation.PSCustomObject]) {
      if (-not $f.style) { throw "pack $Id, tier $($t.id): a frame object needs a style" }
      $kv = @("$($f.style)".Trim())
      foreach ($p in $f.PSObject.Properties) { if ($p.Name -ne 'style') { $kv += "$($p.Name)=$("$($p.Value)" -replace '[;\s]+', ' ')".Trim() } }
      if (-not $f.seed) { $kv += "seed=$($t.id)" }   # the stain / edge pattern: per tier unless the pack says otherwise
      $kv -join ';'
    }
    else { (@($f) | ForEach-Object { "$_".Trim() }) -join ',' }
  })
  $pack | Add-Member -NotePropertyName names -NotePropertyValue $names -Force
  $pack | Add-Member -NotePropertyName tags -NotePropertyValue $tags -Force
  $pack | Add-Member -NotePropertyName posterNames -NotePropertyValue $posters -Force
  $pack | Add-Member -NotePropertyName bounties -NotePropertyValue $bounties -Force
  $pack | Add-Member -NotePropertyName frames -NotePropertyValue $frames -Force
  $pack | Add-Member -NotePropertyName dir -NotePropertyValue $dir -Force
  $pack | Add-Member -NotePropertyName isCardPack -NotePropertyValue $isCards -Force
  $pack | Add-Member -NotePropertyName cardList -NotePropertyValue $cardList -Force
  $pack | Add-Member -NotePropertyName cardIndex -NotePropertyValue $cardIndex -Force
  $pack | Add-Member -NotePropertyName tierIndex -NotePropertyValue $tierIx -Force
  $pack | Add-Member -NotePropertyName retired -NotePropertyValue $retired -Force
  $pack
}

# a real card's prebuilt art: dist\<pack>\<character>-<card id>.ans (tools\build_realcards.py); cards without it never roll
function Test-PokeshellCardBuilt([string]$Root, [string]$Pack, $Card) {
  [IO.File]::Exists((Join-Path $Root "dist\$Pack\$($Card.character)-$($Card.id).ans"))
}

<#
What a pulls.log line shows today, for the binders: the real card it resolves to, or $null (hide it).
  - packs without "cards": every pull shows as logged ('legacy' is returned)
  - the art column is a card id of this pack (and the character matches): that card
  - else pack.json "retired" names the old character/tier: its card id (e.g. an old common -> the base-set common), or null
  - anything else doesn't resolve to a current real card: hidden
  - a card whose art isn't built (Test-PokeshellCardBuilt) is muted: it counts as absent from the pack, so a pull
    resolving to it is hidden too, until it is built
Mirrored by binder-tui / the web export (docs/PACK_FORMAT.md, "retired").
#>
function Resolve-PokeshellPull($Pack, [string]$Character, [string]$Tier, [string]$Art) {
  if (-not $Pack.isCardPack) { return 'legacy' }
  $root = Split-Path (Split-Path $Pack.dir); $id = Split-Path -Leaf $Pack.dir
  $c = $Pack.cardIndex[$Art]
  if ($c -and $c.character -eq $Character -and (Test-PokeshellCardBuilt $root $id $c)) { return $c }
  $k = "$Character/$Tier"
  $c = if ($Pack.retired.ContainsKey($k) -and $Pack.retired[$k]) { $Pack.cardIndex[$Pack.retired[$k]] }
  if ($c -and (Test-PokeshellCardBuilt $root $id $c)) { return $c }
  $null
}

# WT profile GUID for a skin: .NET Guid(md5("pokeshell:<pack>/<skin>")), stable across installs
function Get-PokeshellSkinGuid([string]$Pack, [string]$Skin) {
  $h = [Security.Cryptography.MD5]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes("pokeshell:$Pack/$Skin"))
  '{' + ([guid]::new($h)).ToString() + '}'
}

# every shader of every pack: pack, skin, tier index, weight, shader path, guid
function Get-PokeshellSkins([string]$Root) {
  foreach ($id in Get-PokeshellPackIds $Root) {
    $pack = Read-PokeshellPack $Root $id
    $seen = @{}
    for ($i = 1; $i -lt @($pack.tiers).Count; $i++) {
      $t = $pack.tiers[$i]
      foreach ($prop in $t.skins.PSObject.Properties) {
        if ($seen[$prop.Name]) { continue }   # a skin several tiers share is one profile (its first tier here)
        $seen[$prop.Name] = $true
        [pscustomobject]@{ pack = $id; skin = $prop.Name; tier = $i; tierId = $t.id; label = $t.label; weight = [int]$prop.Value
          shader = Join-Path $pack.dir "shaders\$($prop.Name).hlsl"; guid = Get-PokeshellSkinGuid $id $prop.Name }
      }
    }
    # shaders that no tier references can still be opened with `pokeshell holo`, they just never drop
    foreach ($f in Get-ChildItem (Join-Path $pack.dir 'shaders') -Filter *.hlsl -ErrorAction SilentlyContinue) {
      if (-not $seen[$f.BaseName]) {
        [pscustomobject]@{ pack = $id; skin = $f.BaseName; tier = 0; tierId = ''; label = ''; weight = 0
          shader = $f.FullName; guid = Get-PokeshellSkinGuid $id $f.BaseName }
      }
    }
  }
}

function Get-PokeshellInstalled([string]$StateDir) {
  $f = Join-Path $StateDir 'installed.tsv'
  if (-not (Test-Path $f)) { return @() }
  foreach ($line in [IO.File]::ReadAllLines($f)) {
    $x = $line.Split("`t")
    if ($x.Count -ge 3 -and -not $line.StartsWith('#')) { [pscustomobject]@{ pack = $x[0]; skin = $x[1]; guid = $x[2]; settings = $(if ($x.Count -ge 4) { $x[3] } else { '' }) } }
  }
}

function Set-PokeshellConfigValue([string]$StateDir, [string]$Key, [string]$Value) {
  [void][IO.Directory]::CreateDirectory($StateDir)
  $p = Join-Path $StateDir 'config.txt'
  $lines = [Collections.Generic.List[string]]::new()
  if (Test-Path $p) { foreach ($l in [IO.File]::ReadAllLines($p)) { if ($l -notmatch "^\s*$([regex]::Escape($Key))\s*=") { $lines.Add($l) } } }
  else { $lines.Add('# pokeshell settings (key=value); see README') }
  $lines.Add("$Key=$Value")
  [IO.File]::WriteAllLines($p, $lines.ToArray())
}

<#
Write %LOCALAPPDATA%\pokeshell\roll.tsv for the selected pack(s): the flat table the startup hook reads.
Only skins recorded in installed.tsv are included, so before `pokeshell install` every pull is a common.
Line 1 stamps the inputs' mtimes; the hook rebuilds the cache when any of them changes.
#>
function Update-PokeshellRollCache([string]$Root, [string]$StateDir, [hashtable]$Cfg) {
  if (-not $Cfg) { $Cfg = Read-PokeshellConfig $StateDir }
  [void][IO.Directory]::CreateDirectory($StateDir)
  $all = @(Get-PokeshellPackIds $Root)
  $sel = if ($Cfg.pack -eq 'all') { $all } elseif ($all -contains $Cfg.pack) { @($Cfg.pack) } else { @($all | Select-Object -First 1) }
  $installed = @{}
  foreach ($i in Get-PokeshellInstalled $StateDir) { $installed["$($i.pack)/$($i.skin)"] = $i.guid }
  $inv = [Globalization.CultureInfo]::InvariantCulture

  $stampFiles = @((Join-Path $StateDir 'config.txt'), (Join-Path $StateDir 'installed.tsv'), (Join-Path $Root 'packs'))
  $body = New-Object System.Collections.Generic.List[string]
  $body.Add("select`t$($Cfg.pack)")
  foreach ($id in $sel) {
    $pack = Read-PokeshellPack $Root $id
    $stampFiles += (Join-Path $pack.dir 'pack.json'), (Join-Path $pack.dir 'art')
    $body.Add("pack`t$id`t$(([double]$pack.foil_chance).ToString($inv))`t$(([double]$pack.shiny_chance).ToString($inv))")
    if ($pack.isCardPack) { Add-PokeshellCardRows $Root $id $pack $body $installed; $stampFiles += (Join-Path $Root "dist\$id"); continue }
    foreach ($c in $pack.characters) {
      # char id name [tag [poster bounty]] (trailing empty columns left off)
      $cols = @("char", $c, $pack.names[$c], $pack.tags[$c], $pack.posterNames[$c], $pack.bounties[$c])
      $n = $cols.Count; while ($n -gt 3 -and -not $cols[$n - 1]) { $n-- }
      $body.Add(($cols[0..($n - 1)] | ForEach-Object { "$_" }) -join "`t")
    }
    $tiers = @($pack.tiers)
    for ($i = 0; $i -lt $tiers.Count; $i++) {
      $t = $tiers[$i]
      $body.Add("tier`t$($t.id)`t$($t.label)`t$($t.art)$(if ($pack.frames[$i]) { "`t$($pack.frames[$i])" })")
      if ($t.shiny -eq 'printed') { $body.Add("printed`t$i") }
      if ($i -eq 0) { continue }
      foreach ($prop in $t.skins.PSObject.Properties) {
        $g = $installed["$id/$($prop.Name)"]
        if ($g -and [int]$prop.Value -gt 0) { $body.Add("skin`t$($prop.Name)`t$([int]$prop.Value)`t$i`t$g") }
      }
    }
  }
  $stamp = 'stamp' + (($stampFiles | ForEach-Object { "`t$_|$([IO.File]::GetLastWriteTimeUtc($_).Ticks)" }) -join '')
  $tmp = Join-Path $StateDir "roll.tsv.$PID.tmp"
  [IO.File]::WriteAllLines($tmp, [string[]](@($stamp) + $body))
  Move-Item -Force $tmp (Join-Path $StateDir 'roll.tsv')
}

<#
roll.tsv rows of a real-card pack (the core's card mode, Pokeshell.cs):
  tier  id label art [frame]                  every tier, by index (art is unused: each card is its own art)
  printed <tier index>                        a tier whose cards print the shiny Pokemon (pack.json tier "shiny":
                                              "printed": Shiny Vault, Radiant): the shiny roll never applies to it
  odds  <tier index> <weight>                 only tiers with at least one built card: a tier is rolled by weight
                                              among these, so an empty tier never rolls (its odds go to the others)
  card  <tier index> <character> <name> <card id> [tag]    every built card; one is picked uniformly in the tier
  skin  name weight <tier index> guid         installed skins of any tier (a tier with none prints in the plain tab)
#>
function Add-PokeshellCardRows([string]$Root, [string]$Id, $Pack, $Body, [hashtable]$Installed) {
  $tiers = @($Pack.tiers)
  $built = @($Pack.cardList | Where-Object { Test-PokeshellCardBuilt $Root $Id $_ })
  for ($i = 0; $i -lt $tiers.Count; $i++) {
    $t = $tiers[$i]
    $Body.Add("tier`t$($t.id)`t$($t.label)`t$($t.art)$(if ($Pack.frames[$i]) { "`t$($Pack.frames[$i])" })")
    if ($t.shiny -eq 'printed') { $Body.Add("printed`t$i") }
    $w = [int]$t.weight
    if ($w -gt 0 -and @($built | Where-Object { $_.tier -eq $i }).Count -gt 0) { $Body.Add("odds`t$i`t$w") }
    foreach ($prop in $t.skins.PSObject.Properties) {
      $g = $Installed["$Id/$($prop.Name)"]
      if ($g -and [int]$prop.Value -gt 0) { $Body.Add("skin`t$($prop.Name)`t$([int]$prop.Value)`t$i`t$g") }
    }
  }
  foreach ($c in $built) {
    $name = if ($c.name) { $c.name } else { $Pack.names[$c.character] }
    $Body.Add("card`t$($c.tier)`t$($c.character)`t$name`t$($c.id)$(if ($c.tag) { "`t$($c.tag)" })")
  }
}

<#
The runtime a new tab needs, as (from, to) pairs relative to a module/checkout root: the $PROFILE hook and
its lib, the core's source (its mtime names the compiled DLL), the command shim, pack.json + art names,
shaders, and the prebuilt art.
#>
function Get-PokeshellRuntimeFiles([string]$Root) {
  $rel = 'scripts\pokeshell-profile.ps1', 'scripts\tab-color-watch.ps1', 'scripts\pokeshell.cmd',
         'scripts\lib\roll.ps1', 'scripts\lib\common.ps1', 'scripts\lib\Pokeshell.cs', 'scripts\lib\anim.ps1', 'scripts\lib\Anim.cs'
  foreach ($r in $rel) { [pscustomobject]@{ from = Join-Path $Root $r; to = $r } }
  [pscustomobject]@{ from = Join-Path $Root 'scripts\lib\pokeshell-shim.ps1'; to = 'scripts\pokeshell.ps1' }
  # a prebuilt binder app and its link launcher next to the scripts, if the package has them: the hotkey and the
  # pokeshell:// handler then point into <state>\current, which survives Update-Module
  foreach ($r in 'bin\binder.exe', 'bin\binder-link.exe') { if ([IO.File]::Exists((Join-Path $Root $r))) { [pscustomobject]@{ from = Join-Path $Root $r; to = $r } } }
  foreach ($id in Get-PokeshellPackIds $Root) {
    $pd = Join-Path $Root "packs\$id"
    [pscustomobject]@{ from = Join-Path $pd 'pack.json'; to = "packs\$id\pack.json" }
    foreach ($sub in @(@('art', '*.json'), @('shaders', '*.hlsl'))) {
      foreach ($f in Get-ChildItem (Join-Path $pd $sub[0]) -Filter $sub[1] -File -ErrorAction SilentlyContinue) {
        [pscustomobject]@{ from = $f.FullName; to = "packs\$id\$($sub[0])\$($f.Name)" }
      }
    }
    foreach ($f in Get-ChildItem (Join-Path $Root "dist\$id") -Filter *.ans -File -ErrorAction SilentlyContinue) {
      [pscustomobject]@{ from = $f.FullName; to = "dist\$id\$($f.Name)" }
    }
    foreach ($f in Get-ChildItem (Join-Path $Root "dist\$id") -Filter *.anim -File -ErrorAction SilentlyContinue) {   # effect loops (lib\anim.ps1)
      [pscustomobject]@{ from = $f.FullName; to = "dist\$id\$($f.Name)" }
    }
  }
}

<#
Copy the runtime from $Root (an installed module version) into <state>\current, the stable folder that
the $PROFILE line and the Windows Terminal shader profiles point at, so they survive Update-Module and the
removal of old module versions. Built next to it and swapped in with two renames; if something holds a
file in the old folder open, it is mirrored in place instead. Returns the folder.
#>
function Sync-PokeshellRuntime([string]$Root, [string]$StateDir, [string]$Version) {
  $cur = Join-Path $StateDir 'current'
  foreach ($d in Get-ChildItem $StateDir -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^current\.(new|old)-' }) { try { $d.Delete($true) } catch { } }
  $new = Join-Path $StateDir "current.new-$PID"
  foreach ($f in Get-PokeshellRuntimeFiles $Root) {
    if (-not [IO.File]::Exists($f.from)) { throw "runtime file missing: $($f.from)" }
    $to = Join-Path $new $f.to
    [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($to))
    [IO.File]::Copy($f.from, $to, $true)
    [IO.File]::SetLastWriteTimeUtc($to, [IO.File]::GetLastWriteTimeUtc($f.from))   # the core DLL's name follows Pokeshell.cs's mtime
  }
  [IO.File]::WriteAllText((Join-Path $new 'version.txt'), $Version)
  [IO.File]::WriteAllText((Join-Path $new 'module-base.txt'), $Root)
  $old = $null
  if ([IO.Directory]::Exists($cur)) {
    $old = Join-Path $StateDir "current.old-$PID"
    try { [IO.Directory]::Move($cur, $old) }
    catch {
      $old = $null
      $keep = @{}
      foreach ($f in Get-ChildItem $new -Recurse -File) {
        $rel = $f.FullName.Substring($new.Length + 1); $keep[$rel] = $true
        $to = Join-Path $cur $rel
        [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($to))
        [IO.File]::Copy($f.FullName, $to, $true); [IO.File]::SetLastWriteTimeUtc($to, $f.LastWriteTimeUtc)
      }
      foreach ($f in Get-ChildItem $cur -Recurse -File) { if (-not $keep[$f.FullName.Substring($cur.Length + 1)]) { try { $f.Delete() } catch { } } }
      try { [IO.Directory]::Delete($new, $true) } catch { }
      return $cur
    }
  }
  [IO.Directory]::Move($new, $cur)
  if ($old) { try { [IO.Directory]::Delete($old, $true) } catch { } }
  $cur
}

<#
The binder app (binder\, Rust): $env:POKESHELL_BINDER if set (tests point it at a missing file), else a prebuilt
bin\binder.exe next to the scripts, else the cargo build in binder\target\release. $null when there is none.
#>
function Get-PokeshellBinderExe([string]$Root) {
  if ($env:POKESHELL_BINDER) { if ([IO.File]::Exists($env:POKESHELL_BINDER)) { return $env:POKESHELL_BINDER } else { return $null } }
  foreach ($p in (Join-Path $Root 'bin\binder.exe'), (Join-Path $Root 'binder\target\release\binder.exe')) { if ([IO.File]::Exists($p)) { return $p } }
  $null
}

# the command line that opens the binder (hotkey pane) or binder-link (pokeshell:// handler); --state only when it isn't the default
function Get-PokeshellBinderCommand([string]$Exe, [string]$Root, [string]$StateDir, [string]$Extra = '') {
  $c = "`"$Exe`" --root `"$Root`""
  if ($env:POKESHELL_HOME) { $c += " --state `"$StateDir`"" }
  if ($Extra) { $c += " $Extra" }
  $c
}

# binder-link.exe (binder\src\link.rs), built next to the binder: the windowless launcher the pokeshell:// handler runs
function Get-PokeshellBinderLinkExe([string]$Exe) {
  if (-not $Exe) { return $null }
  $p = Join-Path ([IO.Path]::GetDirectoryName($Exe)) 'binder-link.exe'
  if ([IO.File]::Exists($p)) { $p } else { $null }
}

<#
Register (or remove) the pokeshell:// URL handler under HKCU\Software\Classes\pokeshell. A Ctrl+click on the card's
`binder` link runs binder-link.exe (windowless: no console flash), which checks the link and opens the binder on
that pull in a Windows Terminal split pane (wt -w 0 sp). Returns what it does (or would do, with -DryRun) as lines
"set <key> [<name>] = <value>" / "remove <key>". Only pokeshell://binder?pull=<ulid> or ?card=<pack/char/tier> is
accepted, and the link never reaches wt.exe itself, so a crafted link can't do anything else.
$env:POKESHELL_REGISTRY = 'dryrun' (the tests set it) turns every call into a dry run.
#>
function Set-PokeshellUrlHandler([string]$Exe, [string]$LinkExe, [string]$Root, [string]$StateDir, [switch]$Remove, [switch]$DryRun,
                                 [string]$Key = 'HKCU:\Software\Classes\pokeshell') {
  if ($env:POKESHELL_REGISTRY -eq 'dryrun') { $DryRun = [switch]$true }
  $ops = [Collections.Generic.List[object]]::new()
  if ($Remove) { $ops.Add(@('remove', $Key)) }
  else {
    $cmd = Get-PokeshellBinderCommand $(if ($LinkExe) { $LinkExe } else { $Exe }) $Root $StateDir '--url "%1"'
    $ops.Add(@('set', $Key, '', 'URL:pokeshell binder')); $ops.Add(@('set', $Key, 'URL Protocol', ''))
    $ops.Add(@('set', "$Key\DefaultIcon", '', "`"$Exe`",0")); $ops.Add(@('set', "$Key\shell\open\command", '', $cmd))
  }
  foreach ($o in $ops) {
    if (-not $DryRun) {
      if ($o[0] -eq 'remove') { if (Test-Path $o[1]) { Remove-Item $o[1] -Recurse -Force } }
      else {
        if (-not (Test-Path $o[1])) { [void](New-Item $o[1] -Force) }
        if ($o[2]) { [void](New-ItemProperty -Path $o[1] -Name $o[2] -Value $o[3] -PropertyType String -Force) } else { Set-Item -Path $o[1] -Value $o[3] }
      }
    }
    if ($o[0] -eq 'remove') { "remove $($o[1])" } else { "set $($o[1]) [$(if ($o[2]) { $o[2] } else { '(default)' })] = $($o[3])" }
  }
}

function Get-PokeshellWtSettingsPath {
  # POKESHELL_REAL_WT=off (the tests set it): never fall back to the real settings.json; callers then need -SettingsPath
  if ($env:POKESHELL_REAL_WT -eq 'off') { return $null }
  $candidates = @(
    (Join-Path $env:LOCALAPPDATA 'Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json'),
    (Join-Path $env:LOCALAPPDATA 'Packages\Microsoft.WindowsTerminalPreview_8wekyb3d8bbwe\LocalState\settings.json'),
    (Join-Path $env:LOCALAPPDATA 'Microsoft\Windows Terminal\settings.json')
  )
  $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
}
