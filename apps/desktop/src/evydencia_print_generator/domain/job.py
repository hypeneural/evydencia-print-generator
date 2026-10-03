"""Job contract: UI edit state (no paths) -> immutable render snapshot (paths from registry)."""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .template import Template, schema_errors
from .transform import SlotTransform, clamp_transform

if TYPE_CHECKING:
    from ..ingest.models import SourceAsset

JOB_SCHEMA_VERSION = "1.0"
_EDIT_STATE_KEYS = frozenset({"template_id", "template_version", "slot_edits"})
_SLOT_EDIT_KEYS = frozenset({"source_id", "pan_x_norm", "pan_y_norm", "scale", "rotation_deg"})


class JobError(ValueError):
    pass


@dataclass(frozen=True)
class SlotEdit:
    source_id: str
    transform: SlotTransform


@dataclass(frozen=True)
class EditState:
    """What the UI is allowed to send. Never contains filesystem paths."""

    template_id: str
    template_version: str
    slot_edits: dict[str, SlotEdit]

    @classmethod
    def from_ui(cls, data: Any) -> EditState:
        if not isinstance(data, dict) or set(data) != _EDIT_STATE_KEYS:
            raise JobError(f"edit state must have exactly {sorted(_EDIT_STATE_KEYS)}")
        template_id, version, edits = (
            data["template_id"],
            data["template_version"],
            data["slot_edits"],
        )
        if not isinstance(template_id, str) or not isinstance(version, str):
            raise JobError("template_id/template_version must be strings")
        if not isinstance(edits, dict):
            raise JobError("slot_edits must be an object")
        parsed: dict[str, SlotEdit] = {}
        for slot_id, edit in edits.items():
            if not isinstance(edit, dict) or set(edit) != _SLOT_EDIT_KEYS:
                expected = sorted(_SLOT_EDIT_KEYS)
                raise JobError(f"slot {slot_id!r}: fields must be exactly {expected}")
            source_id = edit["source_id"]
            if not isinstance(source_id, str) or not source_id:
                raise JobError(f"slot {slot_id!r}: invalid source_id")
            numbers = {}
            for key in ("pan_x_norm", "pan_y_norm", "scale", "rotation_deg"):
                value = edit[key]
                if isinstance(value, bool) or not isinstance(value, int | float):
                    raise JobError(f"slot {slot_id!r}: {key} must be a number")
                if not math.isfinite(value):
                    raise JobError(f"slot {slot_id!r}: {key} must be finite")
                numbers[key] = float(value)
            parsed[slot_id] = SlotEdit(source_id=source_id, transform=SlotTransform(**numbers))
        return cls(template_id=template_id, template_version=version, slot_edits=parsed)


@dataclass(frozen=True)
class JobSource:
    source_id: str
    path: Path
    size_bytes: int
    mtime_ns: int


@dataclass(frozen=True)
class JobSnapshot:
    """Immutable render input. The renderer re-opens originals from ``sources``."""

    template_id: str
    template_version: str
    sources: dict[str, JobSource]
    slot_edits: dict[str, SlotEdit]

    def to_schema_dict(self) -> dict[str, Any]:
        return {
            "schema_version": JOB_SCHEMA_VERSION,
            "template_id": self.template_id,
            "template_version": self.template_version,
            "sources": {sid: {"path": str(src.path)} for sid, src in self.sources.items()},
            "slot_edits": {
                slot_id: {
                    "source_id": edit.source_id,
                    "pan_x_norm": edit.transform.pan_x_norm,
                    "pan_y_norm": edit.transform.pan_y_norm,
                    "scale": edit.transform.scale,
                    "rotation_deg": edit.transform.rotation_deg,
                }
                for slot_id, edit in self.slot_edits.items()
            },
        }


def _check_permissions(template: Template, slot_id: str, t: SlotTransform) -> None:
    slot = template.slot(slot_id)
    if not slot.allow_pan and (t.pan_x_norm != 0 or t.pan_y_norm != 0):
        raise JobError(f"slot {slot_id!r} does not allow pan")
    if not slot.allow_zoom and t.scale != 1:
        raise JobError(f"slot {slot_id!r} does not allow zoom")
    if not slot.allow_rotate and t.rotation_deg != 0:
        raise JobError(f"slot {slot_id!r} does not allow rotation")


def build_job_snapshot(
    template: Template,
    edit_state: EditState,
    resolve_source: Callable[[str], SourceAsset | None],
) -> JobSnapshot:
    if edit_state.template_id != template.id:
        raise JobError(f"edit state targets template {edit_state.template_id!r}")
    if edit_state.template_version != template.template_version:
        raise JobError(
            f"edit state targets version {edit_state.template_version!r}, "
            f"loaded {template.template_version!r}"
        )
    unknown_slots = set(edit_state.slot_edits) - set(template.slot_ids)
    if unknown_slots:
        raise JobError(f"unknown slots {sorted(unknown_slots)}")
    empty = [sid for sid in template.slot_ids if sid not in edit_state.slot_edits]
    if empty:
        raise JobError(f"slots without photo {empty}")

    sources: dict[str, JobSource] = {}
    edits: dict[str, SlotEdit] = {}
    for slot_id in template.slot_ids:
        edit = edit_state.slot_edits[slot_id]
        transform = clamp_transform(edit.transform)
        _check_permissions(template, slot_id, transform)
        if edit.source_id not in sources:
            asset = resolve_source(edit.source_id)
            if asset is None:
                raise JobError(f"unknown source {edit.source_id!r}")
            sources[edit.source_id] = JobSource(
                source_id=asset.id,
                path=asset.path,
                size_bytes=asset.identity.size_bytes,
                mtime_ns=asset.identity.mtime_ns,
            )
        edits[slot_id] = SlotEdit(source_id=edit.source_id, transform=transform)

    snapshot = JobSnapshot(
        template_id=template.id,
        template_version=template.template_version,
        sources=sources,
        slot_edits=edits,
    )
    issues = schema_errors(snapshot.to_schema_dict(), "job.schema.json")
    if issues:
        raise JobError("job snapshot violates job.schema.json: " + "; ".join(issues))
    return snapshot
