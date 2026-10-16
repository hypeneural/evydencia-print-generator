"""Opt-in local EvydFlow recovery via its already-registered safe startup task.

Never spawn a worker or invoke powershell from untrusted input. The EvydFlow
boot script owns process mutexes/worker idempotence. When the startup task
refuses full-stack boot because a live worker already exists without an API
listener, fall back strictly to the canonical API-only supervisor in the same
verified worktree (never passing -AllowForceStop or -ReloadOwnedApi, and never
re-submitting a DRAFT). No physical print flags.
"""
from __future__ import annotations

import os
import stat
import subprocess
import time
from pathlib import Path

from .discovery import discover_panel_port

STARTUP_TASK_NAME = "EvydFlow - Iniciar Servicos ao Entrar"
CANONICAL_WORKTREE = Path(r"C:\Evydencia\evydflow-soclick-copies")
CANONICAL_RECOVER_API_SCRIPT = CANONICAL_WORKTREE / "services" / "recover-api.ps1"

CHECK_TASK = (
    "$t = Get-ScheduledTask -TaskName 'EvydFlow - Iniciar Servicos ao Entrar' "
    "-ErrorAction Stop; "
    "$a = @($t.Actions); "
    "$expected = 'C:\\Evydencia\\evydflow-soclick-copies\\services\\boot-evydflow.ps1'; "
    "$workingDir = 'C:\\Evydencia\\evydflow-soclick-copies'; "
    "if ($a.Count -ne 1) { exit 42 }; "
    "$action = $a[0]; "
    "if ($action.Execute -notmatch '(?i)powershell(\\.exe)?$' -or "
    "$action.WorkingDirectory -ine $workingDir -or "
    "$action.Arguments.IndexOf($expected, [StringComparison]::OrdinalIgnoreCase) -lt 0) "
    "{ exit 42 }; "
    "Write-Output 'VERIFIED'"
)


def is_windows_host() -> bool:
    return os.name == "nt"


def _is_verified_regular_script(path: Path) -> bool:
    """Confirm script exists inside canonical checkout and is not a link/reparse point."""
    try:
        st = os.lstat(path)
    except OSError:
        return False
    if not stat.S_ISREG(st.st_mode) or stat.S_ISLNK(st.st_mode):
        return False
    if getattr(st, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400):
        return False
    return True


def _try_api_only_supervisor(script_path: Path | None = None) -> str | None:
    """Run verified API-only supervisor without force-stop or reload flags."""
    target = script_path or CANONICAL_RECOVER_API_SCRIPT
    if not _is_verified_regular_script(target):
        return None
    cmd = [
        "powershell.exe",
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(target),
        "-Port",
        "8095",
        "-Json",
    ]
    res = subprocess.run(
        cmd,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        # The supervisor may wait up to 15s for the boot mutex and up to 20s
        # for the API to become healthy; 25s truncates a legitimate recovery.
        timeout=45,
        check=False,
    )
    if res.returncode == 0 and discover_panel_port() is not None:
        return "RUNNING"
    return "SUPERVISOR_REFUSED"


def recover_panel_from_scheduled_task() -> dict[str, object]:
    """Manual operator click only; returns no paths, tokens or process output."""
    if discover_panel_port() is not None:
        return {"ok": True, "state": "RUNNING"}
    if not is_windows_host():
        return {"ok": False, "state": "WINDOWS_ONLY"}
    try:
        verified = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", CHECK_TASK],
            capture_output=True, text=True, timeout=6, check=False,
        )
        if verified.returncode != 0 or verified.stdout.strip() != "VERIFIED":
            return {"ok": False, "state": "TASK_NOT_VERIFIED"}
        started = subprocess.run(
            ["schtasks.exe", "/Run", "/TN", STARTUP_TASK_NAME],
            capture_output=True, text=True, timeout=6, check=False,
        )
        if started.returncode != 0:
            return {"ok": False, "state": "TASK_START_FAILED"}
        for _ in range(5):
            if discover_panel_port() is not None:
                return {"ok": True, "state": "RUNNING"}
            time.sleep(1)

        # If the scheduled task ran but the API is still down (e.g. boot-evydflow.ps1
        # refused to start a full stack because a queue worker is already alive),
        # attempt the canonical API-only supervisor from the same verified worktree.
        sup_state = _try_api_only_supervisor()
        if sup_state == "RUNNING":
            return {"ok": True, "state": "RUNNING"}
        if sup_state == "SUPERVISOR_REFUSED":
            return {"ok": False, "state": "SUPERVISOR_REFUSED"}
        return {"ok": False, "state": "STARTING"}
    except (OSError, subprocess.TimeoutExpired):
        return {"ok": False, "state": "TASK_START_FAILED"}
