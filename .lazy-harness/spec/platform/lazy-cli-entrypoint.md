# Lazy CLI Entrypoint

Status: accepted
Layer: SDD
Date: 2026-05-16
Related SDD: `.lazy-harness/spec/platform/host-root-resolution.md`
Related SDD: `.lazy-harness/spec/platform/package-health-generate-remediation.md`
Related ADR: `.lazy-harness/decisions/0022-framework-owned-doctor-and-lazy-test.md`

## Purpose

The canonical executable entrypoint for installed hosts is the per-host dispatcher:

```bash
.lazy-harness/bin/lazy test
.lazy-harness/bin/lazy doctor --profile smoke
.lazy-harness/bin/lazy record-audit --format md
.lazy-harness/bin/lazy version
```

Older package-script names such as `bun run lazy:test`, `bun run lazy:doctor`, `lazy:test`, and `lazy:doctor` are historical references and must not be used for current diagnosis or reproduction.

## Why this matters

Dogfooding showed agents could read stale handoff or ADR text, look for `package.json` scripts, conclude `lazy:test` does not exist, and stop before invoking the real CLI. That is wrong because package scripts are no longer the current source of truth for host validation.

## Contract

1. Use `.lazy-harness/bin/lazy version` to confirm the host root and lazy root.
2. Use `.lazy-harness/bin/lazy test` as the primary host/framework self-test wrapper.
3. Use `.lazy-harness/bin/lazy doctor --profile smoke` for the smoke doctor.
4. If package health fails because generated artifacts are stale, the doctor may run one safe generate remediation and retry before reporting failure.
5. Do not diagnose missing `package.json` `lazy:test` scripts as a lazy-harness failure.
6. If historical docs mention `bun run lazy:test`, prefer this SDD, README current sections, and `.lazy-harness/bin/lazy` usage.

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
  - `.lazy-harness/hooks/lifecycle/helpers/check-lazy-cli-entrypoint.sh` — response-completed guard.
  - `.lazy-harness/hooks/pre-push.sh` — git pre-push gate using the canonical CLI, never package script `lazy:test`.
  - `.lazy-harness/hooks/lifecycle/on-response-completed.sh` — invokes the guard.
  - `.lazy-harness/scripts/self-test.py` — regression fixtures.
  - `.lazy-harness/scripts/doctor.py` — package health generate remediation and retry.
  - `README.md`, `.lazy-harness/framework/framework-contract.md`, `.lazy-harness/handoff/00-current-state.md` — current docs using canonical command.
- Key symbols:
  - `check_lazy_cli_entrypoint_helper` (`.lazy-harness/scripts/self-test.py`) — verifies stale CLI block/canonical pass.
  - `check_pre_push_uses_canonical_lazy_cli` (`.lazy-harness/scripts/self-test.py`) — verifies pre-push does not call stale package scripts.
  - `.lazy-harness/bin/lazy version` — root diagnostic command.
  - `.lazy-harness/bin/lazy record-audit` — read-only host record dashboard dispatcher to `.lazy-harness/scripts/record-audit.ts`.
- Flow:
  1. Agent needs to reproduce lazy-harness validation or inspect accumulated host records.
  2. Agent runs `.lazy-harness/bin/lazy version` if root is uncertain.
  3. Agent runs `.lazy-harness/bin/lazy test`, `doctor`, or `record-audit` depending on whether it needs validation, health diagnosis, or record-quality summary.
  4. Hook blocks stale package-script diagnosis before it becomes final guidance.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - `bash -n .lazy-harness/hooks/lifecycle/helpers/check-lazy-cli-entrypoint.sh`
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/host-root-resolution.md`
  - SDD: `.lazy-harness/spec/platform/package-health-generate-remediation.md`
  - ADR: `.lazy-harness/decisions/0022-framework-owned-doctor-and-lazy-test.md`
- Machine index:
  - graph ids: `kg_sdd_lazy_cli_entrypoint`
  - generated index key: `pending until implementation-index generator exists`
