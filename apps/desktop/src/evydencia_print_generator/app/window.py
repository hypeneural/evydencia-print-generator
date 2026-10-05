"""Application window launcher using pywebview."""

from __future__ import annotations

import logging
from collections.abc import Sequence

from ..ingest import IngestService, PreviewCache, PreviewService, SourceRegistry
from ..paths import preview_cache_dir, ui_dist_dir
from .bridge import DesktopBridge
from .server import AssetServer

logger = logging.getLogger(__name__)


def launch_app(
    initial_image_paths: Sequence[str] | None = None,
    debug: bool = False,
) -> int:
    """Launch the EVYDÊNCIA Print Generator desktop interface."""
    import webview

    index_html = ui_dist_dir() / "index.html"
    if not index_html.is_file():
        logger.error("UI build not found at %s. Run: npm --prefix apps/ui run build", index_html)
        return 2

    # 1. Initialize core services
    registry = SourceRegistry()
    cache = PreviewCache(preview_cache_dir())
    preview_service = PreviewService(registry, cache=cache)
    ingest_service = IngestService(registry, schedule_preview=preview_service.ensure_preview)

    # Pre-ingest any initial paths passed via CLI / Explorer (non-blocking)
    startup_ids: list[str] = []
    if initial_image_paths:
        startup_res = ingest_service.ingest_paths(initial_image_paths, origin="cli")
        startup_ids = list(startup_res.accepted_ids)

    # 2. Start localhost asset server
    server = AssetServer(cache_dir=cache.cache_dir)
    server.start()

    # 3. Create DesktopBridge
    bridge = DesktopBridge(
        registry=registry,
        ingest_service=ingest_service,
        preview_service=preview_service,
        server_base_url=server.base_url,
        startup_accepted_ids=startup_ids,
    )

    try:
        # 4. Create and launch pywebview window
        window = webview.create_window(
            title="EVYDÊNCIA — Gerador de Produção",
            url=server.base_url,
            js_api=bridge,
            width=1280,
            height=800,
            min_size=(1024, 680),
        )
        bridge.set_window(window)

        def on_window_loaded() -> None:
            try:
                from webview.dom import DOMEventHandler

                window.dom.document.events.dragenter += DOMEventHandler(
                    callback=bridge.handle_drag_ignore,
                    prevent_default=True,
                )
                window.dom.document.events.dragover += DOMEventHandler(
                    callback=bridge.handle_drag_ignore,
                    prevent_default=True,
                )
                window.dom.document.events.drop += DOMEventHandler(
                    callback=bridge.handle_native_drop,
                    prevent_default=True,
                )
            except Exception as exc:
                logger.warning("Could not register native DOM drag/drop handlers: %s", exc)

        window.events.loaded += on_window_loaded
        webview.start(debug=debug)
        return 0
    finally:
        # Clean shutdown
        preview_service.shutdown()
        server.stop()
