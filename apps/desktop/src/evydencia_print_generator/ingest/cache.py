"""Local deterministic preview cache with LRU / size / age cleanup."""

from __future__ import annotations

import hashlib
import os
import secrets
import time
from pathlib import Path

from PIL import Image

from ..paths import preview_cache_dir

PREVIEW_CACHE_VERSION = "2"
DEFAULT_MAX_BYTES = 1_000_000_000  # 1 GB
DEFAULT_MAX_AGE_SECONDS = 30 * 86400.0  # 30 days


class PreviewCache:
    def __init__(
        self,
        cache_dir: Path | None = None,
        max_bytes: int = DEFAULT_MAX_BYTES,
        max_age_seconds: float = DEFAULT_MAX_AGE_SECONDS,
    ) -> None:
        self.cache_dir = Path(cache_dir) if cache_dir is not None else preview_cache_dir()
        self.max_bytes = max_bytes
        self.max_age_seconds = max_age_seconds

    def ensure_dir(self) -> Path:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        return self.cache_dir

    @staticmethod
    def cache_key(fingerprint: str, max_side: int = 2048) -> str:
        raw = f"{fingerprint}\0{PREVIEW_CACHE_VERSION}\0{max_side}".encode()
        return hashlib.sha256(raw).hexdigest()[:32]

    def get_path(self, fingerprint: str, max_side: int = 2048) -> Path:
        return self.cache_dir / f"{self.cache_key(fingerprint, max_side)}.jpg"

    def has(self, fingerprint: str, max_side: int = 2048) -> bool:
        path = self.get_path(fingerprint, max_side)
        try:
            return path.is_file() and path.stat().st_size > 0
        except OSError:
            return False

    def save_preview(
        self,
        fingerprint: str,
        img: Image.Image,
        max_side: int = 2048,
        quality: int = 85,
        icc_profile: bytes | None = None,
    ) -> Path:
        """Atomically write a preview image (temp + os.replace)."""
        self.ensure_dir()
        target = self.get_path(fingerprint, max_side)
        token = secrets.token_hex(8)
        temp_path = self.cache_dir / f".tmp_{token}.jpg"

        kwargs: dict = {"quality": quality}
        if icc_profile:
            kwargs["icc_profile"] = icc_profile

        # Ensure image is in RGB mode for JPEG encoding
        if img.mode != "RGB":
            if img.mode in ("RGBA", "LA", "PA"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                mask = img.getchannel("A") if "A" in img.getbands() else None
                background.paste(img, mask=mask)
                save_img = background
            else:
                save_img = img.convert("RGB")
        else:
            save_img = img

        try:
            save_img.save(temp_path, format="JPEG", **kwargs)
            os.replace(temp_path, target)
        except Exception:
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
            raise

        return target

    def cleanup(self) -> int:
        """Remove previews older than max_age or exceeding max_bytes (oldest first)."""
        if not self.cache_dir.is_dir():
            return 0

        now = time.time()
        deleted = 0
        entries: list[tuple[Path, int, float]] = []

        for p in self.cache_dir.iterdir():
            # Clean up abandoned temporary files older than 1 hour
            if p.name.startswith(".tmp_"):
                try:
                    if now - p.stat().st_mtime > 3600:
                        p.unlink()
                        deleted += 1
                except OSError:
                    pass
                continue

            if not (p.is_file() and p.suffix.lower() == ".jpg"):
                continue

            try:
                st = p.stat()
                # Check max age
                if self.max_age_seconds > 0 and (now - st.st_mtime) > self.max_age_seconds:
                    p.unlink()
                    deleted += 1
                    continue
                entries.append((p, st.st_size, st.st_mtime))
            except OSError:
                continue

        # Check total size
        total_size = sum(size for _, size, _ in entries)
        if total_size > self.max_bytes:
            # Sort by mtime ascending (oldest first)
            entries.sort(key=lambda x: x[2])
            target_size = int(self.max_bytes * 0.85)  # 15% hysteresis
            for p, size, _ in entries:
                try:
                    p.unlink()
                    deleted += 1
                    total_size -= size
                    if total_size <= target_size:
                        break
                except OSError:
                    continue

        return deleted

    def clear(self) -> int:
        """Remove all preview files in the cache directory."""
        if not self.cache_dir.is_dir():
            return 0
        deleted = 0
        for p in self.cache_dir.iterdir():
            if p.is_file() and (p.suffix.lower() == ".jpg" or p.name.startswith(".tmp_")):
                try:
                    p.unlink()
                    deleted += 1
                except OSError:
                    pass
        return deleted
