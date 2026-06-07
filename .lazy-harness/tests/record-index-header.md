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
| `record_index_header_complete` | BDD Scenario 1 | Record with all recommended header fields | `record-audit.recordQuality` counts it complete in SCR-501 fixture; header metadata remains cue-only | implemented via `check_record_audit_cli` |
| `record_index_header_missing` | BDD Scenario 5 | Historical record missing `## Index header` | `record-audit.recordQuality.counts["missing-index-header"]` and sample path report advisory warning only; no hard block | implemented via `check_record_audit_cli` |
| `record_index_header_legacy_rule_digest_fallback` | Migration compatibility | Record has Rule digest aliases/hints but no Index Header | Existing Rule digest remains searchable fallback until migration | planned |
| `record_index_header_no_raw_message_query` | DDD/SSOT semantic boundary | Future `record-index` CLI/cache command definitions | No `--message`, no raw user-text query interface, no lifecycle invocation | planned |
| `record_index_map_overview_first` | BDD Scenario 1a | `lazy map --overview` against records, feature navigation, and graph rows | Output includes whole record/layer/feature/graph structure before search-term selection and no semantic-authority fields | implemented via `check_record_index_generator_phase3` |
| `record_index_map_drilldown_cue_only` | BDD Scenario 1a | `lazy map <term-or-file>` against records, feature navigation, and graph rows | Output includes record/source/test/graph drill-down candidates and no requiredRead/confidence/risk/gate/nextAction fields | implemented via `check_record_index_generator_phase3` |
| `record_index_header_canonical_name` | ADR 0042 | Current cache/listing command docs | Canonical name is `record-index`; old command/source/schema/cache paths are absent after Option A migration | implemented |
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
- `check_record_index_map_overview_first`
- `check_record_index_map_drilldown_cue_only`
- `check_record_index_header_canonical_record_index_name`
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
  - `.lazy-harness/scripts/record-index.ts`
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

Given any future `record-index` cache/listing command:

Expected naming and forbidden patterns:

- canonical user-facing name is `record-index`
- old `context-index` command/source/schema/cache paths must be absent after Option A

Expected forbidden patterns:

- `--message`
- `--user-message`
- `--query-user-message`
- lifecycle `message.received` invoking the cache/listing command as semantic query
- output fields named `requiredRead`, `confidence`, `intent`, `risk`, `gate`, `nextAction`, `candidateMeanings`

### Record Map overview-first fixture

Given `lazy map --overview` runs against a host with records, feature navigation, and graph rows:

Expected:

- output mode is `record-map.overview`
- output includes whole structure: record/layer counts, feature navigation entries, graph relation counts, and generated-index presence
- output says to inspect the overview before choosing search terms
- output does not include field names `requiredRead`, `confidence`, `intent`, `risk`, `gate`, `nextAction`, or `candidateMeanings`

### Record Map drill-down fixture

Given `lazy map <term-or-file>` runs against a host with record-authored aliases, project feature navigation, and graph rows:

Expected:

- output mode is `record-map.inspect`
- output includes `drilldown.recordPaths`, `drilldown.sourceFiles`, `drilldown.testFiles`, and `drilldown.graphIds`
- output notes say the result is cue-only and still requires real record/source/test reads
- output does not include field names `requiredRead`, `confidence`, `intent`, `risk`, `gate`, `nextAction`, or `candidateMeanings`

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
| Metadata cue still requires real record read | complete header, cache hit not evidence, record map drill-down cue only |
| Conflicting meanings require option gate | conflict option gate |
| Cache hit is not proof of evidence | cache hit not evidence |
| Missing knowledge converges after confirmation | missing knowledge converges |
| New retrieval concept triggers layer package | layer package required |

## Implementation map

- Status: `fixtures plus SCR-402/SCR-501 executable coverage`
- Primary files:
  - `.lazy-harness/tests/record-index-header.md` — this TDD fixture plan.
  - `.lazy-harness/spec/platform/record-index-header.md` — SDD contract under test.
  - `.lazy-harness/behavior/llm-owned-record-retrieval.md` — scenarios mapped to fixtures.
  - `.lazy-harness/domain/searchable-record-memory.md` — DDD invariants under test.
  - `.lazy-harness/ssot/cli-tool-boundary.md` — semantic-authority boundary under test.
  - `.lazy-harness/decisions/0042-record-index-cache-naming.md` — canonical naming ADR under test.
  - `.lazy-harness/scripts/self-test.py` — concrete executable checks for record-index generation, `lazy map` drill-down output, old command absence, and record-audit recordQuality complete/missing fixtures.
  - `.lazy-harness/scripts/record-map.ts` — read-only CLI under test for cue-only drill-down candidates.
  - `.lazy-harness/scripts/record-audit.ts` — SCR-501 advisory quality counts for historical record metadata.
- Key symbols:
  - `check_record_index_generator_phase3` — validates schema title, deterministic output, aliases/surface terms, implementation hints, graph ids, projectProfile feature ids, generated cache write, and old context-index command/source/schema absence.
  - `check_record_index_generator_phase3` — also validates `lazy map` output mode, feature alias match, record/source/test/graph drill-down candidates, and absence of semantic-authority field names.
  - `check_record_audit_cli` — validates `recordQuality.advisoryOnly`, inspected/complete counts, all four SCR-501 warning counts, sample path retention, and human-readable warning summaries.
- Flow:
  1. SDD defines header field/consumer contract.
  2. TDD records fixture expectations before parser/cache implementation.
  3. SCR-401 decided canonical name/scope: `record-index`, listing/cache only.
  4. SCR-402 Option A implements executable self-test coverage for the deterministic cache generator, `lazy map`, and old command absence.
  5. SCR-501 Option A implements advisory `recordQuality` counts and complete/missing historical self-test fixtures.
- Protection today:
  - existing self-test protects deleted query helpers, static search/read debt, record-index generation, `lazy map` cue-only drill-down output, old context-index command/source/schema absence, and record-audit recordQuality advisories.
  - recordQuality advisories are counts/samples only and do not make historical records invalid.
  - this record prevents semantic-authority drift in future parser/cache/audit changes.
- Cross-layer links:
  - DDD: `.lazy-harness/domain/searchable-record-memory.md`
  - BDD: `.lazy-harness/behavior/llm-owned-record-retrieval.md`
  - SDD: `.lazy-harness/spec/platform/record-index-header.md`
  - SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`
  - Planning: `.lazy-harness/planning/searchable-record-context-retrieval-tasks.md`
- Machine index:
  - graph ids: `kg_record_index_header_tdd_protects_contract`, `kg_record_index_header_no_raw_message_fixture`, `kg_record_index_phase3_self_test`, `kg_record_index_map_self_test`, `kg_record_audit_record_quality`, `kg_record_audit_record_quality_self_test`
  - generated cache key: `.lazy-harness/generated/record-index.json`

## Layer completeness impact

- DDD: covered by `.lazy-harness/domain/searchable-record-memory.md`.
- BDD: covered by `.lazy-harness/behavior/llm-owned-record-retrieval.md` and scenario mapping above.
- SDD: covered by `.lazy-harness/spec/platform/record-index-header.md`.
- TDD: this record defines fixtures and points to executable self-test coverage, including `lazy map` drill-down and SCR-501 complete/missing historical cases.
- SSOT: `.lazy-harness/ssot/cli-tool-boundary.md` reviewed as sufficient for SCR-303/304.
- ADR: `.lazy-harness/decisions/0042-record-index-cache-naming.md` records canonical `record-index` naming.
- Planning: task statuses updated through SCR-501 completion.

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
- SDD: updated by `.lazy-harness/spec/platform/record-index-header.md` and `.lazy-harness/spec/platform/record-audit.md`.
- TDD: updated by this record.
- ADR: `.lazy-harness/decisions/0042-record-index-cache-naming.md` updated/created for SCR-401.
- SSOT: reviewed/updated in `.lazy-harness/ssot/cli-tool-boundary.md`.
- Planning: updated in `.lazy-harness/planning/searchable-record-context-retrieval-tasks.md` and implementation plan.
