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


def test_cli_shell_request_plain_text(make_image, tmp_path, capsys) -> None:
    good1 = make_image("Foto 01 com espaço.jpg", size=(40, 30))
    good2 = make_image("Família Ñó.png", size=(50, 50))
    manifest = tmp_path / "request.txt"
    manifest.write_text(f"{good1}\n\n# comentário\n{good2}\n", encoding="utf-8")

    code = main(["--shell-request", str(manifest)])
    out = capsys.readouterr().out
    assert code == 0
    assert "OK    Foto 01 com espaço.jpg" in out
    assert "OK    Família Ñó.png" in out


def test_cli_shell_request_json(make_image, tmp_path, capsys) -> None:
    import json

    good = make_image("Cliente_A.jpg", size=(60, 40))
    manifest = tmp_path / "request.json"
    manifest.write_text(json.dumps([str(good)]), encoding="utf-8")

    code = main(["--shell-request", str(manifest)])
    out = capsys.readouterr().out
    assert code == 0
    assert "OK    Cliente_A.jpg" in out


def test_cli_shell_request_missing_manifest(capsys) -> None:
    # Manifest doesn't exist -> empty images -> bootstrap message
    code = main(["--shell-request", "c:/nao_existe/request.txt"])
    out = capsys.readouterr().out
    assert code == 0
    assert "bootstrap" in out

