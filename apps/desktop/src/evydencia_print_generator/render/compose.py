"""Composition and affine transformation logic for print templates."""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageOps

from ..domain.job import JobSnapshot
from ..domain.template import Template
from ..domain.transform import SlotTransform
from ..imaging.color import get_srgb_profile_bytes, normalize_to_srgb
from .models import RenderError
from .resample import resample_slot


def render_slot(
    src_image: Image.Image,
    slot_size_px: tuple[int, int],
    transform: SlotTransform,
    resample: Image.Resampling = Image.Resampling.BICUBIC,
) -> Image.Image:
    """Render a source image into slot dimensions using ADR-013 high-fidelity resampling."""
    return resample_slot(src_image, slot_size_px, transform)


def compose_canvas(
    template: Template,
    snapshot: JobSnapshot,
    resample: Image.Resampling = Image.Resampling.BICUBIC,
    draw_cut_guidelines: bool = False,
) -> tuple[Image.Image, bytes | None]:
    """Compose all slots and overlay onto a canvas in canonical sRGB color space.

    Returns:
        (composed_image, canonical_srgb_icc_bytes)
    """
    canvas_w, canvas_h = template.canvas_px()
    # Base RGBA canvas (white solid background in canonical sRGB)
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (255, 255, 255, 255))
    srgb_icc = get_srgb_profile_bytes()

    loaded_sources: dict[str, Image.Image] = {}

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
                    # Normalize source directly to canonical sRGB
                    srgb_img = normalize_to_srgb(oriented, icc)
                    if srgb_img.mode not in {"RGB", "RGBA"}:
                        srgb_img = srgb_img.convert("RGB")
                    loaded_sources[job_source.source_id] = srgb_img

            oriented_srgb = loaded_sources[job_source.source_id]

            slot_img = render_slot(
                oriented_srgb,
                (rect.width, rect.height),
                slot_edit.transform,
                resample=resample,
            )

            if slot_img.mode == "RGBA":
                canvas.paste(slot_img, (rect.left, rect.top), mask=slot_img.split()[3])
            else:
                canvas.paste(slot_img, (rect.left, rect.top))
    finally:
        for img in loaded_sources.values():
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
            # Ensure overlay is normalized to sRGB
            overlay_srgb = normalize_to_srgb(overlay_raw)
            overlay = (
                overlay_srgb
                if overlay_srgb.size == (canvas_w, canvas_h)
                else overlay_srgb.resize((canvas_w, canvas_h), Image.Resampling.LANCZOS)
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
        return out_rgb, srgb_icc

    return canvas, srgb_icc
