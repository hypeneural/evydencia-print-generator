"""Unit and regression tests for canonical sRGB color management (ADR-012)."""

from __future__ import annotations

import base64
from pathlib import Path

from conftest import synthetic_rgb
from evydencia_print_generator.imaging.color import (
    get_srgb_profile_bytes,
    is_srgb_profile,
    normalize_to_srgb,
)
from evydencia_print_generator.ingest.preview import generate_preview_image
from PIL import Image

# Canonical 504-byte Rec. 2020 ICC profile (Adobe Systems) as synthetic fixture
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


def test_srgb_profile_generation() -> None:
    """Verifies that canonical sRGB profile bytes are generated and match expected length."""
    icc_bytes = get_srgb_profile_bytes()
    assert isinstance(icc_bytes, bytes)
    assert len(icc_bytes) == 588
    assert is_srgb_profile(icc_bytes) is True


def test_is_srgb_profile_detection() -> None:
    """Tests detection of sRGB vs non-sRGB, empty or corrupted profiles."""
    srgb_bytes = get_srgb_profile_bytes()
    assert is_srgb_profile(srgb_bytes) is True
    assert is_srgb_profile(REC2020_ICC) is False
    assert is_srgb_profile(None) is False
    assert is_srgb_profile(b"") is False
    assert is_srgb_profile(b"corrupt_icc_profile_data_not_valid") is False


def test_normalize_to_srgb_untagged() -> None:
    """Untagged images must be treated as sRGB without modifying pixel data."""
    im = synthetic_rgb((50, 50))
    norm = normalize_to_srgb(im)
    assert norm.size == (50, 50)
    assert norm.mode == "RGB"
    # Pure pixel comparison: untagged remains identical
    assert norm.tobytes() == im.tobytes()


def test_normalize_to_srgb_rec2020() -> None:
    """Verifies that wide gamut Rec. 2020 pixels are accurately transformed into sRGB."""
    # Skin tone test point: (235, 223, 207) in Rec. 2020 transforms to (245, 225, 210) in sRGB
    im = Image.new("RGB", (10, 10), (235, 223, 207))
    norm = normalize_to_srgb(im, icc_profile=REC2020_ICC)
    assert norm.size == (10, 10)
    assert norm.mode == "RGB"
    px = norm.getpixel((5, 5))
    assert px == (245, 225, 210)


def test_normalize_to_srgb_rgba_preserves_alpha() -> None:
    """Verifies that RGBA images have colors mapped while alpha is preserved bit-exact."""
    im = Image.new("RGBA", (10, 10), (235, 223, 207, 128))
    norm = normalize_to_srgb(im, icc_profile=REC2020_ICC)
    assert norm.size == (10, 10)
    assert norm.mode == "RGBA"
    px = norm.getpixel((5, 5))
    assert px == (245, 225, 210, 128)


def test_normalize_to_srgb_cmyk_and_grayscale() -> None:
    """Verifies mode conversion for CMYK and Grayscale inputs."""
    im_cmyk = Image.new("CMYK", (20, 20), (0, 100, 100, 0))
    norm_cmyk = normalize_to_srgb(im_cmyk)
    assert norm_cmyk.mode == "RGB"

    im_gray = Image.new("L", (20, 20), 128)
    norm_gray = normalize_to_srgb(im_gray)
    assert norm_gray.mode == "RGB"


def test_normalize_to_srgb_corrupt_profile_safe_fallback() -> None:
    """Verifies graceful fallback with zero crash when encountering corrupt ICC profile bytes."""
    im = synthetic_rgb((20, 20))
    orig_bytes = im.tobytes()
    # Pass corrupt bytes
    norm = normalize_to_srgb(im, icc_profile=b"corrupt_invalid_bytes")
    assert norm.size == (20, 20)
    assert norm.tobytes() == orig_bytes


def test_preview_proxy_generates_srgb_profile(tmp_path: Path) -> None:
    """Verifies that generate_preview_image produces an sRGB image with sRGB ICC bytes."""
    test_photo = tmp_path / "rec2020_photo.jpg"
    im = synthetic_rgb((1000, 800))
    im.save(test_photo, format="JPEG", quality=95, icc_profile=REC2020_ICC)

    preview_img, preview_icc = generate_preview_image(test_photo, max_side=500)
    assert preview_img.size == (500, 400)
    assert preview_icc is not None
    assert is_srgb_profile(preview_icc) is True
