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


SCHEMA = "project-health-pass.report.v1"
SKILL_NAME = "project-health-pass"
VERSION = "0.4.1"
VALID_MODES = {"audit-only", "fix-verified", "baseline-diff"}
VALID_SEVERITIES = {"P0", "P1", "P2", "P3"}
VALID_STATUSES = {"open", "fixed", "blocked", "accepted-risk", "false-positive"}
VALID_CHECK_RESULTS = {"passed", "failed", "skipped", "blocked"}
VALID_COVERAGE_STATUSES = {"pass", "finding", "unknown", "not-applicable"}
VALID_BACKLOG_STATUSES = {"pending", "done", "blocked", "deferred"}
VALID_BLAST_RADIUS = {"low", "medium", "high"}
VALID_REVERSIBILITY = {"low", "medium", "high"}
ID_RE = re.compile(
    r"^HP-(SEC|DATA|BUILD|RUN|TEST|CONFIG|DEP|OPS|TYPE|PERF|DOCS)-[0-9]{3}$"
)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def report_template(repo: Path, mode: str) -> dict[str, Any]:
    if mode not in VALID_MODES:
        raise ValueError(f"mode must be one of: {', '.join(sorted(VALID_MODES))}")
    return {
        "schema": SCHEMA,
        "skill": SKILL_NAME,
        "version": VERSION,
        "mode": mode,
        "repo": str(repo),
        "generated_at": now_utc(),
        "repo_map": {
            "primary_languages": [],
            "package_managers": [],
            "entry_points": [],
            "ci": [],
            "source_boundaries": {
                "source": [],
                "generated": [],
                "runtime": [],
            },
        },
        "coverage": [],
        "summary": {
            "status": "findings",
            "p0": 0,
            "p1": 0,
            "p2": 0,
            "p3": 0,
        },
        "findings": [],
        "backlog": [],
        "suppressions": [],
        "checks": [],
        "changed_files": [],
        "memory": {
            "read": "",
            "updated": "",
        },
        "remaining": [],
    }


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8-sig") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def require_type(data: dict[str, Any], key: str, expected_type: type) -> Any:
    value = data.get(key)
    if not isinstance(value, expected_type):
        raise ValueError(f"{key} must be {expected_type.__name__}")
    return value


def validate_report(data: dict[str, Any]) -> None:
    if data.get("schema") != SCHEMA:
        raise ValueError(f"schema must be {SCHEMA!r}")
    if data.get("skill") != SKILL_NAME:
        raise ValueError(f"skill must be {SKILL_NAME!r}")
    if data.get("mode") not in VALID_MODES:
        raise ValueError(f"mode must be one of: {', '.join(sorted(VALID_MODES))}")
    require_type(data, "repo", str)
    require_type(data, "generated_at", str)
    validate_repo_map(data.get("repo_map", {}))
    validate_coverage(require_type(data, "coverage", list))

    summary = require_type(data, "summary", dict)
    for key in ("p0", "p1", "p2", "p3"):
        if not isinstance(summary.get(key), int):
            raise ValueError(f"summary.{key} must be int")

    findings = require_type(data, "findings", list)
    seen_ids: set[str] = set()
    computed = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
    for index, item in enumerate(findings):
        if not isinstance(item, dict):
            raise ValueError(f"findings[{index}] must be object")
        finding_id = item.get("id")
        if not isinstance(finding_id, str) or not ID_RE.fullmatch(finding_id):
            raise ValueError(f"findings[{index}].id must match {ID_RE.pattern}")
        if finding_id in seen_ids:
            raise ValueError(f"duplicate finding id: {finding_id}")
        seen_ids.add(finding_id)

        severity = item.get("severity")
        if severity not in VALID_SEVERITIES:
            raise ValueError(f"{finding_id}.severity must be P0, P1, P2, or P3")
        computed[severity] += 1

        status = item.get("status")
        if status not in VALID_STATUSES:
            raise ValueError(f"{finding_id}.status must be one of: {', '.join(sorted(VALID_STATUSES))}")
        for key in ("title", "recommendation"):
            if not isinstance(item.get(key), str) or not item[key].strip():
                raise ValueError(f"{finding_id}.{key} is required")
        for key in ("locations", "evidence", "verification"):
            if not isinstance(item.get(key), list):
                raise ValueError(f"{finding_id}.{key} must be list")

    for severity, count in computed.items():
        summary_key = severity.lower()
        if summary.get(summary_key) != count:
            raise ValueError(f"summary.{summary_key} must equal {count}")

    validate_backlog(require_type(data, "backlog", list), seen_ids)
    validate_suppressions(require_type(data, "suppressions", list), seen_ids)

    for index, item in enumerate(require_type(data, "checks", list)):
        if not isinstance(item, dict):
            raise ValueError(f"checks[{index}] must be object")
        if not isinstance(item.get("command"), str):
            raise ValueError(f"checks[{index}].command must be string")
        if item.get("result") not in VALID_CHECK_RESULTS:
            raise ValueError(f"checks[{index}].result must be one of: {', '.join(sorted(VALID_CHECK_RESULTS))}")

    require_type(data, "changed_files", list)
    require_type(data, "memory", dict)
    require_type(data, "remaining", list)


def validate_string_list(value: Any, label: str) -> None:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"{label} must be a list of strings")


def validate_repo_map(value: Any) -> None:
    if not isinstance(value, dict):
        raise ValueError("repo_map must be object")
    for key in ("primary_languages", "package_managers", "entry_points", "ci"):
        validate_string_list(value.get(key, []), f"repo_map.{key}")
    source_boundaries = value.get("source_boundaries", {})
    if not isinstance(source_boundaries, dict):
        raise ValueError("repo_map.source_boundaries must be object")
    for key in ("source", "generated", "runtime"):
        validate_string_list(source_boundaries.get(key, []), f"repo_map.source_boundaries.{key}")


def validate_coverage(items: list[Any]) -> None:
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"coverage[{index}] must be object")
        if not isinstance(item.get("surface"), str) or not item["surface"].strip():
            raise ValueError(f"coverage[{index}].surface is required")
        if item.get("status") not in VALID_COVERAGE_STATUSES:
            raise ValueError(
                f"coverage[{index}].status must be one of: {', '.join(sorted(VALID_COVERAGE_STATUSES))}"
            )
        validate_string_list(item.get("evidence", []), f"coverage[{index}].evidence")
        if "notes" in item and not isinstance(item["notes"], str):
            raise ValueError(f"coverage[{index}].notes must be string")


def validate_backlog(items: list[Any], finding_ids: set[str]) -> None:
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"backlog[{index}] must be object")
        finding_id = item.get("finding_id")
        if not isinstance(finding_id, str) or not ID_RE.fullmatch(finding_id):
            raise ValueError(f"backlog[{index}].finding_id must match {ID_RE.pattern}")
        if finding_id not in finding_ids:
            raise ValueError(f"backlog[{index}].finding_id does not exist in findings: {finding_id}")
        if not isinstance(item.get("priority"), int) or item["priority"] < 1:
            raise ValueError(f"backlog[{index}].priority must be positive int")
        if not isinstance(item.get("fix_summary"), str) or not item["fix_summary"].strip():
            raise ValueError(f"backlog[{index}].fix_summary is required")
        if item.get("blast_radius") not in VALID_BLAST_RADIUS:
            raise ValueError(f"backlog[{index}].blast_radius must be low, medium, or high")
        if item.get("reversibility") not in VALID_REVERSIBILITY:
            raise ValueError(f"backlog[{index}].reversibility must be low, medium, or high")
        validate_string_list(item.get("verification", []), f"backlog[{index}].verification")
        if not isinstance(item.get("rollback"), str) or not item["rollback"].strip():
            raise ValueError(f"backlog[{index}].rollback is required")
        if item.get("status") not in VALID_BACKLOG_STATUSES:
            raise ValueError(f"backlog[{index}].status must be one of: {', '.join(sorted(VALID_BACKLOG_STATUSES))}")


def validate_suppressions(items: list[Any], finding_ids: set[str]) -> None:
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"suppressions[{index}] must be object")
        finding_id = item.get("finding_id")
        if not isinstance(finding_id, str) or not ID_RE.fullmatch(finding_id):
            raise ValueError(f"suppressions[{index}].finding_id must match {ID_RE.pattern}")
        if finding_id not in finding_ids:
            raise ValueError(f"suppressions[{index}].finding_id does not exist in findings: {finding_id}")
        if not isinstance(item.get("reason"), str) or not item["reason"].strip():
            raise ValueError(f"suppressions[{index}].reason is required")
        validate_string_list(item.get("evidence", []), f"suppressions[{index}].evidence")
        if "expires" in item and not isinstance(item["expires"], str):
            raise ValueError(f"suppressions[{index}].expires must be string")


def index_findings(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in report.get("findings", []) if isinstance(item, dict) and "id" in item}


def diff_reports(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    validate_report(old)
    validate_report(new)
    old_findings = index_findings(old)
    new_findings = index_findings(new)
    old_ids = set(old_findings)
    new_ids = set(new_findings)
    common_ids = sorted(old_ids & new_ids)
    return {
        "schema": "project-health-pass.diff.v1",
        "old_report": old.get("generated_at", ""),
        "new_report": new.get("generated_at", ""),
        "new_findings": sorted(new_ids - old_ids),
        "new_blocking_findings": sorted(
            finding_id
            for finding_id in new_ids - old_ids
            if new_findings[finding_id].get("severity") in {"P0", "P1"}
        ),
        "resolved_or_removed": sorted(old_ids - new_ids),
        "severity_changed": [
            finding_id
            for finding_id in common_ids
            if old_findings[finding_id].get("severity") != new_findings[finding_id].get("severity")
        ],
        "status_changed": [
            finding_id
            for finding_id in common_ids
            if old_findings[finding_id].get("status") != new_findings[finding_id].get("status")
        ],
        "coverage_regressions": coverage_regressions(old, new),
    }


def coverage_index(report: dict[str, Any]) -> dict[str, str]:
    return {
        item["surface"]: item["status"]
        for item in report.get("coverage", [])
        if isinstance(item, dict) and isinstance(item.get("surface"), str) and isinstance(item.get("status"), str)
    }


def coverage_regressions(old: dict[str, Any], new: dict[str, Any]) -> list[str]:
    old_coverage = coverage_index(old)
    new_coverage = coverage_index(new)
    regressions: list[str] = []
    for surface, new_status in sorted(new_coverage.items()):
        old_status = old_coverage.get(surface)
        if old_status == "pass" and new_status in {"finding", "unknown"}:
            regressions.append(surface)
    return regressions


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create, validate, and diff Project Health Pass JSON reports.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    template = subparsers.add_parser("template", help="Create a blank report template")
    template.add_argument("--repo", default=".", help="Repository root or label")
    template.add_argument("--mode", required=True, choices=sorted(VALID_MODES))
    template.add_argument("--out", help="Write template to this path instead of stdout")

    validate = subparsers.add_parser("validate", help="Validate a report file")
    validate.add_argument("--report", required=True, help="Path to report JSON")

    diff = subparsers.add_parser("diff", help="Diff two report files")
    diff.add_argument("--old", required=True, help="Previous report JSON")
    diff.add_argument("--new", required=True, help="Current report JSON")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.command == "template":
            data = report_template(Path(args.repo), args.mode)
            if args.out:
                write_json(Path(args.out), data)
                print(json.dumps({"status": "written", "path": args.out}, indent=2))
            else:
                print(json.dumps(data, indent=2, ensure_ascii=False))
        elif args.command == "validate":
            validate_report(load_json(Path(args.report)))
            print(json.dumps({"status": "valid", "path": args.report}, indent=2))
        else:
            result = diff_reports(load_json(Path(args.old)), load_json(Path(args.new)))
            print(json.dumps(result, indent=2, ensure_ascii=False))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.exit(1, f"health_report.py: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
