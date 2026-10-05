"""Tests for desktop application server, bridge, and UI integration."""

from __future__ import annotations

import urllib.request
from pathlib import Path

import pytest
from conftest import synthetic_rgb
from evydencia_print_generator.app.bridge import DesktopBridge
from evydencia_print_generator.app.server import AssetServer
from evydencia_print_generator.ingest import (
    IngestService,
    PreviewCache,
    PreviewService,
    SourceRegistry,
)

SYNTHETIC_TPL = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "templates"
    / "calendar-synthetic"
    / "template.json"
)


@pytest.fixture
def asset_server(tmp_path: Path):
    ui_dist = tmp_path / "ui_dist"
    ui_dist.mkdir()
    (ui_dist / "index.html").write_text(
        "<!DOCTYPE html><html><body>Test</body></html>", encoding="utf-8"
    )
    (ui_dist / "test.js").write_text("console.log('test');", encoding="utf-8")

    cache_dir = tmp_path / "preview_cache"
    cache_dir.mkdir()
    # Dummy preview
    synthetic_rgb((100, 100)).save(cache_dir / "preview_dummy.jpg", format="JPEG")

    server = AssetServer(
        ui_dist_dir=ui_dist, cache_dir=cache_dir, templates_root=SYNTHETIC_TPL.parents[1]
    )
    server.start()
    yield server
    server.stop()


def test_asset_server_serves_static_and_previews(asset_server: AssetServer) -> None:
    base = asset_server.base_url

    # 1. Root index.html
    with urllib.request.urlopen(f"{base}/") as res:
        assert res.status == 200
        content = res.read().decode("utf-8")
        assert "Test" in content

    # 2. Static js file
    with urllib.request.urlopen(f"{base}/test.js") as res:
        assert res.status == 200
        content = res.read().decode("utf-8")
        assert "console.log" in content

    # 3. Preview proxy image
    with urllib.request.urlopen(f"{base}/api/preview/preview_dummy.jpg") as res:
        assert res.status == 200
        assert res.headers.get("Content-Type") == "image/jpeg"
        assert len(res.read()) > 0


def test_default_ui_dist_dir_is_repo_apps_ui_dist() -> None:
    """Regression: the default used to resolve to apps/apps/ui/dist (404 index.html)."""
    from evydencia_print_generator.paths import repo_root, ui_dist_dir

    server = AssetServer()  # no injected ui_dist_dir on purpose
    try:
        assert server.ui_dist_dir == repo_root() / "apps" / "ui" / "dist"
        assert server.ui_dist_dir == ui_dist_dir()
        assert server.ui_dist_dir.parent.name == "ui"
        assert server.ui_dist_dir.parent.parent.name == "apps"
        assert server.ui_dist_dir.parent.parent.parent == repo_root()
    finally:
        server.server.server_close()  # not started: stop() would block in shutdown()


def test_ui_dist_dir_env_override(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from evydencia_print_generator.paths import ui_dist_dir

    monkeypatch.setenv("EVYDENCIA_UI_DIST_DIR", str(tmp_path))
    assert ui_dist_dir() == tmp_path


def test_asset_server_reports_missing_ui_build(tmp_path: Path) -> None:
    import urllib.error

    server = AssetServer(ui_dist_dir=tmp_path / "nope", cache_dir=tmp_path)
    server.start()
    try:
        with pytest.raises(urllib.error.HTTPError) as exc:
            urllib.request.urlopen(f"{server.base_url}/")
        assert exc.value.code == 404
        assert "UI build not found" in exc.value.reason
    finally:
        server.stop()


def test_desktop_bridge_full_lifecycle(asset_server: AssetServer, tmp_path: Path) -> None:
    registry = SourceRegistry()
    cache = PreviewCache(asset_server.cache_dir)
    preview_service = PreviewService(registry, cache=cache)
    ingest_service = IngestService(registry, schedule_preview=preview_service.ensure_preview)

    bridge = DesktopBridge(
        registry=registry,
        ingest_service=ingest_service,
        preview_service=preview_service,
        server_base_url=asset_server.base_url,
        templates_root=SYNTHETIC_TPL.parents[1],
    )

    # 1. Get templates
    templates = bridge.get_templates()
    assert len(templates) > 0
    tpl = templates[0]
    assert "slots" in tpl
    assert "canvas_px" in tpl

    # 2. Ingest photo
    photo_path = tmp_path / "camera_input.jpg"
    synthetic_rgb((500, 400)).save(photo_path, format="JPEG", quality=95)

    sources = bridge.ingest_paths([str(photo_path)])
    assert len(sources) == 1
    asset_data = sources[0]
    assert asset_data["display_name"] == "camera_input.jpg"

    # Wait for async background preview worker to finish
    asset = registry.get(asset_data["id"])
    assert asset is not None
    preview_service.ensure_preview(asset).result(timeout=2.0)

    sources = bridge.get_sources()
    asset_data = sources[0]
    assert asset_data["preview"]["status"] == "ready"
    assert asset_data["preview"]["url"].startswith(asset_server.base_url)

    # 3. Render Job via bridge
    edit_state = {
        "template_id": tpl["id"],
        "template_version": tpl["template_version"],
        "slot_edits": {
            tpl["slots"][0]["id"]: {
                "source_id": asset_data["id"],
                "pan_x_norm": 0.1,
                "pan_y_norm": -0.1,
                "scale": 1.1,
                "rotation_deg": 0.0,
            }
        },
    }
    render_result = bridge.render_job(edit_state)
    assert Path(render_result["output_path"]).is_file()
    assert render_result["bytes_written"] > 0
    assert render_result["render_time_ms"] > 0

    preview_service.shutdown()


def test_bridge_ingest_paths_is_non_blocking(tmp_path: Path) -> None:
    """Verify that bridge.ingest_paths returns immediately without waiting for preview."""
    import time

    registry = SourceRegistry()
    cache = PreviewCache(tmp_path / "cache")
    preview_service = PreviewService(registry, cache=cache)
    ingest_service = IngestService(registry, schedule_preview=preview_service.ensure_preview)

    bridge = DesktopBridge(
        registry=registry,
        ingest_service=ingest_service,
        preview_service=preview_service,
        server_base_url="http://127.0.0.1:8000",
    )

    photo_path = tmp_path / "fast_input.jpg"
    synthetic_rgb((1200, 800)).save(photo_path, format="JPEG")

    t0 = time.perf_counter()
    sources = bridge.ingest_paths([str(photo_path)])
    elapsed = time.perf_counter() - t0

    assert len(sources) == 1
    # Must return immediately (well under 200ms) without waiting for preview thumbnail
    assert elapsed < 0.2
    preview_service.shutdown()
