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
$ManifestPath = Join-Path $RepoRoot "native\windows-shell\package\AppxManifest.xml"
$stale = (Test-Path $MsixPath) -and ((Get-Item $ManifestPath).LastWriteTime -gt (Get-Item $MsixPath).LastWriteTime)
if ((-not (Test-Path $MsixPath)) -or $stale) {
    Write-Host "Sparse MSIX package missing or older than AppxManifest.xml."
    Write-Host "Running package_sparse_msix.ps1 first..."
    & (Join-Path $ScriptDir "package_sparse_msix.ps1")
}

# Docs: a version that is already registered cannot be registered again.
if ($existing) {
    Write-Host "Removing previously registered package '$($existing.PackageFullName)'..."
    Remove-AppxPackage -Package $existing.PackageFullName -ErrorAction Stop
}

Write-Host "Registering Sparse MSIX Package..."
Write-Host "  MSIX Path: $MsixPath"
Write-Host "  External Location: $ExternalLocation"

try {
    Add-AppxPackage -Path $MsixPath -ExternalLocation $ExternalLocation -ErrorAction Stop
    $pkg = Get-AppxPackage -Name $PackageName
    Write-Host "`n[SUCCESS] Modern Shell Extension registered successfully!"
    Write-Host "Package: $($pkg.PackageFullName)"
    Write-Host "If the command does not show up yet, restart File Explorer or sign out/in."
} catch {
    Write-Host "`n[NOTICE] Modern package registration did not complete:" -ForegroundColor Yellow
    Write-Host "$($_.Exception.Message)"
    if ($_.Exception.Message -match "0x800B0109") {
        Write-Host "`nReason: the signing certificate is not in 'Cert:\CurrentUser\TrustedPeople'."
        Write-Host "Re-run scripts\package_sparse_msix.ps1 (it imports the public cert there, no admin needed)."
        Write-Host "Alternatively, use the per-user classic fallback (python scripts/manage_shell_extension.py install --classic)."
    }
    exit 1
}
