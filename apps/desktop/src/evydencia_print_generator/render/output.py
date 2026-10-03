"""Output path resolution and atomic disk writing for production prints."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from PIL import Image


def extension_for_format(fmt: str) -> str:
    fmt_upper = fmt.strip().upper()
    if fmt_upper in {"JPEG", "JPG"}:
        return ".jpg"
    if fmt_upper == "PNG":
        return ".png"
    return f".{fmt.lower().lstrip('.')}"


def resolve_output_path(
    source_path: Path,
    prefix: str,
    output_format: str,
    output_dir: Path | None = None,
    overwrite: bool = False,
) -> Path:
    """Resolve a collision-safe output path in the target directory (default: same as source).

    Rules:
    - Never overwrite the input source photo.
    - If overwrite is False (default) and file exists, append numeric sequence suffix:
      e.g. ``Calendario_0M4A3271.jpg`` -> ``Calendario_0M4A3271_002.jpg`` -> ``..._003.jpg``.
    - Target directory is created if it does not exist.
    """
    dest_dir = output_dir if output_dir is not None else source_path.parent
    dest_dir.mkdir(parents=True, exist_ok=True)

    ext = extension_for_format(output_format)
    stem = source_path.stem
    base_name = f"{prefix}{stem}{ext}"
    candidate = dest_dir / base_name

    # Invariant: Never overwrite input source
    if candidate.resolve() == source_path.resolve():
        raise ValueError(f"Resolved output path matches input source path: {candidate.resolve()}")

    if overwrite or not candidate.exists():
        return candidate

    # Collision resolution: _002, _003, ...
    seq = 2
    while True:
        candidate = dest_dir / f"{prefix}{stem}_{seq:03d}{ext}"
        if candidate.resolve() == source_path.resolve():
            seq += 1
            continue
        if not candidate.exists():
            return candidate
        seq += 1


def atomic_save_image(
    image: Image.Image,
    target_path: Path,
    format: str,
    quality: int = 95,
    dpi: tuple[int, int] | None = None,
    icc_profile: bytes | None = None,
    subsampling: int | str = 0,
) -> int:
    """Save image to disk atomically using a temporary file in the target directory.

    Returns the number of bytes written.
    """
    target_path.parent.mkdir(parents=True, exist_ok=True)
    fmt_upper = format.strip().upper()

    save_kwargs: dict[str, object] = {}
    if dpi is not None:
        save_kwargs["dpi"] = dpi
    if icc_profile is not None:
        save_kwargs["icc_profile"] = icc_profile

    if fmt_upper in {"JPEG", "JPG"}:
        save_kwargs["quality"] = quality
        save_kwargs["subsampling"] = subsampling
        # JPEG does not support alpha; ensure mode is RGB
        if image.mode != "RGB":
            image = image.convert("RGB")
    elif fmt_upper == "PNG":
        save_kwargs["compress_level"] = 6

    # Create temporary file in same directory to ensure atomic replace on all filesystems
    fd, tmp_path_str = tempfile.mkstemp(
        dir=target_path.parent,
        prefix=".render_tmp_",
        suffix=target_path.suffix,
    )
    os.close(fd)
    tmp_path = Path(tmp_path_str)

    try:
        image.save(tmp_path, format=fmt_upper, **save_kwargs)
        os.replace(tmp_path, target_path)
        return target_path.stat().st_size
    except Exception:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        raise
