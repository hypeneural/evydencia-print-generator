"""Cliente local do contrato de handoff para a API do EvydFlow / SóClick."""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import parse_qs, urlsplit

from .discovery import discover_panel_port

if TYPE_CHECKING:
    from ..domain.job import JobSnapshot

logger = logging.getLogger(__name__)


class SoclicHandoffError(Exception):
    """Safe error code and human-readable context for a failed draft handoff."""

    def __init__(self, message: str, error_code: str = "SOCLICK_FAILED") -> None:
        super().__init__(message)
        self.error_code = error_code


class PanelUnavailableError(SoclicHandoffError):
    """The local EvydFlow panel could not be reached."""

    def __init__(self, message: str) -> None:
        super().__init__(message, error_code="PANEL_OFFLINE")


def _compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def _get_operator_token() -> str:
    """Recupera token do operador caso configurado em C:\\Evydencia\\secrets\\operator-api.env."""
    env_token = os.environ.get("EVYDFLOW_OPERATOR_API_TOKEN", "").strip()
    if env_token:
        return env_token
    sec_file = Path(r"C:\Evydencia\secrets\operator-api.env")
    if sec_file.is_file():
        try:
            for line in sec_file.read_text(encoding="utf-8-sig").splitlines():
                line = line.strip()
                if line.startswith("EVYDFLOW_OPERATOR_API_TOKEN="):
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if val:
                        return val
        except Exception:
            pass
    return ""


def prepare_soclic_draft(
    output_path_str: str,
    snapshot: JobSnapshot,
    panel_port: int | None = None,
    open_browser: bool = True,
    expected_sha256: str | None = None,
) -> dict[str, Any]:
    """Constrói contrato de handoff, envia para a API local do EvydFlow e abre conferência.

    Garantias:
    1. Nunca expõe tokens nem caminhos de arquivos ao navegador.
    2. Descobre a porta real sem valores hardcoded.
    3. Falha graciosamente se o painel estiver offline.
    4. Abre o modal de conferência diretamente através de #review no navegador padrão.
    """
    out_file = Path(output_path_str).resolve()
    if not out_file.is_file():
        raise SoclicHandoffError(f"Arquivo gerado não existe no disco: '{output_path_str}'")

    port = discover_panel_port(preferred_port=panel_port)
    if not port:
        raise PanelUnavailableError(
            "Painel EvydFlow não está em execução na porta local. "
            "Inicie o EvydFlow para preparar na SóClick."
        )

    file_sha = _compute_sha256(out_file)
    if expected_sha256 is not None and file_sha != expected_sha256:
        raise SoclicHandoffError(
            "O JPEG foi alterado entre a geração e a preparação. Envio bloqueado."
        )

    # Mapeamento restrito aos slots efetivamente renderizados
    slots_map: dict[str, Any] = {}
    for slot_id, edit in snapshot.slot_edits.items():
        src = snapshot.sources.get(edit.source_id)
        if src:
            slots_map[slot_id] = {
                "source_id": edit.source_id,
                "original_path": str(src.path),
                "size_bytes": src.size_bytes,
                "mtime_ns": src.mtime_ns,
            }

    payload = {
        "contract_version": "1.0",
        "idempotency_key": f"{snapshot.template_id}:{file_sha[:16]}",
        "template_id": snapshot.template_id,
        "template_version": snapshot.template_version,
        "output_path": str(out_file),
        "file_sha256": file_sha,
        "bytes_written": out_file.stat().st_size,
        "slots": slots_map,
    }

    url = f"http://127.0.0.1:{port}/api/soclick/intake/print-generator"
    req_data = json.dumps(payload).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "EvydenciaPrintGenerator/1.0",
    }
    token = _get_operator_token()
    if token:
        headers["x-evydflow-operator-token"] = token

    req = urllib.request.Request(url, data=req_data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            resp_body = resp.read().decode("utf-8")
            data = json.loads(resp_body)
    except urllib.error.HTTPError as err:
        # Do not propagate arbitrary provider messages or local source paths
        # into the operator UI. Keep the original response in the Python logger.
        detail = ""
        try:
            payload_error = json.loads(err.read().decode("utf-8"))
            if isinstance(payload_error, dict) and isinstance(payload_error.get("detail"), str):
                detail = payload_error["detail"]
        except (ValueError, OSError):
            pass
        logger.warning("SóClick intake HTTP %s (operator detail withheld)", err.code)
        if err.code == 503 and "EVYDFLOW_ALLOWED_ROOTS" in detail:
            raise SoclicHandoffError(
                "A pasta de fotografias ainda não foi autorizada no EvydFlow.",
                error_code="ROOTS_NOT_CONFIGURED",
            ) from err
        if err.code in (401, 403):
            raise SoclicHandoffError(
                "O EvydFlow não autorizou a preparação do rascunho.",
                error_code="OPERATOR_NOT_AUTHORIZED",
            ) from err
        if err.code in (408, 429, 500, 502, 503, 504):
            raise SoclicHandoffError(
                "Não foi possível confirmar o resultado da preparação no EvydFlow.",
                error_code="HANDOFF_UNCERTAIN",
            ) from err
        raise SoclicHandoffError(
            "O EvydFlow recusou os dados enviados para criar o rascunho.",
            error_code="HANDOFF_REJECTED",
        ) from err
    except urllib.error.URLError as err:
        # Refused connection proves no listener accepted it. A reset, timeout,
        # broken pipe or unrecognized transport failure MAY happen after the
        # server commits DRAFT. Never recommend a blind retry for those cases.
        if isinstance(err.reason, ConnectionRefusedError):
            raise PanelUnavailableError(
                "O painel EvydFlow não está disponível neste computador."
            ) from err
        raise SoclicHandoffError(
            "A conexão foi interrompida; o rascunho pode ter sido criado.",
            error_code="HANDOFF_UNCERTAIN",
        ) from err
    except OSError as err:
        # Includes TimeoutError and a connection dropping after the request
        # was sent. The server may still have committed the draft.
        raise SoclicHandoffError(
            "A conexão caiu durante a preparação; o rascunho pode ter sido criado.",
            error_code="HANDOFF_UNCERTAIN",
        ) from err
    except (ValueError, TypeError) as err:
        raise SoclicHandoffError(
            "O EvydFlow retornou uma resposta incompleta. Confira o painel.",
            error_code="HANDOFF_UNCERTAIN",
        ) from err

    if not isinstance(data, dict):
        raise SoclicHandoffError(
            "O EvydFlow retornou uma resposta incompleta. Confira o painel.",
            error_code="HANDOFF_UNCERTAIN",
        )
    job_id = data.get("job_id")
    panel_url = data.get("panel_url")
    if data.get("ok") is not True or not isinstance(
        job_id, str
    ) or not re.fullmatch(r"job_[A-Za-z0-9_-]{1,100}", job_id):
        raise SoclicHandoffError(
            "O EvydFlow retornou uma resposta incompleta. Confira o painel.",
            error_code="HANDOFF_UNCERTAIN",
        )
    if not isinstance(panel_url, str):
        raise SoclicHandoffError(
            "O EvydFlow não informou a página de conferência.",
            error_code="HANDOFF_UNCERTAIN",
        )
    parsed = urlsplit(panel_url)
    query = parse_qs(parsed.query)
    if (
        parsed.scheme != "http"
        or parsed.hostname != "127.0.0.1"
        or parsed.port != port
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path != "/panel/soclick"
        or query.get("focus") != [job_id]
        or parsed.fragment != "review"
    ):
        raise SoclicHandoffError(
            "A página devolvida pelo EvydFlow não corresponde ao rascunho criado.",
            error_code="HANDOFF_UNCERTAIN",
        )

    browser_opened = False
    if open_browser:
        try:
            browser_opened = bool(webbrowser.open(panel_url))
        except Exception as exc:
            logger.warning("Falha ao abrir navegador padrão: %s", type(exc).__name__)

    return {
        "ok": True,
        "job_id": job_id,
        "observation": data.get("observation", ""),
        "panel_url": panel_url,
        "browser_opened": browser_opened,
        "is_existing": data.get("is_existing", False),
        "total_orders": data.get("total_orders", 0),
    }
