import pytest
from evydencia_print_generator.geometry import mm_to_px


def test_mm_to_px_known_values_at_300_dpi() -> None:
    assert mm_to_px(216, 300) == 2551
    assert mm_to_px(152, 300) == 1795
    assert mm_to_px(34, 300) == 402
    assert mm_to_px(44, 300) == 520
    assert mm_to_px(50, 300) == 591
    assert mm_to_px(80, 300) == 945


def test_mm_to_px_validates_inputs() -> None:
    with pytest.raises(ValueError):
        mm_to_px(-1, 300)
    with pytest.raises(ValueError):
        mm_to_px(10, 0)
