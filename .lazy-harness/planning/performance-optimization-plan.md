# Performance Optimization Plan

Status: planned
Date: 2026-05-21
Source: user-requested next plan after graph source-only path work

## Context

The user noted that lazy-harness CLI/hook execution feels too slow. A parallel agent analysis identified the likely hot path as response lifecycle hooks rather than record registry size alone.

This is a planning record only. Do not start this implementation until the current graph source-only path slice is committed, pushed, and synced to hosts.

## Candidate bottlenecks

1. `on-response-completed.sh` runs many helper checks sequentially on every response.
2. Each helper reparses the response payload JSON.
3. Some helpers repeatedly run `git log`, `git diff`, `grep`, and file scans.
4. Route telemetry can pay a Bun cold-start cost through `task-router.ts` on every response.
5. JSONL registry/graph access is mostly grep/full-scan based.

## Proposed priority order

### P0 — hook fast-path

- If payload has no relevant `recent_tool_calls`, no `.lazy-harness` writes, and no commit-producing actions, skip most layer/placement/regression helpers.
- Skip fix/commit checks when the response is not after a commit-like tool call.

### P1 — single orchestrator

- Replace multiple shell helper invocations with one `lifecycle-check.ts` or `lifecycle-check.py` orchestrator.
- Parse payload once.
- Compute changed/touched files once.
- Query git state once.
- Share derived state with rule checks.

### P2 — registry indexes

- Generate `.lazy-harness/generated/regression-index.json` and similar small indexes.
- Use O(1) maps for fix-registry and graph lookups where possible.
- Update indexes on append rather than scanning full JSONL every hook run.

### P3 — avoid Bun cold start in response hook

- Run route telemetry async/background or sample it.
- Keep gate-critical checks in Python/bash or a long-lived daemon if needed.

### P4 — fingerprint cache

- Cache gate results by `(HEAD, payload_tool_call_hash, touched_paths_hash)`.
- Avoid repeated STOP recalculation for identical response/tool states.

## Acceptance criteria for future implementation

- Add timing instrumentation before refactor.
- Produce before/after timings for response hook on representative no-op, read-only, edit, and commit turns.
- Preserve existing self-test and doctor behavior.
- Do not weaken record-first, option-gate, queue-close, or layer completeness rules.

## Implementation map

Potential files to inspect next:

- `.lazy-harness/hooks/on-response-completed.sh`
- `.lazy-harness/scripts/task-router.ts`
- `.lazy-harness/scripts/*placement*`
- `.lazy-harness/scripts/*regression*`
- `.lazy-harness/logs/route-telemetry-debug.jsonl`

## Discovery capture

- SDD candidate: response lifecycle hook orchestration contract.
- TDD candidate: hook timing fixtures and regression tests.
- SSOT candidate: generated index storage location and invalidation rules.
- ADR candidate: single orchestrator vs independent helper scripts trade-off.
