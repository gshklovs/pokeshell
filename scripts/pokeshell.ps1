<#
pokeshell: trading-card pack pulls for new Windows Terminal tabs. Run `pokeshell help`.
Runs from a source checkout or from an installed module version; user state lives in %LOCALAPPDATA%\pokeshell
(or $env:POKESHELL_HOME). A module install copies what new tabs need into <state>\current (see Invoke-Install).
#>
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'lib\roll.ps1')
. (Join-Path $PSScriptRoot 'lib\common.ps1')

$Root = Split-Path $PSScriptRoot
$State = Get-PokeshellStateDir
$Cfg = Read-PokeshellConfig $State
$esc = [char]27

# tools\publish.ps1 writes packaged.txt into the module it publishes. A module install runs new tabs (the $PROFILE
# hook, the shader profiles) from the stable copy in <state>\current, because Update-Module adds a new version
# folder and old ones get removed; a source checkout runs them straight from the repo.
$Packaged = [IO.File]::Exists((Join-Path $Root 'packaged.txt'))
$Version = 'source'
if ($Packaged) { foreach ($l in [IO.File]::ReadAllLines((Join-Path $Root 'packaged.txt'))) { if ($l -match '^version=(.+)$') { $Version = $Matches[1].Trim() } } }
$Current = Join-Path $State 'current'
$RuntimeRoot = if ($Packaged -and [IO.Directory]::Exists((Join-Path $Current 'packs'))) { $Current } else { $Root }

# split args into positionals and -flags (so `-s`, `-r`, `-shiny` work in any order)
$Command = ''; $Pos = @(); $Flags = @{}; $Opts = @{}
$argList = @($args)
for ($i = 0; $i -lt $argList.Count; $i++) {
  $a = [string]$argList[$i]
  if ($a -match '^-(settingspath|shell)$' -and $i + 1 -lt $argList.Count) { $Opts[$Matches[1]] = [string]$argList[++$i] }
  elseif ($a -match '^--?[a-z]') { $Flags[$a.TrimStart('-').ToLower()] = $true }
  elseif (-not $Command) { $Command = $a.ToLower() }
  else { $Pos += $a }
}
function Has([string[]]$names) { foreach ($n in $names) { if ($Flags[$n]) { return $true } }; $false }

function Show-Help {
  @"
pokeshell - every new Windows Terminal tab is a pack pull

  pokeshell pack [<pack>|all]             show or choose the active pack
  pokeshell odds [pack]                   pull odds for the active pack (or the one named)
  pokeshell collection                    your binder: every character/variant/shiny pulled so far
  pokeshell show <pack>/<character> [variant] [-shiny] [-picture|-card]
                                          print a card (pokeshell show: list what's available)
  pokeshell display [card|picture]        how pulls print: the full card (default) or just the picture
                                          (POKESHELL_DISPLAY=picture overrides it for one shell)
  pokeshell holo [<skin>|plain] [-s] [-r] open a skinned tab here (-s: split pane instead;
                                          -r: move the Claude Code session running here into it)
  pokeshell color <name|#hex|reset>       tint this tab (pokeshell color: list names)
  pokeshell colorwatch [on|off]           tint the tab to match Claude Code's /color (new tabs)
  pokeshell on | off                      enable / disable startup pulls (kill switch)
  pokeshell install [-SettingsPath <p>] [-Shell pwsh|powershell]
                                          add the skin profiles to Windows Terminal (re-run after Update-Module)
  pokeshell update                        update the module from the PowerShell Gallery and re-install
  pokeshell version                       which pokeshell is running, and where new tabs run from
  pokeshell uninstall [-SettingsPath <p>] [-Purge]
                                          remove them again (-Purge also deletes your pull log)
"@
}

function Get-ActivePackIds {
  $all = @(Get-PokeshellPackIds $Root)
  if ($Cfg.pack -eq 'all') { return $all }
  if ($all -contains $Cfg.pack) { return @($Cfg.pack) }
  @($all | Select-Object -First 1)
}

function Get-ProfileLine {
  if (-not $Packaged) { return ". `"$(Join-Path $PSScriptRoot 'pokeshell-profile.ps1')`"" }
  $hook = Join-Path $Current 'scripts\pokeshell-profile.ps1'
  if (-not $env:POKESHELL_HOME -and $env:LOCALAPPDATA) { $hook = '$env:LOCALAPPDATA\pokeshell\current\scripts\pokeshell-profile.ps1' }
  ". `"$hook`""
}

# ---------------------------------------------------------------- install / uninstall
function Invoke-Install {
  . (Join-Path $PSScriptRoot 'lib\wtsettings.ps1')
  $path = if ($Opts.settingspath) { $Opts.settingspath } else { Get-PokeshellWtSettingsPath }
  if (-not $path -or -not (Test-Path $path)) { throw "Windows Terminal settings.json not found (pass -SettingsPath <path>)" }
  $path = (Resolve-Path $path).ProviderPath
  if ($Packaged) { $script:RuntimeRoot = Sync-PokeshellRuntime $Root $State $Version }   # refresh <state>\current from this module version
  $skins = @(Get-PokeshellSkins $RuntimeRoot | Where-Object { Test-Path $_.shader })
  if (-not $skins) { throw "no shaders found under $RuntimeRoot\packs\*\shaders" }
  $shell = if ($Opts.shell -eq 'pwsh' -or ($Opts.shell -ne 'powershell' -and $PSVersionTable.PSEdition -eq 'Core')) { Join-Path $PSHOME 'pwsh.exe' }
           else { '%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe' }
  $profiles = foreach ($s in $skins) {
    [ordered]@{
      guid = $s.guid; name = "pokeshell: $($s.pack)/$($s.skin)"; commandline = $shell; hidden = $true
      scrollbarState = 'hidden'                      # WT draws the scrollbar over the card frame
      'experimental.pixelShaderPath' = $s.shader
    }
  }
  $newGuids = @($skins | ForEach-Object guid)
  $allGuids = @($newGuids) + @(Get-PokeshellInstalled $State | ForEach-Object guid)

  $orig = Read-WtSettingsFile $path
  $origTree = ConvertFrom-Jsonc $orig.text
  foreach ($item in (Get-WtProfileList $origTree).items) {
    $g = Get-JsoncMember $item 'guid'
    if ($g -and $newGuids -contains $g.value -and -not (Test-PokeshellProfileNode $item @())) { throw "settings.json already has a non-pokeshell profile with GUID $($g.value)" }
  }
  $new = Add-PokeshellProfilesText $orig.text $profiles $allGuids

  # verify before touching the real file: only pokeshell profiles changed, the result parses, all skins are in it
  $baseline = Remove-PokeshellProfilesText $orig.text $allGuids
  if (-not (Remove-PokeshellProfilesText $new $allGuids).Equals($baseline)) { throw "verification failed: removing the new profiles does not restore the other settings; nothing written" }
  $got = @((Get-WtProfileList (ConvertFrom-Jsonc $new)).items | ForEach-Object { (Get-JsoncMember $_ 'guid').value })
  $missing = @($newGuids | Where-Object { $got -notcontains $_ })
  if ($missing) { throw "verification failed: $($missing.Count) profiles missing after the edit; nothing written" }
  $strictOk = $true; try { [void]($orig.text | ConvertFrom-Json) } catch { $strictOk = $false }
  if ($strictOk) {   # the file was plain JSON: it must still be, and every profile must still be there
    $o = @(($new | ConvertFrom-Json).profiles.list).Count; $b = @(($baseline | ConvertFrom-Json).profiles.list).Count
    if ($o -ne $b + $skins.Count) { throw "verification failed: expected $($b + $skins.Count) profiles, found $o; nothing written" }
  }

  $backupDir = Join-Path $State 'backups'
  [void][IO.Directory]::CreateDirectory($backupDir)
  $backup = Join-Path $backupDir ("settings-{0:yyyyMMdd-HHmmss}.json" -f (Get-Date))
  Copy-Item -LiteralPath $path -Destination $backup
  if (-not $new.Equals($orig.text)) { Write-WtSettingsFile $path $new $orig.bom }

  # compile the startup core now (so no tab has to), and drop older builds that no tab has loaded
  $core = New-PokeshellCore $State
  Get-ChildItem $State -Filter 'pokeshell-core-*.dll' | Where-Object { $_.FullName -ne $core } | ForEach-Object { try { $_.Delete() } catch { } }

  $tsv = @("# pack`tskin`tguid`tsettings.json (written by pokeshell install)") + @($skins | ForEach-Object { "$($_.pack)`t$($_.skin)`t$($_.guid)`t$path" })
  [IO.File]::WriteAllLines((Join-Path $State 'installed.tsv'), [string[]]$tsv)
  Update-PokeshellRollCache -Root $RuntimeRoot -StateDir $State

  $packs = $skins | Group-Object pack | ForEach-Object { "$($_.Name) ($($_.Count))" }
  Write-Host "pokeshell: $($skins.Count) skin profiles synced into $path  [$($packs -join ', ')]" -ForegroundColor Green
  Write-Host "  backup of the previous settings: $backup"
  if ($Packaged) { Write-Host "  pokeshell $Version; new tabs run from $RuntimeRoot (after Update-Module, run pokeshell install again)" }
  Write-Host ''
  Write-Host 'Add this line to your PowerShell profile (notepad $PROFILE):' -ForegroundColor Yellow
  Write-Host ''
  Write-Host "  $(Get-ProfileLine)"
  Write-Host ''
  Write-Host 'Then open a new tab. `pokeshell off` disables pulls, `pokeshell uninstall` removes the profiles.'
}

function Invoke-Uninstall {
  . (Join-Path $PSScriptRoot 'lib\wtsettings.ps1')
  $installed = @(Get-PokeshellInstalled $State)
  $path = if ($Opts.settingspath) { $Opts.settingspath } elseif ($installed -and $installed[0].settings -and (Test-Path $installed[0].settings)) { $installed[0].settings } else { Get-PokeshellWtSettingsPath }
  if ($path -and (Test-Path $path)) {
    $guids = @($installed | ForEach-Object guid)
    $orig = Read-WtSettingsFile $path
    $new = Remove-PokeshellProfilesText $orig.text $guids
    if ($new.Equals($orig.text)) { Write-Host "pokeshell: no pokeshell profiles in $path" }
    else {
      $left = @((Get-WtProfileList (ConvertFrom-Jsonc $new)).items | Where-Object { Test-PokeshellProfileNode $_ $guids })
      if ($left) { throw "verification failed: $($left.Count) pokeshell profiles still present; nothing written" }
      $backupDir = Join-Path $State 'backups'
      [void][IO.Directory]::CreateDirectory($backupDir)
      $backup = Join-Path $backupDir ("settings-{0:yyyyMMdd-HHmmss}-uninstall.json" -f (Get-Date))
      Copy-Item -LiteralPath $path -Destination $backup
      Write-WtSettingsFile $path $new $orig.bom
      Write-Host "pokeshell: removed the skin profiles from $path (backup: $backup)" -ForegroundColor Green
    }
  } else { Write-Host "pokeshell: Windows Terminal settings.json not found; nothing to remove there" }
  Remove-Item (Join-Path $State 'installed.tsv'), (Join-Path $State 'roll.tsv') -ErrorAction SilentlyContinue
  if (Has 'purge') { Remove-Item $State -Recurse -Force -ErrorAction SilentlyContinue; Write-Host "pokeshell: deleted $State" }
  elseif ($Packaged -and [IO.Directory]::Exists($Current)) { Write-Host "pokeshell: kept $Current so tabs keep working until you remove the line below (-Purge deletes it)" }
  Write-Host ''
  Write-Host 'Remove this line from your PowerShell profile (notepad $PROFILE):' -ForegroundColor Yellow
  Write-Host "  $(Get-ProfileLine)"
}

# ---------------------------------------------------------------- pack / odds / collection / show
function Invoke-Pack {
  $all = @(Get-PokeshellPackIds $Root)
  if (-not $Pos) {
    Write-Host "active pack: $($Cfg.pack)"
    Write-Host "available:   $($all -join ', '), all"
    return
  }
  $want = $Pos[0].ToLower()
  if ($want -ne 'all' -and $all -notcontains $want) { throw "no pack '$want' (available: $($all -join ', '), all)" }
  Set-PokeshellConfigValue $State 'pack' $want
  Update-PokeshellRollCache -Root $RuntimeRoot -StateDir $State
  Write-Host "pokeshell: new tabs now pull from $want"
}

function Invoke-Display {
  if (-not $Pos) {
    $d = [Pokeshell.Core]::Display($Cfg)
    Write-Host "display: $d$(if ($env:POKESHELL_DISPLAY) { "  (POKESHELL_DISPLAY=$env:POKESHELL_DISPLAY in this shell)" })  (pokeshell display card|picture)"
    return
  }
  $want = $Pos[0].ToLower()
  if ($want -notin 'card', 'picture') { throw "display is card or picture, not '$want'" }
  Set-PokeshellConfigValue $State 'display' $want
  Update-PokeshellRollCache -Root $RuntimeRoot -StateDir $State   # config.txt is in the cache stamp: rebuild now, not in the next tab
  Write-Host "pokeshell: pulls now print as $(if ($want -eq 'card') { 'the full card' } else { 'just the picture' })"
}

function Invoke-Odds {
  $ids = if ($Pos) { @($Pos[0].ToLower()) } else { Get-ActivePackIds }
  foreach ($id in $ids) {
    $p = Read-PokeshellPack $Root $id
    $tiers = @($p.tiers)
    $total = 0; foreach ($t in $tiers[1..($tiers.Count - 1)]) { foreach ($s in $t.skins.PSObject.Properties) { $total += [int]$s.Value } }
    $n = @($p.characters).Count
    Write-Host ''
    Write-Host "$($p.name)  ($n characters; each pull is one character, uniformly)" -ForegroundColor Cyan
    if ($Cfg.pack -eq 'all') { Write-Host "  (pack 'all': each tab first picks one of $(@(Get-PokeshellPackIds $Root).Count) packs uniformly, so every number below happens that many times less often)" -ForegroundColor DarkGray }
    $rows = for ($i = 0; $i -lt $tiers.Count; $i++) {
      $t = $tiers[$i]
      $w = 0; $names = @(); foreach ($s in $t.skins.PSObject.Properties) { $w += [int]$s.Value; $names += "$($s.Name) $([math]::Round(100 * $p.foil_chance * $s.Value / $total, 2))%" }
      $pr = if ($i -eq 0) { 1 - $p.foil_chance } else { $p.foil_chance * $w / $total }
      [pscustomobject]@{ tier = $t.label; odds = ('{0,6:0.00}%' -f (100 * $pr)); 'one in' = ('{0:0}' -f (1 / $pr)); 'a given card' = ('1 in {0:0}' -f ($n / $pr)); art = $t.art; skins = $(if ($names) { $names -join ', ' } else { '(plain tab)' }) }
    }
    $rows | Format-Table -AutoSize -Wrap | Out-String -Width 200 | Write-Host
    if ($p.shiny_chance -gt 0) { Write-Host ("  shiny: {0:0.00}% of pulls (1 in {1:0}), any tier" -f (100 * $p.shiny_chance), (1 / $p.shiny_chance)) }
    else { Write-Host "  no shiny forms in this pack" }
  }
  if (-not @(Get-PokeshellInstalled $State)) { Write-Host "`n  not installed yet: until 'pokeshell install' every pull is a common" -ForegroundColor Yellow }
}

function Read-Pulls {
  $log = Join-Path $State 'pulls.log'
  if (-not (Test-Path $log)) { return @() }
  foreach ($line in [IO.File]::ReadAllLines($log)) {
    $f = $line.Split("`t")
    if ($f.Count -lt 7 -or ($f.Count -ge 8 -and $f[7] -match 'dryrun')) { continue }
    [pscustomobject]@{ time = $f[0]; pack = $f[1]; character = $f[2]; tier = $f[3]; art = $f[4]; skin = $f[5]; shiny = $f[6] -eq '1' }
  }
}

function Invoke-Collection {
  $pulls = @(Read-Pulls)
  if (-not $pulls) { Write-Host "pokeshell: no pulls yet. Open a new tab!"; return }
  Write-Host ''
  Write-Host "BINDER  $($pulls.Count) pulls since $($pulls[0].time.Replace('T', ' '))" -ForegroundColor Cyan
  foreach ($grp in ($pulls | Group-Object pack)) {
    $pack = try { Read-PokeshellPack $Root $grp.Name } catch { $null }
    $tiers = if ($pack) { @($pack.tiers) } else { @($grp.Group | Select-Object -ExpandProperty tier -Unique | ForEach-Object { [pscustomobject]@{ id = $_; label = $_ } }) }
    $chars = if ($pack) { @($pack.characters) } else { @($grp.Group | Select-Object -ExpandProperty character -Unique) }
    $caught = ''
    if ($chars.Count -gt 40) {   # big packs: only the rows you have pulled
      $seen = @{}; foreach ($x in $grp.Group) { $seen[$x.character] = $true }
      $caught = "  (caught $(@($chars | Where-Object { $seen[$_] }).Count) of $($chars.Count); rows for those only)"
      $chars = @($chars | Where-Object { $seen[$_] })
    }
    $owned = 0; $slots = 0
    $rows = foreach ($c in $chars) {
      $mine = @($grp.Group | Where-Object character -eq $c)
      $row = [ordered]@{ character = $(if ($pack) { $pack.names[$c] } else { $c }) }
      foreach ($t in $tiers) {
        $k = @($mine | Where-Object tier -eq $t.id).Count; $slots++; if ($k) { $owned++ }
        $row[$t.label] = if ($k) { "$k" } else { '.' }
      }
      $sh = @($mine | Where-Object shiny).Count
      $row['shiny'] = if ($sh) { "$sh *" } else { '.' }
      $row['total'] = $mine.Count
      [pscustomobject]$row
    }
    Write-Host ''
    Write-Host "$(if ($pack) { $pack.name } else { $grp.Name })  -  $($grp.Count) pulls, $owned/$slots card slots filled$caught" -ForegroundColor Yellow
    $rows | Format-Table -AutoSize | Out-String -Width 200 | Write-Host
    $best = @($grp.Group | Where-Object { $_.tier -ne $tiers[0].id -or $_.shiny })
    if ($best) {
      $rank = @{}; for ($i = 0; $i -lt $tiers.Count; $i++) { $rank[$tiers[$i].id] = $i }
      $top = $best | Sort-Object @{ e = { $rank[$_.tier] }; Descending = $true }, @{ e = { $_.shiny }; Descending = $true } | Select-Object -First 5
      Write-Host '  best pulls:'
      foreach ($b in $top) {
        $label = ($tiers | Where-Object id -eq $b.tier | Select-Object -First 1).label
        $name = if ($pack) { $pack.names[$b.character] } else { $b.character }
        Write-Host ("    {0}  {1} : {2}{3}{4}" -f $b.time.Replace('T', ' '), $label, $name, $(if ($b.shiny) { ' (shiny)' }), $(if ($b.skin) { "  [$($b.skin)]" }))
      }
    }
  }
}

function Invoke-Show {
  if (-not $Pos) {
    foreach ($id in Get-PokeshellPackIds $Root) {
      $p = Read-PokeshellPack $Root $id
      $built = @(Get-ChildItem (Join-Path $Root "dist\$id") -Filter '*.ans' -File -ErrorAction SilentlyContinue | ForEach-Object BaseName)
      $chars = @($p.characters)
      Write-Host "$id" -ForegroundColor Cyan
      if ($chars.Count -gt 40) {   # big packs: one summary line instead of a line per character
        $framed = @($p.frames | Where-Object { $_ }).Count -gt 0
        Write-Host ("  {0} characters, {1} art files{2}; e.g. {3}" -f $chars.Count, $built.Count, $(if ($framed) { ', tiers shown as card frames' }), (($chars | Select-Object -First 6 | ForEach-Object { "$id/$_" }) -join ' '))
        continue
      }
      foreach ($c in $chars) {
        $v = @($built | Where-Object { $_.StartsWith("$c-") } | ForEach-Object { $_.Substring($c.Length + 1) })
        Write-Host ("  {0,-22} {1}" -f "$id/$c", $(if ($v) { $v -join ' ' } else { '(no art built yet)' }))
      }
    }
    Write-Host "`nusage: pokeshell show <pack>/<character> [variant] [-shiny]"
    return
  }
  $ref = $Pos[0].ToLower()
  if ($ref -notmatch '^([^/\\]+)[/\\]([^/\\]+)$') {   # bare character: search the packs
    $hits = @(Get-PokeshellPackIds $Root | Where-Object { @((Read-PokeshellPack $Root $_).characters) -contains $ref })
    if (-not $hits) { throw "no character '$ref' (try: pokeshell show)" }
    $ref = "$($hits[0])/$ref"; [void]($ref -match '^(.+)/(.+)$')
  }
  $packId = $Matches[1]; $char = $Matches[2]
  $p = Read-PokeshellPack $Root $packId
  if (@($p.characters) -notcontains $char) {
    $has = @($p.characters); $more = if ($has.Count -gt 12) { " ... ($($has.Count) in all)" } else { '' }
    throw "pack '$packId' has no character '$char' (has: $(($has | Select-Object -First 12) -join ', ')$more)"
  }
  $tiers = @($p.tiers)
  $variant = if ($Pos.Count -gt 1) { $Pos[1].ToLower() } else { $tiers[0].art }
  $shiny = Has @('shiny')
  # the variant names an art variant, or a tier (by id, label, or frame preset: `show pokedex/pikachu gold`)
  $ti = -1
  for ($i = $tiers.Count - 1; $i -ge 0; $i--) {
    if ($tiers[$i].id -eq $variant -or ($tiers[$i].label -replace ' ', '-') -eq $variant -or ($p.frames[$i] -and $p.frames[$i] -eq $variant)) { $ti = $i }
  }
  $art = if ($ti -ge 0) { $tiers[$ti].art } else { $variant }
  $file = Join-Path $Root "dist\$packId\$char-$art$(if ($shiny) { '-shiny' }).ans"
  if (-not (Test-Path $file)) {
    $have = @(Get-ChildItem (Join-Path $Root "dist\$packId") -Filter "$char-*.ans" -ErrorAction SilentlyContinue | ForEach-Object { $_.BaseName.Substring($char.Length + 1) })
    throw "no art $packId/$char-$art$(if ($shiny) { '-shiny' }) in dist (have: $(if ($have) { $have -join ' ' } else { 'none' }))"
  }
  if ($ti -lt 0) { $ti = 0; for ($i = $tiers.Count - 1; $i -ge 0; $i--) { if ($tiers[$i].art -eq $variant) { $ti = $i } } }
  $label = if (@($tiers | Where-Object art -eq $art)) { $tiers[$ti].label } else { $variant }
  $frame = if ($tiers[$ti].art -eq $art) { $p.frames[$ti] } else { '' }
  # -Picture / -Card override the display setting (config `display`, or POKESHELL_DISPLAY for this shell)
  $picture = if (Has @('card')) { $false } elseif (Has @('picture')) { $true } else { [Pokeshell.Core]::Display($Cfg) -eq 'picture' }
  Show-PokeshellPull -Root $Root -Pack $packId -Character $char -Name $p.names[$char] -Art $art -Label $label -Tier $ti -Shiny:$shiny -Frame $frame -Tag $p.tags[$char] -Picture:$picture -Poster $p.posterNames[$char] -Bounty $p.bounties[$char]
}

# ---------------------------------------------------------------- holo / color / colorwatch
function Find-Claude {
  $all = @{}; Get-CimInstance Win32_Process | ForEach-Object { $all[[int]$_.ProcessId] = $_ }
  $cur = $all[$PID]
  for ($i = 0; $i -lt 10 -and $cur; $i++) {
    if ($cur.Name -eq 'claude.exe') { return $cur }
    $cur = $all[[int]$cur.ParentProcessId]
  }
  $all.Values | Where-Object { $_.Name -eq 'claude.exe' -and $_.ParentProcessId -eq $PID } | Select-Object -First 1
}

function Invoke-Holo {
  $installed = @(Get-PokeshellInstalled $State)
  if (-not $Pos) {
    Write-Host "usage: pokeshell holo <skin> [-s] [-r]     (from inside Claude Code: ! pokeshell holo -r cosmos)"
    if (-not $installed) { Write-Host "no skins installed yet: run pokeshell install" -ForegroundColor Yellow; return }
    foreach ($g in ($installed | Group-Object pack)) { Write-Host "  $($g.Name): $(($g.Group | ForEach-Object skin) -join ' ')" }
    Write-Host "  plain"
    return
  }
  $want = $Pos[0].ToLower()
  if ($want -eq 'plain') {
    $guid = if ($PSVersionTable.PSEdition -eq 'Core') { '{574e775e-4f2a-5b96-ac1e-a2962a402336}' } else { '{61c54bbd-c2c6-5271-96e7-009a87ff44bf}' }
  } else {
    $hits = @($installed | Where-Object { "$($_.pack)/$($_.skin)" -eq $want -or $_.skin -eq $want })
    if ($hits.Count -gt 1) { $pref = @($hits | Where-Object { (Get-ActivePackIds) -contains $_.pack }); if ($pref) { $hits = $pref } }
    if (-not $hits) {
      if (-not $installed) { throw "no skins installed yet: run pokeshell install" }
      throw "no skin '$want'. skins: $(($installed | ForEach-Object skin | Sort-Object -Unique) -join ' ') plain"
    }
    $guid = $hits[0].guid
  }
  $dir = if ((Get-Location).Provider.Name -eq 'FileSystem') { (Get-Location).ProviderPath } else { $HOME }
  $wtArgs = @('-w', '0', $(if (Has @('s', 'split')) { 'sp' } else { 'nt' }), '-p', $guid)
  if (Has @('r', 'resume')) {
    $claude = Find-Claude
    if (-not $claude) { throw "no Claude Code session found here. Run it inside Claude Code as:  ! pokeshell holo -r $want" }
    $sf = Join-Path $env:USERPROFILE ".claude\sessions\$($claude.ProcessId).json"
    $info = Get-Content $sf -Raw | ConvertFrom-Json
    $exe = if ($PSVersionTable.PSEdition -eq 'Core') { Join-Path $PSHOME 'pwsh.exe' } else { Join-Path $PSHOME 'powershell.exe' }
    $wtArgs += @('-d', $info.cwd.Replace(';', '\;'), $exe, '-NoExit', '-Command', "claude --resume $($info.sessionId)")
    & wt.exe @wtArgs
    Write-Host "pokeshell: resuming session $($info.sessionId) in a new '$want' tab; ending it here."
    # end this tab's copy a moment later, so this command's output lands first
    Start-Process powershell.exe -WindowStyle Hidden -ArgumentList '-NoProfile', '-Command', "Start-Sleep -Milliseconds 1500; Stop-Process -Id $($claude.ProcessId) -Force"
    return
  }
  $wtArgs += @('-d', $dir.Replace(';', '\;'))
  & wt.exe @wtArgs
}

$ColorNames = [ordered]@{
  red = 'cc3333'; crimson = 'dc143c'; maroon = '800000'; coral = 'ff6f61'; salmon = 'fa8072'
  orange = 'e07a1f'; amber = 'ffbf00'; gold = 'd4af37'; yellow = 'c9a227'; mustard = 'e1ad01'
  lime = '7cb82f'; green = '2e9e4f'; forest = '228b22'; olive = '6b8e23'; mint = '3eb489'
  teal = '1f8f80'; cyan = '1fa8b8'; turquoise = '40e0d0'; sky = '4aa3df'; blue = '2f6fd6'
  navy = '1f3a93'; indigo = '4b0082'; purple = '8a4fd6'; violet = '9b59f6'; lavender = 'a38fd6'
  magenta = 'c233c2'; pink = 'd64f9e'; rose = 'e8527a'; brown = '8b5a2b'; tan = 'c19a6b'
  gray = '6b6b6b'; grey = '6b6b6b'; slate = '5a6b7d'; black = '1a1a1a'; white = 'e8e8e8'
}

# WT draws the tab from palette index 264: OSC 4;264;rgb:.. sets it, OSC 104;264 resets it.
function Invoke-Color {
  $color = ($Pos -join ' ').Trim().ToLower()   # so 'pokeshell color hot pink' works unquoted
  if (-not $color) { Write-Host "usage: pokeshell color <name|#hex|reset>"; Write-Host "names: $($ColorNames.Keys -join ' ')"; return }
  if ($color -in 'reset', 'default', 'off', 'none') { Write-Host -NoNewline "$esc]104;264$esc\"; return }
  $hex = if ($ColorNames.Contains($color)) { $ColorNames[$color] } else { $color.TrimStart('#') }
  if ($hex -match '^[0-9a-f]{3}$') { $hex = -join ($hex.ToCharArray() | ForEach-Object { "$_$_" }) }
  if ($hex -notmatch '^[0-9a-f]{6}$' -and $color -match '^[a-z ]+$') {
    # not in the table: log it, and fall back to .NET's named colors (CSS/X11 names like 'chartreuse')
    Add-Type -AssemblyName System.Drawing
    $k = [System.Drawing.Color]::FromName(($color -replace ' ', ''))
    Write-PokeshellLog $State 'color-misses.log' "$(Get-Date -Format s)`t$color`t$(if ($k.IsKnownColor) { 'css:{0:x2}{1:x2}{2:x2}' -f $k.R, $k.G, $k.B } else { 'unresolved' })"
    if ($k.IsKnownColor) {
      $hex = '{0:x2}{1:x2}{2:x2}' -f $k.R, $k.G, $k.B
      Write-Host "pokeshell: '$color' isn't in the table yet (logged); using $hex" -ForegroundColor DarkGray
    }
  }
  if ($hex -notmatch '^[0-9a-f]{6}$') { Write-Host "pokeshell: '$color' isn't a known name or hex code" -ForegroundColor Red; Write-Host "names: $($ColorNames.Keys -join ' ')"; return }
  Write-Host -NoNewline "$esc]4;264;rgb:$($hex.Substring(0,2))/$($hex.Substring(2,2))/$($hex.Substring(4,2))$esc\"
}

function Invoke-ColorWatch {
  $flag = Join-Path $State 'colorwatch.on'   # a flag file: the hook checks it with one cheap File.Exists
  if (-not $Pos) { Write-Host "colorwatch: $(if (Test-Path $flag) { 'on' } else { 'off' })  (pokeshell colorwatch on|off; applies to new tabs)"; return }
  $on = $Pos[0].ToLower() -in 'on', '1', 'true', 'yes'
  [void][IO.Directory]::CreateDirectory($State)
  if ($on) { Set-Content $flag 'on' } else { Remove-Item $flag -ErrorAction SilentlyContinue }
  Write-Host "pokeshell: Claude Code /color tab tint $(if ($on) { 'on' } else { 'off' }) for new tabs"
}

# ---------------------------------------------------------------- update / version
function Get-CurrentVersion {
  $f = Join-Path $Current 'version.txt'
  if ([IO.File]::Exists($f)) { [IO.File]::ReadAllText($f).Trim() } else { '' }
}

function Invoke-Version {
  Write-Host "pokeshell $Version  ($Root)"
  $cv = Get-CurrentVersion
  if ($Packaged -and $cv) { Write-Host "new tabs run from $Current ($cv)" }
  elseif ($Packaged) { Write-Host "not installed yet: run pokeshell install" -ForegroundColor Yellow }
  else { Write-Host "running from a source checkout: new tabs run from $Root" }
}

# re-run install with the same -SettingsPath / -Shell, in a fresh process of this edition, from $Base
function Invoke-InstallFrom([string]$Base) {
  $exe = if ($PSVersionTable.PSEdition -eq 'Core') { Join-Path $PSHOME 'pwsh.exe' } else { Join-Path $PSHOME 'powershell.exe' }
  $a = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $Base 'scripts\pokeshell.ps1'), 'install')
  if ($Opts.settingspath) { $a += '-SettingsPath', $Opts.settingspath }
  if ($Opts.shell) { $a += '-Shell', $Opts.shell }
  & $exe @a
  if ($LASTEXITCODE) { throw "install from $Base failed" }
}

function Invoke-Update {
  if (-not $Packaged) {
    Write-Host "pokeshell: running from a source checkout ($Root): git pull there, then run pokeshell install"
    return
  }
  Write-Host "pokeshell ${Version}: checking the PowerShell Gallery..."
  Update-Module pokeshell -ErrorAction Stop
  $newest = Get-Module pokeshell -ListAvailable | Sort-Object Version -Descending | Select-Object -First 1
  if (-not $newest) { throw "the pokeshell module was not found after Update-Module" }
  if ("$($newest.Version)" -eq (Get-CurrentVersion)) { Write-Host "pokeshell: up to date ($($newest.Version))"; return }
  Write-Host "pokeshell: installing $($newest.Version) (new tabs switch to it; older module versions can then be removed with Uninstall-Module)"
  Invoke-InstallFrom $newest.ModuleBase
}

# after Update-Module, new tabs still run the previous version's copy until `pokeshell install`
if ($Packaged -and $Command -notin 'install', 'uninstall', 'update', 'version') {
  $cv = Get-CurrentVersion
  if ($cv -and $cv -ne $Version) { Write-Host "pokeshell: module $Version is installed but new tabs still run $cv; run pokeshell install to switch them" -ForegroundColor Yellow }
}

try {
switch ($Command) {
  ''           { Show-Help }
  'help'       { Show-Help }
  'pack'       { Invoke-Pack }
  'odds'       { Invoke-Odds }
  'collection' { Invoke-Collection }
  'binder'     { Invoke-Collection }
  'show'       { Invoke-Show }
  'display'    { Invoke-Display }
  'holo'       { Invoke-Holo }
  'color'      { Invoke-Color }
  'colorwatch' { Invoke-ColorWatch }
  'on'         { Set-PokeshellConfigValue $State 'enabled' '1'; Write-Host 'pokeshell: startup pulls on' }
  'off'        { Set-PokeshellConfigValue $State 'enabled' '0'; Write-Host 'pokeshell: startup pulls off (pokeshell on to re-enable)' }
  'install'    { Invoke-Install }
  'uninstall'  { Invoke-Uninstall }
  'update'     { Invoke-Update }
  'version'    { Invoke-Version }
  default      { Write-Host "pokeshell: unknown command '$Command'" -ForegroundColor Red; Show-Help }
}
} catch {
  Write-Host "pokeshell: $($_.Exception.Message)" -ForegroundColor Red
  exit 1
}
