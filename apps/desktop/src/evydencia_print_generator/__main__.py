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
    parser.add_argument("--debug", action="store_true", help="Enable webview debug tools")
    parser.add_argument("--version", action="version", version=__version__)
    return parser


def _safe_console() -> None:
    # Redirected stdout on Windows may use a legacy code page; never crash on accented names.
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if reconfigure is not None:
        reconfigure(errors="replace")


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    _safe_console()

    # GUI Mode: explicit flag or environment variable
    if args.gui or os.environ.get("EVYDENCIA_GUI") == "1":
        from .app import launch_app

        return launch_app(initial_image_paths=args.images, debug=args.debug)

    # CLI Mode: default behavior for batch/CLI testing
    if not args.images:
        print("EVYDÊNCIA Print Generator bootstrap (use --gui to launch interface)")
        return 0

    from .ingest import IngestService, SourceRegistry

    result = IngestService(SourceRegistry()).ingest_paths(args.images, origin="cli")
    for asset in result.accepted:
        size = f"{asset.width_px}x{asset.height_px}"
        print(f"OK    {asset.display_name}  {asset.probe.format} {size}")
    for rejected in result.rejected:
        print(f"ERRO  {rejected.display_name}  {rejected.code}")
    return 0 if result.accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
