#!/usr/bin/env python3
"""Unified CLI manager for EVYDÊNCIA Windows Context Menu Integration.

Usage:
    python scripts/manage_shell_extension.py status
    python scripts/manage_shell_extension.py build
    python scripts/manage_shell_extension.py stage
    python scripts/manage_shell_extension.py install [--modern | --classic | --auto] [--restart-explorer]
    python scripts/manage_shell_extension.py validate-ui {pass|fail|reset}
    python scripts/manage_shell_extension.py clean-classic
    python scripts/manage_shell_extension.py uninstall [--restart-explorer]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SCRIPTS_DIR = ROOT / "scripts"
RELEASE_DIR = ROOT / "native" / "windows-shell" / "build" / "Release"
DLL_PATH = RELEASE_DIR / "EvydenciaShellExtension.dll"
EXE_PATH = RELEASE_DIR / "EvydenciaPrintGenerator.exe"
STAGE_DIR = ROOT / "dist" / "windows"
MSIX_PATH = ROOT / "installer" / "output" / "EvydenciaPrintGenerator.sparse.msix"
CER_PATH = ROOT / "installer" / "output" / "EvydenciaLabDev.cer"
VALIDATION_MARKER = ROOT / "installer" / "output" / ".modern_ui_validation"

from installer.shell_fallback import (  # noqa: E402
    get_shell_status,
    register_classic_fallback,
    unregister_classic_fallback,
)


def run_ps1(script_name: str, *args: str) -> subprocess.CompletedProcess[str]:
    script_path = SCRIPTS_DIR / script_name
    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script_path),
        *args,
    ]
    return subprocess.run(cmd, text=True, capture_output=True)


def check_localmachine_cert() -> bool:
    if not CER_PATH.exists():
        return False
    check_cmd = [
        "powershell",
        "-NoProfile",
        "-Command",
        f"$cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2 '{CER_PATH}'; "
        "$store = New-Object System.Security.Cryptography.X509Certificates.X509Store 'TrustedPeople', 'LocalMachine'; "
        "$store.Open('ReadOnly'); "
        "$m = $store.Certificates.Find('FindByThumbprint', $cert.Thumbprint, $false); "
        "$found = ($m.Count -gt 0); $store.Close(); "
        "if ($found) { exit 0 } else { exit 1 }",
    ]
    res = subprocess.run(check_cmd, capture_output=True)
    return res.returncode == 0


def get_ui_validation_state() -> str:
    if VALIDATION_MARKER.exists():
        val = VALIDATION_MARKER.read_text(encoding="utf-8").strip()
        if val in ("PASSED", "FAILED"):
            return val
    return "PENDING"


def cmd_status() -> int:
    shell_stat = get_shell_status()
    proc = run_ps1("register_modern_shell.ps1", "-StatusOnly")

    mod_registered = "MODERN_PACKAGE_REGISTERED : YES" in proc.stdout
    runtime_layout_ok = "MODERN_RUNTIME_LAYOUT_OK  : YES" in proc.stdout
    lm_cert_trusted = check_localmachine_cert()
    ui_validation = get_ui_validation_state()
    classic_registered = shell_stat["classic_active"]

    print("=== EVYDÊNCIA Windows Shell Status Diagnostics ===")
    print(f"MODERN_PACKAGE_REGISTERED: { 'YES' if mod_registered else 'NO' }")
    print(f"MODERN_RUNTIME_LAYOUT_OK:  { 'YES' if runtime_layout_ok else 'NO' }")
    print(f"MODERN_TRUST_OK:           { 'YES' if lm_cert_trusted else 'NO' }")
    print(f"MODERN_UI_VALIDATION:      { ui_validation }")
    print(f"CLASSIC_REGISTERED:        { 'YES' if classic_registered else 'NO' }")
    print("--------------------------------------------------")
    print(f"Native DLL built:           { 'YES' if DLL_PATH.exists() else 'NO' } ({DLL_PATH})")
    print(f"Launcher EXE built:         { 'YES' if EXE_PATH.exists() else 'NO' } ({EXE_PATH})")
    print(f"Staged Layout:              { 'YES' if STAGE_DIR.exists() else 'NO' } ({STAGE_DIR})")
    print(f"Sparse MSIX packaged:       { 'YES' if MSIX_PATH.exists() else 'NO' }")
    print(f"Cert in LocalMachine Trust: { 'YES' if lm_cert_trusted else 'NO' }")

    if classic_registered:
        print(f"Classic Command Verb:       {shell_stat['command']}")
    if mod_registered:
        for line in proc.stdout.splitlines():
            if "PackageFullName" in line or "InstallLocation" in line:
                print(f"  {line.strip()}")

    return 0


def cmd_build() -> int:
    print("==> [1/3] Building Native Shell Extension DLL, Launcher & Tests...")
    res = subprocess.run([sys.executable, str(SCRIPTS_DIR / "build_shell_extension.py")])
    if res.returncode != 0:
        return res.returncode

    print("\n==> [2/3] Staging Deterministic External Layout...")
    res = subprocess.run([sys.executable, str(SCRIPTS_DIR / "stage_external_layout.py")])
    if res.returncode != 0:
        return res.returncode

    print("\n==> [3/3] Packaging & Signing Sparse MSIX...")
    proc = run_ps1("package_sparse_msix.ps1")
    print(proc.stdout)
    if proc.stderr:
        print(proc.stderr, file=sys.stderr)
    return proc.returncode


def cmd_stage() -> int:
    res = subprocess.run([sys.executable, str(SCRIPTS_DIR / "stage_external_layout.py")])
    return res.returncode


def cmd_validate_ui(state: str) -> int:
    VALIDATION_MARKER.parent.mkdir(parents=True, exist_ok=True)
    if state == "pass":
        VALIDATION_MARKER.write_text("PASSED\n", encoding="utf-8")
        print("[OK] MODERN_UI_VALIDATION set to: PASSED")
    elif state == "fail":
        VALIDATION_MARKER.write_text("FAILED\n", encoding="utf-8")
        print("[OK] MODERN_UI_VALIDATION set to: FAILED")
    elif state == "reset":
        VALIDATION_MARKER.unlink(missing_ok=True)
        print("[OK] MODERN_UI_VALIDATION reset to: PENDING")
    return 0


def cmd_clean_classic(force: bool = False) -> int:
    ui_state = get_ui_validation_state()
    if not force and ui_state != "PASSED":
        print(
            "Notice: Cannot remove classic fallback because MODERN_UI_VALIDATION is not PASSED.\n"
            f"Current status: {ui_state}. Verify modern menu in Explorer first and run:\n"
            "  python scripts/manage_shell_extension.py validate-ui pass\n"
            "(or pass --force to bypass this safety gate)",
            file=sys.stderr,
        )
        return 1

    print("Cleaning up classic HKCU fallback registration to prevent duplicates...")
    if unregister_classic_fallback():
        print("[SUCCESS] Classic fallback unregistered cleanly.")
        return 0
    print("No classic registration was present.")
    return 0


def cmd_install(mode: str, restart_explorer: bool = False) -> int:
    if not DLL_PATH.exists() or not MSIX_PATH.exists():
        print("Build artifacts missing. Building first...")
        code = cmd_build()
        if code != 0:
            return code

    ps_args = []
    if restart_explorer:
        ps_args.append("-RestartExplorer")

    if mode == "classic":
        print("Registering per-user classic shell fallback (HKCU)...")
        if register_classic_fallback(force=True):
            print("[SUCCESS] Classic shell fallback registered successfully!")
            return 0
        return 1

    if mode == "modern":
        print("Registering Modern Windows 11 Shell Extension (Sparse MSIX)...")
        proc = run_ps1("register_modern_shell.ps1", *ps_args)
        print(proc.stdout)
        if proc.stderr:
            print(proc.stderr, file=sys.stderr)
        return proc.returncode

    # mode == 'auto'
    print("Attempting Modern Windows 11 Shell Extension registration...")
    proc = run_ps1("register_modern_shell.ps1", *ps_args)
    print(proc.stdout)
    if proc.returncode == 0:
        print("[SUCCESS] Windows 11 Modern Shell Extension is registered.")
        print("Note: Classic fallback remains active until manual Explorer validation (Gate G8).")
        return 0

    print("\nModern registration did not succeed.")
    print("Enabling per-user classic fallback so context menu works immediately...")
    if register_classic_fallback(force=True):
        print(
            "[SUCCESS] Classic fallback active! "
            "Photos will display 'Gerar com EVYDÊNCIA' under context menu."
        )
        return 0
    return 1


def cmd_uninstall(restart_explorer: bool = False) -> int:
    print("Unregistering Windows Shell Integration...")
    ps_args = ["-Uninstall"]
    if restart_explorer:
        ps_args.append("-RestartExplorer")
    run_ps1("register_modern_shell.ps1", *ps_args)
    unregister_classic_fallback()
    VALIDATION_MARKER.unlink(missing_ok=True)
    print("[SUCCESS] All shell registrations cleanly removed.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="EVYDÊNCIA Shell Extension Manager")
    subparsers = parser.add_subparsers(dest="action", required=True)

    subparsers.add_parser("status", help="Show current registration status")
    subparsers.add_parser("build", help="Build native DLL and sparse MSIX package")
    subparsers.add_parser("stage", help="Stage deterministic external runtime layout")

    install_parser = subparsers.add_parser("install", help="Install context menu integration")
    install_group = install_parser.add_mutually_exclusive_group()
    install_group.add_argument(
        "--modern", action="store_true", help="Register modern sparse MSIX only"
    )
    install_group.add_argument(
        "--classic", action="store_true", help="Register classic HKCU fallback only"
    )
    install_group.add_argument(
        "--auto", action="store_true", default=True, help="Try modern, fallback to classic"
    )
    install_parser.add_argument(
        "--restart-explorer", action="store_true", help="Restart Windows Explorer upon install"
    )

    val_parser = subparsers.add_parser("validate-ui", help="Record Explorer UI validation status")
    val_parser.add_argument("state", choices=["pass", "fail", "reset"])

    clean_parser = subparsers.add_parser(
        "clean-classic", help="Remove classic fallback once modern is verified"
    )
    clean_parser.add_argument(
        "--force", action="store_true", help="Force removal even if UI validation is pending"
    )

    uninstall_parser = subparsers.add_parser("uninstall", help="Uninstall all shell integrations")
    uninstall_parser.add_argument(
        "--restart-explorer", action="store_true", help="Restart Windows Explorer upon uninstall"
    )

    args = parser.parse_args(argv)

    if args.action == "status":
        return cmd_status()
    elif args.action == "build":
        return cmd_build()
    elif args.action == "stage":
        return cmd_stage()
    elif args.action == "validate-ui":
        return cmd_validate_ui(args.state)
    elif args.action == "clean-classic":
        return cmd_clean_classic(force=getattr(args, "force", False))
    elif args.action == "install":
        mode = "modern" if args.modern else ("classic" if args.classic else "auto")
        return cmd_install(mode, restart_explorer=args.restart_explorer)
    elif args.action == "uninstall":
        return cmd_uninstall(restart_explorer=args.restart_explorer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
