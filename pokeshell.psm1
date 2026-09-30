# pokeshell module: the command, plus the `clip` shortcut. The CLI is scripts\pokeshell.ps1 (the same script a source
# checkout runs). The $PROFILE hook never imports this module: `pokeshell install` copies what new tabs need into
# %LOCALAPPDATA%\pokeshell\current and the hook runs from there (it defines the same two functions).
function pokeshell { & (Join-Path $PSScriptRoot 'scripts\pokeshell.ps1') @args }
# `clip` alone copies this tab's card (pokeshell clip); piped input or any argument goes to Windows' clip.exe unchanged.
# `pokeshell clip alias off` makes it clip.exe always. Kept in step with scripts\pokeshell-profile.ps1.
function clip {
  $exe = if ($env:POKESHELL_CLIP_EXE) { $env:POKESHELL_CLIP_EXE } else { "$env:SystemRoot\System32\clip.exe" }   # (the variable: tests only)
  if ($MyInvocation.ExpectingInput) { $input | & $exe @args; return }
  $d = if ($env:POKESHELL_HOME) { $env:POKESHELL_HOME } else { "$env:LOCALAPPDATA\pokeshell" }
  if ($args.Count -or ([IO.File]::Exists("$d\config.txt") -and [IO.File]::ReadAllText("$d\config.txt") -match '(?m)^\s*clip_alias\s*=\s*off\s*$')) { & $exe @args; return }
  pokeshell clip
}
Export-ModuleMember -Function pokeshell, clip
