$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)

$cert = Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert | Where-Object { $_.Subject -like '*Zicron*' } | Select-Object -First 1

if (-not $cert) {
    Write-Host 'Generating Zicron Code Signing Certificate...'
    $cert = New-SelfSignedCertificate `
        -Type CodeSigningCert `
        -Subject 'CN=Zicron, O=Zicron, C=NG' `
        -CertStoreLocation Cert:\CurrentUser\My `
        -HashAlgorithm SHA256 `
        -NotAfter (Get-Date).AddYears(5)
}

New-Item -ItemType Directory -Force release | Out-Null
$certFile = 'release\Zicron-CodeSigning.cer'
Export-Certificate -Cert $cert -FilePath $certFile -Force | Out-Null
Write-Host "Exported public certificate to $certFile"

$exePath = 'release\RandaframesAttendance-Setup-2.0.0.exe'
if (Test-Path $exePath) {
    Write-Host "Signing $exePath with Zicron certificate..."
    $sig = Set-AuthenticodeSignature -FilePath $exePath -Certificate $cert -HashAlgorithm SHA256
    Write-Host "Status: $($sig.StatusMessage)"
}

$appExe = 'dist\RandaframesAttendance\RandaframesAttendance.exe'
if (Test-Path $appExe) {
    Write-Host "Signing $appExe with Zicron certificate..."
    $sig2 = Set-AuthenticodeSignature -FilePath $appExe -Certificate $cert -HashAlgorithm SHA256
    Write-Host "Status: $($sig2.StatusMessage)"
}

Write-Host 'Done.'
