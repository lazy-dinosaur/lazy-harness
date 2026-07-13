# SDD — Search/Read Debt Contract

Status: accepted
Date: 2026-06-06
Layer: SDD
Related SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`
Related SDD: `.lazy-harness/spec/platform/pre-response-rule-context.md`
Related TDD: `.lazy-harness/tests/pre-action-search-evidence-guard.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Aliases:
  - 검색 빚
  - read debt
  - 리드 뎁트
  - 증거 게이트
  - evidence guard
- Applies when:
  - changing `message.received` search/read debt journaling
  - changing the generic pre-action evidence guard
  - changing response audit handling of unsatisfied search/read debt
- Must:
  - store only sanitized search/read debt rows in `$LAZY_RUNTIME_ROOT/state/search-read-debt.jsonl`
  - keep debt rows static/protocol-level, not selected by a raw user-text classifier
  - use safe message/session hashes and bounded counters, never raw prompts or transcripts
  - let the LLM/searcher satisfy debt by map-first traversal and root-bound record/source/test reads
  - let `check-read-debt-permit.py` measure whether map/read evidence exists before action
  - allow map-first `lazy map --overview` evidence to satisfy search-debt, but never required-read debt
  - on a non-extension mid-turn steer, invalidate prior-instruction evidence for subsequent actions and require fresh post-steer map/read evidence without classifying the steered text
  - bind tool results to the evidence epoch in which their tool call started so a late pre-steer parallel result cannot satisfy post-steer debt
  - keep response audit advisory/backstop, not semantic routing
- Must not:
  - generate required-read lists, confidence scores, intent/risk/gate, or next-action from raw user text
  - treat any generated cache or helper output as proof that the LLM/searcher read evidence
  - reintroduce deleted query/backbone helper CLIs as lifecycle semantic authority
- Record completion:
  - changes to journal name, row shape, evidence tools, or guard semantics update this SDD, `.lazy-harness/spec/platform/pre-response-rule-context.md`, `.lazy-harness/tests/pre-action-search-evidence-guard.md`, `.lazy-harness/tests/pre-response-rule-context.md`, and implementation maps.

## Runtime row shape

The runtime journal is non-canonical and session-scoped:

```json
{
  "event": "message.received.search-read-debt",
  "instructionLevel": "harness-first-static",
  "messageIdHash": "16-char-hash",
  "sessionIdHash": "16-char-hash",
  "fallbackSearchCount": 1,
  "epochSeconds": 1780000000.0
}
```

Allowed fields are transport/evidence bookkeeping only. They are not semantic judgments.

## Flow

```text
message.received
→ append sanitized static search/read-debt row
→ inject compact harness-first reminder with mandatory `lazy map --overview`, concrete map-node drilldown, and no keyword fallback
→ LLM/searcher inspects whole record/feature/graph structure, chooses concrete feature/record/graph/source/test nodes from map output, then reads canonical record/source/test evidence
→ generic pre-action guard allows mutation only after map/read evidence exists
→ response.completed audits misses as a backstop

mid-turn steer
→ Pi/OMP adapter advances a root-scoped evidence epoch and clears prior recent-tool evidence
→ results from tool calls started in an older epoch are ignored for evidence
→ next action remains blocked until a post-steer map/read call completes
```

## Implementation map

- Primary files:
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh` — writes static `message.received.search-read-debt` rows and injects the compact reminder with mandatory overview-first, concrete node drilldown, and fallback search guidance.
  - `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py` — blocks action before root-bound evidence exists.
  - `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — re-arms generic debt on non-extension steering by advancing a root-scoped evidence epoch, clearing prior recent-tool evidence, and rejecting late results from older epochs.
  - `.lazy-harness/hooks/lifecycle/helpers/check-response-rule-audit.py` — audits unsatisfied debt after response.
  - `.lazy-harness/scripts/lifecycle-check.py` — mirrors `search-read-debt.jsonl` in sandbox fidelity checks.
  - `.lazy-harness/scripts/self-test.py` — protects row name, guard behavior, deleted helper absence, and post-steer fresh-evidence recovery.
- Runtime state:
  - `$LAZY_RUNTIME_ROOT/state/search-read-debt.jsonl` — non-canonical sanitized journal.
- Protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - `.lazy-harness/bin/lazy prompt-budget --format=md`

## Layer completeness impact

- SDD: replaces the removed candidate helper contract with the static debt contract.
- TDD: guard and pre-response records must reference `search-read-debt.jsonl`.
- SSOT: CLI boundary remains the authority for no semantic CLI classification.
- BDD: no product UI flow.
- DDD: no domain/business rule.

## Rule placement

- Rule: runtime search/read-debt is static transport evidence, not candidate selection or semantic routing.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/search-read-debt-contract.md`
- Why not AGENTS.md: this is platform runtime contract with implementation map and tests.
- Why not `.jcode`: shared framework behavior, not local/private wiring.
- Confirmation: user-confirmed correction on 2026-06-06.

## Map-first search evidence

`lazy map --overview` and concrete `lazy map <feature-id|record-path|graph-id|source-path>` calls are cue-only traversal commands. The guard may count those tool events or command/output blobs as **search evidence** for search-debt rows because they inspect project-map inventory, but they are never read evidence for concrete `requiredRead` paths.

## Mid-turn steer evidence epoch

A non-extension Pi/OMP `input` event with `streamingBehavior === "steer"` is a generic instruction boundary. The adapter must advance a root-scoped evidence epoch and clear the recent evidence exposed to the pre-action guard. It does not inspect the steer text, select records, or generate a new semantic debt row.

Each allowed tool call is tagged in memory with the current evidence epoch. Its `tool_result` may enter the recent evidence cache only when the recorded start epoch still equals the current root epoch. This prevents a slow or parallel tool that started before the steer from repopulating the cache after invalidation. The existing pre-action guard then applies unchanged: read-only map/read work remains available, while a later action blocks until fresh post-steer evidence exists.

`lazy find --purpose ...`, long free-form `lazy map` input, invented `--query` syntax, and keyword grep/rg/find fallback are invalid retrieval evidence because they imply CLI/tool-owned semantic search.
