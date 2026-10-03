#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_DIRS = {"customer-photos", "private-fixtures", "output", "exports", "local-data"}
FORBIDDEN_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".heic", ".cr2", ".cr3", ".nef", ".arw", ".dng"}
TEXT_PATTERNS = {
    "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "Windows user path": re.compile(r"[A-Za-z]:\\Users\\[^\\\r\n]+"),
    "likely credential": re.compile(
        r"(?i)\b(api[_-]?key|password|secret|access[_-]?token)\b\s*[:=]\s*['\"][^'\"]{8,}['\"]"
    ),
}


def tracked_files() -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=ROOT,
            capture_output=True,
            check=True,
        )
        return [ROOT / item.decode() for item in result.stdout.split(b"\0") if item]
    except Exception:
        return [p for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts]


def main() -> int:
    errors: list[str] = []
    for path in tracked_files():
        rel = path.relative_to(ROOT)
        if any(part.lower() in FORBIDDEN_DIRS for part in rel.parts):
            errors.append(f"{rel}: forbidden production/private directory")
        if path.suffix.lower() in FORBIDDEN_IMAGE_SUFFIXES:
            errors.append(f"{rel}: photographic/raster source type not allowed in repository")
        try:
            if path.stat().st_size > 2_000_000:
                continue
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for label, pattern in TEXT_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{rel}: {label} detected")

    if errors:
        print("Privacy check FAILED:")
        for error in errors:
            print(f" - {error}")
        return 1
    print("Privacy check OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
