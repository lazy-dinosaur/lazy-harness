# TDD — Project Map Update Loop V2

Status: draft
Date: 2026-06-17
Layer: TDD
Related SDD: `.lazy-harness/spec/platform/project-map-update-loop-v2.md`
Related SSOT: `.lazy-harness/ssot/project-map-ingestion-sources.md`
Related Project Map: `.lazy-harness/spec/platform/project-map-v2.md`
Related fixture: `.lazy-harness/fixtures/project-map-update-loop-v2/events.json`

## Rule digest

- Status: draft
- Layer: TDD
- Scope: framework-global
- Applies when:
  - validating Project Map update-loop event packets
  - changing candidate/canonical transition states
  - changing ingestion source/event vocabularies
  - designing adapters or runtime ingestion that submit Project Map update events
- Must:
  - verify required Phase 1.5 event types are represented
  - verify event packets use required fields and controlled source vocabulary
  - verify candidate/canonical transitions are explicit and evidence-backed
  - verify canonical events include root-bound canonical records
  - verify forbidden semantic-authority fields are absent recursively
  - verify Pi/Jcode adapter events remain non-authoritative unless core confirmation rules are satisfied
- Must not:
  - allow generated Project Map views or adapter events to become canonical truth by themselves
  - add runtime mutation in Phase 1.5
  - allow event packets to auto-write records without record-write policy
- Record completion:
  - update-loop changes update this TDD, SDD, ingestion SSOT, fixture, storage SSOT, self-test, manifest, and graph rows together.

## Regression cases

| Case | Input | Expected |
|---|---|---|
| `project_map_update_loop_files_exist` | SDD/SSOT/TDD/fixture | All Phase 1.5 deliverables exist. |
| `project_map_update_event_required_fields` | `events.json` | Each event has schemaVersion/id/eventType/source/occurredAt/scope/target/transition/evidence/effects. |
| `project_map_update_event_vocabulary` | `events.json` | Fixture covers user-correction, implementation-change, source-discovery, validation-failure, validation-success, adr-decision, project-profile-refresh, policy-promotion, policy-demotion, document-ingestion, adapter-event. |
| `project_map_update_sources` | `events.json` + SSOT | Sources are controlled and include pi-adapter/jcode-adapter boundaries. |
| `project_map_update_transitions` | `events.json` | Candidate, needs-confirmation, canonical, superseded/rejected or observation states are explicit. |
| `project_map_update_canonical_records` | canonical transitions | Canonical target states include root-bound canonicalRecords. |
| `project_map_update_forbidden_fields` | recursive event walk | No confidence/intent/risk/requiredRead/optionalRead/gate/nextAction/candidateMeaning keys. |
| `project_map_update_no_runtime` | SDD/TDD text | Phase 1.5 remains design-only and adds no runtime implementation. |

## Acceptance assertions

Self-test should verify:

1. `.lazy-harness/spec/platform/project-map-update-loop-v2.md` exists.
2. `.lazy-harness/ssot/project-map-ingestion-sources.md` exists.
3. `.lazy-harness/tests/project-map-update-loop-v2.md` exists.
4. `.lazy-harness/fixtures/project-map-update-loop-v2/events.json` exists and parses.
5. Fixture `schemaVersion == "project-map-update-events/v1"`.
6. Every event has required top-level fields.
7. Fixture covers all required Phase 1.5 event types.
8. Fixture uses only controlled source, primary, facet, transition state, evidence kind, and effect action values.
9. Canonical transitions have at least one root-bound canonical record path.
10. Forbidden semantic-authority fields are absent recursively.
11. SDD/SSOT say adapters are event sources, not authorities.
12. Manifest includes update-loop SDD/SSOT/TDD and fixture glob.

## Implementation map

- Status: draft
- Primary files:
  - `.lazy-harness/tests/project-map-update-loop-v2.md` — this TDD.
  - `.lazy-harness/spec/platform/project-map-update-loop-v2.md` — event packet contract.
  - `.lazy-harness/ssot/project-map-ingestion-sources.md` — source vocabulary SSOT.
  - `.lazy-harness/fixtures/project-map-update-loop-v2/events.json` — event fixture.
  - `.lazy-harness/scripts/self-test.py` — static validation.
- Key symbols:
  - `self-test.py#check_project_map_update_loop_v2`
- Protection:
  - `python3 .lazy-harness/scripts/self-test.py --scope framework`
  - `.lazy-harness/bin/lazy test`
- Machine index:
  - graph ids: `kg_project_map_update_loop_v2_sdd`, `kg_project_map_ingestion_sources_ssot`, `kg_project_map_update_loop_v2_tdd`, `kg_project_map_update_loop_v2_fixture`

## Layer completeness impact

- DDD: facts branch transitions are covered by user-correction/source-discovery/project-profile/document-ingestion events.
- BDD: expectation branch transitions are covered by implementation/source/profile events.
- SDD: update-loop event contract is covered.
- TDD: validation failure/success events are covered.
- ADR: ADR decision events are covered.
- SSOT: ingestion source vocabulary is covered.
- Planning: Phase 1.5 roadmap exit criteria are covered.

## Rule placement

- Rule: Project Map update-loop fixtures must protect event vocabulary, source boundaries, candidate/canonical transitions, and forbidden semantic-authority fields before runtime implementation proceeds.
- Scope: framework-global
- Primary record: `.lazy-harness/tests/project-map-update-loop-v2.md`
- Why not AGENTS.md: this is regression/validation for an information model, not prompt grammar.
- Why not `.jcode`: update-loop validation is adapter-neutral.
- Confirmation: user-approved move to Phase 1.5 on 2026-06-17.

## Discovery capture

- DDD: fact transition coverage recorded.
- BDD: behavior transition coverage recorded.
- SDD: event contract coverage recorded.
- TDD: validation event coverage recorded.
- ADR: decision event coverage recorded.
- SSOT: ingestion source coverage recorded.
- Planning: Phase 1.5 exit criteria captured.
