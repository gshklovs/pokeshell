# pokeshell module: one command. The CLI is scripts\pokeshell.ps1 (the same script a source checkout runs).
# The $PROFILE hook never imports this module: `pokeshell install` copies what new tabs need into
# %LOCALAPPDATA%\pokeshell\current and the hook runs from there.
function pokeshell { & (Join-Path $PSScriptRoot 'scripts\pokeshell.ps1') @args }
Export-ModuleMember -Function pokeshell
