"""Local ephemeral asset server for UI static files, preview proxies, and template assets."""

from __future__ import annotations

import http.server
import mimetypes
import socketserver
import threading
from pathlib import Path
from urllib.parse import unquote, urlparse

from ..paths import preview_cache_dir, templates_dir


class AssetHandler(http.server.BaseHTTPRequestHandler):
    ui_dist_dir: Path
    cache_dir: Path
    templates_root: Path

    def do_HEAD(self) -> None:
        self._serve(head_only=True)

    def do_GET(self) -> None:
        self._serve(head_only=False)

    def _serve(self, head_only: bool) -> None:
        parsed = urlparse(self.path)
        path = unquote(parsed.path)

        # 1. Preview cache: /api/preview/<filename>
        if path.startswith("/api/preview/"):
            filename = path[len("/api/preview/") :].lstrip("/")
            file_path = self.cache_dir / filename
            self._serve_file(file_path, head_only=head_only)
            return

        # 2. Template assets: /api/templates/<template_id>/<rel_path>
        if path.startswith("/api/templates/"):
            rel = path[len("/api/templates/") :].lstrip("/")
            file_path = self.templates_root / rel
            self._serve_file(file_path, head_only=head_only)
            return

        # 3. Static UI: serve from ui_dist_dir (fallback to index.html for SPA)
        rel_static = path.lstrip("/") or "index.html"
        static_file = self.ui_dist_dir / rel_static
        if not static_file.is_file():
            static_file = self.ui_dist_dir / "index.html"

        self._serve_file(static_file, head_only=head_only)

    def _serve_file(self, target: Path, head_only: bool) -> None:
        if not target.is_file():
            self.send_error(404, f"File not found: {target.name}")
            return

        ctype, _ = mimetypes.guess_type(target.name)
        if ctype is None:
            ctype = "application/octet-stream"

        try:
            stat = target.stat()
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(stat.st_size))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self.end_headers()

            if not head_only:
                with open(target, "rb") as f:
                    self.wfile.write(f.read())
        except Exception:
            self.send_error(500, "Error reading file")

    def log_message(self, format: str, *args: object) -> None:
        # Silence standard HTTP access logging in production
        pass


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


class AssetServer:
    """Ephemeral HTTP server serving frontend and asset proxies on localhost."""

    def __init__(
        self,
        ui_dist_dir: Path | None = None,
        cache_dir: Path | None = None,
        templates_root: Path | None = None,
    ) -> None:
        if ui_dist_dir is None:
            # Default to apps/ui/dist relative to package
            root = Path(__file__).resolve().parents[4]
            ui_dist_dir = root / "apps" / "ui" / "dist"

        self.ui_dist_dir = ui_dist_dir
        self.cache_dir = cache_dir or preview_cache_dir()
        self.templates_root = templates_root or templates_dir()

        handler_cls = type(
            "ConfiguredAssetHandler",
            (AssetHandler,),
            {
                "ui_dist_dir": self.ui_dist_dir,
                "cache_dir": self.cache_dir,
                "templates_root": self.templates_root,
            },
        )

        # Bind to 127.0.0.1 with port 0 (OS picks free ephemeral port)
        self.server = ThreadedTCPServer(("127.0.0.1", 0), handler_cls)
        self.port = self.server.server_address[1]
        self.base_url = f"http://127.0.0.1:{self.port}"
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        try:
            self.server.shutdown()
        except Exception:
            pass
        try:
            self.server.server_close()
        except Exception:
            pass
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
