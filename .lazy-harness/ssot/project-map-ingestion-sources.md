# SSOT — Project Map Ingestion Sources

Status: draft
Date: 2026-06-17
Layer: SSOT
Related SDD: `.lazy-harness/spec/platform/project-map-update-loop-v2.md`
Related Project Map: `.lazy-harness/spec/platform/project-map-v2.md`
Related storage SSOT: `.lazy-harness/ssot/project-map-record-storage.md`
Related TDD: `.lazy-harness/tests/project-map-update-loop-v2.md`
Related fixture: `.lazy-harness/fixtures/project-map-update-loop-v2/events.json`

## Rule digest

- Status: draft
- Layer: SSOT
- Scope: framework-global
- Applies when:
  - classifying Project Map update event sources
  - mapping ingestion/update events to Project Map branches
  - deciding confirmation requirements for candidate-to-canonical promotion
  - designing Pi/Jcode/Project Interview/document ingestion update submissions
- Must:
  - use the controlled source and event vocabulary in this SSOT
  - map each event to one or more Project Map branch categories
  - require confirmation before canonical promotion unless the event already includes changed canonical records
  - keep adapters as event sources, not authorities
- Must not:
  - treat generated views, adapter events, or candidate rows as canonical records by themselves
  - skip record-write-update policy when promoting to canonical
  - store raw transcript text as evidence
- Record completion:
  - source/event vocabulary changes update this SSOT, update-loop SDD, TDD, fixture, self-test, manifest, and graph rows together.

## Controlled source vocabulary

- `user`
- `agent`
- `source-inspection`
- `test-run`
- `record-write`
- `project-profile`
- `document-resource`
- `policy-machinery`
- `pi-adapter`
- `jcode-adapter`

## Controlled event vocabulary

- `user-correction`
- `implementation-change`
- `source-discovery`
- `validation-failure`
- `validation-success`
- `adr-decision`
- `project-profile-refresh`
- `policy-promotion`
- `policy-demotion`
- `document-ingestion`
- `adapter-event`

## Event-to-branch mapping

| Event type | Usual branches | Confirmation requirement |
|---|---|---|
| `user-correction` | facts, ownership, contracts, policies | User correction plus record-write policy. |
| `implementation-change` | contracts, expectations, validation, source-links | Changed source/test plus matching canonical record update, or candidate until reviewed. |
| `source-discovery` | source-links, facts, contracts | Source inspection evidence; canonical promotion requires record update. |
| `validation-failure` | validation, contracts, expectations | Test/log evidence; canonical promotion requires a regression or known-issue record. |
| `validation-success` | validation, evidence, source-links | Validation output can attach evidence; canonical promotion requires related record/evidence update. |
| `adr-decision` | decisions, ownership, policies | ADR record path required for canonical state. |
| `project-profile-refresh` | facts, ownership, policies, source-links | Confirmed profile fields can seed canonical records; unknown fields stay candidate/needs-confirmation. |
| `policy-promotion` | policies, ownership | User/team confirmation or accepted policy record required. |
| `policy-demotion` | policies, decisions | User/team confirmation or supersession record required. |
| `document-ingestion` | facts, contracts, ownership, policies | Document-resource record required before canonical support. |
| `adapter-event` | any branch | Adapter event is observation/candidate until core confirmation rules are satisfied. |

## Confirmation requirements

Canonical promotion requires all of these:

1. A root-bound canonical record path is created, updated, or explicitly designated.
2. The target Project Map branch has primary/facets compatible with `.lazy-harness/ssot/project-map-taxonomy.md`.
3. Evidence is compact and attributable.
4. If user/team/project meaning is ambiguous, option-gate resolution happens before canonical promotion.
5. Generated views remain derived from the canonical records/graph/candidate stores.

## Adapter boundary

- Pi adapter source: `pi-adapter`.
- Jcode compatibility source: `jcode-adapter`.
- Both may submit events with evidence and target metadata.
- Neither may set canonical truth without the core record-write/update path.
- Runtime implementation remains future work after Phase 1.5 review.

## Implementation map

- Status: draft
- Primary files:
  - `.lazy-harness/ssot/project-map-ingestion-sources.md` — this SSOT.
  - `.lazy-harness/spec/platform/project-map-update-loop-v2.md` — event packet contract.
  - `.lazy-harness/tests/project-map-update-loop-v2.md` — regression expectations.
  - `.lazy-harness/fixtures/project-map-update-loop-v2/events.json` — source/event fixture.
  - `.lazy-harness/scripts/self-test.py` — static validation.
- Key symbols:
  - `self-test.py#check_project_map_update_loop_v2`
- Protection:
  - `python3 .lazy-harness/scripts/self-test.py --scope framework`
- Machine index:
  - graph id: `kg_project_map_ingestion_sources_ssot`

## Layer completeness impact

- DDD: domain facts can enter through user/source/profile/document events.
- BDD: expectations can enter through implementation/source/profile events.
- SDD: source/event vocabulary supports update-loop contract.
- TDD: validation events map to validation branches and tests.
- ADR: ADR decision events require ADR records before canonical state.
- SSOT: this is the source vocabulary SSOT.
- Planning: Phase 1.5 design-only deliverable.

## Rule placement

- Rule: Project Map ingestion sources and event-to-branch mapping use this controlled vocabulary, and adapters are event sources rather than authorities.
- Scope: framework-global
- Primary record: `.lazy-harness/ssot/project-map-ingestion-sources.md`
- Why not AGENTS.md: this is source-of-truth vocabulary, not prompt grammar.
- Why not `.jcode`: ingestion semantics are adapter-neutral.
- Confirmation: user-approved move to Phase 1.5 on 2026-06-17.

## Discovery capture

- DDD: fact ingestion sources mapped.
- BDD: expectation ingestion sources mapped.
- SDD: event vocabulary mapped to SDD contract.
- TDD: validation event classes mapped.
- ADR: ADR event class mapped.
- SSOT: updated here.
- Planning: Phase 1.5 source vocabulary clarified.
