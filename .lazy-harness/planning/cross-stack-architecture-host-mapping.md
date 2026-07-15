# Cross-Stack Architecture Guidance — Layer 3 Host Mapping

Status: implemented-pilot; downstream-canary-blocked
Date: 2026-07-13
Updated: 2026-07-14
Layer: Planning
Related Layer 1: `.lazy-harness/planning/cross-stack-architecture-guidance.md`
Related Layer 2: `.lazy-harness/planning/cross-stack-architecture-profiles.md`
Related profile contract: `.lazy-harness/spec/platform/project-profile-v2.md`
Related policy contract: `.lazy-harness/spec/platform/policy-machinery-v2.md`
Related rule placement: `.lazy-harness/ssot/rule-sources.md`
Related ADR: `.lazy-harness/decisions/0054-three-layer-cross-stack-architecture-guidance.md`

## Rule digest

- Status: active
- Layer: Planning
- Scope: framework-global
- Confidence: medium
- Aliases:
  - host architecture map
  - profile-to-record mapping
  - architecture constraint ownership
  - 호스트 아키텍처 맵
  - 프로필 규칙 연결
- Applies when:
  - mapping confirmed Layer 2 profile bindings into a host
  - deciding which record owns an architecture constraint
  - connecting architecture truth to checks or policy/capability enforcement
  - documenting an intentional exception to a profile constraint
- Must:
  - use one host architecture map as the profile composition and provenance index
  - give each architecture constraint exactly one canonical semantic owner
  - keep truth, evidence adapters, and policy/capability enforcement separate
  - represent intentional deviations as scoped waivers
  - preserve observe-confirm-enforce and no-silent-defaults behavior
- Must not:
  - mirror the same constraint body into the map and multiple layer records
  - treat a generated index, check result, or policy as architecture truth
  - mutate a framework profile alias to hide a host exception
  - let confirmation silently activate warning or blocking enforcement
- Record completion:
  - confirmed host-mapping decisions update this planning baseline
  - catalog/schema/writer/adapter changes update ADR 0054 and linked canonical records,
    fixtures, graph facts, and evidence under separate approval
- Related records:
  - `.lazy-harness/planning/cross-stack-architecture-profiles.md`
  - `.lazy-harness/decisions/0054-three-layer-cross-stack-architecture-guidance.md`
  - `.lazy-harness/spec/platform/project-profile-v2.md`
  - `.lazy-harness/spec/platform/policy-machinery-v2.md`
  - `.lazy-harness/ssot/rule-sources.md`

## Confirmed Layer 3 shape

On 2026-07-13 the user confirmed four host-mapping decisions:

1. **Project map plus layer references** is the host composition baseline.
2. **One semantic owner** owns each architecture constraint body.
3. **Truth, check, and policy** are separate responsibilities.
4. **Scoped waivers** represent intentional deviations.

The conceptual flow is:

```text
Layer 1 universal principles
  +
Layer 2 normalized values and versioned aliases
  |
  v
Project Profile inspection/interview
  -> candidate bindings (no authority)
  -> user/team confirmation
  |
  v
Host Architecture Map
  - confirmed binding and scope composition
  - provenance and alias/version references
  - semantic-owner record references
  - waiver, check, policy, and capability references
  |
  +--> DDD/SDD/BDD/TDD/ADR/SSOT semantic owners
  +--> evidence adapters and validation outputs
  +--> optional policies/capabilities with separately approved levels
```

`Host Architecture Map` began as a conceptual name in the 2026-07-13 planning
baseline. ADR 0054's 2026-07-14 bounded amendment now approves its canonical path,
schema, and exact-plan atomic writer while preserving host ownership and no-enforcement.

## Host Architecture Map responsibility

The host map owns **composition facts**, not every rule body. It records:

- which normalized Layer 2 bindings the host confirmed;
- where each binding applies;
- the project-base topology descriptor set;
- runtime entrypoint, organization-scope, and operational-condition bindings;
- activation provenance and the confirmed alias/version, if any;
- stable references to semantic constraints and their owner records;
- stable references to waivers, evidence adapters, policies, and capabilities;
- reconsideration, retirement, or supersession triggers.

Candidates remain in a non-canonical Project Profile queue or Project Map
candidate surface. Only confirmed bindings enter the canonical host composition.
Generated indexes may accelerate retrieval but cannot become semantic authority.

## One semantic owner

Every constraint has one canonical owner. Other surfaces link by stable identity
instead of copying the body.

| Constraint meaning | Canonical semantic owner |
|---|---|
| Host role, source-of-truth, unit/deployment ownership, forbidden mutation | SSOT |
| Domain vocabulary, business invariant, business state authority | DDD |
| API, component, data, IPC, dependency, or boundary contract | SDD |
| User-visible flow or expected behavior | BDD |
| Regression and protection expectation | TDD |
| Architecture choice, trade-off, or rationale | ADR |
| Repeated agent/team operating behavior | typed policy; capability for action steering |
| Multi-step rollout or unresolved backlog | Planning |

The Host Architecture Map is the semantic owner only for the fact that a
particular normalized binding applies to a particular host scope. It links to the
layer record that owns what the associated constraint means.

A cross-layer impact creates references and independently meaningful records only
when each layer has a real semantic delta. It does not create synchronized prose
mirrors.

## Stable-reference grammar

The bounded pilot normalized the previously candidate identity requirements into the
framework schema and writer contract. The approved fields cover:

- stable binding id;
- scope reference;
- normalized value id;
- alias id and version plus its explicit expansion;
- activation evidence and confirmation reference;
- semantic constraint ids and owner-record paths;
- waiver ids;
- evidence-adapter ids;
- policy and capability ids;
- review, retirement, or supersession trigger.

These requirements now have approved pilot field names and validation rules in
`.lazy-harness/spec/platform/architecture-guidance.md`,
`.lazy-harness/schemas/host-architecture-map.schema.json`, and
`.lazy-harness/ssot/architecture-guidance-storage.md`.

## Truth, check, and policy separation

The three responsibilities are deliberately independent:

| Responsibility | Owns | Does not own |
|---|---|---|
| Canonical truth | binding, scope, and constraint meaning | adapters or enforcement |
| Evidence adapter | reproducible observation | architecture authority |
| Policy/capability | stage, level, actions, bypass, rollback | constraint body |

Examples of evidence adapters include dependency-graph queries, import-boundary
checks, API or schema compatibility checks, AST rules, lifecycle probes, and
focused tests. A failed check is evidence of drift or non-conformance; it does not
silently rewrite the profile or canonical constraint.

A confirmed constraint may have no executable adapter. An available adapter may
remain advisory. `default`, `warn`, or `block` requires its own typed policy,
capability/action binding when needed, evidence, bypass/rollback semantics, and
explicit approval under Policy Machinery V2.

## Scoped waiver model

A host deviation does not mutate the framework alias, erase the constraint, or
become an unexplained override. It becomes a waiver linked from the Host
Architecture Map.

A waiver must identify:

- the affected constraint and profile binding;
- the exact host scope;
- owner and approving authority;
- rationale and accepted trade-off;
- compensating evidence or controls;
- creation evidence;
- an expiry or mandatory review trigger;
- current state and supersession reference when replaced.

The waiver body has one canonical semantic owner selected by its meaning. An ADR
is the usual owner for a trade-off, while a more specific contract or ownership
record may own the constraint being waived. The Host Architecture Map stores the
reference and effective scope, not a second copy of the rationale.

Repeated similar waivers may become evidence for revising a Layer 2 alias or
catalog relation, but they never promote themselves automatically.

## Project Profile integration

The confirmed existing Project Profile V2 boundary remains suitable:

1. Inspect source, dependency, runtime, and canonical-record evidence.
2. Produce scoped architecture binding candidates with no authority.
3. Present ambiguous choices through an option gate.
4. On user/team confirmation, plan promotion to the Host Architecture Map and
   referenced semantic-owner records.
5. Offer available evidence adapters as checks.
6. Ask separately before creating or strengthening policy/capability enforcement.

This preserves the existing path:

```text
observation -> candidate -> confirmation -> canonical mapping
                                     \-> optional check
                                     \-> separately approved enforcement
```

The approved writer updates only the host map under an exclusive lock, recomputes the
catalog and baseline digests, and performs validate → temporary write → atomic rename.
Project Profile queue promotion remains a separate delegation and never pretends that
the host map or semantic-owner records were written.

## Post-pilot non-goals

The bounded pilot still does not approve:

- automatic architecture inference or candidate confirmation;
- application-source or host-folder refactoring in the framework work unit;
- automatic updates to semantic-owner records, graph rows, policies, or capabilities;
- portable dependency/AST/API/runtime enforcement adapters;
- typed policy/capability warning or blocking behavior;
- scaffold generation or npm publication.

## Resolved pilot decisions

ADR 0054 and the linked SDD/SSOT now resolve the original pilot questions:

1. Canonical host map: `.lazy-harness/project/architecture-map.json`, host-owned.
2. Framework schema: `.lazy-harness/schemas/host-architecture-map.schema.json`.
3. Stable ID/scope/reference grammar: defined by the schema and storage SSOT.
4. Promotion boundary: Project Profile queues candidates and delegates; only
   `lazy architecture apply` may write the map after exact-plan confirmation.
5. Writer atomicity: exclusive lock, catalog/baseline recheck, temporary write,
   atomic rename, and artifact cleanup.

## Current rollout state

- Framework baseline commit: `71d6e11`.
- Source implementation commit: `c7c3d61b876273ddc78a41fb16171b8187328a7b`,
  pushed to `origin/main` with matching remote SHA.
- Source validation and source-path Pi/OMP skill discovery are complete; durable
  command/results evidence remains in
  `.lazy-harness/evidence/2026-07-14-cross-stack-architecture-pilot-validation.md`.
- No confirmed architecture map exists in the framework source checkout.
- The single downstream canary remains blocked until W1.4 explicitly reports
  `COMPLETE/SAFE`; no downstream sync or application-source edit is authorized before it.

## Remaining decision gates

1. Which initial portable evidence adapters are justified by pilot evidence?
2. How are source drift, record drift, catalog-version drift, retirement, and
   supersession reconciled?
3. How are scoped waivers versioned, reviewed, expired, and superseded?
4. Which real host will first confirm a map composition?
5. Will any independently reviewable host source-refactor seam be approved separately?
6. Will any policy/capability enforcement slice be approved separately?
7. Resume the 37-row legacy graph migration only through `lazy-graph-migrate` with
   batch-scoped user approval; it is not part of architecture rollout.

## Rule placement

- Rule: map confirmed profiles through one host architecture map, one semantic
  owner per constraint, separate check/policy links, and scoped waivers.
- Scope: framework-global
- Primary record: `.lazy-harness/planning/cross-stack-architecture-host-mapping.md`
- Why not AGENTS.md: this is the Layer 3 design and rollout baseline, not immediate grammar.
- Why not local notes: the model is shared framework knowledge.
- Confirmation: user-confirmed the host map, semantic ownership, responsibility
  separation, and waiver decisions on 2026-07-13, then separately approved the bounded
  core + Pi/OMP skill pilot and safety-gated canary rollout on 2026-07-14.

## Discovery capture

- DDD: none because binding, scope, candidate, alias, relation, evidence-adapter, and
  waiver vocabulary is already canonical in `.lazy-harness/domain/architecture-guidance.md`;
  this reconciliation found no independent domain delta.
- SDD: none because the Host Architecture Map, validation, writer, and Project Profile
  delegation contracts are already canonical in
  `.lazy-harness/spec/platform/architecture-guidance.md`; no contract changed.
- BDD: none because candidate inspection, exact map confirmation, separate source-batch
  approval, safety stops, and no-refactor canary behavior are already canonical in
  `.lazy-harness/behavior/architecture-refactor-flow.md`.
- TDD: none because ownership, traversal, digest, relation, scope-cycle, lock, atomicity,
  delegation, package, and sync-preservation regressions are already canonical in
  `.lazy-harness/tests/architecture-guidance.md`; no new protection case was introduced.
- ADR: none because ADR 0054 already preserves the original planning boundary and bounded
  pilot amendment; no new trade-off was approved.
- SSOT: none because exact catalog/schema/map paths, framework-versus-host ownership,
  writer authority, and sync preservation are already canonical in
  `.lazy-harness/ssot/architecture-guidance-storage.md`.
- Planning: updated because this is the primary Layer 3 rollout/backlog record and now
  captures the W1.4-gated canary, portable adapters, drift/lifecycle, real-host mapping and
  source seams, optional enforcement, and separate graph migration.
- Candidate store: none because no unconfirmed architecture fact was discovered; the
  unresolved items are multi-step rollout/design gates and remain in this planning record.
- Graph draft: none because no new implementation fact was discovered. Existing confirmed
  facts remain represented by `kg_adr0054_architecture_core_pilot_20260714`,
  `kg_architecture_guidance_core_impl_20260714`,
  `kg_architecture_guidance_cli_impl_20260714`,
  `kg_project_profile_architecture_adapter_20260714`,
  `kg_architecture_refactor_skill_20260714`,
  `kg_architecture_guidance_self_test_20260714`, and
  `kg_architecture_catalog_storage_20260714`.
