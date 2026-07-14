# DDD — Cross-Stack Architecture Guidance Vocabulary

Status: active
Date: 2026-07-14
Layer: DDD
Related ADR: `.lazy-harness/decisions/0054-three-layer-cross-stack-architecture-guidance.md`
Related SDD: `.lazy-harness/spec/platform/architecture-guidance.md`
Related SSOT: `.lazy-harness/ssot/architecture-guidance-storage.md`

## Rule digest

- Status: active
- Layer: DDD
- Scope: framework-global
- Confidence: high
- Aliases:
  - architecture binding vocabulary
  - profile composition terms
  - 아키텍처 바인딩 용어
  - 프로필 조합 어휘
- Surface terms:
  - project base scope binding alias relation waiver
  - 프로젝트 베이스 스코프 바인딩 별칭 관계 예외
- Applies when:
  - describing architecture profile catalogs or Host Architecture Maps
  - turning observed project structure into candidate architecture bindings
  - reviewing a proposed architecture refactor batch
- Must:
  - distinguish candidates, confirmed host truth, and enforced behavior
  - identify bindings by stable scope and value identities rather than paths alone
  - preserve one semantic owner for each constraint body
  - keep aliases transparent and version-pinned
- Must not:
  - treat folder names, framework names, or source observations as confirmation
  - use checks, generated views, or policies as architecture truth
- Record completion:
  - vocabulary changes update the architecture SDD, SSOT, TDD, and catalog schema
- Related records:
  - `.lazy-harness/planning/cross-stack-architecture-guidance.md`
  - `.lazy-harness/planning/cross-stack-architecture-profiles.md`
  - `.lazy-harness/planning/cross-stack-architecture-host-mapping.md`

## Terms

### Architecture principle

A framework-global invariant inherited by every host and profile. The six Layer 1
principles are identified by `ARCH-L1-01` through `ARCH-L1-06`. Their prose remains
in ADR 0054 and the Layer 1 planning record; catalogs store references only.

### Profile value

A versioned normalized value on one Layer 2 axis:

- project-base descriptor;
- runtime/workload;
- internal organization;
- operational/boundary overlay.

A profile value describes portable semantics, not a framework, directory, or
language.

### Project base

The one confirmed host descriptor set for unit, package, deployment, and ownership
topology plus explicit cross-unit edges.

### Architecture scope

A stable host-local identity for a host, unit, entrypoint, or responsibility. Paths
and package/service names map to a scope but do not define its identity. Scope
parentage determines overlap for relation checks.

### Architecture binding

A confirmed association among a normalized profile value, a declared scope, source
or record evidence, and review triggers. Runtime bindings target entrypoint scopes;
organization bindings target responsibility scopes; operational bindings name their
activation condition.

### Architecture candidate

A non-authoritative proposed binding produced from records, source, dependencies, or
runtime evidence. A candidate may be queued or planned, but it cannot change the
Host Architecture Map until a user or authorized team confirms the exact plan.

### Transparent alias

A friendly, versioned name whose complete expansion is a list of normalized binding
templates. Alias parameters supply host scope identities. An alias adds no hidden
constraint and changing its expansion creates a new version.

### Profile relation

A versioned, scope-aware relation between normalized values or bindings:
`requires`, `compatibleWith`, `conflictsWith`, or `strengthens`. Missing relation
evidence is unknown, not implicit compatibility.

### Host Architecture Map

The host-owned canonical composition index. It owns the fact that a binding applies
to a host scope and links to semantic-owner records, evidence, waivers, policies,
and capabilities. It does not duplicate constraint prose.

### Evidence adapter

A reproducible observer such as a dependency query, schema check, AST rule, runtime
probe, or focused test. Its result is evidence of conformance or drift, never a
binding decision.

### Scoped waiver

A confirmed, reviewable exception linked to one constraint and scope. It identifies
owner, authority, rationale record, compensating evidence, and review trigger. It
does not mutate a framework alias.

### Confirmed versus enforced

`confirmed` means the Host Architecture Map records authorized host truth.
`enforced` is not a binding state. Enforcement belongs to separately approved typed
policies and capabilities that reference confirmed constraints.

## Identity invariants

- Stable host, scope, binding, alias-instance, and decision IDs survive path moves.
- Catalog value references are version-pinned.
- A path selector may change without changing scope identity.
- Omission remains unknown; it never means `simple-direct`.
- One constraint body has one canonical DDD/SDD/BDD/TDD/ADR/SSOT/policy owner.

## Project Map branch

- Anchor: `cross-stack-architecture-guidance`
- Branch: `facts`
- Node: `architecture-guidance-vocabulary`
- Primary: `facts`
- Facets: `DDD`, `Project`
- Edges:
  - `cross-stack-architecture-guidance --has-fact--> architecture-guidance-vocabulary`
- Related records:
  - `.lazy-harness/decisions/0054-three-layer-cross-stack-architecture-guidance.md`
  - `.lazy-harness/spec/platform/architecture-guidance.md`
  - `.lazy-harness/ssot/architecture-guidance-storage.md`

## Implementation map

- Status: `implemented; source validation passed; rollout pending`
- Primary files:
  - `.lazy-harness/domain/architecture-guidance.md` — canonical vocabulary.
  - `.lazy-harness/ssot/architecture-profile-catalog.json` — normalized values,
    aliases, and relations by stable reference.
  - `.lazy-harness/project/architecture-map.json` — future host-owned confirmed
    composition; not created by framework sync.
- Protection:
  - `.lazy-harness/tests/architecture-guidance.md`
  - `.lazy-harness/scripts/self-test.py#check_architecture_guidance_cli`

## Rule placement

- Rule: architecture composition uses stable scopes, normalized values, transparent
  aliases, explicit relations, candidates, confirmed maps, and scoped waivers.
- Scope: framework-global
- Primary record: `.lazy-harness/domain/architecture-guidance.md`
- Why not AGENTS.md: this is reusable domain vocabulary, not always-loaded grammar.
- Confirmation: user-approved core+skill pilot on 2026-07-14.

## Discovery capture

- DDD: this record owns the reusable architecture composition vocabulary.
- BDD: the approval-batched refactor flow has an independent behavior record.
- SDD: the CLI, packet, and validation contracts have an independent SDD.
- TDD: schema, no-write, stale-plan, and Project Profile regressions are independent.
- ADR: ADR 0054 remains the architecture decision and receives a pilot amendment.
- SSOT: storage paths and framework/host ownership have an independent SSOT.
- Planning: Layer 1/2/3 planning remains detailed design evidence.
