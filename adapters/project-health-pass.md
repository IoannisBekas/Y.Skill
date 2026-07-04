# Project Health Pass Prompt

Perform a deep project-wide health pass and fix identified core reliability problems when remediation is requested.

Select exactly one mode before scanning:

- `audit-only`: read-only report; do not modify source, lockfiles, generated data, memory, or runtime state.
- `fix-verified`: fix verified P0/P1/P2 reliability problems that are structurally safe.
- `baseline-diff`: compare current findings against a prior `project-health-pass.report.v1` JSON report and keep matching IDs stable.

At the start, read `.agent_memory.json` from the repository root if present. Treat it as advisory memory for verified false positives, effective strategies, command quirks, failed assumptions, and project idiosyncrasies. Use it to avoid repeating past mistakes, but validate entries against current source before relying on them.

Prioritize correctness over speed. Inspect repository layout, git status, instruction files, manifests, lockfiles, CI configs, scripts, and docs before editing. Use existing package managers and project conventions. Distinguish source code from generated data, logs, build artifacts, caches, and runtime outputs.

Analyze backend, frontend, scripts/ops, security/config, tests, and dependencies. Run native dependency checks, syntax checks, lint, typecheck, tests, builds, audits, and smoke checks where safe. Rank issues as:

- P0: Security vulnerability, data loss, destructive failure, OOM/runaway failure risk.
- P1: Broken core runtime behavior, build failure, deployment blocker.
- P2: Silent failure, reliability issue, major typing or validation gap.
- P3: Style, docs, cleanup, minor maintainability.

Assign every finding a stable ID like `HP-SEC-001`, `HP-BUILD-001`, `HP-TEST-001`, or `HP-CONFIG-001`. Reuse IDs across reruns and baseline diffs for the same root cause. If requested, emit `project-health-pass.report.v1` JSON and validate it.

Maintain evidence coverage for repo map, source boundaries, native checks, runtime entrypoints, config, security, data safety, dependencies, CI/deploy ops, tests, and operability docs. Statuses are `pass`, `finding`, `unknown`, or `not-applicable`; unknown is never a pass.

Counter-review every P0/P1/P2 candidate before reporting or fixing it. Confirm probability, impact, realistic scenario, fix safety, and verification. Build a safest-first remediation backlog with blast radius, reversibility, verification, rollback, and status. Keep false positives and accepted risks visible as suppressions with evidence.

Fix verified P0/P1/P2 issues that are structurally safe now only in `fix-verified` mode. Avoid broad refactors. Preserve user changes. If a patch breaks a native test, build, typecheck, or startup path, pause and answer: what assumption was wrong, why did the native check reject it, and what hidden dependency or environment requirement was missed. Add or update focused tests for changed behavior. Stop when all identified P0/P1/P2 issues are resolved or documented as blocked.

Before the final response, append only verified, non-sensitive future-useful lessons to `.agent_memory.json` unless mode is `audit-only`. Never store secrets, credentials, personal data, or large logs.

Deliver: selected mode, scanned components, evidence coverage, problems grouped by P0-P3 with `HP-*` IDs, modified files with justification, commands/checks and results, memory read/update status, machine report status, suppressions/accepted risks, safest first batch, and remaining risks or blocked next steps.
