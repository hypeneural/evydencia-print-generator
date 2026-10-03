from __future__ import annotations

MM_PER_INCH = 25.4


def mm_to_px(mm: float, dpi: int) -> int:
    """Convert physical millimeters to pixels using the repository rounding rule."""
    if mm < 0:
        raise ValueError("mm must be non-negative")
    if dpi <= 0:
        raise ValueError("dpi must be positive")
    return round(mm / MM_PER_INCH * dpi)
