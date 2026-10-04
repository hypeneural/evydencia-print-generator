# PowerShell script to register or unregister the Windows 11 Modern Shell Extension (Sparse MSIX)
[CmdletBinding()]
param(
    [switch]$Uninstall,
    [switch]$StatusOnly,
    [string]$ExternalLocation = ""
)

$PackageName = "Evydencia.PrintGenerator"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$MsixPath = Join-Path $RepoRoot "installer\output\EvydenciaPrintGenerator.sparse.msix"

if (-not $ExternalLocation) {
    # Default to built Release directory or repo root
    $relDir = Join-Path $RepoRoot "native\windows-shell\build\Release"
    if (Test-Path $relDir) {
        $ExternalLocation = $relDir
    } else {
        $ExternalLocation = $RepoRoot
    }
}

$existing = Get-AppxPackage -Name $PackageName -ErrorAction SilentlyContinue

if ($StatusOnly) {
    if ($existing) {
        Write-Host "Modern Shell Extension is REGISTERED:"
        Write-Host "  Package: $($existing.PackageFullName)"
        Write-Host "  InstallLocation: $($existing.InstallLocation)"
        exit 0
    } else {
        Write-Host "Modern Shell Extension is NOT registered."
        exit 1
    }
}

if ($Uninstall) {
    if ($existing) {
        Write-Host "Removing AppxPackage '$($existing.PackageFullName)'..."
        Remove-AppxPackage -Package $existing.PackageFullName -ErrorAction Stop
        Write-Host "[SUCCESS] Modern Shell Extension unregistered cleanly."
    } else {
        Write-Host "Package '$PackageName' was not registered."
    }
    exit 0
}

# Registration
if (-not (Test-Path $MsixPath)) {
    Write-Host "Sparse MSIX package not found at $MsixPath."
    Write-Host "Running package_sparse_msix.ps1 first..."
    & (Join-Path $ScriptDir "package_sparse_msix.ps1")
}

Write-Host "Registering Sparse MSIX Package..."
Write-Host "  MSIX Path: $MsixPath"
Write-Host "  External Location: $ExternalLocation"

try {
    Add-AppxPackage -Path $MsixPath -ExternalLocation $ExternalLocation -ErrorAction Stop
    $pkg = Get-AppxPackage -Name $PackageName
    Write-Host "`n[SUCCESS] Modern Shell Extension registered successfully!"
    Write-Host "Package: $($pkg.PackageFullName)"
} catch {
    Write-Host "`n[NOTICE] Modern package registration did not complete:" -ForegroundColor Yellow
    Write-Host "$($_.Exception.Message)"
    if ($_.Exception.Message -match "0x800B0109") {
        Write-Host "`nReason: The dev test certificate requires trust in 'Cert:\LocalMachine\Root' or user Root."
        Write-Host "To trust the certificate, run as Administrator: certutil -addstore Root <cert.cer>"
        Write-Host "Alternatively, use the per-user classic fallback (python scripts/manage_shell_extension.py install --classic)."
    }
    exit 1
}
