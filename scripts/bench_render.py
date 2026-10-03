"""Benchmark deterministic rendering engine performance.

Measures:
1. End-to-end render time (original open, EXIF transpose, affine transform,
   canvas composition, JPEG encode, and atomic save).
2. Throughput on synthetic 24 MP (6000x4000) and 12 MP (4000x3000) photos.
3. Real camera RAW-derived JPEG rendering (via --photo or --dir).

Usage:
    python scripts/bench_render.py
    python scripts/bench_render.py --photo "path/to/photo.jpg"
"""

from __future__ import annotations

import argparse
import statistics
import sys
import tempfile
import time
from pathlib import Path

from evydencia_print_generator.domain.job import EditState, build_job_snapshot
from evydencia_print_generator.domain.template import load_template
from evydencia_print_generator.ingest import IngestService, SourceRegistry
from evydencia_print_generator.render import RenderOptions, render
from PIL import Image


def bench_render_single(
    template_path: Path,
    photo_path: Path,
    output_dir: Path,
    iterations: int = 5,
) -> dict[str, float | str | int]:
    template = load_template(template_path)
    registry = SourceRegistry()
    asset = IngestService(registry).ingest_paths([photo_path]).accepted[0]

    edit_state = EditState.from_ui(
        {
            "template_id": template.id,
            "template_version": template.template_version,
            "slot_edits": {
                template.slots[0].id: {
                    "source_id": asset.id,
                    "pan_x_norm": 0.15,
                    "pan_y_norm": -0.10,
                    "scale": 1.25,
                    "rotation_deg": 12.0,
                }
            },
        }
    )
    snapshot = build_job_snapshot(template, edit_state, registry.get)

    times: list[float] = []
    output_bytes = 0
    canvas_size = ""

    options = RenderOptions(output_dir=output_dir, overwrite=True)

    for _ in range(iterations):
        t0 = time.perf_counter()
        result = render(template, snapshot, options)
        dt = time.perf_counter() - t0
        times.append(dt)
        output_bytes = result.bytes_written
        canvas_size = f"{result.canvas_size_px[0]}x{result.canvas_size_px[1]}"

    return {
        "file": photo_path.name,
        "input_size_mb": photo_path.stat().st_size / (1024 * 1024),
        "canvas_size": canvas_size,
        "output_size_kb": output_bytes / 1024,
        "median_ms": statistics.median(times) * 1000,
        "min_ms": min(times) * 1000,
        "p95_ms": (
            statistics.quantiles(times, n=20)[18] * 1000 if len(times) >= 20 else max(times) * 1000
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministic Print Renderer Benchmark")
    parser.add_argument("--photo", type=Path, help="Path to real photo to benchmark")
    parser.add_argument("--dir", type=Path, help="Directory of real photos to benchmark")
    parser.add_argument("--iterations", type=int, default=5, help="Number of iterations per photo")
    args = parser.parse_args()

    tpl_path = (
        Path(__file__).resolve().parent.parent
        / "tests"
        / "fixtures"
        / "templates"
        / "calendar-synthetic"
        / "template.json"
    )

    print("=" * 60)
    print("EVYDENCIA PRINT GENERATOR - RENDERER BENCHMARK")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        out_dir = tmp_path / "renders"

        photos_to_test: list[Path] = []
        if args.photo and args.photo.is_file():
            photos_to_test.append(args.photo)
        elif args.dir and args.dir.is_dir():
            photos_to_test.extend(
                p
                for p in sorted(args.dir.iterdir())
                if p.suffix.lower() in {".jpg", ".jpeg", ".png"}
            )
        else:
            # Generate synthetic 24 MP and 12 MP images
            p24 = tmp_path / "synthetic_24mp.jpg"
            print("Generating synthetic 24 MP test photo (6000x4000)...")
            Image.new("RGB", (6000, 4000), (140, 70, 90)).save(p24, format="JPEG", quality=95)
            photos_to_test.append(p24)

            p12 = tmp_path / "synthetic_12mp.jpg"
            print("Generating synthetic 12 MP test photo (4000x3000)...")
            Image.new("RGB", (4000, 3000), (70, 120, 160)).save(p12, format="JPEG", quality=95)
            photos_to_test.append(p12)

        print(
            f"\nBenchmarking {len(photos_to_test)} photo(s) with "
            f"{args.iterations} iterations each...\n"
        )

        for photo in photos_to_test:
            res = bench_render_single(tpl_path, photo, out_dir, iterations=args.iterations)
            print(f"Photo: {res['file']} ({float(res['input_size_mb']):.2f} MB)")
            print(f"  Canvas Output       : {res['canvas_size']} px")
            print(
                f"  Render Time         : median {float(res['median_ms']):.1f} ms "
                f"(min {float(res['min_ms']):.1f} ms)"
            )
            print(f"  JPEG Output Size    : {float(res['output_size_kb']):.1f} KB")

            # Budget check: target <= 2000 ms
            med = float(res["median_ms"])
            if med <= 2000.0:
                print(f"  Budget Status       : PASS (budget <= 2000 ms, measured {med:.1f} ms)")
            else:
                print(f"  Budget Status       : WARN (exceeds 2000 ms: {med:.1f} ms)")
            print("-" * 60)

    print("\nBenchmark completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
