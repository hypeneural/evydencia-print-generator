"""pywebview JS/Python bridge implementation."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

from ..domain.job import EditState, build_job_snapshot
from ..domain.template import Template, load_template
from ..ingest import IngestService, PreviewService, SourceRegistry
from ..paths import templates_dir
from ..render import RenderOptions, RenderResult, render


class DesktopBridge:
    """Methods exposed to JavaScript as `window.pywebview.api`."""

    def __init__(
        self,
        registry: SourceRegistry,
        ingest_service: IngestService,
        preview_service: PreviewService,
        server_base_url: str,
        templates_root: Path | None = None,
    ) -> None:
        self.registry = registry
        self.ingest_service = ingest_service
        self.preview_service = preview_service
        self.server_base_url = server_base_url.rstrip("/")
        self.templates_root = templates_root or templates_dir()
        self._window: Any = None

    def set_window(self, window: Any) -> None:
        self._window = window

    def get_templates(self) -> list[dict[str, Any]]:
        """Return available templates with resolved pixel geometries and overlay URLs."""
        templates: list[Template] = []

        # Scan production templates directory
        if self.templates_root.is_dir():
            for tpl_dir in sorted(self.templates_root.iterdir()):
                tpl_file = tpl_dir / "template.json"
                if tpl_file.is_file():
                    try:
                        tpl = load_template(tpl_file)
                        templates.append(tpl)
                    except Exception:
                        pass

        # If no renderable template in production yet, include synthetic fixture for development
        if not any(t.is_renderable for t in templates):
            fixture_tpl = (
                Path(__file__).resolve().parents[4]
                / "tests"
                / "fixtures"
                / "templates"
                / "calendar-synthetic"
                / "template.json"
            )
            if fixture_tpl.is_file():
                try:
                    templates.insert(0, load_template(fixture_tpl))
                except Exception:
                    pass

        results: list[dict[str, Any]] = []
        for tpl in templates:
            # We provide templates that can be displayed/rendered
            is_renderable = tpl.is_renderable
            canvas_px = tpl.canvas_px() if is_renderable else (1000, 1000)

            slots_data = []
            for slot in tpl.slots:
                if is_renderable:
                    rect = tpl.slot_rect_px(slot.id)
                    rect_dict = {
                        "left": rect.left,
                        "top": rect.top,
                        "width": rect.width,
                        "height": rect.height,
                    }
                else:
                    rect_dict = {"left": 0, "top": 0, "width": 1000, "height": 500}

                slots_data.append(
                    {
                        "id": slot.id,
                        "x_mm": slot.x_mm or 0.0,
                        "y_mm": slot.y_mm or 0.0,
                        "width_mm": slot.width_mm or 0.0,
                        "height_mm": slot.height_mm or 0.0,
                        "rect_px": rect_dict,
                        "fit": slot.fit,
                        "allow_pan": slot.allow_pan,
                        "allow_zoom": slot.allow_zoom,
                        "allow_rotate": slot.allow_rotate,
                    }
                )

            overlay_data = None
            if tpl.overlay is not None:
                overlay_path = tpl.overlay_path()
                overlay_url = None
                if overlay_path and overlay_path.is_file():
                    rel_to_root = overlay_path.relative_to(self.templates_root)
                    overlay_url = f"{self.server_base_url}/api/templates/{rel_to_root.as_posix()}"

                overlay_data = {
                    "path": tpl.overlay.path,
                    "url": overlay_url,
                }

            results.append(
                {
                    "id": tpl.id,
                    "template_version": tpl.template_version,
                    "name": tpl.name,
                    "status": tpl.status,
                    "canvas": {
                        "width_mm": tpl.canvas.width_mm or 0.0,
                        "height_mm": tpl.canvas.height_mm or 0.0,
                        "dpi": tpl.canvas.dpi or 0,
                    },
                    "canvas_px": {
                        "width": canvas_px[0],
                        "height": canvas_px[1],
                    },
                    "slots": slots_data,
                    "overlay": overlay_data,
                }
            )

        return results

    def get_sources(self) -> list[dict[str, Any]]:
        """Return all assets currently in SourceRegistry with proxy URLs."""
        sources = []
        for asset in self.registry.list():
            preview_url = None
            if asset.preview.cached_path and asset.preview.cached_path.is_file():
                preview_url = f"{self.server_base_url}/api/preview/{asset.preview.cached_path.name}"

            sources.append(
                {
                    "id": asset.id,
                    "display_name": asset.display_name,
                    "probe": {
                        "format": asset.probe.format,
                        "width": asset.probe.stored_width_px,
                        "height": asset.probe.stored_height_px,
                        "oriented_width": asset.probe.width_px,
                        "oriented_height": asset.probe.height_px,
                        "has_icc": asset.probe.has_icc,
                    },
                    "preview": {
                        "status": asset.preview.status.value,
                        "url": preview_url,
                        "error_code": asset.preview.error_code,
                    },
                }
            )
        return sources

    def open_file_dialog(self) -> list[dict[str, Any]]:
        """Trigger native Windows file dialog and ingest selected files."""
        if not self._window:
            return self.get_sources()

        try:
            import webview

            result = self._window.create_file_dialog(
                webview.FileDialog.OPEN,
                allow_multiple=True,
                file_types=["Image Files (*.jpg;*.jpeg;*.png)"],
            )
            if result:
                return self.ingest_paths(list(result))
        except Exception:
            pass

        return self.get_sources()

    def ingest_paths(self, paths: list[str]) -> list[dict[str, Any]]:
        """Ingest paths, trigger async preview generation, and return updated sources."""
        ingest_res = self.ingest_service.ingest_paths(paths, origin="dialog")
        for asset in ingest_res.accepted:
            fut = self.preview_service.ensure_preview(asset)
            try:
                fut.result(timeout=1.0)
            except Exception:
                pass

        return self.get_sources()

    def render_job(self, edit_state_dict: dict[str, Any]) -> dict[str, Any]:
        """Validate UI edit state, load template, build snapshot, and render from original photo."""
        edit_state = EditState.from_ui(edit_state_dict)

        # Find template
        tpl_path = self.templates_root / edit_state.template_id / "template.json"
        if not tpl_path.is_file():
            # Check synthetic fixture
            fixture_tpl = (
                Path(__file__).resolve().parents[4]
                / "tests"
                / "fixtures"
                / "templates"
                / edit_state.template_id
                / "template.json"
            )
            if fixture_tpl.is_file():
                tpl_path = fixture_tpl
            else:
                raise ValueError(f"Template not found: {edit_state.template_id}")

        template = load_template(tpl_path)
        snapshot = build_job_snapshot(template, edit_state, self.registry.get)
        result: RenderResult = render(template, snapshot, RenderOptions(draw_cut_guidelines=True))

        return {
            "output_path": str(result.output_path),
            "template_id": result.template_id,
            "canvas_size_px": list(result.canvas_size_px),
            "dpi": result.dpi,
            "render_time_ms": result.render_time_ms,
            "bytes_written": result.bytes_written,
        }

    def open_output_folder(self, file_path: str) -> bool:
        """Reveal generated output file in Windows File Explorer."""
        p = Path(file_path).resolve()
        if not p.is_file():
            return False

        if os.name == "nt":
            try:
                subprocess.run(
                    ["explorer.exe", f"/select,{p}"],
                    check=False,
                )
                return True
            except Exception:
                pass
        return True
