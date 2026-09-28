<#
tab-color-watch: tint this Windows Terminal tab with the /color of the Claude Code session running in it.
Optional (pokeshell colorwatch on); started by pokeshell-profile.ps1 in a background runspace of this
PowerShell, so it can write to the tab's console without touching the prompt.
  claude.exe child of this shell -> ~/.claude/sessions/<pid>.json (sessionId) -> transcript -> last "agentColor"
  WT draws the tab from palette index 264: OSC 4;264;rgb:.. sets it, OSC 104;264 resets it.
#>
$rs = [runspacefactory]::CreateRunspace()
$rs.Open()
$ps = [powershell]::Create()
$ps.Runspace = $rs
[void]$ps.AddScript({
  param($hostPid, $claudeDir)
  $rgb = @{
    red = 'cc/33/33'; orange = 'e0/7a/1f'; yellow = 'c9/a2/27'; green = '2e/9e/4f'
    cyan = '1f/a8/b8'; blue = '2f/6f/d6'; purple = '8a/4f/d6'; pink = 'd6/4f/9e'
  }
  $esc = [char]27
  $shown = ''          # color currently applied to the tab ('' = default)
  $sid = ''; $path = ''; $offset = 0L; $color = ''

  while ($true) {
    try {
      $kid = Get-CimInstance Win32_Process -Filter "ParentProcessId=$hostPid AND Name='claude.exe'" | Select-Object -First 1
      $want = ''
      if ($kid) {
        $sf = Join-Path $claudeDir "sessions\$($kid.ProcessId).json"
        $cur = if (Test-Path $sf) { (Get-Content $sf -Raw | ConvertFrom-Json).sessionId } else { '' }
        if ($cur -and $cur -ne $sid) {   # new or resumed session: rescan its transcript from the start
          $sid = $cur; $offset = 0L; $color = ''
          $path = Get-ChildItem (Join-Path $claudeDir 'projects') -Directory |
            ForEach-Object { Join-Path $_.FullName "$sid.jsonl" } | Where-Object { Test-Path $_ } | Select-Object -First 1
        }
        if ($path -and (Test-Path $path)) {
          $len = (Get-Item $path).Length
          if ($len -lt $offset) { $offset = 0L }
          if ($len -gt $offset) {        # only read what was appended since the last poll
            $fs = [IO.File]::Open($path, 'Open', 'Read', 'ReadWrite')
            try {
              [void]$fs.Seek($offset, 'Begin')
              $text = (New-Object IO.StreamReader($fs)).ReadToEnd()
              $offset = $len
            } finally { $fs.Close() }
            $m = [regex]::Matches($text, '"agentColor":"([a-z]*)"')
            if ($m.Count) { $color = $m[$m.Count - 1].Groups[1].Value }
          }
        }
        $want = $color
      }
      if (-not $rgb.ContainsKey($want)) { $want = '' }
      if ($want -ne $shown) {
        if ($want) { [Console]::Out.Write("$esc]4;264;rgb:$($rgb[$want])$esc\") }
        else       { [Console]::Out.Write("$esc]104;264$esc\") }
        [Console]::Out.Flush()
        $shown = $want
      }
    } catch { }
    Start-Sleep -Seconds 2
  }
}).AddArgument($PID).AddArgument((Join-Path $env:USERPROFILE '.claude'))
[void]$ps.BeginInvoke()
$global:__pokeshellColorWatch = $ps   # keep a reference so it lives as long as the shell
