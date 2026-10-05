"""Tests for DesktopBridge batch operations, file dialog, native drop, and startup batch."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from types import ModuleType
from typing import Any
from unittest.mock import MagicMock

import pytest
from conftest import synthetic_rgb
from evydencia_print_generator.app.bridge import DesktopBridge
from evydencia_print_generator.ingest import (
    IngestService,
    PreviewCache,
    PreviewService,
    SourceRegistry,
)


@pytest.fixture
def bridge_setup(tmp_path: Path):
    registry = SourceRegistry()
    cache = PreviewCache(tmp_path / "cache")
    preview_service = PreviewService(registry, cache=cache)
    ingest_service = IngestService(registry, schedule_preview=preview_service.ensure_preview)

    bridge = DesktopBridge(
        registry=registry,
        ingest_service=ingest_service,
        preview_service=preview_service,
        server_base_url="http://127.0.0.1:8000",
        startup_accepted_ids=["init_1", "init_2"],
    )

    yield bridge, registry, preview_service

    preview_service.shutdown()


def test_get_startup_batch(bridge_setup) -> None:
    bridge, _, _ = bridge_setup
    batch = bridge.get_startup_batch()
    assert batch == {"accepted_ids": ["init_1", "init_2"]}


def test_native_drop_multiple_files_preserves_order(tmp_path: Path, bridge_setup) -> None:
    bridge, _, _ = bridge_setup

    paths: list[Path] = []
    for i in range(4):
        p = tmp_path / f"photo_{i + 1}.jpg"
        synthetic_rgb((800, 600)).save(p, format="JPEG")
        paths.append(p)

    captured_payload: dict[str, Any] = {}

    class FakeWindow:
        def evaluate_js(self, js: str) -> None:
            nonlocal captured_payload
            # Format: window.__onNativeFileDrop && window.__onNativeFileDrop({...});
            prefix = "window.__onNativeFileDrop && window.__onNativeFileDrop("
            suffix = ");"
            if js.startswith(prefix) and js.endswith(suffix):
                payload_str = js[len(prefix) : -len(suffix)]
                captured_payload = json.loads(payload_str)

    bridge.set_window(FakeWindow())

    event = {
        "dataTransfer": {
            "files": [{"pywebviewFullPath": str(p)} for p in paths]
        },
        "clientX": 250,
        "clientY": 300,
    }

    bridge.handle_native_drop(event)

    assert "accepted_ids" in captured_payload
    assert len(captured_payload["accepted_ids"]) == 4
    assert captured_payload["clientX"] == 250
    assert captured_payload["clientY"] == 300

    # Ensure source display names correspond to input order
    sources_by_id = {s["id"]: s for s in captured_payload["sources"]}
    ordered_names = [sources_by_id[sid]["display_name"] for sid in captured_payload["accepted_ids"]]
    assert ordered_names == ["photo_1.jpg", "photo_2.jpg", "photo_3.jpg", "photo_4.jpg"]


def test_batch_dedupes_same_file_repeated(tmp_path: Path, bridge_setup) -> None:
    bridge, _, _ = bridge_setup

    p = tmp_path / "repeated.jpg"
    synthetic_rgb((400, 400)).save(p, format="JPEG")

    res = bridge.ingest_batch([str(p), str(p)])
    assert len(res["accepted_ids"]) == 1
    assert len(res["sources"]) == 1


def test_batch_mixed_with_invalid_file(tmp_path: Path, bridge_setup) -> None:
    bridge, _, _ = bridge_setup

    valid_1 = tmp_path / "valid_1.jpg"
    synthetic_rgb((400, 400)).save(valid_1, format="JPEG")

    valid_2 = tmp_path / "valid_2.jpg"
    synthetic_rgb((400, 400)).save(valid_2, format="JPEG")

    bad = tmp_path / "not_an_image.jpg"
    bad.write_text("Hello plain text", encoding="utf-8")

    res = bridge.ingest_batch([str(valid_1), str(bad), str(valid_2)])
    assert len(res["accepted_ids"]) == 2
    assert len(res["rejected"]) == 1
    assert res["rejected"][0]["display_name"] == "not_an_image.jpg"
    assert res["rejected"][0]["code"] == "unsupported_format"


def test_batch_ingest_is_non_blocking(tmp_path: Path, bridge_setup) -> None:
    bridge, _, _ = bridge_setup

    p = tmp_path / "speed_test.jpg"
    synthetic_rgb((2000, 1500)).save(p, format="JPEG")

    t0 = time.perf_counter()
    res = bridge.ingest_batch([str(p)])
    elapsed = time.perf_counter() - t0

    assert len(res["accepted_ids"]) == 1
    assert elapsed < 0.2


def test_original_files_unmodified(tmp_path: Path, bridge_setup) -> None:
    bridge, _, _ = bridge_setup

    p = tmp_path / "original_guard.jpg"
    synthetic_rgb((500, 500)).save(p, format="JPEG")

    stat_before = p.stat()
    content_before = p.read_bytes()

    bridge.ingest_batch([str(p)])

    stat_after = p.stat()
    content_after = p.read_bytes()

    assert stat_before.st_size == stat_after.st_size
    assert stat_before.st_mtime_ns == stat_after.st_mtime_ns
    assert content_before == content_after


def test_open_file_dialog_returns_batch_model(
    tmp_path: Path, bridge_setup, monkeypatch: pytest.MonkeyPatch
) -> None:
    bridge, _, _ = bridge_setup

    p1 = tmp_path / "sel_1.jpg"
    synthetic_rgb((400, 400)).save(p1, format="JPEG")
    p2 = tmp_path / "sel_2.jpg"
    synthetic_rgb((400, 400)).save(p2, format="JPEG")

    fake_window = MagicMock()
    fake_window.create_file_dialog.return_value = (str(p1), str(p2))
    bridge.set_window(fake_window)

    fake_webview = ModuleType("webview")
    fake_webview.FileDialog = MagicMock()  # type: ignore[attr-defined]
    fake_webview.FileDialog.OPEN = 10  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "webview", fake_webview)

    res = bridge.open_file_dialog()
    assert "sources" in res
    assert "accepted_ids" in res
    assert "rejected" in res
    assert len(res["accepted_ids"]) == 2


def test_open_file_dialog_cancelled(bridge_setup, monkeypatch: pytest.MonkeyPatch) -> None:
    bridge, _, _ = bridge_setup

    fake_window = MagicMock()
    fake_window.create_file_dialog.return_value = None
    bridge.set_window(fake_window)

    fake_webview = ModuleType("webview")
    fake_webview.FileDialog = MagicMock()  # type: ignore[attr-defined]
    fake_webview.FileDialog.OPEN = 10  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "webview", fake_webview)

    res = bridge.open_file_dialog()
    assert res["accepted_ids"] == []
    assert res["rejected"] == []


def test_reingest_existing_source_in_dialog_included_in_accepted(
    tmp_path: Path, bridge_setup, monkeypatch: pytest.MonkeyPatch
) -> None:
    bridge, _, _ = bridge_setup

    p1 = tmp_path / "existing.jpg"
    synthetic_rgb((400, 400)).save(p1, format="JPEG")
    # First ingest
    first_res = bridge.ingest_batch([str(p1)])
    assert len(first_res["accepted_ids"]) == 1
    existing_id = first_res["accepted_ids"][0]

    p2 = tmp_path / "new_photo.jpg"
    synthetic_rgb((400, 400)).save(p2, format="JPEG")

    # Second ingest via dialog selecting both existing and new
    fake_window = MagicMock()
    fake_window.create_file_dialog.return_value = (str(p1), str(p2))
    bridge.set_window(fake_window)

    fake_webview = ModuleType("webview")
    fake_webview.FileDialog = MagicMock()  # type: ignore[attr-defined]
    fake_webview.FileDialog.OPEN = 10  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "webview", fake_webview)

    dialog_res = bridge.open_file_dialog()
    # Existing source MUST be present in accepted_ids for the new batch!
    assert existing_id in dialog_res["accepted_ids"]
    assert len(dialog_res["accepted_ids"]) == 2
