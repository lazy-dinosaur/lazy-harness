# Lazy CLI Entrypoint

Status: accepted
Layer: SDD
Date: 2026-05-16
Related SDD: `.lazy-harness/spec/platform/host-root-resolution.md`
Related SDD: `.lazy-harness/spec/platform/package-health-generate-remediation.md`
Related ADR: `.lazy-harness/decisions/0022-framework-owned-doctor-and-lazy-test.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Applies when:
  - reproducing, diagnosing, or recommending lazy-harness validation/self-test for a host
  - a doc or handoff mentions `bun run lazy:test`/`lazy:doctor` package scripts
- Must:
  - use the `.lazy-harness/bin/lazy` dispatcher (version/check/validate/test/doctor) as the current entrypoint
  - prefer this SDD and current docs over historical `lazy:test`/`lazy:doctor` references
  - treat `lazy check` as fast static validation only, not equivalent to `lazy test`
- Must not:
  - run, recommend, or diagnose with stale `lazy:test`/`lazy:doctor` package-script names
  - diagnose a missing `package.json` `lazy:test` script as a lazy-harness failure
- Record completion:
  - changes to the canonical CLI surface or the stale-name guard update this SDD and self-test
- Related records:
  - `.lazy-harness/spec/platform/host-root-resolution.md`
  - `.lazy-harness/spec/platform/package-health-generate-remediation.md`
  - `.lazy-harness/spec/platform/bounded-validation-governor.md`
  - `.lazy-harness/decisions/0022-framework-owned-doctor-and-lazy-test.md`

## Purpose

The canonical executable entrypoint for installed hosts is the per-host dispatcher:

```bash
.lazy-harness/bin/lazy test
.lazy-harness/bin/lazy check
.lazy-harness/bin/lazy validate
.lazy-harness/bin/lazy doctor --profile smoke
.lazy-harness/bin/lazy record-audit --format md
.lazy-harness/bin/lazy graph-hygiene --format md
.lazy-harness/bin/lazy hook-timings --format md
.lazy-harness/bin/lazy lifecycle-check --format json
.lazy-harness/bin/lazy lifecycle-parity --format json
.lazy-harness/bin/lazy version
```

Older package-script names such as `bun run lazy:test`, `bun run lazy:doctor`, `lazy:test`, and `lazy:doctor` are historical references and must not be used for current diagnosis or reproduction.

## Why this matters

Dogfooding showed agents could read stale handoff or ADR text, look for `package.json` scripts, conclude `lazy:test` does not exist, and stop before invoking the real CLI. That is wrong because package scripts are no longer the current source of truth for host validation.

## Contract

1. Use `.lazy-harness/bin/lazy version` to confirm the host root and lazy root.
2. Use `.lazy-harness/bin/lazy check` for fast changed-file static validation during edit loops.
3. Use `.lazy-harness/bin/lazy validate` to choose bounded fast/standard/release validation plans without accidentally multiplying full or release-grade checks.
4. Use `.lazy-harness/bin/lazy test` as the primary host/framework full-regression self-test wrapper.
5. Use `.lazy-harness/bin/lazy doctor --profile smoke` for the smoke doctor.
6. If package health fails because generated artifacts are stale, the doctor may run one safe generate remediation and retry before reporting failure.
7. Do not diagnose missing `package.json` `lazy:test` scripts as a lazy-harness failure.
8. If historical docs mention `bun run lazy:test`, prefer this SDD, README current sections, and `.lazy-harness/bin/lazy` usage.
9. Do not describe `.lazy-harness/bin/lazy check` as equivalent to `.lazy-harness/bin/lazy test`; it is a fast static tier only.

## Historical references

Historical ADRs may still mention `bun run lazy:test` because that was the old executable shape at the time. Those references should not be rewritten as history, but active docs and agent behavior must use the current dispatcher.

## Lifecycle helper behavior

`check-lazy-cli-entrypoint.sh` runs from `on-response-completed.sh`.

It emits STOP when an assistant response/tool trace appears to execute, recommend, or diagnose with stale `lazy:test`/`lazy:doctor` package-script names instead of the canonical `.lazy-harness/bin/lazy` dispatcher.

It allows corrective explanations that explicitly call the old form stale/deprecated or say not to use it.

## Discovery capture

- DDD: none.
- SDD: this contract defines the current CLI invocation interface.
- BDD: user-visible behavior is that agents run the actual per-host lazy CLI and do not chase missing package scripts.
- TDD: self-test covers stale CLI block and canonical CLI pass; D07 covers generate remediation behavior through doctor package health.
- ADR: ADR 0022 remains historical context; this SDD clarifies the current interface.
- SSOT: none beyond this accepted SDD.
- Planning: none.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/spec/platform/lazy-cli-entrypoint.md` — this SDD contract.
  - `.lazy-harness/bin/lazy` — canonical per-host dispatcher.
  - `.lazy-harness/scripts/validation-governor.py` — bounded validation plan runner exposed as `lazy validate`.
  - `.lazy-harness/hooks/lifecycle/helpers/check-lazy-cli-entrypoint.sh` — response-completed guard.
  - `.lazy-harness/hooks/pre-push.sh` — git pre-push gate using the canonical CLI, never package script `lazy:test`.
  - `.lazy-harness/hooks/lifecycle/on-response-completed.sh` — invokes the guard.
  - `.lazy-harness/scripts/self-test.py` — regression fixtures.
  - `.lazy-harness/scripts/lazy-check.py` — fast changed-file static validator.
  - `.lazy-harness/scripts/doctor.py` — package health generate remediation and retry.
  - `README.md`, `.lazy-harness/framework/framework-contract.md`, `.lazy-harness/handoff/00-current-state.md` — current docs using canonical command.
- Key symbols:
  - `check_lazy_cli_entrypoint_helper` (`.lazy-harness/scripts/self-test.py`) — verifies stale CLI block/canonical pass.
  - `check_pre_push_uses_canonical_lazy_cli` (`.lazy-harness/scripts/self-test.py`) — verifies pre-push does not call stale package scripts.
  - `.lazy-harness/bin/lazy version` — root diagnostic command.
  - `.lazy-harness/bin/lazy check` — fast static changed-file validation command.
  - `.lazy-harness/bin/lazy validate` — bounded validation governor for fast/standard/release plans.
  - `.lazy-harness/bin/lazy record-audit` — read-only host record dashboard dispatcher to `.lazy-harness/scripts/record-audit.ts`.
  - `.lazy-harness/bin/lazy graph-hygiene` — read-only knowledge graph lint dispatcher to `.lazy-harness/scripts/graph-hygiene.ts`.
  - `.lazy-harness/bin/lazy hook-timings` — read-only response hook timing summary dispatcher to `.lazy-harness/scripts/hook-timing-summary.py`.
  - `.lazy-harness/bin/lazy lifecycle-check` — shadow response.completed lifecycle orchestrator dispatcher to `.lazy-harness/scripts/lifecycle-check.py`.
  - `.lazy-harness/bin/lazy lifecycle-parity` — batch parity runner dispatcher to `.lazy-harness/scripts/lifecycle-parity-runner.py`.
- Flow:
  1. Agent needs to reproduce lazy-harness validation or inspect accumulated host records.
  2. Agent runs `.lazy-harness/bin/lazy version` if root is uncertain.
  3. Agent runs `.lazy-harness/bin/lazy check`, `validate`, `test`, `doctor`, `record-audit`, `graph-hygiene`, `hook-timings`, `lifecycle-check`, or `lifecycle-parity` depending on whether it needs fast static validation, bounded validation plan selection, full regression validation, health diagnosis, record-quality summary, graph lint details, performance measurement summary, response-hook shadow data, or batch shadow-vs-legacy parity.
  4. Hook blocks stale package-script diagnosis before it becomes final guidance.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - `bash -n .lazy-harness/hooks/lifecycle/helpers/check-lazy-cli-entrypoint.sh`
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/host-root-resolution.md`
  - SDD: `.lazy-harness/spec/platform/package-health-generate-remediation.md`
  - SDD: `.lazy-harness/spec/platform/bounded-validation-governor.md`
  - ADR: `.lazy-harness/decisions/0022-framework-owned-doctor-and-lazy-test.md`
- Machine index:
  - graph ids: `kg_sdd_lazy_cli_entrypoint`
  - generated index key: `pending until implementation-index generator exists`
