# SDD — Project Map V2

Status: draft
Date: 2026-06-16
Layer: SDD
Related direction: `.lazy-harness/planning/lazy-harness-v2-direction-purpose.md`
Related roadmap: `.lazy-harness/planning/lazy-harness-v2-implementation-roadmap.md`
Related SSOT: `.lazy-harness/ssot/project-map-taxonomy.md`
Related TDD: `.lazy-harness/tests/project-map-v2.md`
Related Pi: `.lazy-harness/spec/platform/pi-agent-package.md`

## Rule digest

- Status: draft
- Layer: SDD
- Scope: framework-global
- Applies when:
  - defining V2 Project Map / Project Atlas knowledge node shape
  - adding metadata that lets records participate in project map generation
  - designing Project Interview output for project understanding or project/team policy discovery
  - designing Pi-first or Jcode-compat adapter behavior that consumes project map data
- Must:
  - define Project Map nodes as canonical-record-backed knowledge nodes, not generated semantic judgments
  - support one primary category and multiple facets
  - support source/test/decision/ownership/policy/evidence links
  - support stage-aware project/team policy metadata without making testing the center of the model
  - keep Pi as the primary future adapter direction and Jcode as compatibility adapter
  - preserve V1 record folders as compatible canonical storage until a separate migration is approved
- Must not:
  - physically move DDD/SDD/BDD/TDD/ADR/SSOT records in Phase 1
  - treat generated project-map output as canonical truth
  - define intent/risk/confidence/required-read/next-action semantic-authority fields
  - make Jcode-specific wiring part of the V2 core model
- Record completion:
  - changes update this SDD, taxonomy SSOT, TDD, example fixture, self-test, manifest sync entries, and graph rows together.

## Purpose

Project Map V2 is the information model for Lazy-Harness V2's living project map / project atlas.

The goal is to let agents recover project understanding and leave the project clearer after work. The map organizes facts, expectations, contracts, decisions, validation evidence, ownership, source links, and policies while keeping canonical records/source/tests as the authority.

## Core principle

A Project Map node is a **knowledge node backed by canonical evidence**.

It may be indexed, rendered, or generated into views, but the generated view is never the truth by itself. The node must point back to canonical records/source/tests/evidence.

## Node shape

The first V2 node shape is JSON-compatible and can later be represented in Markdown frontmatter, sidecar JSON, XML, or generated map views.

Required fields:

```json
{
  "schemaVersion": "project-map-node/v1",
  "id": "stable-slug",
  "title": "Human-readable title",
  "primary": "expectations",
  "facets": ["BDD", "SDD", "TDD"],
  "status": "draft",
  "scope": "framework-global",
  "canonicalRecords": [".lazy-harness/..."],
  "links": {},
  "evidence": [],
  "policies": []
}
```

### Field contract

| Field | Required | Type | Meaning | Forbidden interpretation |
|---|---:|---|---|---|
| `schemaVersion` | yes | `project-map-node/v1` | Version of this node shape. | Not a compatibility guarantee for future schemas. |
| `id` | yes | stable slug | Stable map node id. | Not priority, confidence, or routing id. |
| `title` | yes | string | Human-readable name. | Not an answer to a user request by itself. |
| `primary` | yes | taxonomy category | Primary home/category for the node. | Does not exclude other facets/layers. |
| `facets` | yes | controlled vocabulary array | DDD/BDD/SDD/TDD/ADR/SSOT/Planning/Policy/Evidence/etc. | Not permission to skip layer impact checks. |
| `status` | yes | draft/active/deprecated/etc. | Lifecycle state. | Not truth confidence. |
| `scope` | yes | framework-global/host-project/team-policy/etc. | Applicability scope. | Not a hard enforcement level. |
| `canonicalRecords` | yes | record paths | Canonical records backing the node. | Not proof those records have been read this turn. |
| `links` | yes | object | Source/test/decision/ownership/related links. | Navigation only, not semantic authority. |
| `evidence` | yes | array | Validation or observation evidence. | Not automatic proof of current correctness. |
| `policies` | yes | array | Stage-aware project/team policy references or inline policy hints. | Not hard-block unless policy level says so and adapter enforces it. |

Recommended optional fields:

- `summary`
- `aliases`
- `tags`
- `updatedAt`
- `owners`
- `stageApplicability`
- `openQuestions`

Forbidden fields anywhere in node output unless a future ADR explicitly changes this:

```text
confidence intent risk requiredRead optionalRead gate nextAction candidateMeaning
```

## Primary categories

Allowed `primary` values are defined in `.lazy-harness/ssot/project-map-taxonomy.md`:

- `facts`
- `expectations`
- `contracts`
- `decisions`
- `validation`
- `ownership`
- `source-links`
- `policies`

A node has exactly one primary category in V2 Phase 1. It may have many facets.

## Facets

Allowed initial facets:

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

Facets describe the kinds of knowledge contained in the node. They are not physical folder placement commands.

Examples:

- A behavior requirement with API contract and tests: `primary=expectations`, `facets=["BDD", "SDD", "TDD"]`.
- A project/team commit convention: `primary=policies`, `facets=["Policy", "SSOT", "TDD"]` when it includes validation gates.
- A source ownership boundary: `primary=ownership`, `facets=["SSOT", "Source"]`.

## Link model

`links` should be an object with optional arrays:

```json
{
  "facts": [],
  "expectations": [],
  "contracts": [],
  "decisions": [],
  "validation": [],
  "ownership": [],
  "source": [],
  "tests": [],
  "policies": [],
  "related": []
}
```

Path-like links must stay root-bound to the current host. External links may be allowed later only through explicit document-resource records.

## Stage-aware policies

Project Map V2 supports policy references so a project/team can express different behavior by stage.

Initial stage vocabulary:

- `turn`
- `read-only-analysis`
- `edit`
- `commit`
- `push`
- `release`
- `high-risk-mutation`

Initial policy levels:

- `discover`
- `recommend`
- `default`
- `warn`
- `block`

Testing is only one possible policy dimension. Other project policies may cover design review, dependency changes, DB/schema migration, security/privacy review, UI accessibility, release, documentation, branch/commit/PR style, or human confirmation boundaries.

## Adapter boundary

Project Map V2 is agent-neutral core data.

- Pi is the primary future adapter direction.
- Jcode remains a compatibility adapter for the current harness.
- Adapters may read Project Map nodes and policy registry data, but they must not redefine project map semantics.
- Adapter output must keep generated map data as navigation aid, not semantic authority.

## Compatibility with V1 folders

Phase 1 keeps existing folders as canonical storage:

- `.lazy-harness/domain/**`
- `.lazy-harness/behavior/**`
- `.lazy-harness/spec/**`
- `.lazy-harness/tests/**`
- `.lazy-harness/decisions/**`
- `.lazy-harness/ssot/**`
- `.lazy-harness/planning/**`
- `.lazy-harness/project/**`

Project Map V2 may generate views over these records, but Phase 1 must not move them.

## Example fixture

The canonical Phase 1 fixture is:

```text
.lazy-harness/fixtures/project-map-v2/example-node.json
```

It demonstrates a policy-oriented node with multiple facets, stage-aware policy levels, Pi-primary adapter direction, Jcode compatibility, and source/test/record links.

## Implementation map

- Status: draft
- Primary files:
  - `.lazy-harness/spec/platform/project-map-v2.md` — this SDD contract.
  - `.lazy-harness/ssot/project-map-taxonomy.md` — canonical categories/facets/stages/levels taxonomy.
  - `.lazy-harness/tests/project-map-v2.md` — TDD acceptance and regression cases.
  - `.lazy-harness/fixtures/project-map-v2/example-node.json` — JSON fixture for Phase 1 node shape.
  - `.lazy-harness/scripts/self-test.py` — static fixture/schema validation.
  - `.lazy-harness/manifests/init-categories.json` — sync entry for fixture and records.
- Key symbols:
  - `self-test.py#check_project_map_v2_schema`
- Protection:
  - `python3 .lazy-harness/scripts/self-test.py --scope framework`
- Machine index:
  - graph ids: `kg_project_map_v2_sdd`, `kg_project_map_v2_taxonomy`, `kg_project_map_v2_tdd`, `kg_project_map_v2_fixture`, `kg_project_map_v2_self_test`

## Layer completeness impact

- DDD: Project Map V2 defines a facts category for domain/project facts but does not replace DDD records.
- BDD: expectations category and stage-aware behavior are represented as node categories/facets.
- SDD: this record defines the Phase 1 node contract.
- TDD: `.lazy-harness/tests/project-map-v2.md` and self-test fixture validation protect the shape.
- ADR: no final trade-off ADR yet; future V2 adoption/migration decisions need ADRs.
- SSOT: `.lazy-harness/ssot/project-map-taxonomy.md` defines canonical taxonomy.
- Planning: roadmap Phase 1 is implemented as draft records/fixture only.

## Rule placement

- Rule: Project Map V2 nodes use one primary category plus multiple facets, stay backed by canonical records/source/tests, and remain adapter-neutral with Pi as the primary future adapter direction.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/project-map-v2.md`
- Why not AGENTS.md: this is schema/contract design, not immediate prompt grammar.
- Why not `.jcode`: V2 is agent-neutral and Pi-primary; Jcode is compatibility adapter only.
- Confirmation: user-approved Phase 1 execution; still draft schema subject to review.

## Discovery capture

- DDD: updated as facts category/facet compatibility only.
- BDD: updated as expectations and stage-aware behavior compatibility only.
- SDD: updated by this SDD.
- TDD: updated by `.lazy-harness/tests/project-map-v2.md` and self-test fixture.
- ADR: none yet.
- SSOT: updated by `.lazy-harness/ssot/project-map-taxonomy.md`.
- Planning: roadmap Phase 1 started.
