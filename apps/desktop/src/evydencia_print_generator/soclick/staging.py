"""Copy only the finished verified JPEG into a fixed, approved intake area.

The operator may import photographs from any readable directory. The EvydFlow
HTTP API never needs broad permission to inspect that arbitrary directory.
No original photo, token or mutable edit-state is copied by this step.
"""
from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

from ..soclick.render_receipt import file_sha256

WINDOWS_STAGING_ROOT = Path(r"C:\Evydencia\print-generator-handoff")


class StagingError(OSError):
    """The safe handoff copy could not be prepared."""


def configured_staging_root() -> Path | None:
    configured = os.environ.get("EVYDENCIA_SOCLICK_HANDOFF_DIR", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    if os.name == "nt":
        return WINDOWS_STAGING_ROOT
    # Linux CI and local tests continue using their original file unless
    # the test explicitly opts into the Windows-style staging contract.
    return None


def stage_verified_jpeg(source: Path, expected_sha256: str) -> Path:
    """Make immutable-by-name intake copy; never change the rendered original.

    sha is checked both before and after copying; an existing collision is
    verified, never silently overwritten. Exactly the original JPEG bytes are
    used, so 300 DPI, profile, color and pixel dimensions cannot change.
    """
    src = source.resolve(strict=True)
    if src.suffix.lower() not in {".jpg", ".jpeg"} or not src.is_file():
        raise StagingError("O arquivo final não é um JPEG regular.")
    if file_sha256(src) != expected_sha256:
        raise StagingError("O arquivo final mudou depois da geração.")
    root = configured_staging_root()
    if root is None:
        return src
    try:
        # Keep the filename (preset/production label) and make the location
        # content-addressed. The source directory need not be allowlisted.
        target_dir = root / expected_sha256[:2] / expected_sha256
        target_dir.mkdir(parents=True, exist_ok=True)
        if root.is_symlink() or target_dir.resolve() != target_dir.absolute():
            raise StagingError("A área autorizada não pode redirecionar o JPEG.")
        dest = target_dir / src.name
        if dest.exists():
            if not dest.is_file() or file_sha256(dest) != expected_sha256:
                raise StagingError("Já existe um arquivo diferente no destino.")
            return dest
        fd, temp_name = tempfile.mkstemp(dir=target_dir, prefix=".handoff-", suffix=".tmp")
        temp = Path(temp_name)
        try:
            with os.fdopen(fd, "wb") as out, src.open("rb") as inp:
                shutil.copyfileobj(inp, out, length=1024 * 1024)
                out.flush()
                os.fsync(out.fileno())
            if file_sha256(temp) != expected_sha256:
                raise StagingError("Falha na verificação da cópia preparada.")
            # Guard against a destination created after the first check;
            # Windows uses a replace operation on the same local filesystem.
            if dest.exists():
                if file_sha256(dest) != expected_sha256:
                    raise StagingError("Conflito na área de preparação.")
            else:
                os.replace(temp, dest)
        finally:
            temp.unlink(missing_ok=True)
        return dest
    except StagingError:
        raise
    except OSError as exc:
        raise StagingError("Não foi possível copiar o JPEG para a área autorizada.") from exc
