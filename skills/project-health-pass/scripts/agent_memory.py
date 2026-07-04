#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SKILL_NAME = "project-health-pass"
MEMORY_FILE = ".agent_memory.json"
VERSION = "0.4.1"
VALID_CATEGORIES = {
    "false_positive",
    "effective_strategy",
    "project_quirk",
    "command_quirk",
    "failed_assumption",
}
SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|token|secret|password|credential)\s*[:=]\s*['\"]?[^'\"\s,}]+"),
    re.compile(r"\b[A-Za-z0-9_=-]{32,}\b"),
]


def redact(value: str) -> str:
    result = value
    for pattern in SECRET_PATTERNS:
        result = pattern.sub("[REDACTED]", result)
    return result[:2000]


def memory_path(repo: Path) -> Path:
    return repo.resolve() / MEMORY_FILE


def default_memory() -> dict[str, Any]:
    return {
        "skill": SKILL_NAME,
        "version": VERSION,
        "entries": [],
    }


def load_memory(path: Path) -> dict[str, Any]:
    if not path.exists():
        return default_memory()
    with path.open(encoding="utf-8-sig") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("memory file must contain a JSON object")
    entries = data.setdefault("entries", [])
    if not isinstance(entries, list):
        raise ValueError("memory entries must be a list")
    data.setdefault("skill", SKILL_NAME)
    data.setdefault("version", VERSION)
    return data


def write_memory(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".agent_memory.", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def normalize_entry(args: argparse.Namespace) -> dict[str, str]:
    if args.category not in VALID_CATEGORIES:
        raise ValueError(f"category must be one of: {', '.join(sorted(VALID_CATEGORIES))}")
    entry = {
        "category": args.category,
        "summary": redact(args.summary.strip()),
        "details": redact(args.details.strip()),
        "evidence": redact(args.evidence.strip()),
        "action": redact(args.action.strip()),
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    for key in ("summary", "details", "evidence", "action"):
        if not entry[key]:
            raise ValueError(f"{key} is required")
    return entry


def append_entry(repo: Path, args: argparse.Namespace) -> dict[str, Any]:
    path = memory_path(repo)
    data = load_memory(path)
    entry = normalize_entry(args)
    entries = data["entries"]
    for existing in entries:
        if (
            isinstance(existing, dict)
            and existing.get("category") == entry["category"]
            and existing.get("summary") == entry["summary"]
        ):
            existing.update(entry)
            write_memory(path, data)
            return {"path": str(path), "status": "updated", "entry": existing}
    entries.append(entry)
    write_memory(path, data)
    return {"path": str(path), "status": "appended", "entry": entry}


def read_memory(repo: Path) -> dict[str, Any]:
    path = memory_path(repo)
    data = load_memory(path)
    return {"path": str(path), "exists": path.exists(), "memory": data}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read or update a project health pass memory ledger.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    read = subparsers.add_parser("read", help="Read .agent_memory.json")
    read.add_argument("--repo", default=".", help="Repository root")

    append = subparsers.add_parser("append", help="Append or update one memory entry")
    append.add_argument("--repo", default=".", help="Repository root")
    append.add_argument("--category", required=True, choices=sorted(VALID_CATEGORIES))
    append.add_argument("--summary", required=True, help="Short future-facing rule")
    append.add_argument("--details", required=True, help="Why this matters")
    append.add_argument("--evidence", required=True, help="Command, file, or trace that verified it")
    append.add_argument("--action", required=True, help="What future agents should do")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    repo = Path(args.repo)
    try:
        if args.command == "read":
            result = read_memory(repo)
        else:
            result = append_entry(repo, args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.exit(1, f"agent_memory.py: {exc}\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
