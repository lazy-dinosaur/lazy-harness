# BDD — LLM-Owned Record Retrieval

Status: accepted
Date: 2026-06-06
Layer: BDD
Related DDD: `.lazy-harness/domain/searchable-record-memory.md`
Related PRD: `.lazy-harness/prd/searchable-record-context-retrieval-prd.md`
Related SDD: `.lazy-harness/spec/platform/search-read-debt-contract.md`
Related SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`

## Rule digest

- Status: active
- Layer: BDD
- Scope: framework-global
- Aliases:
  - LLM 검색 주체
  - 검색 행동 규약
  - retrieval behavior
  - 메타데이터 큐
- Applies when:
  - an agent/searcher uses searchable record memory before answering, planning, or editing
  - an agent/searcher starts a retrieval flow with `lazy map --overview`
  - an agent/searcher runs `lazy map <feature-id|record-path|graph-id|source-path>` to inspect a concrete map node
  - `## Index header` or other metadata suggests records/source/tests
  - retrieved metadata conflicts, is incomplete, or could be mistaken for semantic authority
- Must:
  - use metadata as a starting cue only
  - prefer `lazy map --overview` as the first inventory call before choosing dependent follow-up queries/reads
  - treat `lazy map` output as drill-down candidates, not evidence that anything was read
  - read the real record body/Rule digest/Implementation map before relying on a record
  - inspect source/tests when a plan or mutation depends on implementation facts
  - ask a 3-5 option gate when meanings/layers still conflict after evidence reads
  - create or update durable records after user confirmation when missing host knowledge is found
- Must not:
  - answer or mutate based only on cache/header existence
  - treat batched `lazy map --overview` output as proof that dependent follow-up calls were evidence-informed or read-satisfying
  - treat metadata field names as requiredRead, confidence, risk, gate, or next-action output
  - skip DDD/BDD impact when a new retrieval concept or behavior appears
- Record completion:
  - changes to retrieval behavior update this BDD, DDD terminology, SDD contract, TDD fixtures, tasks, and HTML report together.

## Scenarios

### Scenario 1 — Metadata cue still requires real record read

Given a user request touches a host detail
And a future Record Index Header lists aliases or source/test hints
When the agent uses the metadata to choose where to start
Then the agent reads the actual record body and Rule digest
And reads implementation maps/source/tests when implementation facts matter
And only then answers, plans, or edits.

### Scenario 1a — Record Map narrows the first pass only

Given a user request touches a host detail
When the agent runs `lazy map --overview` first
Then the output shows whole record/feature/graph structure for choosing concrete feature ids, record paths, graph ids, source paths, or test paths
And when the agent repeatedly runs `lazy map <feature-id|record-path|graph-id|source-path>` for nodes copied from the map
Then the outputs may suggest dispersed feature, record, graph, source, and test candidates
And free-form natural-language query text is rejected because `lazy map` is traversal, not semantic search
But those candidates are cue-only
And the agent must still read all relevant actual record bodies, Implementation maps, source, and tests before answering or mutating.

### Scenario 2 — Conflicting meanings require option gate

Given metadata or grep finds multiple plausible records/layers
When the agent cannot establish one meaning from canonical records/source/tests
Then the agent presents 3-5 options with one recommended option
And does not choose on behalf of the user.

### Scenario 3 — Cache hit is not proof of evidence

Given a generated cache lists a record, alias, or source path
When pre-action search/read debt is still unsatisfied
Then the agent must perform root-bound record/source/test reads
And the cache hit alone must not satisfy evidence debt.

### Scenario 4 — Missing knowledge converges after confirmation

Given a needed host fact is missing from `.lazy-harness`
When source/docs/package/config provide one likely fact
Then the agent asks a short confirmation if needed
And writes the confirmed fact into the correct DDD/SDD/BDD/TDD/ADR/SSOT record.

### Scenario 5 — New retrieval concept triggers layer package

Given a new retrieval concept changes terminology, behavior, component contract, or regression fixtures
When planning the next phase
Then DDD, BDD, SDD, TDD, and SSOT/ADR impact must be considered together
And “SDD/TDD only” is insufficient unless DDD/BDD are explicitly judged not impacted.

### Scenario 6 — Search and final verification check for missing related layers

Given a retrieved record declares top-level `Related DDD`, `Related BDD`, `Related SDD`, `Related TDD`, `Related SSOT`, or similar layer links
When an agent/searcher uses `lazy map`, `record-index`, or `lazy retrieval-audit` during search or final validation
Then those related record paths must be surfaced as cue-only candidates
And the agent checks whether any impacted DDD/BDD/SDD/TDD/ADR/SSOT records are missing before writing records, committing, or reporting completion.

### Scenario 7 — Overview-first guidance is advisory, not a tool block

Given `lazy map --overview` is the required first inventory step
When an agent/searcher has not yet inspected the overview output
Then the agent/searcher should prefer a standalone sequential overview before choosing dependent `lazy map <node>`, grep, source reads, or record reads
But `batch` or `multi_tool_use.parallel` tool shapes containing `lazy map --overview` are not hard-blocked
And the generic search/read evidence guard still blocks mutation until root-bound record/source/test evidence exists.

### Scenario 8 — Dynamic write/read loop treats graph as cue, not truth

Given an agent is iterating through search, record/source edits, validation, and follow-up reads
And generated graph/query/explain output suggests ranked candidates
When the agent has just changed records, source, tests, manifests, or graph rows
Then the agent may use graph output as a routing accelerator only
And must read the changed canonical records/source/tests directly before relying on the result
And must run focused validation when implementation or record truth changed
And must not treat generated graph state as fresher than the canonical files.

## Usability checks

- The behavior should make it obvious to an agent that metadata is a navigation aid, not an answer.
- The behavior should reduce repeated broad grep work without replacing evidence reads.
- The behavior should surface ambiguity early instead of silently ranking candidate meanings.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/behavior/llm-owned-record-retrieval.md` — this BDD behavior record.
  - `.lazy-harness/domain/searchable-record-memory.md` — DDD terms used by the scenarios.
  - `.lazy-harness/scripts/record-index.ts` — indexes top-level Related layer links into cue-only related-record metadata.
  - `.lazy-harness/scripts/record-map.ts` — read-only `lazy map` implementation that lists cue-only candidates.
  - `.lazy-harness/scripts/retrieval-coverage-audit.ts` — read-only coverage audit that surfaces related-record candidates plus structural coverage gaps.
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh` — injects static search/read debt reminder.
  - `.lazy-harness/hooks/lifecycle/helpers/check-overview-batch-order.py` — retired compatibility no-op for the old overview batch hard block.
  - `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py` — guards mutation until evidence exists.
  - `.lazy-harness/planning/searchable-record-context-retrieval-tasks.md` — schedules the layer package.
- Key symbols:
  - `buildRecordMap` (`.lazy-harness/scripts/record-map.ts`) — emits candidate records/source/tests/graph ids without semantic-authority fields.
  - `extractTopLevelRelatedRecords` (`.lazy-harness/scripts/record-index.ts`) — parses `Related <Layer>:` links as cue-only related-record paths.
  - `buildAudit` (`.lazy-harness/scripts/retrieval-coverage-audit.ts`) — includes related-record paths during coverage audit without becoming semantic authority.
  - `check-overview-batch-order.py` — compatibility helper that intentionally emits no deny output; batching policy is advisory while mutation safety stays in `check-read-debt-permit.py`.
- Flow:
  1. Static reminder tells the agent to inspect real records/source/tests.
  2. `lazy map --overview` shows whole structure before concrete node selection.
  3. Standalone sequential overview remains preferred, but read-only batch/parallel tool shapes are allowed and must not be treated as evidence reads by themselves.
  4. Repeated `lazy map <feature-id|record-path|graph-id|source-path>` calls on copied concrete nodes may suggest dispersed candidate records or files.
  5. Agent reads canonical evidence across the dispersed candidates and resolves or gates ambiguity.
  6. Confirmed missing knowledge is persisted into records.
  7. Search-time and final verification-time checks include related layer records so “SDD/TDD only” does not silently pass when DDD/BDD/SSOT are linked.
  8. In dynamic write/read loops, map/index/graph cues may narrow candidate paths, but canonical records/source/tests and validation remain the source of truth after mutation.
- Tests / protection:
  - `.lazy-harness/tests/pre-action-search-evidence-guard.md` — protects evidence before action.
  - `.lazy-harness/tests/record-index-header.md` — includes `lazy map` drill-down output and no-semantic-authority checks.
  - `.lazy-harness/tests/retrieval-coverage-audit.md` — protects cross-layer related-record candidates and missing-completeness checks.
  - `.lazy-harness/scripts/self-test.py#check_tool_execute_before_hook` — protects removal of the overview-batch hard block while preserving generic mutation evidence denial.
- Cross-layer links:
  - DDD: `.lazy-harness/domain/searchable-record-memory.md`
  - SDD: `.lazy-harness/spec/platform/search-read-debt-contract.md`
  - TDD: `.lazy-harness/tests/pre-action-search-evidence-guard.md`
  - SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`
  - Planning: `.lazy-harness/planning/searchable-record-context-retrieval-tasks.md`
- Machine index:
  - graph ids: `kg_llm_owned_retrieval_behaves_from_domain`, `kg_record_index_header_layer_package_planned`, `kg_record_index_top_level_related_parser_20260608`, `kg_retrieval_audit_cross_layer_related_self_test_20260608`, `kg_overview_batch_order_guard_20260608`, `kg_overview_batch_order_guard_self_test_20260608`
  - generated index key: pending until index generator exists

## Layer completeness impact

- DDD: depends on searchable record memory terminology.
- BDD: this record covers expected agent/searcher behavior.
- SDD: future Index Header contract must cite this behavior.
- TDD: future fixtures should protect every scenario listed above.
- TDD: retrieval-audit fixtures protect top-level Related DDD/BDD/SSOT/TDD candidate surfacing.
- TDD: tool-execute-before fixtures protect overview-first sequential ordering against batch/parallel misuse.
- SSOT: CLI boundary remains canonical for code/tool authority.
- ADR: required only for unresolved cache naming or authority trade-offs.

## Rule placement

- Rule: LLM-owned retrieval behavior belongs in BDD because it describes how the agent/searcher should act across multi-step record/source/test discovery flows.
- Scope: framework-global
- Primary record: `.lazy-harness/behavior/llm-owned-record-retrieval.md`
- Why not SDD only: the behavior is user/agent flow, not merely a component contract.
- Why not `.jcode`: shared lazy-harness framework behavior.
- Confirmation: user-corrected on 2026-06-06 that BDD is required before SDD/TDD-only planning.
