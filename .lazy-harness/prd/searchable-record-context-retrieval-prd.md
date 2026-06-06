# PRD — Searchable Record Context Retrieval

Date: 2026-06-06
Status: proposed
Owner: lazy-harness
Related plan: `.lazy-harness/planning/searchable-record-context-retrieval-implementation-plan.md`
Related task backlog: `.lazy-harness/planning/searchable-record-context-retrieval-tasks.md`

> This PRD is for the lazy-harness framework itself. It defines the product requirement for making durable project memory searchable and selectively readable by LLM agents without letting CLI tools become semantic authorities.

## 1. Product summary

Searchable Record Context Retrieval makes lazy-harness records usable as external memory for LLM agents.

The product turns records into:

```text
canonical human-readable knowledge
+ searchable metadata
+ graph/index pointers
+ explicit candidate retrieval tools
```

so that an LLM can satisfy generic read/search-debt by finding and reading only the relevant records/source/tests, while retaining responsibility for intent, importance, required-read judgment, and next action.

## 2. Target users

| Persona | Need |
|---|---|
| Main LLM agent | Quickly recover relevant project memory without loading everything |
| Searcher subagent | Return candidate records/source/tests with matched fields, not decisions |
| Framework maintainer | Enforce consistent searchable metadata at record-write time |
| Host project owner | Preserve domain/product rules so future agents can rediscover them |

## 3. Problem statement

LLMs forget or fail to retrieve the right project memory. Current records are canonical, but not every record has consistent searchable metadata.

Failure modes:

1. LLM cannot remember which records exist.
2. LLM opens too many files because there is no compact searchable header.
3. LLM misses host-specific aliases or product surface names.
4. Generated indexes exist but are incomplete/non-uniform.
5. Some records lack implementation map/source/test hints.
6. CLI tools are tempting to use as semantic classifiers, which violates the LLM-owned judgment rule.

## 4. Goals

1. Every reusable record has a searchable header or audited fallback metadata.
2. LLM/searcher can find candidate records from aliases, surface terms, source/test hints, graph ids, and related records.
3. Tools return candidate evidence only: paths, matched fields, matched queries, fallback searches.
4. Generic search/read-debt remains the enforcement mechanism.
5. CLI-selected `requiredRead`, `confidence`, `intent`, `risk`, `gate`, or `nextAction` are forbidden.
6. Generated indexes become useful caches but never canonical truth.
7. Host project feature navigation/profile records become queryable by candidate tools.
8. Record write/update workflows surface missing search metadata before future agents lose context.

## 5. Non-goals

- Do not reintroduce task-router or operational-state semantic classifiers.
- Do not require hosted/vector RAG.
- Do not make generated indexes canonical.
- Do not block all historical records immediately for missing index headers.
- Do not put full templates into the runtime prompt.
- Do not replace LLM reasoning with CLI ranking or confidence scores.

## 6. Functional requirements

| ID | Requirement |
|---|---|
| FR-1 | Define a `## Index header` standard for reusable records. |
| FR-2 | Parse `Index header` fields into `context-index`. |
| FR-3 | Make `context-delivery` prefer structured index-header fields before legacy fields. |
| FR-4 | Extend `record-audit` to report missing searchable metadata. |
| FR-5 | Keep audit warnings advisory first, then block only new/modified records after dogfood. |
| FR-6 | Revise `relevant-record-query` to candidate-only output language and schema. |
| FR-7 | Add a graph candidate query tool for record/file neighbor discovery. |
| FR-8 | Reduce implementation-map `needs-map` backlog because retrieval quality depends on source/test links. |
| FR-9 | Dogfood host feature-navigation/profile queries across medivance projects. |
| FR-10 | Keep prompt budget within current bounds while adding only compact search instructions. |

## 7. Non-functional requirements

| Area | Requirement |
|---|---|
| Correctness | Candidate tools must not output requiredRead/confidence/intent/risk/gate. |
| Privacy | Candidate tools must not persist raw user messages by default. |
| Portability | Sync must update all host projects without stale managed files. |
| Performance | Runtime prompt remains compact; indexes are optional caches. |
| Recoverability | Missing indexes fall back to source scan/root-bound grep. |
| Auditability | PRD/tasks/SDD/TDD/implementation maps record every phase. |

## 8. User stories

1. As an LLM, when I receive a request with an unfamiliar host term, I can search index headers and feature navigation before opening full records.
2. As a searcher subagent, I can return candidate paths and matched fields without deciding what is important.
3. As a maintainer, when I add a record without aliases/source/test hints, `record-audit` warns me.
4. As a host owner, when a product surface has aliases/routes/components/tests, future agents can rediscover them from `feature-navigation` and records.
5. As a framework maintainer, when I sync lazy-harness to hosts, managed files match source and removed semantic classifiers stay removed.

## 9. Acceptance criteria

- New SDD/TDD exists for `record-index-header`.
- `context-index --write` includes index-header fields.
- `context-delivery --message "..."` returns candidate hits from index header fields.
- `record-audit --format=json` reports index-header/search metadata gaps.
- `relevant-record-query` no longer uses score/ranking/should-be-in-context semantics.
- `graph-query` candidate tool can return neighbors for record path and source file path.
- `impl-map --format=json` needs-map count trends down from 31.
- `lazy test`, `doctor --profile=smoke`, `prompt-budget`, `graph-hygiene` pass in source and synced hosts.
- Prompt budget duplicates remain 0.

## 10. Metrics

| Metric | Baseline | Target |
|---|---:|---:|
| implementation-map needs-map | 31 | 0 or accepted historical none/planned |
| generated context-index presence | missing | generated on demand and validated |
| generated relevant-record-index presence | missing | generated or superseded by candidate-only helper |
| records with index header | 0 baseline | increasing per phase; enforce on new/modified records |
| candidate tool semantic authority fields | 0 allowed | 0 |
| prompt duplicates | 0 | 0 |

## 11. Dependencies

- `.lazy-harness/ssot/cli-tool-boundary.md`
- `.lazy-harness/spec/platform/context-delivery-contract.md`
- `.lazy-harness/spec/platform/pre-response-rule-context.md`
- `.lazy-harness/spec/platform/implementation-map-standard.md`
- `.lazy-harness/ssot/implementation-map-storage.md`
- `.lazy-harness/project/feature-navigation.xml`

## 12. Risks

| Risk | Mitigation |
|---|---|
| Too many required fields make record writing heavy | Start advisory, block only new/modified records later |
| Tool outputs creep back into semantic authority | Self-test forbidden fields and SSOT boundary checks |
| Generated index goes stale | Keep source scan fallback and stale detection |
| Host aliases are incomplete | Dogfood host feature-navigation/profile maps |
| Prompt grows again | Maintain prompt-budget checks |

## 13. Rollout plan

1. Phase 1: SDD/TDD for Record Index Header.
2. Phase 2: parser + record-audit advisory warnings.
3. Phase 3: context-index productization.
4. Phase 4: relevant-record-query candidate-only revision.
5. Phase 5: graph-query candidate tool.
6. Phase 6: implementation-map backlog reduction.
7. Phase 7: host dogfood and sync validation.
8. Phase 8: compact prompt/skill search instructions.

## Rule placement

- Rule: lazy-harness needs a product-level requirement for searchable record context retrieval so LLM agents can recover memory without CLI semantic authority.
- Scope: framework-global
- Primary record: `.lazy-harness/prd/searchable-record-context-retrieval-prd.md`
- Why not AGENTS.md: PRD is product requirement and acceptance criteria, not runtime prompt grammar.
- Why not `.jcode`: framework-global product requirement, not local/private Jcode preference.
- Confirmation: user-confirmed

## Discovery capture

- DDD: none
- SDD: candidate/updated via planned `record-index-header`, `context-delivery`, `relevant-record-query`, graph-query contracts
- BDD: none yet; host dogfood may add behavior records later
- TDD: candidate/updated via planned `record-index-header` and dogfood tests
- ADR: candidate if trade-off emerges around separate Index header vs extending Rule digest
- SSOT: updated/related via CLI tool boundary and implementation-map storage
- Planning: updated by this PRD and task backlog
