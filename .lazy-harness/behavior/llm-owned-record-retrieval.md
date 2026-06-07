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
- Applies when:
  - an agent/searcher uses searchable record memory before answering, planning, or editing
  - an agent/searcher runs `lazy map <term-or-file>` to find candidate records/source/tests
  - `## Index header` or other metadata suggests records/source/tests
  - retrieved metadata conflicts, is incomplete, or could be mistaken for semantic authority
- Must:
  - use metadata as a starting cue only
  - treat `lazy map` output as drill-down candidates, not evidence that anything was read
  - read the real record body/Rule digest/Implementation map before relying on a record
  - inspect source/tests when a plan or mutation depends on implementation facts
  - ask a 3-5 option gate when meanings/layers still conflict after evidence reads
  - create or update durable records after user confirmation when missing host knowledge is found
- Must not:
  - answer or mutate based only on cache/header existence
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
When the agent runs `lazy map <term-or-file>`
Then the output may suggest feature, record, graph, source, and test candidates
But those candidates are cue-only
And the agent must still read the actual record body, Implementation map, source, and tests before answering or mutating.

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

## Usability checks

- The behavior should make it obvious to an agent that metadata is a navigation aid, not an answer.
- The behavior should reduce repeated broad grep work without replacing evidence reads.
- The behavior should surface ambiguity early instead of silently ranking candidate meanings.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/behavior/llm-owned-record-retrieval.md` — this BDD behavior record.
  - `.lazy-harness/domain/searchable-record-memory.md` — DDD terms used by the scenarios.
  - `.lazy-harness/scripts/record-map.ts` — read-only `lazy map` implementation that lists cue-only candidates.
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh` — injects static search/read debt reminder.
  - `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py` — guards mutation until evidence exists.
  - `.lazy-harness/planning/searchable-record-context-retrieval-tasks.md` — schedules the layer package.
- Key symbols:
  - `buildRecordMap` (`.lazy-harness/scripts/record-map.ts`) — emits candidate records/source/tests/graph ids without semantic-authority fields.
- Flow:
  1. Static reminder tells the agent to inspect real records/source/tests.
  2. `lazy map` or metadata may suggest candidate records or files.
  3. Agent reads canonical evidence and resolves or gates ambiguity.
  4. Confirmed missing knowledge is persisted into records.
- Tests / protection:
  - `.lazy-harness/tests/pre-action-search-evidence-guard.md` — protects evidence before action.
  - `.lazy-harness/tests/record-index-header.md` — includes `lazy map` drill-down output and no-semantic-authority checks.
- Cross-layer links:
  - DDD: `.lazy-harness/domain/searchable-record-memory.md`
  - SDD: `.lazy-harness/spec/platform/search-read-debt-contract.md`
  - TDD: `.lazy-harness/tests/pre-action-search-evidence-guard.md`
  - SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`
  - Planning: `.lazy-harness/planning/searchable-record-context-retrieval-tasks.md`
- Machine index:
  - graph ids: `kg_llm_owned_retrieval_behaves_from_domain`, `kg_record_index_header_layer_package_planned`
  - generated index key: pending until index generator exists

## Layer completeness impact

- DDD: depends on searchable record memory terminology.
- BDD: this record covers expected agent/searcher behavior.
- SDD: future Index Header contract must cite this behavior.
- TDD: future fixtures should protect every scenario listed above.
- SSOT: CLI boundary remains canonical for code/tool authority.
- ADR: required only for unresolved cache naming or authority trade-offs.

## Rule placement

- Rule: LLM-owned retrieval behavior belongs in BDD because it describes how the agent/searcher should act across multi-step record/source/test discovery flows.
- Scope: framework-global
- Primary record: `.lazy-harness/behavior/llm-owned-record-retrieval.md`
- Why not SDD only: the behavior is user/agent flow, not merely a component contract.
- Why not `.jcode`: shared lazy-harness framework behavior.
- Confirmation: user-corrected on 2026-06-06 that BDD is required before SDD/TDD-only planning.
