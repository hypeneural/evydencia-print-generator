"""Unit and regression tests for high-fidelity resampling and anti-aliasing (ADR-013)."""

from __future__ import annotations

import pytest
from conftest import QUADRANT_COLORS, synthetic_rgb
from evydencia_print_generator.domain.transform import (
    SlotTransform,
    resolve_placement,
    slot_to_source_affine,
)
from evydencia_print_generator.render.resample import resample_slot
from PIL import Image, ImageDraw, ImageStat


def test_resampling_anti_aliasing_grid() -> None:
    """Mathematical proof of anti-aliasing:

    Tests that resample_slot band-limits high-frequency content, reducing aliasing
    variance by more than 80% compared to direct single-pass affine bicubic.
    """
    w, h = 4000, 3000
    src = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(src)
    for x in range(0, w, 4):
        draw.line([(x, 0), (x, h)], fill=(0, 0, 0))
    for y in range(0, h, 4):
        draw.line([(0, y), (w, y)], fill=(0, 0, 0))

    slot_size = (800, 600)
    transform = SlotTransform()

    # 1. Old method: direct single-pass bicubic affine
    p = resolve_placement(w, h, slot_size[0], slot_size[1], transform)
    aff = slot_to_source_affine(w, h, p)
    old_out = src.transform(
        slot_size,
        method=Image.Transform.AFFINE,
        data=aff,
        resample=Image.Resampling.BICUBIC,
    )
    old_std = float(ImageStat.Stat(old_out.convert("L")).stddev[0])

    # 2. New method: resample_slot (Lanczos + reducing_gap)
    new_out = resample_slot(src, slot_size, transform)
    new_std = float(ImageStat.Stat(new_out.convert("L")).stddev[0])

    # Direct bicubic skips pixels, creating wild 0/255 alternating moiré (std dev > 100)
    # Lanczos properly anti-aliases and band-limits to smooth gray (std dev < 20)
    assert old_std > 100.0, f"Expected high aliasing in direct bicubic, got std {old_std}"
    assert new_std < 20.0, f"Expected smooth Nyquist anti-aliasing, got std {new_std}"


def test_resample_slot_quadrant_rotation() -> None:
    """Verifies that quadrant colors are preserved exactly under 0 and 90 degree transforms."""
    quad = synthetic_rgb((400, 400))

    # Rotation 0: (30, 30) is TL (Red), (70, 70) is BR (Yellow)
    t0 = SlotTransform(pan_x_norm=0.0, pan_y_norm=0.0, scale=1.0, rotation_deg=0.0)
    slot_0 = resample_slot(quad, (100, 100), t0)
    assert slot_0.size == (100, 100)
    assert slot_0.getpixel((30, 30)) == QUADRANT_COLORS["tl"]
    assert slot_0.getpixel((70, 70)) == QUADRANT_COLORS["br"]

    # Rotation 90: Top-Left moves to Top-Right; Bottom-Left moves to Top-Left (Blue)
    t90 = SlotTransform(pan_x_norm=0.0, pan_y_norm=0.0, scale=1.0, rotation_deg=90.0)
    slot_90 = resample_slot(quad, (100, 100), t90)
    assert slot_90.size == (100, 100)
    assert slot_90.getpixel((30, 30)) == QUADRANT_COLORS["bl"]
    assert slot_90.getpixel((70, 30)) == QUADRANT_COLORS["tl"]


@pytest.mark.parametrize("angle", [-135.0, -45.0, -15.5, 0.0, 15.5, 45.0, 90.0, 180.0])
def test_resample_slot_arbitrary_rotations(angle: float) -> None:
    """Verifies that arbitrary rotation angles render robustly without errors."""
    src = synthetic_rgb((600, 400))
    slot_size = (200, 150)
    t = SlotTransform(pan_x_norm=0.2, pan_y_norm=-0.1, scale=1.25, rotation_deg=angle)

    result = resample_slot(src, slot_size, t)
    assert result.size == slot_size
    assert result.mode == src.mode


def test_resample_slot_extreme_edge_panning() -> None:
    """Verifies that panning at the extreme normalized boundaries (-1.0, 1.0) does not error."""
    src = synthetic_rgb((500, 500))
    slot_size = (150, 150)

    for pan_x, pan_y in [(-1.0, -1.0), (1.0, 1.0), (-1.0, 1.0), (1.0, -1.0)]:
        t = SlotTransform(pan_x_norm=pan_x, pan_y_norm=pan_y, scale=1.5, rotation_deg=0.0)
        res = resample_slot(src, slot_size, t)
        assert res.size == slot_size


def test_resample_slot_determinism() -> None:
    """Verifies that two consecutive renders of identical parameters produce bit-exact output."""
    src = synthetic_rgb((800, 600))
    t = SlotTransform(pan_x_norm=0.3, pan_y_norm=-0.4, scale=1.3, rotation_deg=22.5)

    r1 = resample_slot(src, (300, 200), t)
    r2 = resample_slot(src, (300, 200), t)
    assert r1.tobytes() == r2.tobytes()
