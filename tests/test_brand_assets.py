"""Tests for canonical EVYDÊNCIA brand assets and absence of placeholders."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PKG_ASSETS = ROOT / "native" / "windows-shell" / "package" / "Assets"
SHELL_ASSETS = ROOT / "native" / "windows-shell" / "assets"
UI_PUBLIC = ROOT / "apps" / "ui" / "public"


def test_package_and_shell_brand_assets_exist() -> None:
    expected_files = [
        PKG_ASSETS / "app.ico",
        SHELL_ASSETS / "app.ico",
        PKG_ASSETS / "Square44x44Logo.png",
        PKG_ASSETS / "Square150x150Logo.png",
        PKG_ASSETS / "StoreLogo.png",
        UI_PUBLIC / "favicon.ico",
        UI_PUBLIC / "app-icon-32.png",
        UI_PUBLIC / "app-icon-64.png",
    ]
    for path in expected_files:
        assert path.is_file(), f"Missing brand asset: {path}"
        assert path.stat().st_size > 500, f"Asset file size too small: {path}"


def test_msix_logos_dimensions_and_modes() -> None:
    sq44 = PKG_ASSETS / "Square44x44Logo.png"
    with Image.open(sq44) as img:
        assert img.size == (44, 44)
        assert img.mode == "RGBA"

    sq150 = PKG_ASSETS / "Square150x150Logo.png"
    with Image.open(sq150) as img:
        assert img.size == (150, 150)
        assert img.mode == "RGBA"

    store = PKG_ASSETS / "StoreLogo.png"
    with Image.open(store) as img:
        assert img.size == (50, 50)
        assert img.mode == "RGBA"


def test_no_blue_placeholder_blocks() -> None:
    """Verify that MSIX logos are not the legacy solid blue+white placeholder blocks."""
    for filename in ["Square44x44Logo.png", "Square150x150Logo.png", "StoreLogo.png"]:
        path = PKG_ASSETS / filename
        with Image.open(path) as img:
            # Check corners have transparency (anti-aliased rounded rect)
            corner_pixel = img.getpixel((0, 0))
            assert corner_pixel[3] == 0, f"Expected transparent corner on {filename}"


def test_web_icons_dimensions() -> None:
    with Image.open(UI_PUBLIC / "app-icon-32.png") as img:
        assert img.size == (32, 32)
        assert img.mode == "RGBA"

    with Image.open(UI_PUBLIC / "app-icon-64.png") as img:
        assert img.size == (64, 64)
        assert img.mode == "RGBA"
