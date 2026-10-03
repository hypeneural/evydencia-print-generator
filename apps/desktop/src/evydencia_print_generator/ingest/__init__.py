"""Local photo ingest: one service for CLI/context menu, file dialog and drag-and-drop."""

from .cache import PreviewCache
from .models import (
    ImageProbe,
    IngestResult,
    PreviewInfo,
    PreviewStatus,
    RejectCode,
    RejectedInput,
    SourceAsset,
    SourceIdentity,
)
from .preview import PreviewService
from .registry import SourceRegistry
from .service import IngestService

__all__ = [
    "ImageProbe",
    "IngestResult",
    "IngestService",
    "PreviewCache",
    "PreviewInfo",
    "PreviewService",
    "PreviewStatus",
    "RejectCode",
    "RejectedInput",
    "SourceAsset",
    "SourceIdentity",
    "SourceRegistry",
]
