"""Tests for Chaveiro 3x4 partial rendering policy (minimum 2 slots)."""

from __future__ import annotations

from pathlib import Path

import pytest
from conftest import synthetic_rgb
from evydencia_print_generator.domain.job import EditState, JobError, SlotEdit, build_job_snapshot
from evydencia_print_generator.domain.template import load_template
from evydencia_print_generator.domain.transform import SlotTransform
from evydencia_print_generator.ingest import IngestService, SourceRegistry
from evydencia_print_generator.render import RenderOptions, render
from PIL import Image

TEMPLATES_ROOT = Path(__file__).resolve().parents[1] / "templates"


@pytest.fixture
def chaveiro_setup(tmp_path: Path):
    tpl_path = TEMPLATES_ROOT / "chaveiro-3x4" / "template.json"
    template = load_template(tpl_path)

    photo_1 = tmp_path / "photo_a.jpg"
    photo_2 = tmp_path / "photo_b.jpg"
    synthetic_rgb((800, 1000)).save(photo_1, format="JPEG")
    synthetic_rgb((800, 1000)).save(photo_2, format="JPEG")

    registry = SourceRegistry()
    ingest = IngestService(registry)
    sources = ingest.ingest_paths([photo_1, photo_2]).accepted

    return template, registry, sources[0], sources[1], tmp_path


def test_chaveiro_zero_slots_rejected(chaveiro_setup) -> None:
    template, registry, s1, s2, tmp_path = chaveiro_setup
    edit_state = EditState(
        template_id=template.id,
        template_version=template.template_version,
        slot_edits={},
    )
    with pytest.raises(JobError, match="insufficient photos"):
        build_job_snapshot(template, edit_state, registry.get)


def test_chaveiro_one_slot_rejected(chaveiro_setup) -> None:
    template, registry, s1, s2, tmp_path = chaveiro_setup
    edit_state = EditState(
        template_id=template.id,
        template_version=template.template_version,
        slot_edits={
            "slot_01": SlotEdit(source_id=s1.id, transform=SlotTransform(scale=1.0)),
        },
    )
    with pytest.raises(JobError, match="insufficient photos"):
        build_job_snapshot(template, edit_state, registry.get)


def test_chaveiro_two_slots_renders_partial_sheet(chaveiro_setup) -> None:
    template, registry, s1, s2, tmp_path = chaveiro_setup
    # Fill slot_03 and slot_07 (skipping slot_01 and slot_02)
    edit_state = EditState(
        template_id=template.id,
        template_version=template.template_version,
        slot_edits={
            "slot_03": SlotEdit(source_id=s1.id, transform=SlotTransform(scale=1.0)),
            "slot_07": SlotEdit(source_id=s2.id, transform=SlotTransform(scale=1.0)),
        },
    )
    snapshot = build_job_snapshot(template, edit_state, registry.get)
    assert len(snapshot.slot_edits) == 2

    result = render(
        template,
        snapshot,
        RenderOptions(output_dir=tmp_path / "out", draw_cut_guidelines=True),
    )

    assert result.output_path.is_file()
    # Output filename derives from first filled slot in physical order (s1: photo_a)
    assert "photo_a" in result.output_path.name
    with Image.open(result.output_path) as img:
        assert img.size == (2551, 1795)
        # Verify an empty slot (slot_01) has white canvas background
        slot1_rect = template.slot_rect_px("slot_01")
        cx = slot1_rect.left + slot1_rect.width // 2
        cy = slot1_rect.top + slot1_rect.height // 2
        pixel = img.getpixel((cx, cy))
        assert pixel[:3] == (255, 255, 255)
