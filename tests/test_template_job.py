"""Template + Job domain contracts."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from conftest import SYNTHETIC_TEMPLATE
from evydencia_print_generator.domain.job import EditState, JobError, build_job_snapshot
from evydencia_print_generator.domain.template import (
    Canvas,
    OutputSpec,
    PixelRect,
    Slot,
    Template,
    TemplateError,
    load_template,
    parse_template,
)
from evydencia_print_generator.ingest import IngestService, SourceRegistry
from evydencia_print_generator.paths import templates_dir


def _edit(source_id: str, **overrides) -> dict:
    edit = {"source_id": source_id, "pan_x_norm": 0, "pan_y_norm": 0, "scale": 1, "rotation_deg": 0}
    edit.update(overrides)
    return edit


def _state(slot_edits: dict, version: str = "0.0.1") -> dict:
    return {
        "template_id": "calendar-synthetic",
        "template_version": version,
        "slot_edits": slot_edits,
    }


@pytest.fixture
def template():
    return load_template(SYNTHETIC_TEMPLATE)


@pytest.fixture
def registry_with_source(make_image):
    registry = SourceRegistry()
    source = make_image("src.jpg", size=(120, 80))
    asset = IngestService(registry).ingest_paths([source]).accepted[0]
    return registry, asset


# --- Template ---------------------------------------------------------------


@pytest.mark.parametrize("product", ["calendario-2027", "chaveiro-3x4", "globo-neve"])
def test_repo_templates_load(product: str) -> None:
    tpl = load_template(templates_dir() / product / "template.json")
    assert tpl.status in {"draft", "production"}


def test_real_calendar_is_production_and_renderable() -> None:
    tpl = load_template(templates_dir() / "calendario-2027" / "template.json")
    assert tpl.is_renderable
    assert tpl.status == "production"
    assert tpl.output.filename_prefix == "Calendario_"
    assert tpl.canvas_px() == (1067, 1474)
    assert tpl.overlay is not None
    assert tpl.overlay_path() is not None and tpl.overlay_path().is_file()


def test_draft_template_not_renderable() -> None:
    tpl = Template(
        id="draft-item",
        template_version="1.0.0",
        name="Draft Item",
        status="draft",
        canvas=Canvas(width_mm=None, height_mm=None, dpi=None),
        output=OutputSpec(format="JPEG", quality=95, filename_prefix="Draft_"),
        slots=(
            Slot(
                id="s1",
                x_mm=None,
                y_mm=None,
                width_mm=None,
                height_mm=None,
                fit="cover",
                allow_pan=True,
                allow_zoom=True,
                allow_rotate=True,
            ),
        ),
        overlay=None,
        base_dir=Path("."),
    )
    assert not tpl.is_renderable
    missing = tpl.missing_for_render()
    assert "canvas.dpi" in missing and "slots.s1.width_mm" in missing
    with pytest.raises(TemplateError):
        tpl.canvas_px()


def test_synthetic_template_geometry(template) -> None:
    assert template.is_renderable
    assert template.canvas_px() == (591, 827)  # 100x140 mm @150 dpi
    # edge-based: left=59, right=round(90/25.4*150)=531, top=59, bottom=round(50/25.4*150)=295
    assert template.slot_rect_px("foto_principal") == PixelRect(59, 59, 472, 236)


def test_edge_based_rects_tile_without_gaps() -> None:
    data = json.loads(SYNTHETIC_TEMPLATE.read_text(encoding="utf-8"))
    data["canvas"] = {"width_mm": 216, "height_mm": 152, "dpi": 300}
    data["slots"] = [
        {
            **data["slots"][0],
            "id": f"s{i}",
            "x_mm": 6 + 34 * i,
            "y_mm": 10,
            "width_mm": 34,
            "height_mm": 44,
        }
        for i in range(6)
    ]
    tpl = parse_template(data, SYNTHETIC_TEMPLATE.parent)
    rects = [tpl.slot_rect_px(f"s{i}") for i in range(6)]
    for left, right in zip(rects, rects[1:], strict=False):
        assert left.left + left.width == right.left


def test_invalid_templates_rejected() -> None:
    base = json.loads(SYNTHETIC_TEMPLATE.read_text(encoding="utf-8"))
    bad_schema = copy.deepcopy(base)
    bad_schema["canvas"]["dpi"] = 10
    with pytest.raises(TemplateError):
        parse_template(bad_schema, SYNTHETIC_TEMPLATE.parent)
    overflow = copy.deepcopy(base)
    overflow["slots"][0]["width_mm"] = 500
    with pytest.raises(TemplateError, match="exceeds canvas"):
        parse_template(overflow, SYNTHETIC_TEMPLATE.parent)
    traversal = copy.deepcopy(base)
    traversal["overlay"] = {"path": "../../segredo.png", "required": False}
    with pytest.raises(TemplateError, match="relative"):
        parse_template(traversal, SYNTHETIC_TEMPLATE.parent)


def test_unreadable_template(tmp_path: Path) -> None:
    broken = tmp_path / "template.json"
    broken.write_text("{nope", encoding="utf-8")
    with pytest.raises(TemplateError):
        load_template(broken)


def test_required_overlay_missing_blocks_render(tmp_path: Path) -> None:
    data = json.loads(SYNTHETIC_TEMPLATE.read_text(encoding="utf-8"))
    data["overlay"] = {"path": "assets/overlay.png", "required": True}
    tpl = parse_template(data, tmp_path)
    assert tpl.missing_for_render() == ["overlay:assets/overlay.png"]


# --- Job --------------------------------------------------------------------


def test_snapshot_resolves_paths_from_registry(template, registry_with_source) -> None:
    registry, asset = registry_with_source
    state = EditState.from_ui(_state({"foto_principal": _edit(asset.id, scale=1.5)}))
    snap = build_job_snapshot(template, state, registry.get)
    assert snap.sources[asset.id].path == asset.path
    assert snap.sources[asset.id].mtime_ns == asset.identity.mtime_ns
    assert snap.to_schema_dict()["sources"][asset.id]["path"] == str(asset.path)


def test_snapshot_clamps_and_normalizes(template, registry_with_source) -> None:
    registry, asset = registry_with_source
    state = EditState.from_ui(
        _state({"foto_principal": _edit(asset.id, pan_x_norm=4, scale=99, rotation_deg=270)})
    )
    t = build_job_snapshot(template, state, registry.get).slot_edits["foto_principal"].transform
    assert (t.pan_x_norm, t.scale, t.rotation_deg) == (1.0, 8.0, -90.0)


def test_shared_source_listed_once(registry_with_source) -> None:
    registry, asset = registry_with_source
    data = json.loads(SYNTHETIC_TEMPLATE.read_text(encoding="utf-8"))
    data["slots"].append({**data["slots"][0], "id": "foto_2", "y_mm": 60})
    tpl = parse_template(data, SYNTHETIC_TEMPLATE.parent)
    state = EditState.from_ui(
        _state({"foto_principal": _edit(asset.id), "foto_2": _edit(asset.id, scale=2)})
    )
    snap = build_job_snapshot(tpl, state, registry.get)
    assert list(snap.sources) == [asset.id]


@pytest.mark.parametrize(
    "payload",
    [
        {"template_id": "x", "template_version": "1", "slot_edits": {}, "sources": {}},
        {"template_id": "x", "template_version": "1"},
        {"template_id": "x", "template_version": "1", "slot_edits": {"a": {"path": "C:/x"}}},
        _state({"foto_principal": {**_edit("src_1"), "path": "C:/foto.jpg"}}),
        _state({"foto_principal": _edit("src_1", scale="2")}),
        _state({"foto_principal": _edit("src_1", scale=True)}),
        _state({"foto_principal": _edit("src_1", rotation_deg=float("nan"))}),
        "not a dict",
    ],
)
def test_edit_state_is_strict_and_path_free(payload) -> None:
    with pytest.raises(JobError):
        EditState.from_ui(payload)


def test_snapshot_rejections(template, registry_with_source) -> None:
    registry, asset = registry_with_source
    cases = [
        (_state({"foto_principal": _edit("src_desconhecida")}), "unknown source"),
        (_state({"outro_slot": _edit(asset.id)}), "unknown slots"),
        (_state({}), "without photo"),
        (_state({"foto_principal": _edit(asset.id)}, version="9.9.9"), "version"),
    ]
    for payload, message in cases:
        with pytest.raises(JobError, match=message):
            build_job_snapshot(template, EditState.from_ui(payload), registry.get)


def test_slot_permissions_enforced(registry_with_source) -> None:
    registry, asset = registry_with_source
    data = json.loads(SYNTHETIC_TEMPLATE.read_text(encoding="utf-8"))
    data["slots"][0].update(allow_pan=False, allow_zoom=False, allow_rotate=False)
    tpl = parse_template(data, SYNTHETIC_TEMPLATE.parent)
    for override, message in [
        ({"pan_x_norm": 0.2}, "pan"),
        ({"scale": 1.2}, "zoom"),
        ({"rotation_deg": 5}, "rotation"),
    ]:
        state = EditState.from_ui(_state({"foto_principal": _edit(asset.id, **override)}))
        with pytest.raises(JobError, match=message):
            build_job_snapshot(tpl, state, registry.get)
    ok = EditState.from_ui(_state({"foto_principal": _edit(asset.id)}))
    assert build_job_snapshot(tpl, ok, registry.get)
