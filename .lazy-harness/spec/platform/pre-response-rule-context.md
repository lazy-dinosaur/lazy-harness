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
  - implementing same-turn lazy-harness direct-search prompt injection
  - comparing `response.completed` with pre-response context
- Must:
  - use Jcode `message.received` for bounded same-turn direct-search prompt injection when host context is likely needed
  - keep `blocking = true` with `timeout_ms = 800` for same-turn prompt inclusion
  - fail open on timeout or hook failure
  - keep response policy in lifecycle context, not tool-specific project-policy branches
  - inject framework-structured direct-search instructions for ambiguous/surface-like or host-dependent requests without running a subagent or semantic search backend in the hook
  - journal sanitized direct-search debt before the first action so the generic evidence guard/audit can verify real root-bound search evidence
  - keep Context Delivery and Relevant Record Query CLIs optional/manual/dogfood helpers, not automatic semantic authority in `message.received`
- Record completion:
  - changes to pre-turn hook payload/output contract or self-resolution protocol update this SDD
- Related records:
  - `.lazy-harness/spec/platform/relevant-record-query.md`
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh`

## Purpose

Pre-response rule context is the lifecycle surface that lets lazy-harness inject a direct framework-structured search protocol after a user message is received and before the assistant response/provider prompt is generated.

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
    "body": "STOP. Direct lazy-harness search-debt before response\n- ...",
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
3. cheaply classify whether the turn likely depends on host details, code, records, rules, tests, config, or ambiguous references,
4. emit `STOP. Direct lazy-harness search-debt before response` only for host-dependent turns,
5. include framework structure in the prompt: DDD/SDD/BDD/TDD/ADR/SSOT/Planning folders, `## Rule digest`, Related records, Implementation map, graph links, source/tests, option-gate-after-search,
6. append sanitized direct-search debt rows to `.lazy-harness/state/context-delivery-packets.jsonl` with hashed identifiers and no raw user message,
7. stay silent for smalltalk/clearly context-free turns,
8. avoid running `relevant-record-query.ts`, `context-delivery.ts`, subagents, `jcode run`, or any semantic search backend inside `message.received`,
9. log latency without raw message bodies when logging is needed.

The surfaced digest journal is runtime state only and is now written by explicit digest surfacing/dogfood paths, not by the default `message.received` direct-search hook. It stores safe hashes and record-authored fields (record path, title, layer, status, record-completion text, compact bullets) so `response.completed` can audit the same turn without storing raw user or assistant message bodies.

Protocol-only direct-search injections are prompt context, not surfaced record evidence. They must not write raw user messages or synthetic candidate meanings to the surfaced digest journal. Direct-search debt rows and explicit Context Delivery packet rows share `.lazy-harness/state/context-delivery-packets.jsonl` as non-canonical runtime state with sanitized metadata and safe message/session hashes; those rows are consumed by the generic evidence guard and response audit/backstop as search/read debt evidence.

## Token and latency budget

Target:

- timeout: 800ms bounded by Jcode,
- normal digest: 200–600 tokens,
- hard ceiling: 1,000 tokens,
- no full record dumps,
- fail-open on error/timeout.

If helper/index performance is not dogfood-proven, keep it explicit/manual instead of enabling same-turn semantic authority broadly.

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
→ cheap host-context classifier
→ direct framework-structured search-debt prompt into current turn when needed
→ direct root-bound search evidence before action when search-debt exists
→ read evidence before action when requiredRead debt exists
→ assistant response/actions
→ response.completed audit/backstop
```

## Implementation map

- Primary files:
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh` - resolves host root, injects direct framework-structured search-debt prompt for likely host-dependent turns, and journals sanitized direct-search debt without running semantic query backends.
  - `.lazy-harness/hooks/lifecycle/helpers/check-response-rule-audit.py` - post-response audit helper that consumes sanitized packet journal rows and reports missed requiredRead/search evidence.
  - `.lazy-harness/scripts/relevant-record-query.ts` - read-only digest query CLI for explicit/manual/dogfood use, not automatic `message.received` semantic authority.
  - `.lazy-harness/spec/platform/context-delivery-contract.md` - defines the self-resolution instruction level and packet-compatible search protocol.
  - `.lazy-harness/scripts/self-test.py` - protects direct-search prompt, search-debt journal, and evidence guard fixtures.
- Flow:
  1. Hook receives `last_user_message` and host root from Jcode.
  2. Hook decides only whether direct root-bound search is required; it does not resolve semantics.
  3. Hook injects the framework search structure and examples.
  4. Hook journals direct-search debt with safe hashes.
  5. Main LLM/searcher performs root-bound grep/rg/agentgrep/read work before answering or acting.
  6. Unsatisfied direct-search/read debt is guarded before action and audited after response.
- Protection:
  - `.lazy-harness/scripts/self-test.py#check_message_received_hook_context_injection`

## Rule placement

- Rule: lazy-harness uses Jcode `message.received` as the bounded pre-turn hook that injects direct framework-structured search prompts for host-dependent turns; `response.completed` alone is too late.
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
