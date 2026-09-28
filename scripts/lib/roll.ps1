<#
pokeshell roll helpers. The decisions (guards, dice, spawn gate) live in Pokeshell.cs, compiled once
into %LOCALAPPDATA%\pokeshell\pokeshell-core-*.dll. pokeshell-profile.ps1 calls the DLL directly for
the common case and only loads this file for foils, a stale roll cache, or the first compile.
#>

function Get-PokeshellStateDir {
  if ($env:POKESHELL_HOME) { return $env:POKESHELL_HOME }
  $env:LOCALAPPDATA + '\pokeshell'
}

# The compiled core's path. The name carries Pokeshell.cs's mtime and the PowerShell edition, so an
# update gets a new file (open tabs keep the old one loaded, which is fine). Mirrored in pokeshell-profile.ps1.
function Get-PokeshellCorePath([string]$StateDir) {
  "$StateDir\pokeshell-core-" + [IO.File]::GetLastWriteTimeUtc("$PSScriptRoot\Pokeshell.cs").Ticks + "-$PSEdition.dll"
}

# Compile this version of the core into the state dir unless it's already there (~1 s, once). Returns its path.
function New-PokeshellCore([string]$StateDir) {
  if (-not $StateDir) { $StateDir = Get-PokeshellStateDir }
  $dll = Get-PokeshellCorePath $StateDir
  if (-not [IO.File]::Exists($dll)) {
    [void][IO.Directory]::CreateDirectory($StateDir)
    $tmp = "$dll.$PID.tmp"
    Add-Type -Path "$PSScriptRoot\Pokeshell.cs" -OutputAssembly $tmp -OutputType Library
    try { [IO.File]::Move($tmp, $dll) } catch { [IO.File]::Delete($tmp) }   # another tab won the race: use theirs
  }
  $dll
}

# Load the compiled core (compiling it first if needed)
function Import-PokeshellCore([string]$StateDir) {
  if ('Pokeshell.Core' -as [type]) { return }
  [void][Reflection.Assembly]::LoadFile((New-PokeshellCore $StateDir))
}

# Print art + banner (the pulled foil tab, `pokeshell show`)
function Show-PokeshellPull([string]$Root, [string]$Pack, [string]$Character, [string]$Name, [string]$Art,
                            [string]$Label, [int]$Tier, [switch]$Shiny) {
  Import-PokeshellCore
  $Host.UI.Write([Pokeshell.Core]::PullText($Root, $Pack, $Character, $Name, $Art, $Label, $Tier, [bool]$Shiny))
}

<#
Where a foil can replace this shell, via UI Automation (foil path only; ~50-300 ms):
  'nt'  this is the only pane of the selected tab in the foreground Windows Terminal window
  'sp'  this is one pane of a split tab there: the skinned pull opens as a split pane instead
  anything else = the reason it can't be done safely (the pull then stays a common, here):
  WT's `-w 0` means "most recently used window", so we only replace ourselves when our own window is
  the foreground one, and we find our own pane by briefly setting a unique title and looking for it.
#>
function Get-PokeshellPlacement([int]$TimeoutMs = 600) {
  try { Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes } catch { return 'no-uia' }
  $fg = [Pokeshell.Core]::ForegroundWindow()
  if ($fg -eq [IntPtr]::Zero) { return 'no-foreground' }
  $AE = [Windows.Automation.AutomationElement]
  try { $win = $AE::FromHandle($fg) } catch { return 'no-foreground' }
  if ($win.Current.ClassName -ne 'CASCADIA_HOSTING_WINDOW_CLASS') { return 'not-foreground' }
  $isTerm = [Windows.Automation.PropertyCondition]::new($AE::ClassNameProperty, 'TermControl')
  $isTab = [Windows.Automation.PropertyCondition]::new($AE::ControlTypeProperty, [Windows.Automation.ControlType]::TabItem)
  $raw = $Host.UI.RawUI; $old = $raw.WindowTitle
  $tag = 'pokeshell-' + [Guid]::NewGuid().ToString('N').Substring(0, 12)
  $raw.WindowTitle = $tag
  $sw = [Diagnostics.Stopwatch]::StartNew()
  try {
    while ($sw.ElapsedMilliseconds -lt $TimeoutMs) {
      # only the selected tab's panes are in the tree; its tab item shows the focused pane's title
      $terms = $win.FindAll([Windows.Automation.TreeScope]::Descendants, $isTerm)
      $mine = $false
      foreach ($t in $terms) { if ($t.Current.Name -eq $tag) { $mine = $true } }
      if (-not $mine) {
        foreach ($t in $win.FindAll([Windows.Automation.TreeScope]::Descendants, $isTab)) {
          if ($t.Current.Name -eq $tag) {
            try { $mine = $t.GetCurrentPattern([Windows.Automation.SelectionItemPattern]::Pattern).Current.IsSelected } catch { }
          }
        }
      }
      if ($mine) { if ($terms.Count -gt 1) { return 'sp' } else { return 'nt' } }
      [Threading.Thread]::Sleep(40)
    }
    'not-found'
  } finally { $raw.WindowTitle = $old }
}

<#
Finish a roll result: print a common, or for a foil open the skinned tab (same folder), which prints
the pull, and close this one (exit code 0, so WT closes the tab). -DryRun (or POKESHELL_DRYRUN=1)
records the wt.exe call in dryrun-spawns.log instead of making it and doesn't exit.
#>
function Complete-PokeshellPull($R, [string]$StateDir, [switch]$DryRun, [switch]$Quiet) {
  if ($env:POKESHELL_DRYRUN -eq '1') { $DryRun = $true }
  if ($R.Action -ne 'foil') {
    if ($R.Text -and -not $Quiet) { $Host.UI.Write($R.Text) }
    return $R
  }
  if (-not $DryRun -or $env:POKESHELL_PLACEMENT -eq '1') {
    $where = Get-PokeshellPlacement
    if ($where -ne 'nt' -and $where -ne 'sp') {
      # can't be sure where the new tab would land: keep this one, show the pull here as a common
      [Pokeshell.Core]::Log($StateDir, 'pulls.log', $R.FallbackLogLine + "foil-not-placed:$where")
      $R.Action = 'foil-denied'; $R.Reason = "placement:$where"
      if (-not $Quiet) { $Host.UI.Write($R.FallbackText) }
      return $R
    }
    $R.WtArgs[2] = $where
  }
  if ($DryRun) {
    [Pokeshell.Core]::Log($StateDir, 'pulls.log', $R.LogLine + 'dryrun')
    [Pokeshell.Core]::Log($StateDir, 'dryrun-spawns.log', "$($R.Guid)`t$($R.WtArgs -join ' ')")
    return $R
  }
  $ok = $false
  try { & wt.exe $R.WtArgs; $ok = $? } catch { }
  if (-not $ok) {
    # couldn't open the tab: show the pull here (as a common) and never exit
    [Pokeshell.Core]::Log($StateDir, 'pulls.log', $R.FallbackLogLine + 'foil-spawn-failed')
    $R.Action = 'foil-denied'
    if (-not $Quiet) { $Host.UI.Write($R.FallbackText) }
    return $R
  }
  [Pokeshell.Core]::Log($StateDir, 'pulls.log', $R.LogLine)
  [Environment]::Exit(0)
}

<#
The startup pull, end to end. Returns a Pokeshell.Pull (Action = skip | common | foil | foil-denied,
Reason, Pack, Character, Skin, WtArgs, ...). Defaults are the real tab's identity; tests inject
-ProfileId / -Argv / -Now / -Seed / -FoilChance.
#>
function Invoke-PokeshellRoll([string]$Root, [string]$StateDir, [string]$ProfileId, [string[]]$Argv,
                              [long]$Now, [int]$Seed, [double]$FoilChance = -1, [switch]$DryRun, [switch]$Quiet) {
  if (-not $StateDir) { $StateDir = Get-PokeshellStateDir }
  if (-not $PSBoundParameters.ContainsKey('ProfileId')) { $ProfileId = $env:WT_PROFILE_ID }
  if (-not $Argv) { $Argv = [Environment]::GetCommandLineArgs() }
  if (-not $Now) { $Now = [DateTime]::UtcNow.Ticks }
  if (-not $PSBoundParameters.ContainsKey('Seed')) { $Seed = [Guid]::NewGuid().GetHashCode() }
  Import-PokeshellCore $StateDir
  $r = [Pokeshell.Core]::Roll($Root, $StateDir, $ProfileId, $Argv, $Now, $Seed, $FoilChance, $null, $null, $PSScriptRoot)
  if ($r.Action -eq 'stale') {
    # the roll table's inputs changed (pack, art, install): rebuild it (slow, once) and roll again
    . "$PSScriptRoot\common.ps1"
    Update-PokeshellRollCache -Root $Root -StateDir $StateDir
    $r = [Pokeshell.Core]::Roll($Root, $StateDir, $ProfileId, $Argv, $Now, $Seed, $FoilChance, $null, $null, $PSScriptRoot)
    if ($r.Action -eq 'stale') { $r.Action = 'skip'; $r.Reason = 'cache-unreadable'; return $r }
  }
  Complete-PokeshellPull $r $StateDir -DryRun:$DryRun -Quiet:$Quiet
}
