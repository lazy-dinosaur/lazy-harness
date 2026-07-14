# Cross-Stack Architecture Guidance — Layer 3 Host Mapping

Status: active
Date: 2026-07-13
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
  - confirmed host-mapping decisions update this planning record
  - schema, writer, validator, or enforcement work requires follow-up records and approval
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

`Host Architecture Map` is a conceptual name. Its exact path, schema, and writer
are not approved by this planning decision.

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

## Stable-reference concept

A future confirmed binding needs enough identity to remain explainable across
profile and record evolution. Candidate concepts include:

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

These are semantic requirements, not approved field names or a data schema.

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

A future writer must define atomicity and partial-failure behavior before it may
update the host map and multiple referenced records.

## Non-goals

This planning decision does not approve:

- a Host Architecture Map filename, serialization format, or schema;
- changes to Project Profile V2 packets or promotion writers;
- a profile or constraint registry implementation;
- automatic architecture inference or candidate confirmation;
- dependency, AST, API, runtime, or repository validators;
- new typed policies, capabilities, warning behavior, or hard stops;
- scaffold generation or host source changes.

## Open decisions

1. What exact path and schema own the Host Architecture Map?
2. What stable id and scope-selector grammar links bindings and constraints?
3. How does a promotion transaction update the map and semantic-owner records?
4. Which initial evidence adapters are portable enough for the first catalog?
5. Where and how are waivers versioned, reviewed, expired, and superseded?
6. How are source drift, record drift, and profile-version drift reconciled?
7. Which hosts will pilot the full candidate-to-confirmed mapping flow?

## Rule placement

- Rule: map confirmed profiles through one host architecture map, one semantic
  owner per constraint, separate check/policy links, and scoped waivers.
- Scope: framework-global
- Primary record: `.lazy-harness/planning/cross-stack-architecture-host-mapping.md`
- Why not AGENTS.md: this is a future architecture model, not immediate grammar.
- Why not local notes: the model is shared framework knowledge.
- Confirmation: user-confirmed host map, semantic ownership, responsibility
  separation, and waiver decisions on 2026-07-13.

## Discovery capture

- DDD: candidate vocabulary for binding, constraint, semantic owner, and waiver.
- SDD: candidate Host Architecture Map, reference, and promotion contracts.
- BDD: candidate inspect, option-gate, confirm, and reconsider flow.
- TDD: future ownership, partial-write, drift, conflict, and waiver fixtures.
- ADR: ADR 0054 adopts the responsibility split; storage and implementation remain open.
- SSOT: exact map, id, scope, catalog, and waiver ownership remain undecided.
- Planning: this record is the primary Layer 3 host-mapping baseline.
