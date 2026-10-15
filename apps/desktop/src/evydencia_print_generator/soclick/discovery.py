"""Detecção dinâmica da porta real do painel EvydFlow sem valores fixos."""
from __future__ import annotations

import json
import logging
import os
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

logger = logging.getLogger(__name__)

DEFAULT_PROBE_PORTS = (8095, 8090)


def _is_port_healthy(port: int, timeout_sec: float = 0.8) -> bool:
    """Require the EvydFlow SóClick contract; a generic /health is insufficient.

    Read-only loopback probes. In particular, a foreign service answering /health
    on 8090 must never receive the local customer's production image paths.
    """
    if not isinstance(port, int) or not 1024 <= port <= 65535:
        return False
    base = f"http://127.0.0.1:{port}"
    try:
        health_req = urllib.request.Request(
            f"{base}/health", headers={"User-Agent": "PrintGenerator-Probe"}
        )
        with urllib.request.urlopen(health_req, timeout=timeout_sec) as resp:
            if resp.status != 200 or json.load(resp).get("ok") is not True:
                return False
        env_req = urllib.request.Request(
            f"{base}/api/soclick/environment",
            headers={"User-Agent": "PrintGenerator-Probe"},
        )
        with urllib.request.urlopen(env_req, timeout=timeout_sec) as resp:
            if resp.status != 200:
                return False
            data = json.load(resp)
        return (
            isinstance(data, dict)
            and data.get("environment") in {"OPERACIONAL", "HOMOLOGACAO", "OFFLINE_TEST"}
            and isinstance(data.get("enviar_blocked"), bool)
            and isinstance(data.get("real_production_allowed"), bool)
        )
    except (OSError, ValueError, TypeError, KeyError):
        return False

def discover_panel_port(preferred_port: int | None = None, timeout_sec: float = 0.8) -> int | None:
    """Descobre a porta em que o painel EvydFlow está rodando ativamente.

    Prioridade:
    1. preferred_port explícito se informado e saudável.
    2. Variável de ambiente EVYDFLOW_PANEL_URL ou EVYDFLOW_PANEL_PORT.
    3. Arquivo de configuração de runtime em C:\\Evydencia\\data.
    4. Sondagem ativa nas portas candidatas (8095, 8090).
    """
    if preferred_port and _is_port_healthy(preferred_port, timeout_sec):
        return preferred_port

    # 1. Variáveis de ambiente
    env_url = os.environ.get("EVYDFLOW_PANEL_URL", "").strip()
    if env_url:
        try:
            parsed = urlsplit(env_url)
            if (parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost"}
                    and not parsed.username and not parsed.password and parsed.port
                    and _is_port_healthy(parsed.port, timeout_sec)):
                return parsed.port
        except Exception:
            pass

    env_port = os.environ.get("EVYDFLOW_PANEL_PORT", "").strip()
    if env_port.isdigit():
        p = int(env_port)
        if _is_port_healthy(p, timeout_sec):
            return p

    # 2. Arquivos de runtime
    for cand_file in (
        Path(r"C:\Evydencia\data\panel_server.json"),
        Path(r"C:\Evydencia\data\panel_port.json"),
    ):
        if cand_file.is_file():
            try:
                data = json.loads(cand_file.read_text(encoding="utf-8"))
                p = int(data.get("port", 0))
                if p > 0 and _is_port_healthy(p, timeout_sec):
                    return p
            except Exception:
                pass

    # 3. Sondagem ativa
    for cand_port in DEFAULT_PROBE_PORTS:
        if _is_port_healthy(cand_port, timeout_sec):
            logger.info("EvydFlow panel discovered on port %d", cand_port)
            return cand_port

    logger.warning(
        "EvydFlow panel is not running or unreachable on probe ports %s", DEFAULT_PROBE_PORTS
    )
    return None
