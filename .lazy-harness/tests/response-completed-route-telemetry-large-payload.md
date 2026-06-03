# TDD — response.completed route telemetry large payload regression

Status: accepted
Date: 2026-05-20
Layer: TDD
Related: `.lazy-harness/spec/platform/workflow-compression-router.md`, `.lazy-harness/decisions/0037-workflow-compression-not-safety-reduction.md`

## Regression

Automatic route telemetry is supposed to accumulate during normal Jcode use so the user can keep working without remembering manual `lazy route --log` probes.

Observed failure: `response.completed` hooks were firing and could inject other lifecycle reminders, but `$LAZY_SHARED_ROOT/logs/route-decisions.jsonl` was not growing after normal responses. Manual `lazy route --log` still appended successfully.

Root cause: `on-response-completed.sh` copied the full lifecycle payload into `PAYLOAD_JSON` and parsed it from the environment inside Python. Real payloads can contain large `recent_tool_calls` previews. That env path plus inline Python shell quoting made the telemetry extraction fail silently before `last_user_message` reached `task-router.ts`.

## Expected behavior

- Given a `response.completed` payload with `last_user_message` and `message_id`, the hook appends one route sample to `$LAZY_SHARED_ROOT/logs/route-decisions.jsonl`.
- Replaying the same `message_id` does not append duplicates.
- Live-sized payloads with large `recent_tool_calls` still append successfully.
- Telemetry never stores raw user message text.
- If the payload has no supported user-message field, diagnostics may go to `$LAZY_SHARED_ROOT/logs/route-telemetry-debug.jsonl` with keys/counts/hashes only.

## Layer completeness impact

- DDD: none. No domain terminology or business rule changed.
- SDD: updated. The workflow compression router telemetry contract now requires stdin payload parsing and no-raw diagnostic logging.
- BDD: none. User-visible behavior is unchanged except the intended background accumulation now works.
- TDD: updated. `check_response_completed_auto_route_telemetry` covers dedupe plus live-sized payload handling.
- ADR: none. ADR 0037 already decided automatic non-canonical telemetry; no decision changed.
- SSOT: none. No config/schema/source-of-truth ownership changed.

## Implementation map

- `.lazy-harness/hooks/lifecycle/on-response-completed.sh`
  - Parses the response payload from stdin for route telemetry extraction.
  - Supports `last_user_message`, `lastUserMessage`, `last_user_input`, `lastUserInput`, `user_message`, and `userMessage` aliases.
  - Calls `task-router.ts --log --message-id` silently when a message is available.
  - Writes no-raw diagnostic metadata to `$LAZY_SHARED_ROOT/logs/route-telemetry-debug.jsonl` only when no route message can be extracted.
- `.lazy-harness/scripts/task-router.ts`
  - Owns route classification, telemetry append, and `messageIdHash` dedupe.
- `.lazy-harness/scripts/self-test.py`
  - `check_response_completed_auto_route_telemetry` protects automatic append, dedupe, no raw message storage, and live-sized payload tolerance.

## Validation

- `.lazy-harness/scripts/self-test.py`
- `python3 .lazy-harness/scripts/doctor.py --profile smoke`

## Discovery capture

- DDD: none
- SDD: updated, telemetry contract clarified in `.lazy-harness/spec/platform/workflow-compression-router.md`
- BDD: none
- TDD: updated, this regression record plus self-test coverage
- ADR: none, existing ADR 0037 still applies
- SSOT: none
- Planning: none
