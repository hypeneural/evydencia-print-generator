"""Filesystem locations used at runtime (repo assets now; app-data/cache added in PR B)."""

from __future__ import annotations

import os
from pathlib import Path

_PACKAGE_DIR = Path(__file__).resolve().parent


def repo_root() -> Path:
    """Repository root in a source checkout (apps/desktop/src/<pkg> -> 4 levels up)."""
    return _PACKAGE_DIR.parents[3]


def schemas_dir() -> Path:
    override = os.environ.get("EVYDENCIA_SCHEMAS_DIR")
    return Path(override) if override else repo_root() / "schemas"


def templates_dir() -> Path:
    override = os.environ.get("EVYDENCIA_TEMPLATES_DIR")
    return Path(override) if override else repo_root() / "templates"
