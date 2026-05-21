# SDD — Hook Performance Measurement

Status: accepted
Date: 2026-05-21
Layer: SDD
Related: `.lazy-harness/planning/performance-optimization-plan.md`, `.lazy-harness/decisions/0016-lifecycle-hook-strategy.md`, `.lazy-harness/tests/response-completed-route-telemetry-large-payload.md`

## Contract

Phase 0 performance optimization is measurement-only.

`response.completed` lifecycle behavior must remain identical except for append-only timing telemetry. Timing data may be used to plan future optimization, but must not be used to skip gates until a later conservative fast-path phase has golden parity tests.

Phase 1 introduces one conservative fast-path: when `recent_tool_calls` is present, is a list, and every tool name is in the known read-only allowlist, the hook may skip helpers whose logic is exclusively triggered by file writes. Any unknown payload shape or unknown/non-read-only tool falls back to the full helper set.

Phase 2 adds a shadow lifecycle orchestrator. It runs outside the production hook, mirrors helper order and fast-path selection, and produces JSON for parity tests. It must not replace `on-response-completed.sh` until shadow parity covers STOP/no-STOP fixtures.

## Hook timing log

Default path:

```text
.lazy-harness/logs/hook-timings.jsonl
```

Environment controls:

- `LAZY_HOOK_TIMING=0`: disables timing logging.
- `LAZY_HOOK_TIMING_LOG=/path/to/file.jsonl`: overrides the timing log path.

Each JSONL row contains:

- `ts`: UTC timestamp.
- `event`: currently `response.completed`.
- `component`: `route-telemetry`, a helper path, or `hook-total`.
- `durationMs`: elapsed milliseconds.
- `exitCode`: component exit code where available.
- `outputEmitted`: whether the component emitted a user-visible STOP/reminder output.

## Summary CLI

```bash
.lazy-harness/bin/lazy hook-timings --format=md
.lazy-harness/bin/lazy hook-timings --format=json --limit=500
python3 .lazy-harness/scripts/hook-timing-summary.py --log .lazy-harness/logs/hook-timings.jsonl
```

The summary command is read-only and reports per-component count, total, average, p50, p90, p99, max, emitted count, and non-zero exit count.

## Safety constraints

- No timing failure may block or alter hook decisions.
- Timing rows must not contain raw user messages or payload bodies.
- Timing instrumentation must not change the helper order.
- Timing instrumentation must not suppress helper output.
- Unknown timing failures are swallowed, preserving the legacy hook behavior.
- Fast-path skip decisions must be based only on parsed payload facts, not natural-language guesses.
- Unknown payload shape, missing `recent_tool_calls`, or unknown tool names must run the full helper set.
- Phase 1 may skip only write-only helpers that already no-op unless write/edit tools are present.

## Phase 1 read-only fast-path

Read-only allowlist:

- `read`, `Read`
- `grep`, `Grep`, `agentgrep`, `glob`, `Glob`, `ls`, `LS`
- `webfetch`, `websearch`
- filesystem read/list/search/get-info MCP tools

Skipped only for known read-only payloads:

- `check-layer-impact.sh`
- `check-ddd-trigger.sh`
- `check-ssot-trigger.sh`
- `check-layer-completeness.sh`
- `check-tdd-cross-verify.sh`
- `check-affected-tests.sh`

Not skipped:

- BDD trigger, because it can inspect natural-language user flow even without writes.
- analysis discovery, project rule placement, option-gate discipline, record-before-session-history, lazy CLI entrypoint, aftershock reanalysis, fix-regression, ADR sync, and handoff stale helpers.

## Phase 2 shadow orchestrator

CLI:

```bash
.lazy-harness/bin/lazy lifecycle-check --format=json < payload.json
python3 .lazy-harness/scripts/lifecycle-check.py --format=md --payload '{"recent_tool_calls":[]}'
```

Contract:

- Read-only with respect to production hook wiring. It does not change `on-response-completed.sh` behavior.
- Mirrors the production helper order and Phase 1 fast-path selection.
- Stops at the first helper output, matching production hook semantics.
- Emits `firstOutput`, `firstOutputHelper`, `injectJson`, selected/skipped helpers, helper timing, and fast-path reason.
- May execute existing helpers and therefore uses the same queue/validation environment variables as legacy hook tests.
- Replacement is forbidden until self-test parity covers representative STOP/no-STOP cases.

## Implementation map

- `.lazy-harness/hooks/lifecycle/on-response-completed.sh`
  - Emits timing rows around route telemetry, each lifecycle helper, and total hook runtime.
  - Applies Phase 1 read-only fast-path only for known read-only payloads, with full-check fallback for unknowns.
- `.lazy-harness/scripts/lifecycle-check.py`
  - Phase 2 shadow orchestrator. Parses payload once, mirrors helper order/fast-path selection, runs existing helpers, and reports first-output parity data.
- `.lazy-harness/scripts/hook-timing-summary.py`
  - Read-only timing summary CLI.
- `.lazy-harness/bin/lazy`
  - Exposes `lazy hook-timings` and `lazy lifecycle-check`.
- `.lazy-harness/scripts/self-test.py`
  - `check_response_completed_auto_route_telemetry` verifies timing rows are emitted without changing telemetry behavior and that the summary CLI works.
  - The same test protects fast-path safety: read-only payloads skip only write-only helpers, while unknown/missing payload shapes run the full helper set.
  - `check_lifecycle_hook_integration` verifies shadow parity for TDD cross-verify and aftershock STOP outputs.

## Discovery capture

- DDD: none.
- SDD: this contract defines Phase 0 measurement-only behavior.
- BDD: user-visible behavior is unchanged except an explicit `lazy hook-timings` command.
- TDD: existing response.completed telemetry regression test extended to protect timing output.
- ADR: no replacement decision yet; Phase 2 shadow orchestrator is explicitly not a production replacement.
- SSOT: timing log path and env toggles are defined here.
