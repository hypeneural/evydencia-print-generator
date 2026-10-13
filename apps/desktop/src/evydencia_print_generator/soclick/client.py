"""Cliente local do contrato de handoff para a API do EvydFlow / SóClick."""
from __future__ import annotations

import hashlib
import json
import logging
import os
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .discovery import discover_panel_port

if TYPE_CHECKING:
    from ..domain.job import JobSnapshot

logger = logging.getLogger(__name__)


class SoclicHandoffError(Exception):
    """Erro geral durante o handoff para a SóClick."""


class PanelUnavailableError(SoclicHandoffError):
    """Painel do EvydFlow está offline ou inacessível no host local."""


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
        err_msg = err.reason
        try:
            err_json = json.loads(err.read().decode("utf-8"))
            err_msg = err_json.get("detail", err_msg)
        except Exception:
            pass
        raise SoclicHandoffError(f"Falha na SóClick ({err.code}): {err_msg}") from err
    except urllib.error.URLError as err:
        raise PanelUnavailableError(
            f"Não foi possível conectar ao EvydFlow na porta {port}: {err.reason}"
        ) from err
    except Exception as exc:
        raise SoclicHandoffError(f"Erro inesperado no envio para a SóClick: {exc}") from exc

    panel_url = data.get("panel_url", "")
    if open_browser and panel_url:
        try:
            webbrowser.open(panel_url)
        except Exception as exc:
            logger.warning("Falha ao abrir navegador padrão: %s", exc)

    return {
        "ok": True,
        "job_id": data.get("job_id", ""),
        "observation": data.get("observation", ""),
        "panel_url": panel_url,
        "is_existing": data.get("is_existing", False),
        "total_orders": data.get("total_orders", 0),
    }
