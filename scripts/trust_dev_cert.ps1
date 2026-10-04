# PowerShell script to trust the development certificate in Cert:\LocalMachine\TrustedPeople
# Microsoft officially documents self-signed MSIX trust in Cert:\LocalMachine\TrustedPeople.
[CmdletBinding()]
param(
    [string]$CerPath = ""
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir

if (-not $CerPath) {
    $CerPath = Join-Path $RepoRoot "installer\output\EvydenciaLabDev.cer"
}

if (-not (Test-Path $CerPath)) {
    # Generate / export if missing
    & (Join-Path $ScriptDir "package_sparse_msix.ps1")
}

$certObj = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2 $CerPath
$thumb = $certObj.Thumbprint

function Test-CertTrustedLM([string]$thumbprint) {
    $store = New-Object System.Security.Cryptography.X509Certificates.X509Store "TrustedPeople", "LocalMachine"
    $store.Open("ReadOnly")
    $matches = $store.Certificates.Find("FindByThumbprint", $thumbprint, $false)
    $found = ($matches.Count -gt 0)
    $store.Close()
    return $found
}

if (Test-CertTrustedLM $thumb) {
    Write-Host "[OK] Certificate is already trusted in Cert:\LocalMachine\TrustedPeople ($thumb)"
    exit 0
}

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "Elevated permissions are required to add the developer certificate to Cert:\LocalMachine\TrustedPeople."
    Write-Host "Opening Windows UAC elevation prompt..."
    $argList = "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`" -CerPath `"$CerPath`""
    $p = Start-Process powershell -Verb RunAs -ArgumentList $argList -PassThru -Wait
    
    # Re-check after elevation
    if (Test-CertTrustedLM $thumb) {
        Write-Host "[SUCCESS] Developer certificate successfully imported into Cert:\LocalMachine\TrustedPeople!"
        exit 0
    } else {
        throw "Certificate was not imported. UAC prompt was cancelled or failed."
    }
}

# Running as elevated Administrator:
Write-Host "Importing certificate into Cert:\LocalMachine\TrustedPeople..."
Import-Certificate -FilePath $CerPath -CertStoreLocation Cert:\LocalMachine\TrustedPeople | Out-Null
Write-Host "[SUCCESS] Imported certificate ($thumb) into Cert:\LocalMachine\TrustedPeople."
