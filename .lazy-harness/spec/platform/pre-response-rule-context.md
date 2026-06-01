# SDD — Pre-Response Rule Context

Status: accepted
Date: 2026-06-01
Layer: SDD
Related ADR: `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
Related SDD: `.lazy-harness/spec/platform/relevant-record-query.md`
Related plan: `.lazy-harness/planning/record-query-context-loop-transition-plan.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Applies when:
  - configuring Jcode `message.received` or pre-turn context hooks
  - implementing same-turn lazy-harness rule digest injection
  - comparing `response.completed` with pre-response context
- Must:
  - use Jcode `message.received` for bounded same-turn relevant-record injection
  - keep `blocking = true` with `timeout_ms = 800` for same-turn prompt inclusion
  - fail open on timeout or hook failure
  - keep response policy in lifecycle context, not tool-specific project-policy branches
- Record completion:
  - changes to pre-turn hook payload/output contract update this SDD
- Related records:
  - `.lazy-harness/spec/platform/relevant-record-query.md`
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh`

## Purpose

Pre-response rule context is the lifecycle surface that lets lazy-harness run a relevant-record query after a user message is received and before the assistant response/provider prompt is generated.

This is the key Phase 3 integration point for C+ v2 organic hybrid guidance.

## Confirmed Jcode lifecycle capability

`response.completed` is too late for this purpose. It can inject into a later continuation/turn, but it cannot reliably place context into the same assistant response that is about to be generated.

Jcode added the required pre-turn event in commit `3eb71ddb Add pre-turn message received hooks`.

Confirmed event:

- `message.received`

## Timing contract

The hook must run:

1. after the user message is appended/accepted,
2. before provider prompt construction,
3. before the first model/tool decision of that turn.

If the hook emits an injection, that injection must be included in the **current** turn prompt/context, not a future turn.

## Hook registration shape

Confirmed Jcode config shape:

```toml
[[hooks.commands]]
event = "message.received"
command = ".lazy-harness/hooks/lifecycle/on-message-received.sh"
blocking = true
timeout_ms = 800
```

`blocking = true` here means bounded pre-turn execution, not policy hard-blocking. The hook must be short-timeout and fail-open so normal flow is not held hostage by context generation.

A non-blocking observer hook is acceptable for telemetry, but it cannot guarantee same-turn prompt injection.

## Payload contract

Minimum payload:

```json
{
  "event": "message.received",
  "session_id": "...",
  "message_id": "...",
  "working_dir": "/path/to/host",
  "last_user_message": "..."
}
```

Recommended payload:

```json
{
  "event": "message.received",
  "session_id": "...",
  "message_id": "...",
  "turn_count": 42,
  "working_dir": "/path/to/host",
  "last_user_message": "...",
  "recent_context": ["short context only"],
  "recent_tool_calls": [
    { "name": "read", "args_preview": ".lazy-harness/..." }
  ]
}
```

Requirements:

- include current working directory or host root,
- include current user message text,
- do not require assistant response text,
- avoid raw long transcript dumps,
- keep payload small and privacy-conscious.

## Output contract

The hook may output JSON:

```json
{
  "action": "allow",
  "inject": {
    "body": "Relevant lazy-harness rules\n- ...",
    "format": "system_reminder"
  }
}
```

Semantics:

- `inject.body` is appended to the current turn prompt/context.
- empty output means no injection.
- failures/timeouts are fail-open.
- hook output is advisory context unless a future promoted hard-stop mechanism explicitly says otherwise.

## Lazy-harness hook behavior

`on-message-received.sh` should eventually:

1. resolve host root,
2. parse payload,
3. call `relevant-record-query.ts --message ... --format=json --token-budget=600`,
4. render compact Markdown and emit `inject` JSON when relevant records exist,
5. append sanitized surfaced digest metadata to `.lazy-harness/state/surfaced-rule-digests.jsonl`,
6. stay silent when no relevant records are found,
7. log latency without raw message bodies.

The surfaced digest journal is runtime state only. It stores safe hashes and record-authored fields (record path, title, layer, status, record-completion text, compact bullets) so `response.completed` can audit the same turn without storing raw user or assistant message bodies.

## Token and latency budget

Target:

- timeout: 800ms bounded by Jcode,
- normal digest: 200–600 tokens,
- hard ceiling: 1,000 tokens,
- no full record dumps,
- fail-open on error/timeout.

If query/index performance is not ready, run in measurement/shadow mode before enabling same-turn injection broadly.

## Relationship to response.completed

`message.received` provides **before-response context**.

`response.completed` remains the **after-response audit/backstop**:

- checks whether surfaced rules were ignored,
- checks mandatory record completion,
- updates guidance/journal state,
- emits no output on clean turns.

Phase 4 contract details live in `.lazy-harness/spec/platform/response-rule-audit.md`.

Together:

```text
message.received
→ relevant-record query
→ compact digest injection into current turn
→ assistant response
→ response.completed audit/backstop
```

## Rule placement

- Rule: lazy-harness uses Jcode `message.received` as the bounded pre-turn hook that can inject compact relevant-record context into the current assistant turn; `response.completed` alone is too late.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/pre-response-rule-context.md`
- Why not AGENTS.md: this is a platform/Jcode lifecycle contract, not final operational grammar.
- Why not `.jcode`: the event must be supported by Jcode/lazy-harness integration generally, not local/private workflow only.
- Confirmation: user-confirmed; Jcode implementation confirmed in commit `3eb71ddb`.

## Discovery capture

- DDD: none.
- SDD: updated, this contract defines pre-response rule context lifecycle requirements.
- BDD: future agent behavior should include relevant rule context before the response.
- TDD: fixtures needed for lazy-harness hook payload/output behavior.
- ADR: ADR 0041 selected the organic hybrid response lifecycle model.
- SSOT: harness enforcement policy anchors mandatory record vs organic guidance split.
- Planning: record-query context loop transition plan Phase 3.
