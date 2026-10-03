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
REQUIRED = [
    "AGENTS.md",
    "schemas/template.schema.json",
    "schemas/job.schema.json",
    "docs/ARCHITECTURE.md",
    "docs/PRODUCT_SPECS.md",
    "docs/ANTIGRAVITY.md",
    "docs/EDITOR_UX.md",
    "docs/IMAGE_PIPELINE.md",
    "docs/PERFORMANCE_BUDGETS.md",
    "docs/EDITOR_IMPLEMENTATION_PLAN.md",
    "docs/WINDOWS_INTEGRATION.md",
    "docs/adr/001-template-driven-engine.md",
    "docs/adr/002-millimeters-canonical.md",
    "docs/adr/003-fabric-pillow-boundary.md",
    "docs/adr/004-windows-shell-phases.md",
    "docs/adr/005-domain-editor.md",
    "docs/adr/006-antigravity-context.md",
    "docs/adr/007-explorer-process-boundary.md",
    "docs/adr/008-preview-original-boundary.md",
    "docs/adr/009-operator-manager-modes.md",
    "docs/adr/010-domain-command-history.md",
]


def main() -> int:
    missing = [item for item in REQUIRED if not (ROOT / item).exists()]
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
