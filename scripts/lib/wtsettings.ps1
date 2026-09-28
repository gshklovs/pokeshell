<#
Edit Windows Terminal's settings.json without a JSON round-trip.

Windows PowerShell 5.1's ConvertFrom-Json/ConvertTo-Json would drop comments, re-escape strings and
reformat the whole file, so instead this parses the file (JSON with comments and trailing commas) into
spans and edits only the text of profiles.list: it removes the elements whose name starts with
"pokeshell: " and appends freshly generated ones. Every other byte stays as it was, and
Remove(Add(x)) == Remove(x) exactly, which the installer checks before it writes anything.
#>

function New-JsoncParser([string]$Text) { @{ s = $Text; i = 0; n = $Text.Length } }

function Skip-JsoncWs($P) {
  $s = $P.s
  while ($P.i -lt $P.n) {
    $c = $s[$P.i]
    if ($c -eq ' ' -or $c -eq "`t" -or $c -eq "`r" -or $c -eq "`n" -or $c -eq [char]0xFEFF) { $P.i++ }
    elseif ($c -eq '/' -and $P.i + 1 -lt $P.n -and $s[$P.i + 1] -eq '/') {
      $j = $s.IndexOf("`n", $P.i); $P.i = if ($j -lt 0) { $P.n } else { $j + 1 }
    }
    elseif ($c -eq '/' -and $P.i + 1 -lt $P.n -and $s[$P.i + 1] -eq '*') {
      $j = $s.IndexOf('*/', $P.i + 2); if ($j -lt 0) { throw "settings.json: unterminated /* comment" }; $P.i = $j + 2
    }
    else { break }
  }
}

function Read-JsoncString($P) {
  $s = $P.s; $P.i++   # opening quote
  $sb = [Text.StringBuilder]::new()
  while ($true) {
    if ($P.i -ge $P.n) { throw "settings.json: unterminated string" }
    $c = $s[$P.i]
    if ($c -eq '"') { $P.i++; break }
    if ($c -eq '\') {
      $e = $s[$P.i + 1]
      switch -CaseSensitive ($e) {
        'n' { [void]$sb.Append("`n") } 't' { [void]$sb.Append("`t") } 'r' { [void]$sb.Append("`r") }
        'b' { [void]$sb.Append([char]8) } 'f' { [void]$sb.Append([char]12) }
        'u' { [void]$sb.Append([char][Convert]::ToInt32($s.Substring($P.i + 2, 4), 16)); $P.i += 4 }
        default { [void]$sb.Append($e) }
      }
      $P.i += 2; continue
    }
    [void]$sb.Append($c); $P.i++
  }
  $sb.ToString()
}

# A value node: @{ type; start; end; value (strings/literals); members (objects: key/value pairs); items (arrays) }
function Read-JsoncValue($P) {
  Skip-JsoncWs $P
  if ($P.i -ge $P.n) { throw "settings.json: unexpected end of file" }
  $s = $P.s; $start = $P.i; $c = $s[$P.i]
  if ($c -eq '{') {
    $P.i++; $members = [Collections.Generic.List[object]]::new()
    while ($true) {
      Skip-JsoncWs $P
      if ($s[$P.i] -eq '}') { $P.i++; break }
      if ($s[$P.i] -ne '"') { throw "settings.json: expected a key at offset $($P.i)" }
      $key = Read-JsoncString $P
      Skip-JsoncWs $P
      if ($s[$P.i] -ne ':') { throw "settings.json: expected ':' at offset $($P.i)" }
      $P.i++
      $members.Add(@{ key = $key; value = (Read-JsoncValue $P) })
      Skip-JsoncWs $P
      if ($s[$P.i] -eq ',') { $P.i++ } elseif ($s[$P.i] -ne '}') { throw "settings.json: expected ',' or '}' at offset $($P.i)" }
    }
    return @{ type = 'object'; start = $start; end = $P.i; members = $members }
  }
  if ($c -eq '[') {
    $P.i++; $items = [Collections.Generic.List[object]]::new()
    while ($true) {
      Skip-JsoncWs $P
      if ($s[$P.i] -eq ']') { $P.i++; break }
      $items.Add((Read-JsoncValue $P))
      Skip-JsoncWs $P
      if ($s[$P.i] -eq ',') { $P.i++ } elseif ($s[$P.i] -ne ']') { throw "settings.json: expected ',' or ']' at offset $($P.i)" }
    }
    return @{ type = 'array'; start = $start; end = $P.i; items = $items }
  }
  if ($c -eq '"') { $v = Read-JsoncString $P; return @{ type = 'string'; start = $start; end = $P.i; value = $v } }
  $m = [regex]::Match($s.Substring($P.i, [Math]::Min(64, $P.n - $P.i)), '^(true|false|null|-?\d+(\.\d+)?([eE][+-]?\d+)?)')
  if (-not $m.Success) { throw "settings.json: unexpected '$c' at offset $($P.i)" }
  $P.i += $m.Length
  @{ type = 'literal'; start = $start; end = $P.i; value = $m.Value }
}

function ConvertFrom-Jsonc([string]$Text) {
  $P = New-JsoncParser $Text
  $root = Read-JsoncValue $P
  Skip-JsoncWs $P
  if ($P.i -lt $P.n) { throw "settings.json: trailing content at offset $($P.i)" }
  $root
}

function Get-JsoncMember($Node, [string]$Key) {
  if ($Node.type -ne 'object') { return $null }
  foreach ($m in $Node.members) { if ($m.key -eq $Key) { return $m.value } }
  $null
}

# The profiles array: profiles.list, or the older bare "profiles": [ ... ] form
function Get-WtProfileList($Root) {
  $profiles = Get-JsoncMember $Root 'profiles'
  if (-not $profiles) { throw "settings.json has no 'profiles'" }
  if ($profiles.type -eq 'array') { return $profiles }
  $list = Get-JsoncMember $profiles 'list'
  if (-not $list -or $list.type -ne 'array') { throw "settings.json has no 'profiles.list' array" }
  $list
}

function Test-PokeshellProfileNode($Item, [string[]]$Guids) {
  if ($Item.type -ne 'object') { return $false }
  $name = Get-JsoncMember $Item 'name'
  if ($name -and $name.type -eq 'string' -and $name.value.StartsWith('pokeshell: ')) { return $true }
  $guid = Get-JsoncMember $Item 'guid'
  ($guid -and $guid.type -eq 'string' -and $Guids -and ($Guids -contains $guid.value))
}

# settings text with every pokeshell profile removed (and nothing else touched)
function Remove-PokeshellProfilesText([string]$Text, [string[]]$Guids = @()) {
  $list = Get-WtProfileList (ConvertFrom-Jsonc $Text)
  $items = $list.items
  $drop = @(for ($k = 0; $k -lt $items.Count; $k++) { Test-PokeshellProfileNode $items[$k] $Guids })
  if ($drop -notcontains $true) { return $Text }
  $spans = [Collections.Generic.List[int[]]]::new()     # [start, end) to delete
  $first = -1; for ($k = 0; $k -lt $items.Count; $k++) { if (-not $drop[$k]) { $first = $k; break } }
  if ($first -lt 0) { $spans.Add(@($items[0].start, $items[$items.Count - 1].end)) }   # everything goes: keep the brackets
  else {
    if ($first -gt 0) { $spans.Add(@($items[0].start, $items[$first].start)) }       # leading run: item(s), comma, whitespace
    for ($k = $first + 1; $k -lt $items.Count; $k++) {
      if ($drop[$k]) { $spans.Add(@($items[$k - 1].end, $items[$k].end)) }            # ", <ws> {item}" after the previous one
    }
  }
  $sb = [Text.StringBuilder]::new($Text)
  # spans were added in ascending order and don't overlap: delete from the end so offsets stay valid
  for ($k = $spans.Count - 1; $k -ge 0; $k--) { [void]$sb.Remove($spans[$k][0], $spans[$k][1] - $spans[$k][0]) }
  $sb.ToString()
}

function ConvertTo-JsonString([string]$S) {
  $sb = [Text.StringBuilder]::new('"')
  foreach ($c in $S.ToCharArray()) {
    switch ($c) {
      '"' { [void]$sb.Append('\"') } '\' { [void]$sb.Append('\\') }
      default { if ([int]$c -lt 0x20) { [void]$sb.Append(('\u{0:x4}' -f [int]$c)) } else { [void]$sb.Append($c) } }
    }
  }
  [void]$sb.Append('"'); $sb.ToString()
}

<#
settings text with the given profiles appended to profiles.list (after removing old pokeshell ones).
$Profiles: ordered dictionaries of string/bool values. Indentation and line endings follow the file.
#>
function Add-PokeshellProfilesText([string]$Text, [object[]]$Profiles, [string[]]$Guids = @()) {
  $Text = Remove-PokeshellProfilesText $Text $Guids
  if (-not $Profiles) { return $Text }
  $list = Get-WtProfileList (ConvertFrom-Jsonc $Text)
  $nl = if ($Text.Contains("`r`n")) { "`r`n" } else { "`n" }
  $lineStart = { param($pos) $j = $Text.LastIndexOf("`n", [Math]::Max($pos - 1, 0)); $j + 1 }
  $unit = '    '
  if ($list.items.Count -gt 0) {
    $last = $list.items[$list.items.Count - 1]
    $indent = $Text.Substring((& $lineStart $last.start), $last.start - (& $lineStart $last.start))
    if ($indent.Trim()) { $indent = '' }
    $m = [regex]::Match($Text.Substring($last.start, $last.end - $last.start), '\n([ \t]+)"')
    if ($m.Success -and $m.Groups[1].Value.Length -gt $indent.Length) { $unit = $m.Groups[1].Value.Substring($indent.Length) }
  } else {
    $ls = & $lineStart $list.start
    $indent = [regex]::Match($Text.Substring($ls, $list.start - $ls), '^[ \t]*').Value + $unit
  }
  $blocks = foreach ($p in $Profiles) {
    $fields = foreach ($k in $p.Keys) {
      $v = $p[$k]
      $jv = if ($v -is [bool]) { if ($v) { 'true' } else { 'false' } } else { ConvertTo-JsonString ([string]$v) }
      "$indent$unit$(ConvertTo-JsonString $k): $jv"
    }
    "$indent{$nl$($fields -join ",$nl")$nl$indent}"
  }
  $joined = $blocks -join ",$nl"
  if ($list.items.Count -gt 0) {
    $at = $list.items[$list.items.Count - 1].end
    return $Text.Substring(0, $at) + ",$nl" + $joined + $Text.Substring($at)
  }
  $closeIndent = $indent.Substring(0, $indent.Length - $unit.Length)
  $Text.Substring(0, $list.start + 1) + $nl + $joined + $nl + $closeIndent + $Text.Substring($list.end - 1)
}

function Read-WtSettingsFile([string]$Path) {
  $bytes = [IO.File]::ReadAllBytes($Path)
  $bom = $bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF
  $text = [Text.UTF8Encoding]::new($false, $true).GetString($bytes, $(if ($bom) { 3 } else { 0 }), $bytes.Length - $(if ($bom) { 3 } else { 0 }))
  @{ text = $text; bom = $bom }
}

# write via a temp file + replace, so WT (which watches the file) never sees half a file
function Write-WtSettingsFile([string]$Path, [string]$Text, [bool]$Bom) {
  $tmp = "$Path.pokeshell.tmp"
  [IO.File]::WriteAllText($tmp, $Text, [Text.UTF8Encoding]::new($Bom))
  [IO.File]::Replace($tmp, $Path, [NullString]::Value)
}
