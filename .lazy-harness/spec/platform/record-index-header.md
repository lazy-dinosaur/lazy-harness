# SDD — Record Index Header

Status: accepted
Date: 2026-06-06
Layer: SDD
Related DDD: `.lazy-harness/domain/searchable-record-memory.md`
Related BDD: `.lazy-harness/behavior/llm-owned-record-retrieval.md`
Related TDD: `.lazy-harness/tests/record-index-header.md`
Related SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`
Related SDD: `.lazy-harness/spec/platform/record-digest-format.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Applies when:
  - adding or editing `## Index header` in a `.lazy-harness` record
  - designing deterministic record/source cache fields
  - designing record-audit warnings for searchable metadata
  - deciding whether metadata may satisfy search/read debt or semantic authority
- Must:
  - define `## Index header` as record-authored metadata written in canonical records
  - keep Index Header fields as searchability/storage cues only
  - require real record body, Rule digest, Implementation map, source, and test reads before an agent relies on a record
  - cite DDD terms and BDD behavior scenarios when changing the header contract
  - keep generated cache output non-canonical and rebuildable
  - keep parser/cache implementation blocked until SCR-401 naming/scope approval
- Must not:
  - define any raw-user-message query interface
  - define required-read, optional-read, confidence, intent, risk, gate, next-action, or candidate-meaning fields
  - allow a cache/header hit to satisfy evidence debt by itself
  - rank, infer, or decide what the user means from the header alone
- Record completion:
  - changes to fields or semantics update this SDD, DDD, BDD, TDD, SSOT/ADR review, tasks, report, and graph rows together.

## Header placement

`## Index header` is an optional section near the top of canonical `.lazy-harness` records.

Preferred order:

1. Title
2. Status/date/layer metadata if used
3. `## Index header`
4. `## Rule digest`
5. Body sections
6. `## Implementation map`
7. `## Layer completeness impact`
8. `## Rule placement`
9. `## Discovery capture` when needed

`Rule digest` remains the behavior/policy digest. `Index header` is only a compact metadata header for findability.

## Field contract

| Field | Required | Type | Meaning | Forbidden interpretation |
|---|---:|---|---|---|
| Record id | yes for new records | stable slug/string | Stable id for graph/cache joins. | Not a priority or routing id. |
| Layer | yes | DDD/SDD/BDD/TDD/ADR/SSOT/Planning/PRD/Evidence/etc. | Record layer for filtering and layer completeness. | Not a permission to skip other impacted layers. |
| Status | yes | active/proposed/deprecated/etc. | Record lifecycle status. | Not a confidence score for current request. |
| Scope | yes | framework-global/host-project/team-policy/etc. | Scope of the record fact. | Not a user intent classification. |
| Primary aliases | optional | list of strings | Names the LLM/searcher may grep/search for this record. | Not candidate meanings chosen for the user. |
| Surface terms | optional | list of strings | User-facing or UI/product terms that may lead to this record. | Not automatic mapping from user text to answer. |
| Search keys | optional | list of strings | Stable technical keys, abbreviations, or slugs. | Not ranking features. |
| Applies when | optional | list of prose bullets | Circumstances where the record may be relevant. | Not a trigger that automatically executes tools or gates. |
| Related records | optional | list of record paths | Records often read nearby. | Not required-read. |
| Source files | optional | list of repository paths | Implementation files likely worth inspecting after record read. | Not proof that source was inspected. |
| Test files | optional | list of repository paths | Tests likely worth inspecting/running after record read. | Not proof that tests were inspected or passed. |
| Graph ids | optional | list of graph row ids | Machine-readable joins into `knowledge/graph.jsonl`. | Not canonical truth by itself. |
| Notes | optional | short prose | Human hint about caveats. | Not a semantic decision. |

## Example

```md
## Index header

- Record id: record_searchable_memory_example
- Layer: SDD
- Status: active
- Scope: framework-global
- Primary aliases:
  - Record Index Header
  - searchable record metadata
- Surface terms:
  - index header
  - record lookup hints
- Search keys:
  - record-index-header
  - record-authored-metadata
- Applies when:
  - an agent/searcher needs to find records from stable metadata cues
  - a record needs source/test/graph hints without creating semantic authority
- Related records:
  - `.lazy-harness/domain/searchable-record-memory.md`
  - `.lazy-harness/behavior/llm-owned-record-retrieval.md`
- Source files:
  - `.lazy-harness/scripts/context-index.ts`
- Test files:
  - `.lazy-harness/tests/record-index-header.md`
- Graph ids:
  - `kg_record_index_header_contract_defines_fields`
- Notes:
  - Header values are navigation cues only; the LLM/searcher must still read real evidence.
```

## Consumer contract

Allowed consumers:

1. **LLM/searcher** may use header fields to choose where to begin root-bound search/read.
2. **Record-audit** may warn about missing or incomplete metadata.
3. **Deterministic cache/listing tools** may index field values after SCR-401 approval.
4. **Graph hygiene tools** may verify referenced graph ids and paths exist.

Forbidden consumers:

1. Lifecycle hooks must not invoke a raw-message query backend based on headers.
2. Cache/listing tools must not expose `requiredRead`, `confidence`, `intent`, `risk`, `gate`, `nextAction`, or equivalent semantic fields.
3. Any future parser must not accept `--message`, `--query-user-message`, or equivalent raw user text input without a new user-confirmed ADR/SSOT update.
4. A header/cache hit must not satisfy `search-read-debt.jsonl` evidence by itself.

## Future parser/cache constraints

Parser/cache implementation is **not part of SCR-303**.

Before implementation:

1. SCR-401 decision: canonical future command/cache name is `record-index`.
2. The chosen command must be listing/cache generation only; any `context-index` path is legacy/deprecated compatibility only if retained during SCR-402.
3. Output schema must avoid semantic-authority field names.
4. Self-test must prove the command has no raw-user-message query entry point.
5. BDD/TDD scenarios in `.lazy-harness/behavior/llm-owned-record-retrieval.md` and `.lazy-harness/tests/record-index-header.md` must be mapped to tests.

## Implementation map

- Status: `contract-only; SCR-401 naming decided`
- Primary files:
  - `.lazy-harness/spec/platform/record-index-header.md` — this SDD field/consumer contract.
  - `.lazy-harness/domain/searchable-record-memory.md` — DDD terms and invariants.
  - `.lazy-harness/behavior/llm-owned-record-retrieval.md` — behavior scenarios this contract must preserve.
  - `.lazy-harness/tests/record-index-header.md` — TDD fixture plan.
  - `.lazy-harness/ssot/cli-tool-boundary.md` — canonical no semantic CLI authority boundary and SCR-401 decision.
  - `.lazy-harness/decisions/0042-record-index-cache-naming.md` — ADR for canonical `record-index` naming.
  - `.lazy-harness/planning/searchable-record-context-retrieval-tasks.md` — SCR-303/304/305/401 status.
- Key symbols:
  - none yet; parser/cache implementation remains blocked.
- Flow:
  1. Record author writes canonical metadata in `## Index header`.
  2. Agent/searcher may use metadata as a starting cue.
  3. Agent/searcher reads real record/source/test evidence.
  4. If implementation is later approved, deterministic cache lists metadata only.
- Tests / protection:
  - `.lazy-harness/tests/record-index-header.md` maps fixtures to every BDD scenario.
  - `python3 .lazy-harness/scripts/self-test.py` currently protects deleted helper absence and search/read debt.
- Cross-layer links:
  - DDD: `.lazy-harness/domain/searchable-record-memory.md`
  - BDD: `.lazy-harness/behavior/llm-owned-record-retrieval.md`
  - TDD: `.lazy-harness/tests/record-index-header.md`
  - SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`
  - Planning: `.lazy-harness/planning/searchable-record-context-retrieval-tasks.md`
- Machine index:
  - graph ids: `kg_record_index_header_contract_defines_fields`, `kg_record_index_header_tdd_protects_contract`
  - generated index key: pending until cache generator approval

## Layer completeness impact

- DDD: already updated in `.lazy-harness/domain/searchable-record-memory.md`.
- BDD: already updated in `.lazy-harness/behavior/llm-owned-record-retrieval.md`.
- SDD: this record defines the contract.
- TDD: `.lazy-harness/tests/record-index-header.md` defines fixtures and future self-test names.
- SSOT: `.lazy-harness/ssot/cli-tool-boundary.md` reviewed; existing boundary is sufficient for SCR-303/304.
- ADR: `.lazy-harness/decisions/0042-record-index-cache-naming.md` records SCR-401 canonical `record-index` naming.
- Planning: tasks and implementation plan updated.

## Rule placement

- Rule: `## Index header` field structure and consumer constraints are a platform SDD contract.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/record-index-header.md`
- Why not DDD only: field structure and consumer constraints are component/contract-level details.
- Why not `.jcode`: shared lazy-harness framework behavior, not local/private wiring.
- Confirmation: user-confirmed on 2026-06-06 that this must never move against the LLM-owned retrieval direction.

## Discovery capture

- DDD: updated/covered by `.lazy-harness/domain/searchable-record-memory.md`.
- BDD: updated/covered by `.lazy-harness/behavior/llm-owned-record-retrieval.md`.
- SDD: updated by this record.
- TDD: updated by `.lazy-harness/tests/record-index-header.md`.
- ADR: `.lazy-harness/decisions/0042-record-index-cache-naming.md` updated/created for SCR-401.
- SSOT: reviewed/updated in `.lazy-harness/ssot/cli-tool-boundary.md`.
- Planning: updated in `.lazy-harness/planning/searchable-record-context-retrieval-tasks.md` and implementation plan.
