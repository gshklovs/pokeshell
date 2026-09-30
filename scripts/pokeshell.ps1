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
  if ($a -match '^--?(settingspath|shell|pull|card|keys|art)$' -and $i + 1 -lt $argList.Count) { $Opts[$Matches[1].ToLower()] = [string]$argList[++$i] }
  elseif ($a -match '^--?[a-z]') { $Flags[$a.TrimStart('-').ToLower()] = $true }
  elseif (-not $Command) { $Command = $a.ToLower() }
  else { $Pos += $a }
}
function Has([string[]]$names) { foreach ($n in $names) { if ($Flags[$n]) { return $true } }; $false }

# `collection --json --pack <id>` (or --pack=<id>, or the pack as the one positional): the pack to list, '' for all
function Get-JsonPackFilter {
  foreach ($k in $Flags.Keys) { if ($k -match '^pack=(.+)$') { return $Matches[1] } }
  if ($Pos) { return [string]$Pos[0] }
  ''
}

function Show-Help {
  @"
pokeshell - every new Windows Terminal tab is a pack pull

  pokeshell pack [<pack>|all]             show or choose the active pack
  pokeshell odds [pack]                   pull odds for the active pack (or the one named)
  pokeshell binder [--pull <id>|--card <pack/char/tier>]
                                          the binder app, full screen (q returns); `binder` for short.
                                          Without the app built: the text binder (pokeshell collection)
  pokeshell binder --web                  rebuild the web binder and open it in your browser
  pokeshell collection                    the text binder: every character/variant/shiny you've earned
  pokeshell collection --json [--pack <id>]   your caught and seen cards as JSON, for other tools (README)
  pokeshell earn [first-command|minutes:N|off]
                                          what earns a pull: its tab's first command (default), the tab
                                          staying open N minutes, or nothing (off: every pull counts)
  pokeshell hotkey [on|off] [-Keys ctrl+shift+b] [-SettingsPath <p>]
                                          the Windows Terminal key that opens the binder in a split pane on
                                          your newest pull (install adds it; off keeps it out)
  pokeshell urlhandler [on|off] [-DryRun] the card's Ctrl+click "binder" link (pokeshell://; install adds it)
  pokeshell show <pack>/<character> [variant|card id|tier] [-shiny] [-picture|-card]
                                          print a card (pokeshell show: list what's available; also pokemon/<card id>)
  pokeshell display [card|picture]        how pulls print: the full card (default) or just the picture
                                          (POKESHELL_DISPLAY=picture overrides it for one shell)
  pokeshell holo [<skin>|plain] [-s] [-r] open a skinned tab here (-s: split pane instead;
                                          -r: move the Claude Code session running here into it)
  pokeshell color <name|#hex|reset>       tint this tab (pokeshell color: list names)
  pokeshell colorwatch [on|off]           tint the tab to match Claude Code's /color (new tabs)
  pokeshell on | off                      enable / disable startup pulls (kill switch)
  pokeshell install [-SettingsPath <p>] [-Shell pwsh|powershell] [-Art auto|download|local|skip] [-ArtStillOnly]
                                          add the skin profiles, the binder hotkey and the card link to
                                          Windows Terminal (re-run after Update-Module)
                                          and download the card art release art.json pins (auto: if missing)
  pokeshell update                        update the module from the PowerShell Gallery and re-install
  pokeshell version                       which pokeshell is running, and where new tabs run from
  pokeshell version --json                the same as JSON: version, api level, folders, packs, JSON commands
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
# The card art is not in the repo or the module: it is a release of the art repo art.json names, downloaded into
# $Root\dist\<pack> (lib\cardart.ps1, docs\ART_RELEASES.md). A failed download never fails the install.
function Get-ArtMode {
  $m = if ($Opts.art) { $Opts.art } elseif ($env:POKESHELL_ART) { $env:POKESHELL_ART } else { 'auto' }
  $m = $m.ToLower()
  if ($m -notin 'auto', 'download', 'local', 'skip') { throw "-Art is auto, download, local or skip, not '$m'" }
  $m
}

function Invoke-ArtInstall([string]$Mode) {
  . (Join-Path $PSScriptRoot 'lib\cardart.ps1')
  $cfgPath = if ($env:POKESHELL_ART_JSON) { $env:POKESHELL_ART_JSON } else { Join-Path $Root 'art.json' }
  try { $null = Install-CardArt -Root $Root -ConfigPath $cfgPath -Mode $Mode -CacheDir (Join-Path $State 'art-cache') -StillOnly:(Has 'artstillonly') -Prefix 'pokeshell' }
  catch { Write-Host "pokeshell: card art not installed: $($_.Exception.Message)" -ForegroundColor Yellow }
}

function Invoke-Install {
  . (Join-Path $PSScriptRoot 'lib\wtsettings.ps1')
  $path = if ($Opts.settingspath) { $Opts.settingspath } else { Get-PokeshellWtSettingsPath }
  if (-not $path -or -not (Test-Path $path)) { throw "Windows Terminal settings.json not found (pass -SettingsPath <path>)" }
  $path = (Resolve-Path $path).ProviderPath
  Invoke-ArtInstall (Get-ArtMode)   # before the runtime sync, so a module install copies the art into current
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
  # the binder from a pulled card, by default: Ctrl+Shift+B (a split pane on the newest pull) and the card's
  # Ctrl+click link (pokeshell://, "safeUriSchemes"); `pokeshell hotkey off` / `urlhandler off` keep them out
  $access = Get-BinderAccessPlan $new -Hotkey (-not [IO.File]::Exists((Join-Path $State 'hotkey.off'))) -Link (-not [IO.File]::Exists((Join-Path $State 'urlhandler.off')))
  if (-not (Remove-BinderAccessText $access.text $access).Equals((Remove-BinderAccessText $new $access))) { throw "verification failed: removing the binder hotkey / link again would not restore settings.json; nothing written" }
  $new = $access.text
  [void](ConvertFrom-Jsonc $new)
  if ($strictOk) { [void]($new | ConvertFrom-Json) }

  $backupDir = Join-Path $State 'backups'
  [void][IO.Directory]::CreateDirectory($backupDir)
  $backup = Join-Path $backupDir ("settings-{0:yyyyMMdd-HHmmss}.json" -f (Get-Date))
  Copy-Item -LiteralPath $path -Destination $backup
  if (-not $new.Equals($orig.text)) { Write-WtSettingsFile $path $new $orig.bom }
  Complete-BinderAccess $access $path

  # compile the startup core now (so no tab has to), and drop older builds that no tab has loaded
  $core = New-PokeshellCore $State
  Get-ChildItem $State -Filter 'pokeshell-core-*.dll' | Where-Object { $_.FullName -ne $core } | ForEach-Object { try { $_.Delete() } catch { } }
  . (Join-Path $PSScriptRoot 'lib\anim.ps1'); $animCore = New-PokeshellAnimCore $State   # the card animation player, likewise
  Get-ChildItem $State -Filter 'pokeshell-anim-*.dll' | Where-Object { $_.FullName -ne $animCore } | ForEach-Object { try { $_.Delete() } catch { } }

  $tsv = @("# pack`tskin`tguid`tsettings.json (written by pokeshell install)") + @($skins | ForEach-Object { "$($_.pack)`t$($_.skin)`t$($_.guid)`t$path" })
  [IO.File]::WriteAllLines((Join-Path $State 'installed.tsv'), [string[]]$tsv)
  Update-PokeshellRollCache -Root $RuntimeRoot -StateDir $State

  $packs = $skins | Group-Object pack | ForEach-Object { "$($_.Name) ($($_.Count))" }
  Write-Host "pokeshell: $($skins.Count) skin profiles synced into $path  [$($packs -join ', ')]" -ForegroundColor Green
  Write-Host "  backup of the previous settings: $backup"
  if ($access.hotkey) { Write-Host "  binder: $($access.hotkey.combo) opens it in a split pane on your newest pull" }
  if ($access.link) { Write-Host "  binder: Ctrl+click the ``binder`` link under a pulled card opens it on that card" }
  foreach ($n in $access.notes) { Write-Host "  $n" -ForegroundColor Yellow }
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
  # the binder hotkey, the "safeUriSchemes" entry and the pokeshell:// handler, if this state dir installed them
  $hk = Join-Path $State 'hotkey.tsv'
  if ([IO.File]::Exists($hk)) {
    $hp = [IO.File]::ReadAllText($hk).Trim().Split("`t")[0]
    if ($hp -and (Test-Path $hp)) { $b = Remove-PokeshellHotkey $hp; Write-Host "pokeshell: removed the binder hotkey from $hp$(if ($b) { " (backup: $b)" })" }
    Remove-Item $hk -ErrorAction SilentlyContinue
  }
  $su = Read-StateTsv 'safeuri.tsv'
  if ($su.Count) { $b = Remove-PokeshellSafeScheme $su[0]; Write-Host "pokeshell: removed `"pokeshell`" from safeUriSchemes in $($su[0])$(if ($b) { " (backup: $b)" })" }
  if ([IO.File]::Exists((Join-Path $State 'urlhandler.txt'))) {
    [void](Set-PokeshellUrlHandler -Remove); Remove-Item (Join-Path $State 'urlhandler.txt') -ErrorAction SilentlyContinue
    Write-Host "pokeshell: removed the pokeshell:// link handler"
  }
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
    if ($p.isCardPack) { Show-CardOdds $p; continue }
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

# a real-card pack's odds: a tier by its weight among the tiers that have a built card, then one of its cards
function Show-CardOdds($p) {
  $tiers = @($p.tiers)
  $built = @($p.cardList | Where-Object { Test-PokeshellCardBuilt $Root $p.id $_ })
  $live = @(for ($i = 0; $i -lt $tiers.Count; $i++) { if ([int]$tiers[$i].weight -gt 0 -and @($built | Where-Object tier -eq $i)) { $i } })
  $total = 0; foreach ($i in $live) { $total += [int]$tiers[$i].weight }
  Write-Host ''
  Write-Host "$($p.name)  ($($built.Count) real cards in $($live.Count) of $($tiers.Count) rarity tiers; a pull picks a tier by weight, then one of its cards)" -ForegroundColor Cyan
  if ($Cfg.pack -eq 'all') { Write-Host "  (pack 'all': each tab first picks one of $(@(Get-PokeshellPackIds $Root).Count) packs uniformly, so every number below happens that many times less often)" -ForegroundColor DarkGray }
  if (-not $live) { Write-Host "  no card art built yet: nothing to pull (tools\build_realcards.py builds it; see tools\README.md)" -ForegroundColor Yellow; return }
  $rows = foreach ($i in $live) {
    $t = $tiers[$i]; $pr = [int]$t.weight / $total
    $cs = @($built | Where-Object tier -eq $i)
    $sk = @($t.skins.PSObject.Properties | ForEach-Object Name)
    [pscustomobject]@{ tier = $t.label; odds = ('{0,6:0.00}%' -f (100 * $pr)); 'one in' = ('{0:0}' -f (1 / $pr)); 'a given card' = ('1 in {0:0}' -f ($cs.Count / $pr))
      cards = (($cs | ForEach-Object { "$($_.id) $($_.name)" }) -join ', '); skins = $(if ($sk) { $sk -join ', ' } else { '(plain tab)' }) }
  }
  $rows | Format-Table -AutoSize -Wrap | Out-String -Width 220 | Write-Host
  $empty = @(for ($i = 0; $i -lt $tiers.Count; $i++) { if ($live -notcontains $i) { $tiers[$i].label } })
  if ($empty) { Write-Host "  no card yet (these never roll; the tiers listed above share their odds): $($empty -join ', ')" -ForegroundColor DarkGray }
  $unbuilt = @($p.cardList | Where-Object { -not (Test-PokeshellCardBuilt $Root $p.id $_) })
  if ($unbuilt) { Write-Host "  $($unbuilt.Count) cards in pack.json have no art built: $(($unbuilt | ForEach-Object id) -join ', ')" -ForegroundColor Yellow }
  if ($p.shiny_chance -gt 0) { Write-Host ("  shiny: {0:0.00}% of pulls (1 in {1:0}), any tier" -f (100 * $p.shiny_chance), (1 / $p.shiny_chance)) }
}

# Every pull with the earned rule applied (status earned | pending | expired; dry runs left out). Pending pulls that
# have since expired get their `expired:<id>` line written here (the log stays append-only).
function Read-Pulls([switch]$All) {
  $now = [DateTime]::UtcNow.Ticks
  $recs = @([Pokeshell.Core]::ReadPulls($State, $now, [Pokeshell.Core]::BootId()))
  foreach ($r in $recs) {
    if ($r.Status -eq 'expired' -and $r.Derived) { [Pokeshell.Core]::Log($State, 'pulls.log', [Pokeshell.Core]::EventLine('expired', $r.Id, $now)) }
    if (-not $All -and $r.Status -ne 'earned') { continue }
    [pscustomobject]@{ time = $r.Time; pack = $r.Pack; character = $r.Character; tier = $r.Tier; art = $r.Art; skin = $r.Skin; shiny = $r.Shiny; id = $r.Id; status = $r.Status; new = $r.New }
  }
}

# Real-card packs: each pull as the card it resolves to today (Resolve-PokeshellPull), its tier/art columns set to
# that card's; pulls of retired art (pack.json "retired") or of a card whose art isn't built are left out and counted
# in $script:HiddenPulls. $script:RealSince: when the real cards went live, the time of the first shown pull whose
# line names a built card itself (the default start of the best pulls). pulls.log itself is never rewritten.
function Get-ShownPulls($Pulls) {
  $packs = @{}; $script:ShownPacks = $packs; $script:HiddenPulls = 0; $script:RealSince = $null   # ShownPacks: pack id -> Read-PokeshellPack, for reuse
  foreach ($x in $Pulls) {
    if (-not $packs.ContainsKey($x.pack)) { $packs[$x.pack] = try { Read-PokeshellPack $Root $x.pack } catch { $null } }
    $pk = $packs[$x.pack]
    if (-not $pk -or -not $pk.isCardPack) { $x; continue }
    $c = Resolve-PokeshellPull $pk $x.character $x.tier $x.art
    if (-not $c) { $script:HiddenPulls++; continue }
    if ($c.id -eq $x.art -and ($null -eq $script:RealSince -or [string]::CompareOrdinal($x.time, $script:RealSince) -lt 0)) { $script:RealSince = $x.time }
    $x.tier = $c.tierId; $x.art = $c.id; $x
  }
}

# config.txt best_since: 'all' -> '' (every pull); 'YYYY-MM-DD[THH:MM[:SS]]' -> that local time (pull times compare as
# ISO strings); anything else (unset) -> $Default, when the real cards went live
function Get-BestSince([string]$Setting, [string]$Default) {
  $v = "$Setting".Trim()
  if ($v -eq 'all') { return '' }
  $v = $v.Replace(' ', 'T')
  if ($v -match '^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}(:\d{2})?)?$') { return $v }
  "$Default"
}

function Invoke-Collection {
  $every = @(Get-ShownPulls @(Read-Pulls -All))   # earned, pending (expired left out); retired art hidden
  $pulls = @($every | Where-Object status -eq 'earned')
  $pending = @($every | Where-Object status -eq 'pending')
  $since = Get-BestSince $Cfg['best_since'] $script:RealSince   # best pulls start here ('' = all)
  $hidden = if ($script:HiddenPulls) { "  ($script:HiddenPulls pulls of retired art not shown)" } else { '' }
  if (-not $pulls) {
    if ($pending) { Write-Host "pokeshell: $($pending.Count) pending pull$(if ($pending.Count -gt 1) { 's' }): use $(if ($pending.Count -gt 1) { 'their tabs' } else { 'its tab' }) to earn $(if ($pending.Count -gt 1) { 'them' } else { 'it' })$hidden" }
    else { Write-Host "pokeshell: no pulls yet. Open a new tab!$hidden" }
    return
  }
  Write-Host ''
  $newN = @($pulls | Where-Object new).Count
  Write-Host ("BINDER  $($pulls.Count) pulls since $($pulls[0].time.Replace('T', ' '))$hidden" +
    $(if ($pending) { "  ($($pending.Count) pending: use $(if ($pending.Count -gt 1) { 'their tabs' } else { 'its tab' }) to earn $(if ($pending.Count -gt 1) { 'them' } else { 'it' }))" }) +
    $(if ($newN) { "  $newN new" })) -ForegroundColor Cyan
  foreach ($grp in ($pulls | Group-Object pack)) {
    $pack = try { Read-PokeshellPack $Root $grp.Name } catch { $null }
    $isCards = $pack -and $pack.isCardPack
    $cards = if ($isCards) { @($pack.cardList | Where-Object { Test-PokeshellCardBuilt $Root $grp.Name $_ }) }   # unbuilt cards are muted: no slot
    $tiers = if ($isCards) { $has = @($cards | ForEach-Object tier); @(for ($i = 0; $i -lt @($pack.tiers).Count; $i++) { if ($has -contains $i) { $pack.tiers[$i] } }) }   # the rarities it has cards in
             elseif ($pack) { @($pack.tiers) } else { @($grp.Group | Select-Object -ExpandProperty tier -Unique | ForEach-Object { [pscustomobject]@{ id = $_; label = $_ } }) }
    $chars = if ($isCards) { @($pack.characters | Where-Object { $ch = $_; @($cards | Where-Object character -eq $ch).Count }) }
             elseif ($pack) { @($pack.characters) } else { @($grp.Group | Select-Object -ExpandProperty character -Unique) }
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
        $inTier = @($mine | Where-Object tier -eq $t.id); $k = $inTier.Count
        if ($isCards) {   # every real card is its own slot (a character can have several in one rarity: "pulls (cards got/of)")
          $of = @($cards | Where-Object { $_.character -eq $c -and $_.tierId -eq $t.id }).Count
          if (-not $of) { $row[$t.label] = '-'; continue }   # no such real card
          $got = @($inTier | Select-Object -ExpandProperty art -Unique).Count; $slots += $of; $owned += $got
          $row[$t.label] = if (-not $k) { '.' } elseif ($of -gt 1) { "$k ($got/$of)" } else { "$k" }
          continue
        }
        $slots++; if ($k) { $owned++ }
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
    $best = @($grp.Group | Where-Object { ($_.tier -ne $tiers[0].id -or $_.shiny) -and [string]::CompareOrdinal($_.time, $since) -ge 0 })
    if ($best) {
      $rank = @{}; for ($i = 0; $i -lt $tiers.Count; $i++) { $rank[$tiers[$i].id] = $i }
      $top = $best | Sort-Object @{ e = { $rank[$_.tier] }; Descending = $true }, @{ e = { $_.shiny }; Descending = $true } | Select-Object -First 5
      Write-Host "  best pulls$(if ($since) { ' (since ' + [datetime]::ParseExact($since.Substring(0, 10), 'yyyy-MM-dd', [Globalization.CultureInfo]::InvariantCulture).ToString('MMM d', [Globalization.CultureInfo]::InvariantCulture) + ')' }):"
      foreach ($b in $top) {
        $label = ($tiers | Where-Object id -eq $b.tier | Select-Object -First 1).label
        $name = if ($pack) { $pack.names[$b.character] } else { $b.character }
        Write-Host ("    {0}  {1} : {2}{3}{4}" -f $b.time.Replace('T', ' '), $label, $name, $(if ($b.shiny) { ' (shiny)' }), $(if ($b.skin) { "  [$($b.skin)]" }))
      }
    }
  }
}

# Real-card packs: `show pokemon/pikachu` (the character's lowest-tier card), `show pokemon/pikachu <card id | tier>`,
# `show pokemon/<card id>` or `show <card id>`. Returns $false when the reference isn't in a real-card pack.
function Show-Card {
  $ref = $Pos[0]; $want = if ($Pos.Count -gt 1) { $Pos[1] } else { '' }
  $packIds = @(Get-PokeshellPackIds $Root); $name = $ref
  if ($ref -match '^([^/\\]+)[/\\]([^/\\]+)$') { $packIds = @($Matches[1].ToLower()); $name = $Matches[2] }
  foreach ($id in $packIds) {
    if (-not (Test-Path (Join-Path $Root "packs\$id\pack.json"))) { return $false }
    $p = Read-PokeshellPack $Root $id
    if (-not $p.isCardPack) { continue }
    $card = @($p.cardList | Where-Object { $_.id -eq $name })[0]
    if (-not $card) {
      $mine = @($p.cardList | Where-Object { $_.character -eq $name.ToLower() } | Sort-Object tier)
      if (-not $mine) {
        if ($packIds.Count -gt 1) { continue }
        throw "pack '$id' has no character '$name' and no card '$name' (cards: $(($p.cardList | ForEach-Object { "$($_.character)/$($_.id)" }) -join ' '))"
      }
      $card = if (-not $want) { $mine[0] } else {
        @($mine | Where-Object { $_.id -eq $want -or $_.tierId -eq $want.ToLower() -or ($p.tiers[$_.tier].label -replace ' ', '-') -eq $want.ToLower() })[0] }
      if (-not $card) { throw "no $name card '$want' in $id (has: $(($mine | ForEach-Object { "$($_.id) ($($_.tierId))" }) -join ', '))" }
    }
    $t = $p.tiers[$card.tier]
    # a tier whose cards print the shiny Pokemon (pack.json "shiny": "printed") has no separate shiny form
    $shiny = (Has @('shiny')) -and $t.shiny -ne 'printed'
    # no -shiny.ans: the regular art is shown (Core.PullText falls back the same way)
    $file = Join-Path $Root "dist\$id\$($card.character)-$($card.id).ans"
    if (-not (Test-Path $file)) { throw "$id/$($card.id) has no art built (tools\build_realcards.py; see tools\README.md)" }
    $picture = if (Has @('card')) { $false } elseif (Has @('picture')) { $true } else { [Pokeshell.Core]::Display($Cfg) -eq 'picture' }
    Show-PokeshellPull -Root $Root -Pack $id -Character $card.character -Name $card.name -Art $card.id -Label $t.label -Tier $card.tier -Shiny:$shiny -Frame $p.frames[$card.tier] -Tag $card.tag -Picture:$picture
    return $true
  }
  $false
}

function Invoke-Show {
  if (-not $Pos) {
    foreach ($id in Get-PokeshellPackIds $Root) {
      $p = Read-PokeshellPack $Root $id
      if ($p.isCardPack) {   # real cards: per character, its cards and their rarity tiers
        Write-Host "$id" -ForegroundColor Cyan
        foreach ($g in ($p.cardList | Group-Object character)) {
          $cs = @($g.Group | Sort-Object tier | ForEach-Object { "$($_.id) ($($p.tiers[$_.tier].label))$(if (-not (Test-PokeshellCardBuilt $Root $id $_)) { ' [not built]' })" })
          Write-Host ("  {0,-22} {1}" -f "$id/$($g.Name)", ($cs -join '  '))
        }
        if (-not $p.cardList) { Write-Host "  (no cards)" }
        continue
      }
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
    Write-Host "`nusage: pokeshell show <pack>/<character> [variant] [-shiny]   (real-card packs: <pack>/<character> [card id|tier], or <pack>/<card id>)"
    return
  }
  if (Show-Card) { return }
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
  if ($ti -ge 0 -and $tiers[$ti].shiny -eq 'printed') { $shiny = $false }   # printed shiny: no separate shiny form
  $file = Join-Path $Root "dist\$packId\$char-$art.ans"   # no -shiny.ans: the regular art (as Core.PullText)
  if (-not (Test-Path $file)) {
    $have = @(Get-ChildItem (Join-Path $Root "dist\$packId") -Filter "$char-*.ans" -ErrorAction SilentlyContinue | ForEach-Object { $_.BaseName.Substring($char.Length + 1) })
    throw "no art $packId/$char-$art in dist (have: $(if ($have) { $have -join ' ' } else { 'none' }))"
  }
  if ($ti -lt 0) { $ti = 0; for ($i = $tiers.Count - 1; $i -ge 0; $i--) { if ($tiers[$i].art -eq $variant) { $ti = $i } } }
  $label = if (@($tiers | Where-Object art -eq $art)) { $tiers[$ti].label } else { $variant }
  $frame = if ($tiers[$ti].art -eq $art) { $p.frames[$ti] } else { '' }
  # -Picture / -Card override the display setting (config `display`, or POKESHELL_DISPLAY for this shell)
  $picture = if (Has @('card')) { $false } elseif (Has @('picture')) { $true } else { [Pokeshell.Core]::Display($Cfg) -eq 'picture' }
  Show-PokeshellPull -Root $Root -Pack $packId -Character $char -Name $p.names[$char] -Art $art -Label $label -Tier $ti -Shiny:$shiny -Frame $frame -Tag $p.tags[$char] -Picture:$picture -Poster $p.posterNames[$char] -Bounty $p.bounties[$char]
}

# ---------------------------------------------------------------- binder / earn / hotkey / urlhandler
# `pokeshell binder` (and the `binder` function the $PROFILE hook defines): the Rust binder app full screen in this
# tab (it switches to the alternate screen; q brings the prompt back as it was). Without the app: the text binder.
function Invoke-Binder {
  if (Has @('web')) { Invoke-BinderWeb; return }
  $exe = Get-PokeshellBinderExe $Root
  [void]@(Read-Pulls -All)   # writes expired:<id> lines for pulls that have expired since the last look
  if (-not $exe) {
    Write-Host "(the binder app isn't built: binder\build.ps1 builds it; here is the text binder)" -ForegroundColor DarkGray
    Invoke-Collection
    return
  }
  $a = @('--root', $RuntimeRoot, '--state', $State)
  if ($Opts.pull) { $a += '--pull', $Opts.pull }
  if ($Opts.card) { $a += '--card', $Opts.card }
  & $exe @a
  if ($LASTEXITCODE) { throw "the binder exited with code $LASTEXITCODE" }
}

# Python with Pillow for the web export: $env:POKESHELL_PYTHON, the repo's .venv, then py -3 / python on PATH
function Find-PokeshellPython {
  $c = @()
  if ($env:POKESHELL_PYTHON) { $c += , @($env:POKESHELL_PYTHON) }
  $c += , @((Join-Path $Root '.venv\Scripts\python.exe'))
  $c += , @('py', '-3'); $c += , @('python')
  foreach ($x in $c) {
    $exe = $x[0]
    if ($exe -match '[\\/]' -and -not (Test-Path $exe)) { continue }
    if ($exe -notmatch '[\\/]' -and -not (Get-Command $exe -ErrorAction SilentlyContinue)) { continue }
    $rest = @($x | Select-Object -Skip 1)
    & $exe @rest -c 'import PIL' 2>$null
    if ($LASTEXITCODE -eq 0) { return , $x }
  }
  $null
}

# `binder --web`: rebuild the static web binder into <state>\web (about a second) and open it in the browser
function Invoke-BinderWeb {
  $py = Find-PokeshellPython
  if (-not $py) { throw "binder --web needs Python 3 with Pillow (py -3 -m venv .venv; .venv\Scripts\python -m pip install pillow), or set POKESHELL_PYTHON" }
  $out = Join-Path $State 'web'
  [void]@(Read-Pulls -All)
  $exe = $py[0]; $pre = @($py | Select-Object -Skip 1)
  & $exe @pre (Join-Path $Root 'tools\binder_web.py') --root $RuntimeRoot --state $State --out $out
  if ($LASTEXITCODE) { throw "the web export failed (exit $LASTEXITCODE)" }
  $page = Join-Path $out 'binder.html'
  if ($env:POKESHELL_NO_OPEN -eq '1' -or (Has @('noopen'))) { Write-Host "pokeshell: web binder at $page" }
  else { Start-Process $page; Write-Host "pokeshell: opened $page" }
}

function Invoke-Earn {
  if (-not $Pos) {
    Write-Host "earn: $([Pokeshell.Core]::EarnMode($Cfg.earn))  (pokeshell earn first-command|minutes:N|off)"
    Write-Host '  first-command: a pull counts once you run a command in its tab; minutes:N: once its tab has been open N minutes; off: every pull counts'
    return
  }
  $want = $Pos[0].ToLower()
  if ($want -notmatch '^(first-command|off|minutes:\d+(\.\d+)?)$') { throw "earn is first-command, minutes:N or off, not '$want'" }
  Set-PokeshellConfigValue $State 'earn' $want
  Update-PokeshellRollCache -Root $RuntimeRoot -StateDir $State   # config.txt is in the cache stamp
  Write-Host "pokeshell: new pulls are earned by: $want"
}

function Get-HotkeySettingsPath {
  if ($Opts.settingspath) { return (Resolve-Path $Opts.settingspath).ProviderPath }
  foreach ($n in 'hotkey.tsv', 'safeuri.tsv') {
    $f = Join-Path $State $n
    if ([IO.File]::Exists($f)) { $x = [IO.File]::ReadAllText($f).Trim().Split("`t"); if ($x[0] -and (Test-Path $x[0])) { return $x[0] } }
  }
  $p = Get-PokeshellWtSettingsPath
  if (-not $p) { throw "Windows Terminal settings.json not found (pass -SettingsPath <path>)" }
  $p
}

# write settings.json the way install does: verify, back up, then replace in one step
function Save-HotkeySettings([string]$Path, $Orig, [string]$New, [string]$Tag) {
  [void](ConvertFrom-Jsonc $New)   # must still parse
  if ($New.Equals($Orig.text)) { return $null }
  $backupDir = Join-Path $State 'backups'
  [void][IO.Directory]::CreateDirectory($backupDir)
  $backup = Join-Path $backupDir ("settings-{0:yyyyMMdd-HHmmss}-$Tag.json" -f (Get-Date))
  Copy-Item -LiteralPath $Path -Destination $backup
  Write-WtSettingsFile $Path $New $Orig.bom
  $backup
}

# a state file's tab-separated fields (settings path, ...), or @() when it isn't there
function Read-StateTsv([string]$Name) {
  $f = Join-Path $State $Name
  if ([IO.File]::Exists($f)) { , @([IO.File]::ReadAllText($f).Trim().Split("`t")) } else { , @() }
}

function Remove-PokeshellHotkey([string]$Path) {
  $x = Read-StateTsv 'hotkey.tsv'
  $created = $x.Count -ge 3 -and $x[2] -eq '1'
  $orig = Read-WtSettingsFile $Path
  $new = Remove-PokeshellHotkeyText $orig.text -DropEmptyActions:$created
  $b = Save-HotkeySettings $Path $orig $new 'hotkey-off'
  Remove-Item (Join-Path $State 'hotkey.tsv') -ErrorAction SilentlyContinue
  $b
}

# "safeUriSchemes": ["pokeshell"] out of settings.json again, if we put it there (safeuri.tsv: path, created)
function Remove-PokeshellSafeScheme([string]$Path) {
  $x = Read-StateTsv 'safeuri.tsv'
  if (-not $x.Count) { return $null }
  $b = $null
  if ($Path -and (Test-Path $Path)) {
    $orig = Read-WtSettingsFile $Path
    $b = Save-HotkeySettings $Path $orig (Remove-PokeshellSafeSchemeText $orig.text -DropEmpty:($x.Count -ge 2 -and $x[1] -eq '1')) 'link-off'
  }
  Remove-Item (Join-Path $State 'safeuri.tsv') -ErrorAction SilentlyContinue
  $b
}

<#
The binder's two ways in from a pulled card, both set up by `pokeshell install` unless turned off (hotkey.off /
urlhandler.off, written by `pokeshell hotkey off` / `urlhandler off`):
  hotkey  a settings.json action + keybinding (default Ctrl+Shift+B): a split pane running binder.exe --pull latest
  link    Ctrl+click on the card's `binder` footer: pokeshell://binder?pull=<id>, registered under HKCU (binder-link.exe
          opens `wt -w 0 sp` on that pull), plus "safeUriSchemes": ["pokeshell"] so Windows Terminal opens it without
          its "may lead to an unsafe location" dialog
Returns @{ text (the settings text with them added); hotkey / scheme (what to record, or $null); link (binder-link.exe
or $null); notes }. Nothing is written here.
#>
function Get-BinderAccessPlan([string]$Text, [bool]$Hotkey = $true, [bool]$Link = $true, [string]$Keys) {
  $plan = @{ text = $Text; hotkey = $null; scheme = $null; link = $null; exe = $null; notes = [Collections.Generic.List[string]]::new() }
  $exe = Get-PokeshellBinderExe $RuntimeRoot
  if (-not $exe) {
    $plan.notes.Add($(if ($Packaged) { "this pokeshell package has no binder app: no Ctrl+Shift+B and no card link; ``binder`` shows the text binder" }
                      else { "the binder app isn't built (binder\build.ps1, then pokeshell install again): no Ctrl+Shift+B and no card link yet; ``binder`` shows the text binder" }))
    return $plan
  }
  $plan.exe = $exe
  if ($Hotkey) {
    $old = Read-StateTsv 'hotkey.tsv'
    if (-not $Keys) { $Keys = if ($old.Count -ge 2 -and $old[1]) { $old[1] } else { 'ctrl+shift+b' } }
    try {
      # take out what an earlier install added exactly as its removal would (an "actions" it created goes too), so
      # adding it again gives the same bytes: a re-install is idempotent
      $base = Remove-PokeshellHotkeyText $plan.text -DropEmptyActions:($old.Count -ge 3 -and $old[2] -eq '1')
      $res = Add-PokeshellHotkeyText $base (Get-PokeshellBinderCommand $exe $RuntimeRoot $State '--pull latest') $Keys
      $plan.text = $res.text
      $plan.hotkey = @{ combo = $Keys; created = ($res.created -or ($old.Count -ge 3 -and $old[2] -eq '1')) }
    } catch { $plan.notes.Add("no binder hotkey: $($_.Exception.Message) (pokeshell hotkey on -Keys <keys>)") }
  }
  if ($Link) {
    $linkExe = Get-PokeshellBinderLinkExe $exe
    if (-not $linkExe) { $plan.notes.Add("no card link: binder-link.exe isn't built next to $exe (binder\build.ps1)") }
    else {
      $plan.link = $linkExe
      $old = Read-StateTsv 'safeuri.tsv'
      $base = if ($old.Count) { Remove-PokeshellSafeSchemeText $plan.text -DropEmpty:($old.Count -ge 2 -and $old[1] -eq '1') } else { $plan.text }
      $res = Add-PokeshellSafeSchemeText $base
      $plan.text = $res.text
      if ($res.ours -or $old.Count) { $plan.scheme = @{ created = ($res.created -or ($old.Count -ge 2 -and $old[1] -eq '1')) } }
    }
  }
  $plan
}

# the settings text without what this plan adds (for the Remove(Add(x)) == Remove(x) check); only the parts the plan
# touched, so `hotkey on` keeps an existing card link and `link on` an existing hotkey
function Remove-BinderAccessText([string]$Text, $Plan) {
  $t = if ($Plan.hotkey) { Remove-PokeshellHotkeyText $Text -DropEmptyActions:($Plan.hotkey.created) } else { $Text }
  if ($Plan.link) { $t = Remove-PokeshellSafeSchemeText $t -DropEmpty:($Plan.scheme -and $Plan.scheme.created) }
  $t
}

# after settings.json was written: record the plan, and register the pokeshell:// handler (HKCU)
function Complete-BinderAccess($Plan, [string]$Path) {
  if ($Plan.hotkey) {
    [IO.File]::WriteAllText((Join-Path $State 'hotkey.tsv'), "$Path`t$($Plan.hotkey.combo)`t$(if ($Plan.hotkey.created) { '1' } else { '0' })")
    Remove-Item (Join-Path $State 'hotkey.off') -ErrorAction SilentlyContinue
  }
  if ($Plan.scheme) { [IO.File]::WriteAllText((Join-Path $State 'safeuri.tsv'), "$Path`t$(if ($Plan.scheme.created) { '1' } else { '0' })") }
  if ($Plan.link) {
    $ops = @(Set-PokeshellUrlHandler -Exe $Plan.exe -LinkExe $Plan.link -Root $RuntimeRoot -StateDir $State)
    [IO.File]::WriteAllText((Join-Path $State 'urlhandler.txt'), $Plan.link)
    Remove-Item (Join-Path $State 'urlhandler.off') -ErrorAction SilentlyContinue
    if ($env:POKESHELL_REGISTRY -eq 'dryrun') { foreach ($o in $ops) { Write-Host "  (registry dry run) would $o" -ForegroundColor DarkGray } }
  }
}

# `pokeshell hotkey on|off`: a Windows Terminal key (default Ctrl+Shift+B) that opens the binder in a split pane on
# the newest pull. `pokeshell install` adds it by default; `off` also keeps later installs from adding it again.
function Invoke-Hotkey {
  . (Join-Path $PSScriptRoot 'lib\wtsettings.ps1')
  $path = Get-HotkeySettingsPath
  if (-not $Pos) {
    $acts = Get-JsoncMember (ConvertFrom-Jsonc (Read-WtSettingsFile $path).text) 'actions'
    $on = $acts -and @($acts.items | Where-Object { Test-PokeshellHotkeyNode $_ }).Count -gt 0
    Write-Host "hotkey: $(if ($on) { 'on' } else { 'off' })  ($path)  (pokeshell hotkey on|off [-Keys ctrl+shift+b])"
    return
  }
  $want = $Pos[0].ToLower()
  if ($want -in 'off', 'remove', 'uninstall') {
    $b = Remove-PokeshellHotkey $path
    [IO.File]::WriteAllText((Join-Path $State 'hotkey.off'), 'pokeshell install leaves the binder hotkey out (pokeshell hotkey on adds it back)')
    Write-Host "pokeshell: binder hotkey removed from $path$(if ($b) { " (backup: $b)" })"
    return
  }
  if ($want -notin 'on', 'install') { throw "hotkey is on or off, not '$want'" }
  if (-not (Get-PokeshellBinderExe $RuntimeRoot)) { throw "the binder app isn't built (binder\build.ps1), so there is nothing for the hotkey to open" }
  $orig = Read-WtSettingsFile $path
  $plan = Get-BinderAccessPlan $orig.text -Link $false -Keys $Opts['keys']
  if (-not $plan.hotkey) { throw ($plan.notes -join '; ') }
  # verify like install: removing it again gives back exactly what was there
  if (-not (Remove-BinderAccessText $plan.text $plan).Equals((Remove-PokeshellHotkeyText $orig.text))) { throw "verification failed: removing the hotkey again would not restore settings.json; nothing written" }
  $b = Save-HotkeySettings $path $orig $plan.text 'hotkey'
  Complete-BinderAccess $plan $path
  Write-Host "pokeshell: $($plan.hotkey.combo) opens the binder in a split pane ($path$(if ($b) { "; backup: $b" }))" -ForegroundColor Green
}

# `pokeshell urlhandler on|off [-DryRun]`: the card's Ctrl+click link (pokeshell:// under HKCU\Software\Classes, and
# "safeUriSchemes" in settings.json). `pokeshell install` sets it up by default; `off` keeps later installs from it.
function Invoke-UrlHandler {
  . (Join-Path $PSScriptRoot 'lib\wtsettings.ps1')
  $f = Join-Path $State 'urlhandler.txt'
  $dry = Has @('dryrun')
  if (-not $Pos) { Write-Host "urlhandler: $(if (Test-Path $f) { 'on' } else { 'off' })  (pokeshell urlhandler on|off [-DryRun])"; return }
  $want = $Pos[0].ToLower()
  if ($want -in 'off', 'remove', 'uninstall') {
    $ops = @(Set-PokeshellUrlHandler -Remove -DryRun:$dry)
    if (-not $dry) {
      $x = Read-StateTsv 'safeuri.tsv'
      if ($x.Count) { [void](Remove-PokeshellSafeScheme $x[0]) }
      Remove-Item $f -ErrorAction SilentlyContinue
      [IO.File]::WriteAllText((Join-Path $State 'urlhandler.off'), 'pokeshell install leaves the card link out (pokeshell urlhandler on adds it back)')
    }
  } elseif ($want -in 'on', 'install') {
    $exe = Get-PokeshellBinderExe $RuntimeRoot
    if (-not $exe) { throw "the binder app isn't built (binder\build.ps1), so there is nothing for pokeshell:// links to open" }
    $linkExe = Get-PokeshellBinderLinkExe $exe
    if (-not $linkExe) { throw "binder-link.exe isn't built next to $exe (binder\build.ps1)" }
    if ($dry) { $ops = @(Set-PokeshellUrlHandler -Exe $exe -LinkExe $linkExe -Root $RuntimeRoot -StateDir $State -DryRun) }
    else {
      # Windows Terminal's settings.json, if there is one (other terminals only need the handler)
      $path = try { Get-HotkeySettingsPath } catch { $null }
      if ($path) {
        $orig = Read-WtSettingsFile $path
        $plan = Get-BinderAccessPlan $orig.text -Hotkey $false
        if (-not (Remove-BinderAccessText $plan.text $plan).Equals((Remove-PokeshellSafeSchemeText $orig.text))) { throw "verification failed: removing the link again would not restore settings.json; nothing written" }
        [void](Save-HotkeySettings $path $orig $plan.text 'link')
        $plan.link = $null   # registered below
        Complete-BinderAccess $plan $path
      }
      $ops = @(Set-PokeshellUrlHandler -Exe $exe -LinkExe $linkExe -Root $RuntimeRoot -StateDir $State)
      [IO.File]::WriteAllText($f, $linkExe); Remove-Item (Join-Path $State 'urlhandler.off') -ErrorAction SilentlyContinue
    }
  } else { throw "urlhandler is on or off, not '$want'" }
  $regDry = $dry -or $env:POKESHELL_REGISTRY -eq 'dryrun'
  foreach ($o in $ops) { Write-Host "  $(if ($regDry) { 'would ' })$o" }
  Write-Host "pokeshell: pokeshell:// handler $(if ($want -in 'on', 'install') { 'registered' } else { 'removed' })$(if ($dry) { ' (dry run: nothing changed)' } elseif ($regDry) { ' (registry dry run)' })"
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
  foreach ($id in Get-PokeshellPackIds $Root) {
    $rec = Join-Path $Root "dist\$id\.cardart.json"
    if ([IO.File]::Exists($rec)) {
      $r = [IO.File]::ReadAllText($rec) | ConvertFrom-Json
      Write-Host "card art ${id}: $($r.repo) release $($r.tag) ($(@($r.parts.PSObject.Properties | ForEach-Object Name) -join ', '))"
    }
  }
}

# re-run install with the same -SettingsPath / -Shell, in a fresh process of this edition, from $Base
function Invoke-InstallFrom([string]$Base) {
  $exe = if ($PSVersionTable.PSEdition -eq 'Core') { Join-Path $PSHOME 'pwsh.exe' } else { Join-Path $PSHOME 'powershell.exe' }
  $a = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $Base 'scripts\pokeshell.ps1'), 'install')
  if ($Opts.settingspath) { $a += '-SettingsPath', $Opts.settingspath }
  if ($Opts.shell) { $a += '-Shell', $Opts.shell }
  if ($Opts.art) { $a += '-Art', $Opts.art }
  if (Has 'artstillonly') { $a += '-ArtStillOnly' }
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
# (not for --json: other tools parse stdout as one JSON document)
if ($Packaged -and $Command -notin 'install', 'uninstall', 'update', 'version' -and -not (Has 'json')) {
  $cv = Get-CurrentVersion
  if ($cv -and $cv -ne $Version) { Write-Host "pokeshell: module $Version is installed but new tabs still run $cv; run pokeshell install to switch them" -ForegroundColor Yellow }
}

try {
switch ($Command) {
  ''           { Show-Help }
  'help'       { Show-Help }
  'pack'       { Invoke-Pack }
  'odds'       { Invoke-Odds }
  'collection' { if (Has 'json') { . (Join-Path $PSScriptRoot 'lib\jsonapi.ps1'); Invoke-PokeshellCollectionJson (Get-JsonPackFilter) } else { Invoke-Collection } }
  'binder'     { Invoke-Binder }
  'earn'       { Invoke-Earn }
  'hotkey'     { Invoke-Hotkey }
  'urlhandler' { Invoke-UrlHandler }
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
  'version'    { if (Has 'json') { . (Join-Path $PSScriptRoot 'lib\jsonapi.ps1'); Invoke-PokeshellVersionJson } else { Invoke-Version } }
  default      { Write-Host "pokeshell: unknown command '$Command'" -ForegroundColor Red; Show-Help }
}
} catch {
  if (Has 'json') {   # --json: the error as JSON on stdout too (the exit code says it failed)
    $m = $_.Exception.Message.Replace('\', '\\').Replace('"', '\"') -replace '[\x00-\x1f]', ' ' -replace '[^\x00-\x7f]', '?'
    [Console]::Out.Write("{`"error`":`"$m`"}`n")
  } else { Write-Host "pokeshell: $($_.Exception.Message)" -ForegroundColor Red }
  exit 1
}
