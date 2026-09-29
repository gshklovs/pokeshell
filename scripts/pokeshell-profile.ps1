# pokeshell $PROFILE hook:  . "<repo>\scripts\pokeshell-profile.ps1"   (pokeshell install prints the line)
# Defines `pokeshell` and rolls the startup pull on fresh plain tabs. Kept tiny because it runs on every
# new shell: a common pull is one call into the compiled core (lib\Pokeshell.cs) and one write. Foils,
# a stale roll cache and the first compile go through lib\roll.ps1. Never throws into your profile;
# errors go to %LOCALAPPDATA%\pokeshell\errors.log.
function global:pokeshell { & "$PSScriptRoot\pokeshell.ps1" @args }
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
        $r = [Pokeshell.Core]::Startup($root, $d, $env:WT_PROFILE_ID, $a, $lib, -1)
      }
      $act = 'stale'; if ($r) { $act = $r.Action }
      if ($act -eq 'common' -or $act -eq 'foil-denied') { $Host.UI.Write($r.Text) }
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
