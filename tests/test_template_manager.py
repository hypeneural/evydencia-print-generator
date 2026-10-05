"""Tests for template persistence, versioning, and atomic publishing pipeline."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from evydencia_print_generator.domain.template import TemplateError
from evydencia_print_generator.domain.template_manager import (
    bump_version,
    publish_template_to_disk,
)


def test_bump_version_valid() -> None:
    assert bump_version("1.0.0", "patch") == "1.0.1"
    assert bump_version("1.0.0", "minor") == "1.1.0"
    assert bump_version("1.0.0", "major") == "2.0.0"

    assert bump_version("1.4.9", "patch") == "1.4.10"
    assert bump_version("1.4.9", "minor") == "1.5.0"
    assert bump_version("1.4.9", "major") == "2.0.0"


def test_bump_version_invalid_format() -> None:
    with pytest.raises(ValueError, match="Invalid semver version"):
        bump_version("1.0")

    with pytest.raises(ValueError, match="Invalid semver version"):
        bump_version("v1.0.0")

    with pytest.raises(ValueError, match="Invalid semver version"):
        bump_version("alpha.1")


def test_bump_version_invalid_type() -> None:
    with pytest.raises(ValueError, match="Invalid bump_type"):
        bump_version("1.0.0", "unknown")  # type: ignore[arg-type]


def test_publish_template_to_disk_success(tmp_path: Path) -> None:
    templates_root = tmp_path / "templates"
    templates_root.mkdir()

    draft = {
        "id": "teste-gestor",
        "name": "Template Teste Gestor",
        "template_version": "1.0.0",
        "status": "production",
        "canvas": {
            "width_mm": 150.0,
            "height_mm": 100.0,
            "dpi": 300,
        },
        "slots": [
            {
                "id": "slot_01",
                "x_mm": 10.0,
                "y_mm": 10.0,
                "width_mm": 60.0,
                "height_mm": 80.0,
                "fit": "cover",
                "allow_pan": True,
                "allow_zoom": True,
                "allow_rotate": False,
            },
            {
                "id": "slot_02",
                "x_mm": 75.0,
                "y_mm": 10.0,
                "width_mm": 65.0,
                "height_mm": 80.0,
                "fit": "cover",
                "allow_pan": True,
                "allow_zoom": True,
                "allow_rotate": False,
            },
        ],
        "overlay": None,
    }

    # First publication
    tpl = publish_template_to_disk(
        templates_root, draft, bump_type="minor", notes="Primeira versão gestor"
    )

    assert tpl.id == "teste-gestor"
    assert tpl.template_version == "1.1.0"
    assert len(tpl.slots) == 2
    assert tpl.canvas.width_mm == 150.0
    assert tpl.canvas.height_mm == 100.0
    assert tpl.canvas.dpi == 300

    target_file = templates_root / "teste-gestor" / "template.json"
    assert target_file.is_file()

    # Load directly from disk and check json content
    disk_data = json.loads(target_file.read_text(encoding="utf-8"))
    assert disk_data["schema_version"] == "1.0"
    assert disk_data["template_version"] == "1.1.0"
    assert len(disk_data["provenance"]["derived"]) >= 1
    assert "Modo Gestor" in disk_data["provenance"]["derived"][-1]
    assert "Primeira versão gestor" in disk_data["notes"]

    # Second publication with patch bump
    draft_patch = dict(draft)
    draft_patch["slots"] = [
        {
            "id": "slot_01",
            "x_mm": 12.0,
            "y_mm": 10.0,
            "width_mm": 60.0,
            "height_mm": 80.0,
            "fit": "cover",
            "allow_pan": True,
            "allow_zoom": True,
            "allow_rotate": False,
        }
    ]
    tpl_v2 = publish_template_to_disk(templates_root, draft_patch, bump_type="patch")
    assert tpl_v2.template_version == "1.1.1"
    assert len(tpl_v2.slots) == 1
    assert tpl_v2.slots[0].x_mm == 12.0


def test_publish_template_preserves_metadata(tmp_path: Path) -> None:
    templates_root = tmp_path / "templates"
    tpl_dir = templates_root / "meu-produto"
    tpl_dir.mkdir(parents=True)

    initial_json = {
        "schema_version": "1.0",
        "template_version": "2.0.0",
        "id": "meu-produto",
        "name": "Meu Produto Especial",
        "status": "production",
        "canvas": {"width_mm": 100.0, "height_mm": 100.0, "dpi": 300},
        "output": {
            "format": "PNG",
            "quality": 99,
            "filename_prefix": "Especial_",
        },
        "slots": [
            {
                "id": "slot_a",
                "x_mm": 5.0,
                "y_mm": 5.0,
                "width_mm": 40.0,
                "height_mm": 40.0,
                "fit": "cover",
                "allow_pan": True,
                "allow_zoom": True,
                "allow_rotate": True,
            }
        ],
        "overlay": None,
        "groups": [{"id": "grp1", "slot_ids": ["slot_a"], "fill_mode": "independent"}],
        "provenance": {
            "measured": ["Medição manual de régua"],
            "derived": ["Canvas 100x100"],
            "pending": [],
        },
        "notes": ["Nota inicial de teste"],
    }
    (tpl_dir / "template.json").write_text(json.dumps(initial_json, indent=2), encoding="utf-8")

    draft = {
        "id": "meu-produto",
        "name": "Meu Produto Especial",
        "template_version": "2.0.0",
        "status": "production",
        "canvas": {"width_mm": 100.0, "height_mm": 100.0, "dpi": 300},
        "slots": [
            {
                "id": "slot_a",
                "x_mm": 10.0,
                "y_mm": 10.0,
                "width_mm": 40.0,
                "height_mm": 40.0,
                "fit": "cover",
                "allow_pan": True,
                "allow_zoom": True,
                "allow_rotate": True,
            }
        ],
        "overlay": None,
    }

    tpl = publish_template_to_disk(templates_root, draft, bump_type="minor")
    assert tpl.template_version == "2.1.0"
    assert tpl.output.format == "PNG"
    assert tpl.output.quality == 99
    assert tpl.output.filename_prefix == "Especial_"

    # Load from disk to verify provenance and groups
    reloaded = json.loads((tpl_dir / "template.json").read_text(encoding="utf-8"))
    assert reloaded["groups"] == [
        {"id": "grp1", "slot_ids": ["slot_a"], "fill_mode": "independent"}
    ]
    assert "Medição manual de régua" in reloaded["provenance"]["measured"]
    assert len(reloaded["provenance"]["derived"]) == 2


def test_publish_template_rejection_out_of_bounds(tmp_path: Path) -> None:
    templates_root = tmp_path / "templates"
    templates_root.mkdir()

    draft = {
        "id": "invalid-template",
        "name": "Invalid Template",
        "template_version": "1.0.0",
        "status": "production",
        "canvas": {"width_mm": 100.0, "height_mm": 100.0, "dpi": 300},
        "slots": [
            {
                "id": "slot_1",
                "x_mm": 50.0,
                "y_mm": 50.0,
                "width_mm": 60.0,  # 50 + 60 = 110 > 100 mm (canvas overflow)
                "height_mm": 40.0,
                "fit": "cover",
                "allow_pan": True,
                "allow_zoom": True,
                "allow_rotate": False,
            }
        ],
        "overlay": None,
    }

    with pytest.raises(TemplateError) as exc_info:
        publish_template_to_disk(templates_root, draft, bump_type="minor")

    assert "exceeds canvas" in str(exc_info.value)
    # Target file must not have been created
    assert not (templates_root / "invalid-template" / "template.json").exists()


def test_desktop_bridge_publish_template(tmp_path: Path) -> None:
    from evydencia_print_generator.app.bridge import DesktopBridge
    from evydencia_print_generator.ingest import (
        IngestService,
        PreviewCache,
        PreviewService,
        SourceRegistry,
    )

    templates_root = tmp_path / "templates"
    templates_root.mkdir()
    registry = SourceRegistry()
    cache = PreviewCache(tmp_path / "cache")
    preview_service = PreviewService(registry, cache=cache)
    ingest_service = IngestService(registry, schedule_preview=preview_service.ensure_preview)

    bridge = DesktopBridge(
        registry=registry,
        ingest_service=ingest_service,
        preview_service=preview_service,
        server_base_url="http://127.0.0.1:8000",
        templates_root=templates_root,
    )

    draft = {
        "id": "template-bridge-test",
        "name": "Template Bridge Test",
        "template_version": "1.0.0",
        "status": "production",
        "canvas": {"width_mm": 100.0, "height_mm": 150.0, "dpi": 300},
        "slots": [
            {
                "id": "s1",
                "x_mm": 10.0,
                "y_mm": 10.0,
                "width_mm": 80.0,
                "height_mm": 120.0,
                "fit": "cover",
                "allow_pan": True,
                "allow_zoom": True,
                "allow_rotate": False,
            }
        ],
        "overlay": None,
    }

    # 1. Successful publish
    res = bridge.publish_template(draft, bump_type="minor", notes="Bridge test")
    assert res["success"] is True
    assert res["template"]["id"] == "template-bridge-test"
    assert res["template"]["template_version"] == "1.1.0"
    assert len(res["templates"]) == 1
    assert res["templates"][0]["id"] == "template-bridge-test"

    # 2. Rejection handling
    invalid_draft = dict(draft)
    invalid_draft["slots"] = [
        {
            "id": "s1",
            "x_mm": 10.0,
            "y_mm": 10.0,
            "width_mm": 200.0,  # exceeds width
            "height_mm": 120.0,
            "fit": "cover",
            "allow_pan": True,
            "allow_zoom": True,
            "allow_rotate": False,
        }
    ]
    fail_res = bridge.publish_template(invalid_draft, bump_type="patch")
    assert fail_res["success"] is False
    assert "exceeds canvas" in fail_res["error"]
    assert len(fail_res["issues"]) > 0
