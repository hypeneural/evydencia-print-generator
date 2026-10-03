"""E1 — SourceRegistry + IngestService (synthetic images only)."""

from __future__ import annotations

import json
import os
import sys
import threading
from pathlib import Path

import pytest
from conftest import QUADRANT_COLORS, synthetic_rgb
from evydencia_print_generator.ingest import (
    IngestService,
    PreviewStatus,
    RejectCode,
    SourceRegistry,
)
from evydencia_print_generator.ingest.validator import probe_image
from PIL import Image, ImageOps


@pytest.fixture
def service() -> IngestService:
    return IngestService(SourceRegistry())


def test_accepts_jpeg_and_png(service: IngestService, make_image) -> None:
    jpg = make_image("a.jpg", size=(80, 60))
    png = make_image("b.png", size=(30, 50), fmt="PNG")
    result = service.ingest_paths([jpg, png])
    assert [a.probe.format for a in result.accepted] == ["JPEG", "PNG"]
    assert (result.accepted[0].width_px, result.accepted[0].height_px) == (80, 60)
    assert (result.accepted[1].width_px, result.accepted[1].height_px) == (30, 50)
    assert all(a.preview.status is PreviewStatus.PENDING for a in result.accepted)
    assert not result.rejected


@pytest.mark.parametrize("orientation", [1, 3, 6, 8])
def test_exif_fixture_roundtrip(make_image, orientation: int) -> None:
    path = make_image("o.png", size=(64, 48), fmt="PNG", orientation=orientation)
    with Image.open(path) as im:
        upright = ImageOps.exif_transpose(im).convert("RGB")
    assert upright.tobytes() == synthetic_rgb((64, 48)).tobytes()


@pytest.mark.parametrize(("orientation", "swapped"), [(1, False), (3, False), (6, True), (8, True)])
def test_dimensions_after_exif(make_image, orientation: int, swapped: bool) -> None:
    path = make_image(f"o{orientation}.jpg", size=(64, 48), orientation=orientation)
    probe = probe_image(path)
    assert probe.exif_orientation == orientation
    assert (probe.width_px, probe.height_px) == (64, 48)  # upright size == canonical
    stored = (probe.stored_width_px, probe.stored_height_px)
    assert stored == ((48, 64) if swapped else (64, 48))


def test_same_file_twice_in_batch_is_one_source(service: IngestService, make_image) -> None:
    path = make_image()
    result = service.ingest_paths([path, path, str(path)])
    assert len(result.accepted) == 1
    assert len(service.registry) == 1


def test_reingest_returns_existing_without_new_preview(make_image) -> None:
    scheduled: list[str] = []
    svc = IngestService(SourceRegistry(), schedule_preview=lambda a: scheduled.append(a.id))
    path = make_image()
    first = svc.ingest_paths([path])
    second = svc.ingest_paths([path], origin="drop")
    assert first.added and not first.existing
    assert second.existing and not second.added
    assert first.accepted[0].id == second.accepted[0].id
    assert scheduled == [first.accepted[0].id]  # exactly one preview request


def test_relative_and_absolute_paths_dedupe(
    service: IngestService, make_image, monkeypatch, tmp_path: Path
) -> None:
    path = make_image("rel.jpg")
    monkeypatch.chdir(tmp_path)
    result = service.ingest_paths(["rel.jpg", path])
    assert len(result.accepted) == 1


@pytest.mark.skipif(sys.platform != "win32", reason="case-insensitive filesystem")
def test_case_variants_dedupe_on_windows(service: IngestService, make_image) -> None:
    path = make_image("Caixa.jpg")
    result = service.ingest_paths([path, Path(str(path).upper())])
    assert len(result.accepted) == 1


def test_modified_file_keeps_id_and_refreshes(make_image) -> None:
    scheduled: list[str] = []
    svc = IngestService(SourceRegistry(), schedule_preview=lambda a: scheduled.append(a.id))
    path = make_image("m.jpg", size=(64, 48))
    first = svc.ingest_paths([path]).accepted[0]
    old_fp = first.identity.fingerprint
    synthetic_rgb((100, 40)).save(path, format="JPEG", quality=90)
    st = path.stat()
    os.utime(path, ns=(st.st_atime_ns, st.st_mtime_ns + 5_000_000_000))
    result = svc.ingest_paths([path])
    assert result.refreshed and not result.added
    refreshed = result.refreshed[0]
    assert refreshed.id == first.id
    assert refreshed.identity.fingerprint != old_fp
    assert (refreshed.width_px, refreshed.height_px) == (100, 40)
    assert scheduled == [first.id, first.id]


def test_png_with_jpg_extension_is_detected_by_content(service: IngestService, make_image) -> None:
    path = make_image("disfarcado.jpg", fmt="PNG")
    result = service.ingest_paths([path])
    assert result.accepted[0].probe.format == "PNG"


def test_text_with_jpg_extension_is_rejected(service: IngestService, tmp_path: Path) -> None:
    fake = tmp_path / "nota.jpg"
    fake.write_text("isto não é uma imagem", encoding="utf-8")
    result = service.ingest_paths([fake])
    assert [r.code for r in result.rejected] == [RejectCode.UNSUPPORTED_FORMAT]


def test_unsupported_real_format_is_rejected(service: IngestService, tmp_path: Path) -> None:
    gif = tmp_path / "anim.gif"
    synthetic_rgb().save(gif, format="GIF")
    result = service.ingest_paths([gif])
    assert [r.code for r in result.rejected] == [RejectCode.UNSUPPORTED_FORMAT]


def test_truncated_png_is_corrupt(service: IngestService, make_image) -> None:
    path = make_image("cortado.png", size=(256, 256), fmt="PNG")
    data = path.read_bytes()
    path.write_bytes(data[: len(data) // 2])
    result = service.ingest_paths([path])
    assert [r.code for r in result.rejected] == [RejectCode.CORRUPT]


def test_cmyk_is_rejected_until_color_policy(service: IngestService, make_image) -> None:
    path = make_image("cmyk.jpg", mode="CMYK")
    result = service.ingest_paths([path])
    assert [r.code for r in result.rejected] == [RejectCode.UNSUPPORTED_COLOR_MODE]


def test_camera_mpo_is_treated_as_jpeg(service: IngestService, tmp_path: Path) -> None:
    """Regression: Canon EOS JPEGs embed an MPF secondary image and open as 'MPO'."""
    path = tmp_path / "IMG_0001.JPG"
    exif = Image.Exif()
    exif[0x0112] = 8
    exif.get_ifd(0x8769)[0xA001] = 1  # ExifIFD ColorSpace = sRGB
    primary = synthetic_rgb((60, 40))
    primary.save(
        path, format="MPO", save_all=True, append_images=[synthetic_rgb((16, 12))],
        exif=exif.tobytes(),
    )
    asset = service.ingest_paths([path]).accepted[0]
    assert asset.probe.container == "MPO"
    assert asset.probe.format == "JPEG"
    assert (asset.width_px, asset.height_px) == (40, 60)  # EXIF 8 swaps
    assert asset.probe.exif_color_space == "sRGB"
    assert asset.to_ui_dict()["format"] == "JPEG"


def test_missing_directory_and_empty_inputs(service: IngestService, tmp_path: Path) -> None:
    result = service.ingest_paths([tmp_path / "nao-existe.jpg", tmp_path, ""])
    assert [r.code for r in result.rejected] == [
        RejectCode.NOT_FOUND,
        RejectCode.NOT_A_FILE,
        RejectCode.NOT_FOUND,
    ]


def test_unicode_spaces_and_long_names(service: IngestService, make_image, tmp_path: Path) -> None:
    folder = tmp_path / "Ensaio de Natal — Família Conceição"
    names = ["Fotografia ção ñ 日本 (1).jpg", ("x" * 180) + ".png"]
    paths = [
        make_image(names[0], directory=folder),
        make_image(names[1], fmt="PNG", directory=folder),
    ]
    result = service.ingest_paths(paths)
    assert [a.display_name for a in result.accepted] == names


def test_mixed_batch_keeps_order_and_reports_rejections(
    service: IngestService, make_image, tmp_path: Path
) -> None:
    good1, good2 = make_image("1.jpg"), make_image("2.png", fmt="PNG")
    bad = tmp_path / "ruim.jpg"
    bad.write_bytes(b"\x00" * 32)
    result = service.ingest_paths([good2, bad, good1])
    assert [a.display_name for a in result.accepted] == ["2.png", "1.jpg"]
    assert [r.display_name for r in result.rejected] == ["ruim.jpg"]


def test_icc_detected(service: IngestService, make_image) -> None:
    asset = service.ingest_paths([make_image("icc.jpg", icc=True)]).accepted[0]
    assert asset.probe.has_icc
    assert asset.probe.icc_description and "sRGB" in asset.probe.icc_description
    plain = service.ingest_paths([make_image("plain.jpg")]).accepted[0]
    assert not plain.probe.has_icc


def test_ui_payload_never_contains_paths(service: IngestService, make_image, tmp_path) -> None:
    good = make_image("privado.jpg", directory=tmp_path / "Cliente Secreto")
    result = service.ingest_paths([good, tmp_path / "sumiu.jpg"])
    payload = json.dumps(result.to_ui_dict(), ensure_ascii=False)
    assert "Cliente Secreto" not in payload
    assert str(tmp_path) not in payload
    assert "path" not in result.accepted[0].to_ui_dict()
    assert "privado.jpg" in payload  # basename is fine for the operator


def test_unknown_origin_rejected(service: IngestService) -> None:
    with pytest.raises(ValueError):
        service.ingest_paths([], origin="network")  # type: ignore[arg-type]


def test_registry_preview_update_ignores_stale_fingerprint(service: IngestService, make_image):
    asset = service.ingest_paths([make_image()]).accepted[0]
    reg = service.registry
    assert reg.update_preview(asset.id, "stale", PreviewStatus.READY) is None
    assert reg.get(asset.id).preview.status is PreviewStatus.PENDING
    fp = asset.identity.fingerprint
    assert reg.update_preview(asset.id, fp, PreviewStatus.READY).preview.status == "ready"


def test_registry_is_thread_safe_under_concurrent_ingest(make_image) -> None:
    svc = IngestService(SourceRegistry())
    paths = [make_image(f"c{i}.jpg") for i in range(8)]
    errors: list[BaseException] = []

    def worker() -> None:
        try:
            svc.ingest_paths(paths)
        except BaseException as exc:  # pragma: no cover - surfaced below
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
    assert len(svc.registry) == 8


def test_synthetic_quadrants_are_distinct() -> None:
    assert len(set(QUADRANT_COLORS.values())) == 4
