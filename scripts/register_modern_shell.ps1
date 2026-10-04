# PowerShell script to register or unregister the Windows 11 Modern Shell Extension (Sparse MSIX)
[CmdletBinding()]
param(
    [switch]$Uninstall,
    [switch]$StatusOnly,
    [switch]$RestartExplorer,
    [string]$ExternalLocation = ""
)

$PackageName = "Evydencia.PrintGenerator"
$ScriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
if (-not $ScriptDir) { $ScriptDir = Join-Path (Get-Location).Path "scripts" }
$RepoRoot = Split-Path -Parent $ScriptDir
$MsixPath = Join-Path $RepoRoot "installer\output\EvydenciaPrintGenerator.sparse.msix"
$CerPath = Join-Path $RepoRoot "installer\output\EvydenciaLabDev.cer"
$ValidationMarker = Join-Path $RepoRoot "installer\output\.modern_ui_validation"

if (-not $ExternalLocation) {
    # Staged deterministic external layout
    $stagedDir = Join-Path $RepoRoot "dist\windows"
    if (Test-Path $stagedDir) {
        $ExternalLocation = $stagedDir
    } else {
        $ExternalLocation = Join-Path $RepoRoot "native\windows-shell\build\Release"
    }
}

$existing = Get-AppxPackage -Name $PackageName -ErrorAction SilentlyContinue

if ($StatusOnly) {
    # 1. MODERN_PACKAGE_REGISTERED
    $pkgRegistered = if ($existing) { "YES" } else { "NO" }

    # 2. MODERN_RUNTIME_LAYOUT_OK
    $dllPath = Join-Path $ExternalLocation "EvydenciaShellExtension.dll"
    $exePath = Join-Path $ExternalLocation "EvydenciaPrintGenerator.exe"
    $iconPath = Join-Path $ExternalLocation "Assets\app.ico"
    $layoutOk = (Test-Path $dllPath) -and (Test-Path $exePath) -and (Test-Path $iconPath)
    $runtimeLayoutState = if ($layoutOk) { "YES" } else { "NO" }

    # 3. MODERN_TRUST_OK
    $certTrustedLM = $false
    if (Test-Path $CerPath) {
        $certObj = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2 $CerPath
        $store = New-Object System.Security.Cryptography.X509Certificates.X509Store "TrustedPeople", "LocalMachine"
        $store.Open("ReadOnly")
        $matches = $store.Certificates.Find("FindByThumbprint", $certObj.Thumbprint, $false)
        $certTrustedLM = ($matches.Count -gt 0)
        $store.Close()
    }
    $trustState = if ($certTrustedLM) { "YES" } else { "NO" }

    # 4. MODERN_UI_VALIDATION
    $uiState = "PENDING"
    if (Test-Path $ValidationMarker) {
        $valContent = (Get-Content $ValidationMarker -ErrorAction SilentlyContinue).Trim()
        if ($valContent -eq "PASSED" -or $valContent -eq "FAILED") {
            $uiState = $valContent
        }
    }

    # 5. CLASSIC_REGISTERED
    $classicKey = "HKCU:\Software\Classes\*\shell\EvydenciaPrintGenerator"
    $classicRegistered = if (Test-Path -LiteralPath $classicKey) { "YES" } else { "NO" }

    Write-Host "=== Diagnostic Status Telemetry ==="
    Write-Host "MODERN_PACKAGE_REGISTERED : $pkgRegistered"
    if ($existing) {
        Write-Host "  PackageFullName          : $($existing.PackageFullName)"
        Write-Host "  InstallLocation          : $($existing.InstallLocation)"
    }
    Write-Host "MODERN_RUNTIME_LAYOUT_OK  : $runtimeLayoutState ($ExternalLocation)"
    Write-Host "MODERN_TRUST_OK           : $trustState"
    Write-Host "MODERN_UI_VALIDATION      : $uiState"
    Write-Host "CLASSIC_REGISTERED        : $classicRegistered"

    if ($pkgRegistered -eq "YES" -and $layoutOk -and $certTrustedLM) {
        return
    } else {
        $host.SetShouldExit(1)
        return
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
    if (Test-Path $ValidationMarker) {
        Remove-Item $ValidationMarker -Force -ErrorAction SilentlyContinue
    }
    if ($RestartExplorer) {
        Write-Host "Restarting Windows Explorer as requested..."
        Stop-Process -Name explorer -Force
    }
    exit 0
}

# 1. Ensure Sparse MSIX exists and is fresh
$ManifestPath = Join-Path $RepoRoot "native\windows-shell\package\AppxManifest.xml"
$stale = (Test-Path $MsixPath) -and ((Get-Item $ManifestPath).LastWriteTime -gt (Get-Item $MsixPath).LastWriteTime)
if ((-not (Test-Path $MsixPath)) -or $stale) {
    Write-Host "Sparse MSIX package missing or older than AppxManifest.xml."
    Write-Host "Running package_sparse_msix.ps1 first..."
    & (Join-Path $ScriptDir "package_sparse_msix.ps1")
}

# 2. Ensure Developer Certificate is trusted in LocalMachine\TrustedPeople
Write-Host "==> Checking certificate trust in Cert:\LocalMachine\TrustedPeople..."
& (Join-Path $ScriptDir "trust_dev_cert.ps1") -CerPath $CerPath

# 3. Ensure External Layout is staged
$py = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }
& $py (Join-Path $ScriptDir "stage_external_layout.py")

# 4. Safe Registration: try new registration/update first without deleting previous version
Write-Host "`n==> Safe Registration of Sparse MSIX Package..."
Write-Host "  MSIX Path: $MsixPath"
Write-Host "  External Location: $ExternalLocation"

$registered = $false
try {
    Add-AppxPackage -Path $MsixPath -ExternalLocation $ExternalLocation -ErrorAction Stop
    $registered = $true
} catch {
    $errRecord = $_
    $hresult = $errRecord.Exception.HResult
    # 0x80073CFB is ERROR_PACKAGE_ALREADY_EXISTS (same version already registered)
    $isAlreadyInstalled = ($hresult -eq [int]0x80073CFB) -or ($errRecord.Exception.Message -match "0x80073CFB|already exists|já existe")

    if ($isAlreadyInstalled) {
        Write-Host "Notice: Package version already registered (0x$($hresult.ToString('X8'))). Performing safe update (unregister and re-register)..."
        $currentPkg = Get-AppxPackage -Name $PackageName -ErrorAction SilentlyContinue
        if ($currentPkg) {
            Remove-AppxPackage -Package $currentPkg.PackageFullName -ErrorAction Stop
        }
        Add-AppxPackage -Path $MsixPath -ExternalLocation $ExternalLocation -ErrorAction Stop
        $registered = $true
    } else {
        # Other failures: DO NOT remove previous working package!
        Write-Host "ERROR: Add-AppxPackage failed with HRESULT: 0x$($hresult.ToString('X8'))" -ForegroundColor Red
        Write-Host "Exception: $($errRecord.Exception.Message)" -ForegroundColor Red
        throw $errRecord
    }
}

$pkg = Get-AppxPackage -Name $PackageName
if (-not $pkg) {
    throw "Verification failed: Package $PackageName not found after Add-AppxPackage."
}

Write-Host "`n[SUCCESS] Modern Shell Extension registered successfully!"
Write-Host "  Package Full Name : $($pkg.PackageFullName)"
Write-Host "  External Location : $($pkg.InstallLocation)"
Write-Host "`nNOTE: Classic fallback is intentionally PRESERVED until real Explorer validation passes."

if ($RestartExplorer) {
    Write-Host "Restarting Windows Explorer as requested (--restart-explorer)..."
    Stop-Process -Name explorer -Force
} else {
    Write-Host "Windows Explorer was NOT restarted. Pass -RestartExplorer or restart explorer if changes are not immediately visible."
}
