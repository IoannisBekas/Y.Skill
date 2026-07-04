# Y.Skill

![Taking control with Y.Skill](assets/yskill-overview.png)

[![Validate](https://github.com/IoannisBekas/Y.Skill/actions/workflows/validate.yml/badge.svg)](https://github.com/IoannisBekas/Y.Skill/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Agent Skill](https://img.shields.io/badge/Agent%20Skill-SKILL.md-blue.svg)](skills/project-health-pass/SKILL.md)
[![Version](https://img.shields.io/badge/version-0.4.1-black.svg)](skills/project-health-pass/SKILL.md)

**Y.Skill packages `project-health-pass`, a self-improving Agent Skill for repository health remediation.**

It gives Claude Code, OpenAI Codex, Cursor, and other `SKILL.md`-compatible agents a disciplined way to inspect real repositories, verify serious findings, fix safe reliability issues, and remember project-specific lessons for future runs.

## Quick Start

Claude Code:

```text
/plugin marketplace add IoannisBekas/Y.Skill
/plugin install project-health-pass@project-health-pass
/reload-plugins
```

Start with a read-only pass:

```text
Use project-health-pass in audit-only mode. Do not edit files. Run the native checks that are safe, produce stable HP-* findings, and mark unknown evidence surfaces explicitly.
```

Then ask for safe remediation:

```text
Use project-health-pass in fix-verified mode. Counter-review serious findings, fix only safe P0-P2 issues, add focused tests, and report anything blocked.
```

## What It Does

`project-health-pass` turns "review this repo" into a repeatable health workflow:

- maps project structure, package managers, CI, scripts, docs, and runtime boundaries;
- distinguishes source from generated files, logs, caches, and build outputs;
- runs native lint, typecheck, test, build, audit, and smoke checks when safe;
- ranks findings as P0/P1/P2/P3 using evidence, blast radius, and reversibility;
- assigns stable `HP-*` IDs so reports can be compared across runs;
- counter-reviews serious findings before reporting or fixing them;
- fixes verified P0/P1/P2 issues only when the change is safely scoped;
- records useful project lessons in `.agent_memory.json`.

## When to Use It

| Use It For | Avoid Using It For |
| --- | --- |
| CI failures with unclear root cause | Single-function code review |
| Pre-release reliability hardening | Cosmetic lint cleanup |
| Auditing inherited or unfamiliar repos | Broad refactors without verified reliability impact |
| Cleaning up AI-generated apps before real users | Production writes or destructive migrations |
| Comparing weekly or monthly health reports | Replacing a security audit for regulated systems |
| Capturing repo-specific quirks for future agents | Credentialed external actions without explicit approval |

## Modes

| Mode | Use When | File Writes |
| --- | --- | --- |
| `audit-only` | You want a read-only repo health report or baseline | No source, lockfile, generated-data, or memory writes |
| `fix-verified` | You want safe remediation of verified P0-P2 issues | Yes, but only scoped fixes with verification |
| `baseline-diff` | You want to compare against a previous health report | Read-only unless remediation is explicitly requested |

If a request is ambiguous, the skill chooses `audit-only`. If the user asks to fix, repair, or unblock CI/deployments, it chooses `fix-verified`.

## Core Practices

- **Evidence coverage:** every checked surface is marked `pass`, `finding`, `unknown`, or `not-applicable`.
- **Counter-review gate:** P0/P1/P2 findings need source trace, native command output, test evidence, or reproducible behavior.
- **Stable finding IDs:** findings use IDs such as `HP-SEC-001`, `HP-BUILD-001`, `HP-TEST-001`, and `HP-CONFIG-001`.
- **Safest-first remediation:** fixes are ranked by severity, evidence strength, reversibility, blast radius, and available verification.
- **Project memory:** verified command quirks, false positives, failed assumptions, and effective strategies are written to `.agent_memory.json`.

Review `.agent_memory.json` before committing it to a team repository.

## Install

### Claude Code

```text
/plugin marketplace add IoannisBekas/Y.Skill
/plugin install project-health-pass@project-health-pass
/reload-plugins
```

Invoke it:

```text
Use the project-health-pass skill in fix-verified mode for a deep repo health pass.
```

### OpenAI Codex

As a plugin marketplace:

```bash
codex plugin marketplace add IoannisBekas/Y.Skill
```

Then open Codex Plugins and install or enable `Project Health Pass`.

As a local skill:

```bash
mkdir -p ~/.codex/skills
cp -R skills/project-health-pass ~/.codex/skills/
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force "$HOME\.codex\skills"
Copy-Item -Recurse -Force ".\skills\project-health-pass" "$HOME\.codex\skills\"
```

### Claude.ai Custom Skill

Claude.ai expects a ZIP whose root contains the skill folder. Build it locally, or download `project-health-pass.zip` from the latest GitHub release.

```powershell
.\scripts\package-claude-ai.ps1
```

macOS/Linux:

```bash
bash scripts/package-claude-ai.sh
```

Upload `dist/project-health-pass.zip` in Claude settings under Skills.

### Cursor

Copy the project rule into your target repo:

```text
.cursor/rules/project-health-pass.mdc
```

The Cursor rule is not always-on by default; invoke it when you want a deep health pass.

### Generic Agent Skills Clients

Copy the skill folder into a project-scoped skills directory:

```bash
mkdir -p .agents/skills
cp -R skills/project-health-pass .agents/skills/
```

## Reports and Memory

The skill can emit and validate `project-health-pass.report.v1` JSON for baselines, CI handoff, or long-running reliability programs.

```bash
python skills/project-health-pass/scripts/health_report.py template --repo . --mode audit-only --out health-report.json
python skills/project-health-pass/scripts/health_report.py validate --report health-report.json
python skills/project-health-pass/scripts/health_report.py diff --old previous.json --new health-report.json
```

Report sections include `repo_map`, `coverage`, `findings`, `backlog`, `suppressions`, `checks`, `changed_files`, `memory`, and `remaining`.

Memory helpers:

```bash
python skills/project-health-pass/scripts/agent_memory.py read --repo .
python skills/project-health-pass/scripts/agent_memory.py append --repo . \
  --category command_quirk \
  --summary "..." \
  --details "..." \
  --evidence "..." \
  --action "..."
```

## Repository Layout

```text
skills/project-health-pass/SKILL.md       Portable Agent Skill
skills/project-health-pass/agents/        Codex/OpenAI UI metadata
skills/project-health-pass/scripts/       Memory and report helpers
.codex-plugin/plugin.json                 Codex plugin manifest
.claude-plugin/plugin.json                Claude Code plugin manifest
.cursor/rules/project-health-pass.mdc     Cursor rule adapter
adapters/                                 AGENTS.md, CLAUDE.md, generic prompt adapters
evals/trigger-evals.json                  Trigger-quality prompts
scripts/validate.py                       No-dependency validator
scripts/package-claude-ai.*               Claude.ai ZIP packaging
assets/yskill-overview.png                README image
```

## Safety

Y.Skill is deliberately conservative:

- preserves user changes;
- avoids destructive operations and production writes;
- avoids credentialed external actions unless explicitly approved;
- treats generated data, logs, caches, and build outputs as non-source by default;
- does not hide failures by weakening tests or broadening ignores;
- records skipped checks with exact blockers;
- keeps false positives and accepted risks visible with evidence.

## Validate

```bash
python scripts/validate.py
```

The repository validator checks manifests, JSON files, Python helper syntax, skill metadata, README links, placeholder drift, and version consistency.

## License

Y.Skill is released under the MIT License. See [LICENSE](LICENSE) for the full license text.
