<#
Run every pokeshell test. Nothing here touches your real Windows Terminal settings, $PROFILE or
%LOCALAPPDATA%\pokeshell: state goes to %TEMP%\pokeshell-test-*, settings edits go to copies, and
foil pulls are dry runs (no tab is opened).
  powershell -NoProfile -ExecutionPolicy Bypass -File tests\run-all.ps1
#>
$failed = @()
foreach ($t in 'test-no-loop.ps1', 'test-install.ps1', 'test-cli.ps1', 'test-cards.ps1', 'test-earned.ps1', 'test-anim.ps1', 'test-art.ps1', 'test-module.ps1', 'measure-startup.ps1') {
  Write-Host "`n=== $t ===" -ForegroundColor Magenta
  & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot $t)
  if ($LASTEXITCODE -ne 0) { $failed += $t }
}
Write-Host ''
if ($failed) { Write-Host "FAILED: $($failed -join ', ')" -ForegroundColor Red; exit 1 }
Write-Host 'all tests passed' -ForegroundColor Green
