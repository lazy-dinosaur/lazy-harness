# Task Backlog — Searchable Record Context Retrieval

Status: proposed
Date: 2026-06-06
Related PRD: `.lazy-harness/prd/searchable-record-context-retrieval-prd.md`
Related plan: `.lazy-harness/planning/searchable-record-context-retrieval-implementation-plan.md`

## Rule placement

- Rule: Implementation tasks for searchable record context retrieval should be tracked as a planning backlog with SDD/TDD/SSOT links, not left in chat.
- Scope: framework-global
- Primary record: `.lazy-harness/planning/searchable-record-context-retrieval-tasks.md`
- Why not AGENTS.md: this is execution backlog and sequencing, not runtime prompt grammar.
- Why not `.jcode`: framework-global implementation backlog, not local/private Jcode wiring.
- Confirmation: user-confirmed

## Task status legend

- `todo`: not started
- `blocked`: needs decision/user approval
- `in-progress`: active branch work
- `done`: implemented and validated
- `deferred`: intentionally postponed

## Milestone 0 — Approval and scope lock

### SCR-000 — Confirm Phase 1 implementation boundary

- Status: todo
- Type: planning gate
- Primary records:
  - `.lazy-harness/planning/searchable-record-context-retrieval-implementation-plan.md`
  - `.lazy-harness/prd/searchable-record-context-retrieval-prd.md`
- Scope:
  - approve only Phase 1 before coding
  - keep later phases as backlog
- Acceptance:
  - user approves exact SDD/TDD/files/parser fields/warning names for Phase 1
  - no implementation starts before approval

## Milestone 1 — Record Index Header Standard

### SCR-101 — Create Record Index Header SDD

- Status: todo
- Type: SDD
- Create:
  - `.lazy-harness/spec/platform/record-index-header.md`
- Update:
  - `.lazy-harness/spec/platform/record-digest-format.md`
  - `.lazy-harness/ssot/cli-tool-boundary.md`
- Requirements:
  - define `## Index header` field names
  - define relationship with `Rule digest` and `Implementation map`
  - define structured fields allowed for candidate matching
  - forbid generic prose matching as product-surface evidence
  - include Rule placement and Implementation map
- Acceptance:
  - SDD includes Rule digest
  - SDD includes example complete header
  - SDD includes migration/fallback behavior for legacy records

### SCR-102 — Create Record Index Header TDD

- Status: todo
- Type: TDD
- Create:
  - `.lazy-harness/tests/record-index-header.md`
- Requirements:
  - fixture complete record with index header
  - fixture legacy record without header but with Rule digest fallback
  - fixture framework-global example prose that must not become host product candidate
  - fixture missing alias/search key warning
- Acceptance:
  - TDD lists self-test function names to add
  - TDD includes SDD/BDD/SSOT/DDD impact notes

### SCR-103 — Add context-index parser support

- Status: todo
- Type: source
- Update:
  - `.lazy-harness/scripts/context-index.ts`
- Requirements:
  - parse `## Index header`
  - expose `recordId`, `indexHeaderSource`, `primaryAliases`, `searchKeys`, `surfaceTerms`, `sourceFiles`, `testFiles`, `graphIds`
  - preserve current Rule digest fallback
  - avoid semantic judgment fields
- Acceptance:
  - `lazy context-index --write --format=json` includes new fields
  - source-scan fallback still works
  - no requiredRead/confidence/intent/risk fields

### SCR-104 — Add self-test fixtures for index header parsing

- Status: todo
- Type: test
- Update:
  - `.lazy-harness/scripts/self-test.py`
- Requirements:
  - temp record with Index header parsed into context-index
  - context-delivery returns candidate hit from index header alias/search key
  - generic Must/Applies prose does not match as product candidate
- Acceptance:
  - `python3 .lazy-harness/scripts/self-test.py` passes

## Milestone 2 — Record Audit Enforcement

### SCR-201 — Extend record-audit with searchable metadata checks

- Status: todo
- Type: source
- Update:
  - `.lazy-harness/scripts/record-audit.ts`
  - `.lazy-harness/spec/platform/record-digest-format.md`
- Requirements:
  - detect `missing-index-header`
  - detect `missing-alias-or-search-key`
  - detect `missing-source-test-hints`
  - detect `missing-graph-link`
  - include implementation-map status
- Acceptance:
  - `lazy record-audit --format=json` reports summary counts
  - warnings are advisory for historical records

### SCR-202 — Add record-audit TDD coverage

- Status: todo
- Type: test
- Update:
  - `.lazy-harness/scripts/self-test.py`
  - possibly `.lazy-harness/tests/record-index-header.md`
- Requirements:
  - complete record has no warning
  - missing header warning appears
  - historical ADR missing header is warning, not hard block
- Acceptance:
  - `lazy test` passes

## Milestone 3 — Context Index Productization

### SCR-301 — Write context-index cache with header fields

- Status: todo
- Type: source
- Update:
  - `.lazy-harness/scripts/context-index.ts`
  - `.lazy-harness/generated/README.md`
- Requirements:
  - generated `context-index.json` includes index header fields
  - include record fingerprint/stale metadata
  - document regeneration triggers
- Acceptance:
  - `lazy context-index --write --format=md` creates cache
  - deleting cache still falls back to source scan

### SCR-302 — Add context-index generated cache self-test

- Status: todo
- Type: test
- Update:
  - `.lazy-harness/scripts/self-test.py`
- Acceptance:
  - validates generated cache path
  - validates source-scan fallback

## Milestone 4 — Relevant Record Query Candidate-Only Revision

### SCR-401 — Revise relevant-record-query contract

- Status: todo
- Type: SDD/source
- Update:
  - `.lazy-harness/spec/platform/relevant-record-query.md`
  - `.lazy-harness/scripts/relevant-record-query.ts`
  - `.lazy-harness/schemas/relevant-record-index.schema.json`
- Requirements:
  - rename score/ranking language to matched cues/source order
  - output `candidateRecords`, `matchedFields`, `matchedQueries`, `fallbackSearches`, `notes`
  - no requiredRead/confidence/importance/intent/risk
- Acceptance:
  - schema forbids semantic authority fields
  - helper remains explicit/manual only

### SCR-402 — Add relevant-record-query tests

- Status: todo
- Type: test
- Update:
  - `.lazy-harness/scripts/self-test.py`
- Acceptance:
  - query returns candidates only
  - no lifecycle hook invokes it automatically

## Milestone 5 — Graph Query Candidate Tool

### SCR-501 — Design graph-query SDD/TDD

- Status: todo
- Type: SDD/TDD
- Create/update:
  - `.lazy-harness/spec/platform/graph-query.md`
  - `.lazy-harness/tests/graph-query.md`
  - `.lazy-harness/ssot/implementation-map-storage.md`
- Requirements:
  - candidate-only graph neighbor query
  - by record path, graph id, source file path
  - no importance/requiredRead/nextAction

### SCR-502 — Implement graph-query CLI

- Status: todo
- Type: source
- Create:
  - `.lazy-harness/scripts/graph-query.ts`
- Update:
  - `.lazy-harness/bin/lazy`
  - `.lazy-harness/scripts/self-test.py`
- Acceptance:
  - `lazy graph-query --path <record>` returns linked candidate files/records
  - `lazy graph-query --impacted-file <file>` returns candidate records/tests
  - graph-hygiene remains green

## Milestone 6 — Implementation Map Backlog

### SCR-601 — Produce needs-map backlog report

- Status: todo
- Type: audit
- Command:
  - `lazy impl-map --format=json`
- Acceptance:
  - exact list of 31 needs-map records captured in a planning record or generated report

### SCR-602 — Migrate ADR batches

- Status: todo
- Type: record migration
- Batches:
  - ADR 0001-0010
  - ADR 0011-0020
  - ADR 0021-0030
- Acceptance:
  - each touched ADR has Implementation map or explicit `Status: none/planned`
  - graph rows only for verified links

### SCR-603 — Migrate residual TDD/SDD records

- Status: todo
- Type: record migration
- Acceptance:
  - needs-map count decreases to 0 or accepted historical statuses

## Milestone 7 — Host Profile and Feature Navigation Dogfood

### SCR-701 — Audit host project profiles

- Status: todo
- Type: dogfood
- Hosts:
  - `/home/lazydino/dev/medivance`
  - `/home/lazydino/dev/medivance-homepage`
  - `/home/lazydino/dev/medivance-pwa`
- Check:
  - project/profile.xml
  - project/stack.xml
  - project/filesystem.xml
  - project/feature-navigation.xml
  - tests/test-strategy.xml
- Acceptance:
  - gaps recorded as host planning/SSOT candidates, not chat-only

### SCR-702 — Dogfood product-surface candidate queries

- Status: todo
- Type: dogfood
- Commands:
  - `lazy context-delivery --message "<host term>" --format=json`
  - `lazy context-index --write --format=md`
- Acceptance:
  - host product aliases return candidate hits
  - framework example prose does not become host product candidate

## Milestone 8 — Prompt and Skill Search Instructions

### SCR-801 — Compact search protocol prompt update

- Status: todo
- Type: prompt/SDD
- Update:
  - `.lazy-harness/AGENTS.md`
  - `.lazy-harness/spec/platform/pre-response-rule-context.md`
- Requirements:
  - mention Index header / Rule digest / Implementation map / graph / feature navigation as search surfaces
  - keep token budget small
- Acceptance:
  - `lazy prompt-budget --format=json` pass/warn and duplicates 0

### SCR-802 — Optional skill wrapper for context search

- Status: todo
- Type: skill
- Scope:
  - only if it helps LLM use tools correctly
  - must not add semantic authority
- Acceptance:
  - skill points to SDD/SSOT, not duplicate long rules

## Milestone 9 — Sync and Cross-host Validation

### SCR-901 — Source validation

- Status: todo
- Type: validation
- Commands:
  - `python3 .lazy-harness/scripts/self-test.py`
  - `.lazy-harness/bin/lazy test`
  - `.lazy-harness/bin/lazy prompt-budget --format=json`
  - `.lazy-harness/bin/lazy graph-hygiene --format=json --fail-on-issues`

### SCR-902 — Host sync and managed-file comparison

- Status: todo
- Type: validation
- Hosts:
  - medivance
  - medivance-homepage
  - medivance-pwa
- Acceptance:
  - sync markers match source HEAD
  - managed files missing/mismatched = 0
  - known removed files absent
  - host `lazy test`, doctor smoke, prompt-budget pass/warn

## Cross-cutting non-goals for all tasks

- Do not add CLI-selected `requiredRead`.
- Do not add CLI `confidence`/importance/risk/intent/gate/nextAction.
- Do not add automatic lifecycle calls to context-delivery/relevant-record-query/graph-query.
- Do not make generated indexes canonical.
- Do not bloat runtime prompt with full templates.

## Discovery capture

- DDD: none
- SDD: candidate tasks SCR-101, SCR-401, SCR-501, SCR-801
- BDD: candidate after host dogfood SCR-701/SCR-702
- TDD: candidate tasks SCR-102, SCR-104, SCR-202, SCR-302, SCR-402, SCR-501/SCR-502
- ADR: possible if Index header vs Rule digest extension becomes a trade-off decision
- SSOT: candidate/updated through CLI boundary and implementation-map storage references
- Planning: updated by this task backlog
