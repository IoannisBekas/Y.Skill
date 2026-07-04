# Y.Skill

[![Validate](https://github.com/IoannisBekas/Y.Skill/actions/workflows/validate.yml/badge.svg)](https://github.com/IoannisBekas/Y.Skill/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Agent Skill](https://img.shields.io/badge/Agent%20Skill-SKILL.md-blue.svg)](skills/project-health-pass/SKILL.md)
[![Version](https://img.shields.io/badge/version-0.4.1-black.svg)](skills/project-health-pass/SKILL.md)

**Y.Skill is a self-improving Agent Skill for repository health remediation.**

It gives Claude Code, OpenAI Codex, Cursor, and other `SKILL.md`-compatible agents a disciplined workflow for finding, fixing, verifying, and remembering core reliability problems in real repositories.

This repository is the installable package. The marketplace and plugin are named `project-health-pass`, and the bundled skill is [`project-health-pass`](skills/project-health-pass/SKILL.md).

## Start Here

Install the marketplace, then invoke the skill by name:

```text
/plugin marketplace add IoannisBekas/Y.Skill
/plugin install project-health-pass@project-health-pass
/reload-plugins
```

First useful prompt:

```text
Use project-health-pass in audit-only mode. Do not edit files. Run the native checks that are safe, produce stable HP-* findings, and mark unknown evidence surfaces explicitly.
```

When you want remediation:

```text
Use project-health-pass in fix-verified mode. Counter-review serious findings, fix only safe P0-P2 issues, add focused tests, and report anything blocked.
```

## Why This Exists

Asking an agent to "review this repo" usually produces a one-off opinion. Y.Skill turns that request into a repeatable health pass with evidence, stable IDs, safe remediation rules, and project memory.

It gives the agent a durable workflow:

- read project memory from `.agent_memory.json`;
- select a safe mode before touching files;
- inspect repo structure, toolchains, CI, docs, and runtime boundaries;
- run the repo's own lint, typecheck, test, build, audit, and smoke checks where safe;
- assign stable `HP-*` finding IDs;
- counter-review serious findings before reporting or fixing them;
- fix verified P0/P1/P2 issues only when safely scoped;
- update focused tests;
- emit optional machine-readable reports;
- write verified lessons back to memory.

## Use It For

- CI failures where the real root cause is unclear.
- Pre-release reliability hardening.
- Auditing an unfamiliar or inherited repository.
- Cleaning up AI-generated apps before they face real users.
- Comparing health reports across weekly or monthly runs.
- Capturing repo-specific quirks so future agents do not repeat the same mistakes.

## Not For

- Single-function code review.
- Cosmetic lint cleanup.
- Broad refactors without a verified reliability reason.
- Production writes, credentialed external actions, or destructive migrations.
- Replacing a security audit for regulated or high-risk systems.

## The Three Modes

| Mode | Use When | File Writes |
| --- | --- | --- |
| `audit-only` | You want a read-only repo health report or baseline | No source, lockfile, generated-data, or memory writes |
| `fix-verified` | You want safe remediation of verified P0-P2 issues | Yes, but only scoped fixes with verification |
| `baseline-diff` | You want to compare against a previous health report | Read-only unless remediation is explicitly requested |

If a request is ambiguous, the skill chooses `audit-only`. If the user asks to fix, repair, or unblock CI/deployments, it chooses `fix-verified`.

## What Makes It Different

- **Evidence coverage matrix:** each surface is marked `pass`, `finding`, `unknown`, or `not-applicable`. Unknown is never treated as healthy.
- **Counter-review gate:** P0/P1/P2 findings must be verified by source trace, native command, test, or reproducible behavior before they are reported or fixed.
- **Stable finding IDs:** findings use IDs such as `HP-SEC-001`, `HP-BUILD-001`, `HP-TEST-001`, and `HP-CONFIG-001`, so reports can be diffed across runs.
- **Safest-first remediation:** fixes are prioritized by severity, evidence strength, reversibility, blast radius, and available verification.
- **Project memory:** verified command quirks, false positives, failed assumptions, and effective strategies are written to `.agent_memory.json` for future runs. Review that file before committing it to a team repository.

## Example Prompts

```text
Use project-health-pass in audit-only mode. Do not edit files. Produce stable HP-* findings and mark unknown evidence surfaces explicitly.
```

```text
Use project-health-pass in fix-verified mode. Run the native checks, counter-review serious findings, fix safe P0-P2 issues, and update focused tests.
```

```text
Use project-health-pass in baseline-diff mode. Compare the current repo against the previous project-health-pass JSON report.
```

```text
CI is failing. Use project-health-pass to find the root cause, fix verified build/test blockers, and report any remaining blocked items.
```

## Install

### Claude Code

```text
/plugin marketplace add IoannisBekas/Y.Skill
/plugin install project-health-pass@project-health-pass
/reload-plugins
```

Then invoke it:

```text
Use the project-health-pass skill in fix-verified mode for a deep repo health pass.
```

### OpenAI Codex

As a plugin marketplace:

```bash
codex plugin marketplace add IoannisBekas/Y.Skill
```

Then open Codex Plugins and install or enable `Project Health Pass`.

Or as a local skill:

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

Claude.ai expects a ZIP whose root contains the skill folder. Build it locally with one of the commands below, or download `project-health-pass.zip` from the latest GitHub release.

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

## Optional JSON Reports

The skill can emit and validate `project-health-pass.report.v1` JSON for baselines, CI handoff, or long-running reliability programs.

```bash
python skills/project-health-pass/scripts/health_report.py template --repo . --mode audit-only --out health-report.json
python skills/project-health-pass/scripts/health_report.py validate --report health-report.json
python skills/project-health-pass/scripts/health_report.py diff --old previous.json --new health-report.json
```

The report schema includes:

- `repo_map`
- `coverage`
- `findings`
- `backlog`
- `suppressions`
- `checks`
- `changed_files`
- `memory`
- `remaining`

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
```

## Safety Model

Y.Skill is deliberately conservative:

- preserves user changes;
- does not run destructive operations or production writes;
- avoids credentialed external actions unless explicitly approved;
- distinguishes source from generated/runtime artifacts before editing;
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
