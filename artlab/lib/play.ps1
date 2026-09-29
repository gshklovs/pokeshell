<#
.SYNOPSIS
  Play an animated pixel-art card in place in the terminal (style-lab prototype).

.EXAMPLE
  .\play.ps1 holo_pikachu              # ~1.5 s intro, ends on the card's final frame
  .\play.ps1 gold -Loops 2             # two full loops
  .\play.ps1 pikachu -UntilKey         # loop while idle, stop the instant a key is pressed (key is NOT consumed)

.NOTES
  Works in Windows PowerShell 5.1 and PowerShell 7 inside Windows Terminal.
  Frames come from <card>\<card>.anim (built by build_anim.py): a JSON header line, then
  each full truecolor half-block frame separated by a form feed.
  Safety: if the console is redirected, too small, or the session is not an interactive
  console host, it prints just the final frame (no cursor tricks, no waiting). -Force skips
  the interactivity check (not the size/redirection checks).
#>
param(
    [Parameter(Mandatory = $true, Position = 0)][string]$Card,
    [double]$Seconds = 1.5,
    [int]$Loops = 0,
    [int]$Final = -1,
    [int]$Fps = 0,
    [switch]$UntilKey,
    [double]$MaxSeconds = 30,
    [switch]$Force,
    [switch]$Stats
)

$ErrorActionPreference = 'Stop'
$esc = [char]27

# ---- locate + load the frame bundle ---------------------------------------------------
$dir = $PSScriptRoot
$file = Join-Path $dir "$Card\$Card.anim"
if (-not (Test-Path -LiteralPath $file)) {
    $hit = Get-ChildItem -LiteralPath $dir -Directory | Where-Object { $_.Name -like "*$Card*" } | Select-Object -First 1
    if (-not $hit) { throw "no animated card matching '$Card' in $dir" }
    $file = Join-Path $hit.FullName "$($hit.Name).anim"
}
$raw = [IO.File]::ReadAllText($file, [Text.Encoding]::UTF8)
$parts = $raw.Split([char]12)
$hdr = $parts[0] | ConvertFrom-Json
$lines = [int]$hdr.lines
if ($Fps -le 0) { $Fps = [int]$hdr.fps }
if ($Final -lt 0) { $Final = [int]$hdr.final }
$n = $parts.Length - 1
# erase-to-end-of-line on every line so a frame fully overwrites the previous one
$frames = New-Object 'string[]' $n
for ($i = 0; $i -lt $n; $i++) { $frames[$i] = $parts[$i + 1].Replace("`n", "$esc[K`n") }
$Final = (($Final % $n) + $n) % $n
$up = "$esc[${lines}A`r"

function Write-Raw([string]$s) { $Host.UI.Write($s) }

# ---- can we animate here? ------------------------------------------------------------
$why = $null
try {
    if ([Console]::IsOutputRedirected) { $why = 'output redirected' }
    elseif ($Host.Name -ne 'ConsoleHost') { $why = "host '$($Host.Name)'" }
    elseif ([Console]::WindowWidth -lt 49 -or [Console]::WindowHeight -lt ($lines + 2)) { $why = 'window too small' }
    elseif ($UntilKey -and [Console]::IsInputRedirected) { $why = 'input redirected' }
    elseif (-not $Force) {
        # a profile also runs for `powershell -Command/-File ...` launched by other programs:
        # only animate in a session that will end at an interactive prompt
        $argsLine = ' ' + ([Environment]::GetCommandLineArgs() -join ' ')
        $scripted = $argsLine -match '(?i)\s-(c|command|f|file|e|ec|enc|encodedcommand)(\s|$)'
        # -NoExit -Command/-File still runs the command BEFORE the prompt: an intro is ok there,
        # but an until-key loop would hold that command hostage, so it is refused.
        if (-not [Environment]::UserInteractive -or $argsLine -match '(?i)\s-noni' -or
            ($scripted -and ($UntilKey -or $argsLine -notmatch '(?i)\s-noe'))) {
            $why = 'non-interactive session'
        }
    }
} catch { $why = 'no console' }

if ($why) {
    Write-Raw $frames[$Final]
    if ($Stats) { Write-Host "[play] static: $why" }
    return
}

# ---- play -------------------------------------------------------------------------------
$frameMs = 1000.0 / $Fps
$sw = [Diagnostics.Stopwatch]::StartNew()
$cpu0 = if ($Stats) { (Get-Process -Id $PID).TotalProcessorTime } else { $null }
$width0 = [Console]::WindowWidth
$shown = 0
$finalOnScreen = $false
$stopReason = 'done'
try {
    Write-Raw "$esc[?25l"
    if ($UntilKey) {
        # loop from the final frame's successor forever (capped); poll only, never read the key
        $cap = [int]($MaxSeconds * 1000)
        $idx = ($Final + 1) % $n
        while ($true) {
            if ([Console]::KeyAvailable) { $stopReason = 'key'; break }
            if ($shown) { Write-Raw ($up + $frames[$idx]) } else { Write-Raw $frames[$idx] }
            $shown++
            $idx = ($idx + 1) % $n
            $due = $shown * $frameMs
            while ($sw.ElapsedMilliseconds -lt $due) {
                if ([Console]::KeyAvailable) { break }
                [Threading.Thread]::Sleep(10)
            }
            if ($sw.ElapsedMilliseconds -ge $cap) { $stopReason = 'cap'; break }
            if ([Console]::WindowWidth -ne $width0) { $stopReason = 'resize'; break }   # reflow would break cursor-up
        }
    } else {
        $count = if ($Loops -gt 0) { $Loops * $n } else { [Math]::Max(1, [int][Math]::Round($Seconds * $Fps)) }
        # start so that the last frame played IS the final frame: no jump at the end
        $idx = (($Final + 1 - $count) % $n + $n) % $n
        for ($k = 0; $k -lt $count; $k++) {
            if ($shown) { Write-Raw ($up + $frames[$idx]) } else { Write-Raw $frames[$idx] }
            $shown++
            $idx = ($idx + 1) % $n
            if ($k -lt $count - 1) {
                $wait = [int]($shown * $frameMs - $sw.ElapsedMilliseconds)
                if ($wait -gt 0) { [Threading.Thread]::Sleep($wait) }
            }
        }
        $finalOnScreen = $true   # the last frame played was the final frame
    }
} catch {
    $stopReason = "error: $($_.Exception.Message)"
} finally {
    # always end on the clean final frame with the cursor visible, even on error / Ctrl+C
    if (-not $finalOnScreen) {
        if ($shown -gt 0) { Write-Raw ($up + $frames[$Final]) } else { Write-Raw $frames[$Final] }
    }
    Write-Raw "$esc[0m$esc[?25h"
}
if ($Stats) {
    $cpu = ((Get-Process -Id $PID).TotalProcessorTime - $cpu0).TotalMilliseconds
    $ms = $sw.ElapsedMilliseconds
    Write-Host ("[play] {0}: {1} frames in {2} ms, stop={3}, cpu {4:N0} ms ({5:N1}% of one core)" -f `
        (Split-Path $file -Leaf), $shown, $ms, $stopReason, $cpu, (100.0 * $cpu / [Math]::Max(1, $ms)))
}
