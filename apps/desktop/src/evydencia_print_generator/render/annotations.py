"""Visual annotations layer for photographic products (keychain customer header)."""
from __future__ import annotations

import functools
import logging
import os
import re
from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image, ImageDraw, ImageFont

if TYPE_CHECKING:
    from ..domain.job import JobSnapshot
    from ..domain.template import Template

logger = logging.getLogger(__name__)

# System fonts candidates in priority order (Windows / Linux)
_FONT_CANDIDATES = [
    r"C:\Windows\Fonts\segoeuib.ttf",
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\segoeui.ttf",
    r"C:\Windows\Fonts\arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]

_GENERIC_FOLDER_NAMES = {
    "desktop",
    "downloads",
    "temp",
    "tmp",
    "fotos",
    "foto_teste",
    "artes natal",
    "print",
    "evydencia-print-generator",
    "output",
    "dist",
    "raw",
    "camera",
    "chaveiro",
    "globo",
    "calendario",
}


def _clean_word_name(name_raw: str) -> str:
    """Extract clean uppercase first name or short name from raw string."""
    cleaned = re.sub(r"(?i)\b(pedido|cliente|foto|fotos|img|dsc|0m4a|canon|nikon)\b", "", name_raw)
    cleaned = cleaned.strip(" -_#")
    words = [w for w in re.findall(r"[\wÀ-ÿ]+", cleaned) if not w.isdigit()]
    if not words:
        return ""
    if len(words) >= 2 and words[0].upper() in {"DE", "DA", "DO", "DOS", "DAS", "ANA"}:
        return f"{words[0]} {words[1]}".upper()
    return words[0].upper()


def extract_client_label(path: Path | str | None, display_name: str = "") -> str:
    """Extract normalized customer label ('NOME ID' or 'NOME') from path or folder.

    Guarantees:
    - Never leaks full filesystem paths.
    - Preserves Portuguese accented characters (JOÃO, MARIA, LAÍS).
    - Falls back to uppercase name when no ID is present.
    - Preserves order ID when present.
    """
    candidates: list[str] = []

    if path:
        p = Path(path)
        # Parent folder name (primary source of customer / order identity)
        if p.parent and p.parent.name.lower() not in _GENERIC_FOLDER_NAMES:
            candidates.append(p.parent.name)
        # File stem
        if p.stem:
            candidates.append(p.stem)

    if display_name:
        stem = Path(display_name).stem
        if stem and stem not in candidates:
            candidates.append(stem)

    for cand in candidates:
        cand_str = cand.strip()
        if not cand_str:
            continue

        # Pattern 1: EvydFlow standard 4-part folder (<Nome> - <Telefone> - <Pacote> - <ID>)
        parts = [part.strip() for part in cand_str.split(" - ")]
        if len(parts) == 4 and parts[3].isdigit():
            clean_name = _clean_word_name(parts[0])
            order_id = parts[3]
            return f"{clean_name} {order_id}" if clean_name else order_id

        # Pattern 2: <ID> - <Nome> or <ID> _ <Nome> (e.g. "1510 - JOÃO")
        m2 = re.match(r"^(\d{1,18})\s*[-_ ]\s*([^\d\-_].+)$", cand_str)
        if m2:
            order_id = m2.group(1).strip()
            clean_name = _clean_word_name(m2.group(2))
            return f"{clean_name} {order_id}" if clean_name else order_id

        # Pattern 3: <Nome> - <ID> or <Nome> <ID> (e.g. "JOÃO 1510", "MARIA 4545", "LAIS 1010")
        m3 = re.match(r"^([^\d#]+?)\s*[-_# ]\s*#?(\d{1,18})$", cand_str)
        if m3:
            clean_name = _clean_word_name(m3.group(1))
            order_id = m3.group(2).strip()
            return f"{clean_name} {order_id}" if clean_name else order_id

        # Pattern 4: Pedido #<ID> - <Nome> or #<ID> <Nome>
        m4 = re.search(r"(?:pedido\s*#?|#)(\d{1,18})", cand_str, re.IGNORECASE)
        if m4:
            order_id = m4.group(1).strip()
            rest = re.sub(r"(?:pedido\s*#?|#)\d{1,18}", "", cand_str, flags=re.IGNORECASE)
            clean_name = _clean_word_name(rest)
            return f"{clean_name} {order_id}" if clean_name else order_id

        # Pattern 5: Fallback without ID (only clean letters/accents)
        clean_only = _clean_word_name(cand_str)
        if clean_only and clean_only.lower() not in _GENERIC_FOLDER_NAMES:
            return clean_only

    return ""


def build_keychain_header_text(template: Template, snapshot: JobSnapshot) -> str:
    """Build unique, de-duplicated customer header string in slot order.

    Format example:
        'JOÃO 1510 | MARIA 4545 | LAIS 1010'
    """
    if template.id != "chaveiro-3x4":
        return ""

    seen: set[str] = set()
    labels: list[str] = []

    for slot in template.slots:
        if slot.id not in snapshot.slot_edits:
            continue
        edit = snapshot.slot_edits[slot.id]
        job_source = snapshot.sources.get(edit.source_id)
        if not job_source:
            continue

        label = extract_client_label(job_source.path, getattr(job_source, "display_name", ""))
        if label and label not in seen:
            seen.add(label)
            labels.append(label)

    return " | ".join(labels)


@functools.lru_cache(maxsize=1)
def _find_font_path() -> str | None:
    for font_path in _FONT_CANDIDATES:
        if os.path.isfile(font_path):
            return font_path
    return None


@functools.lru_cache(maxsize=32)
def _load_font(size_px: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_path = _find_font_path()
    if font_path:
        try:
            return ImageFont.truetype(font_path, size=size_px)
        except Exception:
            pass
    return ImageFont.load_default()


def _get_auto_fit_font(
    text: str,
    max_width: int,
    target_size_px: int = 34,
    min_size_px: int = 16,
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Find the largest font size within bounds that fits max_width."""
    # Test target size first (fits in >95% of typical customer headers)
    target_font = _load_font(target_size_px)
    dummy_img = Image.new("RGBA", (1, 1))
    draw = ImageDraw.Draw(dummy_img)
    try:
        bbox = draw.textbbox((0, 0), text, font=target_font)
        if (bbox[2] - bbox[0]) <= max_width:
            return target_font
    except Exception:
        return target_font

    for sz in range(target_size_px - 2, min_size_px - 1, -2):
        font = _load_font(sz)
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            if (bbox[2] - bbox[0]) <= max_width:
                return font
        except Exception:
            return font
    return _load_font(min_size_px)


def draw_keychain_header(
    canvas: Image.Image,
    template: Template,
    snapshot: JobSnapshot,
) -> None:
    """Draw discrete visual customer annotation header on keychain canvas.

    Guarantees:
    - Runs strictly when template.id == 'chaveiro-3x4'.
    - Positioned inside the 10 mm top margin (y = 0 to 118 px), strictly above slot 1.
    - Zero modification to canvas dimensions, DPI, or slot images.
    - Auto-scales font size to fit width and draws a subtle divider line below.
    """
    if template.id != "chaveiro-3x4":
        return

    text = build_keychain_header_text(template, snapshot)
    if not text:
        return

    dpi = template.canvas.dpi or 300
    # Margins in pixels @ 300 DPI:
    # Slots start at x = 6 mm (71 px), end at x = 210 mm (2480 px)
    # Slots start vertically at y = 10 mm (118 px)
    left = round(6.0 / 25.4 * dpi)        # ~71 px
    right = round(210.0 / 25.4 * dpi)     # ~2480 px
    top = round(1.5 / 25.4 * dpi)         # ~18 px
    bottom = round(8.0 / 25.4 * dpi)      # ~94 px
    divider_y = round(9.0 / 25.4 * dpi)   # ~106 px
    max_width = right - left               # ~2409 px

    draw = ImageDraw.Draw(canvas)

    # 1. Subtle horizontal divider line (2px in soft slate #e2e8f0)
    draw.line([(left, divider_y), (right, divider_y)], fill=(226, 232, 240, 255), width=2)

    # 2. Auto-fit font
    font = _get_auto_fit_font(text, max_width, target_size_px=34, min_size_px=16)

    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
    except Exception:
        text_w = len(text) * 10
        text_h = 24

    text_x = left + max(0, (max_width - text_w) // 2)
    text_y = top + max(0, ((bottom - top) - text_h) // 2)

    # 3. Draw text in dark slate (#334155)
    draw.text((text_x, text_y), text, fill=(51, 65, 85, 255), font=font)
