#!/usr/bin/env python3
"""Build and verify the native Windows Shell Extension (C++20 x64 COM DLL + Launcher).

Auto-detects installed Visual Studio / MSVC Build Tools and x64 toolchain.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHELL_DIR = ROOT / "native" / "windows-shell"
BUILD_DIR = SHELL_DIR / "build"
ASSETS_DIR = SHELL_DIR / "assets"
ICO_PATH = ASSETS_DIR / "app.ico"


def find_cmake() -> str:
    which = shutil.which("cmake")
    if which:
        return which
    candidates = [
        Path(r"C:\Program Files\CMake\bin\cmake.exe"),
        Path(r"C:\Program Files (x86)\CMake\bin\cmake.exe"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    raise RuntimeError("CMake executable not found. Please install CMake or add it to PATH.")


def probe_vswhere() -> dict | None:
    """Detect installed Visual Studio / Build Tools using vswhere.exe."""
    program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    vswhere_path = Path(program_files_x86) / "Microsoft Visual Studio" / "Installer" / "vswhere.exe"
    if not vswhere_path.exists():
        return None

    try:
        cmd = [
            str(vswhere_path),
            "-latest",
            "-products",
            "*",
            "-requires",
            "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
            "-format",
            "json",
            "-utf8",
        ]
        out = subprocess.check_output(cmd, text=True, errors="replace")
        data = json.loads(out)
        if data and isinstance(data, list):
            return data[0]
    except Exception:
        pass
    return None


def detect_vs_generators(cmake_bin: str) -> list[str]:
    """Auto-detect available Visual Studio CMake generators in preferred order."""
    env_gen = os.environ.get("CMAKE_GENERATOR")
    if env_gen:
        return [env_gen]

    preferred = ["Visual Studio 17 2022", "Visual Studio 16 2019"]
    try:
        out = subprocess.check_output([cmake_bin, "--help"], text=True, errors="replace")
        available = []
        for line in out.splitlines():
            line_s = line.strip().lstrip("*").strip()
            if line_s.startswith("Visual Studio") and "=" in line_s:
                name = line_s.split("=")[0].strip()
                name = name.split("[")[0].strip()
                available.append(name)

        ordered = [item for item in preferred if item in available]
        for item in available:
            if item not in ordered:
                ordered.append(item)
        if ordered:
            return ordered
    except Exception:
        pass

    return preferred


def ensure_icon() -> None:
    """Ensure the dedicated app.ico exists without regenerating an existing asset."""
    if ICO_PATH.exists():
        size = ICO_PATH.stat().st_size
        print(f"==> Using deterministic versioned icon: {ICO_PATH} ({size} bytes)")
        return

    pkg_ico = SHELL_DIR / "package" / "Assets" / "app.ico"
    if pkg_ico.exists():
        ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(pkg_ico, ICO_PATH)
        print(f"==> Copied icon to canonical location: {ICO_PATH}")
        return

    print("==> Generating EVYDÊNCIA icon resource...")
    gen_script = ROOT / "scripts" / "generate_app_ico.py"
    subprocess.check_call([sys.executable, str(gen_script)])
    if pkg_ico.exists():
        ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(pkg_ico, ICO_PATH)


def build_and_test() -> int:
    cmake = find_cmake()
    ensure_icon()
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    vs_info = probe_vswhere()
    if vs_info:
        print("\n=== Detected C++ Toolchain (MSVC x64) ===")
        print(f"  Display Name : {vs_info.get('displayName')}")
        print(f"  Version      : {vs_info.get('installationVersion')}")
        print(f"  Path         : {vs_info.get('installationPath')}")
    else:
        print("\n=== C++ Toolchain: probing CMake generators directly ===")

    generators = detect_vs_generators(cmake)
    configured = False

    for generator in generators:
        print(f"==> [1/3] Configuring CMake ({generator} -A x64)...")
        config_cmd = [
            cmake,
            "-B",
            str(BUILD_DIR),
            "-S",
            str(SHELL_DIR),
            "-G",
            generator,
            "-A",
            "x64",
        ]
        res = subprocess.run(config_cmd, cwd=SHELL_DIR)
        if res.returncode == 0:
            configured = True
            break
        print(f"Notice: Generator '{generator}' failed to configure, trying next...")
        shutil.rmtree(BUILD_DIR / "CMakeFiles", ignore_errors=True)
        if (BUILD_DIR / "CMakeCache.txt").exists():
            (BUILD_DIR / "CMakeCache.txt").unlink(missing_ok=True)

    if not configured:
        print("ERROR: Failed to configure CMake with any available Visual Studio generator.")
        return 1

    print("\n==> [2/3] Building Release configuration (x64)...")
    build_cmd = [cmake, "--build", str(BUILD_DIR), "--config", "Release"]
    res = subprocess.run(build_cmd, cwd=SHELL_DIR)
    if res.returncode != 0:
        return res.returncode

    dll_path = BUILD_DIR / "Release" / "EvydenciaShellExtension.dll"
    exe_path = BUILD_DIR / "Release" / "EvydenciaPrintGenerator.exe"

    if not dll_path.exists():
        print(f"ERROR: Expected DLL not found at {dll_path}")
        return 1
    print(f"OK: Shell Extension DLL built: {dll_path} ({dll_path.stat().st_size} bytes)")

    if not exe_path.exists():
        print(f"ERROR: Expected launcher executable not found at {exe_path}")
        return 1
    print(f"OK: Launcher executable built: {exe_path} ({exe_path.stat().st_size} bytes)")

    print("\n==> [3/3] Running Native COM Contract Tests...")
    test_exe = BUILD_DIR / "Release" / "test_shell_extension.exe"
    res = subprocess.run([str(test_exe)], cwd=BUILD_DIR)
    if res.returncode != 0:
        return res.returncode

    print("\n[SUCCESS] Native Windows Shell Extension and Launcher built and contract-verified!")
    return 0


if __name__ == "__main__":
    raise SystemExit(build_and_test())
