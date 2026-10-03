#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKS = [
    "verify_antigravity_customizations.py",
    "validate_templates.py",
    "check_privacy.py",
]


def main() -> int:
    required = [
        ROOT / "AGENTS.md",
        ROOT / "schemas" / "template.schema.json",
        ROOT / "schemas" / "job.schema.json",
        ROOT / "docs" / "ARCHITECTURE.md",
        ROOT / "docs" / "PRODUCT_SPECS.md",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    if missing:
        print("Repository verification FAILED: missing required files")
        for item in missing:
            print(f" - {item}")
        return 1

    for check in CHECKS:
        print(f"\n==> {check}")
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / check)], cwd=ROOT)
        if result.returncode != 0:
            return result.returncode
    print("\nRepository verification OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
