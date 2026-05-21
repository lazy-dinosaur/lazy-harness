# SDD — Hook Performance Measurement

Status: accepted
Date: 2026-05-21
Layer: SDD
Related: `.lazy-harness/planning/performance-optimization-plan.md`, `.lazy-harness/decisions/0016-lifecycle-hook-strategy.md`, `.lazy-harness/tests/response-completed-route-telemetry-large-payload.md`

## Contract

Phase 0 performance optimization is measurement-only.

`response.completed` lifecycle behavior must remain identical except for append-only timing telemetry. Timing data may be used to plan future optimization, but must not be used to skip gates until a later conservative fast-path phase has golden parity tests.

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

## Implementation map

- `.lazy-harness/hooks/lifecycle/on-response-completed.sh`
  - Emits timing rows around route telemetry, each lifecycle helper, and total hook runtime.
- `.lazy-harness/scripts/hook-timing-summary.py`
  - Read-only timing summary CLI.
- `.lazy-harness/bin/lazy`
  - Exposes `lazy hook-timings`.
- `.lazy-harness/scripts/self-test.py`
  - `check_response_completed_auto_route_telemetry` verifies timing rows are emitted without changing telemetry behavior and that the summary CLI works.

## Discovery capture

- DDD: none.
- SDD: this contract defines Phase 0 measurement-only behavior.
- BDD: user-visible behavior is unchanged except an explicit `lazy hook-timings` command.
- TDD: existing response.completed telemetry regression test extended to protect timing output.
- ADR: no replacement decision yet; future orchestrator replacement requires shadow parity.
- SSOT: timing log path and env toggles are defined here.
