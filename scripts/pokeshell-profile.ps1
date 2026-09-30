# pokeshell $PROFILE hook:  . "<repo>\scripts\pokeshell-profile.ps1"   (pokeshell install prints the line)
# Defines `pokeshell` (and `binder`, `clip`) and rolls the startup pull on fresh plain tabs. Kept tiny because it runs on every
# new shell: a common pull is one call into the compiled core (lib\Pokeshell.cs) and one write. Foils,
# a stale roll cache and the first compile go through lib\roll.ps1. Never throws into your profile;
# errors go to %LOCALAPPDATA%\pokeshell\errors.log.
function global:pokeshell { & "$PSScriptRoot\pokeshell.ps1" @args }
function global:binder { & "$PSScriptRoot\pokeshell.ps1" binder @args }   # the binder app (pokeshell binder)
# clip:begin  `clip` alone copies this tab's card (pokeshell clip); piped input or any argument goes to Windows' clip.exe
# unchanged. No work at load: the body runs only when called (the same function is in pokeshell.psm1).
function global:clip {
  $exe = if ($env:POKESHELL_CLIP_EXE) { $env:POKESHELL_CLIP_EXE } else { "$env:SystemRoot\System32\clip.exe" }   # (the variable: tests only)
  if ($MyInvocation.ExpectingInput) { $input | & $exe @args; return }
  $d = if ($env:POKESHELL_HOME) { $env:POKESHELL_HOME } else { "$env:LOCALAPPDATA\pokeshell" }
  if ($args.Count -or ([IO.File]::Exists("$d\config.txt") -and [IO.File]::ReadAllText("$d\config.txt") -match '(?m)^\s*clip_alias\s*=\s*off\s*$')) { & $exe @args; return }
  pokeshell clip
}
# clip:end
& {
  $a = [Environment]::GetCommandLineArgs()
  $d = $env:POKESHELL_HOME; if (-not $d) { $d = "$env:LOCALAPPDATA\pokeshell" }
  try {
    # cheap pre-filter; the core re-checks everything (profile id, argv, markers, kill switch).
    # CARDSHELL_ROLLED: opshell's hook (the One Piece sister project) already rolled this tab: one pull per tab
    if ($env:WT_PROFILE_ID -and -not $env:POKESHELL_PULL -and -not $env:POKESHELL_ROLLED -and -not $env:CARDSHELL_ROLLED -and $a.Count -le 2) {
      $lib = "$PSScriptRoot\lib"; $root = [IO.Path]::GetDirectoryName($PSScriptRoot)
      $dll = "$d\pokeshell-core-" + [IO.File]::GetLastWriteTimeUtc("$lib\Pokeshell.cs").Ticks + "-$PSEdition.dll"   # = Get-PokeshellCorePath
      $r = $null
      if ([IO.File]::Exists($dll)) {
        [void][Reflection.Assembly]::LoadFile($dll)
        $r = [Pokeshell.Core]::Startup($ExecutionContext, $root, $d, $env:WT_PROFILE_ID, $a, $lib, -1)
      }
      $act = 'stale'; if ($r) { $act = $r.Action }
      if ($act -eq 'common' -or $act -eq 'foil-denied') {   # (Startup also hooked the prompt: this tab's first command earns the pull)
        $Host.UI.Write($r.Text)
        # a foil tier printed here (its skin isn't installed): play its effect loop over it (= Start-PokeshellCardAnim, lib\roll.ps1)
        if ([IO.File]::Exists("$root\dist\$($r.Pack)\$($r.Character)-$($r.Art).anim")) {
          $t = [Diagnostics.Stopwatch]::GetTimestamp(); $ad = "$d\pokeshell-anim-" + [IO.File]::GetLastWriteTimeUtc("$lib\Anim.cs").Ticks + "-$PSEdition.dll"
          if ([IO.File]::Exists($ad)) { [void][Reflection.Assembly]::LoadFile($ad) } else { . "$lib\anim.ps1"; Import-PokeshellAnimCore $d }
          [void][Pokeshell.Anim]::Run($root, $d, $r.Pack, $r.Character, $r.Art, $r.Shiny, $r.Text, $Host.Name, $t)
        }
      }
      elseif ($act -eq 'foil') { . "$lib\roll.ps1"; [void](Complete-PokeshellPull $r $d) }
      elseif ($act -eq 'stale') { . "$lib\roll.ps1"; [void](Invoke-PokeshellRoll -Root $root -StateDir $d -Argv $a) }   # compile / rebuild, then roll
    }
    # optional: tint the tab with Claude Code's /color (pokeshell colorwatch on); any interactive WT tab
    if ($env:WT_SESSION -and -not $global:__pokeshellColorWatch -and $a -notcontains '-NonInteractive' -and [IO.File]::Exists("$d\colorwatch.on")) {
      . "$PSScriptRoot\tab-color-watch.ps1"
    }
  } catch {
    try { [IO.File]::AppendAllText("$d\errors.log", [DateTime]::Now.ToString('s') + "`t$($_.Exception.Message)`r`n") } catch { }
  }
}
