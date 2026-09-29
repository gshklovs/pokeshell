<#
Build the binder app (Rust, ratatui) into binder\target\release\binder.exe, where `pokeshell binder` finds it.
  powershell -NoProfile -File binder\build.ps1           # release build
  powershell -NoProfile -File binder\build.ps1 -Test     # unit tests, then the headless selftest
On Windows it builds with the MSVC toolchain explicitly (cargo +stable-x86_64-pc-windows-msvc), so it works whatever
rustup's default host is (a -gnu default needs MinGW's linker). The same as `rustup override set
stable-x86_64-pc-windows-msvc` in this folder, without changing rustup's settings. Elsewhere: plain cargo.
#>
param([switch]$Test)
$ErrorActionPreference = 'Stop'
$manifest = Join-Path $PSScriptRoot 'Cargo.toml'
$tc = @()
if ($env:OS -eq 'Windows_NT') {
  $want = 'stable-x86_64-pc-windows-msvc'
  if (-not (& rustup toolchain list | Select-String -SimpleMatch $want)) { throw "the $want toolchain is missing: rustup toolchain install $want" }
  $tc = @("+$want")
}
if ($Test) {
  & cargo @tc test --release --manifest-path $manifest
  if ($LASTEXITCODE) { throw 'cargo test failed' }
}
& cargo @tc build --release --manifest-path $manifest
if ($LASTEXITCODE) { throw 'cargo build failed' }
$exe = Join-Path $PSScriptRoot 'target\release\binder.exe'
if ($Test) { & $exe --root (Split-Path $PSScriptRoot) --selftest; if ($LASTEXITCODE) { throw 'selftest failed' } }
Write-Host "binder: $exe" -ForegroundColor Green
