"""ADR-011 transform math: analytic checks independent of the committed vectors."""

from __future__ import annotations

import json
import math
import random
from pathlib import Path

import pytest
from evydencia_print_generator.domain.transform import (
    SCALE_MAX,
    SlotTransform,
    clamp_transform,
    cover_scale,
    normalize_rotation,
    pan_by_slot_delta,
    resolve_placement,
    rotated_slot_bbox,
    slot_to_source_affine,
    source_to_slot,
)

VECTORS = Path(__file__).parent / "fixtures" / "transform_vectors.json"


def _apply_affine(coeffs, u, v):
    a, b, c, d, e, f = coeffs
    return a * u + b * v + c, d * u + e * v + f


def test_normalize_rotation() -> None:
    assert normalize_rotation(0) == 0.0
    assert normalize_rotation(180) == -180.0
    assert normalize_rotation(-180) == -180.0
    assert normalize_rotation(270) == -90.0
    assert normalize_rotation(-450) == -90.0
    assert normalize_rotation(359.5) == pytest.approx(-0.5)
    assert math.copysign(1.0, normalize_rotation(-360)) == 1.0  # no -0.0


def test_clamp_transform_limits() -> None:
    t = clamp_transform(SlotTransform(3, -3, 20, 540))
    assert (t.pan_x_norm, t.pan_y_norm, t.scale, t.rotation_deg) == (1.0, -1.0, SCALE_MAX, -180.0)
    assert clamp_transform(SlotTransform(scale=0.2)).scale == 1.0


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
def test_rejects_non_finite(bad: float) -> None:
    with pytest.raises(ValueError):
        clamp_transform(SlotTransform(pan_x_norm=bad))
    with pytest.raises(ValueError):
        clamp_transform(SlotTransform(rotation_deg=bad))


def test_rejects_non_positive_dimensions() -> None:
    with pytest.raises(ValueError):
        cover_scale(0, 100, 10, 10, 0)
    with pytest.raises(ValueError):
        rotated_slot_bbox(10, -1, 0)


def test_cover_scale_known_values() -> None:
    assert cover_scale(4000, 3000, 1000, 1000, 0) == pytest.approx(1 / 3)
    assert cover_scale(4000, 3000, 1000, 500, 0) == pytest.approx(0.25)
    # rotated 90: slot bbox in photo frame becomes 500x1000
    assert cover_scale(4000, 3000, 1000, 500, 90) == pytest.approx(1 / 3)
    # rotated 45: square slot bbox grows by sqrt(2)
    assert cover_scale(3000, 3000, 1000, 1000, 45) == pytest.approx(math.sqrt(2) / 3)


def test_exact_trig_for_right_angles() -> None:
    assert rotated_slot_bbox(1000, 500, 90) == (500.0, 1000.0)
    assert rotated_slot_bbox(1000, 500, -90) == (500.0, 1000.0)
    assert rotated_slot_bbox(1000, 500, 180) == (1000.0, 500.0)


def test_identity_is_centered() -> None:
    p = resolve_placement(4000, 3000, 1000, 1000, SlotTransform())
    assert (p.center_x, p.center_y) == (500.0, 500.0)
    assert p.max_dx == pytest.approx(500 / 3)  # (4000/3 - 1000) / 2
    assert p.max_dy == 0.0


def test_pan_plus_one_is_flush_with_left_edge() -> None:
    p = resolve_placement(4000, 3000, 1000, 1000, SlotTransform(pan_x_norm=1))
    left_edge_x, _ = source_to_slot(4000, 3000, p, 0, 1500)
    assert left_edge_x == pytest.approx(0.0, abs=1e-9)
    # positive pan moves content to +x, i.e. reveals the photo's left part
    assert p.center_x > 500


def test_rotation_is_clockwise_on_screen() -> None:
    p = resolve_placement(3000, 3000, 1000, 1000, SlotTransform(rotation_deg=90))
    # photo top-left corner lands at slot top-right after a clockwise quarter turn
    u, v = source_to_slot(3000, 3000, p, 0, 0)
    assert (u, v) == (pytest.approx(1000), pytest.approx(0, abs=1e-9))


def test_affine_inverts_forward_map() -> None:
    t = SlotTransform(0.4, -0.7, 1.75, -12.5)
    p = resolve_placement(5472, 3648, 1181, 1654, t)
    coeffs = slot_to_source_affine(5472, 3648, p)
    for x, y in [(0, 0), (5472, 3648), (1234.5, 987.25)]:
        u, v = source_to_slot(5472, 3648, p, x, y)
        bx, by = _apply_affine(coeffs, u, v)
        assert (bx, by) == (pytest.approx(x), pytest.approx(y))


def test_never_reveals_empty_area_randomized() -> None:
    rng = random.Random(20261003)
    for _ in range(2000):
        src_w, src_h = rng.randint(200, 8000), rng.randint(200, 8000)
        slot_w, slot_h = rng.randint(50, 3000), rng.randint(50, 3000)
        t = SlotTransform(
            pan_x_norm=rng.uniform(-1.5, 1.5),
            pan_y_norm=rng.uniform(-1.5, 1.5),
            scale=rng.uniform(0.5, 9),
            rotation_deg=rng.uniform(-400, 400),
        )
        p = resolve_placement(src_w, src_h, slot_w, slot_h, t)
        coeffs = slot_to_source_affine(src_w, src_h, p)
        eps = 1e-6 * max(src_w, src_h)
        for u, v in [(0, 0), (slot_w, 0), (0, slot_h), (slot_w, slot_h)]:
            x, y = _apply_affine(coeffs, u, v)
            assert -eps <= x <= src_w + eps, (t, src_w, src_h, slot_w, slot_h, x)
            assert -eps <= y <= src_h + eps, (t, src_w, src_h, slot_w, slot_h, y)


def test_drag_rot0_moves_pan_x() -> None:
    t = pan_by_slot_delta(4000, 3000, 1000, 1000, SlotTransform(scale=1.5), 100, 0)
    p = resolve_placement(4000, 3000, 1000, 1000, SlotTransform(scale=1.5))
    assert t.pan_x_norm == pytest.approx(100 / p.max_dx)
    assert t.pan_y_norm == 0.0


def test_drag_rot90_maps_screen_x_to_negative_photo_y() -> None:
    base = SlotTransform(scale=1.5, rotation_deg=90)
    t = pan_by_slot_delta(4000, 3000, 1000, 500, base, 100, 0)
    assert t.pan_x_norm == 0.0
    assert t.pan_y_norm < 0.0


def test_drag_follows_pointer_in_slot_space() -> None:
    base = SlotTransform(0.1, -0.2, 2.0, 30)
    before = resolve_placement(4000, 3000, 1000, 800, base)
    moved = pan_by_slot_delta(4000, 3000, 1000, 800, base, 12, -7)
    after = resolve_placement(4000, 3000, 1000, 800, moved)
    assert after.center_x - before.center_x == pytest.approx(12)
    assert after.center_y - before.center_y == pytest.approx(-7)


def test_committed_vectors_match_implementation() -> None:
    data = json.loads(VECTORS.read_text(encoding="utf-8"))
    tol = data["tolerance"]
    assert data["adr"] == "ADR-011"
    assert data["placement_cases"] and data["drag_cases"]
    for case in data["placement_cases"]:
        (sw, sh), (w, h) = case["src"], case["slot"]
        t = SlotTransform(**case["transform"])
        exp = case["expected"]
        clamped = clamp_transform(t)
        assert clamped == SlotTransform(**exp["clamped"]), case["name"]
        p = resolve_placement(sw, sh, w, h, t)
        assert cover_scale(sw, sh, w, h, clamped.rotation_deg) == pytest.approx(
            exp["cover_scale"], abs=tol
        )
        assert p.effective_scale == pytest.approx(exp["effective_scale"], abs=tol), case["name"]
        assert [p.center_x, p.center_y] == pytest.approx(exp["center"], abs=tol), case["name"]
        assert [p.max_dx, p.max_dy] == pytest.approx(exp["max_pan"], abs=tol), case["name"]
        assert list(slot_to_source_affine(sw, sh, p)) == pytest.approx(exp["affine"], abs=tol), (
            case["name"]
        )
    for case in data["drag_cases"]:
        (sw, sh), (w, h) = case["src"], case["slot"]
        result = pan_by_slot_delta(sw, sh, w, h, SlotTransform(**case["transform"]), *case["delta"])
        exp = SlotTransform(**case["expected"])
        assert result.pan_x_norm == pytest.approx(exp.pan_x_norm, abs=tol), case["name"]
        assert result.pan_y_norm == pytest.approx(exp.pan_y_norm, abs=tol), case["name"]
        assert result.scale == pytest.approx(exp.scale, abs=tol)
        assert result.rotation_deg == pytest.approx(exp.rotation_deg, abs=tol)
