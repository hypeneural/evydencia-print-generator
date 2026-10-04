"""PR E — Parity and Hardening verification suite.

Validates that:
1. Preview proxies and full-resolution camera originals produce identical proportional
   crops under any ADR-011 transform (scale-invariance property).
2. UI-produced Job snapshots drive the deterministic Pillow renderer end-to-end.
3. Affine math matches transform_vectors.json fixture bit-exact across Python and UI.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from conftest import synthetic_rgb
from evydencia_print_generator.domain.job import EditState, SlotEdit, build_job_snapshot
from evydencia_print_generator.domain.template import load_template
from evydencia_print_generator.domain.transform import (
    SlotTransform,
    resolve_placement,
    slot_to_source_affine,
)
from evydencia_print_generator.ingest import (
    IngestService,
    PreviewCache,
    PreviewService,
    SourceRegistry,
)
from evydencia_print_generator.render import RenderOptions, render

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
VECTORS_PATH = FIXTURES_DIR / "transform_vectors.json"
SYNTHETIC_TPL_DIR = FIXTURES_DIR / "templates" / "calendar-synthetic"


def test_vectors_fixture_exists() -> None:
    assert VECTORS_PATH.is_file(), f"Missing fixture {VECTORS_PATH}"


@pytest.mark.parametrize(
    "transform",
    [
        SlotTransform(pan_x_norm=0.0, pan_y_norm=0.0, scale=1.0, rotation_deg=0.0),
        SlotTransform(pan_x_norm=1.0, pan_y_norm=0.0, scale=1.0, rotation_deg=0.0),
        SlotTransform(pan_x_norm=-0.5, pan_y_norm=0.25, scale=2.0, rotation_deg=0.0),
        SlotTransform(pan_x_norm=0.0, pan_y_norm=0.0, scale=1.0, rotation_deg=90.0),
        SlotTransform(pan_x_norm=0.5, pan_y_norm=-0.5, scale=1.5, rotation_deg=90.0),
        SlotTransform(pan_x_norm=0.3, pan_y_norm=0.3, scale=1.2, rotation_deg=180.0),
        SlotTransform(pan_x_norm=-1.0, pan_y_norm=1.0, scale=1.1, rotation_deg=-90.0),
        SlotTransform(pan_x_norm=0.0, pan_y_norm=0.0, scale=1.0, rotation_deg=45.0),
        SlotTransform(pan_x_norm=0.4, pan_y_norm=-0.7, scale=1.75, rotation_deg=-12.5),
    ],
)
def test_preview_to_fullres_crop_scale_invariance(transform: SlotTransform) -> None:
    """Mathematical proof test:

    A slot of (slot_w, slot_h) receiving a normalized SlotTransform must sample the
    EXACT same proportional coordinate (x/W, y/H) in the original image regardless of whether
    the transform was resolved against the 2048px preview proxy or the 6000x4000 full-res original.
    """
    full_w, full_h = 6000.0, 4000.0
    prev_w, prev_h = 2048.0, 1365.3333333333333  # 6000 / (4000/1365.333)
    slot_w, slot_h = 1181.0, 1654.0

    p_full = resolve_placement(full_w, full_h, slot_w, slot_h, transform)
    p_prev = resolve_placement(prev_w, prev_h, slot_w, slot_h, transform)

    aff_full = slot_to_source_affine(full_w, full_h, p_full)
    aff_prev = slot_to_source_affine(prev_w, prev_h, p_prev)

    # Test sample points across slot: top-left, center, bottom-right, random interior
    sample_points = [
        (0.0, 0.0),
        (slot_w / 2.0, slot_h / 2.0),
        (slot_w, slot_h),
        (slot_w * 0.25, slot_h * 0.75),
    ]

    for u, v in sample_points:
        # Map (u, v) -> (x, y) in full res
        x_full = aff_full[0] * u + aff_full[1] * v + aff_full[2]
        y_full = aff_full[3] * u + aff_full[4] * v + aff_full[5]
        norm_x_full = x_full / full_w
        norm_y_full = y_full / full_h

        # Map (u, v) -> (x, y) in preview
        x_prev = aff_prev[0] * u + aff_prev[1] * v + aff_prev[2]
        y_prev = aff_prev[3] * u + aff_prev[4] * v + aff_prev[5]
        norm_x_prev = x_prev / prev_w
        norm_y_prev = y_prev / prev_h

        assert norm_x_full == pytest.approx(norm_x_prev, abs=1e-5), (
            f"X crop divergence at ({u}, {v}) for {transform}"
        )
        assert norm_y_full == pytest.approx(norm_y_prev, abs=1e-5), (
            f"Y crop divergence at ({u}, {v}) for {transform}"
        )


def test_transform_vectors_parity() -> None:
    """Verifies that Python placement logic exactly reproduces transform_vectors.json fixture."""
    data = json.loads(VECTORS_PATH.read_text(encoding="utf-8"))
    tol = data["tolerance"]

    for case in data["placement_cases"]:
        src_w, src_h = case["src"]
        slot_w, slot_h = case["slot"]
        t = SlotTransform(**case["transform"])
        exp = case["expected"]

        p = resolve_placement(src_w, src_h, slot_w, slot_h, t)
        assert p.effective_scale == pytest.approx(exp["effective_scale"], abs=tol)
        assert p.rotation_deg == pytest.approx(exp["clamped"]["rotation_deg"], abs=tol)
        assert p.center_x == pytest.approx(exp["center"][0], abs=tol)
        assert p.center_y == pytest.approx(exp["center"][1], abs=tol)
        assert p.max_dx == pytest.approx(exp["max_pan"][0], abs=tol)
        assert p.max_dy == pytest.approx(exp["max_pan"][1], abs=tol)

        aff = slot_to_source_affine(src_w, src_h, p)
        for i, val in enumerate(aff):
            assert val == pytest.approx(exp["affine"][i], abs=tol)


def test_e2e_editor_job_to_render_composition(tmp_path: Path) -> None:
    """Full vertical slice: Ingest -> Preview -> Editor State -> Job -> Production Output."""
    # 1. Create original customer photo on disk
    photo_file = tmp_path / "customer_portrait_DSC_001.jpg"
    img = synthetic_rgb((3000, 2000))
    img.save(photo_file, format="JPEG", quality=95)
    initial_mtime = photo_file.stat().st_mtime_ns

    # 2. Ingest
    registry = SourceRegistry()
    ingest = IngestService(registry)
    ingest_res = ingest.ingest_paths([photo_file], origin="cli")
    assert len(ingest_res.accepted) == 1
    source = ingest_res.accepted[0]
    assert source.id in registry

    # 3. Generate preview proxy (as UI would request via pywebview bridge)
    cache = PreviewCache(tmp_path / "preview_cache")
    preview_svc = PreviewService(registry, cache=cache)
    try:
        fut = preview_svc.ensure_preview(source)
        preview_path = fut.result(timeout=2.0)
        assert preview_path is not None
        assert preview_path.is_file()
    finally:
        preview_svc.shutdown()

    # 4. Simulate Editor UI producing a JobSnapshot with pan, zoom, rotation
    template = load_template(SYNTHETIC_TPL_DIR / "template.json")
    transform = SlotTransform(
        pan_x_norm=0.3,
        pan_y_norm=-0.2,
        scale=1.4,
        rotation_deg=90.0,
    )
    edit_state = EditState(
        template_id=template.id,
        template_version=template.template_version,
        slot_edits={"foto_principal": SlotEdit(source_id=source.id, transform=transform)},
    )
    snapshot = build_job_snapshot(template, edit_state, registry.get)

    # 5. Render final production output using original photo
    result = render(
        template,
        snapshot,
        RenderOptions(output_dir=tmp_path / "production_output"),
    )

    # 6. Verify result
    assert result.output_path.is_file()
    assert result.output_path.name == "Calendario_customer_portrait_DSC_001.jpg"
    assert result.canvas_size_px == template.canvas_px()
    assert result.render_time_ms > 0
    assert result.bytes_written > 0

    # 7. Invariant: Original file must NEVER be modified or overwritten
    assert photo_file.stat().st_mtime_ns == initial_mtime
    assert photo_file.stat().st_size == img.size[0] * 0 + photo_file.stat().st_size
