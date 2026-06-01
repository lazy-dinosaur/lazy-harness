# SDD — Pre-Response Rule Context

Status: accepted
Date: 2026-06-01
Layer: SDD
Related ADR: `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
Related SDD: `.lazy-harness/spec/platform/relevant-record-query.md`
Related SDD: `.lazy-harness/spec/platform/context-delivery-contract.md`
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
  - inject lightweight Context Delivery self-resolution instructions for ambiguous/surface-like implementation requests without running a subagent in the hook
  - when available within timeout, run the deterministic Context Delivery producer and inject/journal concrete read-debt before the first action
- Record completion:
  - changes to pre-turn hook payload/output contract or self-resolution protocol update this SDD
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

`on-message-received.sh` should:

1. resolve host root,
2. parse payload,
3. call `relevant-record-query.ts --message ... --format=json --token-budget=600`,
4. render compact Markdown and emit `inject` JSON when relevant records exist,
5. append sanitized surfaced digest metadata to `.lazy-harness/state/surfaced-rule-digests.jsonl` only when actual digest entries were surfaced,
6. run bounded `context-delivery.ts --journal` to produce concrete requiredRead/read-debt when possible,
7. emit lightweight Context Delivery self-resolution instructions for surface-like implementation/change requests only when a concrete packet is unavailable,
8. keep simple digest requests digest-only,
9. stay silent when neither digest nor safe context delivery/self-resolution protocol applies,
10. log latency without raw message bodies.

The surfaced digest journal is runtime state only. It stores safe hashes and record-authored fields (record path, title, layer, status, record-completion text, compact bullets) so `response.completed` can audit the same turn without storing raw user or assistant message bodies.

Protocol-only self-resolution injections are prompt context, not surfaced record evidence. They must not write raw user messages or synthetic candidate meanings to the surfaced digest journal. Concrete Context Delivery packet rows are written to `.lazy-harness/state/context-delivery-packets.jsonl` with sanitized required/optional read metadata and safe message/session hashes; those rows may be used by the pre-action read-debt permit gate.

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
→ bounded Context Delivery producer when useful
→ compact digest injection and/or concrete read-debt/self-resolution protocol into current turn
→ read/search evidence before action when requiredRead debt exists
→ assistant response/actions
→ response.completed audit/backstop
```

## Implementation map

- Primary files:
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh` - resolves host root, runs the bounded digest query, runs bounded Context Delivery packet generation when available, renders digest/read-debt context, and adds self-resolution protocol only when no concrete packet is available.
  - `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py` - pre-action permit gate that consumes sanitized packet journal rows and blocks action tools until requiredRead evidence exists.
  - `.lazy-harness/scripts/relevant-record-query.ts` - read-only digest query backend for the hook.
  - `.lazy-harness/spec/platform/context-delivery-contract.md` - defines the self-resolution instruction level and packet-compatible search protocol.
  - `.lazy-harness/scripts/self-test.py` - protects digest-only and self-resolution hook fixtures.
- Flow:
  1. Hook receives `last_user_message` and host root from Jcode.
  2. Hook runs relevant-record query within its bounded timeout.
  3. Hook renders digest entries when present.
  4. Hook journals concrete packet rows when bounded Context Delivery succeeds.
  5. Hook appends self-resolution protocol only for surface-like answer/change requests without a concrete packet.
  6. Main LLM performs root-bound search/reads before acting; pre-action permit blocks action when packet-scoped requiredRead debt is unsatisfied.
- Protection:
  - `.lazy-harness/scripts/self-test.py#check_message_received_hook_context_injection`

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
