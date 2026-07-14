# ADR 0054 — Three-Layer Cross-Stack Architecture Guidance

Status: accepted
Date: 2026-07-13
Layer: ADR
Related Layer 1: `.lazy-harness/planning/cross-stack-architecture-guidance.md`
Related Layer 2: `.lazy-harness/planning/cross-stack-architecture-profiles.md`
Related Layer 3: `.lazy-harness/planning/cross-stack-architecture-host-mapping.md`
Related direction: `.lazy-harness/planning/lazy-harness-v2-direction-purpose.md`
Related evidence: `.lazy-harness/evidence/2026-07-13-cross-stack-architecture-planning-baseline.md`

## Rule digest

- Status: active
- Layer: ADR
- Scope: framework-global
- Confidence: medium
- Aliases:
  - cross-stack architecture baseline
  - architecture profile composition
  - Host Architecture Map
  - three-layer architecture guidance
  - 3층 아키텍처 규격
  - 범용 아키텍처 원칙
- Surface terms:
  - frontend backend CLI worker monorepo multi-service
  - FSD vertical slice Hexagonal modular monolith DDD
  - 프론트엔드 백엔드 워커 모노레포 멀티서비스
- Applies when:
  - defining how Lazy-Harness guides code or system architecture across hosts
  - deciding whether a rule is universal, profile-specific, or host-specific
  - mapping a named architecture method into portable semantics
  - connecting host architecture truth to checks or policy enforcement
- Must:
  - inherit the six Layer 1 principles for every host and profile
  - compose Layer 2 from one project base and scoped bindings across four axes
  - represent named methods as transparent versioned aliases over normalized values
  - keep profile selection scoped, relation-aware, and observe-confirm-enforce
  - map confirmed host composition through one Host Architecture Map
  - give each constraint one semantic owner and separate truth, check, and policy
  - record intentional host deviations as scoped waivers
- Must not:
  - make FSD, Clean, Hexagonal, DDD, microservices, or a folder taxonomy universal
  - infer or confirm a profile silently from paths, frameworks, or source evidence
  - mirror one constraint body across the host map and multiple layer records
  - let generated indexes, check output, or policy levels become architecture truth
  - treat this ADR as schema, validator, scaffold, or enforcement approval
- Record completion:
  - changes to the three-layer architecture require this ADR or a superseding ADR
  - schema/storage work requires explicit SSOT, SDD, TDD, and execution approval
  - enforcement work requires evidence, policy/capability approval, and rollback
- Related records:
  - `.lazy-harness/planning/cross-stack-architecture-guidance.md`
  - `.lazy-harness/planning/cross-stack-architecture-profiles.md`
  - `.lazy-harness/planning/cross-stack-architecture-host-mapping.md`
  - `.lazy-harness/spec/platform/project-profile-v2.md`
  - `.lazy-harness/spec/platform/policy-machinery-v2.md`
  - `.lazy-harness/ssot/rule-sources.md`

## Context

Lazy-Harness Project Profile can ask about system design, source ownership,
frontend, backend/data, dependencies, and validation. It did not have a portable
model that distinguishes:

1. principles that survive frontend, backend, CLI/worker, monorepo, and
   multi-service counterexamples;
2. conditional architecture mechanisms that apply only to certain runtimes or
   responsibility scopes;
3. confirmed host mappings, exceptions, evidence, and enforcement choices.

Using one named architecture as the framework default would overfit its original
stack. Keeping every project free-form would preserve flexibility but make
comparison, evaluation, and executable evidence inconsistent. Putting architecture
truth directly in policies would conflate what the system is with how strongly an
agent should be steered.

The planning investigation used Goedamjip and Feature-Sliced Design as one
frontend evidence track, then balanced it with backend, CLI/worker, monorepo, and
multi-service evidence. The user confirmed the complete planning baseline on
2026-07-13 and then separately approved formalizing it as an ADR.

## Decision

Adopt a **three-layer cross-stack architecture guidance model**.

### Layer 1 — inherited cross-stack principles

Every host inherits six principles. They are not selectable profiles:

1. `ARCH-L1-01` — declared boundary, owner, and contract;
2. `ARCH-L1-02` — cohesion and responsibility-directed composition;
3. `ARCH-L1-03` — explicit boundary data and outcomes;
4. `ARCH-L1-04` — owned effects and lifecycles;
5. `ARCH-L1-05` — authoritative mutable-state ownership;
6. `ARCH-L1-06` — executable, proportional architecture rules.

The detailed applicability, counterexamples, and evidence surfaces remain in the
Layer 1 planning baseline. A future wording change that alters semantics requires
an ADR amendment or supersession.

### Layer 2 — normalized, scoped profile composition

A project uses one base descriptor set plus scoped unit bindings across four axes:

1. **Project base** — observable topology and ownership facts;
2. **Runtime/workload** — invocation and lifetime per entrypoint;
3. **Internal organization** — responsibility placement per declared scope;
4. **Operational/boundary** — condition-activated overlays.

Cardinality is scope-based:

- one active project-base descriptor set per host;
- one runtime value per entrypoint, with multiple entrypoints allowed per unit;
- one primary organization value per declared responsibility scope;
- zero-to-many operational overlays where their conditions exist.

Composition uses scope-aware `requires`, `compatibleWith`, `conflictsWith`, and
`strengthens` relations. An undocumented combination is unknown, not silently
compatible.

FSD, Vertical Slice, modular monolith, Hexagonal/Clean/Onion, tactical DDD, and
similar names may be transparent versioned aliases. Every alias must expand into
normalized bindings and relations without hidden semantics. Folder names and
framework names remain host mappings, not portable profile truth.

### Layer 3 — confirmed host architecture mapping

Each host has one conceptual **Host Architecture Map** that owns composition and
provenance facts:

- confirmed profile bindings and scopes;
- topology, entrypoint, organization, and operational composition;
- alias/version and activation evidence references;
- links to semantic-owner records, waivers, checks, policies, and capabilities;
- reconsideration, retirement, and supersession triggers.

The map does not own every constraint body. Each constraint has one canonical
semantic owner:

- DDD for business vocabulary and invariants;
- SDD for API, component, data, IPC, dependency, and boundary contracts;
- BDD for user-visible behavior;
- TDD for regression and protection expectations;
- ADR for architecture choices and trade-offs;
- SSOT for host identity, ownership, and source-of-truth boundaries;
- typed policies for repeated agent/team behavior, with capabilities only for
  action steering.

Other records and generated views link to that owner instead of mirroring prose.

### Truth, check, and policy remain separate

- **Canonical truth** owns the confirmed binding, scope, and constraint meaning.
- **Evidence adapters** produce reproducible observations or validation output.
- **Policies/capabilities** own stage, steering level, action, bypass, and rollback.

A failed check is drift evidence; it cannot rewrite the architecture choice. A
confirmed constraint may have no executable adapter. `default`, `warn`, or
`block` requires separate policy/capability approval and evidence.

### Observe, confirm, enforce

Architecture discovery follows three distinct states:

1. source or record evidence may create a `candidate` with no authority;
2. a user or authorized team may promote it to `confirmed` host truth;
3. separately approved policy/capability work may make it `enforced`.

Observation never confirms silently. Confirmation never activates warning or
blocking behavior implicitly.

### Scoped waivers

An intentional deviation is a scoped waiver, not an alias mutation or unexplained
override. It identifies the constraint and scope, owner, approving authority,
rationale, compensating evidence or controls, and an expiry or review trigger.
Repeated waivers may inform a future profile revision but cannot promote one.

## Alternatives considered

### One universal named architecture

Rejected. FSD, Hexagonal, Clean, DDD, modular monolith, and microservices have
valuable but conditional mechanisms. None survives every project type and scale
without false ceremony or missing runtime semantics.

### Stack-specific convention packs as the primary model

Rejected as the canonical layer. Packs can improve onboarding but tend to mix
framework names, folders, runtime facts, and architecture meaning. Transparent
aliases over normalized values preserve portability and explainability.

### Host-only free-form architecture records

Rejected as the only model. They preserve local accuracy but cannot provide a
cross-project evaluation vocabulary, compatibility model, or reusable evidence
adapters.

### Policy registry as the architecture source of truth

Rejected. Policies answer how agents should behave at a lifecycle stage. They do
not own topology, contracts, state authority, or the host's architecture choice.

### Folder taxonomy as the portable contract

Rejected. Observable ownership, dependencies, contracts, effects, and lifecycle
semantics are stronger evidence than directory names. Folder mappings remain
Layer 3 host choices.

## Consequences

### Positive

- One framework model spans frontend, backend, CLI/worker, monorepo, and services.
- Small or thin units can remain proportional without weakening universal rules.
- Named methods remain useful onboarding surfaces without becoming hidden truth.
- Mixed hosts can apply different organization and runtime bindings by scope.
- Architecture truth remains stable when checks or enforcement levels change.
- Waivers are reviewable and can become evidence for profile evolution.

### Costs and risks

- The model adds vocabulary, scope identity, relation, version, and provenance work.
- Alias quality depends on complete, reviewable expansion.
- Unknown combinations require human decisions until catalog evidence grows.
- One semantic owner requires disciplined links and duplicate control.
- Portable evidence adapters and pilot coverage are still unproven.

### Neutral

- Existing Project Profile V1/V2 behavior is unchanged by this ADR.
- Existing policies and capabilities keep their current semantics and levels.
- No host folder structure, runtime, or deployment topology changes automatically.

## Explicit non-approval boundary

This ADR adopts the architecture model only. It does not approve:

- a profile catalog schema or storage path;
- a Host Architecture Map filename, schema, or writer;
- stable id or scope-selector syntax;
- alias and relation registries;
- Project Profile packet or promotion-writer changes;
- dependency, AST, API, runtime, or repository validators;
- scaffolding or host source edits;
- new policies, capabilities, warnings, or hard stops;
- Category A sync or Medivance sample cleanup.

Each implementation slice requires its own requirements, plan, approval, records,
fixtures, and validation evidence.

## Follow-up decision gates

1. Select canonical paths and schemas for profile catalogs, bindings, and waivers.
2. Define stable ids, scope selectors, relation validation, and version lifecycle.
3. Specify Project Profile candidate, confirmation, promotion, and failure behavior.
4. Select a minimal portable evidence-adapter set and mixed-host pilot matrix.
5. Define drift, retirement, supersession, and waiver review behavior.
6. Approve implementation and enforcement slices independently.

## Implementation map

- Status: `decision-only; no implementation approved`
- Primary records:
  - `.lazy-harness/decisions/0054-three-layer-cross-stack-architecture-guidance.md`
  - `.lazy-harness/planning/cross-stack-architecture-guidance.md`
  - `.lazy-harness/planning/cross-stack-architecture-profiles.md`
  - `.lazy-harness/planning/cross-stack-architecture-host-mapping.md`
- Evidence:
  - `.lazy-harness/evidence/2026-07-13-cross-stack-architecture-planning-baseline.md`
- Source files changed by this decision: none.
- Runtime or host changes: none.
- Future protection: SDD/TDD contracts and pilot evidence require separate approval.

## Rule placement

- Rule: guide architecture through inherited cross-stack principles, normalized
  scoped profiles, and confirmed host mappings with separated checks/policies.
- Scope: framework-global
- Primary record: `.lazy-harness/decisions/0054-three-layer-cross-stack-architecture-guidance.md`
- Why not AGENTS.md: this is an architecture decision; AGENTS should carry only a
  compact retrieval or execution pointer after an implementation is approved.
- Why not local notes: the decision is shared framework knowledge.
- Confirmation: the user selected the three-layer planning baseline on 2026-07-13
  and explicitly selected formal ADR progress in the current work unit.

## Discovery capture

- DDD: no independent promoted record; vocabulary remains linked planning input.
- SDD: no contract implementation approved; follow-up schema/flow SDD is required.
- BDD: no user-visible runtime flow changed.
- TDD: no implementation regression exists; future composition and pilot fixtures
  are required before implementation closure.
- ADR: this record is the primary architecture decision.
- SSOT: catalog, Host Architecture Map, id, scope, and waiver storage remain open.
- Planning: the three planning records remain detailed design and evidence inputs.
