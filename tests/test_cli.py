"""CLI contract: argv goes through the same IngestService as dialog/drop."""

from __future__ import annotations

from evydencia_print_generator.__main__ import main


def test_no_args_bootstrap(capsys) -> None:
    assert main([]) == 0
    assert "bootstrap" in capsys.readouterr().out


def test_cli_ingests_valid_and_reports_invalid(make_image, tmp_path, capsys) -> None:
    good = make_image("Família Ñ.jpg", size=(40, 30))
    code = main([str(good), str(tmp_path / "faltando.jpg")])
    out = capsys.readouterr().out
    assert code == 0
    assert "OK    Família Ñ.jpg  JPEG 40x30" in out
    assert "ERRO  faltando.jpg  not_found" in out
    assert str(tmp_path) not in out  # never print full paths


def test_cli_all_rejected_returns_error(tmp_path, capsys) -> None:
    assert main([str(tmp_path / "nada.png")]) == 1
