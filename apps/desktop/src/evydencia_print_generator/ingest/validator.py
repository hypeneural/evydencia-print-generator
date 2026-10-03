"""Validate that a file is a real, supported image and read the metadata ingest needs."""

from __future__ import annotations

import io
import struct
import warnings
from pathlib import Path

from PIL import ExifTags, Image, UnidentifiedImageError

from .models import ImageProbe, RejectCode

SUPPORTED_FORMATS = ("JPEG", "PNG")
# Canon (and other) cameras embed a secondary image (MPF); Pillow reports these as "MPO".
# Frame 0 is the primary JPEG, so for the product it is a JPEG.
_NORMALIZED_FORMATS = {"MPO": "JPEG"}
# CMYK/LAB/etc. are rejected until a lab color policy exists (docs/IMAGE_PIPELINE.md).
SUPPORTED_MODES = frozenset(
    {"1", "L", "LA", "P", "PA", "RGB", "RGBA", "I", "I;16", "I;16B", "I;16L"}
)
MAX_PIXELS = 150_000_000  # ~150 MP; above this we refuse instead of risking RAM blow-up
EXIF_ORIENTATION_TAG = 0x0112
EXIF_COLOR_SPACE_TAG = 0xA001
_EXIF_COLOR_SPACES = {1: "sRGB", 0xFFFF: "uncalibrated"}
_SWAPPING_ORIENTATIONS = frozenset({5, 6, 7, 8})


class ProbeError(Exception):
    def __init__(self, code: RejectCode, detail: str = "") -> None:
        super().__init__(f"{code}: {detail}" if detail else str(code))
        self.code = code
        self.detail = detail


def _icc_description(icc: bytes) -> str | None:
    try:
        from PIL import ImageCms

        profile = ImageCms.ImageCmsProfile(io.BytesIO(icc))
        return ImageCms.getProfileDescription(profile).strip() or None
    except Exception:  # noqa: BLE001 - description is informative only
        return None


def probe_image(path: Path) -> ImageProbe:
    """Header-level validation + metadata. Does not decode full pixel data for JPEG."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", Image.DecompressionBombWarning)
            # Pass 1: format/size/mode + structural verify (verify() must follow open()).
            with Image.open(path, formats=SUPPORTED_FORMATS) as im:
                fmt = im.format
                stored_w, stored_h = im.size
                mode = im.mode
                if stored_w <= 0 or stored_h <= 0:
                    raise ProbeError(RejectCode.CORRUPT, "empty image")
                if stored_w * stored_h > MAX_PIXELS:
                    raise ProbeError(RejectCode.TOO_LARGE, f"{stored_w}x{stored_h}")
                if mode not in SUPPORTED_MODES:
                    raise ProbeError(RejectCode.UNSUPPORTED_COLOR_MODE, mode)
                im.verify()
            # Pass 2: metadata (verify() leaves the image unusable).
            with Image.open(path, formats=SUPPORTED_FORMATS) as im:
                exif = im.getexif()
                raw_orientation = exif.get(EXIF_ORIENTATION_TAG, 1)
                raw_color_space = exif.get_ifd(ExifTags.IFD.Exif).get(EXIF_COLOR_SPACE_TAG)
                icc = im.info.get("icc_profile")
    except ProbeError:
        raise
    except UnidentifiedImageError as exc:
        raise ProbeError(RejectCode.UNSUPPORTED_FORMAT) from exc
    except Image.DecompressionBombError as exc:
        raise ProbeError(RejectCode.TOO_LARGE) from exc
    except (OSError, SyntaxError, ValueError, struct.error, EOFError) as exc:
        raise ProbeError(RejectCode.CORRUPT, type(exc).__name__) from exc

    orientation = raw_orientation if isinstance(raw_orientation, int) else 1
    if not 1 <= orientation <= 8:
        orientation = 1
    if orientation in _SWAPPING_ORIENTATIONS:
        width, height = stored_h, stored_w
    else:
        width, height = stored_w, stored_h

    return ImageProbe(
        format=_NORMALIZED_FORMATS.get(fmt, fmt),
        mode=mode,
        width_px=width,
        height_px=height,
        stored_width_px=stored_w,
        stored_height_px=stored_h,
        exif_orientation=orientation,
        has_icc=bool(icc),
        icc_description=_icc_description(icc) if icc else None,
        container=fmt,
        exif_color_space=_EXIF_COLOR_SPACES.get(raw_color_space),
    )
