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
- Applies when:
  - defining searchable record memory terminology
  - defining `## Index header` or record-authored retrieval metadata
  - deciding whether code, cache, or LLM/searcher owns retrieval meaning
- Must:
  - treat records as canonical memory and generated caches as rebuildable aids
  - treat Record Index Header fields as record-authored search cues
  - keep meaning, priority, ambiguity, gate, and next-action decisions with the LLM/searcher after real evidence reads
  - distinguish storage/searchability metadata from semantic authority
- Must not:
  - define Index Header as a raw-user-message query interface
  - define cache hits as proof that a record/source/test was read
  - use metadata names that imply required-read or confidence decisions unless the LLM/searcher has read real evidence
- Record completion:
  - changes to terms below update DDD, BDD, SDD, TDD, PRD/tasks/plan, and graph links together.

## Ubiquitous language

| Term | Meaning | Not this |
|---|---|---|
| Searchable Record Memory | The durable `.lazy-harness` record system made easier for an LLM/searcher to rediscover through stable terms, implementation maps, graph links, and optional deterministic caches. | A RAG service, classifier, or lifecycle query backend. |
| Record-authored metadata | Metadata written inside canonical records, such as aliases, surface terms, source/test hints, graph ids, and future `## Index header` fields. | Generated judgement about the current user request. |
| Record Index Header | A planned record section that stores compact record-authored metadata for searchability. | A command, ranking system, or required-read selector. |
| LLM-owned retrieval | The process where the LLM/searcher performs root-bound search/read, inspects records/source/tests, then decides relevance and ambiguity. | Code-owned candidate selection from raw user text. |
| Semantic authority | The authority to decide intent, meaning, priority, required reads, risk, gate, or next action. In this framework, that authority belongs to the LLM/searcher plus canonical evidence, not deterministic helper code. | Deterministic parsing, validation, cache generation, or evidence bookkeeping. |
| Deterministic cache | A rebuildable cache derived from already-authored records/source/graph data. | Canonical memory or proof of read evidence. |

## Domain invariants

1. Canonical memory lives in records and source/test evidence, not generated caches.
2. Record Index Header improves findability, not authority.
3. A cache may list metadata but must not answer, “what does this user mean?”
4. LLM/searcher may use metadata as a starting point only after reading real records/source/tests.
5. Conflicting candidate meanings require an option gate, not automatic ranking.
6. Missing host knowledge converges into the right layer only after source evidence and/or user confirmation.

## Implementation map

- Status: `planned`
- Primary files:
  - `.lazy-harness/domain/searchable-record-memory.md` — defines the domain terms and invariants for searchable record memory.
  - `.lazy-harness/behavior/llm-owned-record-retrieval.md` — records the expected agent/searcher behavior that uses these terms.
  - `.lazy-harness/planning/searchable-record-context-retrieval-tasks.md` — schedules DDD/BDD/SDD/TDD layer package tasks.
  - `.lazy-harness/prd/searchable-record-context-retrieval-prd.md` — product requirements for searchable record memory.
- Key symbols:
  - none; this is terminology/behavior planning, not implementation code.
- Flow:
  1. DDD defines what “searchable record memory” and “semantic authority” mean.
  2. BDD describes how agents behave when metadata exists or conflicts.
  3. SDD/TDD will define and protect `## Index header` structure.
  4. Only after the layer package is accepted may deterministic cache/parser work be considered.
- Tests / protection:
  - Future `.lazy-harness/tests/record-index-header.md` will protect the no-semantic-query invariant.
  - Existing `.lazy-harness/scripts/self-test.py` protects deleted helper absence and static search/read debt.
- Cross-layer links:
  - BDD: `.lazy-harness/behavior/llm-owned-record-retrieval.md`
  - SDD: `.lazy-harness/spec/platform/search-read-debt-contract.md`
  - SDD: `.lazy-harness/spec/platform/pre-response-rule-context.md`
  - TDD: `.lazy-harness/tests/pre-action-search-evidence-guard.md`
  - SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`
  - Planning: `.lazy-harness/planning/searchable-record-context-retrieval-tasks.md`
- Machine index:
  - graph ids: `kg_searchable_record_memory_defines_domain`, `kg_llm_owned_retrieval_behaves_from_domain`
  - generated index key: pending until index generator exists

## Layer completeness impact

- DDD: this record supplies terminology and invariants.
- BDD: `.lazy-harness/behavior/llm-owned-record-retrieval.md` supplies behavior scenarios.
- SDD: future `record-index-header.md` must cite these terms.
- TDD: future `record-index-header.md` TDD must test “metadata is not semantic authority.”
- SSOT: `.lazy-harness/ssot/cli-tool-boundary.md` remains the boundary for code/tool authority.
- ADR: needed only if a future naming/cache trade-off cannot be resolved by existing SSOT.

## Rule placement

- Rule: searchable record memory terms and semantic-authority boundaries are domain vocabulary.
- Scope: framework-global
- Primary record: `.lazy-harness/domain/searchable-record-memory.md`
- Why not SDD only: the terms apply before any specific component contract.
- Why not `.jcode`: shared framework behavior, not local/private wiring.
- Confirmation: user-corrected on 2026-06-06 that DDD/BDD must be included before SDD/TDD-only planning.
