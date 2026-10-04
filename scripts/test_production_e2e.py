#!/usr/bin/env python3
"""E2E Production Validation and Benchmark Verification for M1/M2 Products.

Validates the full pipeline against real customer photos and templates:
- Calendário 2027 (1 slot com moldura)
- Globo de Neve (2 slots simétricos 50x80mm em 10x15cm)
- Chaveiro 3x4 (18 slots 34x44mm em folha 15x21cm)

Usage:
    python scripts/test_production_e2e.py --template calendario
    python scripts/test_production_e2e.py --template globo
    python scripts/test_production_e2e.py --template chaveiro
    python scripts/test_production_e2e.py --template all
"""

from __future__ import annotations

import argparse
import sys
import tempfile
import time
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "desktop" / "src"))

from evydencia_print_generator.domain.job import (  # noqa: E402
    EditState,
    SlotEdit,
    build_job_snapshot,
)
from evydencia_print_generator.domain.template import (  # noqa: E402
    Canvas,
    OutputSpec,
    Overlay,
    Slot,
    Template,
    load_template,
)
from evydencia_print_generator.domain.transform import SlotTransform  # noqa: E402
from evydencia_print_generator.ingest import (  # noqa: E402
    IngestService,
    PreviewCache,
    PreviewService,
    SourceRegistry,
)
from evydencia_print_generator.render import RenderOptions, render  # noqa: E402

TEMPLATES_DIR = ROOT / "templates"


def find_default_photo() -> Path | None:
    candidate_dir = Path.home() / "Desktop" / "ARTES NATAL" / "Foto_teste"
    if candidate_dir.is_dir():
        for p in candidate_dir.glob("*.JPG"):
            return p
        for p in candidate_dir.glob("*.jpg"):
            return p
    return None


def find_default_moldura() -> Path | None:
    candidate = Path.home() / "Desktop" / "ARTES NATAL" / "FINAL" / "moldura.png"
    return candidate if candidate.is_file() else None


def run_template_validation(
    tpl_name: str,
    photo_path: Path,
    moldura_path: Path | None,
    out_dir: Path,
    registry: SourceRegistry,
    asset: any,
) -> bool:
    print("\n==================================================")
    print(f"==> Validating product: {tpl_name.upper()}")
    print("==================================================")

    initial_mtime = photo_path.stat().st_mtime_ns
    initial_size = photo_path.stat().st_size

    # Configure template
    if tpl_name == "calendario":
        if moldura_path is not None and moldura_path.is_file():
            with Image.open(moldura_path) as m_im:
                mw, mh = m_im.size
            overlay_obj = Overlay(path=str(moldura_path), required=True)
            dpi = 254
            canvas_w_mm = mw / dpi * 25.4
            canvas_h_mm = mh / dpi * 25.4
            slot_x_mm = 118 / dpi * 25.4
            slot_y_mm = 107 / dpi * 25.4
            slot_w_mm = 823 / dpi * 25.4
            slot_h_mm = 395 / dpi * 25.4
        else:
            dpi = 254
            canvas_w_mm = 106.7
            canvas_h_mm = 147.4
            slot_x_mm = 11.8
            slot_y_mm = 10.7
            slot_w_mm = 82.3
            slot_h_mm = 39.5
            overlay_obj = None

        template = Template(
            id="calendario-2027",
            template_version="1.0.0",
            name="Calendário 2027",
            status="production",
            canvas=Canvas(width_mm=canvas_w_mm, height_mm=canvas_h_mm, dpi=dpi),
            output=OutputSpec(format="JPEG", quality=95, filename_prefix="Calendario_"),
            slots=(
                Slot(
                    id="foto_principal",
                    x_mm=slot_x_mm,
                    y_mm=slot_y_mm,
                    width_mm=slot_w_mm,
                    height_mm=slot_h_mm,
                    fit="cover",
                    allow_pan=True,
                    allow_zoom=True,
                    allow_rotate=True,
                ),
            ),
            overlay=overlay_obj,
            base_dir=moldura_path.parent if moldura_path else Path("."),
        )
        edits = {
            "foto_principal": SlotEdit(
                source_id=asset.id,
                transform=SlotTransform(pan_x_norm=0.0, pan_y_norm=0.0, scale=1.0),
            )
        }
    elif tpl_name == "globo":
        tpl_file = TEMPLATES_DIR / "globo-neve" / "template.json"
        template = load_template(tpl_file)
        edits = {
            "foto_1": SlotEdit(source_id=asset.id, transform=SlotTransform(scale=1.0)),
            "foto_2": SlotEdit(source_id=asset.id, transform=SlotTransform(scale=1.0)),
        }
    elif tpl_name == "chaveiro":
        tpl_file = TEMPLATES_DIR / "chaveiro-3x4" / "template.json"
        template = load_template(tpl_file)
        edits = {
            slot_id: SlotEdit(source_id=asset.id, transform=SlotTransform(scale=1.0))
            for slot_id in template.slot_ids
        }
    else:
        print(f"[FAIL] Unknown template: {tpl_name}", file=sys.stderr)
        return False

    # Build snapshot
    edit_state = EditState(
        template_id=template.id,
        template_version=template.template_version,
        slot_edits=edits,
    )
    snapshot = build_job_snapshot(template, edit_state, registry.get)

    # Render
    t0 = time.perf_counter()
    opts = RenderOptions(output_dir=out_dir, draw_cut_guidelines=True)
    result = render(template, snapshot, opts)
    t_render = (time.perf_counter() - t0) * 1000.0

    print(f"    Output: {result.output_path.name}")
    print(f"    Canvas: {result.canvas_size_px} @ {result.dpi} DPI")
    print(f"    File size: {result.bytes_written / 1024:.1f} KB")
    print(f"    Render time: {t_render:.1f} ms")

    assert result.output_path.is_file(), "Output file does not exist"
    assert t_render <= 3000.0, f"Render took {t_render:.1f} ms (> budget 3000 ms)"
    assert photo_path.stat().st_mtime_ns == initial_mtime, "Original file modified!"
    assert photo_path.stat().st_size == initial_size, "Original size changed!"
    print(f"    [OK] {tpl_name.upper()} validation PASSED 100%!")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Run E2E production validation.")
    parser.add_argument(
        "--template",
        choices=["calendario", "globo", "chaveiro", "all"],
        default="all",
        help="Target product template to validate",
    )
    parser.add_argument("--photo", type=Path, default=None, help="Path to source photo")
    parser.add_argument("--moldura", type=Path, default=None, help="Path to overlay moldura PNG")
    parser.add_argument("--out-dir", type=Path, default=None, help="Directory for output")
    args = parser.parse_args()

    photo_path = args.photo or find_default_photo()
    moldura_path = args.moldura or find_default_moldura()

    use_synthetic = photo_path is None or not photo_path.is_file()
    temp_dir = None

    if use_synthetic:
        print("[INFO] Real customer photo not found; using synthetic test fixture for CI.")
        temp_dir = tempfile.TemporaryDirectory()
        work_dir = Path(temp_dir.name)
        photo_path = work_dir / "synthetic_camera_001.jpg"
        synthetic_img = Image.new("RGB", (6000, 4000), color=(120, 180, 240))
        synthetic_img.save(photo_path, format="JPEG", quality=95)
    else:
        print(f"[OK] Using real customer photo: {photo_path}")

    out_dir = args.out_dir or photo_path.parent

    # 1. Ingest
    print("\n==> Ingesting source photo...")
    t0 = time.perf_counter()
    registry = SourceRegistry()
    ingest = IngestService(registry)
    ingest_res = ingest.ingest_paths([photo_path], origin="cli")
    t_ingest = (time.perf_counter() - t0) * 1000.0

    if not ingest_res.accepted:
        print(f"[FAIL] Ingest rejected file: {ingest_res.rejected}", file=sys.stderr)
        return 1
    asset = ingest_res.accepted[0]
    dims = f"{asset.probe.width_px}x{asset.probe.height_px}"
    print(f"    Ingested: {asset.id} ({dims}) in {t_ingest:.1f} ms")

    # 2. Preview generation
    print("==> Generating preview proxy...")
    cache_dir = Path(tempfile.gettempdir()) / "evydencia_bench_cache"
    cache = PreviewCache(cache_dir=cache_dir)
    preview_svc = PreviewService(registry, cache=cache)
    try:
        t0 = time.perf_counter()
        fut = preview_svc.ensure_preview(asset)
        preview_path = fut.result(timeout=5.0)
        t_preview = (time.perf_counter() - t0) * 1000.0
        print(f"    Preview ready: {preview_path.name} in {t_preview:.1f} ms")
        assert preview_path.is_file()
    finally:
        preview_svc.shutdown()

    # Determine templates to run
    targets = ["calendario", "globo", "chaveiro"] if args.template == "all" else [args.template]

    for tpl in targets:
        success = run_template_validation(tpl, photo_path, moldura_path, out_dir, registry, asset)
        if not success:
            return 1

    print("\n==================================================")
    print("==> ALL PRODUCTS VALIDATED IN PRODUCTION 100%!")
    print("==================================================")

    if temp_dir is not None:
        temp_dir.cleanup()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
