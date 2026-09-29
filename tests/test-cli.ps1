<#
The pokeshell command against a throwaway state dir: show every built card, odds, pack, collection, color.
  powershell -NoProfile -File tests\test-cli.ps1
#>
. (Join-Path $PSScriptRoot '_setup.ps1')
$st = New-TestState 'cli'
$cli = Join-Path $RepoRoot 'scripts\pokeshell.ps1'
function Invoke-Cli { $env:POKESHELL_HOME = $st; try { & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $cli @args 2>&1 | Out-String -Width 300 } finally { Remove-Item Env:POKESHELL_HOME } }
$e = [char]27
function Strip([string]$s) { $s -replace "$e\[[0-9;]*m", '' -replace "$e\][^$e]*$e\\", '' }

Write-Host "1. show: every built card prints its art and banner (big packs: a sample)" -ForegroundColor Cyan
$ans = @(Get-ChildItem (Join-Path $RepoRoot 'dist') -Recurse -Filter *.ans)
$bad = @(); $shown = 0; $packCache = @{}
foreach ($grp in ($ans | Group-Object { $_.Directory.Name })) {
  $files = @($grp.Group | Sort-Object Name)
  if ($files.Count -gt 40) { $step = [Math]::Ceiling($files.Count / 12); $files = @(for ($i = 0; $i -lt $files.Count; $i += $step) { $files[$i] }) }
  foreach ($f in $files) {
    $pack = $f.Directory.Name
    if (-not $packCache[$pack]) { $packCache[$pack] = Read-PokeshellPack $RepoRoot $pack }
    $packObj = $packCache[$pack]
    $char = @($packObj.characters | Where-Object { $f.BaseName.StartsWith("$_-") } | Sort-Object Length -Descending)[0]
    if (-not $char) { continue }
    $variant = $f.BaseName.Substring($char.Length + 1); $shiny = $variant.EndsWith('-shiny'); if ($shiny) { $variant = $variant.Substring(0, $variant.Length - 6) }
    $a = @('show', "$pack/$char", $variant); if ($shiny) { $a += '-shiny' }
    $out = Invoke-Cli @a; $shown++
    $lines = @((Strip $out) -split "`r?`n" | Where-Object { $_.Trim() })
    $ti = [array]::IndexOf(@($packObj.tiers | ForEach-Object art), $variant)
    if ($ti -ge 0 -and [Pokeshell.Core]::FrameStyle($packObj.frames[$ti]) -eq 'wanted') {   # wanted poster: header, full name, bounty + label
      $poster = $packObj.posterNames[$char]; if (-not $poster) { $poster = $packObj.names[$char].ToUpperInvariant() }
      $ok = $lines.Count -ge 4 -and $lines[0].Contains('W A N T E D') -and $lines[-2].Contains($poster) -and
            $lines[-1].Contains($packObj.tiers[$ti].label.ToUpperInvariant()) -and (-not $packObj.bounties[$char] -or $lines[-1].Contains($packObj.bounties[$char]))
      if (-not $ok) { $bad += "$pack/$char ${variant}: wanted '$($lines[0])' / '$($lines[-1])'" }
      continue
    }
    if ($ti -ge 0 -and $packObj.frames[$ti]) {   # framed card: name on the top edge, label on the bottom edge
      $ok = $lines.Count -ge 3 -and $lines[0].StartsWith([string][char]0x256d) -and $lines[0].Contains($packObj.names[$char]) -and
            $lines[-1].StartsWith([string][char]0x2570) -and $lines[-1].Contains($packObj.tiers[$ti].label) -and ($lines[0].Contains([string][char]0x2726) -eq $shiny)
      if (-not $ok) { $bad += "$pack/$char $variant$(if ($shiny) { ' shiny' }): framed '$($lines[0])'" }
      continue
    }
    $banner = $lines[-1].Trim()
    $want = " : $($packObj.names[$char])$(if ($shiny) { ' (shiny)' })"
    if (-not $banner.EndsWith($want) -or $lines.Count -lt 3) { $bad += "$pack/$char $variant$(if ($shiny) { ' shiny' }): '$banner'" }
  }
}
Assert ($ans.Count -gt 0) "$($ans.Count) built .ans files found in dist/ ($shown shown)"
Assert ($bad.Count -eq 0) "all of them show with the right banner$(if ($bad) { ': ' + ($bad -join '; ') })"
$out = Strip (Invoke-Cli show pokemon/nobody)
Assert ($out -match "has no character 'nobody'") "unknown character: one clear error line"

Write-Host "2. pack / odds" -ForegroundColor Cyan
$out = Invoke-Cli pack all
Assert ((Get-Content (Join-Path $st 'config.txt')) -contains 'pack=all') "pack all saved"
$out = Strip (Invoke-Cli odds)
foreach ($id in Get-PokeshellPackIds $RepoRoot) { $n = (Read-PokeshellPack $RepoRoot $id).name; Assert ($out -match [regex]::Escape($n)) "odds lists $n" }
$out = Strip (Invoke-Cli pack bogus)
Assert ($out -match "no pack 'bogus'" -and (Get-Content (Join-Path $st 'config.txt')) -contains 'pack=all') "bad pack refused, setting kept"
$null = Invoke-Cli pack pokemon
$roll = Get-Content (Join-Path $st 'roll.tsv')
Assert ($roll[1] -eq "select`tpokemon" -and @($roll | Where-Object { $_ -like 'skin*' }).Count -gt 0) "roll cache rebuilt for pokemon with its installed skins"

Write-Host "3. collection" -ForegroundColor Cyan
Import-PokeshellCore $st
$lines = foreach ($i in 1..300) {
  $env:POKESHELL_ROLLED = $null; $env:POKESHELL_PULL = $null; $env:CARDSHELL_ROLLED = $null
  $r = [Pokeshell.Core]::Roll($RepoRoot, $st, $PlainGuid, @('powershell.exe'), [DateTime]::UtcNow.AddMinutes(-1000 + $i * 3).Ticks, $i, -1, 'x', 'C:\', 'C:\')
  if ($r.Action -eq 'foil') { $r.LogLine }   # commons log themselves; foils are logged by PowerShell after the tab opens
}
Remove-Item Env:POKESHELL_ROLLED, Env:POKESHELL_PULL, Env:CARDSHELL_ROLLED -ErrorAction SilentlyContinue
[IO.File]::AppendAllLines((Join-Path $st 'pulls.log'), [string[]]@($lines))
$total = @(Get-Content (Join-Path $st 'pulls.log')).Count
$out = Strip (Invoke-Cli collection)
Assert ($out -match "BINDER\s+$total pulls") "binder counts all $total pulls"
Assert ($out -match 'Pikachu' -and $out -match 'card slots filled') "per-character rows and completion"
Assert ($out -match 'best pulls:') "best pulls listed"
Write-Host ($out -split "`n" | Select-Object -First 16 | Out-String)

Write-Host "4. color" -ForegroundColor Cyan
$out = Invoke-Cli color blue
Assert ($out.Contains("$e]4;264;rgb:2f/6f/d6$e\")) "named color -> OSC 4;264"
$out = Invoke-Cli color '#f80'
Assert ($out.Contains("$e]4;264;rgb:ff/88/00$e\")) "3-digit hex"
$out = Invoke-Cli color reset
Assert ($out.Contains("$e]104;264$e\")) "reset -> OSC 104;264"
$null = Invoke-Cli color papaya whip
Assert ((Get-Content (Join-Path $st 'color-misses.log')) -match "papaya whip`tcss:ffefd5") "unknown name: CSS fallback + miss log"

Write-Host "5. card frames (a throwaway pack with tier frames, names and tags in pack.json)" -ForegroundColor Cyan
$fr = Join-Path ([IO.Path]::GetTempPath()) "pokeshell-test-frames-$PID"
Remove-Item $fr -Recurse -Force -ErrorAction SilentlyContinue
foreach ($d in 'packs\framed', 'dist\framed', 'state') { [void][IO.Directory]::CreateDirectory((Join-Path $fr $d)) }
$utf8 = [Text.UTF8Encoding]::new($false)
[IO.File]::WriteAllText((Join-Path $fr 'packs\framed\pack.json'), @'
{ "id": "framed", "name": "Framed", "foil_chance": 0.5, "shiny_chance": 0,
  "characters": ["bob", "nido"], "names": { "bob": "Bob", "nido": "Nidoran\u2640" }, "tags": { "bob": "#001" },
  "tiers": [
    { "id": "common", "label": "common", "art": "common", "skins": {}, "frame": "plain" },
    { "id": "holo", "label": "holo", "art": "common", "skins": { "sk": 1 }, "frame": ["#ff0000", "#0000ff"] },
    { "id": "bare", "label": "bare", "art": "common", "skins": {} }
  ] }
'@, $utf8)
$art = "$e[0;38;2;10;20;30m" + [char]0x2580 + [char]0x2584 + "$e[0m  `n $e[0;38;2;1;2;3;48;2;4;5;6m" + [char]0x2580 + "$e[0m`n"
foreach ($n in 'bob-common.ans', 'bob-common-shiny.ans', 'nido-common.ans') { [IO.File]::WriteAllText((Join-Path $fr "dist\framed\$n"), $art, $utf8) }
function VisLen([string]$s) { ($s -replace "$e\[[0-9;]*m", '').Length }
$fp = Read-PokeshellPack $fr 'framed'
Assert ($fp.names['bob'] -eq 'Bob' -and $fp.names['nido'] -eq "Nidoran$([char]0x2640)" -and $fp.tags['bob'] -eq '#001') "names and tags come from pack.json (no art/*.json needed)"
Assert ($fp.frames[0] -eq 'plain' -and $fp.frames[1] -eq '#ff0000,#0000ff' -and $fp.frames[2] -eq '') "tier frames: preset, gradient list, none"
$txt = [Pokeshell.Core]::PullText($fr, 'framed', 'bob', 'Bob', 'common', 'common', 0, $true, 'plain', '#001')
$fl = @($txt -split "`r`n" | Where-Object { $_ })
$widths = @($fl | ForEach-Object { VisLen $_ } | Sort-Object -Unique)
Assert ($fl.Count -eq 4) "framed card = art height + 2 lines ($($fl.Count))"
Assert ($widths.Count -eq 1) "every framed line has the same visible width ($($widths -join ','))"
$top = Strip $fl[0]; $bot = Strip $fl[-1]
Assert ($top.StartsWith([string][char]0x256d) -and $top.Contains('Bob') -and $top.Contains('#001') -and $top.Contains([string][char]0x2726)) "top edge: shiny mark, name and tag ('$top')"
Assert ($bot.StartsWith([string][char]0x2570) -and $bot.Contains('common') -and $bot.Contains('shiny')) "bottom edge: label + shiny ('$bot')"
$g = [Pokeshell.Core]::PullText($fr, 'framed', 'bob', 'Bob', 'common', 'holo', 1, $false, '#ff0000,#0000ff', '')
Assert ($g.Contains("$e[0;38;2;255;0;0m") -and $g.Contains("$e[0;38;2;0;0;255m")) "a gradient-list frame starts and ends on its stops"
Assert (-not $g.Contains([string][char]0x2726)) "no shiny mark on a non-shiny card"
$plain = [Pokeshell.Core]::PullText($fr, 'framed', 'bob', 'Bob', 'common', 'bare', 2, $false)
Assert ($plain -eq [Pokeshell.Core]::PullText($fr, 'framed', 'bob', 'Bob', 'common', 'bare', 2, $false, '', '') -and (Strip $plain).Contains('bare : Bob')) "no frame: the classic art + banner, unchanged"
$fst = Join-Path $fr 'state'
[IO.File]::WriteAllLines((Join-Path $fst 'installed.tsv'), [string[]]@("framed`tsk`t{00000000-0000-0000-0000-00000000f00d}`ttest"))
Update-PokeshellRollCache -Root $fr -StateDir $fst -Cfg @{ pack = 'framed' }
$rt = @(Get-Content (Join-Path $fst 'roll.tsv') -Encoding UTF8)
Assert ($rt -contains "char`tbob`tBob`t#001" -and $rt -contains "char`tnido`tNidoran$([char]0x2640)" -and $rt -contains "tier`tholo`tholo`tcommon`t#ff0000,#0000ff" -and $rt -contains "tier`tbare`tbare`tcommon") "roll cache carries tags and frames (and omits empty ones)"
[IO.File]::WriteAllLines((Join-Path $fst 'config.txt'), [string[]]@('pack=framed'))
Update-PokeshellRollCache -Root $fr -StateDir $fst
$r = Invoke-Fresh { [Pokeshell.Core]::Roll($fr, $fst, $PlainGuid, @('powershell.exe'), [DateTime]::UtcNow.Ticks, 7, 0, 'x', 'C:\', 'C:\') }
Assert ($r.Action -eq 'common' -and $r.Frame -eq 'plain' -and (Strip $r.Text).Contains([string][char]0x256d)) "a common pull prints the tier-0 frame"
$r = Invoke-Fresh { [Pokeshell.Core]::Roll($fr, $fst, $PlainGuid, @('powershell.exe'), [DateTime]::UtcNow.Ticks, 7, 1, 'x', 'C:\', 'C:\') }
$cmd = if ($r.WtArgs) { [Text.Encoding]::Unicode.GetString([Convert]::FromBase64String($r.WtArgs[-1])) } else { '' }
Assert ($r.Action -eq 'foil' -and $r.Frame -eq '#ff0000,#0000ff' -and $cmd.Contains("-Frame '#ff0000,#0000ff'") -and (Strip $r.FallbackText).Contains('common')) "a foil passes its frame (and tag) to the skinned tab; the fallback is the framed common"
Remove-Item Env:POKESHELL_ROLLED, Env:POKESHELL_PULL, Env:CARDSHELL_ROLLED -ErrorAction SilentlyContinue

Write-Host "5b. frame styles: the wanted poster (a throwaway pack with style-object frames, poster_names, bounties)" -ForegroundColor Cyan
foreach ($d in 'packs\posters', 'dist\posters') { [void][IO.Directory]::CreateDirectory((Join-Path $fr $d)) }
[IO.File]::WriteAllText((Join-Path $fr 'packs\posters\pack.json'), @'
{ "id": "posters", "name": "Posters", "foil_chance": 0.5, "shiny_chance": 0,
  "characters": ["bob", "nido"], "names": { "bob": "Bob", "nido": "Nido" }, "tags": { "nido": "#029" },
  "poster_names": { "bob": "BOB\u00b7THE\u00b7BUILDER" }, "bounties": { "bob": "3,000,000,000" },
  "tiers": [
    { "id": "common", "label": "common", "art": "common", "skins": {}, "frame": { "style": "wanted", "palette": "common" } },
    { "id": "manga-rare", "label": "manga rare", "art": "common", "skins": { "sk2": 1 }, "frame": { "style": "wanted", "palette": "manga" } },
    { "id": "secret", "label": "secret rare", "art": "common", "skins": {}, "frame": { "style": "wanted", "palette": "secret-rare", "seed": "x" } },
    { "id": "odd", "label": "odd", "art": "common", "skins": {}, "frame": { "style": "no-such-style" } }
  ] }
'@, $utf8)
foreach ($n in 'bob-common.ans', 'nido-common.ans') { [IO.File]::WriteAllText((Join-Path $fr "dist\posters\$n"), $art, $utf8) }
$pp = Read-PokeshellPack $fr 'posters'
$bobPoster = "BOB$([char]0xb7)THE$([char]0xb7)BUILDER"
Assert ($pp.frames[0] -eq 'wanted;palette=common;seed=common' -and $pp.frames[1] -eq 'wanted;palette=manga;seed=manga-rare' -and $pp.frames[2] -eq 'wanted;palette=secret-rare;seed=x') "a style-object frame becomes 'style;key=value;seed=<tier id>' ($($pp.frames -join ' | '))"
Assert ($pp.posterNames['bob'] -eq $bobPoster -and $pp.bounties['bob'] -eq '3,000,000,000' -and -not $pp.bounties['nido']) "poster_names and bounties come from pack.json"
Assert ([Pokeshell.Core]::FrameStyle($pp.frames[0]) -eq 'wanted' -and [Pokeshell.Core]::FrameStyle('gold') -eq '' -and [Pokeshell.Core]::FrameStyle('#ff0000,#0000ff') -eq '') "FrameStyle: wanted vs preset / gradient frames"
$wt = [Pokeshell.Core]::PullText($fr, 'posters', 'bob', 'Bob', 'common', 'common', 0, $false, $pp.frames[0], '', $false, $bobPoster, '3,000,000,000')
$wl = @($wt -split "`r`n" | Where-Object { $_ })
$ww = @($wl | ForEach-Object { VisLen $_ } | Sort-Object -Unique)
Assert ($wl.Count -eq 2 + 3) "wanted poster = art height + 3 lines ($($wl.Count))"
Assert ($ww.Count -eq 1) "every wanted line has the same visible width ($($ww -join ','))"
Assert ((Strip $wl[0]).Contains('W A N T E D')) "header row: W A N T E D ('$(Strip $wl[0])')"
Assert ((Strip $wl[3]).Trim() -eq $bobPoster) "name row: the poster name under the art ('$(Strip $wl[3])')"
$wb = Strip $wl[4]
Assert ($wb.Contains("$([char]0x0e3f) 3,000,000,000-") -and $wb.EndsWith("COMMON $([char]0x2598)") -and $wb.IndexOf('3,000') -lt $wb.IndexOf('COMMON')) "bottom row: bounty left, label right ('$wb')"
function PaperColors([string]$s) { @([regex]::Matches($s, '48;2;(\d+);(\d+);(\d+)m') | ForEach-Object { , @([int]$_.Groups[1].Value, [int]$_.Groups[2].Value, [int]$_.Groups[3].Value) }) }
$pc = PaperColors (($wl[0], $wl[3], $wl[4]) -join '')   # the frame rows (the art has colors of its own)
Assert ($wt.Contains("$e[0;1;38;2;59;38;22;48;2;") -and $pc.Count -gt 0 -and -not @($pc | Where-Object { $_[0] -lt 207 -or $_[0] -gt 230 -or $_[1] -lt 181 -or $_[1] -gt 211 -or $_[2] -lt 124 -or $_[2] -gt 163 })) "common palette: dark-brown ink on paper between #e6d3a3 and its stain #cfb57c"
Assert ($wt -eq [Pokeshell.Core]::PullText($fr, 'posters', 'bob', 'Bob', 'common', 'common', 0, $false, $pp.frames[0], '', $false, $bobPoster, '3,000,000,000')) "deterministic: the same pull draws the same poster"
$wm = [Pokeshell.Core]::PullText($fr, 'posters', 'bob', 'Bob', 'common', 'manga rare', 1, $false, $pp.frames[1], '', $false, $bobPoster, '3,000,000,000')
Assert ($wm.Contains(";48;2;236;235;228m") -and $wm.Contains("$e[0;1;38;2;200;40;30;") -and $wm -ne $wt) "manga palette: newsprint paper, red rarity ink"
$ws = [Pokeshell.Core]::PullText($fr, 'posters', 'bob', 'Bob', 'common', 'secret rare', 2, $false, $pp.frames[2], '', $false, $bobPoster, '3,000,000,000')
Assert (@($ws -split "`r`n" | Where-Object { $_ } | ForEach-Object { VisLen $_ } | Sort-Object -Unique).Count -eq 1 -and @(PaperColors ($ws -split "`r`n")[1] | Where-Object { $_[0] -lt 170 }).Count -eq 0 -and @(PaperColors ($ws -split "`r`n")[1] | Where-Object { $_[0] -ge 245 }).Count -gt 0) "secret-rare palette: gold-leaf gradient paper, rows still even"
$wn = [Pokeshell.Core]::PullText($fr, 'posters', 'nido', 'Nido', 'common', 'common', 0, $true, $pp.frames[0], '#029', $false, '', '')
$wnl = @($wn -split "`r`n" | Where-Object { $_ } | ForEach-Object { Strip $_ })
Assert ($wnl[3].Trim() -eq 'NIDO' -and $wnl[4].Contains("$([char]0x0e3f) #029-") -and $wnl[4].Contains("COMMON $([char]0x2726)")) "no poster name / bounty: the upper-cased name and the tag; shiny marks the label"
Assert ([Pokeshell.Core]::PullText($fr, 'posters', 'bob', 'Bob', 'common', 'common', 0, $false, $pp.frames[0], '', $true, $bobPoster, '3,000,000,000') -eq "`r`n" + $art.Replace("`n", "`r`n") + "`r`n") "display picture: no poster, just the art"
Assert ((Strip ([Pokeshell.Core]::PullText($fr, 'posters', 'bob', 'Bob', 'common', 'odd', 3, $false, $pp.frames[3], ''))).Contains([string][char]0x256d)) "an unknown style falls back to a rounded box"
$pst = Join-Path $fr 'pstate'; [void][IO.Directory]::CreateDirectory($pst)
[IO.File]::WriteAllLines((Join-Path $pst 'installed.tsv'), [string[]]@("posters`tsk2`t{00000000-0000-0000-0000-00000000f00e}`ttest"))
[IO.File]::WriteAllLines((Join-Path $pst 'config.txt'), [string[]]@('pack=posters'))
Update-PokeshellRollCache -Root $fr -StateDir $pst
$rt = @(Get-Content (Join-Path $pst 'roll.tsv') -Encoding UTF8)
Assert ($rt -contains "char`tbob`tBob`t`t$bobPoster`t3,000,000,000" -and $rt -contains "char`tnido`tNido`t#029" -and $rt -contains "tier`tmanga-rare`tmanga rare`tcommon`twanted;palette=manga;seed=manga-rare") "roll cache carries poster names, bounties and style frames"
$r = $null; foreach ($seed in 1..40) { $r = Invoke-Fresh { [Pokeshell.Core]::Roll($fr, $pst, $PlainGuid, @('powershell.exe'), [DateTime]::UtcNow.Ticks, $seed, 0, 'x', 'C:\', 'C:\') }; if ($r.Character -eq 'bob') { break } }
Assert ($r.Action -eq 'common' -and $r.Poster -eq $bobPoster -and $r.Bounty -eq '3,000,000,000' -and $r.Text -eq $wt) "a common pull prints the tier-0 poster (same bytes as PullText)"
$r = $null; foreach ($seed in 1..40) { [IO.File]::Delete((Join-Path $pst 'spawn-gate.txt')); $r = Invoke-Fresh { [Pokeshell.Core]::Roll($fr, $pst, $PlainGuid, @('powershell.exe'), [DateTime]::UtcNow.Ticks, $seed, 1, 'x', 'C:\', 'C:\') }; if ($r.Character -eq 'bob') { break } }
$cmd = if ($r.WtArgs) { [Text.Encoding]::Unicode.GetString([Convert]::FromBase64String($r.WtArgs[-1])) } else { '' }
Assert ($r.Action -eq 'foil' -and $cmd.Contains("-Frame 'wanted;palette=manga;seed=manga-rare'") -and $cmd.Contains("-Poster '$bobPoster' -Bounty '3,000,000,000'") -and $r.FallbackText -eq $wt) "a foil passes frame, poster name and bounty to the skinned tab; the fallback is the tier-0 poster"
Remove-Item Env:POKESHELL_ROLLED, Env:POKESHELL_PULL, Env:CARDSHELL_ROLLED -ErrorAction SilentlyContinue
# the One Piece pack (local only): byte-identical to the style-lab prototype's output
$proto = Join-Path $RepoRoot 'style-lab\op-frames\out'
if ((Test-Path (Join-Path $RepoRoot 'packs\onepiece\pack.json')) -and (Test-Path $proto)) {
  $op = Read-PokeshellPack $RepoRoot 'onepiece'; $same = 0; $diff = @()
  for ($i = 0; $i -lt @($op.tiers).Count; $i++) {
    $t = $op.tiers[$i]; if ([Pokeshell.Core]::FrameStyle($op.frames[$i]) -ne 'wanted') { continue }
    foreach ($c in $op.characters) {
      $f = Join-Path $proto "wanted-$c-$($t.id).ans"; if (-not (Test-Path $f)) { continue }
      $got = [Pokeshell.Core]::PullText($RepoRoot, 'onepiece', $c, $op.names[$c], $t.art, $t.label, $i, $false, $op.frames[$i], $op.tags[$c], $false, $op.posterNames[$c], $op.bounties[$c])
      if ($got.Replace("`r`n", "`n").Trim("`n") + "`n" -eq [IO.File]::ReadAllText($f, [Text.Encoding]::UTF8)) { $same++ } else { $diff += "$c/$($t.id)" }
    }
  }
  Assert ($same -gt 0 -and -not $diff) "onepiece: $same wanted posters byte-identical to style-lab/op-frames$(if ($diff) { '; differ: ' + ($diff -join ' ') })"
}

Write-Host "6. display: card (default) | picture" -ForegroundColor Cyan
$pic = [Pokeshell.Core]::PullText($fr, 'framed', 'bob', 'Bob', 'common', 'common', 0, $true, 'plain', '#001', $true)
Assert ($pic -eq "`r`n" + $art.Replace("`n", "`r`n") + "`r`n") "picture = just the art: no frame, no banner"
Assert ([Pokeshell.Core]::PullText($fr, 'framed', 'bob', 'Bob', 'common', 'common', 0, $true, 'plain', '#001') -eq $txt) "the card is the default"
Assert ([Pokeshell.Core]::Display((Read-PokeshellConfig $fst)) -eq 'card') "no display setting = card"
[IO.File]::AppendAllText((Join-Path $fst 'config.txt'), "display=picture`r`n")
Update-PokeshellRollCache -Root $fr -StateDir $fst   # config.txt is part of the cache stamp (pokeshell display does this too)
Assert ([Pokeshell.Core]::Display((Read-PokeshellConfig $fst)) -eq 'picture') "display=picture in config.txt"
$r = Invoke-Fresh { [Pokeshell.Core]::Roll($fr, $fst, $PlainGuid, @('powershell.exe'), [DateTime]::UtcNow.Ticks, 7, 0, 'x', 'C:\', 'C:\') }
Assert ($r.Action -eq 'common' -and $r.Display -eq 'picture' -and -not (Strip $r.Text).Contains([string][char]0x256d) -and -not (Strip $r.Text).Contains(' : ')) "startup pull with display=picture prints only the art"
[IO.File]::Delete((Join-Path $fst 'spawn-gate.txt'))
$r = Invoke-Fresh { [Pokeshell.Core]::Roll($fr, $fst, $PlainGuid, @('powershell.exe'), [DateTime]::UtcNow.Ticks, 7, 1, 'x', 'C:\', 'C:\') }
$cmd = if ($r.WtArgs) { [Text.Encoding]::Unicode.GetString([Convert]::FromBase64String($r.WtArgs[-1])) } else { '' }
Assert ($r.Action -eq 'foil' -and $cmd.EndsWith(' -Picture') -and -not (Strip $r.FallbackText).Contains([string][char]0x256d)) "a foil tells its tab to print the picture too (and so does the fallback)"
Remove-Item Env:POKESHELL_ROLLED, Env:POKESHELL_PULL, Env:CARDSHELL_ROLLED -ErrorAction SilentlyContinue
[IO.File]::WriteAllLines((Join-Path $fst 'config.txt'), [string[]]@('pack=framed', 'display=card'))
$env:POKESHELL_DISPLAY = 'picture'
try { $d = [Pokeshell.Core]::Display((Read-PokeshellConfig $fst)) } finally { Remove-Item Env:POKESHELL_DISPLAY }
Assert ($d -eq 'picture') "POKESHELL_DISPLAY=picture overrides display=card for one shell"
Remove-Item $fr -Recurse -Force -ErrorAction SilentlyContinue

# the command, and `show` honoring it (the pokemon pack: its common tier is a framed card)
$out = Strip (Invoke-Cli display)
Assert ($out -match 'display: card') "pokeshell display: card by default"
$null = Invoke-Cli display picture
Assert ((Get-Content (Join-Path $st 'config.txt')) -contains 'display=picture') "pokeshell display picture is saved in config.txt"
$out = Strip (Invoke-Cli display sideways)
Assert ($out -match 'card or picture' -and (Get-Content (Join-Path $st 'config.txt')) -contains 'display=picture') "a bad value is refused, setting kept"
$out = Strip (Invoke-Cli show pokemon/pikachu)
Assert ($out.Contains([string][char]0x2580) -and -not $out.Contains([string][char]0x256d) -and -not $out.Contains('common : Pikachu')) "show follows display=picture: art, no frame, no banner"
$out = Strip (Invoke-Cli show pokemon/pikachu -card)
Assert ($out.Contains([string][char]0x256d) -and $out.Contains('Pikachu') -and $out.Contains('#025')) "show -card overrides it (framed card)"
$null = Invoke-Cli display card
$out = Strip (Invoke-Cli show pokemon/pikachu -picture)
Assert (-not $out.Contains('common : Pikachu') -and $out.Contains([string][char]0x2580)) "show -picture overrides display=card"
$env:POKESHELL_DISPLAY = 'picture'
try { $out = Strip (Invoke-Cli show pokemon/pikachu) } finally { Remove-Item Env:POKESHELL_DISPLAY }
Assert (-not $out.Contains('common : Pikachu')) "POKESHELL_DISPLAY=picture applies to show"

Remove-Item $st -Recurse -Force -ErrorAction SilentlyContinue
Write-Host ''
if ($script:Failures) { Write-Host "cli: $script:Failures FAILED" -ForegroundColor Red; exit 1 }
Write-Host "cli: all passed" -ForegroundColor Green
