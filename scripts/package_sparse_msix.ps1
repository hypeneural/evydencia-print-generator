# PowerShell script to package and sign the sparse MSIX package for EVYDÊNCIA Print Generator
[CmdletBinding()]
param(
    [string]$MakeAppxPath = "C:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x64\makeappx.exe",
    [string]$SignToolPath = "C:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x64\signtool.exe",
    [string]$CertSubject = "CN=EvydenciaLabDev"
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$PackageDir = Join-Path $RepoRoot "native\windows-shell\package"
$OutputDir = Join-Path $RepoRoot "installer\output"
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}
$OutputMsix = Join-Path $OutputDir "EvydenciaPrintGenerator.sparse.msix"

Write-Host "==> [1/3] Checking Developer Signing Certificate ($CertSubject)..."
$cert = Get-ChildItem -Path Cert:\CurrentUser\My | Where-Object { $_.Subject -eq $CertSubject } | Select-Object -First 1
if (-not $cert) {
    Write-Host "Creating new developer self-signed certificate in Cert:\CurrentUser\My..."
    $cert = New-SelfSignedCertificate `
        -Type Custom `
        -Subject $CertSubject `
        -KeyUsage DigitalSignature `
        -FriendlyName "EVYDENCIA Dev Certificate" `
        -CertStoreLocation "Cert:\CurrentUser\My" `
        -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.3")
}
Write-Host "Using Certificate Thumbprint: $($cert.Thumbprint)"

# Ensure in TrustedPublisher store as well
$pubStore = New-Object System.Security.Cryptography.X509Certificates.X509Store "TrustedPublisher", "CurrentUser"
$pubStore.Open([System.Security.Cryptography.X509Certificates.OpenFlags]::ReadWrite)
$alreadyInPub = $pubStore.Certificates | Where-Object { $_.Thumbprint -eq $cert.Thumbprint }
if (-not $alreadyInPub) {
    $pubStore.Add($cert)
}
$pubStore.Close()

Write-Host "`n==> [2/3] Packing Sparse MSIX with makeappx.exe..."
if (-not (Test-Path $MakeAppxPath)) {
    throw "makeappx.exe not found at $MakeAppxPath"
}
& $MakeAppxPath pack /d $PackageDir /p $OutputMsix /nv /o
if ($LASTEXITCODE -ne 0) {
    throw "makeappx.exe failed with exit code $LASTEXITCODE"
}
Write-Host "Package created: $OutputMsix"

Write-Host "`n==> [3/3] Signing Sparse MSIX with signtool.exe..."
if (-not (Test-Path $SignToolPath)) {
    throw "signtool.exe not found at $SignToolPath"
}
& $SignToolPath sign /fd SHA256 /s My /n "EvydenciaLabDev" $OutputMsix
if ($LASTEXITCODE -ne 0) {
    throw "signtool.exe signing failed with exit code $LASTEXITCODE"
}

Write-Host "`n[SUCCESS] Signed sparse package generated successfully at $OutputMsix"
