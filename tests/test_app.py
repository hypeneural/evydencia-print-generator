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
