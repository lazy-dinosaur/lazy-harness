# SSOT — Project Map V2 Taxonomy

Status: draft
Date: 2026-06-16
Layer: SSOT
Related SDD: `.lazy-harness/spec/platform/project-map-v2.md`
Related TDD: `.lazy-harness/tests/project-map-v2.md`
Related roadmap: `.lazy-harness/planning/lazy-harness-v2-implementation-roadmap.md`

## Rule digest

- Status: draft
- Layer: SSOT
- Scope: framework-global
- Applies when:
  - assigning Project Map V2 primary categories, facets, stages, or policy levels
  - translating V1 DDD/SDD/BDD/TDD/ADR/SSOT records into V2 map nodes
  - designing Project Interview output or Pi/Jcode adapter policy consumption
- Must:
  - keep exactly one primary category per Project Map node in Phase 1
  - allow multiple facets per node
  - keep existing V1 layer folders as canonical storage until a migration is approved
  - keep generated map views cue-only and non-canonical
  - treat Pi as the primary future adapter and Jcode as compatibility adapter
- Must not:
  - collapse DDD/BDD/SDD/TDD/ADR/SSOT into one undifferentiated bucket
  - treat primary category as enforcement level
  - let generated indexes or adapter prompts override canonical records/source/tests
- Record completion:
  - taxonomy changes update SDD, TDD, fixture, self-test, manifest entries, and graph rows together.

## Primary categories

A Project Map node has exactly one primary category in Phase 1.

| Category | Meaning | Typical V1 source | Notes |
|---|---|---|---|
| `facts` | Project facts, domain concepts, business rules, stable vocabulary. | DDD, SSOT, project records | DDD-like, but can include non-domain project facts. |
| `expectations` | User-visible expectations, requirements, behavior, collaboration expectations. | BDD, plans, project interview | May link to contracts and validation. |
| `contracts` | APIs, components, data, system boundaries, integration/interface promises. | SDD, ADR, source | SDD-like. |
| `decisions` | Why/trade-offs/accepted or rejected choices. | ADR, planning | ADR-like. |
| `validation` | Tests, checks, evidence, regression protection, verification results. | TDD, evidence | TDD-like but broader than tests. |
| `ownership` | Source of truth, authority, modification boundaries, upstream/downstream ownership. | SSOT, project profile | SSOT-like. |
| `source-links` | Code/test/config/package/route/file navigation. | Implementation maps, feature-navigation, graph.jsonl | Navigation aid only. |
| `policies` | Project/team working rules, staged enforcement, collaboration conventions. | rules, capability registry, project interview | Not test-centric; covers any repeatable project/team convention. |

## Facets

Facets describe the kinds of knowledge inside a node. They do not decide physical folder placement by themselves.

Allowed Phase 1 facets:

- `DDD`
- `BDD`
- `SDD`
- `TDD`
- `ADR`
- `SSOT`
- `Planning`
- `Policy`
- `Evidence`
- `Project`
- `Source`

Facet rules:

1. A node may have many facets.
2. At least one facet is required.
3. Facets must not be used as proof that all impacted layers were considered.
4. New facets require SSOT update and fixture/test update.

## Stage vocabulary

Allowed Phase 1 stages:

| Stage | Meaning |
|---|---|
| `turn` | Normal agent turn or task execution. |
| `read-only-analysis` | Analysis/planning/search without mutation. |
| `edit` | File write/edit or source mutation. |
| `commit` | Pre-commit/commit-time validation. |
| `push` | Pre-push/push-time validation. |
| `release` | Release/deploy/dispatch boundary. |
| `high-risk-mutation` | DB writes, destructive operations, force push, payments, irreversible actions. |

Stage rules:

- Policy level may differ by stage.
- A policy can be advisory during `turn` and blocking at `push`.
- Tests are one example. Design review, dependency changes, schema migration, security checks, UI accessibility, or documentation policy may also vary by stage.

## Policy levels

Allowed Phase 1 policy levels:

| Level | Meaning |
|---|---|
| `discover` | Record as a discovered possibility; do not recommend or enforce yet. |
| `recommend` | Suggest when relevant, but do not assume default. |
| `default` | Apply as normal project behavior unless context contradicts it. |
| `warn` | Warn loudly when violated; allow user/agent override with reason. |
| `block` | Block only when project/team has explicitly confirmed blocking behavior or high-risk safety requires it. |

Promotion/demotion must be evidence-backed and record-backed.

## Relationship to V1 folders

| V1 layer/folder | V2 relationship |
|---|---|
| `.lazy-harness/domain/**` | Usually `facts` + `DDD`, but may also link to expectations/contracts. |
| `.lazy-harness/behavior/**` | Usually `expectations` + `BDD`, but may link to validation/contracts. |
| `.lazy-harness/spec/**` | Usually `contracts` + `SDD`, but may include project-map schema contracts. |
| `.lazy-harness/tests/**` | Usually `validation` + `TDD`. |
| `.lazy-harness/decisions/**` | Usually `decisions` + `ADR`. |
| `.lazy-harness/ssot/**` | Usually `ownership` + `SSOT`, or taxonomy/registry authority. |
| `.lazy-harness/planning/**` | Usually future/backlog/evolution context + `Planning`. |
| `.lazy-harness/project/**` | Project profile/navigation source + `Project`. |

Phase 1 does not move files. It defines a compatibility view.

## Adapter taxonomy

- `core`: lazy-harness agent-neutral records, project map, policy machinery, validation contracts.
- `pi`: primary future adapter consuming the core.
- `jcode`: compatibility adapter for the current harness.

Adapters must not own taxonomy semantics.

## Implementation map

- Status: draft
- Primary files:
  - `.lazy-harness/ssot/project-map-taxonomy.md` — this SSOT.
  - `.lazy-harness/spec/platform/project-map-v2.md` — node contract.
  - `.lazy-harness/tests/project-map-v2.md` — regression expectations.
  - `.lazy-harness/fixtures/project-map-v2/example-node.json` — taxonomy fixture.
  - `.lazy-harness/scripts/self-test.py` — static validation.
- Key symbols:
  - `self-test.py#check_project_map_v2_schema`
- Protection:
  - `python3 .lazy-harness/scripts/self-test.py --scope framework`
- Machine index:
  - graph ids: `kg_project_map_v2_taxonomy`, `kg_project_map_v2_fixture`

## Layer completeness impact

- DDD: facts category covers DDD compatibility.
- BDD: expectations category covers BDD compatibility.
- SDD: project-map-v2 SDD defines node contract.
- TDD: tests/project-map-v2 and self-test protect taxonomy.
- ADR: future ADR required before physical migration or core/adapter rewrite.
- SSOT: this record is the taxonomy SSOT.
- Planning: implements roadmap Phase 1 draft only.

## Rule placement

- Rule: Project Map V2 taxonomy defines primary categories, facets, stages, policy levels, and adapter taxonomy for the V2 project atlas.
- Scope: framework-global
- Primary record: `.lazy-harness/ssot/project-map-taxonomy.md`
- Why not AGENTS.md: taxonomy/schema belongs in SSOT/SDD, not always-loaded prompt grammar.
- Why not `.jcode`: taxonomy is agent-neutral and Pi-primary; Jcode remains compatibility adapter.
- Confirmation: user-approved Phase 1 execution; still draft taxonomy subject to review.

## Discovery capture

- DDD: updated as facts/DDD compatibility.
- BDD: updated as expectations/BDD compatibility and stage-aware behavior vocabulary.
- SDD: updated by related SDD.
- TDD: updated by related TDD/self-test.
- ADR: none yet.
- SSOT: updated here.
- Planning: roadmap Phase 1 started.
