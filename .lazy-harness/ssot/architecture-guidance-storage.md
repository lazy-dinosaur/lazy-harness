# SSOT — Architecture Guidance Storage and Ownership

Status: active
Date: 2026-07-14
Layer: SSOT
Related ADR: `.lazy-harness/decisions/0054-three-layer-cross-stack-architecture-guidance.md`
Related DDD: `.lazy-harness/domain/architecture-guidance.md`
Related SDD: `.lazy-harness/spec/platform/architecture-guidance.md`
Related TDD: `.lazy-harness/tests/architecture-guidance.md`

## Rule digest

- Status: active
- Layer: SSOT
- Scope: framework-global
- Confidence: high
- Aliases:
  - architecture profile catalog storage
  - Host Architecture Map ownership
  - 아키텍처 프로필 저장소
  - 호스트 아키텍처 맵 소유권
- Surface terms:
  - architecture-profile-catalog.json architecture-map.json
  - profile registry host map schema writer sync ownership
- Applies when:
  - adding or changing architecture catalog, map, proposal, or schema paths
  - syncing architecture guidance into a downstream host
  - deciding whether an architecture artifact is framework-owned or host-owned
- Must:
  - keep the profile catalog and schemas framework-owned and syncable
  - keep each host architecture map host-owned and out of Category A
  - keep candidates outside the confirmed host map
  - keep generated views and validation output non-canonical
  - write confirmed host maps atomically after exact-plan confirmation
- Must not:
  - overwrite or prune a host architecture map during lazy sync
  - store semantic constraint prose in the catalog or host map
  - let policy, capability, graph, or check output become architecture truth
- Record completion:
  - path, ownership, writer, or sync changes update SDD, TDD, manifest, and fixtures
- Related records:
  - `.lazy-harness/ssot/project-map-record-storage.md`
  - `.lazy-harness/spec/lazy-sync-drift-detection.md`
  - `.lazy-harness/ssot/rule-sources.md`

## Canonical paths

| Artifact | Path | Owner | Mutability |
|---|---|---|---|
| Profile catalog | `.lazy-harness/ssot/architecture-profile-catalog.json` | framework | versioned source change |
| Catalog schema | `.lazy-harness/schemas/architecture-profile-catalog.schema.json` | framework | versioned source change |
| Host map schema | `.lazy-harness/schemas/host-architecture-map.schema.json` | framework | versioned source change |
| Confirmed host map | `.lazy-harness/project/architecture-map.json` | host | exact-plan confirmed writer |
| Project Profile queue | `.lazy-harness/project/profile-queue.json` | host | existing queue contract |
| Architecture candidates | existing Project Profile queue or candidate stores | host | non-canonical |
| Generated views | `.lazy-harness/generated/**` | derived | rebuildable |

The framework source repository also consumes the framework catalog, but it does not
receive a confirmed host map merely because the CLI or fixtures exist.

## Ownership boundary

### Framework-owned and Category A

The catalog, schemas, SDD, DDD, BDD, TDD, fixtures, CLI scripts, and operational ADR
0054 are distributed as one compatible framework slice. Downstream edits to these
files are not canonical and may be replaced by `lazy sync`.

### Host-owned and never Category A

`.lazy-harness/project/architecture-map.json` is canonical host composition. It is
created only after a proposal is planned and the exact plan digest is confirmed.
The Category A manifest must not list, seed, merge, prune, or overwrite this path.

Architecture candidates remain in the existing queue/update/candidate surfaces.
They do not enter the host map until confirmation. `lazy sync` preserves all
host-owned project and canonical layer records.

## Stable identity grammar

- Entity IDs use lowercase dot- or colon-separated slugs:
  `^[a-z][a-z0-9-]*(?:[.:][a-z0-9][a-z0-9-]*)*$`.
- Catalog value IDs use `<axis>/<value>` with a lowercase slug value.
- Versioned references use `<axis>/<value>@<semver>`.
- Scope IDs are stable identities such as `scope:host` or `scope:unit:web`.
- Paths, packages, processes, services, and deployments are selectors or mappings,
  not scope identity.
- Binding and alias-instance IDs are unique within one host map.

A renamed folder or package updates a scope selector without changing the scope ID.
Changing catalog semantics creates a new value or alias version.

## Host map authority

The host map owns only:

- the active project-base descriptor set;
- stable scope definitions and Layer 3 path/runtime mappings;
- confirmed normalized bindings and transparent alias instances;
- host-specific composition decisions for otherwise unknown combinations;
- references to semantic-owner records, waivers, checks, policies, and capabilities;
- confirmation, review, retirement, and supersession metadata.

The map links to DDD/SDD/BDD/TDD/ADR/SSOT/policy records for constraint meaning.
It never mirrors their rule bodies.

## Writer contract

`lazy architecture plan` is read-only. It computes:

- the current host-map baseline digest;
- normalized and alias-expanded proposed content;
- schema, reference, cardinality, and relation findings;
- unresolved decisions;
- one deterministic plan digest.

`lazy architecture apply` requires:

- the same proposal;
- the exact plan digest through `--confirm <digest>`;
- an explicit `--confirmation-ref <reference>`;
- an unchanged baseline digest;
- no unresolved validation errors or unknown composition without a decision ref.

Apply validates again, writes a temporary file in the project directory, renames it
atomically, and reports the resulting digest. It writes no semantic-owner record,
policy, capability, graph row, or application source.

## Sync and deployment rule

The package skill and Category A architecture records are separate distribution
channels. A release/canary must verify both:

1. source-linked Pi/OMP package discovery exposes the new skill;
2. `lazy sync` installs the catalog, schemas, records, fixtures, scripts, and ADR 0054;
3. an existing host architecture map remains byte-for-byte unchanged by sync.

## Project Map branch

- Anchor: `cross-stack-architecture-guidance`
- Branch: `ownership`
- Node: `architecture-guidance-storage`
- Primary: `ownership`
- Facets: `SSOT`, `Project`
- Edges:
  - `cross-stack-architecture-guidance --has-ownership--> architecture-guidance-storage`
- Related records:
  - `.lazy-harness/spec/platform/architecture-guidance.md`
  - `.lazy-harness/tests/architecture-guidance.md`
  - `.lazy-harness/ssot/project-map-record-storage.md`

## Implementation map

- Status: `implemented; source validation passed; rollout pending`
- Primary files:
  - `.lazy-harness/ssot/architecture-profile-catalog.json`
  - `.lazy-harness/schemas/architecture-profile-catalog.schema.json`
  - `.lazy-harness/schemas/host-architecture-map.schema.json`
  - `.lazy-harness/scripts/architecture-profile-core.ts`
  - `.lazy-harness/scripts/architecture-profile.ts`
  - `.lazy-harness/manifests/init-categories.json`
- Host-owned target:
  - `.lazy-harness/project/architecture-map.json`
- Protection:
  - `.lazy-harness/tests/architecture-guidance.md`
  - `.lazy-harness/scripts/self-test.py#check_architecture_guidance_cli`

## Rule placement

- Rule: sync the framework catalog and schemas, but never sync or overwrite the
  host-owned confirmed architecture map.
- Scope: framework-global storage and downstream ownership boundary
- Primary record: `.lazy-harness/ssot/architecture-guidance-storage.md`
- Why not AGENTS.md: this is storage and ownership truth, not interaction grammar.
- Confirmation: user-approved core+skill pilot on 2026-07-14.

## Discovery capture

- DDD: vocabulary is owned by `.lazy-harness/domain/architecture-guidance.md`.
- BDD: approval and refactor flow is independently visible to the agent/user.
- SDD: CLI, proposal, validation, and delegation contracts are independent.
- TDD: write boundaries and sync preservation require regression coverage.
- ADR: ADR 0054 is amended with this approved pilot slice.
- SSOT: this record owns canonical paths and framework/host mutability.
- Planning: no additional planning record; the approved scope is implemented here.
