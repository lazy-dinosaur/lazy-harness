# SDD — Architecture Guidance Core and Project Profile Adapter

Status: active-pilot
Date: 2026-07-14
Layer: SDD
Related ADR: `.lazy-harness/decisions/0054-three-layer-cross-stack-architecture-guidance.md`
Related DDD: `.lazy-harness/domain/architecture-guidance.md`
Related BDD: `.lazy-harness/behavior/architecture-refactor-flow.md`
Related TDD: `.lazy-harness/tests/architecture-guidance.md`
Related SSOT: `.lazy-harness/ssot/architecture-guidance-storage.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Confidence: high
- Aliases:
  - lazy architecture CLI
  - architecture profile runtime
  - Host Architecture Map writer
  - 아키텍처 프로필 런타임
  - 아키텍처 맵 작성기
- Surface terms:
  - architecture inspect plan apply plan digest baseline digest
  - architectureCandidates host-architecture-map delegation
- Applies when:
  - implementing or invoking architecture profile inspection, planning, or apply
  - integrating architecture candidates with Project Profile V2
  - validating catalog values, aliases, relations, scopes, or host maps
- Must:
  - keep inspect and plan read-only
  - require an exact current plan digest and confirmation reference for apply
  - validate and expand aliases before writing a confirmed host map
  - preserve Layer 1, scope cardinality, explicit relation, and semantic-owner rules
  - expose Project Profile architecture candidates as non-authoritative inputs
  - delegate map writes to the narrow architecture writer
- Must not:
  - infer or confirm architecture from folders or frameworks
  - accept a bare boolean confirmation or stale plan
  - write policies, capabilities, semantic-owner records, graph rows, or host source
  - report a Project Profile delegation as an applied host-map write
- Record completion:
  - contract changes update DDD/BDD/TDD/SSOT, fixtures, scripts, help, skill, manifest,
    implementation maps, and graph facts in the same change
- Related records:
  - `.lazy-harness/spec/platform/project-profile-v2.md`
  - `.lazy-harness/spec/platform/pi-agent-package.md`
  - `.lazy-harness/spec/platform/project-map-v2.md`

## Approved pilot boundary

The user approved a core plus skill pilot on 2026-07-14. This slice includes:

- a framework-owned normalized profile catalog;
- a host-owned confirmed architecture map;
- read-only inspect and plan commands;
- an exact-plan confirmed atomic writer;
- a thin Project Profile V2 architecture candidate adapter;
- an approval-batched Pi/OMP refactoring skill;
- schema, fixture, sync, and regression protection.

It excludes source inference as authority, automatic host refactoring, portable evidence
adapters, typed policy/capability enforcement, and warn/block behavior.

## CLI contract

```text
lazy architecture inspect [--root DIR] [--format=md|json]
lazy architecture plan --proposal FILE [--root DIR] [--format=md|json]
lazy architecture apply --proposal FILE --confirm PLAN_DIGEST
                        --confirmation-ref REFERENCE
                        [--root DIR] [--format=md|json]
```

Both `--flag value` and `--flag=value` forms are supported for value flags.

### Inspect

`inspect` reads the framework catalog and optional host map. It returns:

- catalog identity and version;
- catalog validation findings;
- whether the host map exists;
- host-map identity, digest, and validation findings when present;
- a candidate-only notice when the map is absent;
- no selected architecture or mutation.

A missing host map is valid and means unclassified, not `simple-direct`.

### Plan

`plan` reads a full host-map proposal and the current baseline. It:

1. validates proposal shape and root-bound references;
2. resolves catalog value references;
3. expands version-pinned aliases deterministically;
4. validates stable scopes and references;
5. validates cardinality and relation constraints;
6. reports unknown overlapping compositions requiring an explicit composition
   decision reference;
7. returns normalized content, baseline digest, findings, and plan digest.

Plan performs no writes. Relative proposal paths resolve against `--root`. The digest
covers normalized validated catalog content (not only its identity/version), the current
baseline digest, and normalized proposed content. Reordering object keys does not
change it.

### Apply

`apply` reruns plan and refuses to write when:

- `--confirm` is missing, empty, or differs from the recomputed plan digest;
- `--confirmation-ref` is absent;
- the catalog or baseline changed since the confirmed plan;
- schema, reference, alias, cardinality, relation, or semantic-owner validation fails;
- an unknown overlapping composition lacks a host composition decision reference.

Apply records `status=confirmed`, confirmation time/reference, and resulting digest,
then acquires an exclusive cooperative writer lock, re-reads the catalog and baseline
digests, and performs validate → temporary write → atomic rename. It changes only
`.lazy-harness/project/architecture-map.json`.

## Catalog contract

The catalog schema is `architecture-profile-catalog/v1` and contains:

- `catalogId` and semantic `catalogVersion`;
- six Layer 1 `principleRefs` without copied prose;
- versioned normalized `values` on the four axes;
- versioned transparent alias templates;
- explicit scope-aware relations;
- canonical record references for semantic ownership.

Value references use `<axis>/<value>@<semver>`. Aliases supply binding templates with
scope parameter names. Alias instances in proposals map every required parameter to
an existing scope ID. Expansion creates deterministic explicit bindings and keeps
the alias/version reference.

An alias cannot recursively reference another alias in this pilot. Duplicate IDs,
self-relations, duplicate relations, missing references, and directional relation
cycles are errors.

## Host map contract

The host map schema is `host-architecture-map/v1`. It contains:

- host and catalog identity;
- status and confirmation metadata;
- one project-base descriptor set;
- stable scopes with optional Layer 3 path selectors;
- explicit normalized bindings;
- alias instances plus materialized binding IDs;
- host composition decisions for otherwise unknown combinations;
- waiver, evidence-adapter, policy, and capability references;
- review and supersession triggers.

Cardinality:

- exactly one project-base descriptor set;
- each declared entrypoint scope has exactly one runtime binding;
- each declared responsibility scope has exactly one primary organization binding;
- operational bindings are zero-to-many and carry a non-empty condition;
- omission remains unclassified.

Scope parent links must be acyclic. Scope overlap follows parent ancestry. Paths are
selectors only.

## Relation validation

- `requires` is directional; the required value must exist in overlapping or
  explicitly related scope.
- `conflictsWith` is symmetric and rejects overlapping bindings.
- `compatibleWith` is symmetric and documents reviewed coexistence.
- `strengthens` is directional and preserves the target binding.
- Unknown combinations are not silently compatible.
- An explicit host composition decision may accept one unknown pair for a scope and
  must link an ADR or other decision owner.

The pilot does not create policy enforcement from relation findings.

## Project Profile V2 adapter

Architecture integration stays thin and separate from the host-map writer.

`project-profile.ts` accepts an optional architecture candidate file:

```text
--architecture-candidates FILE
```

The adapter helper validates a list of candidate objects. Without that flag,
`architectureCandidates` is exactly `[]`; source layout never creates candidates by
itself.

Each candidate has:

- stable candidate ID and `status=candidate`;
- `sourceQuestionGroup=system-design`;
- proposed normalized bindings and scopes;
- evidence references;
- semantic-owner references;
- `requiresConfirmation=true`.

Queue routing uses:

- `source.kind=architecture-candidate`;
- `primaryRoute=decisions`;
- `primaryRoute=contracts`;
- facets `SDD`, `ADR`, `Project`, and `Evidence`;
- related routes `decisions` and `ownership`;
- `promotionTarget.kind=host-architecture-map`.
- Confirmation: user selected the `contracts` route on 2026-07-14; the candidate
  describes proposed architecture contracts while confirmation remains a later decision.

`promote-v2 --dry-run` previews a delegation. `promote-v2 --confirm` may mark the
accepted queue item as delegated/promoted, but writes only queue metadata and reports
a deferred host-map effect. The architecture skill must still run `lazy architecture
plan`, present the exact plan, and invoke apply with the exact digest after approval.

## Refactor boundary

The architecture CLI records host truth only. Source refactoring is performed by the
Pi/OMP skill using structured edit tools after a separate batch option gate. One
approved batch includes exact files, contracts, tests, records, rollback, and stop
criteria. The CLI never edits application source.

## Error and output contract

- Success exits `0`.
- Invalid proposal, catalog, map, digest, or confirmation exits `2`.
- File/system failures exit `1`.
- JSON output is machine-readable and Markdown output is human-readable.
- Errors name the rejected field or invariant without exposing secrets.
- `inspect` and `plan` include `writes: []`.
- `apply` reports exactly one host-map write on success.

## Project Map branch

- Anchor: `cross-stack-architecture-guidance`
- Branch: `contracts`
- Node: `architecture-guidance-runtime`
- Primary: `contracts`
- Facets: `SDD`, `Project`
- Edges:
  - `cross-stack-architecture-guidance --has-contract--> architecture-guidance-runtime`
- Related records:
  - `.lazy-harness/domain/architecture-guidance.md`
  - `.lazy-harness/behavior/architecture-refactor-flow.md`
  - `.lazy-harness/tests/architecture-guidance.md`
  - `.lazy-harness/ssot/architecture-guidance-storage.md`

## Implementation map

- Status: `implemented; source validation passed; rollout pending`
- Primary files:
  - `.lazy-harness/scripts/architecture-profile-core.ts` — validation, alias
    expansion, deterministic planning, and atomic apply.
  - `.lazy-harness/scripts/architecture-profile.ts` — CLI parser and renderer.
  - `.lazy-harness/scripts/project-profile-architecture.ts` — candidate adapter and
    delegation helpers.
  - `.lazy-harness/scripts/project-profile.ts` — thin packet/queue integration.
  - `.lazy-harness/bin/lazy` — `lazy architecture` dispatch and help.
  - `.lazy-harness/ssot/architecture-profile-catalog.json` — initial catalog.
  - `.lazy-harness/schemas/architecture-profile-catalog.schema.json` — catalog schema.
  - `.lazy-harness/schemas/host-architecture-map.schema.json` — proposal/map schema.
- Protection:
  - `.lazy-harness/tests/architecture-guidance.md`
  - `.lazy-harness/fixtures/architecture-guidance/**`
  - `.lazy-harness/scripts/self-test.py#check_architecture_guidance_cli`
  - `.lazy-harness/scripts/self-test.py#check_project_profile_v2_runtime`
  - `.lazy-harness/scripts/self-test.py#check_project_profile_v2_queue_runtime`

## Layer completeness impact

- DDD: independent vocabulary is owned by `domain/architecture-guidance.md`.
- BDD: independent approval-batched user/agent behavior is recorded.
- SDD: this is the primary runtime and component contract.
- TDD: independent no-write, stale-plan, relation, and delegation protection exists.
- ADR: ADR 0054 is amended with the separately approved pilot.
- SSOT: paths, ownership, sync, and writer authority are independently canonical.
- Planning: no new planning record; approved Layer 1/2/3 plans are inputs.

## Rule placement

- Rule: architecture truth is planned from explicit candidates, confirmed by exact
  digest, and atomically written without source or enforcement side effects.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/architecture-guidance.md`
- Why not AGENTS.md: this is a CLI/data/component contract, not universal grammar.
- Confirmation: user-approved recommended core+skill pilot and source+canary rollout
  on 2026-07-14.

## Discovery capture

- DDD: stable architecture terms and identity rules promoted independently.
- BDD: inspect, option gate, apply, refactor, and stop behavior promoted.
- SDD: this record owns the core and Project Profile adapter contract.
- TDD: fixture and sandbox regressions protect the new runtime.
- ADR: ADR 0054 remains primary and records the approved follow-up slice.
- SSOT: architecture storage/ownership paths promoted independently.
- Planning: existing three-layer plans remain detailed evidence, not runtime truth.
