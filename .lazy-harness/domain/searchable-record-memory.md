# DDD — Searchable Record Memory

Status: accepted
Date: 2026-06-06
Layer: DDD
Related PRD: `.lazy-harness/prd/searchable-record-context-retrieval-prd.md`
Related BDD: `.lazy-harness/behavior/llm-owned-record-retrieval.md`
Related SDD: `.lazy-harness/spec/platform/search-read-debt-contract.md`
Related SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`

## Rule digest

- Status: active
- Layer: DDD
- Scope: framework-global
- Aliases:
  - 검색 가능 기억
  - record memory
  - 기억 장치 용어
  - Harness Reader
  - Reader join
  - Parent code lane
- Applies when:
  - defining searchable record memory terminology
  - defining `## Index header` or record-authored retrieval metadata
  - deciding whether code, cache, or LLM/searcher owns retrieval meaning
  - deciding whether code, cache, Parent, or a dedicated Harness Reader owns retrieval meaning
- Must:
  - treat records as canonical memory and generated caches as rebuildable aids
  - treat Record Index Header fields as record-authored search cues
  - keep meaning, priority, ambiguity, gate, and next-action decisions with the Parent after canonical evidence is supplied
  - let one dedicated Harness Reader own map-first search and relevant canonical record reads across all stored harness layers
  - let the Parent investigate source/tests or immediately needed behavior concurrently, then join the Reader response before action
  - treat successful Reader completion as work-unit record context rather than a reason for duplicate Parent read-debt work
  - treat map/read evidence as instruction-scoped: a new accepted mid-turn steer makes prior-instruction evidence stale for later actions
- Must not:
  - define Index Header as a raw-user-message query interface
  - define cache hits as proof that a record/source/test was read
  - use metadata names that imply required-read or confidence decisions unless an LLM/searcher has read real evidence
  - make the Parent preselect record nodes for the Reader or require routine Parent rereads after successful Reader completion
  - treat Reader output as source-code implementation analysis, a user decision, or mutation authority
- Record completion:
  - changes to terms below update DDD, BDD, SDD, TDD, PRD/tasks/plan, and graph links together.

## Ubiquitous language

| Term | Meaning | Not this |
|---|---|---|
| Searchable Record Memory | The durable `.lazy-harness` record system made easier for an LLM/searcher to rediscover through stable terms, implementation maps, graph links, and optional deterministic caches. | A RAG service, classifier, or lifecycle query backend. |
| Record-authored metadata | Metadata written inside canonical records, such as aliases, surface terms, source/test hints, graph ids, and future `## Index header` fields. | Generated judgement about the current user request. |
| Record Index Header | A planned record section that stores compact record-authored metadata for searchability. | A command, ranking system, or required-read selector. |
| Record Map | A read-only CLI overview/drill-down helper (`lazy map --overview`, then repeated `lazy map <feature-id|record-path|graph-id|source-path>` on concrete nodes copied from the map) that surfaces whole record/feature/graph structure before node selection and then lists nearby record/source/test/graph candidates. | Proof that evidence was read, a semantic query engine, ranking authority, or a lifecycle classifier. |
| LLM-owned retrieval | The process where an LLM/searcher performs root-bound search/read, inspects canonical evidence, then reports relevance and ambiguity. In the orchestration flow this owner is the dedicated Harness Reader for stored harness records. | Code-owned candidate selection from raw user text. |
| Harness Reader | The read-only subagent that inventories `.lazy-harness`, selects and reads task-relevant DDD/SDD/BDD/TDD/ADR/SSOT/Planning records, and returns policies, facts, conflicts, missing information, and record paths. | A source-code investigator, decision maker, writer, or proof/audit engine. |
| Parent code lane | The Parent's concurrent investigation of source, tests, implementation reality, or immediately needed behavior while the Harness Reader loads stored records. | A second mandatory pass over every Reader-read record. |
| Reader join | The barrier before planning, mutation, or completion where the Parent waits for and consumes the Reader response. | Search/read-debt bookkeeping, candidate admission, or independent semantic certification. |
| Semantic authority | The authority to decide intent, meaning, priority, required reads, risk, gate, or next action. In this framework, that authority belongs to the LLM/searcher plus canonical evidence, not deterministic helper code. | Deterministic parsing, validation, cache generation, or evidence bookkeeping. |
| Deterministic cache | A rebuildable cache derived from already-authored records/source/graph data. | Canonical memory or proof of read evidence. |
| Instruction-scoped evidence | Root-bound map/read evidence collected after the latest user-instruction boundary. A non-extension mid-turn steer starts a new evidence epoch for later actions. | A user-text classifier, command allowlist, or claim that the earlier evidence became false. |

## Domain invariants

1. Canonical memory lives in records and source/test evidence, not generated caches.
2. Record Index Header improves findability, not authority.
3. A cache may list metadata but must not answer, “what does this user mean?”
4. LLM/searcher may use metadata as a starting point only after reading real records/source/tests.
5. Conflicting candidate meanings require an option gate, not automatic ranking.
6. Missing host knowledge converges into the right layer only after source evidence and/or user confirmation.
7. Evidence gathered for an earlier instruction cannot authorize mutation after a mid-turn steer; the agent must produce fresh root-bound evidence for the steered instruction.
8. One dedicated Harness Reader, not the Parent, owns complete stored-record inventory and task-relevant canonical loading for Reader-managed work units.
9. Parent source/test investigation may proceed concurrently, but plan/mutation/completion waits at the Reader join.
10. Successful Reader completion removes routine duplicate Parent record reads; conflict, incompleteness, Reader failure, or editing the record itself are bounded follow-up cases.

## Implementation map

- Status: `live-r2-terminal-incomplete; selected per-read-cap/source-lane correction focused-green; full-revalidation-and-new-live-approval-pending` — Reader ownership/transport is implemented; functional completion still requires a future separately approved canary.
- Primary files:
  - `.lazy-harness/domain/searchable-record-memory.md` — defines the domain terms and invariants for searchable record memory.
  - `.lazy-harness/behavior/llm-owned-record-retrieval.md` — records the implemented Reader/Parent parallel behavior and result/output barriers.
  - `packages/lazy-harness-pi/agents/record-reader.md` — implements the Harness Reader term as a canonical-record-only subagent.
  - `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — implements Reader launch/join/fingerprint lifecycle and Parent output preservation.
  - `.lazy-harness/evidence/dedicated-reader-runtime-v1-20260906.md` — static validation/review evidence.
  - `.lazy-harness/evidence/dedicated-reader-live-canary-r2-20260906.md` — live incomplete evidence and selected static correction.
  - `.lazy-harness/scripts/record-map.ts` — read-only Record Map implementation that emits cue-only overview and drill-down candidates.
  - `.lazy-harness/bin/lazy` — exposes `lazy map` and `lazy record-index` commands.
  - `.lazy-harness/planning/searchable-record-context-retrieval-tasks.md` — schedules DDD/BDD/SDD/TDD layer package tasks.
  - `.lazy-harness/prd/searchable-record-context-retrieval-prd.md` — product requirements for searchable record memory.
- Key symbols:
  - `buildRecordMap` (`.lazy-harness/scripts/record-map.ts`) — builds cue-only feature/record/graph overview from canonical records and graph rows.
  - `buildRecordIndex` (`.lazy-harness/scripts/record-index.ts`) — supplies deterministic record-authored metadata cache used by Record Map.
- Flow:
  1. DDD defines searchable record memory, Harness Reader, Parent code lane, and Reader join.
  2. BDD describes the parallel Reader/Parent behavior and join-before-action barrier.
  3. The Reader runs `lazy map --overview` across the stored harness memory.
  4. The Reader drills relevant feature/record/graph nodes and reads canonical records across all applicable layers.
  5. In parallel, the Parent inspects source/tests or immediately needed behavior.
  6. The Parent joins the Reader response before planning, mutation, or completion; conflict/incomplete status triggers bounded follow-up or an option gate.
  7. A non-extension mid-turn steer invalidates the earlier work-unit result before later action.
- Tests / protection:
  - `.lazy-harness/tests/record-index-header.md` protects the no-semantic-query invariant and map drill-down output.
  - `.lazy-harness/scripts/self-test.py` protects direct fallback, dedicated Reader package/launch/content/budget/join/reuse/steer behavior, and print-mode output separation.
- Cross-layer links:
  - BDD: `.lazy-harness/behavior/llm-owned-record-retrieval.md`
  - SDD: `.lazy-harness/spec/platform/search-read-debt-contract.md`
  - SDD: `.lazy-harness/spec/platform/pre-response-rule-context.md`
  - TDD: `.lazy-harness/tests/pre-action-search-evidence-guard.md`
  - SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`
  - Planning: `.lazy-harness/planning/searchable-record-context-retrieval-tasks.md`
  - SDD: `.lazy-harness/spec/platform/record-index-header.md`
- Machine index:
  - graph ids: `kg_searchable_record_memory_defines_domain`, `kg_llm_owned_retrieval_behaves_from_domain`, `kg_pi_steer_evidence_epoch_impl_20260713`
  - generated index key: pending until index generator exists

## Layer completeness impact

- DDD: updated here with Harness Reader, Parent code lane, and Reader join terms.
- BDD: `.lazy-harness/behavior/llm-owned-record-retrieval.md` defines the parallel workflow.
- SDD: `.lazy-harness/spec/platform/search-read-debt-contract.md` defines the isolated Reader completion/join implementation and direct fallback.
- TDD: `.lazy-harness/tests/pre-action-search-evidence-guard.md` and `.lazy-harness/tests/pi-agent-package.md` protect focused Reader behavior.
- SSOT: `.lazy-harness/ssot/harness-enforcement-policy.md` owns mandatory recall and transitional enforcement.
- ADR: `.lazy-harness/decisions/0055-agent-neutral-orchestration-core-pi-runtime.md` owns the confirmed responsibility change.

## Discovery capture — Harness Reader ownership correction

- DDD: updated — new orchestration vocabulary and invariants.
- SDD: updated — Reader join supersession direction is implemented focused-green in the isolated worktree.
- BDD: updated — parallel Reader-record and Parent-code lanes.
- TDD: updated — Reader join/fallback protection is focused-green; live model/main integration remain pending.
- ADR: updated — prior parent-global/child-scoped debt model superseded.
- SSOT: updated — Reader response join is the target mandatory-recall mechanism.
- Planning: updated — v3 proof remediation superseded by simple Reader orchestration.

## Discovery capture — Reader term implementation status

- DDD: updated here only to connect existing terms to verified isolated source symbols.
- SDD/BDD/TDD: implementation status updated in their owning records.
- ADR: ownership remains unchanged; isolated status updated.
- SSOT: direct debt remains fallback; main unchanged.
- Planning: isolated implementation is focused-green; live model/main integration remain gated.
## Rule placement

- Rule: searchable record memory terms and semantic-authority boundaries are domain vocabulary.
- Scope: framework-global
- Primary record: `.lazy-harness/domain/searchable-record-memory.md`
- Why not SDD only: the terms apply before any specific component contract.
- Why not `.jcode`: shared framework behavior, not local/private wiring.
- Confirmation: user-corrected on 2026-06-06 that DDD/BDD must be included before SDD/TDD-only planning.
