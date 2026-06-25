# TDD — Project Map V2

Status: draft
Date: 2026-06-16
Layer: TDD
Related SDD: `.lazy-harness/spec/platform/project-map-v2.md`
Related SSOT: `.lazy-harness/ssot/project-map-taxonomy.md`
Related roadmap: `.lazy-harness/planning/lazy-harness-v2-implementation-roadmap.md`

## Rule digest

- Status: needs-review
- Layer: TDD
- Scope: framework-global
- Applies when:
  - validating Project Map V2 node fixtures or generated map outputs
  - changing Project Map V2 primary categories, facets, stage vocabulary, or policy levels
  - adding Pi/Jcode adapter consumption of project-map nodes
- Must:
  - verify example nodes have required fields and valid controlled vocabulary
  - verify one primary category plus multiple facets are supported
  - verify anchor/branch/edge cluster metadata is present and valid
  - verify policy stage/level metadata supports non-test policies
  - verify Pi is represented as primary future adapter and Jcode as compatibility adapter
  - verify generated map data remains navigation/cue-only, not semantic authority
  - verify the host sync manifest includes Project Map V2 fixture canonical records and related planning context needed by BOTH-scope host checks
- Must not:
  - require physical movement of existing layer records in Phase 1
  - permit forbidden semantic-authority fields such as confidence/intent/risk/requiredRead/nextAction
  - center the model on tests only
- Record completion:
  - fixture/schema changes update this TDD, SDD, SSOT, self-test, manifest, and graph rows together.

## Regression cases

| Case | Input | Expected |
|---|---|---|
| `project_map_node_required_fields` | `.lazy-harness/fixtures/project-map-v2/example-node.json` | Required fields exist: schemaVersion, id, title, primary, facets, status, scope, canonicalRecords, links, evidence, policies. |
| `project_map_node_primary_category` | example fixture | `primary` is one of facts/expectations/contracts/decisions/validation/ownership/source-links/policies. |
| `project_map_node_facets` | example fixture | facets are controlled vocabulary and include more than one facet. |
| `project_map_node_cluster` | example fixture | cluster role/anchorId/branches/edges are valid and demonstrate branching beyond one typed node. |
| `project_map_node_edges` | example fixture | edge relations are controlled vocabulary and include facts/expectations/contracts/validation branches. |
| `project_map_node_policy_stages` | example fixture | policies include stage-aware entries beyond test-only behavior. |
| `project_map_node_adapter_boundary` | example fixture | adapter direction says Pi primary and Jcode compatibility. |
| `project_map_node_forbidden_fields` | recursive walk | no confidence/intent/risk/requiredRead/optionalRead/gate/nextAction/candidateMeaning keys. |
| `project_map_v1_compatibility` | SDD/SSOT records | records explicitly say V1 layer folders are not moved in Phase 1. |
| `project_map_v2_sync_package_complete` | `.lazy-harness/manifests/init-categories.json` | Category A sync includes Project Map V2 direction, roadmap, evolution context, SDD, taxonomy, TDD, and fixture globs used by BOTH-scope host tests. |

## Acceptance assertions

Self-test must verify:

1. `.lazy-harness/spec/platform/project-map-v2.md` exists.
2. `.lazy-harness/ssot/project-map-taxonomy.md` exists.
3. `.lazy-harness/tests/project-map-v2.md` exists.
4. `.lazy-harness/fixtures/project-map-v2/example-node.json` exists and parses as JSON.
5. Fixture `schemaVersion == "project-map-node/v1"`.
6. Fixture `primary` is valid.
7. Fixture `facets` are valid and non-empty.
8. Fixture `cluster.role`, `cluster.anchorId`, `cluster.branches`, and `cluster.edges` are valid.
9. Fixture cluster includes at least facts, expectations, contracts, and validation branches.
10. Fixture edge relations are valid controlled vocabulary.
11. Fixture `policies[*].stages[*].stage` and `level` values are valid.
12. Fixture includes at least one non-test policy example.
13. Fixture adapter boundary has `primary == "pi"` and includes `jcode` as compatibility adapter.
14. Forbidden semantic-authority fields are absent recursively.
15. SDD and SSOT mention that Phase 1 does not move existing V1 folders.
16. Category A sync manifest includes all framework Project Map V2 records needed for host fixture canonical path checks.

## Validation commands

Focused validation:

```bash
python3 -m json.tool .lazy-harness/fixtures/project-map-v2/example-node.json
python3 -m py_compile .lazy-harness/scripts/self-test.py
python3 .lazy-harness/scripts/self-test.py --scope framework
```

Full validation:

```bash
.lazy-harness/bin/lazy test
```

## Implementation map

- Status: draft
- Primary files:
  - `.lazy-harness/tests/project-map-v2.md` — this TDD.
  - `.lazy-harness/spec/platform/project-map-v2.md` — SDD node contract.
  - `.lazy-harness/planning/lazy-harness-v2-direction-purpose.md` — fixture canonical direction record.
  - `.lazy-harness/planning/lazy-harness-v2-implementation-roadmap.md` — fixture canonical roadmap record.
  - `.lazy-harness/planning/lazy-harness-v2-evolution-context.md` — fixture related context record.
  - `.lazy-harness/ssot/project-map-taxonomy.md` — taxonomy SSOT.
  - `.lazy-harness/fixtures/project-map-v2/example-node.json` — fixture under test.
  - `.lazy-harness/manifests/init-categories.json` — Category A host sync package.
  - `.lazy-harness/scripts/self-test.py` — validation implementation.
- Key symbols:
  - `self-test.py#check_project_map_v2_schema`
- Protection:
  - `python3 .lazy-harness/scripts/self-test.py --scope framework`
- Machine index:
  - graph ids: `kg_project_map_v2_tdd`, `kg_project_map_v2_self_test`

## Layer completeness impact

- DDD: facts/DDD compatibility is tested through taxonomy text.
- BDD: expectations/stage-aware behavior compatibility is tested through fixture policy stages.
- SDD: SDD node contract is paired with this TDD.
- TDD: this record defines tests.
- ADR: no ADR yet; physical migration/core rewrite requires future ADR.
- SSOT: taxonomy SSOT is tested.
- Planning: roadmap/direction/context records are included in the sync package and protected by manifest checks.

## Rule placement

- Rule: Project Map V2 requires fixture/self-test coverage for node shape, anchor/branch/edge cluster metadata, and controlled vocabulary before implementation or migration work proceeds.
- Scope: framework-global
- Primary record: `.lazy-harness/tests/project-map-v2.md`
- Why not AGENTS.md: this is regression/validation policy for a schema, not prompt grammar.
- Why not `.jcode`: Project Map V2 is Pi-primary and agent-neutral, not Jcode-local.
- Confirmation: user-approved Phase 1 execution; still draft validation subject to review.

## Discovery capture

- DDD: facts branch compatibility tested.
- BDD: expectations branch and stage behavior tested.
- SDD: contract branch/edge vocabulary tested through SDD pairing.
- TDD: validation branch vocabulary updated here.
- ADR: none yet.
- SSOT: tested through taxonomy fixture.
- Planning: Phase 1 exit criteria covered.
