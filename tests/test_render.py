"""E3 — Deterministic Pillow Renderer tests and golden regression suite."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from conftest import QUADRANT_COLORS, synthetic_rgb
from evydencia_print_generator.domain.job import EditState, JobSnapshot, build_job_snapshot
from evydencia_print_generator.domain.template import load_template
from evydencia_print_generator.domain.transform import SlotTransform
from evydencia_print_generator.ingest import IngestService, SourceRegistry
from evydencia_print_generator.render import (
    RenderOptions,
    atomic_save_image,
    render,
    render_slot,
    resolve_output_path,
)
from PIL import Image, ImageCms

SYNTHETIC_TPL_DIR = (
    Path(__file__).resolve().parent / "fixtures" / "templates" / "calendar-synthetic"
)


@pytest.fixture
def calendar_template():
    return load_template(SYNTHETIC_TPL_DIR / "template.json")


@pytest.fixture
def source_photo(tmp_path: Path) -> Path:
    photo_path = tmp_path / "camera_original.jpg"
    img = synthetic_rgb((600, 400))
    img.save(photo_path, format="JPEG", quality=95)
    return photo_path


def test_resolve_output_path_collision_policy(tmp_path: Path) -> None:
    src = tmp_path / "0M4A3271.JPG"
    src.write_bytes(b"dummy")

    # 1. Base resolution: prefix + stem + .jpg in same folder
    out1 = resolve_output_path(src, prefix="Calendario_", output_format="JPEG")
    assert out1 == tmp_path / "Calendario_0M4A3271.jpg"

    # Simulate existing file
    out1.write_bytes(b"existing 1")

    # 2. Collision resolution -> _002
    out2 = resolve_output_path(src, prefix="Calendario_", output_format="JPEG")
    assert out2 == tmp_path / "Calendario_0M4A3271_002.jpg"

    # Simulate existing file _002
    out2.write_bytes(b"existing 2")

    # 3. Collision resolution -> _003
    out3 = resolve_output_path(src, prefix="Calendario_", output_format="JPEG")
    assert out3 == tmp_path / "Calendario_0M4A3271_003.jpg"

    # 4. Overwrite option
    out_ow = resolve_output_path(src, prefix="Calendario_", output_format="JPEG", overwrite=True)
    assert out_ow == out1

    # 5. Guard: never overwrite source image
    with pytest.raises(ValueError, match="matches input source path"):
        resolve_output_path(src, prefix="", output_format="JPG", overwrite=True)


def test_atomic_save_image_and_metadata(tmp_path: Path) -> None:
    target = tmp_path / "out.jpg"
    img = synthetic_rgb((200, 100))

    # Generate a standard sRGB ICC profile
    srgb_profile = ImageCms.createProfile("sRGB")
    icc_bytes = ImageCms.ImageCmsProfile(srgb_profile).tobytes()

    size_written = atomic_save_image(
        img,
        target,
        format="JPEG",
        quality=95,
        dpi=(300, 300),
        icc_profile=icc_bytes,
        subsampling=0,
    )
    assert size_written > 0
    assert target.is_file()

    # Re-open and verify metadata
    with Image.open(target) as loaded:
        assert loaded.size == (200, 100)
        assert loaded.info.get("dpi") == (300, 300)
        assert loaded.info.get("icc_profile") is not None


def test_render_slot_quadrant_rotation() -> None:
    # 400x400 quadrant: TL=Red, TR=Green, BL=Blue, BR=Yellow
    quad = synthetic_rgb((400, 400))

    # Test rotation 0: (30, 30) samples TL (Red), (70, 70) samples BR (Yellow)
    t0 = SlotTransform(pan_x_norm=0.0, pan_y_norm=0.0, scale=1.0, rotation_deg=0.0)
    slot_0 = render_slot(quad, (100, 100), t0)
    assert slot_0.getpixel((30, 30)) == QUADRANT_COLORS["tl"]
    assert slot_0.getpixel((70, 70)) == QUADRANT_COLORS["br"]

    # Test rotation 90 (clockwise):
    # Top-Left of original moves to Top-Right of slot.
    # Bottom-Left of original moves to Top-Left of slot (Blue).
    t90 = SlotTransform(pan_x_norm=0.0, pan_y_norm=0.0, scale=1.0, rotation_deg=90.0)
    slot_90 = render_slot(quad, (100, 100), t90)
    assert slot_90.getpixel((30, 30)) == QUADRANT_COLORS["bl"]
    assert slot_90.getpixel((70, 30)) == QUADRANT_COLORS["tl"]


def test_render_end_to_end_deterministic(
    calendar_template, source_photo: Path, tmp_path: Path
) -> None:
    registry = SourceRegistry()
    ingest = IngestService(registry)
    asset = ingest.ingest_paths([source_photo]).accepted[0]

    edit_state = EditState.from_ui(
        {
            "template_id": calendar_template.id,
            "template_version": calendar_template.template_version,
            "slot_edits": {
                "foto_principal": {
                    "source_id": asset.id,
                    "pan_x_norm": 0.25,
                    "pan_y_norm": -0.15,
                    "scale": 1.2,
                    "rotation_deg": 15.0,
                }
            },
        }
    )
    snapshot = build_job_snapshot(calendar_template, edit_state, registry.get)

    # Render run 1
    res1 = render(calendar_template, snapshot, RenderOptions(output_dir=tmp_path / "out1"))
    assert res1.output_path.is_file()
    assert res1.canvas_size_px == calendar_template.canvas_px()
    data1 = res1.output_path.read_bytes()

    # Render run 2 (exact same input)
    res2 = render(calendar_template, snapshot, RenderOptions(output_dir=tmp_path / "out2"))
    assert res2.output_path.is_file()
    data2 = res2.output_path.read_bytes()

    # Determinism check: identical bitstream
    assert data1 == data2
    assert hashlib.sha256(data1).hexdigest() == hashlib.sha256(data2).hexdigest()


def test_render_never_modifies_original_source(
    calendar_template, source_photo: Path, tmp_path: Path
) -> None:
    original_bytes = source_photo.read_bytes()
    original_mtime = source_photo.stat().st_mtime_ns

    registry = SourceRegistry()
    asset = IngestService(registry).ingest_paths([source_photo]).accepted[0]
    edit_state = EditState.from_ui(
        {
            "template_id": calendar_template.id,
            "template_version": calendar_template.template_version,
            "slot_edits": {
                "foto_principal": {
                    "source_id": asset.id,
                    "pan_x_norm": 0.0,
                    "pan_y_norm": 0.0,
                    "scale": 1.0,
                    "rotation_deg": 0.0,
                }
            },
        }
    )
    snapshot = build_job_snapshot(calendar_template, edit_state, registry.get)

    res = render(calendar_template, snapshot)
    assert res.output_path.is_file()
    assert res.output_path != source_photo

    # Source photo must remain untouched
    assert source_photo.read_bytes() == original_bytes
    assert source_photo.stat().st_mtime_ns == original_mtime


def test_render_with_overlay_composition(tmp_path: Path) -> None:
    # Build a template with a custom overlay PNG
    tpl_dir = tmp_path / "tpl_overlay"
    tpl_dir.mkdir()

    canvas_w, canvas_h = 300, 400
    overlay_path = tpl_dir / "overlay.png"

    # Create overlay: mostly green frame with a transparent center window (50, 50, 250, 200)
    overlay_img = Image.new("RGBA", (canvas_w, canvas_h), (34, 139, 34, 255))
    # Punch transparent hole
    for x in range(50, 250):
        for y in range(50, 200):
            overlay_img.putpixel((x, y), (0, 0, 0, 0))
    overlay_img.save(overlay_path, format="PNG")

    # Photo: solid bright magenta
    photo_path = tmp_path / "photo.jpg"
    Image.new("RGB", (500, 500), (255, 0, 255)).save(photo_path, format="JPEG")

    # Construct template JSON: 150 DPI, canvas 50.8 x 67.733 mm (300 x 400 px)
    import json

    tpl_data = {
        "schema_version": "1.0",
        "template_version": "1.0.0",
        "id": "tpl-with-overlay",
        "name": "Template with Overlay",
        "status": "production",
        "canvas": {"width_mm": 50.8, "height_mm": 67.7333333333, "dpi": 150},
        "output": {"format": "JPEG", "quality": 95, "filename_prefix": "Calendario_"},
        "slots": [
            {
                "id": "foto_principal",
                "x_mm": 8.4666666667,  # 50 px at 150 dpi
                "y_mm": 8.4666666667,  # 50 px
                "width_mm": 33.8666666667,  # 200 px
                "height_mm": 25.4,  # 150 px
                "fit": "cover",
                "allow_pan": True,
                "allow_zoom": True,
                "allow_rotate": True,
            }
        ],
        "overlay": {"path": "overlay.png", "required": True},
        "groups": [],
        "provenance": {"measured": [], "derived": [], "pending": []},
        "notes": [],
    }
    (tpl_dir / "template.json").write_text(json.dumps(tpl_data), encoding="utf-8")
    template = load_template(tpl_dir / "template.json")

    registry = SourceRegistry()
    asset = IngestService(registry).ingest_paths([photo_path]).accepted[0]
    edit_state = EditState.from_ui(
        {
            "template_id": template.id,
            "template_version": template.template_version,
            "slot_edits": {
                "foto_principal": {
                    "source_id": asset.id,
                    "pan_x_norm": 0.0,
                    "pan_y_norm": 0.0,
                    "scale": 1.0,
                    "rotation_deg": 0.0,
                }
            },
        }
    )
    snapshot = build_job_snapshot(template, edit_state, registry.get)

    result = render(template, snapshot, RenderOptions(output_dir=tmp_path / "out_overlay"))
    assert result.output_path.is_file()

    with Image.open(result.output_path) as out:
        # Outside window (e.g. 10, 10): should be overlay green (34, 139, 34)
        r, g, b = out.getpixel((10, 10))
        assert (r, g, b) == (34, 139, 34)

        # Inside transparent window (e.g. 100, 100): should be photo magenta (255, 0, 255)
        # Note: JPEG compression may alter pixel values slightly by 1-2 levels
        pr, pg, pb = out.getpixel((100, 100))
        assert abs(pr - 255) <= 2
        assert abs(pg - 0) <= 2
        assert abs(pb - 255) <= 2


def test_render_unrenderable_template_raises_template_error() -> None:
    from evydencia_print_generator.domain.template import TemplateError
    from evydencia_print_generator.paths import templates_dir

    # calendario-2027 is in draft status with null dimensions
    draft_tpl = load_template(templates_dir() / "calendario-2027" / "template.json")
    assert not draft_tpl.is_renderable

    # Dummy snapshot
    snapshot = JobSnapshot(
        template_id=draft_tpl.id,
        template_version=draft_tpl.template_version,
        sources={},
        slot_edits={},
    )
    with pytest.raises(TemplateError, match="is not renderable"):
        render(draft_tpl, snapshot)


def test_render_golden_pixel_hash(calendar_template, tmp_path: Path) -> None:
    from evydencia_print_generator.render.compose import compose_canvas

    # Create deterministic synthetic image (lossless PNG to avoid JPEG compression variance)
    photo_path = tmp_path / "golden_input.png"
    synthetic_rgb((600, 400)).save(photo_path, format="PNG")

    registry = SourceRegistry()
    asset = IngestService(registry).ingest_paths([photo_path]).accepted[0]

    edit_state = EditState.from_ui(
        {
            "template_id": calendar_template.id,
            "template_version": calendar_template.template_version,
            "slot_edits": {
                "foto_principal": {
                    "source_id": asset.id,
                    "pan_x_norm": 0.1,
                    "pan_y_norm": -0.1,
                    "scale": 1.15,
                    "rotation_deg": 10.0,
                }
            },
        }
    )
    snapshot = build_job_snapshot(calendar_template, edit_state, registry.get)
    canvas_image, _ = compose_canvas(calendar_template, snapshot)

    assert canvas_image.size == (591, 827)
    assert canvas_image.mode == "RGB"
    pixel_hash = hashlib.sha256(canvas_image.tobytes()).hexdigest()
    # Golden uncompressed pixel hash regression check
    assert pixel_hash == "3e2479ec2ea82556371469267b5b268bc69f592edafa3ba118fc8a6a82222fa5"
