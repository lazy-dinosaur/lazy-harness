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

## Safety invariant

Performance work is allowed only if it preserves or improves harness protection. Faster but less protective is a regression.

Non-negotiables:

- No existing STOP/gate may disappear without an explicit test and canonical record change.
- No helper may skip work solely because a request "looks simple"; skip decisions must be derived from payload/tool/file facts.
- Fast-path must be conservative: unknown payload shape falls back to the current full helper path.
- New orchestrator output must be compared against legacy helper output in shadow mode before replacing it.
- Route telemetry may move async/sampled only after gate-critical checks are proven independent from telemetry.
- Caches must be content-addressed by `HEAD`, payload hash, touched-path hash, and relevant state file mtimes. Stale cache must fall back to full checks.

## Implementation phases

### Phase 0 — measure only

Goal: know where time is spent before changing behavior.

Tasks:

1. Add optional timing logs around `on-response-completed.sh` and each lifecycle helper.
2. Record helper name, elapsed milliseconds, exit code, and whether output was emitted.
3. Keep timing logs out of the user-visible STOP path.
4. Add a small summarizer for p50/p90/p99 helper timings.

Validation:

- Existing self-test and doctor pass.
- Timing can be disabled or sampled.
- No hook decision changes.

### Phase 1 — conservative fast-path

Goal: skip only helpers that are provably irrelevant for the current payload.

Skip examples:

- If `recent_tool_calls` has no write/edit/apply/commit/DB/email/release tools, skip implementation-map/layer-completeness helpers that only protect writes.
- If no `.lazy-harness` paths were touched, skip rule-placement/canonical-record mutation helpers that only inspect record writes.
- If no commit-like action occurred, skip fix-regression post-commit checks.

Fallback rule:

- If payload parsing fails or any expected payload field is missing, run the full current helper set.

Validation:

- Golden fixtures prove fast-path output equals full-helper output for no-op/read-only/write/commit payloads.
- Add negative fixtures proving ambiguous payloads do not skip.

### Phase 2 — shadow orchestrator

Goal: build one orchestrator without replacing the legacy path yet.

Tasks:

1. Create `lifecycle-check.py` or `lifecycle-check.ts` that parses payload once and computes shared state once.
2. Run it in shadow mode from self-test fixtures and optionally local hook debug mode.
3. Compare legacy helper decisions vs orchestrator decisions.

Validation:

- Shadow report must match legacy STOP/no-STOP decisions across existing lifecycle fixtures.
- Any mismatch blocks replacement and creates a TDD regression record.

### Phase 3 — replace sequential helper shell loop

Goal: make the orchestrator the primary path only after shadow parity.

Tasks:

1. Replace helper loop with orchestrator for equivalent checks.
2. Keep a debug flag to run legacy helpers for comparison.
3. Preserve helper scripts as reusable rule implementations or test fixtures until confidence is high.

Validation:

- Full self-test, doctor, and focused lifecycle fixture suite pass.
- Before/after response hook timing improves on no-op/read-only payloads.
- Commit/write payload protection remains identical.

### Phase 4 — indexes and cache

Goal: reduce repeated JSONL/full-file scans after orchestration is stable.

Tasks:

1. Add generated indexes under `.lazy-harness/generated/` only.
2. Define invalidation by source JSONL mtime/hash.
3. Add fingerprint cache for repeated identical STOP states.

Validation:

- Cache disabled path still passes all checks.
- Cache miss/full scan remains the fallback for any uncertainty.

## Planned first slice

Implement Phase 0 only:

- Add timing instrumentation to response lifecycle hook.
- Add a timing summary command or script.
- Dogfood on Medivance and Medivance PWA.
- Do not change skip/orchestration behavior in this first slice.

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
