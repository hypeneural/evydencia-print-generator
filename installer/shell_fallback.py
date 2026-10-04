"""Per-user classic shell verb fallback and dual-registration guard.

Registers a per-user verb in HKCU\\Software\\Classes\\*\\shell\\EvydenciaPrintGenerator
with AppliesTo extension filtering (.jpg, .jpeg, .png).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import TypedDict

if sys.platform == "win32":
    import winreg
else:
    winreg = None  # type: ignore[assignment]

VERB_KEY = r"Software\Classes\*\shell\EvydenciaPrintGenerator"
COMMAND_KEY = rf"{VERB_KEY}\command"
VERB_TITLE = "Gerar com EVYDÊNCIA"
APPLIES_TO = (
    "System.FileExtension:=.jpg OR "
    "System.FileExtension:=.jpeg OR "
    "System.FileExtension:=.png"
)


class ShellStatus(TypedDict):
    modern_active: bool
    classic_active: bool
    command: str | None


def is_modern_extension_active() -> bool:
    """Check if the modern sparse MSIX package is registered for the current user."""
    try:
        ps_query = (
            "Get-AppxPackage -Name Evydencia.PrintGenerator "
            "| Select-Object -ExpandProperty PackageFullName"
        )
        cmd = ["powershell", "-NoProfile", "-Command", ps_query]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        return bool(result.stdout.strip())
    except Exception:
        return False


def get_launcher_command() -> str:
    """Construct the command string to launch the app GUI."""
    # Check if a custom launcher executable exists
    repo_root = Path(__file__).resolve().parents[1]
    local_app_data = Path(os.environ.get("LOCALAPPDATA", ""))
    installed_exe = (
        local_app_data / "EVYDENCIA" / "PrintGenerator" / "EvydenciaPrintGenerator.exe"
    )
    adjacent_exe = (
        repo_root / "native" / "windows-shell" / "build" / "Release" / "EvydenciaPrintGenerator.exe"
    )

    if installed_exe.exists():
        return f'"{installed_exe}" --gui "%1"'
    if adjacent_exe.exists():
        return f'"{adjacent_exe}" --gui "%1"'

    # Python development fallback
    python_exe = sys.executable
    return f'"{python_exe}" -m evydencia_print_generator --gui "%1"'


def is_classic_fallback_active() -> bool:
    """Check if the classic per-user registry verb is registered."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, COMMAND_KEY, 0, winreg.KEY_READ) as key:
            val, _ = winreg.QueryValueEx(key, "")
            return bool(val)
    except FileNotFoundError:
        return False
    except OSError:
        return False


def get_current_classic_command() -> str | None:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, COMMAND_KEY, 0, winreg.KEY_READ) as key:
            val, _ = winreg.QueryValueEx(key, "")
            return str(val)
    except OSError:
        return None


def register_classic_fallback(force: bool = False, custom_command: str | None = None) -> bool:
    """Register the per-user classic shell verb.

    If modern extension is active and force is False, registration is skipped
    to prevent duplicate menu items in Windows 11.
    """
    if not force and is_modern_extension_active():
        print(
            "Notice: Modern Windows 11 Shell Extension is active. "
            "Skipping classic registration to avoid duplication."
        )
        return False

    cmd_str = custom_command or get_launcher_command()

    try:
        # Create or open verb key
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, VERB_KEY) as vkey:
            winreg.SetValueEx(vkey, "", 0, winreg.REG_SZ, VERB_TITLE)
            winreg.SetValueEx(vkey, "MUIVerb", 0, winreg.REG_SZ, VERB_TITLE)
            winreg.SetValueEx(vkey, "AppliesTo", 0, winreg.REG_SZ, APPLIES_TO)

            # Icon
            python_exe = sys.executable
            winreg.SetValueEx(vkey, "Icon", 0, winreg.REG_SZ, python_exe)

        # Create command subkey
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, COMMAND_KEY) as ckey:
            winreg.SetValueEx(ckey, "", 0, winreg.REG_SZ, cmd_str)

        return True
    except OSError as err:
        print(f"Error registering classic shell verb: {err}")
        return False


def unregister_classic_fallback() -> bool:
    """Recursively delete the classic shell verb from HKCU."""
    try:
        # Delete subkey first
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, COMMAND_KEY)
        except FileNotFoundError:
            pass
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, VERB_KEY)
        except FileNotFoundError:
            pass
        return True
    except OSError as err:
        print(f"Error unregistering classic shell verb: {err}")
        return False


def get_shell_status() -> ShellStatus:
    return {
        "modern_active": is_modern_extension_active(),
        "classic_active": is_classic_fallback_active(),
        "command": get_current_classic_command(),
    }
