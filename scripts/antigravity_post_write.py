#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

WATCH_NAMES = {"AGENTS.md", "GEMINI.md"}


def target_from_payload(payload: dict) -> str:
    args = payload.get("toolCall", {}).get("args", {})
    for key in ("TargetFile", "AbsolutePath"):
        value = args.get(key)
        if isinstance(value, str):
            return value
    return ""


def is_customization(path_text: str) -> bool:
    if not path_text:
        return False
    normalized = path_text.replace("\\", "/")
    path = Path(normalized)
    return "/.agents/" in f"/{normalized}/" or path.name in WATCH_NAMES


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        print("{}")
        return 0

    if not is_customization(target_from_payload(payload)):
        print("{}")
        return 0

    result = subprocess.run(
        [sys.executable, "scripts/verify_antigravity_customizations.py"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        print((result.stdout + "\n" + result.stderr).strip(), file=sys.stderr)

    print("{}")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
