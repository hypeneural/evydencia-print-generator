"""Bind a rendered JPEG to the exact immutable editor inputs of that render.

Session-local safety receipt. No photo paths, customer details or secrets are
written to disk; a new application session must render again until durable
recovery is separately designed and verified.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from ..domain.job import EditState, JobSnapshot


class RenderReceiptError(ValueError):
    """The requested handoff does not match a verified local render."""


def file_sha256(path: Path) -> str:
    """Hash in bounded memory; never rely on timestamps alone."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class RenderReceipt:
    """One immutable render intent tied to its output bytes and source snapshot."""

    output_path: Path
    edit_state: EditState
    snapshot: JobSnapshot
    sha256: str

    @classmethod
    def capture(
        cls, output_path: Path, edit_state: EditState, snapshot: JobSnapshot
    ) -> RenderReceipt:
        resolved = output_path.resolve(strict=True)
        if not resolved.is_file():
            raise RenderReceiptError("O arquivo gerado não é um arquivo regular.")
        return cls(resolved, edit_state, snapshot, file_sha256(resolved))

    def verify(self, output_path: str, edit_state: EditState) -> JobSnapshot:
        """Fail closed on a different render, changed edits or modified output."""
        requested = Path(output_path).resolve()
        if requested != self.output_path:
            raise RenderReceiptError(
                "Este arquivo não corresponde à última geração desta sessão. "
                "Gere novamente antes de preparar na SóClick."
            )
        if edit_state != self.edit_state:
            raise RenderReceiptError(
                "O enquadramento ou as fotos foram alterados depois da geração. "
                "Gere novamente para preparar exatamente o que está na tela."
            )
        if not self.output_path.is_file():
            raise RenderReceiptError("O JPEG gerado foi removido. Gere novamente.")
        if file_sha256(self.output_path) != self.sha256:
            raise RenderReceiptError(
                "O JPEG foi modificado depois da geração. "
                "Preparação bloqueada para evitar envio incorreto."
            )
        return self.snapshot
