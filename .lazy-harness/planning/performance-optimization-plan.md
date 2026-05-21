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

## 2026-05-21 Phase 0 implementation

Implemented measurement-only instrumentation:

- `.lazy-harness/hooks/lifecycle/on-response-completed.sh` now appends timing rows for `route-telemetry`, every lifecycle helper, and `hook-total`.
- `.lazy-harness/scripts/hook-timing-summary.py` summarizes timing rows by component.
- `.lazy-harness/bin/lazy hook-timings` exposes the summary.
- `.lazy-harness/spec/platform/hook-performance-measurement.md` defines the measurement-only contract and safety constraints.

Safety notes:

- Helper order is unchanged.
- Gate output behavior is unchanged.
- Timing errors are best-effort and swallowed.
- Timing data contains component names, durations, exit codes, and emitted flags only; it does not store raw user messages or payload bodies.
- `LAZY_HOOK_TIMING=0` disables timing logs, and `LAZY_HOOK_TIMING_LOG` can redirect logs for tests/dogfood.

Next slice remains Phase 1, but only after timing data is reviewed.

## 2026-05-21 Phase 0 dogfood result

After commit `6715146`, synced both confirmed hosts:

- `/home/lazydino/dev/medivance`
- `/home/lazydino/dev/medivance-pwa`

Validation:

- Both hosts synced successfully to `6715146b2fcdd7c56b96c7682491cc0f88dbb056`.
- Both hosts passed `python3 .lazy-harness/scripts/doctor.py --profile smoke --scope host`.
- A synthetic `response.completed` payload with `LAZY_HOOK_TIMING_LOG=/tmp/...` produced 18 timing rows on each host.
- `lazy hook-timings --log /tmp/... --format=json` summarized the timing rows successfully on each host.
- The slowest component in the single synthetic run was `hook-total`, as expected for aggregate timing.

Dogfood conclusion:

- Phase 0 measurement works in source, Medivance, and Medivance PWA without changing hook behavior.
- Next step should be to collect real interactive timing samples before implementing Phase 1 fast-path.

## 2026-05-21 Phase 1 conservative fast-path

Timing samples showed that no-op/read-only hook runs still spend time invoking helpers that immediately parse the payload and discover there were no writes. Phase 1 implements only the safest fast-path:

- If `recent_tool_calls` is present and every call is a known read-only tool, skip helpers whose logic is exclusively write-triggered.
- If `recent_tool_calls` is missing, malformed, contains `bash`, `batch`, `apply_patch`, `edit`, `write`, or any unknown tool, run the full helper set.
- BDD and all natural-language/record discipline helpers remain enabled even on read-only payloads.

Skipped only on known read-only payloads:

- `check-layer-impact.sh`
- `check-ddd-trigger.sh`
- `check-ssot-trigger.sh`
- `check-layer-completeness.sh`
- `check-tdd-cross-verify.sh`
- `check-affected-tests.sh`

Safety validation added:

- Read-only fixture proves those write-only helpers are absent from timing components.
- Unknown `bash` fixture proves full fallback includes all write-only helpers.
- Missing `recent_tool_calls` fixture proves full fallback includes all write-only helpers.

This is not the single orchestrator phase; it is a constrained fast-path inside the existing helper loop.

Host dogfood after commit `8438cc5`:

- Synced `/home/lazydino/dev/medivance`; host smoke doctor passed.
  - Known read-only payload timing components: 12 rows.
  - Unknown `bash` payload timing components: 18 rows.
  - Read-only payload skipped all 6 write-only helpers.
  - Unknown payload included all 6 write-only helpers.
- Synced `/home/lazydino/dev/medivance-pwa`; host smoke doctor passed.
  - Known read-only payload timing components: 12 rows.
  - Unknown `bash` payload timing components: 18 rows.
  - Read-only payload skipped all 6 write-only helpers.
  - Unknown payload included all 6 write-only helpers.

Dogfood conclusion:

- Conservative read-only fast-path reduces no-op/read-only helper invocations without weakening unknown/write payload coverage.
- Next optimization should be based on fresh `lazy hook-timings` samples after this fast-path has run during normal interactive usage.

## 2026-05-21 Phase 2 shadow orchestrator

Implemented the first Phase 2 slice without replacing the production hook:

- Added `.lazy-harness/scripts/lifecycle-check.py`.
- Added `.lazy-harness/bin/lazy lifecycle-check`.
- The shadow orchestrator parses payload once, applies the same Phase 1 fast-path selection, runs existing helpers in production order, stops at first helper output, and emits JSON with selected/skipped helpers plus `firstOutput`/`injectJson`.
- Production `on-response-completed.sh` is unchanged in this slice.

Parity coverage added:

- TDD cross-verify STOP output parity: shadow first output helper and STOP body match the production helper expectation.
- Aftershock re-analysis STOP output parity: shadow first output helper and STOP body match the production helper expectation.
- Existing Phase 1 fixtures still protect read-only skip and unknown full fallback.

Phase 3 replacement remains forbidden until more shadow fixtures cover natural-language BDD, option-gate discipline, record-before-session-history, and no-output cases under host dogfood.

Host dogfood after commit `d6d5527`:

- Synced `/home/lazydino/dev/medivance`; host smoke doctor passed.
  - `lazy lifecycle-check` on known read-only payload: `fastPathReason=read-only-fast-path`, `selectedHelpers=10`, `skippedHelpers=6`, `outputEmitted=false`.
- Synced `/home/lazydino/dev/medivance-pwa`; host smoke doctor passed.
  - `lazy lifecycle-check` on known read-only payload: `fastPathReason=read-only-fast-path`, `selectedHelpers=10`, `skippedHelpers=6`, `outputEmitted=false`.

Dogfood conclusion:

- The shadow CLI works in both installed hosts and mirrors Phase 1 helper selection.
- It is still not a production hook replacement. Next Phase 2 work should add more shadow parity fixtures before Phase 3.

## 2026-05-21 Phase 2 parity expansion

Expanded shadow parity coverage in `check_lifecycle_hook_integration`:

- BDD natural-language scenario STOP parity.
- Option-gate discipline STOP parity.
- Record-before-session-history STOP parity.
- Read-only no-output parity.
- Existing TDD cross-verify and aftershock STOP parity remain covered.

Validation:

- Source self-test passed with all expanded fixtures.
- Source smoke doctor passed.

Replacement status:

- Phase 3 is still blocked. The next safe step is either more host dogfood with real payload samples or a shadow-vs-legacy batch fixture runner before any production hook replacement.

Host dogfood after commit `dc4fbbf`:

- Synced `/home/lazydino/dev/medivance`; host smoke doctor passed.
  - `lazy lifecycle-check` BDD payload produced `firstOutputHelper=.lazy-harness/hooks/lifecycle/helpers/check-bdd-trigger.sh`, `outputEmitted=true`.
- Synced `/home/lazydino/dev/medivance-pwa`; host smoke doctor passed.
  - `lazy lifecycle-check` BDD payload produced `firstOutputHelper=.lazy-harness/hooks/lifecycle/helpers/check-bdd-trigger.sh`, `outputEmitted=true`.

Dogfood conclusion:

- Expanded Phase 2 parity fixtures hold in source, and BDD shadow output is reproducible in both installed hosts.
- Phase 3 remains blocked until a batch shadow-vs-legacy fixture runner compares more payloads automatically.

## 2026-05-21 Phase 2 batch parity runner

Implemented `.lazy-harness/scripts/lifecycle-parity-runner.py` and `.lazy-harness/bin/lazy lifecycle-parity`.

Behavior:

- Creates fresh temporary host copies per fixture.
- Runs production `on-response-completed.sh` and shadow `lifecycle-check` independently.
- Compares output presence, first STOP/reminder body, expected helper, and expected text.
- Supports `--fail-on-mismatch` for self-test/CI.

Initial fixture suite:

- read-only no-output
- BDD natural-language STOP
- option-gate discipline STOP
- record-before-session-history STOP
- TDD cross-verify STOP
- aftershock STOP

Validation:

- `lazy lifecycle-parity --format=json --fail-on-mismatch` passed 6/6 fixtures locally.

Replacement status:

- Phase 3 remains blocked until this runner is dogfooded on installed hosts and additional real payload samples are added.


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
