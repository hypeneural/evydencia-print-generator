"""Tests for shell extension manifest protocol (--shell-request)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from evydencia_print_generator.__main__ import _read_shell_request, main


def test_read_shell_request_json_list(tmp_path: Path) -> None:
    manifest = tmp_path / "req.json"
    manifest.write_text(json.dumps(["C:/a.jpg", "C:/b.png"]), encoding="utf-8")

    paths = _read_shell_request(str(manifest))
    assert paths == ["C:/a.jpg", "C:/b.png"]


def test_read_shell_request_json_dict(tmp_path: Path) -> None:
    manifest = tmp_path / "req_dict.json"
    manifest.write_text(json.dumps({"files": ["C:/1.jpg", "C:/2.jpeg"]}), encoding="utf-8")

    paths = _read_shell_request(str(manifest))
    assert paths == ["C:/1.jpg", "C:/2.jpeg"]


def test_read_shell_request_plain_text_with_comments_and_empty_lines(tmp_path: Path) -> None:
    manifest = tmp_path / "req.txt"
    manifest.write_text(
        "# Header comment\n"
        "C:/photos/Natal 2026.jpg\n"
        "\n"
        "   C:/photos/Família Silva.png   \n"
        "# Another comment\n",
        encoding="utf-8",
    )

    paths = _read_shell_request(str(manifest))
    assert paths == ["C:/photos/Natal 2026.jpg", "C:/photos/Família Silva.png"]


def test_read_shell_request_cleanup_in_temp_dir() -> None:
    temp_dir = Path(tempfile.gettempdir())
    manifest = temp_dir / "evydencia_test_req_temp.txt"
    manifest.write_text("C:/photos/test.jpg\n", encoding="utf-8")
    assert manifest.exists()

    paths = _read_shell_request(str(manifest))
    assert paths == ["C:/photos/test.jpg"]
    # Should be deleted because it is inside system temp dir
    assert not manifest.exists()


def test_cli_combines_argv_and_shell_request(make_image, tmp_path: Path, capsys) -> None:
    img1 = make_image("posicional.jpg", size=(100, 100))
    img2 = make_image("do_manifest.png", size=(80, 80))

    manifest = tmp_path / "request.txt"
    manifest.write_text(str(img2), encoding="utf-8")

    code = main([str(img1), "--shell-request", str(manifest)])
    out = capsys.readouterr().out
    assert code == 0
    assert "OK    posicional.jpg" in out
    assert "OK    do_manifest.png" in out
