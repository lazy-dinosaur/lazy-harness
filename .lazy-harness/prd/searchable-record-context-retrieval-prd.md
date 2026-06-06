# PRD — Searchable Record Memory for LLM-Owned Retrieval

Date: 2026-06-06
Status: active — cleanup and cross-host sync complete; future record-index phases proposed
Owner: lazy-harness
Related plan: `.lazy-harness/planning/searchable-record-context-retrieval-implementation-plan.md`
Related task backlog: `.lazy-harness/planning/searchable-record-context-retrieval-tasks.md`
Related SDD: `.lazy-harness/spec/platform/search-read-debt-contract.md`
Related SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`

## 1. Product summary

Lazy-harness needs durable project memory that an LLM/searcher can rediscover quickly without turning deterministic code into a semantic decision-maker.

The product is not a query backend. The product is a better storage and evidence loop:

```text
canonical records
+ searchable record-authored headers
+ implementation maps
+ graph/source/test pointers
+ static search/read-debt guard
→ LLM/searcher performs real root-bound search/read
→ LLM/searcher decides meaning, priority, gate, and next action
```

## 2. Core correction

The previous draft was wrong because it centered helper CLIs that could appear to choose candidates from raw user text. That conflicts with the confirmed boundary:

```text
Code may build deterministic caches from records.
Code may validate, measure, and audit evidence.
Code must not decide user intent, importance, required reads, risk, gate, or next action.
```

Therefore this PRD removes the candidate-query helper direction. The immediate work is cleanup plus record storage quality.

## 2.1 Current implementation status

Completed on 2026-06-06:

- Obsolete query-helper artifacts deleted from the source framework.
- Runtime journal renamed to `search-read-debt.jsonl`.
- PRD/tasks/plan/report rewritten around LLM-owned retrieval.
- Deleted helper absence protected by self-test.
- Graph/generated stale rows cleaned.
- Cleanup synced to 13 initialized downstream hosts; see `.lazy-harness/evidence/2026-06-06-searchable-record-memory-host-sync.md`.

Not started yet:

- Record Index Header Layer Package: DDD terminology, BDD behavior, SDD contract, TDD fixtures, and SSOT/ADR boundary review.
- Any deterministic cache/parser implementation.
- Record-audit metadata warnings.
- Implementation-map backlog migration.

## 3. Target users

| Persona | Need |
|---|---|
| Main LLM agent | Know where to start searching, then read real records/source/tests before acting |
| Searcher subagent | Use root-bound grep/read/graph/source inspection, not a semantic helper output |
| Framework maintainer | Keep records searchable and implementation-mapped over time |
| Host project owner | Ensure confirmed product/domain rules can be rediscovered next session |

## 4. Problem statement

Records are canonical, but retrieval discipline fails when metadata is inconsistent or when helper tools try to shortcut LLM judgment.

Observed failure modes:

1. Stale helper artifacts remain in the framework and keep suggesting code-owned candidate selection.
2. Runtime state names still carry obsolete architecture names.
3. PRD/plan/tasks can accidentally reintroduce deleted semantic-query patterns.
4. Records lack a consistent place for aliases, source/test hints, and graph ids.
5. Generated indexes are sometimes treated as if they could decide relevance.
6. Future agents may follow stale docs instead of the static search/read-debt loop.

## 5. Goals

1. Delete obsolete candidate-query helper artifacts and stale references.
2. Rename runtime debt journal to `search-read-debt.jsonl` so the name matches its actual purpose.
3. Preserve the generic search/read-debt guard as static transport/evidence only.
4. Define a `## Index header` record standard for record-authored metadata.
5. Keep `context-index` or any future cache as deterministic cache only, with no raw-user-message semantic query.
6. Extend audit/test coverage so removed helper artifacts cannot come back silently.
7. Rebuild PRD/tasks/plan around LLM-owned root-bound search/read.

## 6. Non-goals

- No vector/RAG service.
- No helper CLI that takes a raw user message and returns semantic candidate decisions.
- No generated required-read, confidence, intent, risk, gate, or next-action fields.
- No lifecycle hook query backend.
- No full record dump in the default prompt.
- No hard block for historical records missing headers until audit data proves a safe promotion path.

## 7. Functional requirements

| ID | Requirement |
|---|---|
| FR-1 | Remove obsolete query-helper artifacts, CLI commands, schemas, tests, fixtures, and stale planning records. |
| FR-2 | Replace `context-delivery-packets.jsonl` with `search-read-debt.jsonl` in runtime contracts, hooks, helpers, tests, and docs. |
| FR-3 | Add/maintain an SDD for static search/read-debt runtime rows. |
| FR-4 | Update the system reminder inventory so it does not advertise missing obsolete indexes. |
| FR-5 | Add self-test coverage that deleted helper files/commands remain absent. |
| FR-6 | Define `## Index header` as record-authored metadata, not a user-message query interface. |
| FR-7 | Keep generated caches non-canonical and source-regenerable. |
| FR-8 | Extend record-audit later to warn about missing headers/source/test/graph hints. |
| FR-9 | Maintain implementation-map and graph hygiene after deletions. |
| FR-10 | Rewrite planning/task docs so future agents do not follow the removed architecture. |

## 8. Acceptance criteria

- Deleted artifacts are absent from `git ls-files` and `lazy help`.
- Root-bound grep shows no active references that instruct agents to use removed query helpers.
- Runtime code writes/reads `$LAZY_RUNTIME_ROOT/state/search-read-debt.jsonl`.
- `message.received` still emits static harness-first prompt only.
- `lazy test`, `prompt-budget`, and `graph-hygiene` pass.
- PRD/tasks/plan describe LLM-owned retrieval only.
- Any future `Index header` parser work has no raw-message query entry point.

## 9. Metrics

| Metric | Baseline | Target |
|---|---:|---:|
| Obsolete helper source files tracked | 3 | 0 |
| Obsolete query schemas tracked | 2 | 0 |
| Obsolete helper CLI commands | 3 | 0 |
| Runtime debt journal obsolete-name refs | many | 0 active refs |
| Prompt advertised obsolete indexes | 2 | 0 |
| Semantic authority fields in retrieval/cache outputs | 0 allowed | 0 |
| Prompt duplicates | 0 | 0 |

## 10. Dependencies

- `.lazy-harness/domain/searchable-record-memory.md`
- `.lazy-harness/behavior/llm-owned-record-retrieval.md`
- `.lazy-harness/ssot/cli-tool-boundary.md`
- `.lazy-harness/spec/platform/search-read-debt-contract.md`
- `.lazy-harness/spec/platform/pre-response-rule-context.md`
- `.lazy-harness/spec/platform/record-digest-format.md`
- `.lazy-harness/spec/platform/implementation-map-standard.md`
- `.lazy-harness/ssot/implementation-map-storage.md`

## 11. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Removing helper artifacts breaks self-test | Remove obsolete checks, add absence checks, keep static guard tests |
| Renaming runtime journal breaks guards | Update hook/helper/audit/lifecycle fixtures together |
| Stale generated index still references deleted files | Regenerate derived indexes or remove stale rows |
| Future plan reintroduces raw-message query helper | PRD/tasks explicitly forbid it; self-test checks commands absent |
| Record search quality remains weak after cleanup | Add `Index header` standard and record-audit warnings as separate later phases |

## 12. Rollout plan

1. Cleanup and decontamination.
2. Static search/read-debt contract rename and validation.
3. PRD/tasks/plan rewrite.
4. Record Index Header Layer Package: DDD, BDD, SDD, TDD, and SSOT/ADR impact review.
5. Deterministic cache/parser work only after explicit approval and after the layer package is accepted.
6. Record-audit advisory warnings.
7. Implementation-map backlog reduction.
8. Host sync/dogfood using normal LLM/searcher root-bound evidence, not query helpers.

## Rule placement

- Rule: lazy-harness searchable memory must be LLM-owned retrieval over canonical records, not code-owned semantic query/ranking.
- Scope: framework-global
- Primary record: `.lazy-harness/prd/searchable-record-context-retrieval-prd.md`
- Why not AGENTS.md: product requirements and rollout criteria, not runtime prompt grammar.
- Why not `.jcode`: framework-global behavior.
- Confirmation: user-confirmed correction on 2026-06-06.

## Discovery capture

- SDD: new `search-read-debt-contract` replaces the removed helper contract.
- TDD: self-test and pre-response/pre-action records protect static debt and deleted helper absence.
- SSOT: CLI boundary remains canonical.
- Planning: this PRD and the task backlog replace the earlier contaminated plan.
- ADR: no new ADR yet; this implements the user-confirmed correction to ADR 0041 boundary.
