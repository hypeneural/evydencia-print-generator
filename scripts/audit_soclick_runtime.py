"""Read-only, non-PII local diagnostics for the EvydFlow / SóClick interface.

Never POST, start/stop processes, mutate SQLite, send prints or expose credentials.
Works on Python 3.12+ and Windows 11 Home with stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import time
import urllib.error
import urllib.request
from pathlib import Path

_REQUIRED = {
    "jobs": {"job_id", "state", "reference", "manifest_sha256", "draft_version"},
    "job_manifests": {"job_id", "manifest_sha256", "manifest_version", "state"},
    "print_items": {"item_id", "job_id", "copies", "file_sha256", "source_path"},
    "source_files": {"source_id", "job_id", "source_path", "file_sha256"},
    "job_events": {"seq", "job_id", "event_type", "created_at"},
    "job_status_watches": {"job_id", "order_id", "state", "next_check_at"},
    "remote_snapshots": {"job_id", "snapshot_id", "provenance"},
    "remote_snapshot_photos": {"snapshot_id", "remote_filename_key"},
    "upload_attempts": {"attempt_id", "item_id", "job_id"},
    "schema_migrations": {"version", "applied_at"},
}


def _get_json(url: str, timeout: float = 2.0) -> dict | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Evydencia-Local-Audit/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status != 200:
                return None
            payload = response.read(16384)
        result = json.loads(payload)
        return result if isinstance(result, dict) else None
    except (OSError, ValueError, TypeError, urllib.error.URLError):
        return None


def probe_api(port: int) -> dict:
    """GET-only checks; not evidence that the worker or laboratory is healthy."""
    base = f"http://127.0.0.1:{port}"
    health = _get_json(base + "/health")
    env = _get_json(base + "/api/soclick/environment")
    valid = bool(
        health is not None and health.get("ok") is True
        and env is not None
        and env.get("environment") in {"OPERACIONAL", "HOMOLOGACAO", "OFFLINE_TEST"}
        and isinstance(env.get("enviar_blocked"), bool)
        and isinstance(env.get("real_production_allowed"), bool)
    )
    return {
        "http_api_contract": "PASS" if valid else "FAIL",
        "api_health_only": bool(health and health.get("ok") is True),
        "environment": env.get("environment") if valid else None,
        "physical_send_allowed_by_env": env.get("real_production_allowed") if valid else None,
        "worker_status": "NOT_VERIFIED",
        "laboratory_delivery": "NOT_VERIFIED",
    }


def inspect_sqlite(path: Path) -> dict:
    """Read-only SQLite schema validation; no customer rows are selected or printed."""
    report: dict = {"sqlite_schema": "FAIL", "schema_version": None, "missing": {}}
    if not path.is_file():
        report["error_type"] = "DATABASE_NOT_FOUND"
        return report
    try:
        uri = path.resolve().as_uri() + "?mode=ro"
        con = sqlite3.connect(uri, uri=True, timeout=2)
        try:
            con.execute("PRAGMA query_only=ON")
            names = {
                row[0] for row in con.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            for table, required_cols in _REQUIRED.items():
                if table not in names:
                    report["missing"][table] = "TABLE"
                    continue
                # Table identifiers are static constants defined in this module.
                present = {row[1] for row in con.execute(f"PRAGMA table_info({table})")}
                absent = sorted(required_cols - present)
                if absent:
                    report["missing"][table] = absent
            if "schema_migrations" in names:
                report["schema_version"] = con.execute(
                    "SELECT MAX(version) FROM schema_migrations"
                ).fetchone()[0]
            report["sqlite_schema"] = "PASS" if not report["missing"] else "FAIL"
        finally:
            con.close()
    except (sqlite3.Error, OSError, ValueError) as exc:
        report["error_type"] = type(exc).__name__
    return report


def inspect_worker_pulse(repo_root: Path) -> dict:
    """A timestamp is informational only; PID ownership is not proven here."""
    file = repo_root / ".agent-runtime" / "worker_pulse.json"
    try:
        pulse = json.loads(file.read_text(encoding="utf-8"))
        age = time.time() - float(pulse["updated_at"])
        pid = int(pulse["pid"])
        fresh = pid > 0 and -2 <= age <= 30
    except (OSError, ValueError, TypeError, KeyError, OverflowError):
        fresh = False
    return {"recent_worker_pulse": fresh, "worker_identity_verified": False}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8095)
    parser.add_argument("--evydflow-root", type=Path)
    parser.add_argument("--soclick-db", type=Path)
    args = parser.parse_args(argv)
    if not 1024 <= args.port <= 65535:
        parser.error("a porta deve estar entre 1024 e 65535")
    report: dict = {"contract": "evydencia-soclick-local-audit-v1"}
    report["api"] = probe_api(args.port)
    if args.evydflow_root:
        report["worker"] = inspect_worker_pulse(args.evydflow_root)
    if args.soclick_db:
        report["db"] = inspect_sqlite(args.soclick_db)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    # This is observational: nonzero indicates an invalid selected API/schema.
    bad_db = "db" in report and report["db"]["sqlite_schema"] != "PASS"
    return 2 if bad_db or report["api"]["http_api_contract"] != "PASS" else 0


if __name__ == "__main__":
    raise SystemExit(main())
