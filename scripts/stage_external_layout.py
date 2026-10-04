#!/usr/bin/env python3
"""Stage the deterministic external runtime layout for EVYDÊNCIA Sparse MSIX package.

Ensures that ExternalLocation contains all binaries and assets referenced
by AppxManifest.xml, serving as a BLOCKER gate before MSIX registration.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHELL_DIR = ROOT / "native" / "windows-shell"
BUILD_RELEASE = SHELL_DIR / "build" / "Release"
PKG_ASSETS = SHELL_DIR / "package" / "Assets"
CANONICAL_ASSETS = SHELL_DIR / "assets"

STAGE_DIR = ROOT / "dist" / "windows"
STAGE_ASSETS = STAGE_DIR / "Assets"


def stage_layout() -> Path:
    print(f"==> Staging deterministic external layout to: {STAGE_DIR}")
    STAGE_DIR.mkdir(parents=True, exist_ok=True)
    STAGE_ASSETS.mkdir(parents=True, exist_ok=True)

    # 1. Copy DLL
    src_dll = BUILD_RELEASE / "EvydenciaShellExtension.dll"
    if not src_dll.exists():
        raise RuntimeError(f"BLOCKER: Native DLL missing at {src_dll}. Run build_shell_extension.py first.")
    dst_dll = STAGE_DIR / "EvydenciaShellExtension.dll"
    shutil.copy2(src_dll, dst_dll)

    # 2. Copy Launcher
    src_exe = BUILD_RELEASE / "EvydenciaPrintGenerator.exe"
    if not src_exe.exists():
        raise RuntimeError(f"BLOCKER: Launcher exe missing at {src_exe}. Run build_shell_extension.py first.")
    dst_exe = STAGE_DIR / "EvydenciaPrintGenerator.exe"
    shutil.copy2(src_exe, dst_exe)

    # 3. Copy Assets
    assets_to_copy = [
        (CANONICAL_ASSETS / "app.ico", STAGE_ASSETS / "app.ico"),
        (PKG_ASSETS / "Square150x150Logo.png", STAGE_ASSETS / "Square150x150Logo.png"),
        (PKG_ASSETS / "Square44x44Logo.png", STAGE_ASSETS / "Square44x44Logo.png"),
        (PKG_ASSETS / "StoreLogo.png", STAGE_ASSETS / "StoreLogo.png"),
    ]

    for src, dst in assets_to_copy:
        if not src.exists():
            raise RuntimeError(f"BLOCKER: Required asset missing at {src}")
        shutil.copy2(src, dst)

    # 4. Verification Gate (Hard stop if any required file is missing or empty)
    required_files = [
        dst_dll,
        dst_exe,
        STAGE_ASSETS / "app.ico",
        STAGE_ASSETS / "Square150x150Logo.png",
        STAGE_ASSETS / "Square44x44Logo.png",
        STAGE_ASSETS / "StoreLogo.png",
    ]

    print("\n=== Validating Staged External Layout ===")
    for rf in required_files:
        if not rf.exists():
            raise RuntimeError(f"BLOCKER: Staged file not found: {rf}")
        sz = rf.stat().st_size
        if sz == 0:
            raise RuntimeError(f"BLOCKER: Staged file is empty: {rf}")
        rel = rf.relative_to(STAGE_DIR)
        print(f"  [OK] {rel} ({sz} bytes)")

    print(f"\n[GATE PASS] External layout successfully staged and verified at {STAGE_DIR}\n")
    return STAGE_DIR


if __name__ == "__main__":
    try:
        stage_layout()
    except Exception as exc:
        print(f"\n[GATE FAIL] {exc}", file=sys.stderr)
        sys.exit(1)
