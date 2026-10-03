from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from . import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="evydencia-print-generator")
    parser.add_argument("images", nargs="*", help="Image paths passed by Windows Explorer or CLI")
    parser.add_argument("--version", action="version", version=__version__)
    return parser


def _safe_console() -> None:
    # Redirected stdout on Windows may use a legacy code page; never crash on accented names.
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if reconfigure is not None:
        reconfigure(errors="replace")


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.images:
        print("EVYDÊNCIA Print Generator bootstrap")
        return 0

    from .ingest import IngestService, SourceRegistry

    _safe_console()
    result = IngestService(SourceRegistry()).ingest_paths(args.images, origin="cli")
    for asset in result.accepted:
        size = f"{asset.width_px}x{asset.height_px}"
        print(f"OK    {asset.display_name}  {asset.probe.format} {size}")
    for rejected in result.rejected:
        print(f"ERRO  {rejected.display_name}  {rejected.code}")
    print("Ingest concluído; editor visual ainda não implementado (M1 PR D).")
    return 0 if result.accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
