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
      $keyStart = $P.i
      $key = Read-JsoncString $P
      Skip-JsoncWs $P
      if ($s[$P.i] -ne ':') { throw "settings.json: expected ':' at offset $($P.i)" }
      $P.i++
      $members.Add(@{ key = $key; value = (Read-JsoncValue $P); keyStart = $keyStart })
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

# ---------------------------------------------------------------- the binder hotkey (actions + keybindings)
# Same approach as the profiles: edit only the text of the entries we own, identified by the action id, so
# Remove(Add(x)) == x. WT 1.21+ keeps actions and their keys apart ("actions": [{command, id}], "keybindings":
# [{id, keys}]); a file without "keybindings" gets the older inline form ({command, id, keys} in "actions").

$PokeshellBinderActionId = 'User.pokeshell.binder'

# a JSON value (ordered dictionaries, strings, bools) as text, nested objects indented one $Unit per level
function ConvertTo-JsoncValueText($Value, [string]$Indent, [string]$Unit, [string]$Nl) {
  if ($Value -is [bool]) { if ($Value) { return 'true' } else { return 'false' } }
  if ($Value -is [Collections.IDictionary]) {
    # get_Keys(): a "keys" entry (a keybinding's) would shadow the .Keys property
    $fields = foreach ($k in @($Value.get_Keys())) { "$Indent$Unit$(ConvertTo-JsonString $k): $(ConvertTo-JsoncValueText $Value[$k] "$Indent$Unit" $Unit $Nl)" }
    return "{$Nl$($fields -join ",$Nl")$Nl$Indent}"
  }
  ConvertTo-JsonString ([string]$Value)
}

# text with the items of the top-level array $Name that $Match accepts removed (every other byte kept)
function Remove-JsoncArrayItemsText([string]$Text, [string]$Name, [scriptblock]$Match) {
  $list = Get-JsoncMember (ConvertFrom-Jsonc $Text) $Name
  if (-not $list -or $list.type -ne 'array') { return $Text }
  $items = $list.items
  $drop = @(foreach ($it in $items) { [bool](& $Match $it) })
  if ($drop -notcontains $true) { return $Text }
  $spans = [Collections.Generic.List[int[]]]::new()
  $first = -1; for ($k = 0; $k -lt $items.Count; $k++) { if (-not $drop[$k]) { $first = $k; break } }
  if ($first -lt 0) { $spans.Add(@($items[0].start, $items[$items.Count - 1].end)) }
  else {
    if ($first -gt 0) { $spans.Add(@($items[0].start, $items[$first].start)) }
    for ($k = $first + 1; $k -lt $items.Count; $k++) { if ($drop[$k]) { $spans.Add(@($items[$k - 1].end, $items[$k].end)) } }
  }
  $sb = [Text.StringBuilder]::new($Text)
  for ($k = $spans.Count - 1; $k -ge 0; $k--) { [void]$sb.Remove($spans[$k][0], $spans[$k][1] - $spans[$k][0]) }
  $sb.ToString()
}

# text with $Items appended to the top-level array $Name (created after the last top-level member if missing)
function Add-JsoncArrayItemsText([string]$Text, [string]$Name, [object[]]$Items) {
  $root = ConvertFrom-Jsonc $Text
  if ($root.type -ne 'object') { throw "settings.json: the top level is not an object" }
  $nl = if ($Text.Contains("`r`n")) { "`r`n" } else { "`n" }
  $lineStart = { param($pos) $j = $Text.LastIndexOf("`n", [Math]::Max($pos - 1, 0)); $j + 1 }
  $unit = '    '
  $list = Get-JsoncMember $root $Name
  if (-not $list) {
    $ms = $root.members; $rootIndent = $unit
    if ($ms.Count -gt 0) {
      $ks = $ms[0].keyStart; $ls = & $lineStart $ks; $pre = $Text.Substring($ls, $ks - $ls)
      if ($pre.Length -gt 0 -and -not $pre.Trim()) { $rootIndent = $pre; $unit = $pre }
    }
    $blocks = foreach ($it in $Items) { "$rootIndent$unit" + (ConvertTo-JsoncValueText $it "$rootIndent$unit" $unit $nl) }
    $member = "$(ConvertTo-JsonString $Name): [$nl$($blocks -join ",$nl")$nl$rootIndent]"
    if ($ms.Count -gt 0) { $at = $ms[$ms.Count - 1].value.end; return $Text.Substring(0, $at) + ",$nl$rootIndent" + $member + $Text.Substring($at) }
    $at = $root.start + 1
    return $Text.Substring(0, $at) + "$nl$rootIndent$member$nl" + $Text.Substring($at)
  }
  if ($list.type -ne 'array') { throw "settings.json: '$Name' is not an array" }
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
  $joined = @(foreach ($it in $Items) { $indent + (ConvertTo-JsoncValueText $it $indent $unit $nl) }) -join ",$nl"
  if ($list.items.Count -gt 0) {
    $at = $list.items[$list.items.Count - 1].end
    return $Text.Substring(0, $at) + ",$nl" + $joined + $Text.Substring($at)
  }
  $closeIndent = $indent.Substring(0, $indent.Length - $unit.Length)
  $Text.Substring(0, $list.start + 1) + $nl + $joined + $nl + $closeIndent + $Text.Substring($list.end - 1)
}

# text without the top-level member $Name (the inverse of Add-JsoncArrayItemsText creating it)
function Remove-JsoncMemberText([string]$Text, [string]$Name) {
  $ms = (ConvertFrom-Jsonc $Text).members
  for ($k = 0; $k -lt $ms.Count; $k++) {
    if ($ms[$k].key -ne $Name) { continue }
    if ($k -gt 0) { $a = $ms[$k - 1].value.end; $b = $ms[$k].value.end }
    elseif ($ms.Count -gt 1) { $a = $ms[0].keyStart; $b = $ms[1].keyStart }
    else { $a = $ms[0].keyStart; $b = $ms[0].value.end }
    return $Text.Remove($a, $b - $a)
  }
  $Text
}

function Test-PokeshellHotkeyNode($Item) {
  if ($Item.type -ne 'object') { return $false }
  $id = Get-JsoncMember $Item 'id'
  [bool]($id -and $id.type -eq 'string' -and $id.value -eq $PokeshellBinderActionId)
}

# settings text without the binder hotkey; -DropEmptyActions: also the "actions" array if the install created it
function Remove-PokeshellHotkeyText([string]$Text, [switch]$DropEmptyActions) {
  $t = Remove-JsoncArrayItemsText $Text 'keybindings' { param($i) Test-PokeshellHotkeyNode $i }
  $t = Remove-JsoncArrayItemsText $t 'actions' { param($i) Test-PokeshellHotkeyNode $i }
  if ($DropEmptyActions -and -not $t.Equals($Text)) {
    $a = Get-JsoncMember (ConvertFrom-Jsonc $t) 'actions'
    if ($a -and $a.type -eq 'array' -and $a.items.Count -eq 0) { $t = Remove-JsoncMemberText $t 'actions' }
  }
  $t
}

function ConvertTo-PokeshellKeys([string]$Keys) { ((($Keys -replace '\s', '').ToLower() -split '\+') | Sort-Object) -join '+' }

<#
Settings text with the binder hotkey: an action that splits the pane vertically (wt -w 0 sp -V <binder.exe>) bound to
$Keys. Throws if another action already uses those keys. Returns @{ text; created } (created: "actions" was added).
#>
function Add-PokeshellHotkeyText([string]$Text, [string]$CommandLine, [string]$Keys = 'ctrl+shift+b') {
  $Text = Remove-PokeshellHotkeyText $Text
  $root = ConvertFrom-Jsonc $Text
  $want = ConvertTo-PokeshellKeys $Keys
  foreach ($arr in 'keybindings', 'actions') {
    $list = Get-JsoncMember $root $arr
    if (-not $list -or $list.type -ne 'array') { continue }
    foreach ($it in $list.items) {
      $k = Get-JsoncMember $it 'keys'
      $ks = if ($k -and $k.type -eq 'string') { @($k.value) } elseif ($k -and $k.type -eq 'array') { @($k.items | Where-Object type -eq 'string' | ForEach-Object value) } else { @() }
      foreach ($x in $ks) {
        if ((ConvertTo-PokeshellKeys $x) -eq $want) {
          $id = Get-JsoncMember $it 'id'
          throw "$Keys is already bound in settings.json$(if ($id) { " (to $($id.value))" }); pick other keys with -Keys"
        }
      }
    }
  }
  $action = [ordered]@{ command = [ordered]@{ action = 'splitPane'; split = 'vertical'; commandline = $CommandLine; tabTitle = 'binder' }; id = $PokeshellBinderActionId }
  $created = -not (Get-JsoncMember $root 'actions')
  $kb = Get-JsoncMember $root 'keybindings'
  if ($kb -and $kb.type -eq 'array') {
    $Text = Add-JsoncArrayItemsText $Text 'actions' @($action)
    $Text = Add-JsoncArrayItemsText $Text 'keybindings' @([ordered]@{ keys = $Keys; id = $PokeshellBinderActionId })
  } else {
    $action['keys'] = $Keys
    $Text = Add-JsoncArrayItemsText $Text 'actions' @($action)
  }
  @{ text = $Text; created = $created }
}
# ---------------------------------------------------------------- "safeUriSchemes": ["pokeshell"]
# Windows Terminal (1.24: TerminalPage::_IsUriConsideredSomewhatSafe) opens a Ctrl+clicked link of any other scheme
# than http(s)/file only after an "This link may lead to an unsafe location" dialog, unless the scheme is listed in
# the top-level "safeUriSchemes". The install adds "pokeshell" there, so the card's link opens straight away.

function Test-PokeshellSchemeNode($Item) { $Item.type -eq 'string' -and $Item.value -ieq 'pokeshell' }

# @{ text; created ("safeUriSchemes" was added); ours (we added the entry: false when it was already there) }
function Add-PokeshellSafeSchemeText([string]$Text) {
  $root = ConvertFrom-Jsonc $Text
  $list = Get-JsoncMember $root 'safeUriSchemes'
  if ($list -and $list.type -ne 'array') { throw "settings.json: 'safeUriSchemes' is not an array" }
  if ($list -and @($list.items | Where-Object { Test-PokeshellSchemeNode $_ }).Count) { return @{ text = $Text; created = $false; ours = $false } }
  @{ text = (Add-JsoncArrayItemsText $Text 'safeUriSchemes' @('pokeshell')); created = -not $list; ours = $true }
}

# settings text without our "pokeshell" entry; -DropEmpty: also the member, if the install created it
function Remove-PokeshellSafeSchemeText([string]$Text, [switch]$DropEmpty) {
  $t = Remove-JsoncArrayItemsText $Text 'safeUriSchemes' { param($i) Test-PokeshellSchemeNode $i }
  if ($DropEmpty -and -not $t.Equals($Text)) {
    $a = Get-JsoncMember (ConvertFrom-Jsonc $t) 'safeUriSchemes'
    if ($a -and $a.type -eq 'array' -and $a.items.Count -eq 0) { $t = Remove-JsoncMemberText $t 'safeUriSchemes' }
  }
  $t
}
