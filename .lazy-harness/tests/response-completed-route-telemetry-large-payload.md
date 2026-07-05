# TDD — response.completed route telemetry regression — Superseded

Status: superseded
Layer: TDD
Superseded by: `.lazy-harness/ssot/cli-tool-boundary.md` and `.lazy-harness/scripts/self-test.py#check_response_completed_no_auto_route_telemetry`

## Rule digest

- Status: deprecated
- Layer: TDD
- Scope: framework-global
- Aliases:
  - 텔레메트리 회귀
  - large payload
- Applies when:
  - working on `response.completed` lifecycle, route telemetry, or user-text classification
  - asking why automatic route telemetry / a static route classifier was removed
- Must:
  - keep `response.completed` free of any static route/user-text classifier
  - create no automatic route telemetry from raw user messages
  - preserve hook timing telemetry, tolerating large payloads
- Must not:
  - revive the removed task-router or automatic route-decision logging
- Record completion:
  - superseded by `.lazy-harness/ssot/cli-tool-boundary.md` and the no-auto-route-telemetry self-test
- Related records:
  - `.lazy-harness/ssot/cli-tool-boundary.md`
  - `.lazy-harness/spec/platform/hook-performance-measurement.md`

## Supersession

This regression originally protected automatic route telemetry for large `response.completed` payloads. The task-router and automatic route telemetry have been removed.

Current expected behavior:

- `response.completed` must not run a static route/user-text classifier.
- No automatic route telemetry should be created from raw user messages.
- Hook timing telemetry still works and still tolerates large payloads.

## Protection

- `.lazy-harness/scripts/self-test.py#check_response_completed_no_auto_route_telemetry`

## Rule placement

- Rule: response.completed must not auto-run raw user-text route classifiers.
- Scope: framework-global
- Primary record: `.lazy-harness/tests/response-completed-route-telemetry-large-payload.md`
- Why not AGENTS.md: this is regression history and test mapping, not prompt grammar.
- Why not `.jcode`: shared framework lifecycle behavior.
- Confirmation: user-confirmed

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/tests/response-completed-route-telemetry-large-payload.md` — superseded regression record and rule placement.
  - `.lazy-harness/scripts/self-test.py` — executable regression fixture.
  - `.lazy-harness/hooks/lifecycle/on-response-completed.sh` — response.completed hook wrapper and helper timing loop.
  - `.lazy-harness/hooks/lifecycle/helpers/check-bdd-trigger.sh` — non-write-only helper that remains on the read-only fast path.
- Key symbols:
  - `check_response_completed_no_auto_route_telemetry` (`.lazy-harness/scripts/self-test.py`) — runs response.completed hook on normal and large payloads, verifies no route telemetry log is created, and verifies timing rows remain.
  - `run_hook_with_timing` (`.lazy-harness/scripts/self-test.py`) — fixture helper that runs the hook under different payload/tool shapes and captures timing components.
  - `on-response-completed.sh` helper loop — executes lifecycle helpers with timing rows and intentionally does not run route/user-text classifier telemetry.
- Flow:
  1. Self-test copies `.lazy-harness` into a temporary git worktree and runs `on-response-completed.sh` with normal and large payloads.
  2. The fixture verifies `$LAZY_SHARED_ROOT/logs/route-decisions.jsonl` is not created from raw user text.
  3. The fixture verifies timing telemetry still records `hook-total` and non-write-only helpers, while `route-telemetry` is absent after task-router removal.
  4. Read-only fast-path checks keep `check-bdd-trigger.sh` active and skip only write-only helpers.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py` runs `check_response_completed_no_auto_route_telemetry`.
  - The same fixture also validates `lazy hook-timings --format=json`, `--all-sessions`, and lifecycle compare-mode timing output.
- Cross-layer links:
  - SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`
  - SDD: `.lazy-harness/spec/platform/hook-performance-measurement.md`
  - TDD: `.lazy-harness/tests/response-completed-route-telemetry-large-payload.md`
- Machine index:
  - graph ids: `kg_response_completed_no_auto_route_tdd`, `kg_response_completed_no_auto_route_self_test`, `kg_response_completed_no_auto_route_hook`
  - generated index key: `pending`
