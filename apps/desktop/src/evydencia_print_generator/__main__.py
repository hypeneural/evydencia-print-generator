"""CLI and GUI entry point for EVYDÊNCIA Print Generator."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence

from . import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="evydencia-print-generator")
    parser.add_argument("images", nargs="*", help="Image paths passed by Windows Explorer or CLI")
    parser.add_argument("--gui", action="store_true", help="Launch interactive graphical interface")
    parser.add_argument(
        "--shell-request",
        help="Path to manifest containing selected files from Windows shell extension",
    )
    parser.add_argument("--debug", action="store_true", help="Enable webview debug tools")
    parser.add_argument("--version", action="version", version=__version__)
    return parser


def _safe_console() -> None:
    # Redirected stdout on Windows may use a legacy code page; never crash on accented names.
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if reconfigure is not None:
        reconfigure(errors="replace")


def _read_shell_request(manifest_path_str: str) -> list[str]:
    import tempfile
    from pathlib import Path

    manifest_path = Path(manifest_path_str)
    if not manifest_path.exists():
        return []

    try:
        content = manifest_path.read_text(encoding="utf-8").strip()
    except Exception:
        try:
            content = manifest_path.read_text(encoding="latin-1").strip()
        except Exception:
            return []

    paths: list[str] = []
    if content.startswith(("[", "{")):
        import json

        try:
            data = json.loads(content)
            if isinstance(data, list):
                paths = [str(p) for p in data if isinstance(p, str)]
            elif isinstance(data, dict) and "files" in data and isinstance(data["files"], list):
                paths = [str(p) for p in data["files"] if isinstance(p, str)]
        except Exception:
            pass

    if not paths:
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                paths.append(line)

    # Clean up manifest if located inside system temp directory
    try:
        temp_dir = Path(tempfile.gettempdir()).resolve()
        if temp_dir in manifest_path.resolve().parents:
            manifest_path.unlink(missing_ok=True)
    except Exception:
        pass

    return paths


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    _safe_console()

    images = list(args.images)
    if args.shell_request:
        images.extend(_read_shell_request(args.shell_request))

    # GUI Mode: explicit flag or environment variable
    if args.gui or os.environ.get("EVYDENCIA_GUI") == "1":
        from .app import launch_app

        return launch_app(initial_image_paths=images, debug=args.debug)

    # CLI Mode: default behavior for batch/CLI testing
    if not images:
        print("EVYDÊNCIA Print Generator bootstrap (use --gui to launch interface)")
        return 0

    from .ingest import IngestService, SourceRegistry

    result = IngestService(SourceRegistry()).ingest_paths(images, origin="cli")
    for asset in result.accepted:
        size = f"{asset.width_px}x{asset.height_px}"
        print(f"OK    {asset.display_name}  {asset.probe.format} {size}")
    for rejected in result.rejected:
        print(f"ERRO  {rejected.display_name}  {rejected.code}")
    return 0 if result.accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
