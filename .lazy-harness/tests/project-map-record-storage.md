# TDD — Project Map V2 Record Storage

Status: draft
Date: 2026-06-17
Layer: TDD
Related SSOT: `.lazy-harness/ssot/project-map-record-storage.md`
Related SDD: `.lazy-harness/spec/platform/project-map-v2.md`, `.lazy-harness/spec/platform/record-write-update-policy.md`
Related fixture: `.lazy-harness/fixtures/project-map-v2/record-branch-block.md`

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Applies when:
  - changing how Project Map V2 knowledge is stored
  - adding Project Map branch metadata to canonical records
  - generating Project Map views from canonical records
- Must:
  - verify canonical layer records remain the source of truth
  - verify the `## Project Map branch` block template exists and contains required fields
  - verify generated Project Map views are derived/cue-only
  - verify V1 folders are not physically moved by this storage rule
- Must not:
  - allow canonical facts to live only in generated project-map output
  - allow generated views to decide intent/risk/required reads/gates
  - make one overloaded record the default for every branch when separate canonical records are clearer
- Record completion:
  - storage-rule changes update this TDD, SSOT, SDD, fixture, self-test, manifest, and graph rows together.

## Regression cases

| Case | Input | Expected |
|---|---|---|
| `project_map_record_storage_ssot_exists` | `.lazy-harness/ssot/project-map-record-storage.md` | Defines canonical records + Project Map branch block + generated view storage rule. |
| `project_map_branch_block_fixture` | `.lazy-harness/fixtures/project-map-v2/record-branch-block.md` | Contains required fields Anchor/Branch/Node/Primary/Facets/Edges/Related records. |
| `project_map_record_write_policy` | `.lazy-harness/spec/platform/record-write-update-policy.md` | Mentions Project Map branch metadata when writing/updating records. |
| `project_map_generated_view_cue_only` | SSOT/SDD text | Generated Project Map view is derived and cue-only. |
| `project_map_storage_no_folder_move` | SSOT/SDD text | V1 layer folders remain canonical storage until separate migration. |

## Acceptance assertions

Self-test should verify:

1. `.lazy-harness/ssot/project-map-record-storage.md` exists.
2. `.lazy-harness/tests/project-map-record-storage.md` exists.
3. `.lazy-harness/fixtures/project-map-v2/record-branch-block.md` exists.
4. Storage SSOT contains `canonical layer records`, `Project Map branch`, and `generated Project Map view`.
5. Fixture contains required `## Project Map branch` fields.
6. `record-write-update-policy.md` says Project Map branch metadata must be maintained when confirmed records participate in a cluster.
7. Generated view remains cue-only/non-canonical.

## Implementation map

- Status: draft
- Primary files:
  - `.lazy-harness/tests/project-map-record-storage.md` — this TDD.
  - `.lazy-harness/ssot/project-map-record-storage.md` — storage SSOT.
  - `.lazy-harness/fixtures/project-map-v2/record-branch-block.md` — fixture.
  - `.lazy-harness/scripts/self-test.py` — static validation.
- Key symbols:
  - `self-test.py#check_project_map_v2_schema`
- Protection:
  - `python3 .lazy-harness/scripts/self-test.py --scope framework`

## Layer completeness impact

- DDD: canonical DDD storage preserved.
- BDD: canonical BDD storage preserved.
- SDD: storage rule integrated with Project Map V2 SDD and write policy.
- TDD: updated here.
- ADR: none yet.
- SSOT: storage SSOT protected.
- Planning: supports Phase 1.5 update-loop design.

## Rule placement

- Rule: Project Map V2 storage must keep canonical knowledge in layer records and use `## Project Map branch` metadata plus generated cue-only views for navigation.
- Scope: framework-global
- Primary record: `.lazy-harness/tests/project-map-record-storage.md`
- Why not AGENTS.md: this is regression/validation for storage architecture, not prompt grammar.
- Why not `.jcode`: Project Map V2 is Pi-primary and agent-neutral.
- Confirmation: user-confirmed preferred storage approach on 2026-06-17.

## Discovery capture

- DDD: canonical DDD record storage protected.
- BDD: canonical BDD record storage protected.
- SDD: write/update policy integration protected.
- TDD: updated here.
- ADR: none yet.
- SSOT: storage SSOT protected.
- Planning: Phase 1.5 input clarified.
