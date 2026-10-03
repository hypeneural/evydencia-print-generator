from __future__ import annotations

import argparse

from . import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="evydencia-print-generator")
    parser.add_argument("images", nargs="*", help="Image paths passed by Windows Explorer or CLI")
    parser.add_argument("--version", action="version", version=__version__)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.images:
        print("Bootstrap only: image launch contract accepted; UI not implemented yet.")
    else:
        print("EVYDÊNCIA Print Generator bootstrap")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
