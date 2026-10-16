"""Automatic local recovery happens *before* any SóClick intake POST.

An unreachable local API may be started once. Ambiguous POST outcomes are never
retried because an API can commit the DRAFT before a socket timeout.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from evydencia_print_generator.app.bridge import DesktopBridge


def _bridge(tmp_path: Path):
    bridge = DesktopBridge.__new__(DesktopBridge)
    output = tmp_path / "render.jpg"
    output.write_bytes(b"synthetic-render")
    receipt = SimpleNamespace(
        output_path=output,
        sha256="abc123",
        verify=lambda *args: object(),
    )
    bridge._last_render_receipt = receipt
    return bridge, output


def test_prepare_recovers_offline_panel_before_single_draft_post(tmp_path):
    bridge, output = _bridge(tmp_path)
    response = {"ok": True, "job_id": "job_synthetic_1"}
    with (
        patch("evydencia_print_generator.app.bridge.EditState.from_ui", return_value=object()),
        patch("evydencia_print_generator.soclick.discovery.discover_panel_port", return_value=None),
        patch(
            "evydencia_print_generator.soclick.recovery.recover_panel_from_scheduled_task",
            return_value={"ok": True, "state": "RUNNING"},
        ) as recover,
        patch(
            "evydencia_print_generator.soclick.prepare_soclic_draft",
            return_value=response,
        ) as send,
    ):
        result = bridge.prepare_soclic({"output_path": str(output)}, {})
    assert result == response
    recover.assert_called_once_with()
    send.assert_called_once()
    assert send.call_args.kwargs["expected_sha256"] == "abc123"


def test_prepare_fails_closed_without_post_when_recovery_is_refused(tmp_path):
    bridge, output = _bridge(tmp_path)
    with (
        patch("evydencia_print_generator.app.bridge.EditState.from_ui", return_value=object()),
        patch("evydencia_print_generator.soclick.discovery.discover_panel_port", return_value=None),
        patch(
            "evydencia_print_generator.soclick.recovery.recover_panel_from_scheduled_task",
            return_value={"ok": False, "state": "SUPERVISOR_REFUSED"},
        ),
        patch("evydencia_print_generator.soclick.prepare_soclic_draft") as send,
    ):
        result = bridge.prepare_soclic({"output_path": str(output)}, {})
    assert result["ok"] is False
    assert result["error_code"] == "PANEL_OFFLINE"
    send.assert_not_called()


def test_prepare_uses_healthy_panel_without_restarting_services(tmp_path):
    bridge, output = _bridge(tmp_path)
    with (
        patch("evydencia_print_generator.app.bridge.EditState.from_ui", return_value=object()),
        patch("evydencia_print_generator.soclick.discovery.discover_panel_port", return_value=8095),
        patch(
            "evydencia_print_generator.soclick.recovery.recover_panel_from_scheduled_task"
        ) as recover,
        patch(
            "evydencia_print_generator.soclick.prepare_soclic_draft",
            return_value={"ok": True},
        ) as send,
    ):
        result = bridge.prepare_soclic({"output_path": str(output)}, {})
    assert result["ok"] is True
    recover.assert_not_called()
    send.assert_called_once()
