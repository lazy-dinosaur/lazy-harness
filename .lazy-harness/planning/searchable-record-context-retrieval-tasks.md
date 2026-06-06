# Task Backlog — Searchable Record Memory for LLM-Owned Retrieval

Status: proposed
Date: 2026-06-06
Related PRD: `.lazy-harness/prd/searchable-record-context-retrieval-prd.md`
Related plan: `.lazy-harness/planning/searchable-record-context-retrieval-implementation-plan.md`

## Rule placement

- Rule: cleanup and rebuild tasks for searchable record memory must be explicit so stale helper architecture cannot leak into future work.
- Scope: framework-global
- Primary record: `.lazy-harness/planning/searchable-record-context-retrieval-tasks.md`
- Why not AGENTS.md: execution backlog, not runtime grammar.
- Why not `.jcode`: framework-global implementation work.
- Confirmation: user-confirmed correction on 2026-06-06.

## Task status legend

- `todo`: not started
- `in-progress`: active branch work
- `done`: implemented and validated
- `blocked`: needs explicit decision
- `deferred`: intentionally postponed

## Milestone 0 — Decontamination first

### SCR-001 — Delete obsolete query-helper artifacts

- Status: done
- Type: source/schema/spec/test cleanup
- Delete tracked files:
  - `.lazy-harness/scripts/context-delivery.ts`
  - `.lazy-harness/scripts/relevant-record-query.ts`
  - `.lazy-harness/scripts/context-broker-dogfood.ts`
  - `.lazy-harness/schemas/context-delivery-packet.schema.json`
  - `.lazy-harness/schemas/relevant-record-index.schema.json`
  - `.lazy-harness/spec/platform/context-delivery-contract.md`
  - `.lazy-harness/spec/platform/relevant-record-query.md`
  - `.lazy-harness/spec/platform/context-broker-dogfood.md`
  - `.lazy-harness/tests/relevant-record-query-cli-equals-flags.md`
  - `.lazy-harness/tests/context-broker-dogfood.md`
  - obsolete `fixtures/context-delivery/*`
- Acceptance:
  - `git ls-files` shows none of the deleted paths
  - `lazy help` has no `context`, query-helper, or context-dogfood commands
  - self-test has no checks that require deleted artifacts

### SCR-002 — Rename runtime search/read debt journal

- Status: done
- Type: runtime contract
- Update:
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh`
  - `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py`
  - `.lazy-harness/hooks/lifecycle/helpers/check-response-rule-audit.py`
  - `.lazy-harness/scripts/lifecycle-check.py`
  - `.lazy-harness/scripts/prompt-budget.py`
  - `.lazy-harness/scripts/self-test.py`
  - `.lazy-harness/spec/platform/pre-response-rule-context.md`
  - `.lazy-harness/spec/platform/search-read-debt-contract.md`
  - runtime/shared-state records
- Change:
  - from `$LAZY_RUNTIME_ROOT/state/context-delivery-packets.jsonl`
  - to `$LAZY_RUNTIME_ROOT/state/search-read-debt.jsonl`
- Acceptance:
  - all runtime tests use the new filename
  - static prompt remains unchanged in behavior except obsolete generated-index inventory is removed

### SCR-003 — Remove active stale references

- Status: done
- Type: record cleanup
- Update/remove:
  - graph rows pointing to deleted helpers
  - candidates that recommend obsolete helper architecture
  - generated README/schema README/manifest descriptions
  - Jcode integration text
  - planning records that told agents to use the deleted architecture
- Acceptance:
  - root-bound grep finds no active instruction to use deleted query helpers
  - historical mentions, if any, are explicitly marked removed/superseded and do not include runnable commands

## Milestone 1 — Correct PRD/plan/task surface

### SCR-101 — Rewrite PRD around LLM-owned retrieval

- Status: done
- Type: PRD
- Acceptance:
  - no helper CLI takes raw user text to return semantic candidates
  - goals start with cleanup/static debt/header quality
  - acceptance criteria mention deleted helper absence

### SCR-102 — Rewrite implementation plan

- Status: done
- Type: planning
- Acceptance:
  - current state lists deleted artifacts and remaining allowed primitives
  - implementation phases are cleanup → static debt → index header SDD/TDD → cache/parser only after approval
  - validation commands are concrete

### SCR-103 — Rewrite HTML report

- Status: done
- Type: report
- Acceptance:
  - report explains why previous plan was wrong
  - report shows deleted artifacts and corrected flow
  - report links to corrected PRD/tasks/plan

## Milestone 2 — Guard deleted helper absence

### SCR-201 — Add self-test absence check

- Status: done
- Type: TDD/source
- Update:
  - `.lazy-harness/scripts/self-test.py`
- Requirements:
  - deleted source/schema/spec/test files must not exist
  - `lazy help` must not list deleted commands
  - hook code must not invoke deleted query helpers
- Acceptance:
  - `python3 .lazy-harness/scripts/self-test.py` passes

### SCR-202 — Update graph/generated indexes

- Status: done
- Type: hygiene
- Requirements:
  - remove graph edges to deleted files
  - regenerate implementation index if needed
  - run graph-hygiene
- Acceptance:
  - no graph rows target deleted paths
  - graph-hygiene passes

## Milestone 3 — Record Index Header Layer Package, no query helper

### SCR-301 — Create/maintain DDD searchable record memory terminology

- Status: done
- Type: DDD
- Create/Update:
  - `.lazy-harness/domain/searchable-record-memory.md`
- Requirements:
  - define Searchable Record Memory
  - define record-authored metadata
  - define Record Index Header
  - define LLM-owned retrieval
  - define semantic authority
  - define deterministic cache
  - state that metadata improves findability, not authority
- Acceptance:
  - DDD includes Rule digest, ubiquitous language table, domain invariants, implementation map, layer completeness, and rule placement
  - DDD cross-links BDD/SDD/TDD/SSOT/planning

### SCR-302 — Create/maintain BDD LLM-owned retrieval behavior

- Status: done
- Type: BDD
- Create/Update:
  - `.lazy-harness/behavior/llm-owned-record-retrieval.md`
- Requirements:
  - scenario: metadata cue still requires real record read
  - scenario: conflicting meanings require option gate
  - scenario: cache hit is not proof of evidence
  - scenario: missing knowledge converges after confirmation
  - scenario: new retrieval concept triggers layer package
- Acceptance:
  - BDD includes Rule digest, scenarios, usability checks, implementation map, layer completeness, and rule placement
  - BDD cross-links DDD/SDD/TDD/SSOT/planning

### SCR-303 — Create Record Index Header SDD

- Status: done
- Type: SDD
- Create:
  - `.lazy-harness/spec/platform/record-index-header.md`
- Requirements:
  - define record-authored metadata fields
  - clarify it is for storage/searchability, not raw-message matching authority
  - define relationship to DDD terms, BDD scenarios, `Rule digest`, `Implementation map`, and graph rows
  - include example header
- Acceptance:
  - SDD includes Rule digest, implementation map, layer completeness, and rule placement
  - SDD cites `.lazy-harness/domain/searchable-record-memory.md` and `.lazy-harness/behavior/llm-owned-record-retrieval.md`

### SCR-304 — Create Record Index Header TDD

- Status: done
- Type: TDD
- Create:
  - `.lazy-harness/tests/record-index-header.md`
- Requirements:
  - complete header fixture
  - missing header warning fixture
  - legacy Rule digest fallback fixture
  - no raw-message semantic query fixture
  - cache hit is not proof of evidence fixture
  - conflict requires option gate fixture
- Acceptance:
  - TDD names future self-test fixtures without implementing parser yet
  - TDD maps every BDD scenario to at least one future fixture or existing guard

### SCR-305 — SSOT/ADR semantic-authority boundary review

- Status: done
- Type: SSOT/ADR review
- Requirements:
  - verify `.lazy-harness/ssot/cli-tool-boundary.md` covers Index Header/cache work
  - decide whether a new ADR is needed for `context-index` vs `record-index` naming before SCR-401
  - explicitly record “no new ADR needed” if existing SSOT is sufficient
- Acceptance:
  - plan records cite the SSOT/ADR decision result before parser/cache implementation starts

## Milestone 4 — Deterministic cache/parser only after approval

- Result: existing `.lazy-harness/ssot/cli-tool-boundary.md` is sufficient for SCR-303/304; no new ADR needed now. SCR-401 naming/scope remains blocked behind option gate and may require ADR after user choice.

### SCR-401 — Context index cache rename/contract review

- Status: blocked
- Type: decision gate
- Decision needed:
  - keep `context-index` name, or rename to `record-index` to avoid obsolete architecture language
- Acceptance before coding:
  - user approves exact command/name/scope
  - no raw-message query input
  - output is cache/listing only

### SCR-402 — Parser/cache implementation

- Status: blocked
- Type: source/test
- Prerequisite:
  - SCR-401 approved
- Acceptance:
  - deterministic record-authored fields only
  - no requiredRead/confidence/intent/risk/gate/nextAction
  - source scan/read remains the LLM/searcher responsibility

## Milestone 5 — Record audit advisory warnings

### SCR-501 — Extend record-audit

- Status: todo
- Type: source/test
- Requirements:
  - warn `missing-index-header`
  - warn `missing-alias-or-search-key`
  - warn `missing-source-test-hints`
  - warn `missing-graph-link`
  - advisory only for historical records
- Acceptance:
  - `lazy record-audit --format=json` reports counts
  - self-test covers at least complete/missing historical cases

## Milestone 6 — Implementation-map backlog

### SCR-601 — Produce needs-map backlog

- Status: todo
- Type: audit/planning
- Command:
  - `.lazy-harness/bin/lazy impl-map --format=json`
- Acceptance:
  - exact needs-map list captured
  - migration batches proposed before edits

### SCR-602 — Migrate verified implementation maps

- Status: deferred
- Type: record migration
- Acceptance:
  - only verified source/test/graph links are recorded
  - graph-hygiene remains green

## Milestone 7 — Host sync validation

### SCR-701 — Sync cleanup to hosts

- Status: done
- Type: dogfood
- Requirements:
  - sync framework source to selected hosts
  - run host `lazy test` and doctor smoke
  - verify removed helper artifacts prune from hosts
- Acceptance:
  - no stale helper commands/files in synced hosts
  - static search/read-debt reminder still works
- Evidence: `.lazy-harness/evidence/2026-06-06-searchable-record-memory-host-sync.md`
- Result: 13 initialized downstream hosts synced to marker `34c1ef2`; stale files/help/hook checks all zero.

## Discovery capture

- DDD: `searchable-record-memory` created for terminology/invariants.
- BDD: `llm-owned-record-retrieval` created for agent/searcher behavior.
- SDD: `search-read-debt-contract` created; `record-index-header` created for header field/consumer contract.
- TDD: deleted-helper absence and static debt tests planned/updated; `record-index-header` created for fixture expectations.
- SSOT/ADR: `cli-tool-boundary` reviewed as sufficient for SCR-303/304; SCR-401 naming gate may need ADR later.
- SSOT: CLI tool boundary remains canonical.
- Planning: native query-helper plan removed; this backlog is the replacement.
- ADR: no new ADR until a new trade-off decision is needed.
