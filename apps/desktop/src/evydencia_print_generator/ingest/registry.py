"""Thread-safe registry of SourceAssets with dedupe by identity."""

from __future__ import annotations

import hashlib
import threading
from dataclasses import replace
from pathlib import Path
from typing import Literal

from .models import ImageProbe, PreviewInfo, PreviewStatus, SourceAsset, SourceIdentity

UpsertStatus = Literal["added", "existing", "refreshed"]


class SourceRegistry:
    """Logical source ID is stable per normalized path within a session.

    The identity fingerprint (path + size + mtime_ns) changes when the file changes and is the
    preview cache key, so slots keep their source_id while the preview is regenerated.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._by_id: dict[str, SourceAsset] = {}

    @staticmethod
    def source_id_for(norm_path: str) -> str:
        return "src_" + hashlib.sha256(norm_path.encode("utf-8")).hexdigest()[:16]

    def find(self, identity: SourceIdentity) -> SourceAsset | None:
        with self._lock:
            asset = self._by_id.get(self.source_id_for(identity.norm_path))
            return asset if asset is not None and asset.identity == identity else None

    def upsert(
        self, identity: SourceIdentity, path: Path, display_name: str, probe: ImageProbe
    ) -> tuple[SourceAsset, UpsertStatus]:
        source_id = self.source_id_for(identity.norm_path)
        with self._lock:
            current = self._by_id.get(source_id)
            if current is not None and current.identity == identity:
                return current, "existing"
            asset = SourceAsset(
                id=source_id,
                identity=identity,
                path=path,
                display_name=display_name,
                probe=probe,
                preview=PreviewInfo(fingerprint=identity.fingerprint),
            )
            self._by_id[source_id] = asset
            return asset, ("refreshed" if current is not None else "added")

    def get(self, source_id: str) -> SourceAsset | None:
        with self._lock:
            return self._by_id.get(source_id)

    def list(self) -> list[SourceAsset]:
        with self._lock:
            return list(self._by_id.values())  # insertion order

    def remove(self, source_id: str) -> bool:
        with self._lock:
            return self._by_id.pop(source_id, None) is not None

    def update_preview(
        self,
        source_id: str,
        fingerprint: str,
        status: PreviewStatus,
        error_code: str | None = None,
    ) -> SourceAsset | None:
        """Update preview state; ignored if the asset changed meanwhile (stale fingerprint)."""
        with self._lock:
            asset = self._by_id.get(source_id)
            if asset is None or asset.identity.fingerprint != fingerprint:
                return None
            asset.preview = replace(
                asset.preview, status=status, fingerprint=fingerprint, error_code=error_code
            )
            return asset

    def __len__(self) -> int:
        with self._lock:
            return len(self._by_id)

    def __contains__(self, source_id: object) -> bool:
        with self._lock:
            return source_id in self._by_id
