#!/usr/bin/env python3
"""Canonical EVYDÊNCIA Brand Assets Generator.

Generates all desktop, Windows Shell, MSIX package, and web/Vite application icons
from a single canonical master design:
- native/windows-shell/package/Assets/app.ico
- native/windows-shell/assets/app.ico
- native/windows-shell/package/Assets/Square44x44Logo.png (44x44)
- native/windows-shell/package/Assets/Square150x150Logo.png (150x150)
- native/windows-shell/package/Assets/StoreLogo.png (50x50)
- apps/ui/public/favicon.ico (16, 24, 32, 48)
- apps/ui/public/app-icon-32.png (32x32)
- apps/ui/public/app-icon-64.png (64x64)
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]

# Output target paths
PKG_ASSETS_DIR = ROOT / "native" / "windows-shell" / "package" / "Assets"
SHELL_ASSETS_DIR = ROOT / "native" / "windows-shell" / "assets"
UI_PUBLIC_DIR = ROOT / "apps/ui/public"


def create_master_evydencia_icon(size: int = 512) -> Image.Image:
    """Draw high-resolution canonical master EVYDÊNCIA camera brand icon."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Scale factor relative to 512px design
    s = size / 512.0

    pad = int(24 * s)
    radius = int(96 * s)
    draw.rounded_rectangle(
        [(pad, pad), (size - pad, size - pad)],
        radius=radius,
        fill=(15, 23, 42, 255),       # slate-900 background
        outline=(59, 130, 246, 255),   # blue-500 border
        width=max(1, int(16 * s)),
    )

    # Camera body
    f_left, f_top = int(100 * s), int(140 * s)
    f_right, f_bottom = int(412 * s), int(400 * s)
    draw.rounded_rectangle(
        [(f_left, f_top), (f_right, f_bottom)],
        radius=int(36 * s),
        fill=(30, 41, 59, 255),       # slate-800
        outline=(245, 158, 11, 255),   # amber-500
        width=max(1, int(12 * s)),
    )

    # Camera top flash bump
    bump_w, bump_h = int(100 * s), int(36 * s)
    b_left = (size - bump_w) // 2
    b_top = f_top - bump_h + max(1, int(4 * s))
    draw.rounded_rectangle(
        [(b_left, b_top), (b_left + bump_w, f_top + max(1, int(8 * s)))],
        radius=int(12 * s),
        fill=(245, 158, 11, 255),
    )

    # Lens outer ring & fill
    center_x, center_y = size // 2, (f_top + f_bottom) // 2
    lens_r = int(76 * s)
    draw.ellipse(
        [(center_x - lens_r, center_y - lens_r), (center_x + lens_r, center_y + lens_r)],
        fill=(37, 99, 235, 255),      # blue-600
        outline=(96, 165, 250, 255),  # blue-400
        width=max(1, int(10 * s)),
    )

    # Glare reflection
    glare_r = int(28 * s)
    gx = center_x - int(30 * s)
    gy = center_y - int(25 * s)
    draw.ellipse(
        [(gx - glare_r, gy - glare_r), (gx + glare_r, gy + glare_r)],
        fill=(255, 255, 255, 180),
    )

    # Red/amber sensor lamp
    lamp_x1 = f_right - int(44 * s)
    lamp_y1 = f_top + int(20 * s)
    lamp_x2 = f_right - int(20 * s)
    lamp_y2 = f_top + int(44 * s)
    draw.ellipse(
        [(lamp_x1, lamp_y1), (lamp_x2, lamp_y2)],
        fill=(245, 158, 11, 255),
    )

    return img


def generate_png_icon(target_size: tuple[int, int], master: Image.Image) -> Image.Image:
    """Generate cleanly downsampled RGBA icon using LANCZOS."""
    return master.resize(target_size, Image.Resampling.LANCZOS)


def main() -> int:
    PKG_ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    SHELL_ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    UI_PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

    master = create_master_evydencia_icon(512)

    # 1. Multi-resolution .ico for Windows Shell & Package (16 to 256)
    ico_sizes = [
        (16, 16),
        (24, 24),
        (32, 32),
        (48, 48),
        (64, 64),
        (128, 128),
        (256, 256),
    ]
    pkg_ico = PKG_ASSETS_DIR / "app.ico"
    master.save(pkg_ico, format="ICO", sizes=ico_sizes)
    print(f"[OK] Generated {pkg_ico} ({pkg_ico.stat().st_size} bytes)")

    shell_ico = SHELL_ASSETS_DIR / "app.ico"
    master.save(shell_ico, format="ICO", sizes=ico_sizes)
    print(f"[OK] Generated {shell_ico} ({shell_ico.stat().st_size} bytes)")

    # 2. MSIX Package Logos
    square44_path = PKG_ASSETS_DIR / "Square44x44Logo.png"
    generate_png_icon((44, 44), master).save(square44_path, format="PNG")
    print(f"[OK] Generated {square44_path} ({square44_path.stat().st_size} bytes)")

    square150_path = PKG_ASSETS_DIR / "Square150x150Logo.png"
    generate_png_icon((150, 150), master).save(square150_path, format="PNG")
    print(f"[OK] Generated {square150_path} ({square150_path.stat().st_size} bytes)")

    store_logo_path = PKG_ASSETS_DIR / "StoreLogo.png"
    generate_png_icon((50, 50), master).save(store_logo_path, format="PNG")
    print(f"[OK] Generated {store_logo_path} ({store_logo_path.stat().st_size} bytes)")

    # 3. Web / Vite Favicon & Header Icons
    favicon_sizes = [(16, 16), (24, 24), (32, 32), (48, 48)]
    favicon_path = UI_PUBLIC_DIR / "favicon.ico"
    master.save(favicon_path, format="ICO", sizes=favicon_sizes)
    print(f"[OK] Generated {favicon_path} ({favicon_path.stat().st_size} bytes)")

    app_icon_32 = UI_PUBLIC_DIR / "app-icon-32.png"
    generate_png_icon((32, 32), master).save(app_icon_32, format="PNG")
    print(f"[OK] Generated {app_icon_32} ({app_icon_32.stat().st_size} bytes)")

    app_icon_64 = UI_PUBLIC_DIR / "app-icon-64.png"
    generate_png_icon((64, 64), master).save(app_icon_64, format="PNG")
    print(f"[OK] Generated {app_icon_64} ({app_icon_64.stat().st_size} bytes)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
