"""Opt-in local EvydFlow recovery via its already-registered safe startup task.

Never spawn a worker or invoke powershell from untrusted input. The EvydFlow
boot script owns process mutexes/worker idempotence. No physical print flags.
"""
from __future__ import annotations

import os
import subprocess
import time

from .discovery import discover_panel_port

STARTUP_TASK_NAME = "EvydFlow - Iniciar Servicos ao Entrar"
CHECK_TASK = (
    "$t = Get-ScheduledTask -TaskName 'EvydFlow - Iniciar Servicos ao Entrar' "
    "-ErrorAction Stop; "
    "$a = @($t.Actions); "
    "if ($a.Count -ne 1 -or "
    "$a[0].Execute -notmatch '(?i)powershell(\\.exe)?$' -or "
    "$a[0].Arguments -notmatch 'boot-evydflow\\.ps1') { exit 42 }; "
    "Write-Output 'VERIFIED'"
)


def recover_panel_from_scheduled_task() -> dict[str, object]:
    """Manual operator click only; returns no paths, tokens or process output."""
    if discover_panel_port() is not None:
        return {"ok": True, "state": "RUNNING"}
    if os.name != "nt":
        return {"ok": False, "state": "WINDOWS_ONLY"}
    try:
        verified = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", CHECK_TASK],
            capture_output=True, text=True, timeout=6, check=False,
        )
        if verified.returncode != 0 or verified.stdout.strip() != "VERIFIED":
            return {"ok": False, "state": "TASK_NOT_VERIFIED"}
        # Existing task is the only authorized starter. The task's bootstrap
        # owns the EvydFlowStartup8095 mutex and checks running worker PIDs.
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
        return {"ok": False, "state": "STARTING"}
    except (OSError, subprocess.TimeoutExpired):
        return {"ok": False, "state": "TASK_START_FAILED"}
