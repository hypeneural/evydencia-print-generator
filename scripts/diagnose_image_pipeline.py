#!/usr/bin/env python3
"""Standalone read-only diagnostic utility to inspect image pipeline metadata.

Inspects raster format, pixel dimensions, color mode, EXIF ColorSpace, embedded ICC
profiles, JPEG chroma subsampling, and DPI without modifying any files.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
from pathlib import Path
from typing import Any

from PIL import Image, ImageCms


def inspect_image(path: Path) -> dict[str, Any]:
    """Inspect image metadata without altering the file."""
    if not path.is_file():
        return {"path": str(path), "error": "File does not exist"}

    result: dict[str, Any] = {
        "path": str(path),
        "filename": path.name,
        "size_bytes": path.stat().st_size,
    }

    try:
        with Image.open(path) as im:
            result["format"] = im.format
            result["mode"] = im.mode
            result["width"] = im.width
            result["height"] = im.height
            result["dpi"] = im.info.get("dpi")

            # JPEG subsampling (0=4:4:4, 1=4:2:2, 2=4:2:0)
            subsampling = im.info.get("subsampling")
            result["subsampling"] = subsampling

            # EXIF extraction
            exif = im.getexif()
            if exif:
                exif_data: dict[str, Any] = {}
                for tag_id, value in exif.items():
                    # Check specifically for orientation and color space
                    if tag_id == 0x0112:  # Orientation
                        exif_data["Orientation"] = value
                    elif tag_id == 0x011A:  # XResolution
                        exif_data["XResolution"] = float(value) if value else None
                    elif tag_id == 0x011B:  # YResolution
                        exif_data["YResolution"] = float(value) if value else None
                    elif tag_id == 0x0128:  # ResolutionUnit
                        exif_data["ResolutionUnit"] = value
                    elif tag_id == 0xA001:  # ColorSpace
                        cs_map = {1: "sRGB", 2: "Adobe RGB", 65535: "Uncalibrated / Wide Gamut"}
                        cs_name = cs_map.get(value, f"Unknown ({value})")
                        exif_data["ColorSpace"] = f"{value} ({cs_name})"
                if exif_data:
                    result["exif"] = exif_data

            # ICC Profile inspection
            icc_bytes = im.info.get("icc_profile")
            if icc_bytes:
                icc_info: dict[str, Any] = {
                    "present": True,
                    "length_bytes": len(icc_bytes),
                    "sha256": hashlib.sha256(icc_bytes).hexdigest(),
                }
                try:
                    prof = ImageCms.ImageCmsProfile(io.BytesIO(icc_bytes))
                    name = ImageCms.getProfileName(prof)
                    desc = ImageCms.getProfileDescription(prof)
                    info = ImageCms.getProfileInfo(prof)
                    icc_info["profile_name"] = name.strip() if name else None
                    icc_info["profile_description"] = desc.strip() if desc else None
                    icc_info["profile_info"] = info.strip() if info else None
                except Exception as exc:
                    icc_info["parse_error"] = str(exc)
                result["icc"] = icc_info
            else:
                result["icc"] = {"present": False}

    except Exception as exc:
        result["error"] = str(exc)

    return result


def format_report(data: dict[str, Any]) -> str:
    """Format dictionary into a clean human-readable diagnostic report."""
    lines = [
        "==================================================",
        f"File: {data.get('filename')} ({data.get('size_bytes', 0):,} bytes)",
        f"Path: {data.get('path')}",
    ]
    if "error" in data:
        lines.append(f"ERROR: {data['error']}")
        lines.append("==================================================")
        return "\n".join(lines)

    lines.append(f"Format: {data.get('format')} | Mode: {data.get('mode')}")
    lines.append(f"Dimensions: {data.get('width')} x {data.get('height')} px")
    lines.append(f"DPI: {data.get('dpi')}")
    lines.append(f"JPEG Subsampling: {data.get('subsampling')}")

    exif = data.get("exif")
    if exif:
        lines.append("EXIF Metadata:")
        for k, v in exif.items():
            lines.append(f"  - {k}: {v}")
    else:
        lines.append("EXIF Metadata: None detected")

    icc = data.get("icc", {})
    if icc.get("present"):
        lines.append(f"ICC Profile: PRESENT ({icc.get('length_bytes')} bytes)")
        lines.append(f"  - SHA-256: {icc.get('sha256')}")
        lines.append(f"  - Name: {icc.get('profile_name')}")
        lines.append(f"  - Description: {icc.get('profile_description')}")
        lines.append(f"  - Info: {icc.get('profile_info')}")
        if "parse_error" in icc:
            lines.append(f"  - Warning/Error: {icc['parse_error']}")
    else:
        lines.append("ICC Profile: NONE (untagged raster)")

    lines.append("==================================================")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose image pipeline metadata (read-only).")
    parser.add_argument("paths", nargs="+", type=Path, help="Paths to image files to inspect")
    parser.add_argument("--json", action="store_true", help="Output diagnostic in JSON format")
    args = parser.parse_args()

    results = [inspect_image(p) for p in args.paths]

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for r in results:
            print(format_report(r))

    return 0


if __name__ == "__main__":
    sys.exit(main())
