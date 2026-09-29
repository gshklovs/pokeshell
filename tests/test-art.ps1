<#
The card art release path (scripts\lib\cardart.ps1, tools\publish_art.ps1's archive builder, `pokeshell install -Art`):
fixture releases served from file:// URLs, so it runs offline, into temp roots and a temp state folder. Never touches
this checkout's dist\, %LOCALAPPDATA%\pokeshell, the real settings.json or $PROFILE.
  powershell -NoProfile -File tests\test-art.ps1            # offline
  powershell -NoProfile -File tests\test-art.ps1 -Online    # also downloads the release art.json pins (into temp)
#>
param([switch]$Online)
. (Join-Path $PSScriptRoot '_setup.ps1')
. (Join-Path $RepoRoot 'scripts\lib\cardart.ps1')
Add-Type -AssemblyName System.IO.Compression, System.IO.Compression.FileSystem
$work = Join-Path ([IO.Path]::GetTempPath()) "pokeshell-test-art-$PID"
Remove-Item $work -Recurse -Force -ErrorAction SilentlyContinue
[void][IO.Directory]::CreateDirectory($work)
$utf8 = [Text.UTF8Encoding]::new($false)
$esc = [char]27
$packJson = '{ "id": "fx", "name": "Fixture", "shiny_chance": 0,
  "tiers": [ { "id": "common", "label": "common", "weight": 1, "skins": {}, "frame": "plain" } ],
  "cards": { "fx-1": { "character": "bob", "tier": "common", "name": "Bob", "number": "1/2" },
             "fx-2": { "character": "amy", "tier": "common", "name": "Amy", "number": "2/2" } } }'

function New-Root([string]$Name) {
  $r = Join-Path $work $Name
  [void][IO.Directory]::CreateDirectory((Join-Path $r 'packs\fx'))
  [IO.File]::WriteAllText((Join-Path $r 'packs\fx\pack.json'), $packJson, $utf8)
  $r
}
function Set-Art([string]$Root, [hashtable]$Files) {
  $d = Join-Path $Root 'dist\fx'; [void][IO.Directory]::CreateDirectory($d)
  foreach ($k in $Files.Keys) { [IO.File]::WriteAllText((Join-Path $d $k), $Files[$k], $utf8) }
}
function Get-Names([string]$Root) {
  [string[]]$n = @(Get-ChildItem (Join-Path $Root 'dist\fx') -File -ErrorAction SilentlyContinue | Where-Object Name -ne '.cardart.json' | ForEach-Object Name)
  [Array]::Sort($n, [StringComparer]::Ordinal); , $n
}
function Get-Print([string]$Root) { (Get-ChildItem (Join-Path $Root 'dist\fx') -File -Force -ErrorAction SilentlyContinue | Sort-Object Name | ForEach-Object { "$($_.Name)|$($_.Length)|$($_.LastWriteTimeUtc.Ticks)" }) -join ';' }

# ---- a fixture "release": two tags of the fx pack, published into a folder served as file:// URLs
$rel = Join-Path $work 'release'
function New-Release([string]$Tag, [hashtable]$Files) {
  $src = New-Root "src-$Tag"; Set-Art $src $Files
  $assets = foreach ($p in @(@('still', 'ans', $false), @('anim', 'anim', $true))) {
    New-CardArtAsset -Source $src -Pack fx -Part $p[0] -Ext $p[1] -Tag $Tag -OutDir (Join-Path $rel $Tag) -SourceCommit 'abc123' -SourceRepo 'test/fx' -Optional $p[2]
  }
  $assets
}
function Write-ArtJson([string]$Path, [string]$Tag, $Assets, [string]$Base) {
  if (-not $Base) { $Base = ([Uri]$rel).AbsoluteUri }
  Write-CardArtJson $Path ([ordered]@{ repo = 'test/fx-art'; code_repo = 'test/fx'; packs = @(); tag = $Tag; base_url = $Base
    assets = @($Assets | ForEach-Object { [ordered]@{ pack = $_.pack; part = $_.part; name = $_.name; sha256 = $_.sha256; size = $_.size; files = $_.files; cards = $_.cards; optional = $_.optional } }) })
}
$v1Files = @{ 'bob-fx-1.ans' = "$esc[0;38;2;9;9;9m$([char]0x2580)$esc[0m`n"; 'bob-fx-1-shiny.ans' = "$esc[0;38;2;1;1;1m$([char]0x2580)$esc[0m`n"
              'amy-fx-2.ans' = "$esc[0;38;2;5;5;5m$([char]0x2584)$esc[0m`n"; 'bob-fx-1.anim' = "{`"lines`": 1, `"fps`": 12, `"frames`": 1, `"final`": 0}`n`f$([char]0x2580)`n" }
$v1 = @(New-Release 'art-t1' $v1Files)
$v2Files = @{ 'bob-fx-1.ans' = "$esc[0;38;2;9;9;90m$([char]0x2580)$esc[0m`n"; 'amy-fx-2.ans' = $v1Files['amy-fx-2.ans']; 'bob-fx-1.anim' = $v1Files['bob-fx-1.anim'] }
$v2 = @(New-Release 'art-t2' $v2Files)
$j1 = Join-Path $work 'art-t1.json'; Write-ArtJson $j1 'art-t1' $v1
$j2 = Join-Path $work 'art-t2.json'; Write-ArtJson $j2 'art-t2' $v2
$cache = Join-Path $work 'cache'

Write-Host '1. the archives' -ForegroundColor Cyan
$still = $v1 | Where-Object part -eq 'still'
$chk = Test-CardArtAssetContents $still.path 'fx' 'ans'
Assert ($chk.ok -and $chk.files -eq 3 -and $still.cards -eq 2) "still zip: manifest.json + 3 dist/fx/*.ans, 2 cards (not counting shinies)"
$za = [IO.Compression.ZipFile]::OpenRead($still.path)
$m = (New-Object IO.StreamReader($za.GetEntry('manifest.json').Open())).ReadToEnd() | ConvertFrom-Json; $za.Dispose()
$want = -join ([Security.Cryptography.SHA256]::Create().ComputeHash($utf8.GetBytes($v1Files['amy-fx-2.ans'])) | ForEach-Object { $_.ToString('x2') })
Assert ($m.pack -eq 'fx' -and $m.part -eq 'still' -and $m.version -eq 'art-t1' -and $m.source_commit -eq 'abc123' -and @($m.files).Count -eq 3 -and
        (@($m.files) | Where-Object path -eq 'dist/fx/amy-fx-2.ans').sha256 -eq $want) "manifest: pack, part, version, source commit, each file's sha256"

Write-Host '2. auto into an empty root: downloads both parts' -ForegroundColor Cyan
$r1 = New-Root 'r1'
$res = @(Install-CardArt -Root $r1 -ConfigPath $j1 -Mode auto -CacheDir $cache -Prefix test)
Assert (($res | ForEach-Object status) -join ',' -eq 'installed,installed') "still and anim installed ($(($res | ForEach-Object status) -join ','))"
Assert ((Get-Names $r1) -join ',' -eq 'amy-fx-2.ans,bob-fx-1-shiny.ans,bob-fx-1.anim,bob-fx-1.ans') "dist\fx holds exactly the release's files"
Assert ([IO.File]::ReadAllText((Join-Path $r1 'dist\fx\bob-fx-1.ans')) -eq $v1Files['bob-fx-1.ans']) "file contents intact"
$rec = Read-CardArtRecord $r1 'fx'
Assert ($rec.tag -eq 'art-t1' -and $rec.parts.still.sha256 -eq $still.sha256 -and @($rec.parts.anim.files).Count -eq 1) "dist\fx\.cardart.json records the tag, the parts and their files"
Assert (@(Get-ChildItem (Join-Path $r1 'dist') -Directory -Force | Where-Object Name -like '.cardart-*').Count -eq 0) "no staging folder left behind"

Write-Host '3. re-run: idempotent, nothing downloaded or rewritten' -ForegroundColor Cyan
$before = Get-Print $r1
Start-Sleep -Milliseconds 50
$res = @(Install-CardArt -Root $r1 -ConfigPath $j1 -Mode auto -CacheDir (Join-Path $work 'nocache') -Prefix test)
Assert (($res | ForEach-Object status) -join ',' -eq 'current,current') "both parts current"
Assert ((Get-Print $r1) -eq $before) "no file touched"
Assert (-not (Test-Path (Join-Path $work 'nocache\*.zip'))) "nothing downloaded"

Write-Host '4. a newer pinned release replaces exactly the old files' -ForegroundColor Cyan
$res = @(Install-CardArt -Root $r1 -ConfigPath $j2 -Mode auto -CacheDir $cache -Prefix test)
Assert (($res | ForEach-Object status) -join ',' -eq 'installed,installed') "art-t2 installed over art-t1"
Assert ((Get-Names $r1) -join ',' -eq 'amy-fx-2.ans,bob-fx-1.anim,bob-fx-1.ans') "the file art-t2 dropped (bob shiny) is gone"
Assert ([IO.File]::ReadAllText((Join-Path $r1 'dist\fx\bob-fx-1.ans')) -eq $v2Files['bob-fx-1.ans'] -and (Read-CardArtRecord $r1 'fx').tag -eq 'art-t2') "changed file updated, record says art-t2"
Assert (@(Get-ChildItem $cache -File | ForEach-Object Name) -notcontains $still.name) "the cache keeps only the zips art.json pins"

Write-Host '5. local builds are kept unless -Art download' -ForegroundColor Cyan
$r2 = New-Root 'r2'; Set-Art $r2 @{ 'bob-fx-1.ans' = 'LOCAL'; 'zed-fx-9.ans' = 'LOCAL ONLY' }
$res = @(Install-CardArt -Root $r2 -ConfigPath $j1 -Mode auto -CacheDir $cache -Prefix test)
Assert (($res | ForEach-Object status) -join ',' -eq 'local,local' -and [IO.File]::ReadAllText((Join-Path $r2 'dist\fx\bob-fx-1.ans')) -eq 'LOCAL' -and -not (Read-CardArtRecord $r2 'fx')) "auto: a local build (no record) is left alone"
$res = @(Install-CardArt -Root $r2 -ConfigPath $j1 -Mode local -CacheDir $cache -Prefix test)
Assert (($res | ForEach-Object status) -join ',' -eq 'local,local' -and [IO.File]::ReadAllText((Join-Path $r2 'dist\fx\bob-fx-1.ans')) -eq 'LOCAL') "-Art local never downloads"
$res = @(Install-CardArt -Root $r2 -ConfigPath $j1 -Mode skip -CacheDir $cache -Prefix test)
Assert ($res.Count -eq 0 -and [IO.File]::ReadAllText((Join-Path $r2 'dist\fx\bob-fx-1.ans')) -eq 'LOCAL') "-Art skip does nothing"
$res = @(Install-CardArt -Root $r2 -ConfigPath $j1 -Mode download -CacheDir $cache -Prefix test)
Assert (($res | ForEach-Object status) -join ',' -eq 'installed,installed' -and [IO.File]::ReadAllText((Join-Path $r2 'dist\fx\bob-fx-1.ans')) -eq $v1Files['bob-fx-1.ans']) "-Art download replaces the local build's same-named files"
Assert ([IO.File]::ReadAllText((Join-Path $r2 'dist\fx\zed-fx-9.ans')) -eq 'LOCAL ONLY') "...and keeps its other files"
$r3 = New-Root 'r3'
$null = Install-CardArt -Root $r3 -ConfigPath $j1 -Mode auto -CacheDir $cache -Prefix test
$f = Join-Path $r3 'dist\fx\amy-fx-2.ans'; [IO.File]::WriteAllText($f, 'REBUILT'); [IO.File]::SetLastWriteTimeUtc($f, [DateTime]::UtcNow.AddMinutes(1))
$res = @(Install-CardArt -Root $r3 -ConfigPath $j2 -Mode auto -CacheDir $cache -Prefix test)
Assert (($res | ForEach-Object status) -join ',' -eq 'local,local' -and [IO.File]::ReadAllText($f) -eq 'REBUILT') "auto: a release rebuilt locally afterwards is not overwritten by a newer release"

Write-Host '6. checksum mismatch: refused' -ForegroundColor Cyan
$bad = @($v1 | ForEach-Object { $c = $_.PSObject.Copy(); $c.sha256 = ('0' * 64); $c })
$jb = Join-Path $work 'bad.json'; Write-ArtJson $jb 'art-t1' $bad
$r4 = New-Root 'r4'; $cb = Join-Path $work 'cache-bad'
$res = @(Install-CardArt -Root $r4 -ConfigPath $jb -Mode auto -CacheDir $cb -Prefix test)
Assert (($res | ForEach-Object status) -join ',' -eq 'checksum,checksum') "both parts refused: $($res[0].message)"
Assert (-not (Test-Path (Join-Path $r4 'dist')) -and @(Get-ChildItem $cb -File).Count -eq 0) "nothing unpacked, nothing left in the cache"
$pre = Get-Print $r1
$res = @(Install-CardArt -Root $r1 -ConfigPath $jb -Mode download -CacheDir $cb -Prefix test)
Assert ((Get-Print $r1) -eq $pre) "installed art is untouched when the new download fails its checksum"

Write-Host '7. offline: a clear message, no exception, nothing changed' -ForegroundColor Cyan
$jo = Join-Path $work 'offline.json'; Write-ArtJson $jo 'art-t1' $v1 'http://127.0.0.1:9/nothing-here'
$r5 = New-Root 'r5'
$threw = $false
try { $res = @(Install-CardArt -Root $r5 -ConfigPath $jo -Mode auto -CacheDir (Join-Path $work 'cache-off') -Prefix test) } catch { $threw = $true }
Assert (-not $threw -and ($res | ForEach-Object status) -join ',' -eq 'offline,offline' -and $res[0].message -match 'could not download') "offline: status offline, '$($res[0].message)'"
Assert (-not (Test-Path (Join-Path $r5 'dist'))) "no art unpacked"
$res = @(Install-CardArt -Root $r5 -ConfigPath (Join-Path $work 'missing.json') -Mode auto -CacheDir $cache -Prefix test)
Assert ($res.Count -eq 0) "a missing art.json is a message, not an error"

Write-Host '8. -StillOnly skips the optional animations' -ForegroundColor Cyan
$r6 = New-Root 'r6'
$res = @(Install-CardArt -Root $r6 -ConfigPath $j1 -Mode auto -CacheDir $cache -StillOnly -Prefix test)
Assert (($res | ForEach-Object status) -join ',' -eq 'installed,skipped' -and -not (Test-Path (Join-Path $r6 'dist\fx\*.anim'))) "still installed, anim skipped"
$res = @(Install-CardArt -Root $r6 -ConfigPath $j1 -Mode auto -CacheDir $cache -Prefix test)
Assert (($res | ForEach-Object status) -join ',' -eq 'current,installed' -and (Test-Path (Join-Path $r6 'dist\fx\bob-fx-1.anim'))) "a later run without it adds the animations"

Write-Host '9. a hostile archive is refused' -ForegroundColor Cyan
foreach ($evil in 'dist/fx/../../evil.ans', 'dist/other/x.ans', 'packs/fx/pack.json') {
  $z = Join-Path $work 'evil.zip'; Remove-Item $z -ErrorAction SilentlyContinue
  $za = [IO.Compression.ZipFile]::Open($z, 'Create')
  foreach ($e in @(@('manifest.json', (@{ pack = 'fx'; part = 'still'; files = @(@{ path = $evil }) } | ConvertTo-Json -Depth 4)), @($evil, 'x'))) {
    $w = New-Object IO.StreamWriter($za.CreateEntry($e[0]).Open()); $w.Write($e[1]); $w.Dispose()
  }
  $za.Dispose()
  $r7 = New-Root 'r7'; $threw = ''
  try { $null = Expand-CardArtAsset $z $r7 ([pscustomobject]@{ pack = 'fx'; part = 'still'; name = 'evil.zip' }) } catch { $threw = $_.Exception.Message }
  Assert ($threw -match 'unexpected entry' -and -not (Test-Path (Join-Path $work 'evil.ans')) -and (Get-Names $r7).Count -eq 0) "refused '$evil'"
}

Write-Host '10. pokeshell install end to end (a staged module, temp state, a settings copy)' -ForegroundColor Cyan
$mods = Join-Path $work 'Modules'; $home1 = Join-Path $work 'state'
$settings = Join-Path $work 'settings.json'
[IO.File]::WriteAllText($settings, '{ "profiles": { "list": [ { "guid": "{61c54bbd-c2c6-5271-96e7-009a87ff44bf}", "name": "Windows PowerShell" } ] } }', $utf8)
[void][IO.Directory]::CreateDirectory($home1)
[IO.File]::WriteAllLines((Join-Path $home1 'config.txt'), [string[]]@('pack=fx'))
function Stage([string]$Ver) {
  $d = Join-Path $mods "pokeshell\$Ver"
  $null = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $RepoRoot 'tools\publish.ps1') -StageOnly -OutDir $d -Version $Ver 2>&1
  [void][IO.Directory]::CreateDirectory((Join-Path $d 'packs\fx')); [IO.File]::WriteAllText((Join-Path $d 'packs\fx\pack.json'), $packJson, $utf8)
  $d
}
function Run([string]$ModDir, [string[]]$CliArgs, [hashtable]$Env) {
  $saved = @{}
  $all = @{ POKESHELL_HOME = $home1; POKESHELL_ART = $null; POKESHELL_ART_JSON = $j1; CARDART_BASE_URL = $null }
  foreach ($k in $Env.Keys) { $all[$k] = $Env[$k] }
  foreach ($k in $all.Keys) { $saved[$k] = [Environment]::GetEnvironmentVariable($k); [Environment]::SetEnvironmentVariable($k, $all[$k]) }
  try { (& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $ModDir 'scripts\pokeshell.ps1') @CliArgs 2>&1 | Out-String) }
  finally { foreach ($k in $saved.Keys) { [Environment]::SetEnvironmentVariable($k, $saved[$k]) } }
}
$m1 = Stage '0.1.0'
Assert ((Test-Path (Join-Path $m1 'art.json')) -and (Test-Path (Join-Path $m1 'scripts\lib\cardart.ps1')) -and -not (Test-Path (Join-Path $m1 'dist\pokemon'))) "the module ships art.json and cardart.ps1, no Pokemon art"
$out = Run $m1 @('install', '-SettingsPath', $settings)
Assert ($out -match 'fx/still installed from test/fx-art release art-t1' -and (Test-Path (Join-Path $m1 'dist\fx\bob-fx-1.ans'))) "install downloads the art into the module folder"
Assert ((Test-Path (Join-Path $home1 'current\dist\fx\bob-fx-1.ans')) -and (Test-Path (Join-Path $home1 'current\dist\fx\bob-fx-1.anim'))) "...and new tabs get it in current"
$roll = [IO.File]::ReadAllText((Join-Path $home1 'roll.tsv'))
Assert ($roll -match "(?m)^card`t0`tbob`tBob`tfx-1" -and $roll -match "(?m)^card`t0`tamy`tAmy`tfx-2") "both cards roll"
$out = Run $m1 @('install', '-SettingsPath', $settings) @{ CARDART_BASE_URL = 'http://127.0.0.1:9/x' }
Assert ($out -match 'fx/still is release art-t1, up to date' -and $out -notmatch 'could not download') "re-install: up to date, no download attempted"
$out = Run $m1 @('version')
Assert ($out -match 'card art fx: test/fx-art release art-t1 \(still, anim\)') "pokeshell version shows the art release"
$m2 = Stage '0.2.0'
$out = Run $m2 @('install', '-SettingsPath', $settings) @{ CARDART_BASE_URL = 'http://127.0.0.1:9/x' }
Assert ($out -match 'installed from test/fx-art release art-t1: 3 files \(cached download\)' -and (Test-Path (Join-Path $m2 'dist\fx\amy-fx-2.ans'))) "a module update re-installs the art from the cache, offline"
$out = Run $m2 @('install', '-SettingsPath', $settings, '-Art', 'bogus')
Assert ($out -match "-Art is auto, download, local or skip, not 'bogus'") "a bad -Art value is an error"
$m3 = Stage '0.3.0'
$home1 = Join-Path $work 'state-offline'   # a machine without the cached download
[void][IO.Directory]::CreateDirectory($home1); [IO.File]::WriteAllLines((Join-Path $home1 'config.txt'), [string[]]@('pack=fx'))
$out = Run $m3 @('install', '-SettingsPath', $settings) @{ POKESHELL_ART_JSON = $jo; CARDART_BASE_URL = $null }
Assert ($out -match 'could not download' -and $out -match 'the code is installed' -and $out -match 'skin profiles synced' -and $LASTEXITCODE -eq 0) "offline install: the art fails with a message, the rest installs"
Assert ([IO.File]::ReadAllText((Join-Path $home1 'roll.tsv')) -notmatch "(?m)^card`t") "...and the pack without art has nothing to roll"
$out = Run $m3 @('install', '-SettingsPath', $settings, '-Art', 'skip')
Assert ($out -notmatch 'fx/' -and $out -match 'skin profiles synced') "-Art skip: install says nothing about art"

if ($Online) {
  Write-Host '11. online: the release art.json pins, from GitHub, into a temp root' -ForegroundColor Cyan
  $cfg = Read-CardArtConfig (Join-Path $RepoRoot 'art.json')
  $ro = Join-Path $work 'online'
  foreach ($p in @($cfg.packs)) { [void][IO.Directory]::CreateDirectory((Join-Path $ro "packs\$($p.id)")); Copy-Item (Join-Path $RepoRoot "packs\$($p.id)\pack.json") (Join-Path $ro "packs\$($p.id)\pack.json") }
  $co = Join-Path $work 'cache-online'
  $res = @(Install-CardArt -Root $ro -ConfigPath (Join-Path $RepoRoot 'art.json') -Mode auto -CacheDir $co -Prefix online)
  Assert (@($res | Where-Object status -ne 'installed').Count -eq 0 -and $res.Count -eq @($cfg.assets).Count) "every pinned asset downloaded, verified and installed ($(($res | ForEach-Object { "$($_.pack)/$($_.part)=$($_.status)" }) -join ', '))"
  foreach ($a in @($cfg.assets)) {
    $n = @(Get-ChildItem (Join-Path $ro "dist\$($a.pack)") -Filter "*.$((@($cfg.packs) | Where-Object id -eq $a.pack).parts | Where-Object part -eq $a.part | ForEach-Object ext)" -File).Count
    Assert ($n -eq [int]$a.files) "$($a.pack)/$($a.part): $n files, as art.json says"
  }
  $res = @(Install-CardArt -Root $ro -ConfigPath (Join-Path $RepoRoot 'art.json') -Mode auto -CacheDir $co -Prefix online)
  Assert (@($res | Where-Object status -ne 'current').Count -eq 0) "re-run: all current"
  $jbo = Join-Path $work 'online-bad.json'
  $c = $cfg.PSObject.Copy(); $c.assets = @($cfg.assets | Select-Object -First 1 | ForEach-Object { $x = $_.PSObject.Copy(); $x.sha256 = ('f' * 64); $x })
  Write-CardArtJson $jbo $c
  $rb = Join-Path $work 'online-bad'; [void][IO.Directory]::CreateDirectory((Join-Path $rb "packs\$($c.assets[0].pack)")); Copy-Item (Join-Path $ro "packs\$($c.assets[0].pack)\pack.json") (Join-Path $rb "packs\$($c.assets[0].pack)\pack.json")
  $res = @(Install-CardArt -Root $rb -ConfigPath $jbo -Mode auto -CacheDir (Join-Path $work 'cache-online-bad') -Prefix online)
  Assert ($res[0].status -eq 'checksum' -and -not (Test-Path (Join-Path $rb 'dist'))) "the real asset with a wrong sha256 in art.json is refused"
}

Remove-Item $work -Recurse -Force -ErrorAction SilentlyContinue
if ($script:Failures) { Write-Host "art: $script:Failures FAILED" -ForegroundColor Red; exit 1 }
Write-Host "art: all passed" -ForegroundColor Green
