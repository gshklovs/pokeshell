@{
  RootModule           = 'pokeshell.psm1'
  ModuleVersion        = '0.1.0'
  GUID                 = 'ed6d57b3-982a-4eca-a102-da6781ef804d'
  Author               = 'gshklovs'
  CompanyName          = 'gshklovs'
  Copyright            = '(c) gshklovs. MIT License.'
  Description          = 'Every new Windows Terminal PowerShell tab is a trading-card pack pull: pixel art for common pulls, animated holofoil pixel-shader skins for foils, and a binder of everything you pulled. Run "pokeshell install" after installing the module.'
  PowerShellVersion    = '5.1'
  CompatiblePSEditions = @('Desktop', 'Core')
  FunctionsToExport    = @('pokeshell', 'clip')
  CmdletsToExport      = @()
  VariablesToExport    = @()
  AliasesToExport      = @()
  PrivateData          = @{
    PSData = @{
      Tags         = @('WindowsTerminal', 'PowerShell', 'Pokemon', 'shader', 'terminal', 'fun', 'Windows')
      ProjectUri   = 'https://github.com/gshklovs/pokeshell'
      LicenseUri   = 'https://github.com/gshklovs/pokeshell/blob/main/LICENSE'
      ReleaseNotes = 'First release. After Install-Module (or Update-Module), run: pokeshell install'
    }
  }
}
