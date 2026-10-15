"""Read-only, privacy-safe runtime check for the ACTUAL Windows venv.

Use `.venv\\Scripts\\python.exe scripts/audit_win11_print_generator_runtime.py`.
No network, filesystem writes, service restarts or credential disclosures.
"""
from __future__ import annotations

import importlib.metadata
import json
import re
import sys
import tomllib
from pathlib import Path


def _tuple_version(value: str) -> tuple[int, ...] | None:
    """Simple stable numeric comparison; pre-releases are intentionally not certified."""
    if not re.fullmatch(r"\d+(?:\.\d+)*", value):
        return None
    return tuple(int(x) for x in value.split("."))


def matches_numeric_spec(version: str, spec: str) -> bool:
    """Check project numeric bounds without an additional runtime dependency."""
    current = _tuple_version(version)
    if current is None:
        return False
    if not spec:
        return True
    for segment in spec.split(","):
        segment = segment.strip()
        match = re.fullmatch(r"(>=|<=|==|!=|>|<)(\d+(?:\.\d+)*)", segment)
        if not match:
            return False
        operator, target_version = match.groups()
        required = _tuple_version(target_version)
        assert required is not None
        size = max(len(current), len(required))
        lhs = current + (0,) * (size - len(current))
        rhs = required + (0,) * (size - len(required))
        if not {
            ">=": lhs >= rhs, "<=": lhs <= rhs, "==": lhs == rhs,
            "!=": lhs != rhs, ">": lhs > rhs, "<": lhs < rhs,
        }[operator]:
            return False
    return True


def required_version_spec(requirements: list[str], package: str) -> str:
    for item in requirements:
        body = item.split(";", 1)[0].strip()
        m = re.fullmatch(
            rf"{re.escape(package)}\s*((?:(?:>=|<=|==|!=|>|<)\d+(?:\.\d+)*(?:,\s*)?)+)",
            body, flags=re.IGNORECASE,
        )
        if m:
            return m.group(1).rstrip(",").replace(" ", "")
    return ""


def check_runtime(config_path: Path) -> dict[str, object]:
    project = tomllib.loads(config_path.read_text(encoding="utf-8"))["project"]
    python_spec = project.get("requires-python", "")
    version = ".".join(str(n) for n in sys.version_info[:3])
    checks: list[dict[str, object]] = [
        {
            "component": "Python",
            "installed": version,
            "required": python_spec,
            "ok": matches_numeric_spec(version, python_spec),
        },
    ]
    for package in ("Pillow", "pywebview"):
        if package == "pywebview" and sys.platform != "win32":
            continue
        required = required_version_spec(project["dependencies"], package)
        try:
            installed = importlib.metadata.version(package)
            ok = bool(required) and matches_numeric_spec(installed, required)
        except importlib.metadata.PackageNotFoundError:
            installed = "not installed"
            ok = False
        checks.append({
            "component": package, "installed": installed, "required": required, "ok": ok,
        })
    return {
        "contract": "evydencia-print-generator-runtime-v1",
        "platform": "windows" if sys.platform == "win32" else "other",
        "checks": checks,
        "ready": all(c["ok"] for c in checks),
        "note": "This checks local packages, NOT the actual EvydFlow worker or SóClick provider.",
    }


def main() -> int:
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    report = check_runtime(pyproject)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
