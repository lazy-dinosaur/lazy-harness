# Cross-Stack Architecture Guidance — Layer 1 Baseline

Status: active
Date: 2026-07-13
Layer: Planning
Related direction: `.lazy-harness/planning/lazy-harness-v2-direction-purpose.md`
Related profile contract: `.lazy-harness/spec/platform/project-profile-v2.md`
Related record format: `.lazy-harness/spec/platform/record-digest-format.md`
Related Layer 2: `.lazy-harness/planning/cross-stack-architecture-profiles.md`
Related Layer 3: `.lazy-harness/planning/cross-stack-architecture-host-mapping.md`
Related evidence: `.lazy-harness/evidence/2026-07-13-cross-stack-architecture-planning-baseline.md`
Related ADR: `.lazy-harness/decisions/0054-three-layer-cross-stack-architecture-guidance.md`

## Rule digest

- Status: active
- Layer: Planning
- Scope: framework-global
- Confidence: medium
- Aliases:
  - cross-stack architecture
  - architecture principles
  - three-layer architecture guidance
  - 범용 아키텍처 원칙
  - 코드 구조화 원칙
- Surface terms:
  - frontend backend CLI worker monorepo multi-service
  - 프론트엔드 백엔드 워커 모노레포 멀티서비스
- Applies when:
  - evaluating how Lazy-Harness should guide code structure or system design
  - deciding whether a convention is universal, profile-specific, or
    host-specific
  - designing frontend, backend, CLI, worker, monorepo, or multi-service
    profiles
- Must:
  - use the six confirmed Layer 1 principles as the cross-stack baseline
  - keep named architectures in transparent Layer 2 aliases and folder mappings
    in Layer 3
  - state applicability, exceptions, and executable evidence for material
    rules
- Must not:
  - make FSD or any backend architecture the universal default
  - promote slogans or diagrams as enforced guarantees without observable
    checks
- Record completion:
  - confirmed Layer 2 and Layer 3 decisions live in their dedicated planning records
  - schema or enforcement changes require ADR, SDD, TDD, and explicit approval
- Related records:
  - `.lazy-harness/planning/lazy-harness-v2-direction-purpose.md`
  - `.lazy-harness/spec/platform/project-profile-v2.md`
  - `.lazy-harness/spec/platform/project-profile.md`
  - `.lazy-harness/planning/cross-stack-architecture-profiles.md`
  - `.lazy-harness/planning/cross-stack-architecture-host-mapping.md`
  - `.lazy-harness/evidence/2026-07-13-cross-stack-architecture-planning-baseline.md`
  - `.lazy-harness/decisions/0054-three-layer-cross-stack-architecture-guidance.md`

## Confirmed decision

The user confirmed the following direction on 2026-07-13:

1. Lazy-Harness architecture guidance covers frontend applications, backend
   services, CLI/worker runtimes, monorepos, and multi-service systems.
2. Goedamjip and Feature-Sliced Design form one frontend evidence track.
   They are neither the center nor the default.
3. The guidance uses cross-stack invariants, selectable profiles, and
   confirmed host overlays.
4. Layer 1 uses the six-principle minimum set below instead of a fixed
   taxonomy or a larger checklist.

This confirmation approves the research baseline. It does not approve schemas,
scaffolding, validators, policies, capabilities, or hook enforcement.

## Three-layer planning baseline approval

On 2026-07-13 the user selected **3층 baseline 확정** as the final planning
decision. The baseline consists of:

1. this record for the six cross-stack Layer 1 principles;
2. `.lazy-harness/planning/cross-stack-architecture-profiles.md` for normalized,
   scoped, composable Layer 2 profiles;
3. `.lazy-harness/planning/cross-stack-architecture-host-mapping.md` for the
   Layer 3 Host Architecture Map, semantic owners, checks/policies, and waivers.

ADR 0054 now formalizes this research/design baseline. It still does not approve
schemas, storage paths, SDD/TDD contracts, implementation, or enforcement; each
follow-up slice requires its own plan and execution approval.

## Evaluation standard

A candidate belongs in Layer 1 only when it:

- recurs across frontend, backend, CLI/worker, and package/service evidence;
- can be phrased without a framework, language, or folder name;
- names conditional applicability instead of assuming identical complexity;
- can identify an owner, contract, violation, or evidence surface;
- survives small-project and thin-adapter counterexamples;
- leaves mechanisms to Layer 2 profiles and Layer 3 host choices.

## Evidence tracks

### Goedamjip

Supports validated ingress, explicit workflow state, lifecycle ownership,
failure semantics, and boundary-drift counterexamples.

It cannot establish a positive reference architecture because it has no
tracked behavioral tests or CI.

### Feature-Sliced Design

Supports cohesion, directed dependencies, peer isolation, public contracts,
and broader-owner composition.

It cannot establish backend, worker, data, deployment, or distributed-system
rules.

### Backend architecture

Supports capability boundaries, module/data ownership, consistency boundaries,
and proportional use of ports or domain patterns.

It cannot establish one universal named architecture or folder layout.

### CLI and worker runtimes

Support effect ownership, cancellation, acknowledgement, scoped
retry/idempotency behavior, and process contracts.

They cannot establish universal retry or exactly-once defaults.

### Monorepos and multi-service systems

Support package visibility, contract evolution, generated provenance, and
deployment-unit isolation.

They cannot establish a one-to-one mapping among package, service, process,
and deployment.

Research artifacts:

- `/tmp/lazy-architecture-principles/goedamjip.md`
- `/tmp/lazy-architecture-principles/fsd.md`
- `/tmp/lazy-architecture-principles/backend.md`
- `/tmp/lazy-architecture-principles/runtime-multiproject.md`
- `/tmp/lazy-architecture-principles/synthesis-review.md`

These `/tmp` artifacts are supporting evidence, not canonical records.

## Layer 1 — six confirmed principles

### ARCH-L1-01 — Declared boundary, owner, and contract

Every boundary consumed outside its owning unit declares:

- the accountable owner;
- the public surface;
- permitted dependency or effect directions;
- the exception path;
- the evidence that detects material bypass.

This applies when another module, package, process, service, team, plugin,
script, or external client consumes the unit.

It does not require a fixed folder name, one interface per class, a barrel
file, a network API, or independent deployment.

### ARCH-L1-02 — Cohesion and responsibility-directed composition

Keep code and data that change for one responsibility locally discoverable.
Coordinate independent responsibilities at the narrowest unit that owns the
broader workflow. Merge fictional boundaries that always change together
before adding shared abstractions.

This applies when the host has more than one non-trivial responsibility or
repeated cross-boundary change.

It does not prescribe FSD layers, vertical slices, horizontal layers,
components, or bounded-context granularity.

### ARCH-L1-03 — Boundary data and outcomes are explicit

Validate untrusted, persisted, generated, or independently evolving input
before core traversal. Distinguish outcomes that can materially differ, such
as success, absence, invalid input, authorization failure,
cancellation/deadline, and operational failure. Published boundaries state
compatibility or migration behavior.

This applies when data crosses a trust, persistence, process, team, or
independent-release boundary.

It does not require DTO layers or duplicate representations for every private
in-process call.

### ARCH-L1-04 — Owned effects and lifecycles

Every acquired resource or externally visible effect has an owner, a
completion or commit point, and interruption/cleanup behavior. Spawned work is
joined, supervised, or explicitly detached under an owner.

This applies to timers, listeners, I/O, transactions, files, subprocesses,
leases, messages, external calls, animation/media handles, and long-running
work.

Worker/service overlays additionally define acknowledgement, retryability,
idempotency scope, deadline, deduplication/compensation, and
drain/hard-stop behavior when relevant.

It does not require a pure domain core for thin proxies or transformations
with no meaningful decision logic.

### ARCH-L1-05 — Authoritative mutable-state ownership

When mutable or persistent state crosses a boundary, identify its
authoritative writer and the scope in which invariants are atomic.
Cross-boundary workflows state consistency, freshness, compensation, or
reconciliation behavior.

This applies when multiple owners can observe or mutate shared state, or one
workflow spans transaction or consistency boundaries.

Record mappings among code module, bounded context, package, schema, process,
service, and deployment. Do not assume those boundaries are one-to-one.

It does not require one database per module/service or one service per bounded
context.

### ARCH-L1-06 — Executable, proportional architecture rules

A rule promoted beyond advice names a violation that tooling or tests can
observe. Enforcement strength is proportional to exposure, longevity, team
count, operational risk, and failure cost. Exceptions identify scope, owner,
rationale, evidence, and a review trigger.

This applies whenever the project claims a dependency, boundary,
compatibility, lifecycle, ownership, or consistency guarantee.

Evidence may use compiler/module visibility, dependency lint, package exports,
database permissions, schema compatibility, contract/integration tests, or CI
checks.

It does not require maximum isolation or ceremony for prototypes, small CRUD
hosts, or one-shot utilities.

## Excluded from Layer 1

The following are profile mechanisms or host choices:

- FSD `app/pages/widgets/features/entities/shared` layers;
- mandatory Clean, Onion, Hexagonal, or controller/service/repository rings;
- tactical DDD, aggregates, repositories, CQRS, or domain events everywhere;
- microservices, one database per service, or one context per service;
- universal retries, exactly-once claims, outbox, saga, or DLQ defaults;
- universal barrels, DI frameworks, or interface-per-class rules;
- one package equals one service equals one deployment;
- fixed CLI flags, queue limits, retry budgets, versioning, or directories.

## Layer 2 profile activation cues

- **Browser UI, SSR/hydration, animation, or media**
  - Consider semantic UI/accessibility, browser lifecycle, asset degradation,
    and an optional FSD-inspired profile.
- **Small CRUD backend or thin CLI**
  - Consider feature/use-case locality, explicit external schemas/outcomes,
    direct adapters, and selective ports.
- **Complex invariant-rich domain**
  - Consider strategic DDD, selective aggregates/repositories, and
    domain-independent infrastructure ports.
- **Modular monolith**
  - Consider capability APIs, module dependency rules, write ownership, and an
    internal profile choice per module.
- **Long-running worker or event consumer**
  - Consider acknowledgement, idempotency identity, bounded retries/deadlines,
    poison handling, drain, and reconciliation.
- **Multi-package monorepo**
  - Consider a target graph, visibility/exports, generated provenance, and a
    package release mode.
- **Independently deployed services**
  - Consider contract compatibility, deployment isolation, observability,
    state ownership, and remote-failure/consistency policy.

Confirmed Layer 2 values and composition rules live in
`.lazy-harness/planning/cross-stack-architecture-profiles.md`.

## Layer 3 host mapping

The confirmed Layer 3 baseline lives in
`.lazy-harness/planning/cross-stack-architecture-host-mapping.md`:

- one Host Architecture Map owns binding composition and provenance;
- each constraint body has one canonical semantic owner;
- truth, evidence adapters, and policy/capability enforcement stay separate;
- intentional deviations use scoped waivers.

The exact map path, schema, writer, and enforcement adapters remain unapproved.

## Current Lazy-Harness gap

Project Profile already asks generic questions about system design, frontend
design, backend/data, source ownership, and dependency policy. The three planning
records now define the missing conceptual bridge:

```text
six Layer 1 principles
→ normalized and composable Layer 2 bindings
→ confirmed Layer 3 host mapping, semantic owners, waivers, checks, and policies
```

The remaining gap is implementation-level: no approved profile catalog schema,
Host Architecture Map schema, promotion transaction, evidence-adapter registry,
or architecture enforcement integration exists.

## Open decisions

1. What schemas and canonical paths store catalogs, bindings, and waivers?
2. What stable ids, scope selectors, version rules, and relation catalogs apply?
3. What evidence adapters and pilot hosts validate the model?
4. How do promotion, partial failure, drift, retirement, and supersession work?
5. Which implementation and enforcement slices receive separate approval?

## Primary sources

The supporting research artifacts preserve full citations and source triage.
Primary evidence includes:

- Feature-Sliced Design official references and v2.1 release notes;
- Cockburn on Hexagonal Architecture;
- Bogard on Vertical Slice Architecture;
- Brown on modular monoliths;
- Fowler on monolith/microservice trade-offs;
- Evans' Domain-Driven Design Reference;
- AWS guidance on safe retries and transactional outbox;
- Apache Kafka delivery semantics;
- Bazel target visibility and Node.js package entry points;
- Semantic Versioning and Kubernetes pod lifecycle.

## Rule placement

- Rule: use the six Layer 1 principles; keep named architectures in profiles.
- Scope: framework-global
- Primary record: `.lazy-harness/planning/cross-stack-architecture-guidance.md`
- Why not AGENTS.md: this is architecture design, not immediate grammar.
- Why not local notes: this is shared framework knowledge.
- Confirmation: the user adopted the linked three-layer model as the final planning
  baseline on 2026-07-13; implementation and enforcement remain unapproved.

## Discovery capture

- DDD: define `boundary`, `owner`, `unit`, `public surface`, and
  `consistency boundary` before schema work.
- SDD: architecture-guidance and Project Profile contracts remain candidates.
- BDD: define profile discovery, proposal, confirmation, and application flow.
- TDD: require cross-profile fixtures and pilot repositories before
  enforcement.
- ADR: ADR 0054 adopts the three-layer model; follow-up implementation decisions remain.
- SSOT: profile taxonomy and host mapping storage remain undecided.
- Planning: this is the primary detailed research baseline.
