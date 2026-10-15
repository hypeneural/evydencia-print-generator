"""Offline checks for the read-only operator diagnostic."""
from __future__ import annotations

import importlib.util
import json
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _diagnostic_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "audit_soclick_runtime.py"
    spec = importlib.util.spec_from_file_location("audit_soclick_runtime", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_offline_api_never_claims_worker_or_delivery() -> None:
    audit = _diagnostic_module()
    with patch.object(audit, "_get_json", return_value=None):
        result = audit.probe_api(8095)
    assert result["http_api_contract"] == "FAIL"
    assert result["worker_status"] == "NOT_VERIFIED"
    assert result["laboratory_delivery"] == "NOT_VERIFIED"


def test_api_contract_requires_typed_soclick_environment() -> None:
    audit = _diagnostic_module()
    with patch.object(audit, "_get_json", side_effect=[
        {"ok": True},
        {"environment": "OPERACIONAL", "enviar_blocked": True,
         "real_production_allowed": False},
    ]) as get:
        result = audit.probe_api(8095)
    assert result["http_api_contract"] == "PASS"
    assert result["physical_send_allowed_by_env"] is False
    assert get.call_count == 2
    assert get.call_args_list[0].args[0].endswith("/health")
    assert get.call_args_list[1].args[0].endswith("/api/soclick/environment")


def test_sqlite_schema_audit_is_read_only_and_never_reads_customer_rows(tmp_path: Path) -> None:
    audit = _diagnostic_module()
    db = tmp_path / "soclick.db"
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE jobs(job_id TEXT)")
        conn.execute("INSERT INTO jobs(job_id) VALUES ('private-id-do-not-expose')")
    result = audit.inspect_sqlite(db)
    assert result["sqlite_schema"] == "FAIL"
    assert result["missing"]["job_manifests"] == "TABLE"
    assert "private-id" not in json.dumps(result)
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == 1


def test_missing_worker_pulse_cannot_be_reported_live(tmp_path: Path) -> None:
    audit = _diagnostic_module()
    result = audit.inspect_worker_pulse(tmp_path)
    assert result == {"recent_worker_pulse": False, "worker_identity_verified": False}


def test_get_json_uses_read_only_get() -> None:
    audit = _diagnostic_module()
    response = MagicMock()
    response.status = 200
    response.read.return_value = b'{"ok":true}'
    response.__enter__.return_value = response
    with patch("urllib.request.urlopen", return_value=response) as urlopen:
        assert audit._get_json("http://127.0.0.1:8095/health") == {"ok": True}
    req = urlopen.call_args.args[0]
    assert req.get_method() == "GET"


def test_cli_rejects_invalid_port_without_http(capsys: pytest.CaptureFixture[str]) -> None:
    audit = _diagnostic_module()
    with pytest.raises(SystemExit) as exc:
        audit.main(["--port", "99999"])
    assert exc.value.code == 2
