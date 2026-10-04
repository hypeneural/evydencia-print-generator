"""Tests for manage_shell_extension CLI and validation states."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows only test suite")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.manage_shell_extension import (  # noqa: E402
    cmd_clean_classic,
    cmd_status,
    cmd_validate_ui,
    get_ui_validation_state,
)


def test_ui_validation_state_lifecycle(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    marker = tmp_path / ".test_ui_validation"
    monkeypatch.setattr("scripts.manage_shell_extension.VALIDATION_MARKER", marker)

    assert get_ui_validation_state() == "PENDING"

    cmd_validate_ui("pass")
    assert get_ui_validation_state() == "PASSED"

    cmd_validate_ui("fail")
    assert get_ui_validation_state() == "FAILED"

    cmd_validate_ui("reset")
    assert get_ui_validation_state() == "PENDING"


def test_clean_classic_requires_passed_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    marker = tmp_path / ".test_ui_validation"
    monkeypatch.setattr("scripts.manage_shell_extension.VALIDATION_MARKER", marker)

    assert get_ui_validation_state() == "PENDING"
    assert cmd_clean_classic(force=False) == 1

    with patch("scripts.manage_shell_extension.unregister_classic_fallback", return_value=True):
        assert cmd_clean_classic(force=True) == 0

    cmd_validate_ui("pass")
    assert get_ui_validation_state() == "PASSED"
    with patch("scripts.manage_shell_extension.unregister_classic_fallback", return_value=True):
        assert cmd_clean_classic(force=False) == 0


def test_cmd_status_runs_cleanly(capsys: pytest.CaptureFixture[str]) -> None:
    code = cmd_status()
    assert code == 0
    captured = capsys.readouterr()
    assert "MODERN_PACKAGE_REGISTERED:" in captured.out
    assert "MODERN_RUNTIME_LAYOUT_OK:" in captured.out
    assert "MODERN_TRUST_OK:" in captured.out
    assert "MODERN_UI_VALIDATION:" in captured.out
    assert "CLASSIC_REGISTERED:" in captured.out
