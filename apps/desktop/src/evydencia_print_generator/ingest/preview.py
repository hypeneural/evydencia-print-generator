"""Asynchronous preview generation pipeline with draft-optimized decode, EXIF and ICC."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image, ImageOps

from ..imaging.color import get_srgb_profile_bytes, normalize_to_srgb
from .cache import PreviewCache
from .models import PreviewStatus, SourceAsset

if TYPE_CHECKING:
    from .registry import SourceRegistry

logger = logging.getLogger(__name__)

DEFAULT_PREVIEW_MAX_SIDE = 2048
DEFAULT_PREVIEW_QUALITY = 85
PreviewListener = Callable[[SourceAsset, PreviewStatus], None]


def generate_preview_image(
    path: Path, max_side: int = DEFAULT_PREVIEW_MAX_SIDE
) -> tuple[Image.Image, bytes | None]:
    """Read an image, apply draft scaling + EXIF transpose + LANCZOS + sRGB normalization."""
    with Image.open(path) as im:
        icc = im.info.get("icc_profile")
        orig_w, orig_h = im.size
        # Use proportional target size for draft() to trigger DCT downsampling on JPEG/MPO
        scale = max_side / max(orig_w, orig_h)
        if scale < 1.0:
            target = (max(1, round(orig_w * scale)), max(1, round(orig_h * scale)))
            im.draft("RGB", target)
        im.load()
        upright = ImageOps.exif_transpose(im)
        if upright is None:
            upright = im.copy()

    # Downscale to max_side if still larger
    w, h = upright.size
    if max(w, h) > max_side:
        upright.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)

    # Normalize preview proxy to canonical sRGB (ADR-012)
    srgb_img = normalize_to_srgb(upright, icc)
    return srgb_img, get_srgb_profile_bytes()


class PreviewService:
    """Thread-safe background service that produces cached preview proxies."""

    def __init__(
        self,
        registry: SourceRegistry,
        cache: PreviewCache | None = None,
        max_side: int = DEFAULT_PREVIEW_MAX_SIDE,
        quality: int = DEFAULT_PREVIEW_QUALITY,
        max_workers: int = 2,
    ) -> None:
        self.registry = registry
        self.cache = cache if cache is not None else PreviewCache()
        self.max_side = max_side
        self.quality = quality
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="preview-")
        self._lock = threading.Lock()
        self._futures: dict[tuple[str, str], Future[Path]] = {}
        self._listeners: list[PreviewListener] = []
        self._closed = False

    def add_listener(self, listener: PreviewListener) -> None:
        with self._lock:
            if listener not in self._listeners:
                self._listeners.append(listener)

    def remove_listener(self, listener: PreviewListener) -> None:
        with self._lock:
            if listener in self._listeners:
                self._listeners.remove(listener)

    def _notify(self, asset: SourceAsset, status: PreviewStatus) -> None:
        with self._lock:
            listeners = list(self._listeners)
        for listener in listeners:
            try:
                listener(asset, status)
            except Exception:
                logger.exception("Error in preview listener")

    def ensure_preview(self, asset: SourceAsset) -> Future[Path]:
        """Request preview for asset. Returns existing future if already in flight."""
        fp = asset.identity.fingerprint
        key = (asset.id, fp)

        # 1. Fast path: already on disk
        if self.cache.has(fp, self.max_side):
            cached_path = self.cache.get_path(fp, self.max_side)
            updated = self.registry.update_preview(
                asset.id, fp, PreviewStatus.READY, cached_path=cached_path
            )
            fut: Future[Path] = Future()
            fut.set_result(cached_path)
            if updated is not None:
                self._notify(updated, PreviewStatus.READY)
            return fut

        with self._lock:
            if self._closed:
                fut = Future()
                fut.set_exception(RuntimeError("PreviewService is shut down"))
                return fut

            existing = self._futures.get(key)
            if existing is not None and not existing.done():
                return existing

            updated = self.registry.update_preview(asset.id, fp, PreviewStatus.QUEUED)
            fut = self._executor.submit(self._worker, asset)
            self._futures[key] = fut

        if updated is not None:
            self._notify(updated, PreviewStatus.QUEUED)
        return fut

    def _worker(self, asset: SourceAsset) -> Path:
        fp = asset.identity.fingerprint
        key = (asset.id, fp)

        # Transition to LOADING
        loading_asset = self.registry.update_preview(asset.id, fp, PreviewStatus.LOADING)
        if loading_asset is not None:
            self._notify(loading_asset, PreviewStatus.LOADING)

        try:
            # Check cache again in case another worker produced it
            if not self.cache.has(fp, self.max_side):
                img, icc = generate_preview_image(asset.path, max_side=self.max_side)
                cached_path = self.cache.save_preview(
                    fp, img, max_side=self.max_side, quality=self.quality, icc_profile=icc
                )
            else:
                cached_path = self.cache.get_path(fp, self.max_side)

            ready_asset = self.registry.update_preview(
                asset.id, fp, PreviewStatus.READY, cached_path=cached_path
            )
            if ready_asset is not None:
                self._notify(ready_asset, PreviewStatus.READY)
            return cached_path
        except Exception as exc:
            err_code = type(exc).__name__
            err_asset = self.registry.update_preview(
                asset.id, fp, PreviewStatus.ERROR, error_code=err_code
            )
            if err_asset is not None:
                self._notify(err_asset, PreviewStatus.ERROR)
            raise
        finally:
            with self._lock:
                self._futures.pop(key, None)

    def retry(self, source_id: str) -> Future[Path] | None:
        asset = self.registry.get(source_id)
        if asset is None:
            return None
        return self.ensure_preview(asset)

    def shutdown(self, wait: bool = True) -> None:
        with self._lock:
            self._closed = True
        self._executor.shutdown(wait=wait, cancel_futures=True)
