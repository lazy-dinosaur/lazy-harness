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

- Result: existing `.lazy-harness/ssot/cli-tool-boundary.md` is sufficient for SCR-303/304; ADR 0042 now records SCR-401 canonical `record-index` naming. SCR-402 may start as implementation planning/work under no-semantic-authority constraints.

### SCR-401 — Record-index cache/listing naming decision

- Status: done
- Type: ADR/SSOT decision
- Decision:
  - canonical future command/cache/schema naming surface is `record-index`
  - existing `context-index` may remain only as legacy/deprecated compatibility during SCR-402 migration, if tests justify it
  - exact scope is deterministic record-authored metadata listing/cache generation only
- Acceptance before coding:
  - user approved Option A on 2026-06-06
  - no raw-message query input
  - output is cache/listing only
  - ADR recorded in `.lazy-harness/decisions/0042-record-index-cache-naming.md`
- Result: SCR-402 may start as implementation planning/work, but must not add semantic authority or raw-message query behavior.

### SCR-402 — Record-index parser/cache implementation

- Status: done
- Type: source/test
- Decision:
  - Option A selected: replace old cache/listing surface with `record-index` only.
  - No hidden or visible `context-index` alias remains.
- Result:
  - CLI command: `.lazy-harness/bin/lazy record-index [--write] [--format=json|md]`
  - Source: `.lazy-harness/scripts/record-index.ts`
  - Schema: `.lazy-harness/schemas/record-index.schema.json`
  - Cache path: `.lazy-harness/generated/record-index.json`
  - Lazy sync prunes old managed context-index source/schema/cache files from downstream hosts.
- Acceptance:
  - canonical command/cache naming uses `record-index`
  - old `context-index` command/source/schema/cache paths are absent except historical record text and absence tests
  - deterministic record-authored fields only
  - no raw-message query input
  - no requiredRead/confidence/intent/risk/gate/nextAction
  - source scan/read remains the LLM/searcher responsibility
- Planning: `.lazy-harness/planning/record-index-parser-cache-migration-plan.md`
- Validation:
  - `.lazy-harness/bin/lazy record-index --format=json` smoke output method is `record-index-v1`.
  - `python3 .lazy-harness/scripts/self-test.py` protects record-index generation and old command absence.

### SCR-403 — Record Map overview/drill-down CLI

- Status: done
- Type: source/test/record update
- Decision:
  - Add `lazy map --overview` as the mandatory whole-structure first pass before token search.
  - Add repeated `lazy map <term-or-file>` calls as read-only drill-down helpers over record-index, feature navigation, and graph rows.
  - User-confirmed correction (2026-06-07): search must not stop after one “core token”; related records/source/tests can be dispersed, so the agent must repeat query-map across candidate tokens/files/layers until coverage is sufficient.
  - Output remains cue-only and cannot satisfy search/read debt by itself.
- Result:
  - CLI commands: `.lazy-harness/bin/lazy map --overview [--format=json|md] [--limit=N]`, then repeated `.lazy-harness/bin/lazy map <term-or-file> [--format=json|md] [--limit=N]`
  - Source: `.lazy-harness/scripts/record-map.ts`
  - AGENTS/search reminder routine is overview-first, then token map, then grep fallback when empty/ambiguous/incomplete.
  - DDD/BDD/SDD/TDD/SSOT records updated for Record Map terminology, behavior, contract, fixture, and boundary.
- Acceptance:
  - overview output includes record/layer/feature/graph structure before search-term selection
  - repeated token/file/layer output includes feature/record/graph matches plus `drilldown.recordPaths`, `sourceFiles`, `testFiles`, and `graphIds`
  - no requiredRead/confidence/intent/risk/gate/nextAction/candidateMeanings output
  - self-test covers overview output, token fixture output, exact reminder CLI, and help dispatch
- Validation:
  - `.lazy-harness/bin/lazy map record-index --format=md --limit=3` smoke passed.
  - `python3 .lazy-harness/scripts/self-test.py` protects `lazy map` via `check_record_index_generator_phase3`.

## Milestone 5 — Record audit advisory warnings

### SCR-501 — Extend record-audit

- Status: done
- Type: source/test
- Decision:
  - Option A selected: add structured `recordQuality` counts/samples while keeping `warnings[]` as human summaries.
- Result:
  - `lazy record-audit --format=json` includes `recordQuality.advisoryOnly`, `inspectedRecords`, `completeRecords`, `counts`, and `issues[].samplePaths`.
  - Advisory codes: `missing-index-header`, `missing-alias-or-search-key`, `missing-source-test-hints`, `missing-graph-link`.
  - Historical records are not invalidated; warnings are advisory only.
- Acceptance:
  - `lazy record-audit --format=json` reports counts
  - self-test covers complete/missing historical cases in `check_record_audit_cli`
- Validation:
  - Focused `record-audit` JSON smoke passed.
  - `python3 .lazy-harness/scripts/self-test.py` passed 72/72.

## Milestone 6 — Implementation-map backlog

### SCR-601 — Produce needs-map backlog

- Status: done
- Type: audit/planning
- Command:
  - `.lazy-harness/bin/lazy impl-map --format=json`
- Result:
  - dynamic audit output captured in `.lazy-harness/planning/scr-601-implementation-map-needs-map.md`
  - current summary: `ok=80`, `needs-map=31`, `needs-review=0`
  - `needs-map` is not static; it is emitted when current records have implementation hints but no `## Implementation map`
  - migration batches proposed before any implementation-map edits
- Acceptance:
  - exact needs-map list captured
  - migration batches proposed before edits

### SCR-602 — Migrate verified implementation maps

- Status: done
- Type: record migration
- Input:
  - `.lazy-harness/planning/scr-601-implementation-map-needs-map.md`
- Progress:
  - Batch 1 completed for the two TDD regression records.
  - Batch 2 completed for eight framework tooling/storage ADRs.
  - Batch 3 completed for five lifecycle/gate/graph ADRs.
  - Batch 4 completed for sixteen foundational/legacy ADRs.
  - dynamic `lazy impl-map --format=json` summary moved from `ok=80, needs-map=31` to `ok=111, needs-map=0`.
  - `.lazy-harness/tests/lazy-sync-dirty-false-positive.md` map is `needs-review` because the dirty-source regression remains manual-only.
  - `.lazy-harness/tests/response-completed-route-telemetry-large-payload.md` map is `verified` by `check_response_completed_no_auto_route_telemetry`.
  - Batch 2 statuses: ADR 0022/0026/0029/0030 verified; ADR 0016/0023/0024/0025 needs-review because they are historical, broad, or partially superseded.
  - Batch 3 statuses: all five ADR maps are `needs-review`; ADR 0017 also records stale `triggers/external` framework-contract conflict.
  - Batch 4 statuses: ADR 0008/0013 verified; all other legacy/foundational ADR maps are `needs-review` with conflict/supersession notes where current source diverges.
- Constraint:
  - future implementation-map edits must still inspect source/test/graph evidence per record before writing maps
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
- Follow-up result: selected hosts `medivance`, `medivance-pwa`, and `medivance-homepage` synced to marker `30e9866` after SCR-402/SCR-501/SCR-601/SCR-602; `record-index` present, `context-index` absent, host `lazy test` passed. Evidence: `.lazy-harness/evidence/2026-06-06-selected-medivance-host-sync-record-index.md`.

## Discovery capture

- DDD: `searchable-record-memory` created for terminology/invariants.
- BDD: `llm-owned-record-retrieval` created for agent/searcher behavior.
- SDD: `search-read-debt-contract` created; `record-index-header` created/updated for header field, record-index cache, and Record Map consumer contract.
- TDD: deleted-helper absence and static debt tests planned/updated; `record-index-header` created/updated for fixture expectations including Record Map.
- SSOT/ADR: `cli-tool-boundary` reviewed/updated for SCR-303/304/SCR-403; ADR 0042 records SCR-401 canonical `record-index` naming decision.
- SSOT: CLI tool boundary remains canonical.
- Planning: native query-helper plan removed; this backlog is the replacement.
- ADR: no new ADR until a new trade-off decision is needed.
