---
name: project-health-pass
description: Run self-improving repo health checks with audit/fix/diff modes, evidence coverage, counter-review, stable HP-* findings, native checks, and verified P0-P2 fixes.
---

# Project Health Pass

Run a rigorous repository-wide health pass, identify core reliability risks with stable `HP-*` finding IDs, optionally compare against a prior baseline, safely fix verified P0/P1/P2 issues, and report exactly what was scanned, changed, verified, and left blocked.

## Operating rules

- Preserve user changes. Do not revert unrelated dirty or untracked work.
- Do not run destructive operations, production writes, credentialed external actions, or live service mutations.
- Prefer the repository's existing package manager, lockfiles, scripts, tools, and conventions.
- Distinguish authored source from generated data, logs, build outputs, caches, vendored dependencies, and runtime artifacts before editing.
- Fix verified P0/P1/P2 problems that are structurally safe to alter now. Avoid broad refactors and speculative cleanup.
- Treat P3 findings as report-only unless they directly block verification or are trivial local cleanup caused by your own changes.
- Treat `.agent_memory.json` as advisory project-local memory. Validate entries against current code before relying on them.
- Never store secrets, credentials, private tokens, personal data, full environment dumps, or large logs in memory.
- Treat agent observations as hypotheses until verified by source trace, native command, test, or reproducible behavior.

## Modes

Select exactly one mode before scanning:

- `audit-only`: Use when the user asks for a report, score, review, read-only pass, baseline, or explicitly says not to edit. Do not modify source, tests, lockfiles, generated data, memory, or runtime state. If a machine-readable report is useful, include JSON inline or ask before writing it to the repo.
- `fix-verified`: Default when the user asks to fix, repair, unblock CI/deployments, or perform a health pass with remediation. Fix only verified P0/P1/P2 issues that are safely scoped.
- `baseline-diff`: Use when the user asks what changed since a previous health pass. Compare current findings against a prior `project-health-pass.report.v1` JSON report, keep matching IDs stable, and only fix issues if the user also requested remediation.

If the request is ambiguous, choose `audit-only` for safety. If the user asks for "fix" or "repair", choose `fix-verified`.

## Workflow

0. Select mode and retrieve project memory.
   - Pick `audit-only`, `fix-verified`, or `baseline-diff` using the mode rules above. Record the mode in the final report.
   - Check the repository root for `.agent_memory.json` before scanning. If a centralized memory path is documented in repo instructions, check that too.
   - If the bundled helper is available, run `python scripts/agent_memory.py read --repo <repo-root>` from the skill directory, or use the absolute path to this script. Otherwise inspect the JSON manually.
   - Extract verified false positives, effective strategies, project idiosyncrasies, command quirks, and failed assumptions. Inject them into your active plan as constraints.
   - If memory is missing or invalid, continue safely and record that in the final report.
   - In `audit-only`, do not write `.agent_memory.json`; instead report any proposed memory entries.

1. Map the project.
   - Inspect repository layout, git status, root and nested instruction files, manifests, lockfiles, package manager hints, CI configs, scripts, docs, environment examples, and generated-output locations.
   - Identify primary runtimes, entry points, deployment targets, test frameworks, and package-manager commands.
   - Build an initial source/generated/runtime boundary map before editing.
   - Create a scout snapshot: language/runtime, package managers, workspace layout, CI/deploy targets, source/generated/runtime boundaries, native commands, and obvious unavailable evidence.

2. Triage risks.
   - Rank findings with the severity rubric below.
   - Assign every finding a stable `HP-*` ID using the finding ID rules below.
   - Prioritize issues that can break core runtime behavior, corrupt data, fail deployment, hide errors, or create security exposure.
   - Separate confirmed problems from hypotheses. Verify before fixing unless the failure is already directly observable.
   - For every P0/P1/P2 candidate, run the counter-review gate before reporting or fixing it.

3. Analyze in slices.
   - Backend: startup paths, routing, persistence, validation, auth boundaries, background jobs, error handling.
   - Frontend: build path, routing, state, API contracts, asset loading, accessibility regressions that block use.
   - Scripts and ops: setup, dev, build, deploy, migration, seed, release, and CI scripts.
   - Security and config: secrets handling, default credentials, unsafe env fallbacks, CORS, SSRF/path traversal/destructive filesystem patterns.
   - Tests and dependencies: broken tests, missing focused coverage around changed behavior, lockfile/tool mismatches, vulnerable or abandoned critical packages.
   - Use parallel workers or subagents only when their work is read-only or isolated and safe.
   - Maintain an evidence coverage matrix using `pass`, `finding`, `unknown`, or `not-applicable` for each relevant surface. Unknown is not a pass.

4. Run native checks.
   - Run the repository's own install, lint, format-check, typecheck, test, build, audit, and smoke commands where available and safe.
   - Prefer read-only dependency/security checks. Do not upgrade dependencies unless needed to fix a verified P0/P1/P2 and consistent with the project.
   - Record skipped commands with the exact blocker.

5. Fix incrementally when mode is `fix-verified`.
   - Build a remediation backlog first. Each item needs a finding ID, fix summary, likely files touched, blast radius, reversibility, verification command, rollback idea, and status.
   - Choose the safest first batch by severity, evidence strength, reversibility, and testability. Prefer one coherent P0/P1/P2 root cause over mixing unrelated fixes.
   - Make the smallest coherent change that resolves a verified P0/P1/P2.
   - Add or update focused tests for changed behavior. If no framework exists, add the smallest useful smoke or validation script that fits project conventions.
   - Re-run the relevant checks after each meaningful slice. Broaden verification when a change touches shared contracts.
   - If a patch breaks a test, build, typecheck, or startup path, pause before a second fix and run the internal critique loop below.
   - In `audit-only` and read-only `baseline-diff`, stop at evidence-backed recommendations instead of patching.

6. Update project memory.
   - Before the final response, run a short retrospective over this pass.
   - Append only verified, future-useful lessons to `.agent_memory.json`: false positives, effective strategies, command quirks, failed assumptions, and project idiosyncrasies.
   - Prefer the helper: `python scripts/agent_memory.py append --repo <repo-root> --category <category> --summary "<short rule>" --details "<why>" --evidence "<check or file>" --action "<future behavior>"`.
   - If writing memory would be unsafe, blocked, or unwanted by repo policy, skip it and report the exact reason.
   - Never update memory in `audit-only` unless the user explicitly approved that write.

7. Deliver the report.
   - Summarize components scanned.
   - Group problems strictly by P0, P1, P2, P3.
   - List modified files with precise justification.
   - List commands/checks run and their result.
   - Document remaining risks, structural debt, and blocked items with exact next steps.
   - Include whether project memory was read and updated.
   - Include the selected mode and the JSON report path/status if one was produced.
   - Include coverage unknowns and the safest remaining next step when not all P0/P1/P2 items were fixed.

## Evidence coverage

Use this matrix to avoid shallow "looks fine" reports. Mark each surface:

- `pass`: Checked with concrete evidence and no material finding.
- `finding`: At least one `HP-*` finding exists for this surface.
- `unknown`: Relevant, but evidence was missing, blocked, too expensive, or unsafe to collect.
- `not-applicable`: Reasonably irrelevant for this repo, with a short reason.

Default surfaces:

- `repo_map`: layout, languages, package managers, workspaces, instructions.
- `source_boundaries`: source vs generated vs runtime/cache/vendor outputs.
- `native_checks`: install, lint, typecheck, test, build, audit, smoke commands.
- `runtime_entrypoints`: app/server/worker/CLI startup and critical paths.
- `configuration`: env examples, unsafe defaults, feature flags, CORS, deployment config.
- `security`: secrets, auth/authz, injection/path traversal/destructive operation risks.
- `data_safety`: migrations, destructive writes, backups, persistence lifecycle.
- `dependency_health`: lockfiles, package-manager mismatch, known vulnerabilities.
- `ci_deploy_ops`: CI, Docker, deploy/release scripts, smoke checks.
- `test_safety`: broken/flaky tests and missing regression coverage for fixed behavior.
- `docs_operability`: setup/deploy docs that affect reliable operation.

If critical surfaces are `unknown`, do not imply the repo is healthy. Say what exact evidence would close the gap.

## Counter-review gate

Before surfacing or fixing P0/P1/P2 findings, verify serious findings yourself. Agent/subagent output is a lead, not a conclusion.

For each serious candidate answer:

1. Probability: what command, file trace, test, or runtime behavior proves it can happen?
2. Impact: what breaks, leaks, corrupts, or blocks deployment?
3. Scenario: what realistic user, operator, CI, or attacker path reaches it?
4. Fix safety: what files change, what is the blast radius, and how is rollback done?
5. Verification: what native check proves the fix or proves the risk is real?

If evidence is missing, mark the surface `unknown` or the item as an observation. Do not inflate it into a P0/P1/P2 finding.

## Suppressions and accepted risk

Reviewed false positives and accepted risks must stay visible.

- Mark suppressions as `false-positive` only with a reason and evidence.
- Mark `accepted-risk` only when the risk is real but intentionally deferred or owned.
- Do not suppress a finding only because it is noisy, hard, or inconvenient.
- Re-check suppressions during `baseline-diff`; stale suppressions should become findings again.

## Finding IDs and machine reports

Use stable IDs for every finding. They make reports diffable, allow suppressions, and prevent the same issue from being renamed every run.

ID format: `HP-<AREA>-<NNN>`, where `NNN` is a zero-padded sequence within the area.

Areas:

- `HP-SEC-*`: security, secrets, auth, authorization, injection, unsafe data exposure.
- `HP-DATA-*`: data loss, migrations, destructive filesystem/database behavior, backup/restore risk.
- `HP-BUILD-*`: install, build, packaging, bundling, lockfile, compiler, or deployment artifact failure.
- `HP-RUN-*`: startup, routing, critical path crash, process lifecycle, background job failure.
- `HP-TEST-*`: broken tests, absent critical regression tests, flaky core verification.
- `HP-CONFIG-*`: environment, unsafe defaults, CORS, feature flags, config drift.
- `HP-DEP-*`: vulnerable, missing, mismatched, abandoned, or incorrectly pinned dependencies.
- `HP-OPS-*`: CI, deploy scripts, release scripts, Docker, infra, monitoring, smoke checks.
- `HP-TYPE-*`: type contracts, schema validation, API/client mismatch, serialization.
- `HP-PERF-*`: OOM, runaway loops, severe performance/resource risks.
- `HP-DOCS-*`: docs or instruction drift that can break setup, deploy, or operations.

Rules:

- Reuse an existing ID for the same root cause across a baseline diff or rerun.
- Use one ID per root cause, not per repeated symptom.
- Keep the ID stable when status changes from `open` to `fixed`, `blocked`, `accepted-risk`, or `false-positive`.
- Mark false positives explicitly instead of deleting them from machine-readable reports.
- Do not assign IDs to vague suspicions; first gather evidence or report the item as an unconfirmed observation outside the finding list.

When the user asks for a saved artifact, baseline diff, CI handoff, or machine-readable report, emit `project-health-pass.report.v1` JSON. Prefer the helper:

```bash
python scripts/health_report.py template --repo <repo-root> --mode <mode> --out <report.json>
python scripts/health_report.py validate --report <report.json>
python scripts/health_report.py diff --old <old-report.json> --new <new-report.json>
```

The report JSON shape is:

```json
{
  "schema": "project-health-pass.report.v1",
  "skill": "project-health-pass",
  "version": "0.4.1",
  "mode": "fix-verified",
  "repo": "repo-name-or-path",
  "generated_at": "2026-07-04T00:00:00Z",
  "repo_map": {
    "primary_languages": ["TypeScript"],
    "package_managers": ["pnpm"],
    "entry_points": ["src/server.ts"],
    "ci": [".github/workflows/ci.yml"],
    "source_boundaries": {"source": ["src"], "generated": ["src/generated"], "runtime": ["dist"]}
  },
  "coverage": [
    {
      "surface": "native_checks",
      "status": "finding",
      "evidence": ["pnpm build failed before HP-BUILD-001"],
      "notes": ""
    }
  ],
  "summary": {"status": "findings", "p0": 0, "p1": 1, "p2": 2, "p3": 0},
  "findings": [
    {
      "id": "HP-BUILD-001",
      "severity": "P1",
      "title": "Build fails because generated client is stale",
      "status": "fixed",
      "locations": ["src/api/client.ts:42"],
      "evidence": ["npm run build failed before fix and passed after regeneration"],
      "recommendation": "Regenerate the API client after endpoint schema changes.",
      "verification": ["npm run build"]
    }
  ],
  "backlog": [
    {
      "finding_id": "HP-BUILD-001",
      "priority": 1,
      "fix_summary": "Regenerate API client and add build verification.",
      "blast_radius": "low",
      "reversibility": "high",
      "verification": ["npm run build"],
      "rollback": "Revert regenerated client file.",
      "status": "done"
    }
  ],
  "suppressions": [],
  "checks": [{"command": "npm run build", "result": "passed", "notes": ""}],
  "changed_files": [{"path": "src/api/client.ts", "reason": "Regenerated stale API client"}],
  "memory": {"read": ".agent_memory.json", "updated": ".agent_memory.json"},
  "remaining": []
}
```

## Dynamic learning loop

### Phase 0: Memory retrieval

- Load `.agent_memory.json` at the start of every run.
- Use memory entries to avoid repeated false positives, preserve known delicate code paths, and run repo-specific commands correctly.
- Ignore stale or contradicted entries after verifying against current source and checks.

### Phase 4a: Internal critique loop

When a patch causes a native check failure, answer these before editing again:

1. What assumption did I make about this module, type interface, runtime, or dependency?
2. Why did the native build/test/type system reject it?
3. Is there a hidden dependency, generated contract, lifecycle ordering, or environment requirement I missed?

Only then formulate the corrected patch. If the original change is wrong and no safe correction is clear, stop and report the blocker instead of guessing.

### Phase 5a: Meta-evaluation and ledger update

At the end, write concise lessons into `.agent_memory.json` when they are:

- Verified by a command result, test, source trace, or user correction.
- Specific enough to change future behavior.
- Safe to store in the repository.

Do not write vague preferences, unverified suspicions, secrets, or large diagnostic output.

## Memory ledger shape

Store memory at the target repository root:

```json
{
  "skill": "project-health-pass",
  "version": "0.4.1",
  "entries": [
    {
      "category": "command_quirk",
      "summary": "Set ENV_VAR_X=1 before npm test",
      "details": "The custom test runner skips integration setup without this variable.",
      "evidence": "npm test failed without it and passed with it",
      "action": "Run ENV_VAR_X=1 npm test for future health passes.",
      "created_at": "2026-07-04T00:00:00Z"
    }
  ]
}
```

Supported categories: `false_positive`, `effective_strategy`, `project_quirk`, `command_quirk`, `failed_assumption`.

## Severity rubric

- P0: Security vulnerability, data loss, destructive operation risk, OOM or runaway failure risk.
- P1: Broken core runtime behavior, build failure, deployment blocker, migration failure, critical path crash.
- P2: Silent failure, reliability issue, major validation/typing gap, flaky core workflow, missing guard around important edge case.
- P3: Style, lint-only issue, docs cleanup, minor maintainability, non-blocking debt.

## Fix policy

- Fix P0/P1/P2 issues when the cause is verified and the change is safely scoped.
- Report but do not chase P3 issues once core health is verified.
- Do not change generated or runtime data unless required to make a safe source fix or regenerate deterministic artifacts from source.
- Do not mask failing checks by weakening tests, suppressing diagnostics, deleting coverage, or broadening ignores without a concrete root-cause explanation.
- If a fix requires credentials, external production access, destructive migration, or a dependency upgrade with high blast radius, stop that fix and document the safest next step.

## Report template

Use this shape for the final response:

```markdown
Mode: <audit-only | fix-verified | baseline-diff>
Scanned: <components, tools, configs, tests>

P0:
- <HP-AREA-NNN finding or "None">

P1:
- <HP-AREA-NNN finding or "None">

P2:
- <HP-AREA-NNN finding or "None">

P3:
- <HP-AREA-NNN finding or "None">

Coverage:
- <surface>: <pass/finding/unknown/not-applicable> - <evidence or missing evidence>

Changed:
- <file>: <why>

Checks:
- `<command>`: <result>

Memory:
- Read: <yes/no/path/status>
- Updated: <yes/no/path/status>

Machine Report:
- <path/status or "Not requested">

Safest First Batch:
- <finding IDs/status or "None">

Suppressions:
- <false-positive/accepted-risk IDs or "None">

Remaining:
- <risk/debt/blocker and exact next step>
```

## Available scripts

- `scripts/agent_memory.py`: Read and append safe entries to a repository `.agent_memory.json` ledger. It deduplicates entries by category and summary, redacts common secret-looking values, and writes JSON atomically.
- `scripts/health_report.py`: Create, validate, and diff optional `project-health-pass.report.v1` JSON reports with stable `HP-*` finding IDs.

The helper preserves unknown top-level fields, so it can coexist with ledgers that use separate arrays such as `false_positives`, `effective_strategies`, or `project_idiosyncrasies`.
