"""Ingest data model. Original paths live only in runtime objects, never in UI payloads."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


class PreviewStatus(StrEnum):
    PENDING = "pending"  # registered, not yet scheduled
    QUEUED = "queued"
    LOADING = "loading"
    READY = "ready"
    ERROR = "error"


class RejectCode(StrEnum):
    NOT_FOUND = "not_found"
    NOT_A_FILE = "not_a_file"
    UNREADABLE = "unreadable"
    UNSUPPORTED_FORMAT = "unsupported_format"
    UNSUPPORTED_COLOR_MODE = "unsupported_color_mode"
    CORRUPT = "corrupt"
    TOO_LARGE = "too_large"


@dataclass(frozen=True)
class SourceIdentity:
    """V1 identity: normalized path + size + mtime_ns (no full-file hash)."""

    norm_path: str
    size_bytes: int
    mtime_ns: int

    @property
    def fingerprint(self) -> str:
        raw = f"{self.norm_path}\0{self.size_bytes}\0{self.mtime_ns}".encode()
        return hashlib.sha256(raw).hexdigest()[:32]


@dataclass(frozen=True)
class ImageProbe:
    format: str  # detected from content, not extension
    mode: str
    width_px: int  # after EXIF orientation
    height_px: int
    stored_width_px: int  # as encoded in the file
    stored_height_px: int
    exif_orientation: int
    has_icc: bool
    icc_description: str | None


@dataclass
class PreviewInfo:
    status: PreviewStatus = PreviewStatus.PENDING
    fingerprint: str | None = None
    error_code: str | None = None


@dataclass
class SourceAsset:
    id: str
    identity: SourceIdentity
    path: Path = field(repr=False)  # runtime only; never logged nor sent to JS
    display_name: str
    probe: ImageProbe
    preview: PreviewInfo = field(default_factory=PreviewInfo)

    @property
    def width_px(self) -> int:
        return self.probe.width_px

    @property
    def height_px(self) -> int:
        return self.probe.height_px

    def to_ui_dict(self) -> dict[str, Any]:
        """Payload safe for the WebView: no filesystem path."""
        return {
            "id": self.id,
            "display_name": self.display_name,
            "format": self.probe.format,
            "width_px": self.probe.width_px,
            "height_px": self.probe.height_px,
            "has_icc": self.probe.has_icc,
            "preview_status": str(self.preview.status),
            "preview_error": self.preview.error_code,
        }


@dataclass(frozen=True)
class RejectedInput:
    display_name: str
    code: RejectCode
    detail: str = ""

    def to_ui_dict(self) -> dict[str, Any]:
        return {"display_name": self.display_name, "code": str(self.code)}


@dataclass
class IngestResult:
    added: list[SourceAsset] = field(default_factory=list)
    existing: list[SourceAsset] = field(default_factory=list)
    refreshed: list[SourceAsset] = field(default_factory=list)
    rejected: list[RejectedInput] = field(default_factory=list)
    accepted_ids: list[str] = field(default_factory=list)  # input order, de-duplicated

    @property
    def accepted(self) -> list[SourceAsset]:
        by_id = {a.id: a for a in (*self.added, *self.existing, *self.refreshed)}
        return [by_id[i] for i in self.accepted_ids]

    def to_ui_dict(self) -> dict[str, Any]:
        return {
            "accepted": [a.to_ui_dict() for a in self.accepted],
            "added_ids": [a.id for a in self.added],
            "refreshed_ids": [a.id for a in self.refreshed],
            "rejected": [r.to_ui_dict() for r in self.rejected],
        }
