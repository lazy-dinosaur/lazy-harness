# Cross-Stack Architecture Guidance — Layer 2 Profile Model

Status: active
Date: 2026-07-13
Layer: Planning
Related baseline: `.lazy-harness/planning/cross-stack-architecture-guidance.md`
Related direction: `.lazy-harness/planning/lazy-harness-v2-direction-purpose.md`
Related profile contract: `.lazy-harness/spec/platform/project-profile-v2.md`
Related host mapping: `.lazy-harness/planning/cross-stack-architecture-host-mapping.md`
Related ADR: `.lazy-harness/decisions/0054-three-layer-cross-stack-architecture-guidance.md`

## Rule digest

- Status: active
- Layer: Planning
- Scope: framework-global
- Confidence: medium
- Aliases:
  - architecture profiles
  - profile composition
  - base and unit overlays
  - 아키텍처 프로필
  - 프로필 조합
- Applies when:
  - designing Layer 2 architecture profiles for mixed-system hosts
  - deciding whether one repository may use multiple architecture patterns
  - mapping web, API, worker, package, or service units to guidance
- Must:
  - keep the six Layer 1 principles active for every profile
  - combine a project base with scoped unit overlays across four profile axes
  - normalize named methods and declare compatibility, omission, and exit rules
- Must not:
  - force one architecture label across every unit in a host
  - let a profile silently weaken Layer 1 or another profile
- Record completion:
  - confirmed profile families and fields update this record
  - schema or runtime work requires follow-up decision records, SDD, TDD, and approval
- Related records:
  - `.lazy-harness/planning/cross-stack-architecture-guidance.md`
  - `.lazy-harness/decisions/0054-three-layer-cross-stack-architecture-guidance.md`
  - `.lazy-harness/spec/platform/project-profile-v2.md`

## Confirmed composition decision

On 2026-07-13 the user selected **project base + unit overlays**.

A host may contain different architectural units in one repository or system.
For example, a monorepo may include a browser application, an API service, a
background consumer, shared packages, and generated bindings. Applying one
named architecture to all of them would erase real runtime and ownership
differences.

The confirmed composition shape is:

```text
Layer 1: six cross-stack principles (always active)

Layer 2 project base
  ├─ topology and ownership defaults
  ├─ cross-unit dependency rules
  └─ project-wide evidence expectations

Layer 2 unit bindings
  ├─ runtime/workload value per entrypoint
  ├─ internal-organization value per responsibility scope
  └─ condition-activated operational/boundary overlays

Layer 3 host mapping
  └─ paths, units, owners, selected profiles, exceptions, and checks
```

This is a design decision, not an approved data schema or implementation.

## Confirmed catalog organization

On 2026-07-13 the user selected a **multi-axis profile catalog**.

The catalog is organized by four orthogonal concerns:

1. **Project base: topology and ownership**
   - Describes units, ownership, deployment relationships, and cross-unit edges.
2. **Runtime/workload overlays**
   - Describe how a unit is invoked, runs, stops, and interacts with effects.
3. **Internal-organization overlays**
   - Describe responsibility placement and dependency rules inside a unit.
4. **Operational/boundary overlays**
   - Describe contracts, state, delivery, generation, risk, and deployment needs.

Named methods such as FSD, vertical slices, modular monolith, or Hexagonal
Architecture may become documented bundles or aliases over these axes. They do
not replace the axes as canonical semantics. Presets may improve onboarding,
but every preset must decompose into explicit axis values and constraints.

Axis semantics, initial values, scope cardinality, compatibility, aliasing, and
activation lifecycle are confirmed. Concrete schemas and catalogs remain open.

## Composition rules

1. **Layer 1 is inherited, not selected.**
   Profiles instantiate or strengthen the six principles; they cannot silently
   disable them.
2. **The project base governs relationships among units.**
   It owns topology, cross-unit dependency direction, ownership defaults, and
   mappings among repository, package, process, service, and deployment.
3. **Unit overlays govern internal and runtime-specific behavior.**
   A web application and worker in the same host may select different overlays.
4. **Selection is evidence-based and scoped.**
   Every profile instance names its target unit, activation evidence, omissions,
   and reconsideration trigger.
5. **Compatibility is explicit.**
   Profiles declare `requires`, `compatibleWith`, `conflictsWith`, and
   `strengthens` semantics before composition becomes a default.
6. **Stronger constraints win only inside their declared scope.**
   A strict domain-core overlay does not force unrelated CRUD or CLI units to
   add ceremonial ports and mappings.
7. **Folder names are Layer 3 mappings.**
   A profile describes responsibilities and allowed edges. Hosts map those
   semantics to ecosystem-appropriate files, packages, projects, or services.
8. **Ambiguous composition requires confirmation.**
   The harness must not infer a named architecture from directory names alone.

## Confirmed normalized axis values

On 2026-07-13 the user confirmed the value semantics for all four axes.

### Project base — pure topology and ownership descriptors

The project base records observable topology rather than architecture names:

- unit topology: `single-unit` or `multi-unit`;
- package topology: `single-package` or `multi-package`;
- deployment topology: `single-deployment`, `multi-deployment`, or `hybrid`;
- ownership topology: `single-owner` or `multi-owner`;
- explicit edges among units, packages, owners, and deployments.

`modular-monolith`, `microservices`, and `monorepo` are derived descriptions or
presets over these facts, not canonical base values.

### Runtime/workload — invocation and lifetime

Runtime values describe how a scoped entrypoint is invoked and lives:

- `interactive-session`;
- `request-response`;
- `one-shot-command`;
- `scheduled-batch`;
- `long-running-consumer`;
- `reusable-library`;
- `generated-binding`.

Framework names such as Next.js, Spring, Django, or Kafka remain Layer 3 stack
mappings. Each entrypoint has one runtime binding, while a unit may expose
multiple entrypoints as defined below.

### Internal organization — responsibility placement

Organization values describe where decisions and dependencies live:

- `simple-direct`;
- `feature-use-case`;
- `capability-module`;
- `domain-centered`;
- `presentation-composition`.

Named methods can project onto these values:

- FSD-inspired → `presentation-composition` + `feature-use-case`;
- Vertical Slice → `feature-use-case`;
- modular monolith → topology facts + `capability-module`;
- Hexagonal/Clean/Onion → usually `domain-centered` plus boundary overlays;
- tactical DDD → selective `domain-centered` units with invariant-rich rules.

These mappings are explain surfaces, not exact equivalence or universal
activation.

### Operational/boundary — condition-activated overlays

Operational overlays activate only when their condition exists:

- `public-contract`;
- `persisted-state`;
- `async-delivery`;
- `generated-artifact`;
- `independent-deployment`;
- `regulated-or-high-risk`.

Each overlay adds condition-specific declarations and evidence. For example,
`async-delivery` may require acknowledgement, retry, idempotency, poison
handling, and drain semantics. It does not make those mechanisms universal for
all runtimes.

## Confirmed scope-binding cardinality

On 2026-07-13 the user selected a **scope binding** model:

1. A host has exactly one active project-base descriptor set.
   - Each topology dimension has one active value plus its explicit graph edges.
2. A unit has zero or more runtime entrypoints.
   - Each entrypoint has exactly one runtime value.
   - One unit may therefore contain an HTTP endpoint, scheduled task, and command
     without collapsing them into one runtime label.
3. Internal organization is bound to declared responsibility scopes.
   - Each declared scope has one primary organization value.
   - Multiple organization values require nested or disjoint scopes rather than an
     unexplained list on the same scope.
4. Operational overlays are zero-to-many condition bindings.
   - Each binding names its condition, target scope, activation evidence, and
     applicable constraints.
5. Unknown or omitted is not equivalent to `simple-direct`.
   - `simple-direct` is an explicit confirmed choice; missing evidence remains
     unclassified.

## Confirmed compatibility semantics

Compatibility uses a **scope-aware relation graph**, not a single global matrix.
Relations are typed as:

- `requires`: the source binding is incomplete without the target;
- `compatibleWith`: a reviewed composition is known to coexist in the declared
  scope;
- `conflictsWith`: overlapping bindings cannot both govern the declared scope;
- `strengthens`: the source adds stricter constraints without replacing the target.

Resolution rules:

1. Expand versioned aliases into explicit bindings before evaluation.
2. Evaluate relations only where scopes overlap or a relation explicitly crosses
   scopes.
3. Allow different runtime values on different entrypoints of the same unit.
4. Allow nested organization values when each responsibility scope and dependency
   edge is explicit.
5. Compose operational overlays when their conditions coexist.
6. Treat an undocumented combination as unknown, not silently compatible.
7. Route an unresolved conflict through a user option gate; never self-select.

## Confirmed named-method alias rules

FSD, Vertical Slice, modular monolith, Hexagonal/Clean/Onion, and similar names
may be provided as **transparent versioned aliases or bundles**.

A valid alias must:

- have a stable id and explicit version;
- expand completely into project-base descriptors, scoped axis bindings, and
  relation constraints;
- add no hidden semantics beyond that expansion;
- state omissions, assumptions, activation evidence, and exit triggers;
- preserve Layer 1 and surface all conflicts;
- record host overrides separately rather than silently mutating the alias.

Changing an alias expansion creates a new version. A host may cite the friendly
name for explanation, but canonical evaluation uses the expanded bindings.

## Confirmed activation lifecycle

On 2026-07-13 the user selected **observe → confirm → enforce**:

1. `candidate`
   - Source, dependency, runtime, or record evidence may suggest a scoped binding.
   - A candidate has no authority over host behavior.
2. `confirmed`
   - A user or authorized team decision accepts the binding, scope, omissions, and
     review trigger into Layer 3 host records.
3. `enforced`
   - A separate approved policy/capability binding selects stage, enforcement level,
     adapter, and evidence requirements.

Observation never silently promotes a value. Confirmation does not implicitly
authorize a warning or block, and enforcement approval does not rewrite the
underlying architectural choice. Retirement and supersession need explicit schema
and versioning rules.

## Example mixed host

```text
project base:
  units: multi-unit
  packages: multi-package
  deployments: multi-deployment
  ownership: multi-owner

units:
  web:
    runtime:
      browser: interactive-session
    organization:
      unit: presentation-composition
      scopes:
        features/*: feature-use-case

  api:
    runtime:
      http: request-response
    organization:
      unit: capability-module
      scopes:
        use-cases/*: feature-use-case

  billing-domain:
    organization:
      unit: domain-centered
    overlays: persisted-state + public-contract

  notifications-worker:
    runtime:
      events: long-running-consumer
    overlays: async-delivery + independent-deployment

  contracts:
    runtime:
      generated-client: generated-binding
    overlays: generated-artifact + public-contract
```

The example demonstrates composition only. No host is required to use this
combination.

## Candidate profile-instance fields

A future profile instance may need:

- `profileId` and version;
- `scope` or target unit;
- activation evidence;
- inherited Layer 1 principles;
- constraints and allowed dependency edges;
- required declarations or records;
- required/optional evidence adapters;
- `requires`, `compatibleWith`, and `conflictsWith` relations;
- intentional omissions;
- exceptions with owner, rationale, and review trigger;
- strengthening and exit triggers.

These are planning candidates, not an approved schema.

## Open decisions

1. What exact ids, schema fields, and retirement/version rules represent bindings?
2. Which initial relation and alias catalog is small enough to defend with evidence?
3. What minimum observable evidence creates each candidate binding?
4. How will Project Profile present and confirm choices without self-selection?
5. Which policy/capability adapters may enforce confirmed constraints, at what stage?
6. Which pilot hosts will test mixed entrypoints, nested scopes, and alias expansion?

## Rule placement

- Rule: use a project base plus scoped unit overlays for Layer 2 composition.
- Scope: framework-global
- Primary record: `.lazy-harness/planning/cross-stack-architecture-profiles.md`
- Why not AGENTS.md: this is architecture model design, not immediate grammar.
- Why not local notes: the model is shared framework knowledge.
- Confirmation: user-confirmed composition, axes, normalized values, scope bindings,
  relation graph, transparent versioned aliases, and observe-confirm-enforce lifecycle
  on 2026-07-13.

## Discovery capture

- DDD: candidate vocabulary for `project base`, `unit`, `overlay`, and profile
  relationships.
- SDD: candidate profile schema and Project Profile selection contract.
- BDD: candidate mixed-host discovery and confirmation flow.
- TDD: future compatibility, conflict, and mixed-unit fixtures.
- ADR: ADR 0054 adopts the composition model; schema and implementation remain open.
- SSOT: profile catalog ownership and versioning remain undecided.
- Planning: this record is the primary Layer 2 composition baseline.
