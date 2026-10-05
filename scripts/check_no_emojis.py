"""Emoji verification script for EVYDÊNCIA UI.

Ensures that presentation components in apps/ui/src do not contain presentation emojis,
enforcing professional enterprise UX with SVG icons instead.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Match emojis across major emoji ranges
EMOJI_PATTERN = re.compile(
    r"[\U0001F300-\U0001F9FF]"  # Misc Symbols, Pictographs, Supplemental
    r"|[\U0001FA00-\U0001FAFF]"  # Symbols and Pictographs Extended-A
    r"|[\U00002600-\U000027BF]"  # Misc Symbols, Dingbats
    r"|[\U00002300-\U000023FF]"  # Misc Technical
    r"|[\U00002B50-\U00002B55]"  # Stars
    r"|[\U0000203C-\U00002049]"  # Exclamation marks
)

EXCLUDED_PATHS = {
    # If any specific non-UI file is intentionally excluded, add here
}


def check_files(src_dir: Path) -> int:
    errors = 0
    checked = 0
    for ext in ("*.tsx", "*.ts"):
        for path in src_dir.rglob(ext):
            if path in EXCLUDED_PATHS or ".test." in path.name:
                continue
            checked += 1
            content = path.read_text(encoding="utf-8")
            for line_no, line in enumerate(content.splitlines(), start=1):
                # Skip comments if desired, but best practice is zero emojis anywhere in UI code
                matches = EMOJI_PATTERN.findall(line)
                if matches:
                    errors += 1
                    codepoints = " ".join(f"U+{ord(c):04X}" for c in matches)
                    print(
                        f"FAIL: {path.relative_to(src_dir.parent.parent)}:{line_no} "
                        f"contains forbidden emoji codepoints: {codepoints}"
                    )
                    safe_line = line.strip().encode("ascii", errors="replace").decode("ascii")
                    print(f"      Line: {safe_line}")

    print(f"\nAudit complete: checked {checked} files, found {errors} emoji violations.")
    return 1 if errors > 0 else 0


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    ui_src = repo_root / "apps" / "ui" / "src"
    if not ui_src.is_dir():
        print(f"Error: Directory {ui_src} not found.", file=sys.stderr)
        return 2

    return check_files(ui_src)


if __name__ == "__main__":
    sys.exit(main())
