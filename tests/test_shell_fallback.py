"""Tests for classic shell fallback and dual-registration guard."""

from __future__ import annotations

import sys
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows only test suite")

if sys.platform == "win32":
    import winreg
else:
    winreg = None  # type: ignore[assignment]

from installer.shell_fallback import (  # noqa: E402
    APPLIES_TO,
    COMMAND_KEY,
    VERB_KEY,
    VERB_TITLE,
    get_launcher_command,
    get_shell_status,
    is_classic_fallback_active,
    register_classic_fallback,
    unregister_classic_fallback,
)


def test_constants_and_command_format() -> None:
    assert VERB_TITLE == "Gerar com EVYDÊNCIA"
    assert ".jpg" in APPLIES_TO
    assert ".jpeg" in APPLIES_TO
    assert ".png" in APPLIES_TO

    cmd = get_launcher_command()
    assert "--gui" in cmd
    assert '"%1"' in cmd


def test_classic_registration_lifecycle() -> None:
    # Ensure starting clean
    unregister_classic_fallback()
    assert not is_classic_fallback_active()

    # Register
    ok = register_classic_fallback(force=True, custom_command='"dummy.exe" --gui "%1"')
    assert ok is True
    assert is_classic_fallback_active() is True

    # Verify keys directly in HKCU
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, VERB_KEY, 0, winreg.KEY_READ) as key:
        title, _ = winreg.QueryValueEx(key, "MUIVerb")
        assert title == VERB_TITLE
        applies, _ = winreg.QueryValueEx(key, "AppliesTo")
        assert applies == APPLIES_TO

    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, COMMAND_KEY, 0, winreg.KEY_READ) as key:
        cmd_val, _ = winreg.QueryValueEx(key, "")
        assert cmd_val == '"dummy.exe" --gui "%1"'

    # Status helper
    status = get_shell_status()
    assert status["classic_active"] is True
    assert status["command"] == '"dummy.exe" --gui "%1"'

    # Clean unregister
    assert unregister_classic_fallback() is True
    assert not is_classic_fallback_active()


def test_dual_registration_guard_skips_when_modern_active() -> None:
    with patch("installer.shell_fallback.is_modern_extension_active", return_value=True):
        # Without force, registration should be skipped
        res = register_classic_fallback(force=False)
        assert res is False
