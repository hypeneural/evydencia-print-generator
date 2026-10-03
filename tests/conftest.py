"""Shared synthetic fixtures. No real photos: every image is generated at test time."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

FIXTURES = Path(__file__).parent / "fixtures"
SYNTHETIC_TEMPLATE = FIXTURES / "templates" / "calendar-synthetic" / "template.json"

QUADRANT_COLORS = {
    "tl": (220, 40, 40),
    "tr": (40, 180, 60),
    "bl": (40, 80, 220),
    "br": (240, 210, 40),
}
MARKER_COLOR = (255, 255, 255)

# Transpose applied to the canonical image before storing, so that
# ImageOps.exif_transpose(stored) == canonical for each EXIF orientation.
EXIF_STORE_OP = {
    1: None,
    3: Image.Transpose.ROTATE_180,
    6: Image.Transpose.ROTATE_90,
    8: Image.Transpose.ROTATE_270,
}


def synthetic_rgb(size: tuple[int, int] = (64, 48)) -> Image.Image:
    """Four colored quadrants + white marker in the top-left corner."""
    w, h = size
    img = Image.new("RGB", size)
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, w // 2 - 1, h // 2 - 1), fill=QUADRANT_COLORS["tl"])
    draw.rectangle((w // 2, 0, w - 1, h // 2 - 1), fill=QUADRANT_COLORS["tr"])
    draw.rectangle((0, h // 2, w // 2 - 1, h - 1), fill=QUADRANT_COLORS["bl"])
    draw.rectangle((w // 2, h // 2, w - 1, h - 1), fill=QUADRANT_COLORS["br"])
    m = max(2, min(w, h) // 8)
    draw.rectangle((0, 0, m - 1, m - 1), fill=MARKER_COLOR)
    return img


def srgb_icc_bytes() -> bytes:
    from PIL import ImageCms

    return ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()


MakeImage = Callable[..., Path]


@pytest.fixture
def make_image(tmp_path: Path) -> MakeImage:
    def _make(
        name: str = "foto.jpg",
        size: tuple[int, int] = (64, 48),
        fmt: str = "JPEG",
        orientation: int = 1,
        icc: bool = False,
        mode: str = "RGB",
        directory: Path | None = None,
    ) -> Path:
        target_dir = directory or tmp_path
        target_dir.mkdir(parents=True, exist_ok=True)
        path = target_dir / name
        img = synthetic_rgb(size)
        op = EXIF_STORE_OP[orientation]
        if op is not None:
            img = img.transpose(op)
        if mode != "RGB":
            img = img.convert(mode)
        kwargs: dict = {}
        if orientation != 1:
            exif = Image.Exif()
            exif[0x0112] = orientation
            kwargs["exif"] = exif.tobytes()
        if icc:
            kwargs["icc_profile"] = srgb_icc_bytes()
        if fmt == "JPEG":
            kwargs["quality"] = 95
        img.save(path, format=fmt, **kwargs)
        return path

    return _make
