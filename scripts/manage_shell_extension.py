#!/usr/bin/env python3
"""Unified CLI manager for EVYDÊNCIA Windows Context Menu Integration.

Usage:
    python scripts/manage_shell_extension.py status
    python scripts/manage_shell_extension.py build
    python scripts/manage_shell_extension.py install [--modern | --classic | --auto]
    python scripts/manage_shell_extension.py uninstall
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
MSIX_PATH = ROOT / "installer" / "output" / "EvydenciaPrintGenerator.sparse.msix"

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


def cmd_status() -> int:
    status = get_shell_status()
    mod_state = "ACTIVE" if status["modern_active"] else "INACTIVE"
    cls_state = "ACTIVE" if status["classic_active"] else "INACTIVE"
    print("=== EVYDÊNCIA Windows Shell Status ===")
    print(f"Modern Shell Extension (Sparse MSIX): {mod_state}")
    print(f"Classic Fallback (HKCU Registry):     {cls_state}")
    if status["classic_active"]:
        print(f"Classic Command: {status['command']}")
    print(f"Native DLL built:                      {'YES' if DLL_PATH.exists() else 'NO'}")
    print(f"Sparse MSIX packaged:                  {'YES' if MSIX_PATH.exists() else 'NO'}")
    return 0


def cmd_build() -> int:
    print("==> [1/2] Building Native Shell Extension DLL & Contract Tests...")
    res = subprocess.run([sys.executable, str(SCRIPTS_DIR / "build_shell_extension.py")])
    if res.returncode != 0:
        return res.returncode

    print("\n==> [2/2] Packaging & Signing Sparse MSIX...")
    proc = run_ps1("package_sparse_msix.ps1")
    print(proc.stdout)
    if proc.stderr:
        print(proc.stderr, file=sys.stderr)
    return proc.returncode


def cmd_install(mode: str) -> int:
    # Ensure build artifacts exist
    if not DLL_PATH.exists() or not MSIX_PATH.exists():
        print("Build artifacts missing. Building first...")
        code = cmd_build()
        if code != 0:
            return code

    if mode == "classic":
        print("Registering per-user classic shell fallback (HKCU)...")
        if register_classic_fallback(force=True):
            print("[SUCCESS] Classic shell fallback registered successfully!")
            return 0
        return 1

    if mode == "modern":
        print("Registering Modern Windows 11 Shell Extension (Sparse MSIX)...")
        proc = run_ps1("register_modern_shell.ps1")
        print(proc.stdout)
        if proc.stderr:
            print(proc.stderr, file=sys.stderr)
        return proc.returncode

    # mode == 'auto'
    print("Attempting Modern Windows 11 Shell Extension registration...")
    proc = run_ps1("register_modern_shell.ps1")
    print(proc.stdout)
    if proc.returncode == 0:
        # Modern succeeded! Clean up any duplicate classic verb
        unregister_classic_fallback()
        print("[SUCCESS] Windows 11 Modern Shell Extension is active.")
        return 0

    print("\nModern registration did not succeed in current trust context.")
    print("Enabling per-user classic fallback so context menu works immediately...")
    if register_classic_fallback(force=True):
        print(
            "[SUCCESS] Classic fallback active! "
            "Photos will display 'Gerar com EVYDÊNCIA' under context menu."
        )
        return 0
    return 1


def cmd_uninstall() -> int:
    print("Unregistering Windows Shell Integration...")
    # Unregister modern
    run_ps1("register_modern_shell.ps1", "-Uninstall")
    # Unregister classic
    unregister_classic_fallback()
    print("[SUCCESS] All shell registrations cleanly removed.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="EVYDÊNCIA Shell Extension Manager")
    subparsers = parser.add_subparsers(dest="action", required=True)

    subparsers.add_parser("status", help="Show current registration status")
    subparsers.add_parser("build", help="Build native DLL and sparse MSIX package")

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

    subparsers.add_parser("uninstall", help="Uninstall all shell integrations")

    args = parser.parse_args(argv)

    if args.action == "status":
        return cmd_status()
    elif args.action == "build":
        return cmd_build()
    elif args.action == "install":
        mode = "modern" if args.modern else ("classic" if args.classic else "auto")
        return cmd_install(mode)
    elif args.action == "uninstall":
        return cmd_uninstall()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
