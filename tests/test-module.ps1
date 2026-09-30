<#
The PowerShell Gallery module, end to end, without the gallery: stage it with tools\publish.ps1 into a temp
Modules folder, Import-Module it in child processes whose LOCALAPPDATA is a temp folder, install into a COPY of
settings.json, then simulate Update-Module (stage a newer version next to it, `pokeshell install` again through the
$PROFILE hook's command, delete the old version folder) and check that the shader profiles and the hook still resolve.
Never touches the real settings.json, $PROFILE, %LOCALAPPDATA%\pokeshell, or the real module folders.
  powershell -NoProfile -File tests\test-module.ps1
#>
. (Join-Path $PSScriptRoot '_setup.ps1')
. (Join-Path $RepoRoot 'scripts\lib\wtsettings.ps1')
$work = Join-Path ([IO.Path]::GetTempPath()) "pokeshell-test-module-$PID"
Remove-Item $work -Recurse -Force -ErrorAction SilentlyContinue
$mods = Join-Path $work 'Modules'; $lad = Join-Path $work 'LocalAppData'
$state = Join-Path $lad 'pokeshell'; $cur = Join-Path $state 'current'
[void][IO.Directory]::CreateDirectory($mods); [void][IO.Directory]::CreateDirectory($lad)

# guard rails: fingerprints of the real things this test must not touch
$real = $RealWtSettings   # (Get-PokeshellWtSettingsPath is off in tests: _setup.ps1)
$realHash = if ($real) { (Get-FileHash $real).Hash }
$realState = Join-Path $env:LOCALAPPDATA 'pokeshell'
function Get-Fingerprint([string]$Dir) {
  if (-not (Test-Path $Dir)) { return '' }
  # (files your open tabs legitimately write while the test runs are left out)
  (Get-ChildItem $Dir -Recurse -Force | Where-Object { $_.Name -notin 'pulls.log', 'roll.tsv', 'spawn-gate.txt', 'errors.log', 'dryrun-spawns.log' -and $_.Name -notlike 'roll.tsv.*.tmp' } | ForEach-Object { "$($_.FullName)|$($_.Length)|$($_.LastWriteTimeUtc.Ticks)" }) -join "`n"
}
$realStatePrint = Get-Fingerprint $realState
$realModulesPrint = @($RealPokeshellModuleDirs | ForEach-Object { Get-Fingerprint $_ }) -join "`n"   # (_setup.ps1)

$settings = Join-Path $work 'settings.json'
$utf8 = [Text.UTF8Encoding]::new($false)
[IO.File]::WriteAllText($settings, (@'
// test copy
{
    "defaultProfile": "{61c54bbd-c2c6-5271-96e7-009a87ff44bf}",
    "profiles": {
        "list": [
            { "guid": "{61c54bbd-c2c6-5271-96e7-009a87ff44bf}", "name": "Windows PowerShell", "hidden": false }
        ]
    }
}
'@).Replace("`r`n", "`n").Replace("`n", "`r`n"), $utf8)
$origSettings = [IO.File]::ReadAllBytes($settings)

$publish = Join-Path $RepoRoot 'tools\publish.ps1'
function Stage([string]$Ver) {
  $d = Join-Path $mods "pokeshell\$Ver"
  $null = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $publish -StageOnly -OutDir $d -Version $Ver 2>&1
  $d
}
# The published module ships no Pokemon card art (it is built locally and never committed), so the tests pull from
# a tiny real-card fixture pack added to each staged copy, as a pack a user dropped in would be.
function Add-FixturePack([string]$ModDir) {
  foreach ($x in 'packs\fixture', 'dist\fixture') { [void][IO.Directory]::CreateDirectory((Join-Path $ModDir $x)) }
  [IO.File]::WriteAllText((Join-Path $ModDir 'packs\fixture\pack.json'), '{ "id": "fixture", "name": "Fixture", "shiny_chance": 0,
  "tiers": [ { "id": "common", "label": "common", "weight": 1, "skins": {}, "frame": "plain" } ],
  "cards": { "fx-1": { "character": "bob", "tier": "common", "name": "Bob", "number": "1/1" } } }', $utf8)
  [IO.File]::WriteAllText((Join-Path $ModDir 'dist\fixture\bob-fx-1.ans'), "$([char]27)[0;38;2;9;9;9m$([char]0x2580)$([char]27)[0m`n", $utf8)
}
[void][IO.Directory]::CreateDirectory($state)
[IO.File]::WriteAllLines((Join-Path $state 'config.txt'), [string[]]@('pack=fixture'))

# a child process as a user would have it: LOCALAPPDATA -> temp, the staged Modules folder first on PSModulePath
$runner = Join-Path $work 'runner.ps1'
@'
param([string]$Mode, [string]$Lad, [string]$Mods, [string]$Cmd)
$env:LOCALAPPDATA = $Lad
Remove-Item Env:POKESHELL_HOME -ErrorAction SilentlyContinue
# (powershell.exe puts the user's own Modules folder back on PSModulePath at startup: a real pokeshell module there stays out)
$env:PSModulePath = (@($Mods) + @($env:PSModulePath -split ';' | Where-Object { $_ -and -not [IO.Directory]::Exists((Join-Path $_ 'pokeshell')) })) -join ';'
$cliArgs = @($Cmd -split '\|' | Where-Object { $_ })
if ($Mode -eq 'module') {
  # a new shell after Install-Module: the command comes from the newest module version
  Import-Module pokeshell -ErrorAction Stop
  "exports=$((Get-Command -Module pokeshell | ForEach-Object Name) -join ',')"
  pokeshell @cliArgs
} else {
  # a tab with the printed $PROFILE line: the hook's `pokeshell` function (-> current\scripts\pokeshell.ps1 shim)
  . "$Lad\pokeshell\current\scripts\pokeshell-profile.ps1"
  "command=$((Get-Command pokeshell).CommandType)"
  pokeshell @cliArgs
}
'@ | Set-Content $runner
function Run([string]$Mode, [string[]]$CliArgs) {
  (& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $runner $Mode $lad $mods ($CliArgs -join '|') 2>&1 | Out-String -Width 400)
}

# the real hook's text as a fresh plain tab runs it (no argv), from <state>\current, forced to a common pull
function Invoke-HookRoll {
  $probe = Join-Path $work 'hookprobe.ps1'
  $t = [IO.File]::ReadAllText((Join-Path $cur 'scripts\pokeshell-profile.ps1'))
  $t = $t.Replace('$PSScriptRoot', '$__hookDir').Replace('[Environment]::GetCommandLineArgs()', "@('powershell.exe')").Replace('$lib, -1)', '$lib, 0)').Replace('-Argv $a)', '-Argv $a -FoilChance 0)')
  $t = "`$env:LOCALAPPDATA = '$lad'; `$env:WT_PROFILE_ID = '$PlainGuid'; `$env:POKESHELL_DRYRUN = '1'`r`n`$__hookDir = '$cur\scripts'`r`n" + $t +
       "`r`nif (`$env:POKESHELL_ROLLED) { 'ROLLED' }"
  [IO.File]::WriteAllText($probe, $t)
  $e = [char]27
  (& powershell.exe -NoProfile -File $probe 2>&1 | Out-String -Width 400) -replace "$e\[[0-9;]*m", ''
}
function Get-ShaderPaths {
  $items = @((Get-WtProfileList (ConvertFrom-Jsonc (Read-WtSettingsFile $settings).text)).items | Where-Object { Test-PokeshellProfileNode $_ @() })
  @($items | ForEach-Object { (Get-JsoncMember $_ 'experimental.pixelShaderPath').value })
}

Write-Host "1. stage the module (tools\publish.ps1 -StageOnly)" -ForegroundColor Cyan
$v1 = Stage '0.1.0'
$m = Test-ModuleManifest (Join-Path $v1 'pokeshell.psd1')
Assert ("$($m.Version)" -eq '0.1.0' -and @($m.ExportedFunctions.Keys) -join ',' -eq 'pokeshell') "manifest valid: version $($m.Version), exports $(@($m.ExportedFunctions.Keys) -join ',')"
Assert (@($m.ExportedCmdlets.Keys).Count -eq 0 -and @($m.ExportedAliases.Keys).Count -eq 0 -and @($m.ExportedVariables.Keys).Count -eq 0) "nothing else exported"
$rel = @(Get-ChildItem $v1 -Recurse -File | ForEach-Object { $_.FullName.Substring($v1.Length + 1) })
Assert (-not @($rel | Where-Object { $_ -match '^(tests|tools|\.venv|previews|\.git)\\' })) "no tests, tools, .venv, previews or .git in the module ($($rel.Count) files)"
Assert (@($rel | Where-Object { $_ -like 'packs\*\shaders\*.hlsl' }).Count -gt 0 -and (Test-Path (Join-Path $v1 'packs\pokemon\pack.json'))) "ships the shaders and packs\pokemon\pack.json"
Assert (-not @($rel | Where-Object { $_ -like 'dist\pokemon\*' -or $_ -like 'packs\pokemon\art\*' -or $_ -like 'packs\pokemon\cards\*' })) "no Pokemon card art or card text (local-only, git-ignored)"
Assert ((Test-Path (Join-Path $v1 'bin\binder.exe')) -and (Test-Path (Join-Path $v1 'bin\binder-link.exe'))) "ships the binder and its link launcher in bin\ (no art in them)"
Add-FixturePack $v1
Assert ((Get-Content (Join-Path $v1 'packaged.txt')) -contains 'version=0.1.0') "packaged.txt marks it as a module"
$ignored = @(Get-ChildItem (Join-Path $v1 'packs') -Directory | ForEach-Object Name | Where-Object { & git -C $RepoRoot check-ignore -q "packs/$_/pack.json"; $LASTEXITCODE -eq 0 })
Assert (-not $ignored) "no git-ignored / locally excluded packs shipped$(if ($ignored) { ': ' + ($ignored -join ', ') })"
$stagedSkins = @(Get-PokeshellSkins $v1).Count

Write-Host "2. Import-Module + pokeshell install (temp LOCALAPPDATA, settings copy)" -ForegroundColor Cyan
$out = Run module @('version')
Assert ($out -match 'exports=pokeshell\r?\n' -and $out -match 'pokeshell 0\.1\.0' -and $out -match 'not installed yet') "Import-Module exports only pokeshell; version before install: $((($out -split "`n") | Where-Object { $_ -match 'pokeshell 0' }).Trim())"
$out = Run module @('install', '-SettingsPath', $settings)
Assert ($out -match [regex]::Escape('. "$env:LOCALAPPDATA\pokeshell\current\scripts\pokeshell-profile.ps1"')) "prints the stable `$PROFILE line"
$paths = Get-ShaderPaths
Assert ($paths.Count -eq $stagedSkins -and $stagedSkins -gt 0) "$($paths.Count) skin profiles added (staged module has $stagedSkins)"
Assert (-not @($paths | Where-Object { -not $_.StartsWith("$cur\") })) "every pixelShaderPath points into $cur"
Assert (-not @($paths | Where-Object { -not (Test-Path $_) })) "every shader file exists"
Assert ([IO.File]::ReadAllText((Join-Path $cur 'version.txt')) -eq '0.1.0') "current\version.txt = 0.1.0"
Assert (-not (Test-Path (Join-Path $cur 'tests')) -and (Test-Path (Join-Path $cur 'scripts\lib\Pokeshell.cs'))) "current holds the runtime only"
Assert ((Test-Path (Join-Path $cur 'bin\binder.exe')) -and (Test-Path (Join-Path $cur 'bin\binder-link.exe'))) "current\bin has binder.exe and binder-link.exe"
Assert ($out -match 'ctrl\+shift\+b' -and $out -match 'Ctrl\+click') "a module install sets up the binder key and the card link"
$afterV1 = [IO.File]::ReadAllBytes($settings)
$dll = Join-Path $state ("pokeshell-core-" + [IO.File]::GetLastWriteTimeUtc((Join-Path $cur 'scripts\lib\Pokeshell.cs')).Ticks + '-Desktop.dll')
Assert (Test-Path $dll) "the core DLL the hook looks for (named after current's Pokeshell.cs) is compiled"
$out = Invoke-HookRoll
Assert ($out -match 'ROLLED' -and $out -match (' : |' + [char]0x256d)) "the hook from current rolls a pull: '$((($out -split "`n") | Where-Object { $_ -match (' : |' + [char]0x256d) } | Select-Object -First 1).Trim())'"
Assert (-not (Test-Path (Join-Path $state 'errors.log'))) "no hook errors"

Write-Host "3. simulated Update-Module: 0.2.0 next to 0.1.0" -ForegroundColor Cyan
$v2 = Stage '0.2.0'
Add-FixturePack $v2
$out = Run hook @('version')
Assert ($out -match 'command=Function' -and $out -match 'pokeshell 0\.2\.0' -and $out -match '\(0\.1\.0\)') "the hook's pokeshell runs the newest module (0.2.0) while tabs still use 0.1.0"
$out = Run hook @('odds')
Assert ($out -match 'module 0\.2\.0 is installed but new tabs still run 0\.1\.0') "other commands remind you to re-run install"
$out = Run hook @('install', '-SettingsPath', $settings)
Assert ([IO.File]::ReadAllText((Join-Path $cur 'version.txt')) -eq '0.2.0') "pokeshell install refreshed current to 0.2.0"
Assert ([Convert]::ToBase64String([IO.File]::ReadAllBytes($settings)) -eq [Convert]::ToBase64String($afterV1)) "settings.json unchanged by the update (shader paths are stable)"
$left = @(Get-ChildItem $state -Directory | Where-Object Name -ne 'current' | Where-Object Name -like 'current*' | ForEach-Object Name)
Assert (-not $left) "no leftover staging folders$(if ($left) { ': ' + ($left -join ', ') })"
Remove-Item $v1 -Recurse -Force
Assert (-not (Test-Path $v1)) "old module version folder deleted (as Uninstall-Module / cleanup would)"
Assert (-not @(Get-ShaderPaths | Where-Object { -not (Test-Path $_) })) "every shader path still resolves"
Remove-Item (Join-Path $state 'roll.tsv')   # force the stale path too: roll.ps1 + common.ps1 from current rebuild the cache
$out = Invoke-HookRoll
Assert ($out -match 'ROLLED' -and $out -match (' : |' + [char]0x256d) -and (Test-Path (Join-Path $state 'roll.tsv'))) "the hook still rolls (incl. rebuilding the roll cache from current)"
$out = Run hook @('version')
Assert ($out -match 'pokeshell 0\.2\.0' -and $out -match '\(0\.2\.0\)' -and $out -notmatch 'still run') "`pokeshell` from the hook resolves to 0.2.0"
$out = Run module @('odds')
Assert ($out -match 'exports=pokeshell' -and $out -match 'Fixture' -and $out -notmatch 'still run') "Import-Module pokeshell (0.2.0) works"

Write-Host "4. module removed entirely: tabs keep working, the command explains" -ForegroundColor Cyan
Move-Item (Join-Path $mods 'pokeshell') (Join-Path $work 'pokeshell-away')
$out = Invoke-HookRoll
Assert ($out -match 'ROLLED') "the hook runs from current alone"
$out = Run hook @('odds')
Assert ($out -match 'module is not installed') "pokeshell says the module is gone"
Move-Item (Join-Path $work 'pokeshell-away') (Join-Path $mods 'pokeshell')

Write-Host "5. uninstall" -ForegroundColor Cyan
$out = Run module @('uninstall', '-SettingsPath', $settings)
Assert ([Convert]::ToBase64String([IO.File]::ReadAllBytes($settings)) -eq [Convert]::ToBase64String($origSettings)) "uninstall restores the settings copy byte for byte"
Assert ($out -match [regex]::Escape('current\scripts\pokeshell-profile.ps1')) "prints the `$PROFILE line to remove"
$out = Run module @('uninstall', '-SettingsPath', $settings, '-Purge')
Assert (-not (Test-Path $cur) -and -not (Test-Path (Join-Path $state 'config.txt'))) "-Purge deletes the (temp) state folder, current included (the core DLL the CLI has loaded may stay)"

if ($real) { Assert ((Get-FileHash $real).Hash -eq $realHash) "the real Windows Terminal settings.json was not touched" }
$diff = @(Compare-Object @($realStatePrint -split "`n") @((Get-Fingerprint $realState) -split "`n") | ForEach-Object { "$($_.SideIndicator) $($_.InputObject)" })
Assert (-not $diff) "the real %LOCALAPPDATA%\pokeshell was not touched$(if ($diff) { ': ' + ($diff -join '; ') })"
$mdiff = @(Compare-Object @($realModulesPrint -split "`n") @((@($RealPokeshellModuleDirs | ForEach-Object { Get-Fingerprint $_ }) -join "`n") -split "`n") | ForEach-Object { "$($_.SideIndicator) $($_.InputObject)" })
Assert (-not $mdiff) "the really installed pokeshell module ($(if ($RealPokeshellModuleDirs) { $RealPokeshellModuleDirs -join ', ' } else { 'none' })) was not touched$(if ($mdiff) { ': ' + (($mdiff | Select-Object -First 5) -join '; ') })"
Remove-Item $work -Recurse -Force -ErrorAction SilentlyContinue
Write-Host ''
if ($script:Failures) { Write-Host "module: $script:Failures FAILED" -ForegroundColor Red; exit 1 }
Write-Host "module: all passed" -ForegroundColor Green
