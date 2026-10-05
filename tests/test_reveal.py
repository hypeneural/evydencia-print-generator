"""Tests for reveal_in_explorer Windows shell helper."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from evydencia_print_generator.windows.reveal import reveal_in_explorer


def test_reveal_nonexistent_file_returns_false(tmp_path: Path) -> None:
    non_existent = tmp_path / "does_not_exist.png"
    assert reveal_in_explorer(non_existent) is False


def test_reveal_non_nt_platform(tmp_path: Path) -> None:
    test_file = tmp_path / "dummy.png"
    test_file.write_text("dummy")
    with patch("evydencia_print_generator.windows.reveal.os.name", "posix"):
        assert reveal_in_explorer(test_file) is False


@pytest.mark.skipif(sys.platform != "win32", reason="Windows shell tests require Windows OS")
def test_reveal_subprocess_fallback(tmp_path: Path) -> None:
    test_file = tmp_path / "dummy.png"
    test_file.write_text("dummy")

    with patch("ctypes.windll", side_effect=Exception("COM failure")), \
         patch("subprocess.Popen") as mock_popen:
        result = reveal_in_explorer(test_file)
        assert result is True
        mock_popen.assert_called_once()
        args = mock_popen.call_args[0][0]
        assert args[0] == "explorer.exe"
        assert f"/select,{test_file.resolve()}" in args[1]


@pytest.mark.skipif(sys.platform != "win32", reason="Windows shell tests require Windows OS")
def test_reveal_both_methods_fail(tmp_path: Path) -> None:
    test_file = tmp_path / "dummy.png"
    test_file.write_text("dummy")

    with patch("ctypes.windll", side_effect=Exception("COM failure")), \
         patch("subprocess.Popen", side_effect=OSError("File not found")):
        result = reveal_in_explorer(test_file)
        assert result is False


@pytest.mark.skipif(sys.platform != "win32", reason="Windows shell tests require Windows OS")
def test_reveal_path_with_spaces_and_unicode(tmp_path: Path) -> None:
    sub_dir = tmp_path / "Fotos com Espaço e Acentuação — São João"
    sub_dir.mkdir(parents=True, exist_ok=True)
    test_file = sub_dir / "Produção 01 final.jpg"
    test_file.write_text("test")

    with patch("ctypes.windll", side_effect=Exception("Trigger fallback")), \
         patch("subprocess.Popen") as mock_popen:
        result = reveal_in_explorer(test_file)
        assert result is True
        mock_popen.assert_called_once()
        args = mock_popen.call_args[0][0]
        assert args[0] == "explorer.exe"
        assert f"/select,{test_file.resolve()}" in args[1]


@pytest.mark.skipif(sys.platform != "win32", reason="Windows shell tests require Windows OS")
def test_reveal_shell_api_success_path(tmp_path: Path) -> None:
    test_file = tmp_path / "photo.jpg"
    test_file.write_text("data")

    # Mock ctypes.windll with simulated successful COM / Shell calls
    mock_ole32 = MagicMock()
    mock_ole32.CoInitializeEx.return_value = 0  # S_OK
    mock_ole32.CoTaskMemFree.return_value = None
    mock_ole32.CoUninitialize.return_value = None

    mock_shell32 = MagicMock()
    # Simulate SHParseDisplayName assigning valid pointer values (returns S_OK = 0)
    def fake_parse(path, pbc, ppidl, sfgao, psfgao):
        ppidl._obj.value = 0x12345678  # Assign non-null pointer address
        return 0

    mock_shell32.SHParseDisplayName.side_effect = fake_parse
    mock_shell32.ILFindLastID.return_value = 0x12345678
    mock_shell32.SHOpenFolderAndSelectItems.return_value = 0  # S_OK

    mock_windll = MagicMock()
    mock_windll.ole32 = mock_ole32
    mock_windll.shell32 = mock_shell32

    with patch("ctypes.windll", mock_windll), \
         patch("subprocess.Popen") as mock_popen:
        result = reveal_in_explorer(test_file)
        assert result is True
        mock_shell32.SHOpenFolderAndSelectItems.assert_called_once()
        assert mock_ole32.CoTaskMemFree.call_count == 2
        mock_ole32.CoUninitialize.assert_called_once()
        # Fallback should NOT have been invoked
        mock_popen.assert_not_called()
