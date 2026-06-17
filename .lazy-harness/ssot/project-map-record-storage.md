# SSOT — Project Map V2 Record Storage

Status: draft
Date: 2026-06-17
Layer: SSOT
Related SDD: `.lazy-harness/spec/platform/project-map-v2.md`
Related taxonomy: `.lazy-harness/ssot/project-map-taxonomy.md`
Related write policy: `.lazy-harness/spec/platform/record-write-update-policy.md`
Related TDD: `.lazy-harness/tests/project-map-record-storage.md`
Related fixture: `.lazy-harness/fixtures/project-map-v2/record-branch-block.md`

## Rule digest

- Status: active
- Layer: SSOT
- Scope: framework-global
- Applies when:
  - storing real project/framework knowledge in Project Map V2
  - writing or updating DDD/BDD/SDD/TDD/ADR/SSOT records that belong to a Project Map cluster
  - designing generated Project Map views from canonical records
- Must:
  - store canonical content in the appropriate existing layer record first
  - add or maintain a `## Project Map branch` block in canonical records that participate in a cluster
  - keep generated Project Map views derived from canonical records and cue-only
  - keep `knowledge/graph.jsonl` as confirmed edge storage, not canonical prose
  - keep V1 folders as canonical storage until a separate migration is approved
- Must not:
  - store canonical facts only in generated Project Map JSON
  - store all branches for a feature in one overloaded file when separate canonical records are clearer
  - let generated views decide intent, risk, required reads, confidence, gate, or next action
- Record completion:
  - changes update this SSOT, Project Map V2 SDD, Project Map V2 TDD, record-write policy, fixture, self-test, manifest sync entries, and graph rows together.

## Storage rule

Project Map V2 storage uses this pattern:

```text
canonical layer records
+ Project Map branch blocks inside those records
+ generated Project Map view derived from records/graph links
```

Canonical truth stays in existing records:

- DDD facts in `.lazy-harness/domain/**`
- BDD expectations in `.lazy-harness/behavior/**`
- SDD contracts in `.lazy-harness/spec/**`
- TDD validation in `.lazy-harness/tests/**`
- ADR decisions in `.lazy-harness/decisions/**`
- SSOT ownership/source-of-truth in `.lazy-harness/ssot/**`
- Planning/backlog in `.lazy-harness/planning/**` or `.lazy-harness/plans/**`

Project Map metadata links the records together. Generated maps render the links, but do not become the source of truth.

## Required `Project Map branch` block

Canonical records that participate in a Project Map cluster should include:

```md
## Project Map branch

- Anchor: `chat-window-patient-sharing`
- Branch: `facts`
- Node: `patient-sharing-identity-rule`
- Primary: `facts`
- Facets: `DDD`, `SSOT`
- Edges:
  - `chat-window-patient-sharing --has-fact--> patient-sharing-identity-rule`
- Related records:
  - `.lazy-harness/behavior/chat-window-patient-sharing.md`
  - `.lazy-harness/spec/chat-patient-sharing-api.md`
  - `.lazy-harness/tests/chat-patient-sharing.md`
```

Minimum fields:

- `Anchor`
- `Branch`
- `Node`
- `Primary`
- `Facets`
- `Edges`
- `Related records`

## Generated view rule

A future generated Project Map view may assemble:

- `## Project Map branch` blocks,
- `## Implementation map` blocks,
- `.lazy-harness/knowledge/graph.jsonl`,
- `.lazy-harness/project/feature-navigation.xml`,
- policy/capability registry entries,
- test/evidence links.

But generated view output is always a navigation aid. It must point back to canonical records/source/tests before being used.

## Candidate vs canonical note

Until Phase 1.5 defines the full update-loop event model:

- user-confirmed facts can be written to canonical records using existing record-write policy,
- unconfirmed discoveries should remain candidates or planning notes,
- Project Map generated views remain derived,
- cluster/branch metadata can be added to canonical records when the anchor/branch relationship is confirmed.

## Implementation map

- Status: draft
- Primary files:
  - `.lazy-harness/ssot/project-map-record-storage.md` — this SSOT.
  - `.lazy-harness/spec/platform/project-map-v2.md` — Project Map node/cluster SDD.
  - `.lazy-harness/ssot/project-map-taxonomy.md` — category/facet/edge taxonomy.
  - `.lazy-harness/spec/platform/record-write-update-policy.md` — write/update policy integration.
  - `.lazy-harness/tests/project-map-record-storage.md` — regression expectations.
  - `.lazy-harness/fixtures/project-map-v2/record-branch-block.md` — canonical record branch-block fixture.
  - `.lazy-harness/scripts/self-test.py` — static validation.
- Key symbols:
  - `self-test.py#check_project_map_v2_schema`
- Protection:
  - `python3 .lazy-harness/scripts/self-test.py --scope framework`
- Machine index:
  - graph ids: `kg_project_map_record_storage_ssot`, `kg_project_map_record_storage_tdd`, `kg_project_map_record_storage_fixture`, `kg_project_map_record_storage_write_policy`

## Layer completeness impact

- DDD: canonical DDD facts stay in domain records with Project Map branch blocks.
- BDD: canonical expectations stay in behavior records with Project Map branch blocks.
- SDD: this storage rule connects to Project Map V2 SDD and record-write policy.
- TDD: `.lazy-harness/tests/project-map-record-storage.md` and self-test protect the storage pattern.
- ADR: future ADR required before physical folder migration or generated map canonicalization.
- SSOT: this record is the canonical storage SSOT.
- Planning: Phase 1.5 update loop will define candidate/canonical lifecycle in detail.

## Rule placement

- Rule: Real Project Map V2 knowledge is stored in canonical layer records with `## Project Map branch` metadata, while generated map views remain derived/cue-only.
- Scope: framework-global
- Primary record: `.lazy-harness/ssot/project-map-record-storage.md`
- Why not AGENTS.md: this is storage architecture, not prompt grammar.
- Why not `.jcode`: V2 is Pi-primary and agent-neutral; Jcode is compatibility only.
- Confirmation: user-confirmed preferred storage approach on 2026-06-17.

## Discovery capture

- DDD: updated as canonical DDD + branch-block storage rule.
- BDD: updated as canonical BDD + branch-block storage rule.
- SDD: updated through Project Map V2/record-write policy integration.
- TDD: updated through storage TDD and fixture.
- ADR: none yet.
- SSOT: updated here.
- Planning: informs upcoming Phase 1.5 update-loop design.
