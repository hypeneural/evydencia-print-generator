# PowerShell script to package and sign the sparse MSIX package for EVYDÊNCIA Print Generator
[CmdletBinding()]
param(
    [string]$MakeAppxPath = "",
    [string]$SignToolPath = "",
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

function Find-WindowsKitTool([string]$ToolName) {
    # 1. Check if tool is directly in PATH
    $cmd = Get-Command $ToolName -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    # 2. Probe 32-bit and 64-bit Windows Kits directories for newest installed SDK
    $candidateRoots = @(
        "${env:ProgramFiles(x86)}\Windows Kits\10\bin",
        "$env:ProgramFiles\Windows Kits\10\bin"
    )

    foreach ($root in $candidateRoots) {
        if (Test-Path $root) {
            $versions = Get-ChildItem -Path $root -Directory -ErrorAction SilentlyContinue |
                Where-Object { $_.Name -match '^\d+\.\d+\.\d+\.\d+$' } |
                Sort-Object { [version]$_.Name } -Descending

            foreach ($ver in $versions) {
                # Prefer x64 tool
                $x64Path = Join-Path $ver.FullName "x64\$ToolName"
                if (Test-Path $x64Path) { return $x64Path }

                # Fallback to x86
                $x86Path = Join-Path $ver.FullName "x86\$ToolName"
                if (Test-Path $x86Path) { return $x86Path }
            }
        }
    }

    return $null
}

if (-not $MakeAppxPath) {
    $MakeAppxPath = Find-WindowsKitTool "makeappx.exe"
    if (-not $MakeAppxPath) {
        throw "makeappx.exe not found in PATH or any installed Windows SDK."
    }
}

if (-not $SignToolPath) {
    $SignToolPath = Find-WindowsKitTool "signtool.exe"
    if (-not $SignToolPath) {
        throw "signtool.exe not found in PATH or any installed Windows SDK."
    }
}

Write-Host "=== Discovered Windows SDK Toolchain ==="
Write-Host "  makeappx: $MakeAppxPath"
Write-Host "  signtool: $SignToolPath"

# Validate AppxManifest.xml Publisher match
$manifestFile = Join-Path $PackageDir "AppxManifest.xml"
if (-not (Test-Path $manifestFile)) {
    throw "BLOCKER: AppxManifest.xml not found at $manifestFile"
}
[xml]$manifestXml = Get-Content $manifestFile
$manifestPublisher = $manifestXml.Package.Identity.Publisher
if ($manifestPublisher -ne $CertSubject) {
    throw "BLOCKER: AppxManifest Publisher ('$manifestPublisher') does not match Certificate Subject ('$CertSubject')."
}
Write-Host "Identity match: Manifest Publisher ('$manifestPublisher') == Cert Subject ('$CertSubject')"

Write-Host "`n==> [1/4] Checking Developer Signing Certificate ($CertSubject)..."
$cert = Get-ChildItem -Path Cert:\CurrentUser\My | Where-Object { $_.Subject -eq $CertSubject } | Select-Object -First 1
if (-not $cert) {
    Write-Host "Creating new developer self-signed certificate in Cert:\CurrentUser\My with CodeSigning EKU and BasicConstraints..."
    $cert = New-SelfSignedCertificate `
        -Type Custom `
        -Subject $CertSubject `
        -KeyAlgorithm RSA `
        -KeyLength 2048 `
        -KeyUsage DigitalSignature `
        -FriendlyName "EVYDENCIA Dev Certificate" `
        -CertStoreLocation "Cert:\CurrentUser\My" `
        -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.3", "2.5.29.19={text}")
}
Write-Host "Using Certificate Thumbprint: $($cert.Thumbprint)"

# Export public cert to standard location in installer/output
$cerFile = Join-Path $OutputDir "EvydenciaLabDev.cer"
Export-Certificate -Cert $cert -FilePath $cerFile -Force | Out-Null
Write-Host "Exported public certificate to: $cerFile"

# Ensure in CurrentUser\TrustedPeople
$alreadyTrustedUser = Get-ChildItem Cert:\CurrentUser\TrustedPeople -ErrorAction SilentlyContinue |
    Where-Object { $_.Thumbprint -eq $cert.Thumbprint }
if (-not $alreadyTrustedUser) {
    Import-Certificate -FilePath $cerFile -CertStoreLocation Cert:\CurrentUser\TrustedPeople | Out-Null
    Write-Host "Certificate trusted in Cert:\CurrentUser\TrustedPeople"
}

Write-Host "`n==> [2/4] Executing BLOCKER Gate: Staging Deterministic External Layout..."
$py = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }
$stageScript = Join-Path $ScriptDir "stage_external_layout.py"
& $py $stageScript
if ($LASTEXITCODE -ne 0) {
    throw "BLOCKER Gate failed: External layout staging failed."
}

Write-Host "`n==> [3/4] Packing Sparse MSIX with makeappx.exe..."
& $MakeAppxPath pack /d $PackageDir /p $OutputMsix /nv /o
if ($LASTEXITCODE -ne 0) {
    throw "makeappx.exe failed with exit code $LASTEXITCODE"
}
Write-Host "Package created: $OutputMsix"

Write-Host "`n==> [4/4] Signing Sparse MSIX with signtool.exe..."
& $SignToolPath sign /fd SHA256 /sha1 $cert.Thumbprint $OutputMsix
if ($LASTEXITCODE -ne 0) {
    throw "signtool.exe signing failed with exit code $LASTEXITCODE"
}

# Verify Authenticode Signature
$sig = Get-AuthenticodeSignature $OutputMsix
if ($sig.Status -ne "Valid") {
    throw "Authenticode signature validation failed: $($sig.StatusMessage)"
}
Write-Host "Authenticode Signature Verified: $($sig.Status) ($($sig.SignerCertificate.Thumbprint))"

Write-Host "`n[SUCCESS] Signed sparse MSIX package generated and verified at $OutputMsix"
