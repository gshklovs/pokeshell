<#
`pokeshell clip` and the `clip` shortcut, against a throwaway state dir. Never touches the real clipboard: the card
goes to $env:POKESHELL_CLIP_SINK (a file) and clip.exe is a fake one ($env:POKESHELL_CLIP_EXE).
  powershell -NoProfile -File tests\test-clip.ps1
#>
. (Join-Path $PSScriptRoot '_setup.ps1')
$st = New-TestState 'clip'
$cli = Join-Path $RepoRoot 'scripts\pokeshell.ps1'
$e = [char]27; $crlf = "`r`n"
$utf8 = [Text.UTF8Encoding]::new($false)
$sink = Join-Path $st 'clip-sink.txt'
Import-PokeshellCore $st

# the CLI in a child process, stdout as UTF-8 text exactly as written (no Out-String, no console code page)
function Invoke-CliRaw([string[]]$A, [hashtable]$Env = @{}) {
  $quoted = ($A | ForEach-Object { "'" + $_.Replace("'", "''") + "'" }) -join ' '
  $cmd = "[Console]::OutputEncoding = [Text.UTF8Encoding]::new(`$false); & '$cli' $quoted; exit `$LASTEXITCODE"
  $psi = [Diagnostics.ProcessStartInfo]::new('powershell.exe', '-NoProfile -ExecutionPolicy Bypass -EncodedCommand ' + [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($cmd)))
  $psi.UseShellExecute = $false; $psi.RedirectStandardOutput = $true; $psi.RedirectStandardError = $true; $psi.RedirectStandardInput = $true
  $psi.StandardOutputEncoding = $utf8
  $psi.EnvironmentVariables['POKESHELL_HOME'] = $st
  foreach ($k in 'POKESHELL_PULL', 'POKESHELL_DISPLAY', 'POKESHELL_CLIP_SINK') { [void]$psi.EnvironmentVariables.Remove($k) }
  foreach ($k in $Env.Keys) { $psi.EnvironmentVariables[$k] = $Env[$k] }
  $p = [Diagnostics.Process]::Start($psi); $p.StandardInput.Close()
  $err = $p.StandardError.ReadToEndAsync(); $out = $p.StandardOutput.ReadToEnd(); $p.WaitForExit()
  @{ out = $out; err = $err.Result; code = $p.ExitCode }
}
function Clip-To-Sink([string[]]$A, [hashtable]$Env = @{}) {
  Remove-Item $sink -ErrorAction SilentlyContinue
  $Env['POKESHELL_CLIP_SINK'] = $sink
  $r = Invoke-CliRaw (@('clip') + $A) $Env
  $r['clip'] = if (Test-Path $sink) { [IO.File]::ReadAllText($sink, $utf8) } else { $null }
  $r
}
# the hygiene clip applies to what show prints: no blank line before the card, one CRLF after it
function Trim-Card([string]$s) { $s.Trim([char[]]"`r`n") + $crlf }

# fixture pulls, written the way Core.Roll logs them (time pack character tier art skin shiny flags id= boot=)
$pk = Read-PokeshellPack $RepoRoot 'pokemon'
$boot = [Pokeshell.Core]::BootId()
$fx = @(
  @{ id = '01CLIPTEST0000000000000001'; pack = 'pokemon'; char = 'pikachu'; tier = 'common'; art = 'base1-58'; shiny = 0; show = @('pokemon/base1-58') },
  @{ id = '01CLIPTEST0000000000000002'; pack = 'pokemon'; char = 'pikachu'; tier = 'common'; art = 'base1-58'; shiny = 1; show = @('pokemon/base1-58', '-shiny') },
  @{ id = '01CLIPTEST0000000000000003'; pack = 'pokemon'; char = 'glaceon'; tier = $pk.cardIndex['swsh7-40'].tierId; art = 'swsh7-40'; shiny = 0; show = @('pokemon/swsh7-40') }
)
$log = foreach ($f in $fx) { "2026-09-30T10:00:00`t$($f.pack)`t$($f.char)`t$($f.tier)`t$($f.art)`t`t$($f.shiny)`tpending`tid=$($f.id)`tboot=$boot" }
[IO.File]::WriteAllLines((Join-Path $st 'pulls.log'), [string[]]$log)
Assert (Test-Path (Join-Path $RepoRoot 'dist\pokemon\glaceon-swsh7-40.anim')) "fixture: glaceon swsh7-40 is an animated card (its .anim is here)"

Write-Host "a. pokeshell clip = what show prints for the tab's pull (colour escapes, CRLF), in both display modes" -ForegroundColor Cyan
foreach ($disp in 'card', 'picture') {
  foreach ($f in $fx) {
    $shown = Invoke-CliRaw (@('show') + $f.show) @{ POKESHELL_DISPLAY = $disp }
    $r = Clip-To-Sink @() @{ POKESHELL_PULL = $f.id; POKESHELL_DISPLAY = $disp }
    $want = Trim-Card $shown.out
    $c = $r.clip
    $lfOnly = $c -and ([regex]::Matches($c, "(?<!`r)`n").Count -eq 0)
    Assert ($r.code -eq 0 -and $c -and $c.Equals($want) -and $c.Contains("$e[") -and $lfOnly -and $c.EndsWith($crlf)) "$disp, $($f.pack)/$($f.art)$(if ($f.shiny) { ' shiny' }): exact bytes of show ($(if ($c) { $c.Length } else { 0 }) chars, $(if ($c) { ([regex]::Matches($c, $crlf)).Count } else { 0 }) CRLF lines)$(if ($r.code) { ': ' + $r.out + $r.err })"
  }
}
$r = Clip-To-Sink @() @{ POKESHELL_PULL = $fx[1].id }
$name = $pk.cardIndex['base1-58'].name; $label = $pk.tiers[$pk.cardIndex['base1-58'].tier].label
Assert ($r.out.Trim() -eq "copied $name ($label, shiny) to the clipboard") "one line: '$($r.out.Trim())'"
$fr = Clip-To-Sink @('-picture') @{ POKESHELL_PULL = $fx[0].id }
$sp = Invoke-CliRaw @('show', 'pokemon/base1-58', '-picture')
Assert ($fr.clip -eq (Trim-Card $sp.out) -and -not $fr.clip.Contains([string][char]0x256d)) "-picture overrides the display setting (just the art, no frame)"
$anim = Clip-To-Sink @() @{ POKESHELL_PULL = $fx[2].id; POKESHELL_DISPLAY = 'picture' }
$rest = [IO.File]::ReadAllText((Join-Path $RepoRoot 'dist\pokemon\glaceon-swsh7-40.ans'), $utf8).Replace("`r`n", "`n").Replace("`n", $crlf).Trim([char[]]"`r`n") + $crlf
Assert ($anim.clip -eq $rest) "animated card: its resting frame (the .ans), no animation frames"

Write-Host "b. -Plain" -ForegroundColor Cyan
foreach ($f in $fx) {
  $col = (Clip-To-Sink @() @{ POKESHELL_PULL = $f.id }).clip
  $pl = Clip-To-Sink @('-Plain') @{ POKESHELL_PULL = $f.id }
  $n1 = ([regex]::Matches($col, $crlf)).Count; $n2 = ([regex]::Matches($pl.clip, $crlf)).Count
  Assert ($pl.code -eq 0 -and -not $pl.clip.Contains([string]$e) -and $n1 -eq $n2 -and $pl.clip.Contains([string][char]0x2580) -and $pl.clip.Contains($pk.cardIndex[$f.art].name)) "$($f.pack)/$($f.art): no ESC bytes, $n2 lines like the colour copy, half blocks kept"
}

Write-Host "c. no pull in this tab" -ForegroundColor Cyan
$r = Clip-To-Sink @()
Assert ($r.code -eq 1 -and $r.out -match 'no card was pulled in this tab' -and $null -eq $r.clip) "exit 1, a short message, nothing copied: '$($r.out.Trim())'"
$r = Clip-To-Sink @() @{ POKESHELL_PULL = '01NOSUCHPULL00000000000000' }
Assert ($r.code -eq 1 -and $r.out -match "isn't in pulls.log" -and $null -eq $r.clip) "an unknown pull: exit 1, nothing copied"

Write-Host "   -Pull / -Card" -ForegroundColor Cyan
$r = Clip-To-Sink @('-Pull', $fx[1].id)
Assert ($r.code -eq 0 -and $r.clip -eq (Trim-Card (Invoke-CliRaw (@('show') + $fx[1].show)).out)) "-Pull <id> copies another pull"
$r = Clip-To-Sink @('-Pull', 'latest')
Assert ($r.code -eq 0 -and $r.clip -eq (Trim-Card (Invoke-CliRaw (@('show') + $fx[-1].show)).out)) "-Pull latest: the newest pull"
$r = Clip-To-Sink @('-Card', 'pokemon/swsh7-40', '-shiny')
Assert ($r.code -eq 0 -and $r.clip -eq (Trim-Card (Invoke-CliRaw @('show', 'pokemon/swsh7-40', '-shiny')).out) -and $r.out -match 'copied Glaceon V') "-Card <id> [-shiny] copies any card"
$r = Clip-To-Sink @('-Card', 'pokemon/nobody')
Assert ($r.code -eq 1 -and $null -eq $r.clip) "-Card with an unknown card: exit 1"

Write-Host "d. the clip shortcut: piped input and arguments go to clip.exe, alone it is pokeshell clip" -ForegroundColor Cyan
# a fake clip.exe: records its arguments and (only when redirected) its stdin
$fake = Join-Path $st 'fakeclip.exe'
Add-Type -OutputAssembly $fake -OutputType ConsoleApplication -TypeDefinition @"
using System; using System.IO;
public static class FakeClip { public static int Main(string[] a) {
  string d = Path.GetDirectoryName(System.Reflection.Assembly.GetExecutingAssembly().Location);
  File.AppendAllText(Path.Combine(d, "fake-calls.txt"), "call\t" + string.Join(" ", a) + "\t" + (Console.IsInputRedirected ? "stdin=" + Console.In.ReadToEnd().Replace("\r", "\\r").Replace("\n", "\\n") : "console") + "\n");
  return a.Length > 0 && a[0] == "/fail" ? 3 : 0; } }
"@
$calls = Join-Path $st 'fake-calls.txt'
$hookText = [IO.File]::ReadAllText((Join-Path $RepoRoot 'scripts\pokeshell-profile.ps1'))
$block = [regex]::Match($hookText, '(?s)# clip:begin.*?# clip:end').Value
Assert ($block -match 'function global:clip') "the profile hook defines clip (between # clip:begin / # clip:end)"
$psm = [IO.File]::ReadAllText((Join-Path $RepoRoot 'pokeshell.psm1'))
$body = { param($t) [regex]::Match($t, '(?s)function (global:)?clip \{.*?\n\}').Value -replace 'function (global:)?clip', '' }
Assert ((& $body $block) -eq (& $body $psm) -and (& $body $psm)) "the module's clip is the same function"

$env:POKESHELL_HOME = $st; $env:POKESHELL_CLIP_EXE = $fake
$script:pokeshellCalls = @()
function global:pokeshell { $script:pokeshellCalls += , @($args) }   # stands in for the real command
. ([scriptblock]::Create($block))
try {
  Remove-Item $calls -ErrorAction SilentlyContinue; $script:pokeshellCalls = @()
  'x' | clip
  Get-Content (Join-Path $RepoRoot 'LICENSE') -TotalCount 2 | clip
  $got = @(Get-Content $calls)
  Assert ($got.Count -eq 2 -and $got[0] -eq "call`t`tstdin=x\r\n" -and $got[1].StartsWith("call`t`tstdin=") -and $got[1].Contains('\r\n') -and $script:pokeshellCalls.Count -eq 0) "piped input goes to clip.exe unchanged, pokeshell not called ($($got -join ' | '))"
  Remove-Item $calls -ErrorAction SilentlyContinue
  clip /fail
  $code = $LASTEXITCODE
  $got = @(Get-Content $calls)
  Assert ($got.Count -eq 1 -and $got[0] -like "call`t/fail`t*" -and $code -eq 3 -and $script:pokeshellCalls.Count -eq 0) "arguments go to clip.exe, its exit code comes back ($code)"
  Remove-Item $calls -ErrorAction SilentlyContinue
  clip
  Assert (-not (Test-Path $calls) -and $script:pokeshellCalls.Count -eq 1 -and ($script:pokeshellCalls[0] -join ' ') -eq 'clip') "clip alone runs pokeshell clip, not clip.exe"
  Set-PokeshellConfigValue $st 'clip_alias' 'off'; $script:pokeshellCalls = @()
  Remove-Item $calls -ErrorAction SilentlyContinue
  # alias off: clip alone is clip.exe again (in a child whose stdin is an empty file, as a console's would block)
  [IO.File]::WriteAllText("$st\clipblock.ps1", "function global:pokeshell { 'POKESHELL-CALLED' }`r`n" + $block + "`r`nclip`r`n", $utf8)
  [IO.File]::WriteAllText("$st\empty.txt", '')
  $cp = Start-Process powershell.exe -ArgumentList '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$st\clipblock.ps1`"" -NoNewWindow -Wait -PassThru -RedirectStandardInput "$st\empty.txt" -RedirectStandardOutput "$st\o.txt"
  $o = [IO.File]::ReadAllText("$st\o.txt")
  $got = @(Get-Content $calls -ErrorAction SilentlyContinue)
} finally { Remove-Item Function:\clip -ErrorAction SilentlyContinue }
Assert ($got.Count -eq 1 -and $o -notmatch 'POKESHELL-CALLED') "pokeshell clip alias off: clip alone is clip.exe ($($got -join ' | '))"
$r = Invoke-CliRaw @('clip', 'alias')
Assert ($r.out -match 'clip alias: off') "pokeshell clip alias shows it: $($r.out.Trim())"
$null = Invoke-CliRaw @('clip', 'alias', 'on')
Assert ((Get-Content (Join-Path $st 'config.txt')) -contains 'clip_alias=on') "pokeshell clip alias on saves it (config.txt clip_alias)"
$r = Invoke-CliRaw @('clip', 'alias', 'maybe')
Assert ($r.code -eq 1) "clip alias maybe: refused"
Remove-Item Env:POKESHELL_CLIP_EXE; Remove-Item Env:POKESHELL_HOME
Remove-Item Function:\pokeshell -ErrorAction SilentlyContinue

Write-Host "e. the clip function adds under 2 ms to the profile hook" -ForegroundColor Cyan
# fresh processes dot-source the hook's first lines with and without the clip block (what the hook parses and runs)
$without = "function global:binder { & `"`$PSScriptRoot\pokeshell.ps1`" binder @args }`r`n"
[IO.File]::WriteAllText("$st\t-without.ps1", $without, $utf8)
[IO.File]::WriteAllText("$st\t-with.ps1", $without + $block + "`r`n", $utf8)
$probe = "$st\t-probe.ps1"
[IO.File]::WriteAllText($probe, 'param($f) $sw = [Diagnostics.Stopwatch]::StartNew(); . $f; [Console]::Out.WriteLine("MS`t" + $sw.Elapsed.TotalMilliseconds)', $utf8)
$ms = @{ with = @(); without = @() }
foreach ($i in 1..15) {
  foreach ($k in 'without', 'with') {   # interleaved, so machine load hits both alike
    $v = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $probe "$st\t-$k.ps1" | Where-Object { "$_" -like 'MS*' }
    $ms[$k] += [double]("$v".Split("`t")[1])
  }
}
$med = { param($a) $s = @($a | Sort-Object); $s[[int]($s.Count / 2)] }
$d = [math]::Round((& $med $ms.with) - (& $med $ms.without), 2)
Assert ($d -lt 2) ("defining clip: +{0} ms (median of 15 fresh processes: {1:0.00} vs {2:0.00} ms)" -f $d, (& $med $ms.with), (& $med $ms.without))

Remove-Item $st -Recurse -Force -ErrorAction SilentlyContinue
if ($script:Failures) { Write-Host "$script:Failures failed" -ForegroundColor Red; exit 1 }
Write-Host 'all clip tests passed' -ForegroundColor Green
