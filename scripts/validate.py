#!/usr/bin/env python3
from __future__ import annotations

import json
import ast
import re
import sys
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "project-health-pass"
SKILL_MD = SKILL_DIR / "SKILL.md"
README = ROOT / "README.md"
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        fail(f"{path} must start with YAML frontmatter")
    try:
        _, frontmatter, body = text.split("---", 2)
    except ValueError:
        fail(f"{path} must contain closing frontmatter delimiter")
    if not body.strip():
        fail(f"{path} must contain instructions after frontmatter")

    fields: dict[str, str] = {}
    for raw_line in frontmatter.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if ":" not in line:
            fail(f"Unsupported frontmatter line: {raw_line!r}")
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip()
    return fields


def validate_skill() -> None:
    if not SKILL_MD.exists():
        fail(f"Missing {SKILL_MD}")

    fields = parse_frontmatter(SKILL_MD)
    name = fields.get("name", "")
    description = fields.get("description", "")

    if name != SKILL_DIR.name:
        fail(f"name must match folder name: {name!r} != {SKILL_DIR.name!r}")
    if not NAME_RE.fullmatch(name):
        fail("name must use lowercase letters, numbers, and single hyphens")
    if not description:
        fail("description is required")
    if len(description) > 200:
        fail("description must be 200 characters or less for broad Claude.ai compatibility")
    if "[" in description or "TODO" in description:
        fail("description still contains placeholder text")


def validate_json_files() -> None:
    for path in [
        ROOT / ".codex-plugin" / "plugin.json",
        ROOT / ".claude-plugin" / "plugin.json",
        ROOT / ".claude-plugin" / "marketplace.json",
        ROOT / ".agents" / "plugins" / "marketplace.json",
        ROOT / "evals" / "trigger-evals.json",
    ]:
        if not path.exists():
            fail(f"Missing {path}")
        with path.open(encoding="utf-8") as handle:
            json.load(handle)


def validate_version_consistency() -> None:
    codex_manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    version = codex_manifest.get("version")
    if not version:
        fail(".codex-plugin/plugin.json must include version")

    plugin_manifest = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    if plugin_manifest.get("version") != version:
        fail(".claude-plugin/plugin.json version must match .codex-plugin/plugin.json")

    claude_marketplace = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    if claude_marketplace.get("metadata", {}).get("version") != version:
        fail(".claude-plugin/marketplace.json metadata.version must match plugin version")
    for plugin in claude_marketplace.get("plugins", []):
        if plugin.get("version") != version:
            fail(".claude-plugin/marketplace.json plugin version must match plugin version")

    agents_marketplace = json.loads((ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8"))
    if agents_marketplace.get("version") != version:
        fail(".agents/plugins/marketplace.json version must match plugin version")

    for path in [
        SKILL_MD,
        SKILL_DIR / "scripts" / "agent_memory.py",
        SKILL_DIR / "scripts" / "health_report.py",
        README,
    ]:
        if version not in path.read_text(encoding="utf-8"):
            fail(f"{path} does not mention current version {version}")


def validate_python_files() -> None:
    for path in [
        ROOT / "scripts" / "validate.py",
        SKILL_DIR / "scripts" / "agent_memory.py",
        SKILL_DIR / "scripts" / "health_report.py",
    ]:
        if not path.exists():
            fail(f"Missing {path}")
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def validate_no_placeholders_in_skill() -> None:
    text = SKILL_MD.read_text(encoding="utf-8")
    if "TODO" in text or "[TODO" in text:
        fail("SKILL.md still contains placeholder text")


def validate_readme() -> None:
    if not README.exists():
        fail("README.md is required")
    text = README.read_text(encoding="utf-8")
    forbidden = [
        "YOUR_GITHUB_USERNAME",
        "Your Name",
        "project-health-pass-agent-skill",
        "path/to/",
    ]
    for token in forbidden:
        if token in text:
            fail(f"README.md contains stale placeholder/reference: {token}")

    for match in MARKDOWN_LINK_RE.finditer(text):
        target = match.group(1).strip()
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        path_part = unquote(target.split("#", 1)[0])
        if not path_part:
            continue
        if not (ROOT / path_part).exists():
            fail(f"README.md link target does not exist: {target}")


def main() -> None:
    validate_skill()
    validate_json_files()
    validate_version_consistency()
    validate_python_files()
    validate_no_placeholders_in_skill()
    validate_readme()
    print("Validation passed")


if __name__ == "__main__":
    main()
