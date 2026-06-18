# SDD — Project Map Update Loop V2

Status: active-limited-runtime
Date: 2026-06-17
Layer: SDD
Related roadmap: `.lazy-harness/planning/lazy-harness-v2-implementation-roadmap.md`
Related Project Map: `.lazy-harness/spec/platform/project-map-v2.md`
Related storage SSOT: `.lazy-harness/ssot/project-map-record-storage.md`
Related ingestion SSOT: `.lazy-harness/ssot/project-map-ingestion-sources.md`
Related TDD: `.lazy-harness/tests/project-map-update-loop-v2.md`
Related fixture: `.lazy-harness/fixtures/project-map-update-loop-v2/events.json`

## Rule digest

- Status: active-limited-runtime
- Layer: SDD
- Scope: framework-global
- Applies when:
  - defining Project Map V2 cluster create/update/promotion semantics
  - modeling candidate-to-canonical transitions for Project Map branches
  - designing Project Interview, Policy Machinery, generated map views, Pi events, or Jcode compatibility events that update project knowledge
  - appending confirmed Project Profile `promote-v2` update-loop events to the non-canonical update event store
- Must:
  - define update events as adapter-neutral observations plus explicit target cluster/branch metadata
  - keep unconfirmed discoveries as `candidate` or `needs-confirmation`
  - promote to `canonical` only when confirmation requirements are satisfied and a canonical record path is updated or designated
  - attach compact evidence without raw transcripts, secrets, or generated semantic-authority claims
  - let core update-loop semantics own candidate/canonical transitions for Pi and Jcode adapters
  - keep generated Project Map views derived/cue-only
  - store non-canonical update event rows in `.lazy-harness/knowledge/project-map-update-events.jsonl`
  - use stable JSONL append semantics for the event store: append, dedupe-identical, or conflict-recorded
- Must not:
  - let adapters, generated views, or event packets become canonical truth by themselves
  - auto-write canonical records from event packets alone
  - include forbidden semantic-authority fields such as confidence/intent/risk/requiredRead/nextAction/candidateMeaning
  - allow unconfirmed or adapter-owned runtime writes to bypass Project Profile `promote-v2 --confirm` or future explicit update-loop confirmation gates
- Record completion:
  - changes update this SDD, ingestion-source SSOT, TDD, fixture, Project Map storage SSOT, self-test, manifest sync entries, and graph rows together.

## Purpose

Project Map V2 has anchors, branches, and edges. Phase 1.5 defines how those clusters change over time.

The update loop began as design-only in Phase 1.5. It now also has one reviewed, limited runtime writer: Project Profile `promote-v2 --confirm` may append an accepted `promotionTarget.kind = update-loop-event` item to the non-canonical event store. The packet shape and transition rules still ensure Project Interview, source/document ingestion, Policy Machinery, generated map views, Pi, and Jcode do not invent separate semantics.

General adapter/runtime ingestion remains future work. The implemented runtime boundary is limited to confirmed Project Profile promotion and never writes canonical records from the event packet alone.

## Event store

Confirmed non-canonical update event rows live in:

```text
.lazy-harness/knowledge/project-map-update-events.jsonl
```

Store rules:

1. The store is append-only JSONL and is not canonical truth.
2. Rows use the same event packet shape defined in this SDD.
3. Stable JSONL append must return one visible outcome: `appended`, `deduped-identical`, or `conflict-recorded`.
4. Same-id/different-payload conflicts are recorded in `.lazy-harness/knowledge/project-map-update-events.jsonl.conflicts.jsonl`.
5. Canonical promotion still requires record-write policy and root-bound canonical record paths.

## Update event packet shape

Project Map update events are JSON-compatible and adapter-neutral.

Required top-level fields:

```json
{
  "schemaVersion": "project-map-update-event/v1",
  "id": "evt-user-correction-location-id",
  "eventType": "user-correction",
  "source": "user",
  "occurredAt": "2026-06-17T00:00:00Z",
  "scope": "framework-global",
  "target": {
    "anchorId": "chat-window-patient-sharing",
    "branch": "facts",
    "nodeId": "patient-sharing-identity-rule",
    "primary": "facts",
    "facets": ["DDD", "SSOT"]
  },
  "transition": {
    "from": "candidate",
    "to": "canonical",
    "requiresConfirmation": false,
    "canonicalRecords": [".lazy-harness/domain/example.md"],
    "candidateStore": ".lazy-harness/knowledge/candidates.jsonl"
  },
  "evidence": [],
  "effects": []
}
```

### Field contract

| Field | Required | Meaning | Forbidden interpretation |
|---|---:|---|---|
| `schemaVersion` | yes | Event packet schema version. | Not compatibility for future schemas. |
| `id` | yes | Stable event id for fixture/log/debug reference. | Not a semantic priority. |
| `eventType` | yes | Controlled event vocabulary. | Not permission to bypass confirmation rules. |
| `source` | yes | Controlled ingestion source vocabulary. | Not an authority level. |
| `occurredAt` | yes | Event timestamp or placeholder in fixtures. | Not ordering authority across adapters. |
| `scope` | yes | framework-global/host-project/team-policy/etc. | Not enforcement level. |
| `target` | yes | Target Project Map anchor/branch/node metadata. | Not proof the target record was read this turn. |
| `transition` | yes | Candidate/canonical lifecycle intent. | Not a canonical write by itself. |
| `evidence` | yes | Compact evidence references. | Not raw transcript storage. |
| `effects` | yes | Expected record/graph/view effects. | Not proof those effects executed; event rows remain non-canonical. |

Recommended optional fields:

- `summary`
- `adapter`
- `relatedRecordDecisionPacket`
- `openQuestions`
- `stageApplicability`

Forbidden fields anywhere in update event output unless a future ADR explicitly changes this:

```text
confidence intent risk requiredRead optionalRead gate nextAction candidateMeaning candidateMeanings
```

## Event vocabulary

Phase 1.5 required event types:

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

## Candidate/canonical transition model

Allowed transition states:

- `observation`: safe evidence was noticed, but no durable Project Map candidate is warranted yet.
- `candidate`: useful knowledge should be captured as a candidate because wording, layer, target branch, or confirmation is incomplete.
- `needs-confirmation`: evidence likely belongs in canonical records, but user/source/test confirmation or option-gate resolution is missing.
- `canonical`: confirmation requirements are satisfied and canonical record paths are updated or designated.
- `superseded`: a candidate/canonical branch is replaced by a later confirmed record.
- `rejected`: a candidate is explicitly not adopted.

Transition rules:

1. `observation → candidate` requires compact evidence and a target anchor or open question.
2. `candidate → needs-confirmation` requires a plausible canonical layer/branch but missing confirmation.
3. `candidate → canonical` requires confirmation and at least one root-bound canonical record path.
4. `needs-confirmation → canonical` requires the question/option gate to be resolved and record-write policy to be followed.
5. `canonical → superseded` requires a replacement record or ADR/SSOT note.
6. `candidate → rejected` requires an explicit rejection reason or stale-candidate cleanup record.

## Evidence attachment rules

Evidence entries should include only compact, attributable references:

```json
{
  "kind": "changed-record",
  "path": ".lazy-harness/spec/platform/project-map-v2.md",
  "summary": "Project Map storage rule added canonical branch metadata.",
  "redaction": "none"
}
```

Allowed evidence kinds:

- `user-confirmation`
- `user-correction`
- `changed-source`
- `changed-record`
- `changed-test`
- `source-inspection`
- `document-resource`
- `validation-output`
- `adr-record`
- `project-profile`
- `policy-record`
- `adapter-observation`

Evidence must stay root-bound for local paths. External documents require document-resource records before becoming canonical support.

## Adapter boundary

- Pi can submit observations/evidence/update events.
- Jcode can submit compatibility events through existing hooks and tools.
- Project Interview can submit `project-profile-refresh` events.
- Document ingestion can submit `document-ingestion` events.
- None of these sources becomes semantic authority.
- Core update-loop semantics decide candidate/canonical transitions.

## Relationship to Record Decision Broker

Record Decision Broker answers whether a turn needs record action. Project Map Update Loop models how a Project Map cluster changes after a candidate or record action exists.

Record Decision Packets may be linked with `relatedRecordDecisionPacket`, but update events stay non-canonical until record-write policy produces or updates canonical records.

## Relationship to generated views

Generated Project Map views may render update event history, current branch status, and links to candidates/canonical records. Generated views remain cue-only. They must point back to the canonical records, candidate rows, evidence records, and source/test files.

## Implementation map

- Status: active-limited-runtime
- Primary files:
  - `.lazy-harness/spec/platform/project-map-update-loop-v2.md` — this SDD.
  - `.lazy-harness/ssot/project-map-ingestion-sources.md` — controlled source/event mapping.
  - `.lazy-harness/tests/project-map-update-loop-v2.md` — regression expectations.
  - `.lazy-harness/fixtures/project-map-update-loop-v2/events.json` — event packet fixture.
  - `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md` — canonical ADR record referenced by the `adr-decision` fixture event.
  - `.lazy-harness/knowledge/project-map-update-events.jsonl` — non-canonical update event row store created by confirmed runtime writers.
  - `.lazy-harness/scripts/project-profile.ts` — limited Project Profile `promote-v2` update-loop-event writer.
  - `.lazy-harness/scripts/self-test.py` — static validation.
- Key symbols:
  - `self-test.py#check_project_map_update_loop_v2`
  - `project-profile.ts#buildUpdateLoopPromotionWrite`
  - `project-profile.ts#applyPromoteV2`
- Protection:
  - `python3 .lazy-harness/scripts/self-test.py --scope framework`
  - `.lazy-harness/bin/lazy test`
- Machine index:
  - graph ids: `kg_project_map_update_loop_v2_sdd`, `kg_project_map_ingestion_sources_ssot`, `kg_project_map_update_loop_v2_tdd`, `kg_project_map_update_loop_v2_fixture`

## Layer completeness impact

- DDD: facts/domain terms can be target branches for update events.
- BDD: expectations/user behavior can be target branches for update events.
- SDD: this record defines the event contract and limited confirmed Project Profile event writer boundary.
- TDD: update-loop fixture/self-test protect event vocabulary, transitions, host sync dependencies, and Project Profile append-only writer behavior.
- ADR: ADR decisions become `adr-decision` events; ADR 0041 is synced as fixture canonical evidence. No new ADR is required for the confirmed limited writer because it does not change canonical promotion semantics.
- SSOT: ingestion-source mapping is defined in `.lazy-harness/ssot/project-map-ingestion-sources.md`; event store placement is defined here and in `.lazy-harness/ssot/project-map-record-storage.md`.
- Planning: Phase 1.5 design deliverables remain complete; limited Project Profile runtime append slice is implemented.

## Rule placement

- Rule: Project Map cluster updates must flow through adapter-neutral update events with explicit candidate/canonical transition semantics and evidence attachments.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/project-map-update-loop-v2.md`
- Why not AGENTS.md: this is an information-model contract, not prompt grammar.
- Why not `.jcode`: update-loop semantics are Pi-primary and adapter-neutral; Jcode remains compatibility.
- Confirmation: user-approved move to next Phase 1.5 slice on 2026-06-17.
- Confirmation: user-approved Option A event store `.lazy-harness/knowledge/project-map-update-events.jsonl` on 2026-06-18.

## Discovery capture

- DDD: candidate/canonical domain fact transitions modeled.
- BDD: behavior expectation transitions modeled.
- SDD: event packet contract and limited Project Profile writer boundary added.
- TDD: fixture/self-test planned and added, including update event store append/dedupe coverage.
- ADR: no new ADR yet.
- SSOT: ingestion source vocabulary added.
- Planning: Phase 1.5 roadmap deliverables implemented; Project Profile promote-v2 update-loop event writer implemented as a limited confirmed runtime slice.
