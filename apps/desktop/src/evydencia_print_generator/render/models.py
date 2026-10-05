"""Render domain models and options."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image


class RenderError(RuntimeError):
    """Raised when rendering cannot proceed or fails."""


@dataclass(frozen=True)
class RenderOptions:
    """Options for rendering execution."""

    output_dir: Path | None = None  # None -> same directory as primary source photo
    overwrite: bool = False  # False -> collision-safe numeric suffixes (_002, _003)
    resample: Image.Resampling = Image.Resampling.BICUBIC
    subsampling: int | str = 0  # 0 = 4:4:4 (no chroma subsampling)
    draw_cut_guidelines: bool = False  # True -> 1px hairline cut marks around slots


@dataclass(frozen=True)
class RenderResult:
    """Outcome of a successful render."""

    output_path: Path
    template_id: str
    canvas_size_px: tuple[int, int]
    dpi: int
    render_time_ms: float
    bytes_written: int
    primary_source_path: Path
