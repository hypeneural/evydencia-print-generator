"""Staging & scheduled-task recovery: no production side effects in tests."""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import pytest
from evydencia_print_generator.soclick import recovery, staging


def _jpg(tmp_path: Path, name: str = "Calendario_FOTO_001.jpg") -> tuple[Path, str]:
    from PIL import Image

    source = tmp_path / "downloads" / "outside-authorized-root" / name
    source.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (16, 16), "#e8bd79").save(source, "JPEG", dpi=(300, 300))
    return source, hashlib.sha256(source.read_bytes()).hexdigest()


def test_arbitrary_source_is_staged_without_changing_original(monkeypatch, tmp_path):
    jpeg, sha = _jpg(tmp_path)
    root = tmp_path / "controlled-handoff"
    monkeypatch.setenv("EVYDENCIA_SOCLICK_HANDOFF_DIR", str(root))
    before = jpeg.read_bytes()

    staged = staging.stage_verified_jpeg(jpeg, sha)
    assert staged != jpeg
    assert root.resolve() in staged.parents
    assert staged.name == jpeg.name
    assert staged.read_bytes() == before
    assert jpeg.read_bytes() == before
    assert staging.stage_verified_jpeg(jpeg, sha) == staged  # safe replay


def test_reject_modified_or_colliding_staged_file(monkeypatch, tmp_path):
    jpeg, sha = _jpg(tmp_path)
    root = tmp_path / "allowed"
    monkeypatch.setenv("EVYDENCIA_SOCLICK_HANDOFF_DIR", str(root))
    with pytest.raises(staging.StagingError):
        staging.stage_verified_jpeg(jpeg, "0" * 64)
    target = staging.stage_verified_jpeg(jpeg, sha)
    target.write_bytes(b"wrong")
    with pytest.raises(staging.StagingError):
        staging.stage_verified_jpeg(jpeg, sha)
    assert jpeg.read_bytes() != b"wrong"


def test_offline_recovery_never_starts_task_when_api_healthy(monkeypatch):
    monkeypatch.setattr(recovery, "discover_panel_port", lambda: 8095)
    monkeypatch.setattr(recovery.subprocess, "run", lambda *a, **kw: pytest.fail("unexpected"))
    assert recovery.recover_panel_from_scheduled_task() == {"ok": True, "state": "RUNNING"}


def test_task_not_verified_does_not_launch_worker(monkeypatch):
    monkeypatch.setattr(recovery, "discover_panel_port", lambda: None)
    monkeypatch.setattr(recovery, "is_windows_host", lambda: True)
    calls = []
    def fake_run(args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 42, stdout="")
    monkeypatch.setattr(recovery.subprocess, "run", fake_run)
    assert recovery.recover_panel_from_scheduled_task()["state"] == "TASK_NOT_VERIFIED"
    assert len(calls) == 1


def test_explicit_recovery_only_uses_registered_task(monkeypatch):
    monkeypatch.setattr(recovery, "is_windows_host", lambda: True)
    probes = iter([None, None, 8095])
    monkeypatch.setattr(recovery, "discover_panel_port", lambda: next(probes))
    calls = []
    def fake_run(args, **kwargs):
        calls.append(args)
        if args[0] == "powershell.exe":
            return subprocess.CompletedProcess(args, 0, stdout="VERIFIED\n")
        return subprocess.CompletedProcess(args, 0, stdout="SUCCESS")
    monkeypatch.setattr(recovery.subprocess, "run", fake_run)
    monkeypatch.setattr(recovery.time, "sleep", lambda _: None)
    assert recovery.recover_panel_from_scheduled_task() == {"ok": True, "state": "RUNNING"}
    assert len(calls) == 2
    assert calls[1] == ["schtasks.exe", "/Run", "/TN", recovery.STARTUP_TASK_NAME]


def test_recovery_falls_back_to_verified_api_only_supervisor_without_force_stop(
    monkeypatch, tmp_path
):
    script = tmp_path / "recover-api.ps1"
    script.write_text("# mock supervisor\n", encoding="utf-8")
    monkeypatch.setattr(recovery, "CANONICAL_RECOVER_API_SCRIPT", script)
    monkeypatch.setattr(recovery, "is_windows_host", lambda: True)
    # 1 initial check + 5 post-schtasks checks return None, then supervisor check returns 8095
    probes = iter([None, None, None, None, None, None, 8095])
    monkeypatch.setattr(recovery, "discover_panel_port", lambda: next(probes))
    monkeypatch.setattr(recovery.time, "sleep", lambda _: None)
    calls = []

    def fake_run(args, **kwargs):
        calls.append(args)
        if "-Command" in args:
            return subprocess.CompletedProcess(args, 0, stdout="VERIFIED\n")
        if args[0] == "schtasks.exe":
            return subprocess.CompletedProcess(args, 0, stdout="SUCCESS")
        return subprocess.CompletedProcess(
            args, 0, stdout='{"ok":true,"status":"RECOVERED_API_ONLY"}\n'
        )

    monkeypatch.setattr(recovery.subprocess, "run", fake_run)
    assert recovery.recover_panel_from_scheduled_task() == {"ok": True, "state": "RUNNING"}
    assert len(calls) == 3
    sup_args = calls[2]
    assert "-File" in sup_args
    assert str(script) in sup_args
    assert "-AllowForceStop" not in sup_args
    assert "-ReloadOwnedApi" not in sup_args


def test_recovery_reports_supervisor_refused_when_api_only_fails_closed(
    monkeypatch, tmp_path
):
    script = tmp_path / "recover-api.ps1"
    script.write_text("# mock supervisor\n", encoding="utf-8")
    monkeypatch.setattr(recovery, "CANONICAL_RECOVER_API_SCRIPT", script)
    monkeypatch.setattr(recovery, "is_windows_host", lambda: True)
    monkeypatch.setattr(recovery, "discover_panel_port", lambda: None)
    monkeypatch.setattr(recovery.time, "sleep", lambda _: None)

    def fake_run(args, **kwargs):
        if "-Command" in args:
            return subprocess.CompletedProcess(args, 0, stdout="VERIFIED\n")
        if args[0] == "schtasks.exe":
            return subprocess.CompletedProcess(args, 0, stdout="SUCCESS")
        return subprocess.CompletedProcess(args, 2, stdout='{"ok":false,"status":"NO_GO"}\n')

    monkeypatch.setattr(recovery.subprocess, "run", fake_run)
    assert recovery.recover_panel_from_scheduled_task() == {
        "ok": False,
        "state": "SUPERVISOR_REFUSED",
    }

