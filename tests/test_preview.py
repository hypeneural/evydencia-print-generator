"""E2 — Preview proxy and cache tests."""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest
from conftest import synthetic_rgb
from evydencia_print_generator.ingest import (
    IngestService,
    PreviewCache,
    PreviewService,
    PreviewStatus,
    SourceRegistry,
)
from PIL import Image, UnidentifiedImageError


@pytest.fixture
def cache_dir(tmp_path: Path) -> Path:
    d = tmp_path / "preview_cache"
    d.mkdir(parents=True, exist_ok=True)
    return d


@pytest.fixture
def cache(cache_dir: Path) -> PreviewCache:
    return PreviewCache(cache_dir=cache_dir)


@pytest.fixture
def registry() -> SourceRegistry:
    return SourceRegistry()


@pytest.fixture
def preview_service(registry: SourceRegistry, cache: PreviewCache) -> PreviewService:
    svc = PreviewService(registry=registry, cache=cache, max_side=512, max_workers=2)
    yield svc
    svc.shutdown(wait=True)


def test_cache_key_deterministic(cache: PreviewCache) -> None:
    k1 = cache.cache_key("fp123", max_side=2048)
    k2 = cache.cache_key("fp123", max_side=2048)
    k3 = cache.cache_key("fp123", max_side=1024)
    assert k1 == k2
    assert k1 != k3
    assert cache.get_path("fp123", max_side=2048).name == f"{k1}.jpg"


def test_cache_save_and_has(cache: PreviewCache) -> None:
    fp = "test_fp_save"
    assert not cache.has(fp)
    img = synthetic_rgb((100, 100))
    saved_path = cache.save_preview(fp, img, max_side=512)
    assert saved_path.is_file()
    assert cache.has(fp, max_side=512)
    with Image.open(saved_path) as saved_img:
        assert saved_img.format == "JPEG"
        assert saved_img.size == (100, 100)


def test_cache_cleanup_age(cache_dir: Path) -> None:
    cache = PreviewCache(cache_dir=cache_dir, max_age_seconds=10.0)
    img = synthetic_rgb((50, 50))
    p1 = cache.save_preview("fp_old", img)
    p2 = cache.save_preview("fp_new", img)

    # Set p1 mtime to 20 seconds in the past
    past = time.time() - 20
    os.utime(p1, (past, past))

    removed = cache.cleanup()
    assert removed == 1
    assert not p1.exists()
    assert p2.exists()


def test_cache_cleanup_max_bytes(cache_dir: Path) -> None:
    cache = PreviewCache(cache_dir=cache_dir, max_bytes=10_000)
    img = synthetic_rgb((200, 200))
    # Each JPEG is ~2-4 KB
    p1 = cache.save_preview("fp_1", img)
    time.sleep(0.01)
    p2 = cache.save_preview("fp_2", img)
    time.sleep(0.01)
    p3 = cache.save_preview("fp_3", img)
    time.sleep(0.01)
    p4 = cache.save_preview("fp_4", img)

    total_size = sum(p.stat().st_size for p in (p1, p2, p3, p4))
    assert total_size > 5000

    # Limit max_bytes to less than total size
    cache.max_bytes = total_size // 2
    removed = cache.cleanup()
    assert removed >= 1
    # Oldest (p1) should have been deleted first
    assert not p1.exists()
    assert p4.exists()


def test_cache_clear(cache: PreviewCache) -> None:
    img = synthetic_rgb((50, 50))
    cache.save_preview("fp1", img)
    cache.save_preview("fp2", img)
    assert cache.clear() == 2
    assert len(list(cache.cache_dir.glob("*.jpg"))) == 0


def test_preview_service_generates_preview(
    preview_service: PreviewService, registry: SourceRegistry, make_image
) -> None:
    img_path = make_image("sample.jpg", size=(1000, 600))
    ingest = IngestService(registry)
    asset = ingest.ingest_paths([img_path]).accepted[0]

    states: list[str] = []
    preview_service.add_listener(lambda a, s: states.append(str(s)))

    fut = preview_service.ensure_preview(asset)
    preview_path = fut.result(timeout=5.0)

    assert preview_path.is_file()
    assert asset.preview.status is PreviewStatus.READY
    assert asset.preview.cached_path == preview_path
    assert "ready" in states
    assert "loading" in states

    with Image.open(preview_path) as pimg:
        assert pimg.format == "JPEG"
        # max_side for this fixture is 512, ratio is 1000:600 -> 512:307
        assert pimg.size == (512, 307)


def test_preview_service_deduplicates_requests(
    preview_service: PreviewService, registry: SourceRegistry, make_image
) -> None:
    img_path = make_image("dedupe.jpg", size=(800, 800))
    asset = IngestService(registry).ingest_paths([img_path]).accepted[0]

    f1 = preview_service.ensure_preview(asset)
    f2 = preview_service.ensure_preview(asset)
    f3 = preview_service.ensure_preview(asset)

    # All returned the exact same future
    assert f1 is f2 is f3
    p1 = f1.result(timeout=5.0)
    assert p1.is_file()


def test_preview_service_cache_hit_fast_path(
    preview_service: PreviewService, registry: SourceRegistry, make_image
) -> None:
    img_path = make_image("fast.jpg", size=(400, 400))
    asset = IngestService(registry).ingest_paths([img_path]).accepted[0]

    # Generate once
    preview_path = preview_service.ensure_preview(asset).result(timeout=5.0)

    # Now request again
    f2 = preview_service.ensure_preview(asset)
    assert f2.done()  # completed immediately without worker scheduling
    assert f2.result() == preview_path


def test_preview_service_exif_applied(
    preview_service: PreviewService, registry: SourceRegistry, make_image
) -> None:
    # Orientation 8 (rotated 90 CCW stored -> 90 CW upright)
    img_path = make_image("exif8.jpg", size=(600, 400), orientation=8)
    asset = IngestService(registry).ingest_paths([img_path]).accepted[0]

    p_path = preview_service.ensure_preview(asset).result(timeout=5.0)
    with Image.open(p_path) as pimg:
        # Canonical upright was (600, 400), so upright preview is wider than tall
        assert pimg.width > pimg.height
        # Top-left should have the marker / tl quadrant color
        tl_pixel = pimg.getpixel((5, 5))
        # Marker is white or tl quadrant is red (220, 40, 40)
        assert tl_pixel[0] > 180  # high red component


def test_preview_service_preserves_icc(
    preview_service: PreviewService, registry: SourceRegistry, make_image
) -> None:
    img_path = make_image("with_icc.jpg", size=(200, 200), icc=True)
    asset = IngestService(registry).ingest_paths([img_path]).accepted[0]

    p_path = preview_service.ensure_preview(asset).result(timeout=5.0)
    with Image.open(p_path) as pimg:
        assert "icc_profile" in pimg.info
        assert len(pimg.info["icc_profile"]) > 0


def test_preview_service_handles_transparency(
    preview_service: PreviewService, registry: SourceRegistry, make_image
) -> None:
    # Transparent PNG
    img_path = make_image("alpha.png", size=(200, 200), fmt="PNG", mode="RGBA")
    asset = IngestService(registry).ingest_paths([img_path]).accepted[0]

    p_path = preview_service.ensure_preview(asset).result(timeout=5.0)
    with Image.open(p_path) as pimg:
        assert pimg.format == "JPEG"
        assert pimg.mode == "RGB"


def test_preview_service_error_and_retry(
    preview_service: PreviewService, registry: SourceRegistry, tmp_path: Path
) -> None:
    # Create an invalid file
    bad_img = tmp_path / "broken.jpg"
    # Write a valid header so probe passes, then truncate
    img = synthetic_rgb((100, 100))
    img.save(bad_img, format="JPEG")
    asset = IngestService(registry).ingest_paths([bad_img]).accepted[0]

    # Now corrupt it
    bad_img.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 20)

    fut = preview_service.ensure_preview(asset)
    with pytest.raises((UnidentifiedImageError, OSError)):
        fut.result(timeout=5.0)

    assert asset.preview.status is PreviewStatus.ERROR
    assert asset.preview.error_code is not None

    # Now fix the file
    img.save(bad_img, format="JPEG")
    # Invalidate registry identity by updating mtime
    st = bad_img.stat()
    os.utime(bad_img, (st.st_atime, st.st_mtime + 5))
    asset = IngestService(registry).ingest_paths([bad_img]).accepted[0]

    retry_fut = preview_service.retry(asset.id)
    assert retry_fut is not None
    p_path = retry_fut.result(timeout=5.0)
    assert p_path.is_file()
    assert asset.preview.status is PreviewStatus.READY


def test_ingest_service_schedules_preview_automatically(
    preview_service: PreviewService, registry: SourceRegistry, make_image
) -> None:
    ingest = IngestService(registry, schedule_preview=preview_service.ensure_preview)
    img_path = make_image("auto.jpg", size=(300, 200))
    result = ingest.ingest_paths([img_path])

    asset = result.accepted[0]
    # Check that preview is ready or becomes ready shortly
    timeout = time.time() + 5.0
    while asset.preview.status is not PreviewStatus.READY and time.time() < timeout:
        time.sleep(0.05)

    assert asset.preview.status is PreviewStatus.READY
    assert asset.preview.cached_path is not None
    assert asset.preview.cached_path.is_file()
