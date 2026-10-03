"""Composition and affine transformation logic for print templates."""

from __future__ import annotations

from PIL import Image, ImageOps

from ..domain.job import JobSnapshot
from ..domain.template import Template
from ..domain.transform import SlotTransform, resolve_placement, slot_to_source_affine


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
) -> tuple[Image.Image, bytes | None]:
    """Compose all slots and overlay onto a canvas.

    Returns:
        (composed_image, primary_icc_profile_bytes)
    """
    canvas_w, canvas_h = template.canvas_px()
    # Base RGBA canvas (white solid background)
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (255, 255, 255, 255))
    primary_icc: bytes | None = None

    for slot in template.slots:
        rect = template.slot_rect_px(slot.id)
        slot_edit = snapshot.slot_edits[slot.id]
        job_source = snapshot.sources[slot_edit.source_id]

        with Image.open(job_source.path) as raw:
            if primary_icc is None:
                primary_icc = raw.info.get("icc_profile")
            oriented = ImageOps.exif_transpose(raw)
            if oriented.mode not in {"RGB", "RGBA"}:
                oriented = oriented.convert("RGB")

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

    # Composite overlay RGBA if template specifies one
    overlay_path = template.overlay_path()
    if overlay_path is not None and overlay_path.is_file():
        with Image.open(overlay_path) as overlay_raw:
            overlay = (
                overlay_raw
                if overlay_raw.size == (canvas_w, canvas_h)
                else overlay_raw.resize((canvas_w, canvas_h), Image.Resampling.LANCZOS)
            )
            if overlay.mode != "RGBA":
                overlay = overlay.convert("RGBA")
            canvas.alpha_composite(overlay)

    # Flatten for JPEG output if needed
    fmt_upper = template.output.format.strip().upper()
    if fmt_upper in {"JPEG", "JPG"}:
        out_rgb = Image.new("RGB", (canvas_w, canvas_h), (255, 255, 255))
        out_rgb.paste(canvas, mask=canvas.split()[3])
        return out_rgb, primary_icc

    return canvas, primary_icc
