#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "desktop" / "src"))

# Single source of truth for template rules lives in the domain package.
from evydencia_print_generator.domain.template import (  # noqa: E402
    schema_errors,
    semantic_errors,
)

TEMPLATES_DIR = ROOT / "templates"


def main() -> int:
    template_files = sorted(TEMPLATES_DIR.glob("*/template.json"))
    if not template_files:
        print("No templates found", file=sys.stderr)
        return 1

    failed = False
    for path in template_files:
        data = json.loads(path.read_text(encoding="utf-8"))
        issues = schema_errors(data)
        if not issues:
            issues = semantic_errors(data, path.parent)
        if issues:
            failed = True
            print(f"FAIL {path.relative_to(ROOT)}")
            for issue in issues:
                print(f" - {issue}")
        else:
            print(f"OK   {path.relative_to(ROOT)} [{data['status']}]")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
