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

# pack.json + display names from art/<id>.json (falls back to a title-cased id while art is missing)
function Read-PokeshellPack([string]$Root, [string]$Id) {
  $dir = Join-Path $Root "packs\$Id"
  $pack = Get-Content (Join-Path $dir 'pack.json') -Raw -Encoding UTF8 | ConvertFrom-Json
  $names = [ordered]@{}
  foreach ($c in $pack.characters) {
    $artFile = Join-Path $dir "art\$c.json"
    $name = $null
    if (Test-Path $artFile) { try { $name = (Get-Content $artFile -Raw -Encoding UTF8 | ConvertFrom-Json).name } catch { } }
    $names[$c] = if ($name) { $name } else { ConvertTo-PokeshellTitle $c }
  }
  $pack | Add-Member -NotePropertyName names -NotePropertyValue $names -Force
  $pack | Add-Member -NotePropertyName dir -NotePropertyValue $dir -Force
  $pack
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
    foreach ($c in $pack.characters) { $body.Add("char`t$c`t$($pack.names[$c])") }
    $tiers = @($pack.tiers)
    for ($i = 0; $i -lt $tiers.Count; $i++) {
      $t = $tiers[$i]
      $body.Add("tier`t$($t.id)`t$($t.label)`t$($t.art)")
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
The runtime a new tab needs, as (from, to) pairs relative to a module/checkout root: the $PROFILE hook and
its lib, the core's source (its mtime names the compiled DLL), the command shim, pack.json + art names,
shaders, and the prebuilt art.
#>
function Get-PokeshellRuntimeFiles([string]$Root) {
  $rel = 'scripts\pokeshell-profile.ps1', 'scripts\tab-color-watch.ps1', 'scripts\pokeshell.cmd',
         'scripts\lib\roll.ps1', 'scripts\lib\common.ps1', 'scripts\lib\Pokeshell.cs'
  foreach ($r in $rel) { [pscustomobject]@{ from = Join-Path $Root $r; to = $r } }
  [pscustomobject]@{ from = Join-Path $Root 'scripts\lib\pokeshell-shim.ps1'; to = 'scripts\pokeshell.ps1' }
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

function Get-PokeshellWtSettingsPath {
  $candidates = @(
    (Join-Path $env:LOCALAPPDATA 'Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json'),
    (Join-Path $env:LOCALAPPDATA 'Packages\Microsoft.WindowsTerminalPreview_8wekyb3d8bbwe\LocalState\settings.json'),
    (Join-Path $env:LOCALAPPDATA 'Microsoft\Windows Terminal\settings.json')
  )
  $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
}
