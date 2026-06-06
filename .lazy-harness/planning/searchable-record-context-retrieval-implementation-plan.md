# Searchable Record Header and LLM-Owned Context Retrieval Plan

Status: proposed
Date: 2026-06-06
Layer: Planning

Related SSOT:
- `.lazy-harness/ssot/cli-tool-boundary.md`
- `.lazy-harness/ssot/implementation-map-storage.md`
- `.lazy-harness/ssot/rule-sources.md`

Related SDD:
- `.lazy-harness/spec/platform/context-delivery-contract.md`
- `.lazy-harness/spec/platform/pre-response-rule-context.md`
- `.lazy-harness/spec/platform/record-digest-format.md`
- `.lazy-harness/spec/platform/relevant-record-query.md`
- `.lazy-harness/spec/platform/implementation-map-standard.md`
- `.lazy-harness/spec/platform/project-profile.md`

Related TDD:
- `.lazy-harness/tests/context-broker-dogfood.md`
- `.lazy-harness/tests/response-rule-audit.md`

## Summary

The framework already has a solid record-first memory foundation, generic search/read-debt, candidate-only context delivery, implementation maps, graph rows, and generated indexes. The missing piece is a strict, searchable record header/indexing standard that lets the LLM quickly find candidate records without opening entire files, while keeping final importance/read judgment with the LLM/searcher.

The next architecture should be:

```text
user request
→ generic message.received search/read-debt
→ LLM/searcher uses record headers, graph, generated indexes, project profile, and source grep as tools
→ tools return candidates only
→ LLM reads actual records/source/tests
→ LLM decides what matters and acts
→ confirmed new knowledge is saved with searchable headers + implementation map + graph edges
```

## Rule placement

- Rule: Records must be stored with searchable metadata so LLM/searcher can find candidate context; CLIs/indexes may return candidates and matched fields but must not decide importance, required reads, intent, risk, record-write need, or next action.
- Scope: framework-global
- Primary record: `.lazy-harness/planning/searchable-record-context-retrieval-implementation-plan.md`
- Why not AGENTS.md: this is a multi-phase implementation plan with source/test/record changes; AGENTS should only carry compact operating reminders.
- Why not `.jcode`: this is shared lazy-harness framework behavior, not local/private Jcode wiring.
- Confirmation: user-confirmed

## Current evidence inventory

Observed on 2026-06-06:

- Source `lazy test`: green.
- Project sync: `medivance`, `medivance-homepage`, `medivance-pwa` synced to `d1d66bf` and validated.
- CLI boundary: accepted in `.lazy-harness/ssot/cli-tool-boundary.md`.
- Context Delivery: candidate-only in `.lazy-harness/spec/platform/context-delivery-contract.md` and `.lazy-harness/scripts/context-delivery.ts`.
- Generic search/read-debt remains active in `.lazy-harness/spec/platform/pre-response-rule-context.md`.
- Generated indexes present:
  - `reference-index.json`
  - `implementation-index.json`
- Generated indexes missing/tolerated:
  - `context-index.json`
  - `relevant-record-index.json`
- Record counts:
  - DDD 7, SDD 45, BDD 5, TDD 27, ADR 42, SSOT 15, Planning 29, Plans 15, Project 2, Knowledge 5
- Implementation-map audit:
  - 110 records scanned
  - 79 ok
  - 31 needs-map

## What is already complete

### 1. CLI-as-tool boundary

Completed:

- Removed `task-router.ts`.
- Removed `operational-state.ts`.
- Removed route/operational-state commands.
- Prevented lifecycle hooks from static user-text route classification.
- `context-delivery` now returns candidates only.

Canonical rule:

```text
CLI may retrieve, list, normalize, link, measure, validate, perform hygiene, and build caches.
LLM/searcher owns intent, importance, read priority, write-need, risk, gate, and next-action judgment after evidence.
```

### 2. Generic read/search-debt

Completed:

- `message.received` emits static search/read-debt for any non-empty user message.
- Action/mutation remains guarded until root-bound search/read evidence exists.
- This is distinct from CLI-selected `requiredRead`.

Keep:

```text
generic read-debt/search-debt
```

Do not reintroduce:

```text
CLI sees message → chooses requiredRead/confidence/priority → guard treats it as authority
```

### 3. Candidate retrieval

Completed:

- `context-delivery` packet mode: `candidate-retrieval`.
- Fields: `candidateHits`, `matchedFields`, `matchedQueries`, `fallbackSearches`.
- Forbidden: `requiredRead`, `optionalRead`, `confidence`, `instructionLevel`, `intent`, `risk`, `gate`.

## Gaps and required changes

## Phase 1 — Record Index Header Standard

Goal: make every reusable record searchable before full-file reads.

### New/updated records

Create or update:

- New SDD: `.lazy-harness/spec/platform/record-index-header.md`
- New TDD: `.lazy-harness/tests/record-index-header.md`
- Update SDD: `.lazy-harness/spec/platform/record-digest-format.md`
- Update SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`
- Update SDD: `.lazy-harness/spec/platform/context-delivery-contract.md`
- Update SDD: `.lazy-harness/spec/platform/relevant-record-query.md`

### Proposed record header shape

```md
## Index header

- Record id: `record_<stable_slug>`
- Layer: DDD | SDD | BDD | TDD | ADR | SSOT | Planning
- Status: active | advisory | deprecated | reverted | needs-review | proposed
- Scope: framework-global | host-project | team-policy | layer-fact | transient-plan | jcode-local | ambiguous
- Primary aliases:
  - `...`
- Surface terms:
  - `...`
- Search keys:
  - `...`
- Applies when:
  - compact trigger cue
- Related records:
  - `.lazy-harness/...`
- Source files:
  - `src/...` or `.lazy-harness/scripts/...`
- Test files:
  - `.lazy-harness/tests/...` or `tests/...`
- Graph ids:
  - `kg_...`
```

Relationship to existing `Rule digest`:

- `Index header` is for retrieval metadata.
- `Rule digest` is for compact policy/guidance bullets.
- `Implementation map` is for source/test/flow/graph mapping.

Minimal migration option:

- If we do not want a separate section initially, extend `Rule digest` to require aliases/search keys/source/test/graph fields.
- Recommended: separate `Index header` to keep retrieval metadata stable and avoid mixing with policy prose.

### Source changes

Update:

- `.lazy-harness/scripts/context-index.ts`
  - parse `## Index header` fields,
  - retain fallback parsing from `Rule digest` for legacy records,
  - add `indexHeaderSource: index-header | rule-digest | fallback`,
  - expose `searchKeys`, `primaryAliases`, `sourceFiles`, `testFiles`, `graphIds`.

- `.lazy-harness/scripts/context-delivery.ts`
  - match `Index header` fields first,
  - only fall back to current structured fields,
  - keep candidate-only output.

- `.lazy-harness/scripts/record-audit.ts`
  - add index-header completeness summary.

- `.lazy-harness/scripts/self-test.py`
  - fixture proving `Index header` fields are parsed,
  - fixture proving generic prose does not become a product-surface hit,
  - fixture proving missing header is reported but not hard-blocking historical records initially.

### Validation

- `python3 .lazy-harness/scripts/self-test.py`
- `.lazy-harness/bin/lazy record-audit --format=json`
- `.lazy-harness/bin/lazy context-delivery --message "기능패널" --format=json`

Success criteria:

- Records with `Index header` can be found by aliases/search keys/source/test/graph ids.
- Framework-global example prose does not become a host product-surface candidate.
- CLI still does not output requiredRead/confidence/intent/risk/gate.

## Phase 2 — Record Audit Enforcement

Goal: make storage searchable by default.

### Source changes

Update:

- `.lazy-harness/scripts/record-audit.ts`
  - add fields:
    - `indexHeader.present`
    - `aliases.count`
    - `searchKeys.count`
    - `sourceFiles.count`
    - `testFiles.count`
    - `graphIds.count`
    - `implementationMap.status`
  - output warnings:
    - `missing-index-header`
    - `missing-alias-or-search-key`
    - `missing-source-test-hints`
    - `missing-graph-link`
    - `implementation-map-needs-map`

- `.lazy-harness/bin/lazy`
  - no new command required initially; extend `lazy record-audit`.
  - optional later: `lazy index-header audit` alias.

### Enforcement policy

Initial mode:

- advisory warnings only,
- no blocking for historical records.

Promotion path:

- warn for all reusable guidance records,
- block only newly created/modified records in pre-commit once dogfood-proven.

### Validation

- Add self-test fixture with:
  - one complete record,
  - one missing index header,
  - one missing implementation map,
  - one historical ADR allowed with warning.

Success criteria:

- `record-audit` summarizes missing searchable metadata.
- No false hard-stop for historical backlog.

## Phase 3 — Context Index Productization

Goal: make `context-index.json` generation reliable and useful while keeping it non-canonical.

### Current state

- `context-index.ts` exists.
- `generated/context-index.json` is missing and allowed.
- `context-delivery` falls back to source scan when missing.

### Source changes

Update:

- `.lazy-harness/scripts/context-index.ts`
  - include `Index header` fields,
  - include `Implementation map` extracted source/test hints,
  - include graph edge summaries,
  - include source fingerprint per record,
  - include stale detection when generated index is older than canonical records.

- `.lazy-harness/generated/README.md`
  - document trigger to regenerate after `Index header`, `Rule digest`, `Implementation map`, graph, or project profile changes.

- `.lazy-harness/scripts/self-test.py`
  - validate `context-index --write` creates expected index,
  - validate missing cache fallback remains.

### Command flow

```bash
.lazy-harness/bin/lazy context-index --write --format=md
.lazy-harness/bin/lazy context-delivery --message "..." --format=json
```

Success criteria:

- `context-delivery` can use generated index when present.
- Deleting `context-index.json` still falls back to source scan.
- Generated index is never treated as canonical.

## Phase 4 — Relevant Record Query Revision

Goal: align `relevant-record-query.ts` with the CLI boundary.

### Problem

Current SDD/source still uses terms such as `score`/`ranking` and asks “which records should be in working context.” This risks sounding like CLI semantic authority.

### Change

Update:

- `.lazy-harness/spec/platform/relevant-record-query.md`
- `.lazy-harness/scripts/relevant-record-query.ts`
- `.lazy-harness/schemas/relevant-record-index.schema.json`
- self-test fixture(s)

New posture:

```text
relevant-record-query returns compact candidate digests and matched cues.
It does not decide what must be read or what is important.
```

Output should use:

- `candidateRecords[]`
- `matchedFields[]`
- `matchedQueries[]`
- `fallbackSearches[]`
- `notes[]`

Avoid or rename:

- `score` → `matchCount` or `matchedCuesCount` if needed
- `ranking` → `sourceOrder` / `candidateOrder`
- `should be in context` → `candidate record digests`

Success criteria:

- Helper remains explicit/manual.
- No lifecycle hook calls it automatically.
- No `requiredRead`, `confidence`, `importance`, `intent`, `risk` fields.

## Phase 5 — Graph Query Tool

Goal: let LLM query linked-node memory without full-file scans.

### New command options

Add one script or extend graph hygiene:

- `.lazy-harness/scripts/graph-query.ts`
- `lazy graph-query --path <record-or-file>`
- `lazy graph-query --id <kg_id>`
- `lazy graph-query --neighbors <path>`
- `lazy graph-query --impacted-file <file>`

Output remains candidate-only:

```json
{
  "mode": "graph-candidate-query",
  "nodes": [],
  "edges": [],
  "candidateRecords": [],
  "candidateFiles": [],
  "fallbackSearches": []
}
```

Forbidden:

- no importance,
- no requiredRead,
- no next action.

Source updates:

- `.lazy-harness/spec/platform/progressive-knowledge-graph.md`
- `.lazy-harness/spec/platform/implementation-map-standard.md`
- `.lazy-harness/ssot/implementation-map-storage.md`
- `.lazy-harness/scripts/self-test.py`
- `.lazy-harness/bin/lazy`

Success criteria:

- Given a record path, graph-query returns linked source/test/SDD/TDD/ADR/SSOT candidates.
- Given a source file, graph-query returns candidate records/tests that mention it.
- graph-hygiene still validates path existence.

## Phase 6 — Implementation Map Backlog

Goal: improve retrieval quality by fixing `needs-map` records.

### Current backlog

`lazy impl-map --format=json` reports:

- 110 records scanned,
- 79 ok,
- 31 needs-map.

Most examples are older ADRs plus a couple TDD records.

### Plan

Batch in groups:

1. ADR 0001–0010
2. ADR 0011–0020
3. ADR 0021–0030
4. TDD residuals

For each record:

- add concise `Implementation map`,
- add graph rows if implementation/source/test linkage is confirmed,
- do not invent symbols; read source or mark `Status: planned/none`.

Validation:

```bash
.lazy-harness/bin/lazy impl-map --format=json
.lazy-harness/bin/lazy graph-hygiene --format=json --fail-on-issues
python3 .lazy-harness/scripts/self-test.py
```

Success criteria:

- `needs-map` decreases from 31 to 0 or accepted historical `none/planned` statuses.

## Phase 7 — Host Project Profile and Feature Navigation Dogfood

Goal: ensure synced hosts have usable product-surface context.

### Current concern

Framework source has `.lazy-harness/project/feature-navigation.xml`, but host-specific product maps may be incomplete.

### Per-host checks

For each host:

```bash
cd <host>
.lazy-harness/bin/lazy record-audit --format=json
.lazy-harness/bin/lazy context-delivery --message "대표 UI/도메인 용어" --format=json
.lazy-harness/bin/lazy context-index --write --format=md
.lazy-harness/bin/lazy context-dogfood --format=md
```

Fields to verify:

- `.lazy-harness/project/profile.xml`
- `.lazy-harness/project/stack.xml`
- `.lazy-harness/project/filesystem.xml`
- `.lazy-harness/project/feature-navigation.xml`
- `.lazy-harness/tests/test-strategy.xml`
- aliases/routes/components/sourceFiles/tests for key surfaces

Success criteria:

- host product terms return candidate hits via feature navigation or record headers,
- no framework-level examples are mistaken for host product candidates,
- host profile gaps are captured as records or option gates.

## Phase 8 — Prompt / Skill Search Instructions

Goal: ensure LLM knows how to search without bloating prompt.

### Principle

Do not put full templates in runtime prompt. Put compact pointers and search protocol.

Update:

- `.lazy-harness/AGENTS.md` compact reminder,
- maybe `/jcode` skills or lazy-harness skills,
- `.lazy-harness/spec/platform/pre-response-rule-context.md`,
- generated `reference-index` / `context-index` instructions.

Prompt should say only:

```text
Use read-debt protocol.
Search Index header / Rule digest / Implementation map / graph / feature navigation.
Open only candidate records/source/tests needed.
```

The full template stays in SDD/TDD records.

Validation:

- `lazy prompt-budget --format=json`
- self-test prompt token budget checks

## Phase 9 — Sync and Cross-host Validation

Goal: every framework change syncs safely to real hosts.

Use existing flow:

```bash
SOURCE=/home/lazydino/dev/lazy-harness
for HOST in /home/lazydino/dev/medivance /home/lazydino/dev/medivance-homepage /home/lazydino/dev/medivance-pwa; do
  bun $SOURCE/.lazy-harness/scripts/lazy-sync.ts --from $SOURCE --target $HOST --force
  (cd $HOST && .lazy-harness/bin/lazy test)
  (cd $HOST && .lazy-harness/bin/lazy doctor --profile=smoke)
  (cd $HOST && .lazy-harness/bin/lazy prompt-budget --format=json)
done
```

Additionally compare manifest-managed files and verify known removed files are absent.

## Explicit non-goals

Do not reintroduce:

- `task-router` style route classification,
- `operational-state` style task/risk classifier,
- CLI-selected `requiredRead`,
- CLI `confidence`/importance fields,
- automatic context-delivery/relevant-record query calls inside `message.received`,
- hidden external RAG as authority.

Do not require:

- every historical record to be perfect before using the framework,
- generated indexes to always exist,
- vector DB or hosted search.

## Validation matrix

| Area | Command / check | Expected |
|---|---|---|
| Source self-test | `python3 .lazy-harness/scripts/self-test.py` | pass |
| Lazy gate | `.lazy-harness/bin/lazy test` | pass |
| Prompt budget | `.lazy-harness/bin/lazy prompt-budget --format=json` | pass/warn, duplicates 0 |
| Record audit | `.lazy-harness/bin/lazy record-audit --format=json` | reports header gaps, not hard-blocking initially |
| Impl map | `.lazy-harness/bin/lazy impl-map --format=json` | needs-map decreases over time |
| Context index | `.lazy-harness/bin/lazy context-index --write` | generated cache created |
| Context delivery | `.lazy-harness/bin/lazy context-delivery --message "..."` | candidate-only, no requiredRead/confidence |
| Graph | `.lazy-harness/bin/lazy graph-hygiene --format=json --fail-on-issues` | pass |
| Host sync | managed-file compare | no missing/mismatch/stale |

## Recommended implementation order

1. Phase 1: create `record-index-header` SDD/TDD and update parser support.
2. Phase 2: add `record-audit` warnings for missing headers/search metadata.
3. Phase 3: productize `context-index --write` with header fields.
4. Phase 4: revise `relevant-record-query` to candidate-only wording/shape.
5. Phase 5: add graph-query candidate tool.
6. Phase 6: reduce `impl-map` needs-map backlog.
7. Phase 7: host feature-navigation/profile dogfood.
8. Phase 8: compact prompt/skill search instructions.
9. Phase 9: sync and cross-host validation.

## Approval gate

This plan is not implementation approval. Before coding Phase 1, present a small plan proposal for:

- exact SDD/TDD files to add,
- parser field names,
- record-audit warning names,
- self-test fixtures,
- expected command outputs.

Implementation should proceed only after user approval of the phase-level plan.
