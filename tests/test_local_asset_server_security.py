"""Security regression: localhost WebView2 server serves only its asset roots."""
from __future__ import annotations

import urllib.error
import urllib.request

import pytest

from evydencia_print_generator.app.server import AssetServer


def test_local_asset_server_denies_parent_escape_and_cross_origin(tmp_path):
    ui = tmp_path / "ui"
    cache = tmp_path / "previews"
    templates = tmp_path / "templates"
    for root in (ui, cache, templates):
        root.mkdir()
    (ui / "index.html").write_text("Hello UI", encoding="utf-8")
    (cache / "allowed.jpg").write_bytes(b"preview bytes")
    (tmp_path / "private.jpg").write_bytes(b"do not disclose this")
    server = AssetServer(ui_dist_dir=ui, cache_dir=cache, templates_root=templates)
    server.start()
    try:
        with urllib.request.urlopen(server.base_url + "/api/preview/allowed.jpg") as response:
            assert response.read() == b"preview bytes"
            assert response.headers.get("Access-Control-Allow-Origin") is None
            assert response.headers.get("Cross-Origin-Resource-Policy") == "same-origin"
        with pytest.raises(urllib.error.HTTPError) as outside:
            urllib.request.urlopen(
                server.base_url + "/api/preview/..%2Fprivate.jpg"
            )
        assert outside.value.code == 403
        with urllib.request.urlopen(server.base_url + "/index.html") as ui_response:
            assert ui_response.read() == b"Hello UI"
    finally:
        server.stop()


def test_local_asset_server_blocks_symlink_target_outside_root(tmp_path):
    ui = tmp_path / "ui"
    cache = tmp_path / "previews"
    templates = tmp_path / "templates"
    for root in (ui, cache, templates):
        root.mkdir()
    (ui / "index.html").write_text("OK", encoding="utf-8")
    private = tmp_path / "private.jpg"
    private.write_bytes(b"secret")
    link = cache / "linked.jpg"
    try:
        link.symlink_to(private)
    except OSError:
        pytest.skip("Windows symlink requires Developer Mode or privileges")
    server = AssetServer(ui_dist_dir=ui, cache_dir=cache, templates_root=templates)
    server.start()
    try:
        with pytest.raises(urllib.error.HTTPError) as outside:
            urllib.request.urlopen(server.base_url + "/api/preview/linked.jpg")
        assert outside.value.code == 403
    finally:
        server.stop()
