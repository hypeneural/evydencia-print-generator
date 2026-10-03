"""Pure slot-transform math defined by ADR-011.

No Pillow / IO here: this module is mirrored 1:1 by ``apps/ui/src/domain/transform.ts`` and
both are checked against ``tests/fixtures/transform_vectors.json``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

SCALE_MIN = 1.0
SCALE_MAX = 8.0
PAN_LIMIT = 1.0

# Exact (cos, sin) for multiples of 90 degrees, keyed by rotation in [-180, 180).
_EXACT_TRIG = {
    0.0: (1.0, 0.0),
    90.0: (0.0, 1.0),
    -180.0: (-1.0, 0.0),
    -90.0: (0.0, -1.0),
}


@dataclass(frozen=True)
class SlotTransform:
    """Persisted, window-independent transform of a source inside a slot."""

    pan_x_norm: float = 0.0
    pan_y_norm: float = 0.0
    scale: float = 1.0
    rotation_deg: float = 0.0


@dataclass(frozen=True)
class Placement:
    """Resolved placement of the (EXIF-oriented) source inside a slot, in slot pixels."""

    effective_scale: float  # source px -> slot px
    rotation_deg: float  # normalized, clockwise-positive
    center_x: float  # source center in slot coordinates
    center_y: float
    max_dx: float  # pan range (half-travel) along photo x axis, slot px
    max_dy: float  # pan range (half-travel) along photo y axis, slot px


def _require_finite(name: str, value: float) -> float:
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return value


def _require_positive(name: str, value: float) -> float:
    value = _require_finite(name, value)
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


def normalize_rotation(rotation_deg: float) -> float:
    """Normalize degrees to [-180, 180)."""
    deg = _require_finite("rotation_deg", rotation_deg)
    normalized = math.fmod(deg + 180.0, 360.0)
    if normalized < 0:
        normalized += 360.0
    normalized -= 180.0
    # Avoid -0.0 leaking into vectors/UI.
    return normalized + 0.0


def rotation_cos_sin(rotation_deg: float) -> tuple[float, float]:
    """(cos, sin) of a normalized rotation, exact for multiples of 90 degrees."""
    deg = normalize_rotation(rotation_deg)
    exact = _EXACT_TRIG.get(deg)
    if exact is not None:
        return exact
    rad = math.radians(deg)
    return math.cos(rad), math.sin(rad)


def clamp(value: float, low: float, high: float) -> float:
    return min(high, max(low, value))


def clamp_transform(transform: SlotTransform) -> SlotTransform:
    """Clamp pan/scale and normalize rotation. Rejects non-finite values."""
    pan_x = _require_finite("pan_x_norm", transform.pan_x_norm)
    pan_y = _require_finite("pan_y_norm", transform.pan_y_norm)
    scale = _require_finite("scale", transform.scale)
    return SlotTransform(
        pan_x_norm=clamp(pan_x, -PAN_LIMIT, PAN_LIMIT) + 0.0,
        pan_y_norm=clamp(pan_y, -PAN_LIMIT, PAN_LIMIT) + 0.0,
        scale=clamp(scale, SCALE_MIN, SCALE_MAX),
        rotation_deg=normalize_rotation(transform.rotation_deg),
    )


def rotated_slot_bbox(slot_w: float, slot_h: float, rotation_deg: float) -> tuple[float, float]:
    """Bounding box (W', H') of the slot expressed in the photo's (rotated) frame."""
    slot_w = _require_positive("slot_w", slot_w)
    slot_h = _require_positive("slot_h", slot_h)
    cos_t, sin_t = rotation_cos_sin(rotation_deg)
    c, s = abs(cos_t), abs(sin_t)
    return slot_w * c + slot_h * s, slot_w * s + slot_h * c


def cover_scale(
    src_w: float, src_h: float, slot_w: float, slot_h: float, rotation_deg: float
) -> float:
    """Minimum source->slot scale so the rotated source fully covers the slot."""
    src_w = _require_positive("src_w", src_w)
    src_h = _require_positive("src_h", src_h)
    bbox_w, bbox_h = rotated_slot_bbox(slot_w, slot_h, rotation_deg)
    return max(bbox_w / src_w, bbox_h / src_h)


def resolve_placement(
    src_w: float, src_h: float, slot_w: float, slot_h: float, transform: SlotTransform
) -> Placement:
    """Resolve a persisted transform into a concrete placement (ADR-011)."""
    t = clamp_transform(transform)
    bbox_w, bbox_h = rotated_slot_bbox(slot_w, slot_h, t.rotation_deg)
    s_eff = t.scale * cover_scale(src_w, src_h, slot_w, slot_h, t.rotation_deg)
    max_dx = max(0.0, (src_w * s_eff - bbox_w) / 2.0)
    max_dy = max(0.0, (src_h * s_eff - bbox_h) / 2.0)
    off_x = t.pan_x_norm * max_dx
    off_y = t.pan_y_norm * max_dy
    cos_t, sin_t = rotation_cos_sin(t.rotation_deg)
    center_x = slot_w / 2.0 + cos_t * off_x - sin_t * off_y
    center_y = slot_h / 2.0 + sin_t * off_x + cos_t * off_y
    return Placement(
        effective_scale=s_eff,
        rotation_deg=t.rotation_deg,
        center_x=center_x,
        center_y=center_y,
        max_dx=max_dx,
        max_dy=max_dy,
    )


def slot_to_source_affine(
    src_w: float, src_h: float, placement: Placement
) -> tuple[float, float, float, float, float, float]:
    """Inverse affine (a, b, c, d, e, f) mapping slot coords (u, v) -> source coords (x, y).

    ``x = a*u + b*v + c`` and ``y = d*u + e*v + f`` — the layout expected by
    ``PIL.Image.transform(..., Image.Transform.AFFINE, data)``.
    """
    s = placement.effective_scale
    cos_t, sin_t = rotation_cos_sin(placement.rotation_deg)
    cx, cy = placement.center_x, placement.center_y
    a = cos_t / s
    b = sin_t / s
    c = src_w / 2.0 - (cos_t * cx + sin_t * cy) / s
    d = -sin_t / s
    e = cos_t / s
    f = src_h / 2.0 - (-sin_t * cx + cos_t * cy) / s
    return a, b, c, d, e, f


def source_to_slot(
    src_w: float, src_h: float, placement: Placement, x: float, y: float
) -> tuple[float, float]:
    """Forward map of a source point (x, y) to slot coordinates."""
    s = placement.effective_scale
    cos_t, sin_t = rotation_cos_sin(placement.rotation_deg)
    px = (x - src_w / 2.0) * s
    py = (y - src_h / 2.0) * s
    return (
        placement.center_x + cos_t * px - sin_t * py,
        placement.center_y + sin_t * px + cos_t * py,
    )


def pan_by_slot_delta(
    src_w: float,
    src_h: float,
    slot_w: float,
    slot_h: float,
    transform: SlotTransform,
    dx_slot: float,
    dy_slot: float,
) -> SlotTransform:
    """Apply a drag expressed in slot pixels (screen axes) and return a clamped transform."""
    dx_slot = _require_finite("dx_slot", dx_slot)
    dy_slot = _require_finite("dy_slot", dy_slot)
    t = clamp_transform(transform)
    placement = resolve_placement(src_w, src_h, slot_w, slot_h, t)
    cos_t, sin_t = rotation_cos_sin(t.rotation_deg)
    # Rotate the screen-axis delta into the photo frame (R(θ)^-1 = R(θ)^T).
    d_photo_x = cos_t * dx_slot + sin_t * dy_slot
    d_photo_y = -sin_t * dx_slot + cos_t * dy_slot
    pan_x = t.pan_x_norm
    pan_y = t.pan_y_norm
    if placement.max_dx > 0:
        pan_x += d_photo_x / placement.max_dx
    if placement.max_dy > 0:
        pan_y += d_photo_y / placement.max_dy
    return clamp_transform(
        SlotTransform(
            pan_x_norm=pan_x, pan_y_norm=pan_y, scale=t.scale, rotation_deg=t.rotation_deg
        )
    )
