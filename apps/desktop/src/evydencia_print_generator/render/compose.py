"""Composition and affine transformation logic for print templates."""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageOps

from ..domain.job import JobSnapshot
from ..domain.template import Template
from ..domain.transform import SlotTransform, resolve_placement, slot_to_source_affine
from .models import RenderError


def render_slot(
    src_image: Image.Image,
    slot_size_px: tuple[int, int],
    transform: SlotTransform,
    resample: Image.Resampling = Image.Resampling.BICUBIC,
) -> Image.Image:
    """Render a source image into slot dimensions using ADR-011 inverse affine transform."""
    sw, sh = src_image.size
    slot_w, slot_h = slot_size_px
    placement = resolve_placement(sw, sh, slot_w, slot_h, transform)
    affine = slot_to_source_affine(sw, sh, placement)
    return src_image.transform(
        (slot_w, slot_h),
        method=Image.Transform.AFFINE,
        data=affine,
        resample=resample,
    )


def compose_canvas(
    template: Template,
    snapshot: JobSnapshot,
    resample: Image.Resampling = Image.Resampling.BICUBIC,
    draw_cut_guidelines: bool = False,
) -> tuple[Image.Image, bytes | None]:
    """Compose all slots and overlay onto a canvas.

    Returns:
        (composed_image, primary_icc_profile_bytes)
    """
    canvas_w, canvas_h = template.canvas_px()
    # Base RGBA canvas (white solid background)
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (255, 255, 255, 255))
    primary_icc: bytes | None = None

    loaded_sources: dict[str, tuple[Image.Image, bytes | None]] = {}

    try:
        for slot in template.slots:
            if slot.id not in snapshot.slot_edits:
                continue
            rect = template.slot_rect_px(slot.id)
            slot_edit = snapshot.slot_edits[slot.id]
            job_source = snapshot.sources[slot_edit.source_id]

            if job_source.source_id not in loaded_sources:
                with Image.open(job_source.path) as raw:
                    icc = raw.info.get("icc_profile")
                    oriented = ImageOps.exif_transpose(raw)
                    if oriented.mode not in {"RGB", "RGBA"}:
                        oriented = oriented.convert("RGB")
                    loaded_sources[job_source.source_id] = (oriented, icc)

            oriented, icc = loaded_sources[job_source.source_id]
            if primary_icc is None and icc is not None:
                primary_icc = icc

            slot_img = render_slot(
                oriented,
                (rect.width, rect.height),
                slot_edit.transform,
                resample=resample,
            )

            if slot_img.mode == "RGBA":
                canvas.paste(slot_img, (rect.left, rect.top), mask=slot_img.split()[3])
            else:
                canvas.paste(slot_img, (rect.left, rect.top))
    finally:
        for img, _ in loaded_sources.values():
            img.close()

    # Composite overlay RGBA if template specifies one, else draw subtle cut guidelines
    overlay_path = template.overlay_path()
    if overlay_path is not None and overlay_path.is_file():
        with Image.open(overlay_path) as overlay_raw:
            if (
                template.overlay is not None
                and template.overlay.required
                and overlay_raw.size != (canvas_w, canvas_h)
            ):
                actual_sz = f"{overlay_raw.size[0]}x{overlay_raw.size[1]}"
                raise RenderError(
                    f"required overlay size mismatch in template '{template.id}': "
                    f"expected {canvas_w}x{canvas_h}, got {actual_sz} "
                    f"({template.overlay.path})"
                )
            overlay = (
                overlay_raw
                if overlay_raw.size == (canvas_w, canvas_h)
                else overlay_raw.resize((canvas_w, canvas_h), Image.Resampling.LANCZOS)
            )
            if overlay.mode != "RGBA":
                overlay = overlay.convert("RGBA")
            canvas.alpha_composite(overlay)
    elif draw_cut_guidelines:
        # Draw 1px hairline cut boundary to guide physical trimming on photo paper
        draw = ImageDraw.Draw(canvas)
        for slot in template.slots:
            rect = template.slot_rect_px(slot.id)
            draw.rectangle(
                [rect.left, rect.top, rect.left + rect.width - 1, rect.top + rect.height - 1],
                outline=(220, 220, 220, 255),
                width=1,
            )

    # Flatten for JPEG output if needed
    fmt_upper = template.output.format.strip().upper()
    if fmt_upper in {"JPEG", "JPG"}:
        out_rgb = Image.new("RGB", (canvas_w, canvas_h), (255, 255, 255))
        out_rgb.paste(canvas, mask=canvas.split()[3])
        return out_rgb, primary_icc

    return canvas, primary_icc
