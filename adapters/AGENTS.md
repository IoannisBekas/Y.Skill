# Project Health Pass

Use these instructions only when the requested task is a deep project-wide health pass, repository health check, reliability sweep, build/test/lint/typecheck triage, dependency/security audit, deployment blocker investigation, or P0/P1/P2 remediation.

- Preserve user changes and never revert unrelated dirty or untracked files.
- Select exactly one mode before scanning: `audit-only` for read-only reports, `fix-verified` for safe remediation, or `baseline-diff` for comparing against a prior `project-health-pass.report.v1` JSON report.
- At the start, read `.agent_memory.json` in the repository root if present. Treat it as advisory memory containing verified false positives, command quirks, effective strategies, failed assumptions, and project idiosyncrasies.
- Inspect repository layout, git status, instruction files, manifests, lockfiles, CI configs, scripts, and docs before editing.
- Distinguish source code from generated data, logs, build artifacts, caches, vendored dependencies, and runtime outputs.
- Use the existing package manager, lockfiles, scripts, and project conventions.
- Run native dependency checks, syntax checks, lint, typecheck, tests, builds, audits, and smoke checks where available and safe.
- Rank findings as P0 security/data loss/destructive/OOM, P1 runtime/build/deploy blocker, P2 silent failure/reliability/major typing or validation gap, P3 cleanup/debt. Assign every finding a stable ID like `HP-SEC-001`, `HP-BUILD-001`, or `HP-TEST-001`.
- Maintain an evidence coverage matrix: `pass`, `finding`, `unknown`, or `not-applicable` for repo map, source boundaries, native checks, runtime entrypoints, config, security, data safety, dependencies, CI/deploy ops, tests, and operability docs.
- Counter-review every P0/P1/P2 candidate before reporting or fixing it: prove probability, impact, realistic scenario, fix safety, and verification.
- Build a safest-first remediation backlog with finding ID, fix summary, files touched, blast radius, reversibility, verification, rollback, and status.
- Fix verified P0/P1/P2 issues that are structurally safe only in `fix-verified` mode. Avoid broad refactors and speculative cleanup.
- If a patch breaks a test, build, typecheck, or startup path, pause and answer: what assumption was wrong, why did the native check reject it, and what hidden dependency or environment requirement was missed.
- Add or update focused tests for changed behavior.
- Before the final response, append only verified, non-sensitive future-useful lessons to `.agent_memory.json` unless mode is `audit-only`; never store secrets, credentials, personal data, or large logs.
- If the user asks for a machine-readable report, emit `project-health-pass.report.v1` JSON and validate it when possible.
- Final response must include mode, scanned components, evidence coverage, severity-grouped `HP-*` findings, modified files with justification, commands and results, memory read/update status, machine report status, suppressions/accepted risks, safest first batch, and remaining risks or blocked next steps.
