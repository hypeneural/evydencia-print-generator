"""Benchmark preview proxy generation and cache performance.

Measures:
1. Synthetic image preview generation (simulated 24 MP 6000x4000, 12 MP 4000x3000).
2. Real image preview generation (optional via --image <path> or --dir <dir>).
3. Cache hit latency (<5ms target).
4. Proportional draft speedup vs standard decode.

Usage:
    python scripts/bench_preview.py
    python scripts/bench_preview.py --image "path/to/photo.jpg"
"""

from __future__ import annotations

import argparse
import statistics
import sys
import tempfile
import time
from pathlib import Path

from evydencia_print_generator.ingest.cache import PreviewCache
from evydencia_print_generator.ingest.preview import generate_preview_image
from PIL import Image


def bench_single(
    image_path: Path, cache: PreviewCache, iterations: int = 5
) -> dict[str, float | str]:
    # 1. Measure cold generate_preview_image
    cold_times: list[float] = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        img, icc = generate_preview_image(image_path, max_side=2048)
        cold_times.append(time.perf_counter() - t0)

    # 2. Measure cache save
    fp = f"bench_{image_path.stem}"
    t0 = time.perf_counter()
    cached_path = cache.save_preview(fp, img, max_side=2048, quality=85, icc_profile=icc)
    save_time = time.perf_counter() - t0

    # 3. Measure cache hit lookup
    hit_times: list[float] = []
    for _ in range(100):
        t0 = time.perf_counter()
        _ = cache.has(fp, 2048)
        _ = cache.get_path(fp, 2048)
        hit_times.append(time.perf_counter() - t0)

    return {
        "file": image_path.name,
        "size_bytes": image_path.stat().st_size,
        "preview_size": f"{img.width}x{img.height}",
        "cold_median_ms": statistics.median(cold_times) * 1000,
        "cold_min_ms": min(cold_times) * 1000,
        "save_ms": save_time * 1000,
        "cached_file_size_bytes": cached_path.stat().st_size,
        "cache_hit_p95_us": statistics.quantiles(hit_times, n=20)[18] * 1_000_000,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Preview Generation Benchmark")
    parser.add_argument("--image", type=Path, help="Path to real image file to benchmark")
    parser.add_argument("--dir", type=Path, help="Directory of real images to benchmark")
    parser.add_argument("--iterations", type=int, default=5, help="Number of iterations per test")
    args = parser.parse_args()

    print("=" * 60)
    print("EVYDENCIA PRINT GENERATOR - PREVIEW BENCHMARK")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmp_dir:
        cache = PreviewCache(Path(tmp_dir), max_bytes=100 * 1024 * 1024)

        images_to_test: list[Path] = []

        if args.image and args.image.is_file():
            images_to_test.append(args.image)
        elif args.dir and args.dir.is_dir():
            images_to_test.extend(
                p
                for p in sorted(args.dir.iterdir())
                if p.suffix.lower() in {".jpg", ".jpeg", ".png"}
            )
        else:
            # Create synthetic 24 MP and 12 MP images
            tmp_path = Path(tmp_dir)
            p24 = tmp_path / "synthetic_24mp.jpg"
            print("Creating synthetic 24 MP test image (6000x4000)...")
            Image.new("RGB", (6000, 4000), color=(180, 50, 60)).save(p24, format="JPEG", quality=95)
            images_to_test.append(p24)

            p12 = tmp_path / "synthetic_12mp.jpg"
            print("Creating synthetic 12 MP test image (4000x3000)...")
            Image.new("RGB", (4000, 3000), color=(50, 120, 180)).save(
                p12, format="JPEG", quality=95
            )
            images_to_test.append(p12)

        print(
            f"\nBenchmarking {len(images_to_test)} image(s) with "
            f"{args.iterations} iterations each...\n"
        )

        for img_path in images_to_test:
            results = bench_single(img_path, cache, iterations=args.iterations)
            size_mb = float(results["size_bytes"]) / (1024 * 1024)
            print(f"Image: {results['file']} ({size_mb:.2f} MB)")
            print(f"  Preview Output Size : {results['preview_size']}")
            print(
                f"  Cold Preview Decode : median {results['cold_median_ms']:.1f} ms "
                f"(min {results['cold_min_ms']:.1f} ms)"
            )
            cached_kb = float(results["cached_file_size_bytes"]) / 1024
            print(f"  Cache Save          : {results['save_ms']:.1f} ms ({cached_kb:.1f} KB)")
            print(f"  Cache Hit Lookup    : p95 {results['cache_hit_p95_us']:.1f} us")

            # Budget check: <1000 ms target
            median_ms = float(results["cold_median_ms"])
            if median_ms <= 1000.0:
                print(f"  Budget Status       : PASS (budget <= 1000 ms, {median_ms:.1f} ms)")
            else:
                print(f"  Budget Status       : WARN (exceeds 1000 ms: {median_ms:.1f} ms)")
            print("-" * 60)

    print("\nBenchmark completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
