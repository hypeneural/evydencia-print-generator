"""Canonical sRGB color management and LittleCMS profile conversion (ADR-012)."""

from __future__ import annotations

import io
import logging
from functools import lru_cache

from PIL import Image, ImageCms

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_srgb_profile() -> ImageCms.core.CmsProfile:
    """Return the cached in-memory sRGB LittleCMS profile."""
    return ImageCms.createProfile("sRGB")


@lru_cache(maxsize=1)
def get_srgb_profile_bytes() -> bytes:
    """Return the canonical serialized sRGB ICC profile bytes (588 bytes)."""
    prof = ImageCms.ImageCmsProfile(get_srgb_profile())
    return prof.tobytes()


def is_srgb_profile(icc_bytes: bytes | None) -> bool:
    """Check if an ICC profile byte sequence is already standard sRGB."""
    if not icc_bytes:
        return False
    try:
        prof = ImageCms.ImageCmsProfile(io.BytesIO(icc_bytes))
        name = (ImageCms.getProfileName(prof) or "").lower()
        desc = (ImageCms.getProfileDescription(prof) or "").lower()
        return "srgb" in name or "srgb" in desc or "iec61966-2.1" in desc or "iec61966-2.1" in name
    except Exception:
        return False


def normalize_to_srgb(
    image: Image.Image,
    icc_profile: bytes | None = None,
    rendering_intent: int = ImageCms.Intent.RELATIVE_COLORIMETRIC,
) -> Image.Image:
    """Normalize an image to the canonical sRGB working color space.

    - If an ICC profile is present and diverges from sRGB, LittleCMS applies
      a high-fidelity relative colorimetric transformation.
    - Alpha channels (RGBA) are preserved without modification.
    - Untagged images are treated as standard sRGB.
    - Corrupt or unsupported ICC profiles trigger a graceful fail-safe.
    """
    # Normalize pixel mode to RGB or RGBA
    if image.mode == "CMYK":
        image = image.convert("RGB")
    elif image.mode == "L":
        image = image.convert("RGB")
    elif image.mode == "LA":
        image = image.convert("RGBA")
    elif image.mode not in {"RGB", "RGBA"}:
        target_mode = "RGBA" if "transparency" in image.info or image.mode == "PA" else "RGB"
        image = image.convert(target_mode)

    profile_bytes = icc_profile or image.info.get("icc_profile")
    if not profile_bytes:
        # Untagged: standard sRGB assumption
        return image

    if is_srgb_profile(profile_bytes):
        # Already sRGB: return as is
        return image

    try:
        src_profile = ImageCms.ImageCmsProfile(io.BytesIO(profile_bytes))
        srgb_profile = get_srgb_profile()
        mode = image.mode
        transform = ImageCms.buildTransform(
            src_profile,
            srgb_profile,
            mode,
            mode,
            renderingIntent=rendering_intent,
        )
        return ImageCms.applyTransform(image, transform)
    except ImageCms.PyCMSError as exc:
        logger.warning(
            "Corrupt or unsupported ICC profile encountered (%s); "
            "retaining image pixels in sRGB fallback.",
            exc,
        )
        return image
    except Exception as exc:
        logger.warning(
            "Failed to transform image to sRGB (%s); retaining image in sRGB fallback.",
            exc,
        )
        return image
