#!/usr/bin/env python3
from __future__ import annotations

import argparse

MM_PER_INCH = 25.4

def mm_to_px(mm: float, dpi: int) -> int:
    return round(mm / MM_PER_INCH * dpi)

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert millimeters to pixels using the project rounding rule."
    )
    parser.add_argument("mm", type=float)
    parser.add_argument("--dpi", type=int, default=300)
    args = parser.parse_args()
    print(mm_to_px(args.mm, args.dpi))

if __name__ == "__main__":
    main()
