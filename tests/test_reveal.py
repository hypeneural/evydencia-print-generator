"""Tests for reveal_in_explorer Windows shell helper."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from evydencia_print_generator.windows.reveal import reveal_in_explorer


def test_reveal_nonexistent_file_returns_false(tmp_path: Path) -> None:
    non_existent = tmp_path / "does_not_exist.png"
    assert reveal_in_explorer(non_existent) is False


def test_reveal_non_nt_platform(tmp_path: Path) -> None:
    test_file = tmp_path / "dummy.png"
    test_file.write_text("dummy")
    with patch("os.name", "posix"):
        assert reveal_in_explorer(test_file) is False


def test_reveal_subprocess_fallback(tmp_path: Path) -> None:
    test_file = tmp_path / "dummy.png"
    test_file.write_text("dummy")

    with patch("os.name", "nt"), \
         patch("ctypes.windll", side_effect=Exception("COM failure")), \
         patch("subprocess.Popen") as mock_popen:
        result = reveal_in_explorer(test_file)
        assert result is True
        mock_popen.assert_called_once()
        args = mock_popen.call_args[0][0]
        assert args[0] == "explorer.exe"
        assert f"/select,{test_file.resolve()}" in args[1]


def test_reveal_both_methods_fail(tmp_path: Path) -> None:
    test_file = tmp_path / "dummy.png"
    test_file.write_text("dummy")

    with patch("os.name", "nt"), \
         patch("ctypes.windll", side_effect=Exception("COM failure")), \
         patch("subprocess.Popen", side_effect=OSError("File not found")):
        result = reveal_in_explorer(test_file)
        assert result is False
