# TDD — Record Index Header

Status: accepted
Date: 2026-06-06
Layer: TDD
Related DDD: `.lazy-harness/domain/searchable-record-memory.md`
Related BDD: `.lazy-harness/behavior/llm-owned-record-retrieval.md`
Related SDD: `.lazy-harness/spec/platform/record-index-header.md`
Related SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Applies when:
  - adding or changing `## Index header` fields
  - adding parser/cache/audit behavior for record-authored metadata
  - proving metadata does not become semantic authority
- Must:
  - protect complete header parsing expectations before implementation
  - protect missing/incomplete metadata as advisory unless explicitly promoted later
  - protect legacy Rule digest fallback behavior
  - protect no raw-user-message query interface
  - protect cache-hit-not-proof-of-evidence behavior
  - map BDD scenarios to fixtures
- Must not:
  - implement parser/cache in this TDD record
  - mark future parser/cache work complete before SCR-401 approval
  - test for requiredRead/confidence/intent/risk/gate/nextAction outputs as allowed behavior
- Record completion:
  - changes to fixtures update BDD scenarios, SDD contract, tasks, and self-test implementation when implemented.

## Fixture matrix

| Fixture id | Scenario protected | Input shape | Expected result | Implementation status |
|---|---|---|---|---|
| `record_index_header_complete` | BDD Scenario 1 | Record with all recommended header fields | Header metadata can be parsed/listed as cues; no semantic fields exist | planned |
| `record_index_header_missing` | BDD Scenario 5 | Record missing `## Index header` | Advisory warning only for historical records; no hard block | planned |
| `record_index_header_legacy_rule_digest_fallback` | Migration compatibility | Record has Rule digest aliases/hints but no Index Header | Existing Rule digest remains searchable fallback until migration | planned |
| `record_index_header_no_raw_message_query` | DDD/SSOT semantic boundary | Future CLI/cache command definitions | No `--message`, no raw user-text query interface, no lifecycle invocation | planned |
| `record_index_header_cache_hit_not_evidence` | BDD Scenario 3 | Generated cache/list contains record/source path | Search/read debt remains unsatisfied until real read/search evidence exists | planned / partially covered by pre-action guard |
| `record_index_header_conflict_option_gate` | BDD Scenario 2 | Two records share plausible aliases/surface terms | Agent must option-gate after evidence remains ambiguous; no automatic ranking | planned |
| `record_index_header_missing_knowledge_converges` | BDD Scenario 4 | Needed host fact absent from records | Source/user-confirmed fact must be written to correct layer record | planned / framework behavior covered elsewhere |
| `record_index_header_layer_package_required` | BDD Scenario 5 | New retrieval concept changes terms/behavior/contract/test | DDD/BDD/SDD/TDD/SSOT/ADR impact must be recorded | planned / this task package covers current case |

## Future self-test names

These names are reserved for the implementation phase. They must not be marked complete until parser/cache/audit code exists.

- `check_record_index_header_contract_sections`
- `check_record_index_header_complete_fixture`
- `check_record_index_header_missing_is_advisory`
- `check_record_index_header_legacy_rule_digest_fallback`
- `check_record_index_header_no_raw_message_query`
- `check_record_index_header_cache_hit_not_evidence`
- `check_record_index_header_conflict_requires_option_gate`
- `check_record_index_header_layer_package_discovery_capture`

## Concrete fixture sketches

### Complete header fixture

```md
# Example SDD

## Index header

- Record id: record_example_sdd
- Layer: SDD
- Status: active
- Scope: framework-global
- Primary aliases:
  - Example Contract
- Surface terms:
  - example surface
- Search keys:
  - example-contract
- Applies when:
  - example metadata is needed for searchability
- Related records:
  - `.lazy-harness/domain/searchable-record-memory.md`
- Source files:
  - `.lazy-harness/scripts/context-index.ts`
- Test files:
  - `.lazy-harness/tests/record-index-header.md`
- Graph ids:
  - `kg_record_index_header_contract_defines_fields`
- Notes:
  - cue only, not semantic authority
```

Expected future parser/cache output:

- includes listed metadata as strings/arrays
- does not include requiredRead/optionalRead/confidence/intent/risk/gate/nextAction/candidateMeanings
- marks output as generated/non-canonical if written to cache

### Missing header fixture

Given an existing historical record without `## Index header`, future `record-audit` should report advisory metadata warning only.

Expected:

- no hard block
- warning name may be `missing-index-header`
- warning must not imply the record is invalid or irrelevant

### No raw-message query fixture

Given any future cache/listing command:

Expected forbidden patterns:

- `--message`
- `--user-message`
- `--query-user-message`
- lifecycle `message.received` invoking the cache/listing command as semantic query
- output fields named `requiredRead`, `confidence`, `intent`, `risk`, `gate`, `nextAction`, `candidateMeanings`

### Cache hit not evidence fixture

Given a generated cache entry mentions `.lazy-harness/spec/platform/record-index-header.md`
And no root-bound search/read command has been observed
When a mutation is attempted
Then the pre-action search/read debt guard should still require real evidence.

Existing related guard:

- `.lazy-harness/tests/pre-action-search-evidence-guard.md`
- `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py`

## BDD scenario coverage

| BDD scenario | Covered by fixture(s) |
|---|---|
| Metadata cue still requires real record read | complete header, cache hit not evidence |
| Conflicting meanings require option gate | conflict option gate |
| Cache hit is not proof of evidence | cache hit not evidence |
| Missing knowledge converges after confirmation | missing knowledge converges |
| New retrieval concept triggers layer package | layer package required |

## Implementation map

- Status: `fixture-plan-only`
- Primary files:
  - `.lazy-harness/tests/record-index-header.md` — this TDD fixture plan.
  - `.lazy-harness/spec/platform/record-index-header.md` — SDD contract under test.
  - `.lazy-harness/behavior/llm-owned-record-retrieval.md` — scenarios mapped to fixtures.
  - `.lazy-harness/domain/searchable-record-memory.md` — DDD invariants under test.
  - `.lazy-harness/ssot/cli-tool-boundary.md` — semantic-authority boundary under test.
  - `.lazy-harness/scripts/self-test.py` — future home for concrete executable checks.
- Key symbols:
  - no concrete test functions yet; future self-test names reserved above.
- Flow:
  1. SDD defines header field/consumer contract.
  2. TDD records fixture expectations before parser/cache implementation.
  3. SCR-401 decides cache command/name/scope.
  4. Later implementation turns fixture sketches into executable self-test checks.
- Protection today:
  - existing self-test protects deleted query helpers and static search/read debt.
  - this record prevents implementation without fixture expectations.
- Cross-layer links:
  - DDD: `.lazy-harness/domain/searchable-record-memory.md`
  - BDD: `.lazy-harness/behavior/llm-owned-record-retrieval.md`
  - SDD: `.lazy-harness/spec/platform/record-index-header.md`
  - SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`
  - Planning: `.lazy-harness/planning/searchable-record-context-retrieval-tasks.md`
- Machine index:
  - graph ids: `kg_record_index_header_tdd_protects_contract`, `kg_record_index_header_no_raw_message_fixture`
  - generated index key: pending until cache generator approval

## Layer completeness impact

- DDD: covered by `.lazy-harness/domain/searchable-record-memory.md`.
- BDD: covered by `.lazy-harness/behavior/llm-owned-record-retrieval.md` and scenario mapping above.
- SDD: covered by `.lazy-harness/spec/platform/record-index-header.md`.
- TDD: this record defines fixtures.
- SSOT: `.lazy-harness/ssot/cli-tool-boundary.md` reviewed as sufficient for SCR-303/304.
- ADR: none now; SCR-401 naming decision may need one after option gate.
- Planning: task statuses updated.

## Rule placement

- Rule: Record Index Header fixtures and anti-regression cases belong in TDD.
- Scope: framework-global
- Primary record: `.lazy-harness/tests/record-index-header.md`
- Why not SDD only: these are regression and fixture expectations, not just field definitions.
- Why not `.jcode`: shared lazy-harness framework behavior.
- Confirmation: user-confirmed on 2026-06-06 that direction-opposing changes must be prevented.

## Discovery capture

- DDD: covered/updated by `.lazy-harness/domain/searchable-record-memory.md`.
- BDD: covered/updated by `.lazy-harness/behavior/llm-owned-record-retrieval.md`.
- SDD: updated by `.lazy-harness/spec/platform/record-index-header.md`.
- TDD: updated by this record.
- ADR: none now; SCR-401 naming trade-off remains blocked and may need ADR after option gate.
- SSOT: reviewed/updated in `.lazy-harness/ssot/cli-tool-boundary.md`.
- Planning: updated in `.lazy-harness/planning/searchable-record-context-retrieval-tasks.md` and implementation plan.
