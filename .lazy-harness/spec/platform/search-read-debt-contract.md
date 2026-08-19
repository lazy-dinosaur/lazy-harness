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
  - let the LLM/searcher satisfy the first work-unit debt by map-first traversal and root-bound governing-record/source/test reads
  - cache successful Pi/OMP work-unit grounding as an overview marker plus content hashes of directly read governing records
  - reuse valid work-unit grounding across normal message boundaries; do not reissue map/read debt merely because another user message arrived
  - let `check-read-debt-permit.py` measure first-grounding map/read evidence before mutation or a host-specific completion claim
  - allow map-first `lazy map --overview` evidence to satisfy search-debt, but never required-read debt
  - invalidate work-unit reuse on a new runtime session, a non-extension mid-turn steer, or changed/deleted governing-record fingerprints
  - bind tool results to the evidence epoch in which their tool call started so a late pre-steer parallel result cannot satisfy post-steer debt
  - keep genuinely new-scope judgement LLM-owned; lifecycle code must not classify raw user text to guess scope
  - keep response audit advisory/backstop, not semantic routing
- Must not:
  - generate required-read lists, confidence scores, intent/risk/gate, or next-action from raw user text
  - treat any generated cache or helper output as proof that the LLM/searcher read evidence
  - reintroduce deleted query/backbone helper CLIs as lifecycle semantic authority
  - replay full inventory, record lists, or policy/capability catalogs on every normal message or file read
  - invalidate valid work-unit evidence solely because a new normal message started
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
first Pi/OMP work-unit boundary
→ append one sanitized static search/read-debt row
→ inject a pointer-only grounding reminder
→ LLM/searcher runs one overview, chooses a concrete node, and reads only governing records plus exact implementation evidence
→ adapter stores the overview marker and governing-record content hashes
→ generic pre-action guard allows mutation after concrete evidence exists

later normal message in the same work unit
→ adapter verifies governing-record hashes
→ valid: reuse grounding with a visible `reused-work-unit` status and no prompt/catalog replay
→ changed/deleted: arm one fresh grounding packet

explicit mid-turn steer
→ clear work-unit grounding and advance the evidence epoch
→ ignore results from tool calls started in an older epoch
→ require one fresh post-steer map/read grounding before mutation

response.completed
→ audit durable capture and strong misses as a backstop
```

## Implementation map

- Primary files:
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh` — writes the first sanitized work-unit debt row and injects a pointer-only grounding reminder without inventory/catalog replay.
  - `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py` — blocks the first mutation before root-bound evidence exists; later valid Pi/OMP work-unit reuse does not create a new row.
  - `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — caches overview + governing-record hashes, emits `reused-work-unit` on valid later turns, and clears reuse on explicit steering.
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
