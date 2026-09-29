<#
pokeshell card animation: after a card with an approved effect loop is printed (the pulled foil tab, or a foil
tier printed in the plain tab), dist\<pack>\<character>-<card id>[-shiny].anim plays over its art rows until a key
is pressed (config `anim=untilkey|intro|off`, POKESHELL_NO_ANIM=1). The player is lib\Anim.cs, compiled once into
the state dir as pokeshell-anim-<Anim.cs mtime>-<edition>.dll (like the roll core; `pokeshell install` builds it).
The tab paths load that DLL directly when it's there (Start-PokeshellCardAnim in lib\roll.ps1, and the $PROFILE
hook); this file is only read to compile it, and by tests.
#>

function Get-PokeshellAnimCorePath([string]$StateDir) {
  "$StateDir\pokeshell-anim-" + [IO.File]::GetLastWriteTimeUtc("$PSScriptRoot\Anim.cs").Ticks + "-$PSEdition.dll"
}

# Compile the player into the state dir unless it's there (~1 s, once). Returns its path.
function New-PokeshellAnimCore([string]$StateDir) {
  $dll = Get-PokeshellAnimCorePath $StateDir
  if (-not [IO.File]::Exists($dll)) {
    [void][IO.Directory]::CreateDirectory($StateDir)
    $tmp = "$dll.$PID.tmp"
    Add-Type -Path "$PSScriptRoot\Anim.cs" -OutputAssembly $tmp -OutputType Library
    try { [IO.File]::Move($tmp, $dll) } catch { [IO.File]::Delete($tmp) }   # another tab won the race: use theirs
  }
  $dll
}

function Import-PokeshellAnimCore([string]$StateDir) {
  if ('Pokeshell.Anim' -as [type]) { return }
  [void][Reflection.Assembly]::LoadFile((New-PokeshellAnimCore $StateDir))
}

# Play the card just printed ($Text: exactly what was written, the cursor on the line after it). Returns the
# Pokeshell.AnimResult (Status static|played, Reason, Stop, Frames, ...).
function Start-PokeshellAnim([string]$Root, [string]$StateDir, [string]$Pack, [string]$Character, [string]$Art,
                             [bool]$Shiny, [string]$Text, [long]$PrintedAt = 0) {
  if (-not $StateDir) { $StateDir = $env:POKESHELL_HOME; if (-not $StateDir) { $StateDir = "$env:LOCALAPPDATA\pokeshell" } }
  Import-PokeshellAnimCore $StateDir
  [Pokeshell.Anim]::Run($Root, $StateDir, $Pack, $Character, $Art, $Shiny, $Text, $Host.Name, $PrintedAt)
}
