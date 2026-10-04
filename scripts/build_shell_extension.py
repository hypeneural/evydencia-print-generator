#!/usr/bin/env python3
"""Build and verify the native Windows Shell Extension (C++20 x64 COM DLL)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHELL_DIR = ROOT / "native" / "windows-shell"
BUILD_DIR = SHELL_DIR / "build"


def find_cmake() -> str:
    which = shutil.which("cmake")
    if which:
        return which
    candidates = [
        Path(r"C:\Program Files\CMake\bin\cmake.exe"),
        Path(r"C:\Program Files (x86)\CMake\bin\cmake.exe"),
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    raise RuntimeError("CMake executable not found. Please install CMake or add it to PATH.")


def build_and_test() -> int:
    cmake = find_cmake()
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    print("==> [1/3] Configuring CMake (Visual Studio 16 2019 x64)...")
    config_cmd = [
        cmake,
        "-B",
        str(BUILD_DIR),
        "-S",
        str(SHELL_DIR),
        "-G",
        "Visual Studio 16 2019",
        "-A",
        "x64",
    ]
    res = subprocess.run(config_cmd, cwd=SHELL_DIR)
    if res.returncode != 0:
        return res.returncode

    print("\n==> [2/3] Building Release configuration...")
    build_cmd = [cmake, "--build", str(BUILD_DIR), "--config", "Release"]
    res = subprocess.run(build_cmd, cwd=SHELL_DIR)
    if res.returncode != 0:
        return res.returncode

    dll_path = BUILD_DIR / "Release" / "EvydenciaShellExtension.dll"
    if not dll_path.exists():
        print(f"ERROR: Expected DLL not found at {dll_path}")
        return 1
    print(f"OK: DLL built successfully ({dll_path.stat().st_size} bytes)")

    print("\n==> [3/3] Running Native COM Contract Test...")
    test_exe = BUILD_DIR / "Release" / "test_shell_extension.exe"
    res = subprocess.run([str(test_exe)], cwd=BUILD_DIR)
    if res.returncode != 0:
        return res.returncode

    print("\n[SUCCESS] Native Windows Shell Extension built and verified!")
    return 0


if __name__ == "__main__":
    raise SystemExit(build_and_test())
