"""Template persistence, semantic versioning, and publishing pipeline."""

from __future__ import annotations

import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from .template import (
    Template,
    TemplateError,
    load_template,
    schema_errors,
    semantic_errors,
)

BumpType = Literal["patch", "minor", "major"]


def bump_version(current_version: str, bump_type: BumpType = "minor") -> str:
    """Calculate the next semver version string strictly following X.Y.Z format."""
    pattern = r"^(\d+)\.(\d+)\.(\d+)$"
    match = re.match(pattern, current_version.strip())
    if not match:
        raise ValueError(
            f"Invalid semver version: {current_version!r}. Expected format X.Y.Z"
        )

    major, minor, patch = map(int, match.groups())
    if bump_type == "patch":
        patch += 1
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    else:
        raise ValueError(
            f"Invalid bump_type: {bump_type!r}. Must be 'patch', 'minor', or 'major'"
        )

    return f"{major}.{minor}.{patch}"


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    """Write dictionary to JSON atomically using a temporary file and atomic replace."""
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".json.tmp")
    payload_text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    tmp_path.write_text(payload_text, encoding="utf-8")
    os.replace(tmp_path, path)


def build_publish_payload(
    existing: dict[str, Any] | None,
    draft: dict[str, Any],
    new_version: str,
    notes_append: str = "",
) -> dict[str, Any]:
    """Build a complete, schema-compliant template dictionary from a TemplateDraft."""
    template_id = str(draft["id"]).strip()
    name = str(draft["name"]).strip()

    # Preserve or set default output specification
    if existing and "output" in existing:
        output_spec = {
            "format": existing["output"].get("format", "JPEG"),
            "quality": int(existing["output"].get("quality", 95)),
            "filename_prefix": str(
                existing["output"].get("filename_prefix", f"{name}_")
            ),
        }
    else:
        output_spec = {
            "format": "JPEG",
            "quality": 95,
            "filename_prefix": f"{name.replace(' ', '_')}_",
        }

    # Format canvas specs strictly as numbers/integers
    canvas_dict = draft["canvas"]
    canvas = {
        "width_mm": round(float(canvas_dict["width_mm"]), 2),
        "height_mm": round(float(canvas_dict["height_mm"]), 2),
        "dpi": int(canvas_dict["dpi"]),
    }

    # Format slots strictly without UI-only fields
    slots = []
    slot_ids: set[str] = set()
    for s in draft.get("slots", []):
        sid = str(s["id"]).strip()
        slot_ids.add(sid)
        slots.append(
            {
                "id": sid,
                "x_mm": round(float(s["x_mm"]), 2),
                "y_mm": round(float(s["y_mm"]), 2),
                "width_mm": round(float(s["width_mm"]), 2),
                "height_mm": round(float(s["height_mm"]), 2),
                "fit": s.get("fit", "cover"),
                "allow_pan": bool(s.get("allow_pan", True)),
                "allow_zoom": bool(s.get("allow_zoom", True)),
                "allow_rotate": bool(s.get("allow_rotate", False)),
            }
        )

    # Format overlay
    overlay_in = draft.get("overlay")
    if overlay_in and overlay_in.get("path"):
        overlay = {
            "path": str(overlay_in["path"]).strip(),
            "required": bool(overlay_in.get("required", True)),
        }
    else:
        overlay = None

    # Preserve or filter groups to ensure referenced slots exist
    groups = []
    if existing and "groups" in existing:
        for grp in existing["groups"]:
            valid_slots = [sid for sid in grp.get("slot_ids", []) if sid in slot_ids]
            if valid_slots:
                groups.append(
                    {
                        "id": grp["id"],
                        "slot_ids": valid_slots,
                        "fill_mode": grp.get("fill_mode", "independent"),
                    }
                )

    # Audit provenance history
    now_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    provenance_entry = (
        f"Modo Gestor: publicado v{new_version} em {now_iso} com {len(slots)} slot(s)"
    )

    if existing and "provenance" in existing:
        measured = list(existing["provenance"].get("measured", []))
        derived = list(existing["provenance"].get("derived", []))
        derived.append(provenance_entry)
    else:
        measured = [f"Criado via Modo Gestor em {now_iso}"]
        derived = [provenance_entry]

    # Notes
    notes = list(existing.get("notes", [])) if existing else []
    if notes_append and notes_append.strip():
        notes.append(notes_append.strip())

    return {
        "schema_version": "1.0",
        "template_version": new_version,
        "id": template_id,
        "name": name,
        "status": "production",
        "canvas": canvas,
        "output": output_spec,
        "slots": slots,
        "overlay": overlay,
        "groups": groups,
        "provenance": {
            "measured": measured,
            "derived": derived,
            "pending": [],  # Production status strictly forbids pending provenance
        },
        "notes": notes,
    }


def publish_template_to_disk(
    templates_root: Path,
    draft: dict[str, Any],
    bump_type: BumpType = "minor",
    notes: str = "",
) -> Template:
    """Validate, semver-bump, and atomically persist a template draft to disk."""
    templates_root = Path(templates_root).resolve()
    template_id = str(draft.get("id", "")).strip()
    if not template_id:
        raise TemplateError("Cannot publish template with empty ID", ["id: empty"])

    template_dir = templates_root / template_id
    template_file = template_dir / "template.json"

    # Read existing template if present to preserve metadata and extract current version
    existing_data: dict[str, Any] | None = None
    if template_file.is_file():
        try:
            existing_data = json.loads(template_file.read_text(encoding="utf-8"))
        except Exception as exc:
            raise TemplateError(
                f"Failed to read existing template file: {template_file}", [str(exc)]
            ) from exc

    current_version = (
        existing_data.get("template_version")
        if existing_data
        else draft.get("template_version", "1.0.0")
    )
    new_version = bump_version(str(current_version), bump_type=bump_type)

    payload = build_publish_payload(
        existing=existing_data,
        draft=draft,
        new_version=new_version,
        notes_append=notes,
    )

    # Formal schema validation
    schema_issues = schema_errors(payload)
    if schema_issues:
        raise TemplateError(
            f"Template {template_id} payload violated JSON schema", schema_issues
        )

    # Semantic validation
    semantic_issues = semantic_errors(payload, template_dir)
    if semantic_issues:
        raise TemplateError(
            f"Template {template_id} failed semantic validation", semantic_issues
        )

    # Atomic persistence to disk
    atomic_write_json(template_file, payload)

    # Reload template to return valid domain entity
    return load_template(template_file)
