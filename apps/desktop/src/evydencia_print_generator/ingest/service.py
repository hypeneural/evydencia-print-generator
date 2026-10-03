"""IngestService: the single entry point for CLI/context menu, file dialog and drop."""

from __future__ import annotations

import logging
import os
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Literal

from .models import IngestResult, RejectCode, RejectedInput, SourceAsset, SourceIdentity
from .registry import SourceRegistry
from .validator import ProbeError, probe_image

logger = logging.getLogger(__name__)

Origin = Literal["cli", "dialog", "drop"]
PreviewScheduler = Callable[[SourceAsset], None]
_ORIGINS = frozenset({"cli", "dialog", "drop"})


def _display_name(raw: str | os.PathLike[str]) -> str:
    text = os.fspath(raw)
    name = Path(text).name if text else ""
    return name or "<sem nome>"


class IngestService:
    def __init__(
        self, registry: SourceRegistry, schedule_preview: PreviewScheduler | None = None
    ) -> None:
        self.registry = registry
        self._schedule_preview = schedule_preview

    def ingest_paths(
        self, paths: Iterable[str | os.PathLike[str]], origin: Origin = "cli"
    ) -> IngestResult:
        if origin not in _ORIGINS:
            raise ValueError(f"unknown ingest origin {origin!r}")
        result = IngestResult()
        for raw in paths:
            self._ingest_one(raw, result)
        logger.info(
            "ingest origin=%s added=%d existing=%d refreshed=%d rejected=%d",
            origin,
            len(result.added),
            len(result.existing),
            len(result.refreshed),
            len(result.rejected),
        )
        return result

    def _reject(self, result: IngestResult, name: str, code: RejectCode, detail: str = "") -> None:
        result.rejected.append(RejectedInput(display_name=name, code=code, detail=detail))

    def _ingest_one(self, raw: str | os.PathLike[str], result: IngestResult) -> None:
        name = _display_name(raw)
        text = os.fspath(raw)
        if not text.strip():
            self._reject(result, name, RejectCode.NOT_FOUND)
            return
        try:
            resolved = Path(text).expanduser().resolve(strict=True)
        except FileNotFoundError:
            self._reject(result, name, RejectCode.NOT_FOUND)
            return
        except (OSError, RuntimeError) as exc:
            self._reject(result, name, RejectCode.UNREADABLE, type(exc).__name__)
            return
        if not resolved.is_file():
            self._reject(result, name, RejectCode.NOT_A_FILE)
            return
        try:
            stat = resolved.stat()
        except OSError as exc:
            self._reject(result, name, RejectCode.UNREADABLE, type(exc).__name__)
            return

        identity = SourceIdentity(
            norm_path=os.path.normcase(str(resolved)),
            size_bytes=stat.st_size,
            mtime_ns=stat.st_mtime_ns,
        )
        known = self.registry.find(identity)
        if known is not None:  # fast path: no re-probe, no new preview
            self._accept(result, known, "existing")
            return

        try:
            probe = probe_image(resolved)
        except ProbeError as exc:
            self._reject(result, name, exc.code, exc.detail)
            return

        asset, status = self.registry.upsert(identity, resolved, resolved.name, probe)
        self._accept(result, asset, status)
        if status != "existing" and self._schedule_preview is not None:
            self._schedule_preview(asset)

    @staticmethod
    def _accept(result: IngestResult, asset: SourceAsset, status: str) -> None:
        if asset.id in result.accepted_ids:
            return  # same source repeated within one batch
        result.accepted_ids.append(asset.id)
        {"added": result.added, "existing": result.existing, "refreshed": result.refreshed}[
            status
        ].append(asset)
