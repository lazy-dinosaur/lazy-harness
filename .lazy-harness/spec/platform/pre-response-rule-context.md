# SDD — Pre-Response Rule Context

Status: accepted
Date: 2026-06-01
Layer: SDD
Related ADR: `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
Related SDD: `.lazy-harness/spec/platform/search-read-debt-contract.md`
Related plan: `.lazy-harness/planning/searchable-record-context-retrieval-implementation-plan.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Aliases:
  - 사전 규칙 컨텍스트
  - pre-response
  - 응답 전 규칙 주입
- Applies when:
  - configuring Jcode `message.received` or pre-turn context hooks
  - implementing same-turn lazy-harness direct-search prompt injection
  - comparing `response.completed` with pre-response context
  - enforcing harness-first record/source search before agent responses or actions
- Must:
  - use Jcode/Pi/OMP `message.received` only for bounded pointer-only first-grounding guidance; do not replay it on every normal message when valid work-unit evidence exists
  - keep `blocking = true` with `timeout_ms = 800` for Jcode same-turn inclusion and fail open on timeout or hook failure
  - preserve valid non-empty payloads when caller `TMPDIR` is stale, missing, or unusable by retrying payload-file creation under `/tmp` before the final fail-open/no-injection fallback
  - keep response policy in lifecycle context, not tool-specific project-policy branches
  - keep the transport static and user-text-agnostic; it may tell the LLM how to ground the work unit but may not run a subagent or semantic search backend
  - omit full layer inventory, generated-index details, mapped record lists, and policy/capability catalogs from the injected body
  - journal sanitized direct-search debt for the first Pi/OMP work-unit grounding; after overview + governing-record fingerprints exist, later normal messages reuse them without another row or system-prompt injection
  - when Pi/OMP receives a non-extension mid-turn steer, clear work-unit fingerprints and require fresh post-steer map/read evidence before later actions; do not classify the steer text or write a semantic debt row
  - keep deleted query-helper CLIs removed; `message.received` remains static transport, not automatic semantic authority
  - keep exploration tool names as examples, not a closed allowlist; the required behavior is following lazy-harness and leaving root-bound evidence before action
  - surface pending host record migration deterministically (2026-07-05, user-approved resume-surfacing decision; graph probe added same day): the reminder MAY append a `Host record migration PENDING` line derived from bounded, fail-open probes (`helpers/host_migration_state.py`, each timeout < extension hook budget): `lazy record-lint --format=json` (issues/advisories) AND `lazy graph-hygiene --migration-plan --format=json` (legacy-schema rows / removed-framework refs). The line varies ONLY by host validator state, never by user text (static-equality per message preserved); it is omitted when clean/unknown, points at the guided `lazy-record-quality`/`lazy-memory-backfill`/`lazy-graph-migrate` resume paths, and never triggers automatic record/graph rewrites
- Record completion:
  - changes to pre-turn hook payload/output contract or self-resolution protocol update this SDD
- Related records:
  - `.lazy-harness/spec/platform/search-read-debt-contract.md`
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh`

## Purpose

Pre-response rule context is a bounded pointer for the first grounding boundary of a work unit. Pi/OMP suppress repeated injection after concrete overview + governing-record fingerprints are valid; Jcode keeps the same static, compact, fail-open body where native work-unit reuse is unavailable.

This remains the Phase 3 integration point for C+ v2 organic hybrid guidance, but no longer treats every response as a fresh retrieval obligation.

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
    "body": "REMINDER. Ground this work unit once before mutation or a host-specific completion claim.\n- ...",
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
3. avoid all user-text semantic classification in shell/CLI code; the hook must not branch on words such as `fix`, `test`, `고쳐`, or `확인`,
4. emit the same compact work-unit grounding body for any non-empty user message when the runtime requests first grounding,
5. omit harness inventory counts, generated-index details, mapped records, and operating-rule catalogs from the body,
6. keep the body at or below 300 estimated tokens in framework source dogfood,
7. append one sanitized first-grounding debt row with hashed identifiers and no raw user message,
8. let Pi/OMP skip the hook entirely for a valid cached work unit; unchanged normal turns produce only the visible `reused-work-unit` marker,
9. stay silent when no user message exists or the hook cannot resolve a host root,
10. avoid deleted query helpers, subagents, `jcode run`, semantic search, map, catalog, or resolver subprocesses inside `message.received`,
11. log latency without raw message bodies when logging is needed.

The surfaced digest journal is runtime state only and is now written by explicit digest surfacing/dogfood paths, not by the default `message.received` harness-first search hook. It stores safe hashes and record-authored fields (record path, title, layer, status, record-completion text, compact bullets) so `response.completed` can audit the same turn without storing raw user or assistant message bodies.

Protocol-only harness-first inventory/search injections are prompt context, not surfaced record evidence. They must not write raw user messages or synthetic candidate meanings to the surfaced digest journal. Static search/read-debt rows use `$LAZY_RUNTIME_ROOT/state/search-read-debt.jsonl` as non-canonical runtime state with sanitized metadata and safe message/session hashes; those rows are consumed by the generic evidence guard and response audit/backstop as search/read debt evidence.

## Token and latency budget

Target:

- timeout: 800ms bounded by Jcode,
- first-grounding body: <=300 estimated tokens,
- later valid Pi/OMP normal turn: status marker only; no system-prompt injection,
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
→ compact static harness inventory/search prompt into current turn
→ actual stored record/file inventory and canonical record/source reads before action when search-debt exists
→ read evidence before action when requiredRead debt exists
→ assistant response/actions
→ response.completed audit/backstop
```

Pi/OMP mid-turn steering adds an instruction boundary inside the same agent run:

```text
non-extension input(streamingBehavior=steer)
→ invalidate prior recent-tool evidence and advance the root evidence epoch
→ ignore late results from tool calls started before the steer
→ inject compact steer re-grounding
→ generic pre-action guard blocks later actions until fresh post-steer map/read evidence exists
```

## Implementation map

- Primary files:
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh` - resolves host root, injects the same compact static harness-first inventory/search prompt for every non-empty user message, includes bounded layer counts, generated-index/graph/project pointers, and source/test/doc directory presence without per-layer sample dumps, and journals sanitized direct-search debt without running semantic query backends or user-text semantic classifiers.
  - `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py` - generic pre-action evidence detector that blocks action until the turn shows root-bound harness-following inventory/search/read evidence; it is not a tool allowlist.
  - `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` - detects non-extension mid-turn steering, advances a root evidence epoch, clears prior recent-tool evidence, and accepts only results from tool calls started in the current epoch.
  - `.lazy-harness/hooks/lifecycle/helpers/check-response-rule-audit.py` - post-response audit helper that consumes sanitized search/read-debt journal rows and reports missed requiredRead/search evidence.
  - `.lazy-harness/spec/platform/search-read-debt-contract.md` - defines the static search/read-debt runtime row contract.
  - `.lazy-harness/scripts/self-test.py` - protects harness-first prompt, examples-not-allowlist wording, search-debt journal, and evidence guard fixtures.
- Flow:
  1. Hook receives `last_user_message` and host root from Jcode.
  2. Hook checks only structural prerequisites: host root exists and user message is non-empty.
  3. Hook injects bounded `.lazy-harness` layer counts, generated-index/graph/project pointers, and a compact purpose-scoped search/read protocol without inspecting message meaning.
  4. Hook journals direct-search debt with safe hashes and static instruction level `harness-first-static`.
  5. Main LLM/searcher follows lazy-harness, reads actual records/source, and may use any root-bound read-only/search/query affordance before answering or acting.
  6. Unsatisfied direct-search/read debt is guarded before action and audited after response.
  7. A Pi/OMP mid-turn steer invalidates earlier-instruction evidence for later actions until fresh post-steer map/read evidence completes.
- Protection:
  - `.lazy-harness/scripts/self-test.py#check_message_received_hook_context_injection`
  - `.lazy-harness/scripts/self-test.py#check_pi_package_layout_and_contract` (post-steer evidence epoch regression)

## Rule placement

- Rule: lazy-harness uses Jcode `message.received` as the bounded pre-turn hook that injects compact static harness-first inventory/search prompts before LLM understanding/search; `response.completed` alone is too late.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/pre-response-rule-context.md`
- Why not AGENTS.md: this is a platform/Jcode lifecycle contract, not final operational grammar.
- Why not `.jcode`: the event must be supported by Jcode/lazy-harness integration generally, not local/private workflow only.
- Confirmation: user-confirmed; Jcode implementation confirmed in commit `3eb71ddb`.

## Discovery capture

- DDD: `.lazy-harness/domain/searchable-record-memory.md` defines instruction-scoped evidence.
- SDD: updated; this contract defines pre-response and mid-turn steer self-resolution requirements.
- BDD: `.lazy-harness/behavior/llm-owned-record-retrieval.md` defines fresh post-steer evidence behavior.
- TDD: pre-response, pre-action, and Pi package fixtures protect the generic evidence boundary.
- ADR: ADR 0041 remains the organic-hybrid authority; no command-specific policy branch was added.
- SSOT: CLI semantic-authority and enforcement-level boundaries are unchanged.
- Planning: searchable-record tasks/plan and Pi adapter plan track the implemented steer hardening.

## Map-first retrieval prompt guidance

The static `message.received` reminder now teaches map-first traversal without classifying the user message:

- start with `lazy map --overview`
- choose concrete feature ids, record paths, graph ids, source paths, or test paths from the map
- drill down with `lazy map <feature-id|record-path|graph-id|source-path>`
- never pass raw user text, long natural-language strings, or invented `--query` flags to `lazy map`
- fallback to root-bound search only when the map/index is empty, ambiguous, or missing a concrete node

The hook remains static: it must render the same body for all non-empty messages, avoid raw user-text classifiers, and journal the same sanitized `harness-first-static` search debt. Node selection is done by the LLM/searcher or user, not the hook.

## Rule placement

- Rule: `message.received` prompt guidance should point agents to map-first traversal while remaining static/non-semantic and preserving fallback search for ambiguous or incomplete map coverage.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/pre-response-rule-context.md`
- Why not AGENTS.md: this is hook output contract and regression behavior.
- Why not `.jcode`: shared lazy-harness lifecycle behavior.
- Confirmation: inferred-from-record
