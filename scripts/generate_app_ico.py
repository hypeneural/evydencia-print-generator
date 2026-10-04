#!/usr/bin/env python3
"""Generate dedicated multi-resolution EVYDÊNCIA brand icon (.ico)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = ROOT / "native" / "windows-shell" / "package" / "Assets"
ICO_PATH = ASSETS_DIR / "app.ico"


def create_evydencia_icon() -> Image.Image:
    size = 512
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    pad = 24
    radius = 96
    draw.rounded_rectangle(
        [(pad, pad), (size - pad, size - pad)],
        radius=radius,
        fill=(15, 23, 42, 255),
        outline=(59, 130, 246, 255),
        width=16,
    )

    f_left, f_top = 100, 140
    f_right, f_bottom = 412, 400
    draw.rounded_rectangle(
        [(f_left, f_top), (f_right, f_bottom)],
        radius=36,
        fill=(30, 41, 59, 255),
        outline=(245, 158, 11, 255),
        width=12,
    )

    bump_w, bump_h = 100, 36
    b_left = (size - bump_w) // 2
    b_top = f_top - bump_h + 4
    draw.rounded_rectangle(
        [(b_left, b_top), (b_left + bump_w, f_top + 8)],
        radius=12,
        fill=(245, 158, 11, 255),
    )

    center_x, center_y = size // 2, (f_top + f_bottom) // 2
    lens_r = 76
    draw.ellipse(
        [(center_x - lens_r, center_y - lens_r), (center_x + lens_r, center_y + lens_r)],
        fill=(37, 99, 235, 255),
        outline=(96, 165, 250, 255),
        width=10,
    )

    glare_r = 28
    draw.ellipse(
        [
            (center_x - 30 - glare_r, center_y - 25 - glare_r),
            (center_x - 30 + glare_r, center_y - 25 + glare_r),
        ],
        fill=(255, 255, 255, 180),
    )

    draw.ellipse(
        [(f_right - 44, f_top + 20), (f_right - 20, f_top + 44)],
        fill=(245, 158, 11, 255),
    )
    return img


def main() -> int:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    base_img = create_evydencia_icon()

    sizes = [
        (16, 16),
        (24, 24),
        (32, 32),
        (48, 48),
        (64, 64),
        (128, 128),
        (256, 256),
    ]
    base_img.save(ICO_PATH, format="ICO", sizes=sizes)
    print(f"[OK] Generated {ICO_PATH} ({ICO_PATH.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
