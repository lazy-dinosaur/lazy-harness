# TDD — response.completed route telemetry regression — Superseded

Status: superseded
Layer: TDD
Superseded by: `.lazy-harness/ssot/cli-tool-boundary.md` and `.lazy-harness/scripts/self-test.py#check_response_completed_no_auto_route_telemetry`

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
