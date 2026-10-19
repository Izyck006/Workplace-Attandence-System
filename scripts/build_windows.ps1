$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
python -m PyInstaller --noconfirm --clean packaging/desktop.spec
if ($LASTEXITCODE -ne 0) { throw 'Desktop build failed' }
$sdkRoot = if ($env:IBSCAN_SDK_DIR) { Split-Path $env:IBSCAN_SDK_DIR -Parent } else { 'C:\Program Files\Integrated Biometrics\IBScanUltimateSDK_x64' }
New-Item -ItemType Directory -Force installer/vendor | Out-Null
Copy-Item -LiteralPath (Join-Path $sdkRoot 'Driver\IBScanDriver Setup.msi') -Destination 'installer/vendor/IBScanDriver Setup.msi'
$compilerCandidates = @('tools\inno\ISCC.exe', 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe', 'C:\Program Files\Inno Setup 7\ISCC.exe')
$compiler = $compilerCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $compiler) { throw 'Install Inno Setup, then rerun this build.' }
& $compiler installer/setup.iss
if ($LASTEXITCODE -ne 0) { throw 'Installer compilation failed' }
Get-FileHash release/RandaframesAttendance-Setup-2.0.0.exe -Algorithm SHA256
