#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "template.schema.json"
TEMPLATES_DIR = ROOT / "templates"


def semantic_errors(template: dict, path: Path) -> list[str]:
    errors: list[str] = []
    slots = template["slots"]
    ids = [slot["id"] for slot in slots]
    if len(ids) != len(set(ids)):
        errors.append("duplicate slot IDs")

    canvas = template["canvas"]
    width = canvas["width_mm"]
    height = canvas["height_mm"]
    if width is not None and height is not None:
        for slot in slots:
            values = [slot["x_mm"], slot["y_mm"], slot["width_mm"], slot["height_mm"]]
            if all(value is not None for value in values):
                x, y, w, h = values
                if x + w > width + 1e-9 or y + h > height + 1e-9:
                    errors.append(f"{slot['id']}: slot exceeds canvas")

    if template["status"] == "production" and template["provenance"]["pending"]:
        errors.append("production template cannot have pending provenance items")

    group_ids: set[str] = set()
    slot_ids = set(ids)
    for group in template["groups"]:
        if group["id"] in group_ids:
            errors.append(f"duplicate group ID {group['id']}")
        group_ids.add(group["id"])
        unknown = set(group["slot_ids"]) - slot_ids
        if unknown:
            errors.append(f"group {group['id']} references unknown slots {sorted(unknown)}")

    overlay = template["overlay"]
    if template["status"] == "production" and overlay and overlay["required"]:
        asset = path.parent / overlay["path"]
        if not asset.exists():
            errors.append(f"required overlay missing: {overlay['path']}")
    return errors


def main() -> int:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    template_files = sorted(TEMPLATES_DIR.glob("*/template.json"))
    if not template_files:
        print("No templates found", file=sys.stderr)
        return 1

    failed = False
    for path in template_files:
        data = json.loads(path.read_text(encoding="utf-8"))
        issues = [error.message for error in validator.iter_errors(data)]
        issues.extend(semantic_errors(data, path))
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
