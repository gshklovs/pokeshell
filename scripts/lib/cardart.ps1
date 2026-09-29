<#
cardart.ps1: the card art as GitHub release assets, shared by pokeshell, opshell and any sister project.
Copy this file as is (keep it byte-identical across the repos); nothing in it names a product. The design, the
file formats and the maintainer steps are in pokeshell's docs/ART_RELEASES.md.

The built art (dist/<pack>/*.ans, *.anim) is not in the code repo. It is published as zip assets of a release on a
separate art repo, and art.json (tracked, at the root of the code repo) pins which release to install:

  { "repo": "owner/x-art", "code_repo": "owner/x",
    "packs": [ { "id": "pokemon", "parts": [ { "part": "still", "ext": "ans" },
                                           { "part": "anim", "ext": "anim", "optional": true } ] } ],
    "tag": "art-2026-09-29", "base_url": "https://github.com/owner/x-art/releases/download",
    "assets": [ { "pack": "pokemon", "part": "still", "name": "pokemon-still-art-2026-09-29.zip",
                  "sha256": "<hex>", "size": 123, "files": 684, "cards": 342, "optional": false }, ... ] }

An asset's URL is <base_url>/<tag>/<name>. The zip holds manifest.json (pack, part, version = the tag, source
commit, card count, every file with its sha256) and dist/<pack>/<file>.<ext>, nothing else.

Installed art is recorded per pack in dist/<pack>/.cardart.json (which release, which parts, which files). With it,
installs are idempotent (a part whose sha256 already matches is not downloaded again), a newer pinned release
replaces exactly the files the older one installed, and a local build (files newer than the record, or files it
doesn't list, or no record at all) is recognised and left alone unless the caller asks for a download.

Windows PowerShell 5.1 only: .NET's HttpWebRequest for the download, Get-FileHash, System.IO.Compression for the zip.
#>

$script:CardArtEntryRx = '^dist/([a-z0-9][a-z0-9_-]*)/([A-Za-z0-9][A-Za-z0-9._-]*)\.([a-z0-9]+)$'

function Read-CardArtConfig([string]$Path) {
  if (-not [IO.File]::Exists($Path)) { throw "art config not found: $Path" }
  $c = [IO.File]::ReadAllText($Path, [Text.Encoding]::UTF8) | ConvertFrom-Json
  if (-not $c.repo) { throw "$Path has no repo" }
  $c
}

function Write-CardArtJson([string]$Path, $Object) {
  $json = $Object | ConvertTo-Json -Depth 8
  $tmp = "$Path.$PID.tmp"
  [IO.File]::WriteAllText($tmp, $json + "`n", [Text.UTF8Encoding]::new($false))
  if ([IO.File]::Exists($Path)) { [IO.File]::Delete($Path) }
  [IO.File]::Move($tmp, $Path)
}

function Get-CardArtSha256([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }

# ------------------------------------------------------------------------------------------ install side

function Read-CardArtRecord([string]$Root, [string]$Pack) {
  $f = Join-Path $Root "dist\$Pack\.cardart.json"
  if (-not [IO.File]::Exists($f)) { return $null }
  try { [IO.File]::ReadAllText($f, [Text.Encoding]::UTF8) | ConvertFrom-Json } catch { $null }
}

<#
What dist\<pack> holds: 'none' (no art), 'release' (exactly what the record lists, untouched since),
'local' (art without a record: a local build), or 'modified' (a record, plus files newer than it or not in it:
a local build on top of a release).
#>
function Get-CardArtLocalState([string]$Root, [string]$Pack, $Record) {
  $dir = Join-Path $Root "dist\$Pack"
  $files = @(Get-ChildItem -LiteralPath $dir -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -ne '.cardart.json' -and $_.Extension -in '.ans', '.anim' })
  if (-not $files) { return 'none' }
  if (-not $Record) { return 'local' }
  $known = @{}
  foreach ($p in $Record.parts.PSObject.Properties) { foreach ($n in @($p.Value.files)) { $known[[string]$n] = $true } }
  $recTime = [IO.File]::GetLastWriteTimeUtc((Join-Path $dir '.cardart.json')).AddSeconds(2)
  foreach ($f in $files) { if (-not $known[$f.Name] -or $f.LastWriteTimeUtc -gt $recTime) { return 'modified' } }
  'release'
}

function Test-CardArtPartCurrent([string]$Root, $Record, $Asset) {
  if (-not $Record -or -not $Record.parts) { return $false }
  $p = $Record.parts.PSObject.Properties[[string]$Asset.part]
  if (-not $p -or [string]$p.Value.sha256 -ne [string]$Asset.sha256) { return $false }
  foreach ($n in @($p.Value.files)) { if (-not [IO.File]::Exists((Join-Path $Root "dist\$($Asset.pack)\$n"))) { return $false } }
  $true
}

# GET $Url into $Dest with a progress line; http(s) and file:// (tests). Throws on any failure.
function Invoke-CardArtDownload([string]$Url, [string]$Dest, [long]$Size, [string]$Label) {
  [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
  $req = [Net.WebRequest]::Create($Url)
  if ($req -is [Net.HttpWebRequest]) {
    $req.Timeout = 30000; $req.ReadWriteTimeout = 60000; $req.AllowAutoRedirect = $true
    $req.UserAgent = 'cardart-install (WindowsPowerShell)'
  }
  $resp = $req.GetResponse()
  try {
    $in = $resp.GetResponseStream()
    $out = [IO.File]::Create($Dest)
    try {
      $buf = New-Object byte[] 262144; $got = 0L; $shown = -1; $total = if ($Size -gt 0) { $Size } else { $resp.ContentLength }
      while (($n = $in.Read($buf, 0, $buf.Length)) -gt 0) {
        $out.Write($buf, 0, $n); $got += $n
        if ($total -gt 0) {
          $pct = [int][Math]::Floor(100.0 * $got / $total)
          if ($pct -ne $shown -and ($pct % 5 -eq 0)) { $shown = $pct; Write-Host -NoNewline ("`r  downloading {0}: {1,3}% of {2:N1} MB" -f $Label, $pct, ($total / 1MB)) }
        }
      }
      if ($total -gt 0) { Write-Host '' }
    } finally { $out.Dispose(); $in.Dispose() }
  } finally { $resp.Close() }
}

<#
A verified copy of $Asset in $CacheDir: reused when its sha256 matches, else downloaded. Returns
@{ ok; path } or @{ ok = $false; kind = 'offline' | 'checksum'; message }.
#>
function Get-CardArtAsset($Config, $Asset, [string]$CacheDir) {
  [void][IO.Directory]::CreateDirectory($CacheDir)
  $name = [string]$Asset.name
  if ($name -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]*\.zip$') { return @{ ok = $false; kind = 'checksum'; message = "art.json names an odd asset '$name'; refusing it" } }
  $want = ([string]$Asset.sha256).ToLowerInvariant()
  $cached = Join-Path $CacheDir $name
  if ([IO.File]::Exists($cached)) {
    if ((Get-CardArtSha256 $cached) -eq $want) { return @{ ok = $true; path = $cached; cached = $true } }
    [IO.File]::Delete($cached)
  }
  $base = if ($env:CARDART_BASE_URL) { $env:CARDART_BASE_URL } else { [string]$Config.base_url }
  $url = "$($base.TrimEnd('/'))/$($Config.tag)/$name"
  $tmp = Join-Path $CacheDir "$name.part-$PID"
  try { Invoke-CardArtDownload $url $tmp ([long]$Asset.size) $name }
  catch {
    if ([IO.File]::Exists($tmp)) { [IO.File]::Delete($tmp) }
    $m = $_.Exception.Message; if ($_.Exception.InnerException) { $m = $_.Exception.InnerException.Message }
    return @{ ok = $false; kind = 'offline'; message = "could not download $url ($m)" }
  }
  $got = Get-CardArtSha256 $tmp
  if ($got -ne $want) {
    [IO.File]::Delete($tmp)
    return @{ ok = $false; kind = 'checksum'; message = "checksum mismatch for $name (expected $want, got $got): refusing to install it" }
  }
  if ([IO.File]::Exists($cached)) { [IO.File]::Delete($cached) }
  [IO.File]::Move($tmp, $cached)
  @{ ok = $true; path = $cached; cached = $false }
}

<#
Unpack a verified asset into $Root\dist\<pack>. Every entry must be manifest.json or dist/<the asset's pack>/<safe
name>.<the part's extension>, and the manifest must name the same pack, part and files. Files are unpacked next to
the pack folder first and then moved in (each replaced file is deleted first, so nothing is written in place).
Returns the file names installed.
#>
function Expand-CardArtAsset([string]$Zip, [string]$Root, $Asset) {
  Add-Type -AssemblyName System.IO.Compression, System.IO.Compression.FileSystem
  $pack = [string]$Asset.pack
  $za = [IO.Compression.ZipFile]::OpenRead($Zip)
  $stage = Join-Path $Root "dist\.cardart-$pack-$PID"
  try {
    $me = $za.GetEntry('manifest.json')
    if (-not $me) { throw "$($Asset.name) has no manifest.json" }
    $sr = New-Object IO.StreamReader($me.Open(), [Text.Encoding]::UTF8)
    try { $manifest = $sr.ReadToEnd() | ConvertFrom-Json } finally { $sr.Dispose() }
    if ([string]$manifest.pack -ne $pack -or [string]$manifest.part -ne [string]$Asset.part) { throw "$($Asset.name): its manifest is for $($manifest.pack)/$($manifest.part), not $pack/$($Asset.part)" }
    $listed = @{}; foreach ($f in @($manifest.files)) { $listed[[string]$f.path] = $true }
    $names = New-Object Collections.Generic.List[string]
    if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force }
    [void][IO.Directory]::CreateDirectory($stage)
    foreach ($e in $za.Entries) {
      if ($e.FullName -eq 'manifest.json') { continue }
      if ($e.FullName -notmatch $script:CardArtEntryRx -or $Matches[1] -ne $pack) { throw "$($Asset.name): unexpected entry '$($e.FullName)'" }
      if (-not $listed[$e.FullName]) { throw "$($Asset.name): '$($e.FullName)' is not in its manifest" }
      $names.Add($Matches[2] + '.' + $Matches[3])
      [IO.Compression.ZipFileExtensions]::ExtractToFile($e, (Join-Path $stage $names[$names.Count - 1]), $true)
    }
    if ($names.Count -ne $listed.Count) { throw "$($Asset.name): the manifest lists $($listed.Count) files, the zip has $($names.Count)" }
  } catch { Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue; throw }
  finally { $za.Dispose() }
  $dir = Join-Path $Root "dist\$pack"
  [void][IO.Directory]::CreateDirectory($dir)
  $now = [DateTime]::UtcNow
  foreach ($n in $names) {
    $from = Join-Path $stage $n; $to = Join-Path $dir $n
    [IO.File]::SetLastWriteTimeUtc($from, $now)   # installed files are "as of the record", so a later local build is newer
    try { if ([IO.File]::Exists($to)) { [IO.File]::Delete($to) }; [IO.File]::Move($from, $to) }
    catch { [IO.File]::Copy($from, $to, $true); [IO.File]::SetLastWriteTimeUtc($to, $now) }   # a tab holding the old file open
  }
  Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue
  , $names.ToArray()
}

<#
Install the release art.json pins into $Root (a checkout or an installed module version).
  -Mode auto      (default) download what is missing or older than art.json; a local build is kept
        download  download even over a local build (same-named files are replaced; other local files stay)
        local     never download: use whatever dist\ holds (a local build)
        skip      don't touch the art at all
  -StillOnly      skip the optional parts (the .anim effect loops)
Never throws for a failed download: returns one result per asset
  @{ pack; part; status = current|installed|local|skipped|offline|checksum|error; message }
and prints what it did. Packs whose folder isn't in $Root are left out.
#>
function Install-CardArt([string]$Root, [string]$ConfigPath, [string]$Mode = 'auto', [string]$CacheDir, [switch]$StillOnly, [string]$Prefix = 'art') {
  $results = New-Object Collections.Generic.List[object]
  if ($Mode -eq 'skip') { return $results.ToArray() }
  try { $cfg = Read-CardArtConfig $ConfigPath }
  catch { Write-Host "${Prefix}: $($_.Exception.Message); card art not installed" -ForegroundColor Yellow; return $results.ToArray() }
  $assets = @($cfg.assets)
  if (-not $cfg.tag -or -not $assets) { Write-Host "${Prefix}: art.json pins no art release yet; card art not installed" -ForegroundColor Yellow; return $results.ToArray() }
  foreach ($grp in ($assets | Group-Object pack)) {
    $pack = $grp.Name
    if (-not [IO.File]::Exists((Join-Path $Root "packs\$pack\pack.json"))) { continue }
    $record = Read-CardArtRecord $Root $pack
    $local = Get-CardArtLocalState $Root $pack $record
    $parts = [ordered]@{}
    if ($record -and $record.parts) { foreach ($p in $record.parts.PSObject.Properties) { $parts[$p.Name] = $p.Value } }
    $changed = $false
    foreach ($a in $grp.Group) {
      $r = @{ pack = $pack; part = [string]$a.part; status = ''; message = '' }
      $label = "$pack/$($a.part)"
      if ($StillOnly -and $a.optional) { $r.status = 'skipped'; $r.message = "$label skipped (-ArtStillOnly)" }
      elseif ($Mode -eq 'local') { $r.status = 'local'; $r.message = "$label not downloaded (-Art local): using dist\$pack as built" }
      elseif ($Mode -eq 'auto' -and $local -in 'local', 'modified') {
        $r.status = 'local'; $r.message = "$label kept: dist\$pack has a local build (-Art download replaces it with release $($cfg.tag))"
      }
      elseif (Test-CardArtPartCurrent $Root $record $a) { $r.status = 'current'; $r.message = "$label is release $($cfg.tag), up to date" }
      else {
        $got = Get-CardArtAsset $cfg $a $CacheDir
        if (-not $got.ok) { $r.status = $got.kind; $r.message = $got.message }
        else {
          try {
            $names = Expand-CardArtAsset $got.path $Root $a
            $old = $parts[[string]$a.part]
            if ($old) {   # files the previous release of this part installed that this one doesn't have
              $keep = @{}; foreach ($n in $names) { $keep[$n] = $true }
              foreach ($p in $parts.Keys) { if ($p -ne [string]$a.part) { foreach ($n in @($parts[$p].files)) { $keep[[string]$n] = $true } } }
              foreach ($n in @($old.files)) { if (-not $keep[[string]$n]) { Remove-Item -LiteralPath (Join-Path $Root "dist\$pack\$n") -Force -ErrorAction SilentlyContinue } }
            }
            $parts[[string]$a.part] = [pscustomobject]@{ name = [string]$a.name; sha256 = [string]$a.sha256; files = @($names) }
            $changed = $true
            $r.status = 'installed'; $r.message = "$label installed from $($cfg.repo) release $($cfg.tag): $($names.Count) files$(if ($got.cached) { ' (cached download)' })"
          } catch { $r.status = 'error'; $r.message = "$label could not be unpacked: $($_.Exception.Message)" }
        }
      }
      $results.Add([pscustomobject]$r)
      $color = switch ($r.status) { 'installed' { 'Green' } 'current' { 'DarkGray' } 'checksum' { 'Red' } 'error' { 'Red' } default { 'Yellow' } }
      Write-Host "${Prefix}: $($r.message)" -ForegroundColor $color
    }
    if ($changed) {
      Write-CardArtJson (Join-Path $Root "dist\$pack\.cardart.json") ([ordered]@{ repo = [string]$cfg.repo; tag = [string]$cfg.tag; installed = [DateTime]::UtcNow.ToString('o'); parts = $parts })
    }
  }
  # keep only the cached zips art.json still pins
  if ($CacheDir -and [IO.Directory]::Exists($CacheDir)) {
    $pinned = @{}; foreach ($a in $assets) { $pinned[[string]$a.name] = $true }
    Get-ChildItem -LiteralPath $CacheDir -File | Where-Object { -not $pinned[$_.Name] } | ForEach-Object { try { $_.Delete() } catch { } }
  }
  $bad = @($results | Where-Object { $_.status -in 'offline', 'checksum', 'error' })
  if ($bad) {
    Write-Host "${Prefix}: the code is installed; packs without their art simply don't roll until it is there. Re-run install when online, or build the art locally (tools\README.md)." -ForegroundColor Yellow
  }
  $results.ToArray()
}

# ------------------------------------------------------------------------------------------ publish side

<#
Pack $Source\dist\<pack>\*.<ext> into $OutDir\<pack>-<part>-<tag>.zip with a manifest. Each file is read once:
the bytes that are hashed are the bytes that are zipped. Returns the asset entry for art.json.
#>
function New-CardArtAsset([string]$Source, [string]$Pack, [string]$Part, [string]$Ext, [string]$Tag, [string]$OutDir,
                          [string]$SourceCommit, [string]$SourceRepo, [bool]$Optional) {
  Add-Type -AssemblyName System.IO.Compression, System.IO.Compression.FileSystem
  $dir = Join-Path $Source "dist\$Pack"
  $files = @(Get-ChildItem -LiteralPath $dir -File -Filter "*.$Ext" -ErrorAction SilentlyContinue | Where-Object { $_.Extension -eq ".$Ext" } | Sort-Object Name)
  if (-not $files) { throw "no dist\$Pack\*.$Ext in $Source" }
  $name = "$Pack-$Part-$Tag.zip"
  [void][IO.Directory]::CreateDirectory($OutDir)
  $zipPath = Join-Path $OutDir $name
  if ([IO.File]::Exists($zipPath)) { [IO.File]::Delete($zipPath) }
  $sha = [Security.Cryptography.SHA256]::Create()
  $entries = New-Object Collections.Generic.List[object]
  $fs = [IO.File]::Open($zipPath, 'CreateNew')
  $za = New-Object IO.Compression.ZipArchive($fs, [IO.Compression.ZipArchiveMode]::Create)
  try {
    foreach ($f in $files) {
      $path = "dist/$Pack/$($f.Name)"
      if ($path -notmatch $script:CardArtEntryRx) { throw "unsafe file name: $($f.Name)" }
      $bytes = [IO.File]::ReadAllBytes($f.FullName)
      $h = -join ($sha.ComputeHash($bytes) | ForEach-Object { $_.ToString('x2') })
      $e = $za.CreateEntry($path, [IO.Compression.CompressionLevel]::Optimal)
      $e.LastWriteTime = $f.LastWriteTime
      $s = $e.Open(); try { $s.Write($bytes, 0, $bytes.Length) } finally { $s.Dispose() }
      $entries.Add([ordered]@{ path = $path; sha256 = $h; size = $bytes.Length })
    }
    $cards = @($files | Where-Object { $_.BaseName -notmatch '-shiny$' }).Count
    $manifest = [ordered]@{
      format = 1; pack = $Pack; part = $Part; version = $Tag; extension = $Ext
      source_repo = $SourceRepo; source_commit = $SourceCommit; created = [DateTime]::UtcNow.ToString('o')
      cards = $cards; file_count = $entries.Count; files = $entries.ToArray()
    }
    $me = $za.CreateEntry('manifest.json', [IO.Compression.CompressionLevel]::Optimal)
    $w = New-Object IO.StreamWriter($me.Open(), [Text.UTF8Encoding]::new($false))
    try { $w.Write(($manifest | ConvertTo-Json -Depth 5)) } finally { $w.Dispose() }
  } finally { $za.Dispose(); $fs.Dispose(); $sha.Dispose() }
  [pscustomobject][ordered]@{
    pack = $Pack; part = $Part; name = $name; sha256 = (Get-CardArtSha256 $zipPath); size = (Get-Item -LiteralPath $zipPath).Length
    files = $entries.Count; cards = $cards; optional = $Optional; raw_bytes = [long](($entries | ForEach-Object { $_.size } | Measure-Object -Sum).Sum)
    path = $zipPath
  }
}

# every entry of a built asset, checked against the rule install enforces; returns a summary line per extension
function Test-CardArtAssetContents([string]$Zip, [string]$Pack, [string]$Ext) {
  Add-Type -AssemblyName System.IO.Compression, System.IO.Compression.FileSystem
  $za = [IO.Compression.ZipFile]::OpenRead($Zip)
  try {
    $bad = @(); $n = 0; $hasManifest = $false
    foreach ($e in $za.Entries) {
      if ($e.FullName -eq 'manifest.json') { $hasManifest = $true; continue }
      if ($e.FullName -match $script:CardArtEntryRx -and $Matches[1] -eq $Pack -and $Matches[3] -eq $Ext) { $n++ } else { $bad += $e.FullName }
    }
    [pscustomobject]@{ ok = ($hasManifest -and -not $bad -and $n -gt 0); files = $n; manifest = $hasManifest; unexpected = $bad }
  } finally { $za.Dispose() }
}
