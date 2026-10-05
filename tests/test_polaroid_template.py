"""Tests for Polaroid Natal template (draft)."""

from __future__ import annotations

from pathlib import Path

from conftest import synthetic_rgb
from evydencia_print_generator.domain.job import EditState, SlotEdit, build_job_snapshot
from evydencia_print_generator.domain.template import load_template
from evydencia_print_generator.domain.transform import SlotTransform
from evydencia_print_generator.ingest import IngestService, SourceRegistry
from evydencia_print_generator.render import RenderOptions, render
from PIL import Image

TEMPLATES_ROOT = Path(__file__).resolve().parents[1] / "templates"


def test_polaroid_natal_template_definition() -> None:
    tpl_path = TEMPLATES_ROOT / "polaroid-natal" / "template.json"
    template = load_template(tpl_path)

    assert template.id == "polaroid-natal"
    assert template.name == "Polaroid Natal"
    assert template.status == "draft"
    assert template.canvas.dpi == 300
    assert template.canvas_px() == (980, 1205)

    assert len(template.slots) == 1
    slot = template.slots[0]
    assert slot.id == "foto_principal"

    slot_px = template.slot_rect_px("foto_principal")
    assert slot_px.left == 69
    assert slot_px.top == 59
    assert slot_px.width == 843
    assert slot_px.height == 862

    assert template.overlay is not None
    assert template.overlay.required is True
    overlay_path = template.overlay_path()
    assert overlay_path is not None
    assert overlay_path.is_file()
    with Image.open(overlay_path) as img:
        assert img.size == (980, 1205)
        assert img.mode == "RGBA"


def test_polaroid_natal_render(tmp_path: Path) -> None:
    tpl_path = TEMPLATES_ROOT / "polaroid-natal" / "template.json"
    template = load_template(tpl_path)

    photo_file = tmp_path / "natal_input.jpg"
    synthetic_rgb((1200, 1600)).save(photo_file, format="JPEG", quality=95)

    registry = SourceRegistry()
    ingest = IngestService(registry)
    source = ingest.ingest_paths([photo_file]).accepted[0]

    edit_state = EditState(
        template_id=template.id,
        template_version=template.template_version,
        slot_edits={
            "foto_principal": SlotEdit(source_id=source.id, transform=SlotTransform(scale=1.0)),
        },
    )
    snapshot = build_job_snapshot(template, edit_state, registry.get)

    result = render(
        template,
        snapshot,
        RenderOptions(output_dir=tmp_path / "out", draw_cut_guidelines=False),
    )

    assert result.output_path.is_file()
    assert result.output_path.suffix.lower() in {".jpg", ".jpeg"}
    with Image.open(result.output_path) as out_img:
        assert out_img.size == (980, 1205)
