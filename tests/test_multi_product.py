"""M2 — Multi-Product (Globo de Neve & Chaveiro 3x4) Integration Tests."""

from __future__ import annotations

from pathlib import Path

from conftest import synthetic_rgb
from evydencia_print_generator.app.bridge import DesktopBridge
from evydencia_print_generator.domain.job import EditState, SlotEdit, build_job_snapshot
from evydencia_print_generator.domain.template import load_template
from evydencia_print_generator.domain.transform import SlotTransform
from evydencia_print_generator.ingest import (
    IngestService,
    PreviewCache,
    PreviewService,
    SourceRegistry,
)
from evydencia_print_generator.render import RenderOptions, render

TEMPLATES_ROOT = Path(__file__).resolve().parents[1] / "templates"


def test_globo_neve_production_render(tmp_path: Path) -> None:
    """Test Globo de Neve: 2 symmetrical 50x80mm slots on 152x102mm canvas @ 300 DPI."""
    tpl_path = TEMPLATES_ROOT / "globo-neve" / "template.json"
    template = load_template(tpl_path)

    assert template.status == "production"
    assert template.canvas.dpi == 300
    assert template.canvas_px() == (1795, 1205)
    assert len(template.slots) == 2
    assert template.slot_ids == ("foto_1", "foto_2")

    # Ingest 1 source photo and use in both slots
    photo_file = tmp_path / "portrait_input.jpg"
    synthetic_rgb((3000, 2000)).save(photo_file, format="JPEG", quality=95)

    registry = SourceRegistry()
    ingest = IngestService(registry)
    source = ingest.ingest_paths([photo_file]).accepted[0]

    # Batch fill: assign same source to both slots
    edits = {
        "foto_1": SlotEdit(source_id=source.id, transform=SlotTransform(scale=1.0)),
        "foto_2": SlotEdit(source_id=source.id, transform=SlotTransform(scale=1.2, pan_y_norm=0.1)),
    }
    edit_state = EditState(
        template_id=template.id,
        template_version=template.template_version,
        slot_edits=edits,
    )
    snapshot = build_job_snapshot(template, edit_state, registry.get)

    result = render(
        template,
        snapshot,
        RenderOptions(output_dir=tmp_path / "out", draw_cut_guidelines=True),
    )

    assert result.output_path.is_file()
    assert result.output_path.name == "Globo_portrait_input.jpg"
    assert result.canvas_size_px == (1795, 1205)
    assert result.dpi == 300
    assert result.render_time_ms < 2000.0


def test_chaveiro_3x4_production_render_18_slots(tmp_path: Path) -> None:
    """Test Chaveiro 3x4: 18 slots (6x3 grid of 34x44mm) on 216x152mm canvas @ 300 DPI."""
    tpl_path = TEMPLATES_ROOT / "chaveiro-3x4" / "template.json"
    template = load_template(tpl_path)

    assert template.status == "production"
    assert template.canvas.dpi == 300
    assert template.canvas_px() == (2551, 1795)
    assert len(template.slots) == 18

    # Ingest 2 photos to test mixed slot assignments
    photo1 = tmp_path / "chaveiro_foto_A.jpg"
    photo2 = tmp_path / "chaveiro_foto_B.jpg"
    synthetic_rgb((2000, 3000)).save(photo1, format="JPEG", quality=95)
    synthetic_rgb((2000, 3000)).save(photo2, format="JPEG", quality=95)

    registry = SourceRegistry()
    ingest = IngestService(registry)
    res = ingest.ingest_paths([photo1, photo2])
    src_a, src_b = res.accepted[0], res.accepted[1]

    # Assign photo A to slots 01-09 and photo B to slots 10-18
    edits = {}
    for i, slot_id in enumerate(template.slot_ids):
        assigned = src_a if i < 9 else src_b
        edits[slot_id] = SlotEdit(
            source_id=assigned.id,
            transform=SlotTransform(scale=1.0, pan_x_norm=0.0),
        )

    edit_state = EditState(
        template_id=template.id,
        template_version=template.template_version,
        slot_edits=edits,
    )
    snapshot = build_job_snapshot(template, edit_state, registry.get)

    result = render(
        template,
        snapshot,
        RenderOptions(output_dir=tmp_path / "out", draw_cut_guidelines=True),
    )

    assert result.output_path.is_file()
    assert result.output_path.name == "Chaveiro_chaveiro_foto_A.jpg"
    assert result.canvas_size_px == (2551, 1795)
    assert result.dpi == 300
    assert result.bytes_written > 0
    # 18 slots should easily render within 2.5s on modern hardware
    assert result.render_time_ms < 3000.0


def test_bridge_lists_all_three_products(tmp_path: Path) -> None:
    """Verify DesktopBridge exposes all 3 templates to the frontend."""
    registry = SourceRegistry()
    cache = PreviewCache(cache_dir=tmp_path / "cache")
    ingest = IngestService(registry)
    prev = PreviewService(registry, cache=cache)
    try:
        bridge = DesktopBridge(
            registry,
            ingest,
            prev,
            "http://127.0.0.1:5000",
            templates_root=TEMPLATES_ROOT,
        )
        templates = bridge.get_templates()
        ids = [t["id"] for t in templates]
        assert "calendario-2027" in ids
        assert "globo-neve" in ids
        assert "chaveiro-3x4" in ids

        globo = next(t for t in templates if t["id"] == "globo-neve")
        assert len(globo["slots"]) == 2
        assert globo["canvas_px"] == {"width": 1795, "height": 1205}

        chaveiro = next(t for t in templates if t["id"] == "chaveiro-3x4")
        assert len(chaveiro["slots"]) == 18
        assert chaveiro["canvas_px"] == {"width": 2551, "height": 1795}
    finally:
        prev.shutdown()
