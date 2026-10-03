"""Template contract: schema + semantic validation and mm->px resolution."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path, PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator

from ..geometry import mm_to_px
from ..paths import schemas_dir


class TemplateError(ValueError):
    def __init__(self, message: str, issues: list[str] | None = None) -> None:
        self.issues = issues or []
        detail = "; ".join(self.issues)
        super().__init__(f"{message}: {detail}" if detail else message)


@dataclass(frozen=True)
class Canvas:
    width_mm: float | None
    height_mm: float | None
    dpi: int | None


@dataclass(frozen=True)
class Slot:
    id: str
    x_mm: float | None
    y_mm: float | None
    width_mm: float | None
    height_mm: float | None
    fit: str
    allow_pan: bool
    allow_zoom: bool
    allow_rotate: bool


@dataclass(frozen=True)
class Overlay:
    path: str
    required: bool


@dataclass(frozen=True)
class OutputSpec:
    format: str
    quality: int
    filename_prefix: str


@dataclass(frozen=True)
class PixelRect:
    left: int
    top: int
    width: int
    height: int


@dataclass(frozen=True)
class Template:
    id: str
    template_version: str
    name: str
    status: str
    canvas: Canvas
    output: OutputSpec
    slots: tuple[Slot, ...]
    overlay: Overlay | None
    base_dir: Path

    def slot(self, slot_id: str) -> Slot:
        for slot in self.slots:
            if slot.id == slot_id:
                return slot
        raise KeyError(slot_id)

    @property
    def slot_ids(self) -> tuple[str, ...]:
        return tuple(slot.id for slot in self.slots)

    def overlay_path(self) -> Path | None:
        return None if self.overlay is None else self.base_dir / self.overlay.path

    def missing_for_render(self) -> list[str]:
        """Everything that prevents a deterministic render. Empty list = renderable."""
        missing: list[str] = []
        for field in ("width_mm", "height_mm", "dpi"):
            if getattr(self.canvas, field) is None:
                missing.append(f"canvas.{field}")
        for slot in self.slots:
            for field in ("x_mm", "y_mm", "width_mm", "height_mm"):
                if getattr(slot, field) is None:
                    missing.append(f"slots.{slot.id}.{field}")
        overlay = self.overlay_path()
        if self.overlay is not None and self.overlay.required and not overlay.is_file():
            missing.append(f"overlay:{self.overlay.path}")
        return missing

    @property
    def is_renderable(self) -> bool:
        return not self.missing_for_render()

    def _require_renderable(self) -> None:
        missing = self.missing_for_render()
        if missing:
            raise TemplateError(f"template {self.id} is not renderable", missing)

    def canvas_px(self) -> tuple[int, int]:
        self._require_renderable()
        dpi = self.canvas.dpi
        return mm_to_px(self.canvas.width_mm, dpi), mm_to_px(self.canvas.height_mm, dpi)

    def slot_rect_px(self, slot_id: str) -> PixelRect:
        """Edge-based conversion (ADR-011): each edge rounded independently."""
        self._require_renderable()
        slot = self.slot(slot_id)
        dpi = self.canvas.dpi
        left = mm_to_px(slot.x_mm, dpi)
        top = mm_to_px(slot.y_mm, dpi)
        right = mm_to_px(slot.x_mm + slot.width_mm, dpi)
        bottom = mm_to_px(slot.y_mm + slot.height_mm, dpi)
        return PixelRect(left=left, top=top, width=right - left, height=bottom - top)


@lru_cache(maxsize=4)
def _validator(schema_name: str) -> Draft202012Validator:
    schema = json.loads((schemas_dir() / schema_name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def schema_errors(data: Any, schema_name: str = "template.schema.json") -> list[str]:
    validator = _validator(schema_name)
    return [
        f"{'/'.join(map(str, err.absolute_path)) or '<root>'}: {err.message}"
        for err in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    ]


def _overlay_path_is_safe(rel: str) -> bool:
    pure = PurePosixPath(rel.replace("\\", "/"))
    return not pure.is_absolute() and ".." not in pure.parts and ":" not in rel


def semantic_errors(template: dict, base_dir: Path) -> list[str]:
    """Rules JSON Schema cannot express. Assumes schema-valid input."""
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
    if overlay:
        if not _overlay_path_is_safe(overlay["path"]):
            errors.append(f"overlay path must be relative to the template: {overlay['path']}")
        elif template["status"] == "production" and overlay["required"]:
            if not (base_dir / overlay["path"]).exists():
                errors.append(f"required overlay missing: {overlay['path']}")
    return errors


def parse_template(data: dict, base_dir: Path) -> Template:
    issues = schema_errors(data)
    if not issues:
        issues = semantic_errors(data, base_dir)
    if issues:
        raise TemplateError(f"invalid template {data.get('id', '<unknown>')!r}", issues)
    overlay = data["overlay"]
    return Template(
        id=data["id"],
        template_version=data["template_version"],
        name=data["name"],
        status=data["status"],
        canvas=Canvas(**data["canvas"]),
        output=OutputSpec(**data["output"]),
        slots=tuple(Slot(**slot) for slot in data["slots"]),
        overlay=None if overlay is None else Overlay(**overlay),
        base_dir=base_dir,
    )


def load_template(path: Path) -> Template:
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TemplateError(f"cannot read template {path.name}", [str(exc)]) from exc
    return parse_template(data, path.parent)
