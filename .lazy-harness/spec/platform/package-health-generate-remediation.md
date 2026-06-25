# Package Health Generate Remediation

Status: accepted
Layer: SDD
Date: 2026-05-16
Related SDD: `.lazy-harness/spec/platform/lazy-cli-entrypoint.md`
Related ADR: `.lazy-harness/decisions/0022-framework-owned-doctor-and-lazy-test.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Applies when:
  - `lazy test` / `lazy doctor --profile full` package-health typecheck fails on suspected generated-artifact drift
  - a schema/source branch changed but generated client/artifacts are stale
- Must:
  - run one safe generate command (documented precedence) and rerun typecheck once before reporting failure
  - report `ok after generate remediation` on retry pass, else report the attempted remediation and retry diagnostics
- Must not:
  - repair arbitrary app code, run migrations/seed/destructive DB ops, or commit generated files
  - modify downstream project policy records from this framework validation behavior
- Record completion:
  - changes to D07 remediation precedence or the drift heuristic update this SDD and doctor self-test
- Related records:
  - `.lazy-harness/spec/platform/lazy-cli-entrypoint.md`
  - `.lazy-harness/spec/platform/host-root-resolution.md`
  - `.lazy-harness/decisions/0022-framework-owned-doctor-and-lazy-test.md`

## Purpose

`lazy test` / `lazy doctor --profile full` must not stop at the first app typecheck failure when the failure looks like generated-artifact drift. If the host exposes a safe generate command, the framework should run it once and retest before reporting failure.

This protects worktree and Prisma-style generated client flows where a schema/source branch changed but generated artifacts are stale.

## Contract

1. D07 package health still starts with `bun run typecheck:node` when `package.json` exists.
2. If typecheck fails and diagnostics suggest generated-artifact drift, D07 may run one generate remediation command.
3. Generate command precedence:
   - `bun run generate`
   - `bun run db:generate`
   - `bun run prisma:generate`
   - `bun run prisma:gen`
   - `bun x prisma generate` only when Prisma is detected in dependencies or diagnostics.
4. After successful generate remediation, D07 reruns `bun run typecheck:node` once.
5. If the retry passes, D07 is `ok` with `package health ok after generate remediation`.
6. If generate fails or retry still fails, D07 reports the attempted remediation and the retry diagnostics.
7. This is framework validation behavior only. It does not record host app changes or commit generated files.

## Non-goals

- Do not repair arbitrary app code drift.
- Do not run migrations, seed data, or destructive database operations.
- Do not modify downstream project policy records from this framework repo.

## Discovery capture

- DDD: none.
- SDD: this contract defines D07 remediation/retry behavior.
- BDD: user-visible validation now attempts the obvious generate step before stopping.
- TDD: self-test covers stale CLI guard; doctor full covers D07 ok/warn/fail classification. Future fixture can isolate generate retry if needed.
- ADR: no new trade-off beyond ADR 0022; D07 remains framework-owned package health.
- SSOT: none.
- Planning: none.

## Rule placement

- Rule: Lazy-harness validation should run safe generate remediation once before failing generated-artifact package health.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/package-health-generate-remediation.md`
- Why not AGENTS.md: This is executable validation behavior, not conversational grammar.
- Why not `.jcode`: This is framework behavior shared by all hosts, not a local Jcode preference.
- Confirmation: user-confirmed

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/spec/platform/package-health-generate-remediation.md` — this SDD contract.
  - `.lazy-harness/scripts/doctor.py` — D07 package health generate retry implementation.
  - `.lazy-harness/spec/platform/lazy-cli-entrypoint.md` — canonical CLI contract that invokes this behavior via `lazy test`/doctor.
- Key symbols:
  - `check_package_health` — D07 package health gate.
  - `find_generate_command` — safe generate command selection.
  - `should_try_generate` — generated-artifact drift heuristic.
  - `run_generate_remediation` — one-shot generate execution.
- Flow:
  1. D07 runs typecheck.
  2. If generated drift is suspected, D07 runs one generate command.
  3. D07 reruns typecheck once and reports final status with remediation details.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - `python3 .lazy-harness/scripts/doctor.py --profile smoke`
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/lazy-cli-entrypoint.md`
  - SDD: `.lazy-harness/spec/platform/host-root-resolution.md`
- Machine index:
  - graph ids: `kg_sdd_package_health_generate_remediation`
  - generated index key: `pending until implementation-index generator exists`
