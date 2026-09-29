<#
Card animation (lib\Anim.cs, lib\anim.ps1): the effect loop a pulled card plays over its printed art.
  1. bundles and settings: which .anim a card plays, anim=untilkey|intro|off, POKESHELL_NO_ANIM, argv rules
  2. layout: the art rows are found in every printed form of the card (framed, banner, picture)
  3. playback on a fake console (virtual clock, VT screen model): frame sequence and timing, stop on a key /
     the cap / Ctrl+C / a resize, the final screen is exactly the static card, no newline / scroll / wrap,
     cursor hidden then restored, a short window clips the top rows instead of scrolling
  4. redirected output: a pulled tab whose output is a file prints the static card only
  5. end to end on a headless pseudoconsole (ConPTY: no window, no tab): the pulled tab's real startup command
     animates, a key stops it and arrives at the PSReadLine prompt as the first character; Ctrl+C; the cap
  6. the real pack, when its art is built (tools\build_realcards.py): every .anim ends on its .ans, and a dry-run
     pull of Glaceon V (swsh7-174) selects playback in the tab it would open; the same-tab case via the hook
  7. startup: what playback adds before the first frame, measured in fresh processes on a pseudoconsole
State goes to %TEMP%; nothing touches %LOCALAPPDATA%\pokeshell, Windows Terminal or $PROFILE.
  powershell -NoProfile -File tests\test-anim.ps1 [-Runs 8]
#>
param([int]$Runs = 8)
. (Join-Path $PSScriptRoot '_setup.ps1')
. (Join-Path $RepoRoot 'scripts\lib\anim.ps1')
$e = [char]27
$utf8 = [Text.UTF8Encoding]::new($false)
$st = New-TestState 'anim'
$animDll = New-PokeshellAnimCore $st
[void](New-PokeshellCore $st)   # the child processes below load both from the test state
Import-PokeshellAnimCore $st
Add-Type -Path (Join-Path $PSScriptRoot 'AnimHarness.cs') -ReferencedAssemblies $animDll
foreach ($k in 'POKESHELL_NO_ANIM', 'POKESHELL_ANIM_MAX', 'POKESHELL_ANIM_STATS') { [Environment]::SetEnvironmentVariable($k, $null) }

# ---- a throwaway pack with a synthetic animated card (no Nintendo art needed)
$fx = Join-Path ([IO.Path]::GetTempPath()) "pokeshell-test-animfx-$PID"
Remove-Item $fx -Recurse -Force -ErrorAction SilentlyContinue
[void][IO.Directory]::CreateDirectory("$fx\dist\fx")
function New-ArtFrame([int]$f, [int]$h = 8, [int]$w = 12) {
  $sb = [Text.StringBuilder]::new()
  for ($y = 0; $y -lt $h; $y++) {
    for ($x = 0; $x -lt $w; $x++) {
      $v = (40 + 13 * $x + 7 * $y + 20 * $f) % 256
      [void]$sb.Append("$e[0;38;2;$v;90;200;48;2;20;$v;60m" + [char]0x2580)
    }
    [void]$sb.Append("$e[0m`n")
  }
  $sb.ToString()
}
$fxFrames = @(0..15 | ForEach-Object { New-ArtFrame $_ })
[IO.File]::WriteAllText("$fx\dist\fx\bob-set1-9.ans", $fxFrames[15], $utf8)
[IO.File]::WriteAllText("$fx\dist\fx\bob-set1-9.anim", '{"lines": 8, "fps": 12, "frames": 16, "final": 15}' + "`n`f" + ($fxFrames -join "`f"), $utf8)
[IO.File]::WriteAllText("$fx\dist\fx\bob-set1-1.ans", (New-ArtFrame 3), $utf8)   # a common: no .anim
function Get-FxText([string]$Frame = 'holo', [switch]$Picture) {
  [Pokeshell.Core]::PullText($fx, 'fx', 'bob', 'Bob', 'set1-9', 'rare holo', 5, $false, $Frame, '9/9', [bool]$Picture, '', '')
}
function Get-Layout([string]$Text, [string]$Ans) { $w = ''; $l = [Pokeshell.Anim]::Locate($Text, $Ans, [ref]$w); $script:why = $w; $l }
function New-Reader([string]$Path) { [IO.StreamReader]::new($Path, $utf8) }
function Invoke-FakePlay([string]$Text, [string]$Ans, [string]$Anim, [int]$W = 100, [int]$H = 40, [string]$Mode = 'untilkey', [double]$Max = 30, [scriptblock]$Setup) {
  $fc = [PokeshellTest.FakeConsole]::new($W, $H)
  $fc.Write($Text); $snap = $fc.Dump(); $fc.ResetCounters(); $fc.Recording = $true
  if ($Setup) { & $Setup $fc }
  $rd = New-Reader $Anim
  try { $r = [Pokeshell.Anim]::Play($rd, (Get-Layout $Text $Ans), $Mode, $Max, $fc) } finally { $rd.Dispose() }
  [pscustomobject]@{ R = $r; Fake = $fc; Same = ($fc.Dump() -eq $snap); Snap = $snap }
}
$fxAns = [IO.File]::ReadAllText("$fx\dist\fx\bob-set1-9.ans"); $fxAnim = "$fx\dist\fx\bob-set1-9.anim"

Write-Host "1. bundles and settings" -ForegroundColor Cyan
$b = [Pokeshell.Anim]::Find($fx, 'fx', 'bob', 'set1-9', $false)
Assert ($b[0] -like '*bob-set1-9.anim' -and $b[1] -like '*bob-set1-9.ans') 'a card with an .anim plays it and ends on its .ans'
Assert ([Pokeshell.Anim]::Find($fx, 'fx', 'bob', 'set1-1', $false)[0] -eq '') 'a common (no .anim) stays still'
Assert ([Pokeshell.Anim]::Find($fx, 'fx', 'bob', 'set1-9', $true)[0] -like '*bob-set1-9.anim') 'shiny with no shiny art: the regular loop (the regular art is printed)'
[IO.File]::WriteAllText("$fx\dist\fx\bob-set1-9-shiny.ans", $fxAns, $utf8)
Assert ([Pokeshell.Anim]::Find($fx, 'fx', 'bob', 'set1-9', $true)[0] -eq '') 'shiny art without a shiny .anim: no animation (the regular loop would end on the wrong art)'
[IO.File]::Copy($fxAnim, "$fx\dist\fx\bob-set1-9-shiny.anim")
Assert ([Pokeshell.Anim]::Find($fx, 'fx', 'bob', 'set1-9', $true)[0] -like '*bob-set1-9-shiny.anim') 'shiny art with a shiny .anim: the shiny loop'
$cfg = Join-Path $st 'config.txt'
Assert ([Pokeshell.Anim]::Mode($st) -eq 'untilkey') 'default mode: untilkey'
foreach ($c in @(@('intro', 'intro'), @('off', 'off'), @('untilkey', 'untilkey'), @('bogus', 'untilkey'))) {
  [IO.File]::WriteAllText($cfg, "pack=pokemon`r`nanim=$($c[0])`r`n")
  Assert ([Pokeshell.Anim]::Mode($st) -eq $c[1]) "config anim=$($c[0]) -> $($c[1])"
}
[IO.File]::WriteAllText($cfg, "anim=intro`r`n")
$env:POKESHELL_NO_ANIM = '1'; Assert ([Pokeshell.Anim]::Mode($st) -eq 'off') 'POKESHELL_NO_ANIM=1 turns it off over the config'
$env:POKESHELL_NO_ANIM = '0'; Assert ([Pokeshell.Anim]::Mode($st) -eq 'intro') 'POKESHELL_NO_ANIM=0 leaves the config'
$env:POKESHELL_NO_ANIM = $null; [IO.File]::Delete($cfg)
$enc = 'JABlAG4AdgA='
foreach ($c in @(
    @(@('powershell.exe'), ''), @(@('powershell.exe', '-NoLogo'), ''),
    @(@('powershell.exe', '-NoLogo', '-NoExit', '-EncodedCommand', $enc), ''),   # the pulled tab
    @(@('pwsh.exe', '-nol', '-noe', '-ec', $enc), ''),
    @(@('powershell.exe', '-NonInteractive'), 'non-interactive'), @(@('powershell.exe', '-noni', '-NoExit', '-c', 'x'), 'non-interactive'),
    @(@('powershell.exe', '-Command', 'x'), 'scripted'), @(@('powershell.exe', '-File', 'x.ps1'), 'scripted'), @(@('powershell.exe', '-EncodedCommand', $enc), 'scripted'),
    @(@('powershell.exe', '-c', 'echo -NoExit'), 'scripted'))) {
  Assert ([Pokeshell.Anim]::ArgvReason([string[]]$c[0]) -eq $c[1]) "argv '$($c[0][1..9] -join ' ')' -> '$($c[1])'"
}
Assert ([Pokeshell.Anim]::StaticReason('Visual Studio Code Host') -like 'host *') 'another PowerShell host: static'

Write-Host "2. layout" -ForegroundColor Cyan
foreach ($c in @(@('holo', $false, 2), @('', $false, 0), @('', $true, 0), @('wanted;palette=manga;seed=x', $false, -1))) {
  $t = Get-FxText -Frame $c[0] -Picture:$c[1]
  $l = Get-Layout $t $fxAns
  $name = if ($c[1]) { 'picture' } elseif ($c[0]) { "frame $($c[0].Split(';')[0])" } else { 'banner' }
  Assert ($l -and $l.Static.Count -eq 8 -and ($c[2] -lt 0 -or $l.Col -eq $c[2])) "$name card: 8 art rows found$(if ($c[2] -ge 0) { " at column $($c[2])" }) (got $(if ($l) { "column $($l.Col)" } else { $script:why }))"
}
$t = Get-FxText; $l = Get-Layout $t $fxAns
$lines = $t.Replace("`r`n", "`n").Split("`n")
Assert ($l.Dist[7] -eq 3 -and $l.Dist[0] -eq 10) "framed: the last art row is 3 lines above the prompt line, the first 10 (got $($l.Dist[7]), $($l.Dist[0]))"
Assert ($null -eq (Get-Layout $t (New-ArtFrame 4))) 'art that is not the printed card: no layout (static)'
Assert ($null -eq (Get-Layout ($t.TrimEnd("`r", "`n")) $fxAns)) 'printed text not ending in a newline: no layout'

Write-Host "3. playback on a fake console" -ForegroundColor Cyan
$p = Invoke-FakePlay $t $fxAns $fxAnim -Setup { param($f) $f.KeyAt = 1040 }
$r = $p.R
Assert ($r.Status -eq 'played' -and $r.Stop -eq 'key') "untilkey: stops on the key ($r)"
Assert ($r.Frames -eq 12) "12 frames in the first second (got $($r.Frames))"
$late = 0; for ($i = 0; $i -lt $r.FrameMs.Count; $i++) { $late = [Math]::Max($late, [Math]::Abs($r.FrameMs[$i] - ($i + 1) * 1000 / 12)) }
Assert ($late -le 1) "the printed card is the loop's final frame: frame k is written k x 83.3 ms after the print (worst error $late ms)"
$p2 = Invoke-FakePlay $t $fxAns $fxAnim -Setup { param($f) $f.KeyAt = 1040; $f.WriteCostMs = 30 }
$late = 0; for ($i = 1; $i -lt $p2.R.FrameMs.Count; $i++) { $late = [Math]::Max($late, [Math]::Abs($p2.R.FrameMs[$i] - ($i + 1) * 1000 / 12 - 30)) }
Assert ($late -le 1) "slow writes (30 ms each) don't slow the pace (worst drift $late ms)"
Assert (($r.FrameIndex -join ',') -eq '0,1,2,3,4,5,6,7,8,9,10,11') "the loop starts after the final frame: $($r.FrameIndex -join ',')"
Assert ($p.Same -and $r.FinalRestored) 'after the key the screen is exactly the static card'
Assert ($p.Fake.Newlines -eq 0 -and $p.Fake.Scrolls -eq 0 -and $p.Fake.Wraps -eq 0 -and $p.Fake.Clamps -eq 0) 'no newline, scroll, wrap or clamped move while playing'
Assert ($p.Fake.Log[0] -eq "$e[?25l" -and $p.Fake.Log[-1] -eq "$e[0m$e[?25h" -and $p.Fake.CursorVisible) 'cursor hidden while playing, shown after'
Assert ($p.Fake.X -eq 0 -and $p.Fake.Y -eq ($lines.Count - 1)) 'cursor back on the prompt line, column 0'
$mid = [PokeshellTest.FakeConsole]::new(100, 40); $mid.Write($t); $mid.Write($p.Fake.Log[1])
[IO.File]::WriteAllText("$fx\dist\fx\bob-frame0.ans", $fxFrames[0], $utf8)   # the card as it looks on frame 0
$fr0 = [PokeshellTest.FakeConsole]::new(100, 40); $fr0.Write([Pokeshell.Core]::PullText($fx, 'fx', 'bob', 'Bob', 'frame0', 'rare holo', 5, $false, 'holo', '9/9', $false, '', ''))
Assert ($mid.Dump() -eq $fr0.Dump()) 'the first frame drawn is bundle frame 0, in place inside the frame border'
Assert (@($p.Fake.Log | Where-Object { $_.Contains("`n") }).Count -eq 0) 'no write contains a line feed'

$p = Invoke-FakePlay $t $fxAns $fxAnim -Max 2
Assert ($p.R.Stop -eq 'cap' -and $p.R.Frames -eq 23 -and $p.R.TotalMs -eq 2000 -and $p.Same) "the cap stops it (2 s cap: $($p.R.Frames) frames, $($p.R.TotalMs) ms) on the static card"
$p = Invoke-FakePlay $t $fxAns $fxAnim
Assert ($p.R.Stop -eq 'cap' -and $p.R.TotalMs -eq 30000 -and $p.R.Frames -eq 359) "default cap: 30 s ($($p.R.Frames) frames)"
$p = Invoke-FakePlay $t $fxAns $fxAnim -Max 300
Assert ($p.R.TotalMs -eq 30000) 'a longer cap is held to 30 s'
$p = Invoke-FakePlay $t $fxAns $fxAnim -Mode intro
Assert ($p.R.Stop -eq 'intro' -and $p.R.Frames -eq 16 -and $p.R.FrameIndex[-1] -eq 15 -and $p.Same) "intro: one loop, ending on the final frame ($($p.R.Frames) frames)"
$p = Invoke-FakePlay $t $fxAns $fxAnim -Mode intro -Setup { param($f) $f.KeyAt = 400 }
Assert ($p.R.Stop -eq 'key' -and $p.Same) 'intro: a key ends it early, on the static card'
$p = Invoke-FakePlay $t $fxAns $fxAnim -Setup { param($f) $f.CancelAt = 700 }
Assert ($p.R.Stop -eq 'cancel' -and $p.Same) 'Ctrl+C stops it, on the static card'
$p = Invoke-FakePlay $t $fxAns $fxAnim -Setup { param($f) $f.ResizeAt = 500; $f.ResizeW = 120 }
Assert ($p.R.Stop -eq 'resize' -and $p.R.FinalRestored -and $p.Same) 'resize (card still fits): stops, the static card is redrawn in place'
$p = Invoke-FakePlay $t $fxAns $fxAnim -Setup { param($f) $f.ResizeAt = 500; $f.ResizeW = 12 }
Assert ($p.R.Stop -eq 'resize' -and -not $p.R.FinalRestored) 'resize narrower than the card (rewrapped): stops without drawing'
$p = Invoke-FakePlay $t $fxAns $fxAnim -Setup { param($f) $f.KeyAt = 0 }
Assert ($p.R.Status -eq 'static' -and $p.R.Reason -eq 'key already waiting' -and $p.Fake.Writes -eq 0) 'a key typed before the first frame: no animation at all'
$p = Invoke-FakePlay $t $fxAns $fxAnim -W 12
Assert ($p.R.Status -eq 'static' -and $p.R.Reason -eq 'window too narrow' -and $p.Fake.Writes -eq 0) 'a window narrower than the card (it wrapped): static'
# a window shorter than the card: the rows scrolled out of view are skipped, nothing scrolls
$p = Invoke-FakePlay $t $fxAns $fxAnim -H 8 -Setup { param($f) $f.KeyAt = 600 }
Assert ($p.R.Status -eq 'played' -and $p.R.VisibleRows -eq 5 -and $p.R.ArtRows -eq 8) "short window: only the 5 visible art rows animate ($($p.R.VisibleRows)/$($p.R.ArtRows))"
Assert ($p.Fake.Scrolls -eq 0 -and $p.Fake.Clamps -eq 0 -and $p.Fake.Newlines -eq 0 -and $p.Same) 'short window: no scroll, no clamped move, ends on the static card'
$p = Invoke-FakePlay $t $fxAns $fxAnim -H 3
Assert ($p.R.Status -eq 'static' -and $p.R.Reason -like '*scrolled out*') 'the whole card scrolled away: static'
# a bundle whose final frame is not the printed card: stop and show the static card
$bad = "$fx\bad.anim"
[IO.File]::WriteAllText($bad, '{"lines": 8, "fps": 12, "frames": 16, "final": 15}' + "`n`f" + ((0..15 | ForEach-Object { New-ArtFrame ($_ + 1) }) -join "`f"), $utf8)
$p = Invoke-FakePlay $t $fxAns $bad
Assert ($p.R.Stop -eq 'mismatch' -and $p.Same) 'a bundle that does not end on the printed card: stopped, static card shown'
[IO.File]::WriteAllText($bad, '{"lines": 5, "fps": 12, "frames": 16, "final": 15}' + "`n`f" + ($fxFrames -join "`f"), $utf8)
$p = Invoke-FakePlay $t $fxAns $bad
Assert ($p.R.Status -eq 'static' -and $p.Fake.Writes -eq 0) 'a bundle of another size: static, nothing drawn'
# streaming: the first frame is drawn before the rest of the bundle is read
$big = "$fx\big.anim"   # 64 frames, ~300 KB
[IO.File]::WriteAllText($big, '{"lines": 8, "fps": 12, "frames": 64, "final": 63}' + "`n`f" + (((0..62 | ForEach-Object { New-ArtFrame $_ }) + $fxFrames[15]) -join "`f"), $utf8)
$fs = [IO.FileStream]::new($big, 'Open', 'Read'); $rd = [IO.StreamReader]::new($fs, $utf8, $false, 4096)
$fc = [PokeshellTest.FakeConsole]::new(100, 40); $fc.Write($t); $fc.KeyAt = 90
$r = [Pokeshell.Anim]::Play($rd, $l, 'untilkey', 30, $fc)
Assert ($r.Frames -eq 1 -and $fs.Position -lt $fs.Length / 2) "streamed: after one frame $($fs.Position) of $($fs.Length) bytes were read"
Assert ($r.FinalRestored) 'streamed: the final frame (the static .ans) is drawn without reading the rest'
$rd.Dispose()

Write-Host "4. redirected output: the static card only" -ForegroundColor Cyan
$cmdText = "`$env:POKESHELL_PULL='1'; . '$RepoRoot\scripts\lib\roll.ps1'; Show-PokeshellPull -Root '$fx' -Pack 'fx' -Character 'bob' -Name 'Bob' -Art 'set1-9' -Label 'rare holo' -Tier 5 -Frame 'holo' -Tag '9/9'"
$encCmd = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($cmdText))
$stats = Join-Path $st 'anim-stats.txt'
$env:POKESHELL_HOME = $st; $env:POKESHELL_ANIM_STATS = $stats
$out = 'exit' | & powershell.exe -NoProfile -NoLogo -NoExit -EncodedCommand $encCmd
$env:POKESHELL_ANIM_STATS = $null; $env:POKESHELL_HOME = $null
$outText = ($out -join "`n")
Assert ($outText.Contains($fxAns.Split("`n")[0]) -and $outText.Contains($fxAns.Split("`n")[7])) 'the static card is printed'
Assert (-not $outText.Contains("$e[?25l") -and -not $outText.Contains("$e[3A")) 'no cursor tricks in the file'
$sl = if (Test-Path $stats) { @(Get-Content $stats)[-1] } else { '' }
Assert ($sl -like "static`toutput redirected*") "the player saw the redirect: '$sl'"

Write-Host "5. end to end on a pseudoconsole (no window)" -ForegroundColor Cyan
function Start-Pty([string]$Command, [hashtable]$Env = @{}, [int]$Cols = 120, [int]$Rows = 50) {
  $saved = @{}
  foreach ($k in $Env.Keys) { $saved[$k] = [Environment]::GetEnvironmentVariable($k); [Environment]::SetEnvironmentVariable($k, $Env[$k]) }
  try {
    $enc64 = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes("Write-Host PTY-READY`r`n" + $Command))   # the card follows the marker within a few 100 ms
    [PokeshellTest.PtyProcess]::new("powershell.exe -NoProfile -NoLogo -NoExit -EncodedCommand $enc64", $Cols, $Rows)
  } finally { foreach ($k in $saved.Keys) { [Environment]::SetEnvironmentVariable($k, $saved[$k]) } }
}
function Merge([hashtable]$A, [hashtable]$B) { $h = @{} + $A; foreach ($k in $B.Keys) { $h[$k] = $B[$k] }; $h }
function Stop-Pty($P) { try { $P.Type("exit`r"); [void]$P.WaitExit(5000) } finally { $P.Dispose() } }
function Get-Stats { if (Test-Path $stats) { @(Get-Content $stats)[-1] } else { '' } }
function Wait-Stats([int]$N, [int]$Ms = 15000) { $sw = [Diagnostics.Stopwatch]::StartNew(); while ($sw.ElapsedMilliseconds -lt $Ms) { if ((Test-Path $stats) -and @(Get-Content $stats).Count -ge $N) { return $true }; Start-Sleep -Milliseconds 50 }; $false }
function Test-Screen($P, [string]$Printed, [int]$Cols = 120, [int]$Rows = 50) {
  # replay what the pseudoconsole drew and check the card's art rows are on screen as printed (the final frame)
  $scr = [PokeshellTest.FakeConsole]::new($Cols, $Rows); $scr.Write($P.Output)
  $ref = [PokeshellTest.FakeConsole]::new($Cols, 400); $ref.Write($Printed)
  $have = $scr.Dump().Split("`n"); $want = @($ref.Dump().Split("`n") | Where-Object { $_ -match '\S' -and $_.Contains([string][char]0x2580) })
  $at = 0; foreach ($w in $want) { $i = [Array]::IndexOf($have, $w, $at); if ($i -lt 0) { return $false }; $at = $i + 1 }
  $want.Count -gt 0
}
Remove-Item $stats -ErrorAction SilentlyContinue
$ptyEnv = @{ POKESHELL_HOME = $st; POKESHELL_ANIM_STATS = $stats; POKESHELL_ANIM_MAX = $null; POKESHELL_NO_ANIM = $null }
$P = Start-Pty $cmdText $ptyEnv
try {
  $ok = $P.WaitFor('PTY-READY', 20000)
  Start-Sleep -Milliseconds 1200            # let it loop a while
  Assert ($ok -and -not (Test-Path $stats)) 'the pulled tab prints the card, then keeps animating while idle'
  $P.Type('W')                              # the first key: stops the loop and must reach the prompt
  $played = Wait-Stats 1
  $P.Type("rite-Output ('pass'+'through')`r")
  $got = $P.WaitFor("passthrough", 10000)
  $s = Get-Stats
  Assert ($played -and $s -like "played`tuntilkey`tstop=key*") "the key stopped the loop: $s"
  Assert ($s -match 'frames=(\d+)' -and [int]$Matches[1] -ge 10) 'it was animating (>= 10 frames before the key)'
  Assert $got 'the key became the first character at the prompt: "W" + "rite-Output ..." ran as Write-Output'
  Assert (Test-Screen $P (Get-FxText)) 'the screen shows the static card after the key (replayed through the VT model)'
} finally { Stop-Pty $P }

Remove-Item $stats -ErrorAction SilentlyContinue
$P = Start-Pty $cmdText $ptyEnv
try {
  [void]$P.WaitFor('PTY-READY', 20000); Start-Sleep -Milliseconds 1000
  $P.Type([string][char]3)                  # Ctrl+C
  $stopped = Wait-Stats 1 5000
  $P.Type("Write-Output ('after'+'-ctrl-c')`r")
  $alive = $P.WaitFor('after-ctrl-c', 10000)
  Assert ($stopped -and (Get-Stats) -like "*stop=cancel*") "Ctrl+C stops the loop: $(Get-Stats)"
  Assert $alive 'the tab stays usable after Ctrl+C'
} finally { Stop-Pty $P }

Remove-Item $stats -ErrorAction SilentlyContinue
$P = Start-Pty $cmdText (Merge $ptyEnv @{ POKESHELL_ANIM_MAX = '1.5' })
try {
  $capped = Wait-Stats 1 20000
  Assert ($capped -and (Get-Stats) -match "stop=cap\tframes=1[2-7]\t.*total=1[5-6]\d\dms") "with no key it stops at the cap by itself (1.5 s test cap): $(Get-Stats)"
  $P.Type("Write-Output ('cap'+'-ok')`r")
  Assert ($P.WaitFor('cap-ok', 10000)) 'and the prompt works after the cap'
} finally { Stop-Pty $P }

Remove-Item $stats -ErrorAction SilentlyContinue
$P = Start-Pty $cmdText (Merge $ptyEnv @{ POKESHELL_NO_ANIM = '1' })
try { [void](Wait-Stats 1 20000); Assert ((Get-Stats) -like "static`tanim=off*") "POKESHELL_NO_ANIM=1: static ($(Get-Stats))" } finally { Stop-Pty $P }

Remove-Item $stats -ErrorAction SilentlyContinue
$sp = Join-Path $fx 'show.ps1'; [IO.File]::WriteAllText($sp, ". '$RepoRoot\scripts\lib\roll.ps1'; Show-PokeshellPull -Root '$fx' -Pack 'fx' -Character 'bob' -Name 'Bob' -Art 'set1-9' -Label 'rare holo' -Tier 5 -Frame 'holo'; [IO.File]::WriteAllText('$st\show-done.txt', 'x')")
$P = Start-Pty "& '$sp'" $ptyEnv
try {
  $sw = [Diagnostics.Stopwatch]::StartNew(); while (-not (Test-Path "$st\show-done.txt") -and $sw.ElapsedMilliseconds -lt 20000) { Start-Sleep -Milliseconds 50 }
  Assert ((Test-Path "$st\show-done.txt") -and -not (Test-Path $stats)) 'Show-PokeshellPull from a script (pokeshell show) prints without animating'
} finally { Stop-Pty $P }

Write-Host "6. the real pack (Glaceon V)" -ForegroundColor Cyan
$gl = Join-Path $RepoRoot 'dist\pokemon\glaceon-swsh7-174.ans'
if (-not (Test-Path $gl) -or -not (Test-Path ($gl -replace '\.ans$', '.anim'))) {
  Write-Host "  skip  dist\pokemon has no Glaceon V .ans + .anim (build: tools\build_realcards.py import evs)" -ForegroundColor DarkGray
} else {
  $n = 0; $badAnims = @()
  foreach ($a in Get-ChildItem (Join-Path $RepoRoot 'dist\pokemon') -Filter *.anim) {
    $n++
    $parts = [IO.File]::ReadAllText($a.FullName, $utf8).Split([char]12)
    $hdr = $parts[0] | ConvertFrom-Json
    $ans = [IO.File]::ReadAllText(($a.FullName -replace '\.anim$', '.ans'), $utf8)
    if ($parts.Count - 1 -ne $hdr.frames -or $parts[1 + $hdr.final] -ne $ans) { $badAnims += $a.Name }
  }
  Assert ($n -gt 0 -and -not $badAnims) "every dist .anim ($n) ends exactly on its card's .ans$(if ($badAnims) { ': not ' + ($badAnims -join ', ') })"
  # a dry-run pull that lands on Glaceon V: the tab it would open plays the loop
  $rs = New-TestState 'anim-real'
  [void](New-PokeshellCore $rs); [void](New-PokeshellAnimCore $rs); Update-PokeshellRollCache -Root $RepoRoot -StateDir $rs   # as `pokeshell install` leaves it
  $pull = $null
  foreach ($seed in 1..3000) {
    [IO.File]::Delete("$rs\spawn-gate.txt")   # layer 4 allows one spawn per 3 s: each dry run starts with a fresh gate
    $x = Invoke-Fresh { Invoke-PokeshellRoll -Root $RepoRoot -StateDir $rs -ProfileId $PlainGuid -Argv @('powershell.exe') -Seed $seed -FoilChance 1 -DryRun -Quiet }
    if ($x.Art -eq 'swsh7-174' -and $x.Action -eq 'foil' -and -not $x.Shiny) { $pull = $x; break }
  }
  Assert ($null -ne $pull) "a dry-run foil pull of Glaceon V (seed $seed, skin $($pull.Skin))"
  if ($pull) {
    $sel = [Pokeshell.Anim]::Find($RepoRoot, $pull.Pack, $pull.Character, $pull.Art, $pull.Shiny)
    Assert ($sel[0] -like '*glaceon-swsh7-174.anim') "the pull selects playback: $([IO.Path]::GetFileName($sel[0]))"
    $tabCmd = [Text.Encoding]::Unicode.GetString([Convert]::FromBase64String($pull.WtArgs[-1]))
    Assert ($pull.WtArgs -contains '-NoExit' -and $tabCmd -like '*Show-PokeshellPull*swsh7-174*') 'the tab it would open runs Show-PokeshellPull for it (-NoExit -EncodedCommand)'
    Remove-Item $stats -ErrorAction SilentlyContinue
    $P = Start-Pty $tabCmd (Merge $ptyEnv @{ POKESHELL_HOME = $rs }) -Cols 120 -Rows 50
    try {
      [void]$P.WaitFor('PTY-READY', 20000); Start-Sleep -Milliseconds 1500
      $P.Type('W'); $played = Wait-Stats 1
      $P.Type("rite-Output ('glaceon'+'-typed')`r")
      $got = $P.WaitFor('glaceon-typed', 10000)
      Assert ($played -and (Get-Stats) -like "played`tuntilkey`tstop=key*rows=33/33*") "the pulled Glaceon V tab animates until the key: $(Get-Stats)"
      Assert $got 'Glaceon V: the key reaches the prompt'
      $printed = [Pokeshell.Core]::PullText($RepoRoot, 'pokemon', 'glaceon', $pull.Name, 'swsh7-174', $pull.Label, $pull.Tier, $false, $pull.Frame, $pull.Tag, $false, '', '')
      Assert (Test-Screen $P $printed) 'Glaceon V: the screen ends on the static card'
    } finally { Stop-Pty $P }
    # the same card printed in the plain tab (its tier has no installed skin): the $PROFILE hook plays it too
    $ns = Join-Path ([IO.Path]::GetTempPath()) "pokeshell-test-anim-noskin-$PID"
    Remove-Item $ns -Recurse -Force -ErrorAction SilentlyContinue; [void][IO.Directory]::CreateDirectory($ns)
    [void](New-PokeshellCore $ns); [void](New-PokeshellAnimCore $ns); Update-PokeshellRollCache -Root $RepoRoot -StateDir $ns
    $hs = $null
    foreach ($seed in 1..3000) {
      $x = Invoke-Fresh { [Pokeshell.Core]::Roll($RepoRoot, $ns, $PlainGuid, @('powershell.exe'), [DateTime]::UtcNow.Ticks, $seed, -1, $null, $null, "$RepoRoot\scripts\lib") }
      if ($x.Art -eq 'swsh7-174' -and $x.Action -eq 'common' -and -not $x.Shiny) { $hs = $seed; break }
    }
    Assert ($null -ne $hs) "with no skin installed Glaceon V prints in the plain tab (seed $hs)"
    $hook = [IO.File]::ReadAllText("$RepoRoot\scripts\pokeshell-profile.ps1").Replace('$PSScriptRoot', '$__hookDir').Replace('[Environment]::GetCommandLineArgs()', "@('powershell.exe')")
    # Startup(...) = Roll with fresh dice (plus, with the binder, the earned rule's prompt hook): roll with the found seed
    $roll = "[Pokeshell.Core]::Roll(`$root, `$d, `$env:WT_PROFILE_ID, `$a, [DateTime]::UtcNow.Ticks, $hs, -1, `$null, `$null, `$lib)"
    $hook = [regex]::Replace($hook, '\[Pokeshell\.Core\]::Startup\([^)]*\)', [Text.RegularExpressions.MatchEvaluator] { param($m) $roll })
    Assert ($hook.Contains("::Roll(`$root")) 'hook text substituted (fixed seed, fresh-tab argv)'
    Remove-Item $stats -ErrorAction SilentlyContinue
    $P = Start-Pty ("`$env:WT_PROFILE_ID = '$PlainGuid'; `$__hookDir = '$RepoRoot\scripts'`r`n" + $hook) (Merge $ptyEnv @{ POKESHELL_HOME = $ns })
    try {
      [void]$P.WaitFor('PTY-READY', 20000); Start-Sleep -Milliseconds 1500
      $P.Type('W'); $played = Wait-Stats 1
      $P.Type("rite-Output ('same'+'-tab')`r")
      $got = $P.WaitFor('same-tab', 10000)
      Assert ($played -and (Get-Stats) -like "played`tuntilkey`tstop=key*") "same tab (the hook): animates until the key: $(Get-Stats)"
      Assert $got 'same tab: the key reaches the prompt'
    } finally { Stop-Pty $P }
    Remove-Item $ns -Recurse -Force -ErrorAction SilentlyContinue
  }
  Remove-Item $rs -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "7. startup: static print -> first frame" -ForegroundColor Cyan
# fresh powershell.exe per run, on a pseudoconsole, running the pulled tab's real command (Show-PokeshellPull: the
# static print, then the player: load its DLL, check, find the layout, open the bundle, read frame 0). The printed card
# is the loop's final frame, so the first new frame is due one period (83 ms) after the print: "ready" is how long the
# player needed before it could draw it, "first" when it did.
$ts = Join-Path $st 'timing-stats.txt'; Remove-Item $ts -ErrorAction SilentlyContinue
$probe = if (Test-Path $gl) { "`$env:POKESHELL_PULL='1'; . '$RepoRoot\scripts\lib\roll.ps1'; Show-PokeshellPull -Root '$RepoRoot' -Pack 'pokemon' -Character 'glaceon' -Name 'Glaceon V' -Art 'swsh7-174' -Label 'rare ultra' -Tier 5 -Frame 'silver' -Tag '174/203'; exit" } else { "$cmdText; exit" }
& powershell.exe -NoProfile -Command "[void][Reflection.Assembly]::LoadFile('$animDll')"   # warm the disk cache once
for ($i = 0; $i -lt $Runs; $i++) {
  $P = Start-Pty $probe (Merge $ptyEnv @{ POKESHELL_ANIM_MAX = '0.3'; POKESHELL_ANIM_STATS = $ts })
  try { [void]$P.WaitExit(20000) } finally { $P.Dispose() }
}
$rows = @(if (Test-Path $ts) { Get-Content $ts | ForEach-Object {
  $ready = if ($_ -match 'ready=(\d+)ms') { [double]$Matches[1] } else { -1 }
  $first = if ($_ -match "`tfirst=(\d+)ms") { [double]$Matches[1] } else { -1 }
  [pscustomobject]@{ ready = $ready; first = $first; played = $_ -like 'played*' } } })
if ($rows.Count -eq $Runs -and -not ($rows | Where-Object { -not $_.played })) {
  $sR = @($rows.ready | Sort-Object); $sF = @($rows.first | Sort-Object)
  $mR = $sR[[int]($sR.Count / 2)]; $mF = $sF[[int]($sF.Count / 2)]
  Write-Host ("  {0} runs ({1}): after the static print, frame 0 ready in {2} ms (median; min {3}, max {4}); drawn at {5} ms (median; due at 83)" -f $Runs, $(if (Test-Path $gl) { 'Glaceon V' } else { 'fixture card' }), $mR, $sR[0], $sR[-1], $mF)
  Assert ($mR -lt 50) "the player is ready within the 50 ms budget after the static print ($mR ms)"
  Assert ($mF -lt 83 + 50) "the first new frame is on screen when due (83 ms after the print), give or take the budget (median $mF ms, incl. writing it)"
} else { Assert $false "timing runs: $($rows.Count) of $Runs played" }

Remove-Item $fx -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item $st -Recurse -Force -ErrorAction SilentlyContinue
Write-Host ''
if ($script:Failures) { Write-Host "anim: $script:Failures FAILED" -ForegroundColor Red; exit 1 }
Write-Host "anim: all passed" -ForegroundColor Green
