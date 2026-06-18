# TDD — Project Map Update Loop V2

Status: active-limited-runtime
Date: 2026-06-17
Layer: TDD
Related SDD: `.lazy-harness/spec/platform/project-map-update-loop-v2.md`
Related SSOT: `.lazy-harness/ssot/project-map-ingestion-sources.md`
Related Project Map: `.lazy-harness/spec/platform/project-map-v2.md`
Related fixture: `.lazy-harness/fixtures/project-map-update-loop-v2/events.json`

## Rule digest

- Status: active-limited-runtime
- Layer: TDD
- Scope: framework-global
- Applies when:
  - validating Project Map update-loop event packets
  - changing candidate/canonical transition states
  - changing ingestion source/event vocabularies
  - designing adapters or runtime ingestion that submit Project Map update events
  - validating the limited Project Profile `promote-v2 --confirm` update-loop-event writer
- Must:
  - verify required Phase 1.5 event types are represented
  - verify event packets use required fields and controlled source vocabulary
  - verify candidate/canonical transitions are explicit and evidence-backed
  - verify canonical events include root-bound canonical records
  - verify the host sync package includes canonical records referenced by canonical update-loop fixture transitions
  - verify forbidden semantic-authority fields are absent recursively
  - verify Pi/Jcode adapter events remain non-authoritative unless core confirmation rules are satisfied
  - verify Project Profile update-loop promotion appends only `.lazy-harness/knowledge/project-map-update-events.jsonl` plus queue status metadata
  - verify duplicate Project Profile update-loop promotion dedupes identical event rows without conflicts
- Must not:
  - allow generated Project Map views or adapter events to become canonical truth by themselves
  - allow unconfirmed or adapter-owned runtime mutation outside explicit promotion/confirmation gates
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
| `project_map_update_sync_package_complete` | `.lazy-harness/manifests/init-categories.json` | Category A sync includes the ADR 0041 canonical record used by the `adr-decision` fixture. |
| `project_map_update_forbidden_fields` | recursive event walk | No confidence/intent/risk/requiredRead/optionalRead/gate/nextAction/candidateMeaning keys. |
| `project_map_update_limited_runtime_boundary` | SDD/TDD text + Project Profile fixture | Only confirmed Project Profile `promote-v2` writes append non-canonical update event rows; general adapter runtime remains future work. |

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
12a. Manifest includes ADR 0041 because the `adr-decision` fixture uses it as a canonical record.
13. Project Profile `promote-v2 --confirm` for `promotionTarget.kind=update-loop-event` appends one non-canonical event row to `.lazy-harness/knowledge/project-map-update-events.jsonl` and writes only queue status metadata otherwise.
14. Duplicate Project Profile update-loop promotion dedupes identical event rows and does not create a conflict file.

## Implementation map

- Status: active-limited-runtime
- Primary files:
  - `.lazy-harness/tests/project-map-update-loop-v2.md` — this TDD.
  - `.lazy-harness/spec/platform/project-map-update-loop-v2.md` — event packet contract.
  - `.lazy-harness/ssot/project-map-ingestion-sources.md` — source vocabulary SSOT.
  - `.lazy-harness/fixtures/project-map-update-loop-v2/events.json` — event fixture.
  - `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md` — canonical ADR backing the `adr-decision` fixture event.
  - `.lazy-harness/manifests/init-categories.json` — Category A host sync package.
  - `.lazy-harness/fixtures/project-profile-v2/promote-update-loop-event.json` — Project Profile promote writer fixture.
  - `.lazy-harness/knowledge/project-map-update-events.jsonl` — non-canonical update event row store created by confirmed runtime writers.
  - `.lazy-harness/scripts/self-test.py` — static validation.
- Key symbols:
  - `self-test.py#check_project_map_update_loop_v2`
  - `self-test.py#check_project_profile_v2_queue_runtime`
  - `project-profile.ts#buildUpdateLoopPromotionWrite`
- Protection:
  - `python3 .lazy-harness/scripts/self-test.py --scope framework`
  - `.lazy-harness/bin/lazy test`
- Machine index:
  - graph ids: `kg_project_map_update_loop_v2_sdd`, `kg_project_map_ingestion_sources_ssot`, `kg_project_map_update_loop_v2_tdd`, `kg_project_map_update_loop_v2_fixture`

## Layer completeness impact

- DDD: facts branch transitions are covered by user-correction/source-discovery/project-profile/document-ingestion events.
- BDD: expectation branch transitions are covered by implementation/source/profile events.
- SDD: update-loop event contract and limited runtime boundary are covered.
- TDD: validation failure/success events and update-loop writer append/dedupe behavior are covered.
- ADR: ADR decision events are covered.
- SSOT: ingestion source vocabulary is covered.
- Planning: Phase 1.5 roadmap exit criteria and the limited Project Profile writer slice are covered.

## Rule placement

- Rule: Project Map update-loop fixtures and Project Profile promotion tests must protect event vocabulary, source boundaries, candidate/canonical transitions, forbidden semantic-authority fields, and the limited non-canonical event store append boundary.
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
- ADR: decision event coverage and host sync dependency recorded.
- SSOT: ingestion source coverage recorded.
- Planning: Phase 1.5 exit criteria captured.
