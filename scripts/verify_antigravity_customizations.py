#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = ROOT / ".agents"
VALID_TRIGGERS = {"always_on", "model_decision", "glob", "manual"}
VALID_MODELS = {"inherit", "flash", "pro"}
VALID_POLICIES = {"off", "auto", "eager", "sandbox"}
VALID_TOOLS = {
    "view_file",
    "write_to_file",
    "replace_file_content",
    "multi_replace_file_content",
    "list_dir",
    "find_by_name",
    "grep_search",
    "search_web",
    "read_url_content",
    "run_command",
}


def parse_frontmatter(path: Path) -> tuple[dict[str, str], dict[str, list[str]], list[str]]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, {}, [f"{path.relative_to(ROOT)}: missing YAML frontmatter"]
    marker = text.find("\n---", 4)
    if marker == -1:
        return {}, {}, [f"{path.relative_to(ROOT)}: unterminated YAML frontmatter"]
    raw = text[4:marker]
    scalars: dict[str, str] = {}
    lists: dict[str, list[str]] = {}
    current: str | None = None
    for line in raw.splitlines():
        match = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):(?:\s*(.*))?$", line)
        if match:
            key, value = match.group(1), (match.group(2) or "").strip()
            if value:
                scalars[key] = value.strip('"').strip("'")
                current = None
            else:
                lists[key] = []
                current = key
            continue
        item = re.match(r"^\s+-\s+(.+?)\s*$", line)
        if item and current:
            lists[current].append(item.group(1).strip('"').strip("'"))
    return scalars, lists, errors


def validate_agents(errors: list[str]) -> int:
    count = 0
    base = AGENTS_DIR / "agents"
    if not base.exists():
        errors.append(".agents/agents: missing")
        return count
    agent_files = list(base.glob("*.md")) + list(base.glob("*/agent.md"))
    required = (
        "name",
        "description",
        "mainAgent",
        "subagent",
        "model",
        "commandExecutionPolicy",
    )
    for path in sorted(agent_files):
        count += 1
        scalars, lists, local = parse_frontmatter(path)
        errors.extend(local)
        rel = path.relative_to(ROOT)
        for key in required:
            if key not in scalars:
                errors.append(f"{rel}: missing {key}")
        if scalars.get("model") not in VALID_MODELS:
            errors.append(f"{rel}: invalid model {scalars.get('model')!r}")
        if scalars.get("commandExecutionPolicy") not in VALID_POLICIES:
            errors.append(f"{rel}: invalid commandExecutionPolicy")
        for key in ("mainAgent", "subagent"):
            if scalars.get(key) not in {"true", "false"}:
                errors.append(f"{rel}: {key} must be true/false")
        for tool in lists.get("tools", []):
            if tool not in VALID_TOOLS:
                errors.append(f"{rel}: undocumented/unsupported tool {tool!r}")
        for skill in lists.get("skills", []):
            target = AGENTS_DIR / skill
            if not (target / "SKILL.md").exists():
                errors.append(f"{rel}: missing skill dependency {skill}")
        for agent in lists.get("agents", []):
            target = AGENTS_DIR / agent
            if not ((target / "agent.md").exists() or target.with_suffix(".md").exists()):
                errors.append(f"{rel}: missing agent dependency {agent}")
    return count


def validate_skills(errors: list[str]) -> int:
    base = AGENTS_DIR / "skills"
    if not base.exists():
        errors.append(".agents/skills: missing")
        return 0
    count = 0
    for folder in sorted(p for p in base.iterdir() if p.is_dir()):
        skill = folder / "SKILL.md"
        if not skill.exists():
            errors.append(f"{folder.relative_to(ROOT)}: missing SKILL.md")
            continue
        count += 1
        scalars, _, local = parse_frontmatter(skill)
        errors.extend(local)
        if not scalars.get("description"):
            errors.append(f"{skill.relative_to(ROOT)}: missing description")
        if scalars.get("name") and scalars["name"] != folder.name:
            errors.append(f"{skill.relative_to(ROOT)}: name must match folder")
    if (AGENTS_DIR / "workflows").exists():
        errors.append(".agents/workflows is deprecated; migrate to Skills")
    return count


def validate_rules(errors: list[str]) -> int:
    base = AGENTS_DIR / "rules"
    if not base.exists():
        errors.append(".agents/rules: missing")
        return 0
    direct = set(base.glob("*.md"))
    nested = set(base.rglob("*.md")) - direct
    for path in sorted(nested):
        errors.append(f"{path.relative_to(ROOT)}: nested rule is not auto-discovered")
    for path in sorted(direct):
        scalars, _, local = parse_frontmatter(path)
        errors.extend(local)
        trigger = scalars.get("trigger")
        if trigger not in VALID_TRIGGERS:
            errors.append(f"{path.relative_to(ROOT)}: invalid trigger {trigger!r}")
        if trigger == "model_decision" and not scalars.get("description"):
            errors.append(f"{path.relative_to(ROOT)}: model_decision requires description")
        if trigger == "glob" and not (scalars.get("globs") or scalars.get("glob")):
            errors.append(f"{path.relative_to(ROOT)}: glob rule requires globs/glob")
    return len(direct)


def validate_agents_md(errors: list[str]) -> int:
    files = list(ROOT.rglob("AGENTS.md")) + list(ROOT.rglob("GEMINI.md"))
    for path in files:
        if path.read_text(encoding="utf-8").startswith("---\n"):
            errors.append(f"{path.relative_to(ROOT)}: AGENTS/GEMINI must not use frontmatter")
    return len(files)


def validate_hooks(errors: list[str]) -> int:
    path = AGENTS_DIR / "hooks.json"
    if not path.exists():
        return 0
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f".agents/hooks.json: invalid JSON: {exc}")
        return 0
    if not isinstance(data, dict):
        errors.append(".agents/hooks.json: root must be object")
        return 0
    for name, config in data.items():
        if not isinstance(config, dict):
            errors.append(f".agents/hooks.json: hook {name} must be object")
            continue
        for event in ("PreToolUse", "PostToolUse"):
            for entry in config.get(event, []):
                matcher = entry.get("matcher", "")
                try:
                    re.compile(matcher or ".*")
                except re.error as exc:
                    errors.append(f".agents/hooks.json: invalid matcher {matcher!r}: {exc}")
    return len(data)


def main() -> int:
    errors: list[str] = []
    counts = {
        "agents_md": validate_agents_md(errors),
        "rules": validate_rules(errors),
        "skills": validate_skills(errors),
        "agents": validate_agents(errors),
        "hooks": validate_hooks(errors),
    }
    if errors:
        print("Antigravity customization validation FAILED:")
        for error in errors:
            print(f" - {error}")
        return 1
    print(
        "Antigravity customization validation OK: "
        + ", ".join(f"{key}={value}" for key, value in counts.items())
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
