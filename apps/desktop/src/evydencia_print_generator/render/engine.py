"""Deterministic print rendering engine."""

from __future__ import annotations

import time

from ..domain.job import JobSnapshot
from ..domain.template import Template, TemplateError
from .compose import compose_canvas
from .models import RenderOptions, RenderResult
from .output import atomic_save_image, resolve_output_path


class RenderError(RuntimeError):
    """Raised when rendering cannot proceed or fails."""


def render(
    template: Template,
    snapshot: JobSnapshot,
    options: RenderOptions | None = None,
) -> RenderResult:
    """Render a deterministic print from a Template and JobSnapshot."""
    if not template.is_renderable:
        missing = template.missing_for_render()
        raise TemplateError(f"Template {template.id} is not renderable", missing)

    if snapshot.template_id != template.id:
        raise RenderError(
            f"Job snapshot targets template {snapshot.template_id!r}, "
            f"but engine received {template.id!r}"
        )
    if snapshot.template_version != template.template_version:
        raise RenderError(
            f"Job snapshot version {snapshot.template_version!r} does not match "
            f"template version {template.template_version!r}"
        )

    opts = options or RenderOptions()
    t0 = time.perf_counter()

    # Compose full resolution canvas and extract ICC profile
    composed_image, icc = compose_canvas(template, snapshot, resample=opts.resample)

    # Determine primary source path for output naming
    primary_slot = template.slots[0]
    primary_edit = snapshot.slot_edits[primary_slot.id]
    primary_source = snapshot.sources[primary_edit.source_id]
    primary_source_path = primary_source.path

    # Resolve output path with collision safety
    output_path = resolve_output_path(
        source_path=primary_source_path,
        prefix=template.output.filename_prefix,
        output_format=template.output.format,
        output_dir=opts.output_dir,
        overwrite=opts.overwrite,
    )

    dpi_val = template.canvas.dpi
    dpi_tuple = (dpi_val, dpi_val) if dpi_val is not None else None

    # Save atomically to disk
    bytes_written = atomic_save_image(
        image=composed_image,
        target_path=output_path,
        format=template.output.format,
        quality=template.output.quality,
        dpi=dpi_tuple,
        icc_profile=icc,
        subsampling=opts.subsampling,
    )

    render_time_ms = (time.perf_counter() - t0) * 1000

    return RenderResult(
        output_path=output_path,
        template_id=template.id,
        canvas_size_px=(composed_image.width, composed_image.height),
        dpi=dpi_val or 0,
        render_time_ms=render_time_ms,
        bytes_written=bytes_written,
        primary_source_path=primary_source_path,
    )
