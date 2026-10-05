"""Tests for fail-closed required overlay validation."""

from __future__ import annotations

from pathlib import Path

import pytest
from conftest import synthetic_rgb
from evydencia_print_generator.domain.job import EditState, SlotEdit, build_job_snapshot
from evydencia_print_generator.domain.template import load_template
from evydencia_print_generator.domain.transform import SlotTransform
from evydencia_print_generator.ingest import IngestService, SourceRegistry
from evydencia_print_generator.render import RenderOptions, render
from evydencia_print_generator.render.models import RenderError
from PIL import Image

TEMPLATES_ROOT = Path(__file__).resolve().parents[1] / "templates"


def test_overlay_exact_size_succeeds(tmp_path: Path) -> None:
    tpl_path = TEMPLATES_ROOT / "polaroid-natal" / "template.json"
    template = load_template(tpl_path)

    photo = tmp_path / "photo.jpg"
    synthetic_rgb((800, 800)).save(photo, format="JPEG")

    registry = SourceRegistry()
    ingest = IngestService(registry)
    source = ingest.ingest_paths([photo]).accepted[0]

    edit_state = EditState(
        template_id=template.id,
        template_version=template.template_version,
        slot_edits={"foto_principal": SlotEdit(source_id=source.id, transform=SlotTransform())},
    )
    snapshot = build_job_snapshot(template, edit_state, registry.get)
    result = render(template, snapshot, RenderOptions(output_dir=tmp_path / "out"))
    assert result.output_path.is_file()


def test_required_overlay_mismatched_size_raises_render_error(tmp_path: Path) -> None:
    tpl_path = TEMPLATES_ROOT / "polaroid-natal" / "template.json"

    # Create a corrupted/mismatched overlay file in a mock template directory
    mock_dir = tmp_path / "mock_template"
    mock_dir.mkdir()
    mock_assets = mock_dir / "assets"
    mock_assets.mkdir()

    # Mismatched size: 800x600 instead of 980x1205
    bad_overlay = mock_assets / "overlay.png"
    Image.new("RGBA", (800, 600), (255, 0, 0, 128)).save(bad_overlay)

    # Write modified template.json pointing to bad overlay
    tpl_json = tpl_path.read_text(encoding="utf-8")
    tpl_json = tpl_json.replace("assets/polaroid-overlay.png", "assets/overlay.png")
    (mock_dir / "template.json").write_text(tpl_json, encoding="utf-8")

    mock_template = load_template(mock_dir / "template.json")

    photo = tmp_path / "photo.jpg"
    synthetic_rgb((800, 800)).save(photo, format="JPEG")

    registry = SourceRegistry()
    ingest = IngestService(registry)
    source = ingest.ingest_paths([photo]).accepted[0]

    edit_state = EditState(
        template_id=mock_template.id,
        template_version=mock_template.template_version,
        slot_edits={"foto_principal": SlotEdit(source_id=source.id, transform=SlotTransform())},
    )
    snapshot = build_job_snapshot(mock_template, edit_state, registry.get)

    with pytest.raises(RenderError, match="required overlay size mismatch"):
        render(mock_template, snapshot, RenderOptions(output_dir=tmp_path / "out"))
