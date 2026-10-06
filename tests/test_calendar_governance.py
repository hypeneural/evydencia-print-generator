"""Governance and production quality tests for Calendário 2027."""

from __future__ import annotations

import base64
from pathlib import Path

import pytest
from conftest import synthetic_rgb
from evydencia_print_generator.domain.job import EditState, build_job_snapshot
from evydencia_print_generator.domain.template import load_template
from evydencia_print_generator.imaging.color import is_srgb_profile
from evydencia_print_generator.ingest import IngestService, SourceRegistry
from evydencia_print_generator.render import RenderOptions, render
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
CALENDAR_TPL_PATH = REPO_ROOT / "templates" / "calendario-2027" / "template.json"

REC2020_B64 = (
    "AAAB+EFEQkUEAAAAbW50clJHQiBYWVogB+AABQAVAAIALAAsYWNzcEFQUEwAAAAA"
    "bm9uZQAAAAAAAAAAAAAAAAAAAAEAAPbWAAEAAAAA0yxBREJFAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAJY3BydAAAAPAAAAAy"
    "ZGVzYwAAASQAAABkd3RwdAAAAYgAAAAUclhZWgAAAZwAAAAUZ1hZWgAAAbAAAAAU"
    "YlhZWgAAAcQAAAAUclRSQwAAAdgAAAAgZ1RSQwAAAdgAAAAgYlRSQwAAAdgAAAAg"
    "dGV4dAAAAABDb3B5cmlnaHQgMjAxNiBBZG9iZSBTeXN0ZW1zIEluY29ycG9yYXRl"
    "ZAAAAGRlc2MAAAAAAAAAClJlYy4gMjAyMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAABYWVogAAAAAAAA81IAAQAAAAEWzFhZWiAAAAAAAACsaQAAR2////+B"
    "WFlaIAAAAAAAACpqAACs5AAAB61YWVogAAAAAAAAIAMAAAutAADL/nBhcmEAAAAA"
    "AAMAAAACOOQAAOjgAAAXIAAAOOQAABTM"
)
REC2020_ICC = base64.b64decode(REC2020_B64)


def test_calendar_template_geometry_and_resolution() -> None:
    """Verifies that the canonical Calendário 2027 template geometry matches measured facts."""
    template = load_template(CALENDAR_TPL_PATH)
    assert template.canvas.dpi == 254
    assert template.canvas.width_mm == pytest.approx(106.7, abs=1e-3)
    assert template.canvas.height_mm == pytest.approx(147.4, abs=1e-3)

    canvas_w, canvas_h = template.canvas_px()
    assert canvas_w == 1067
    assert canvas_h == 1474

    slot_rect = template.slot_rect_px("foto_principal")
    assert slot_rect.left == 118
    assert slot_rect.top == 107
    assert slot_rect.width == 823
    assert slot_rect.height == 395


def test_calendar_overlay_asset_matches_template() -> None:
    """Verifies that the overlay PNG matches template dimensions 1:1 without scaling."""
    template = load_template(CALENDAR_TPL_PATH)
    overlay_path = template.overlay_path()
    assert overlay_path is not None
    assert overlay_path.is_file()

    with Image.open(overlay_path) as overlay:
        assert overlay.size == template.canvas_px()
        assert overlay.mode == "RGBA"


def test_calendar_render_embeds_canonical_srgb_profile(tmp_path: Path) -> None:
    """Verifies that rendering Calendário 2027 with a wide gamut Rec. 2020 photo produces

    a production file that strictly embeds the canonical sRGB ICC profile.
    """
    template = load_template(CALENDAR_TPL_PATH)

    # 1. Create a customer photo with Rec. 2020 ICC profile
    photo_file = tmp_path / "customer_rec2020.jpg"
    photo_img = synthetic_rgb((4000, 3000))
    photo_img.save(photo_file, format="JPEG", quality=95, icc_profile=REC2020_ICC)
    original_mtime = photo_file.stat().st_mtime_ns

    # 2. Ingest
    registry = SourceRegistry()
    ingest = IngestService(registry)
    asset = ingest.ingest_paths([photo_file]).accepted[0]

    # 3. Build snapshot
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

    # 4. Render
    out_dir = tmp_path / "production_out"
    result = render(template, snapshot, RenderOptions(output_dir=out_dir))

    assert result.output_path.is_file()
    assert result.canvas_size_px == (1067, 1474)
    assert result.dpi == 254

    # 5. Verify production file metadata
    with Image.open(result.output_path) as out_img:
        assert out_img.size == (1067, 1474)
        assert out_img.info.get("dpi") == (254, 254)
        out_icc = out_img.info.get("icc_profile")
        assert out_icc is not None
        # MUST be sRGB, NEVER pass-through Rec. 2020!
        assert is_srgb_profile(out_icc) is True

    # 6. Verify original source was never touched
    assert photo_file.stat().st_mtime_ns == original_mtime
