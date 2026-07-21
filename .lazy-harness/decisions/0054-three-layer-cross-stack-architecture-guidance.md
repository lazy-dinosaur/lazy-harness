# ADR 0054 — Three-Layer Cross-Stack Architecture Guidance

Status: accepted
Date: 2026-07-13
Updated: 2026-07-20
Layer: ADR
Related Layer 1: `.lazy-harness/planning/cross-stack-architecture-guidance.md`
Related Layer 2: `.lazy-harness/planning/cross-stack-architecture-profiles.md`
Related Layer 3: `.lazy-harness/planning/cross-stack-architecture-host-mapping.md`
Related direction: `.lazy-harness/planning/lazy-harness-v2-direction-purpose.md`
Related baseline evidence: `.lazy-harness/evidence/2026-07-13-cross-stack-architecture-planning-baseline.md`
Related pilot evidence: `.lazy-harness/evidence/2026-07-14-cross-stack-architecture-pilot-validation.md`

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
  - extend the approved core+skill pilot into inferred architecture, application-source refactors, or enforcement
  - treat local code organization, source ordering, or extraction advice as Host Architecture Map truth
- Record completion:
  - changes to the three-layer architecture require this ADR or a superseding ADR
  - bounded catalog/schema/CLI/Project Profile/skill changes update the linked DDD/SDD/BDD/TDD/SSOT records, fixtures, manifests, graph facts, and evidence together
  - host source-refactor or enforcement work requires separate scope, evidence, and execution approval
- Related records:
  - `.lazy-harness/planning/cross-stack-architecture-guidance.md`
  - `.lazy-harness/planning/cross-stack-architecture-profiles.md`
  - `.lazy-harness/planning/cross-stack-architecture-host-mapping.md`
  - `.lazy-harness/spec/platform/project-profile-v2.md`
  - `.lazy-harness/spec/platform/policy-machinery-v2.md`
  - `.lazy-harness/spec/platform/code-organization-profile.md`
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
- Portable evidence adapters and downstream mixed-host use remain unproven.

### Neutral

- Existing Project Profile V1 behavior remains unchanged; V2 gains only an explicit candidate-only architecture input and defaults to no candidates.
- Existing policies and capabilities keep their current semantics and levels.
- No host folder structure, runtime, or deployment topology changes automatically.

## 2026-07-20 amendment — Code Organization Profile is a separate track

The user selected a Goedamjip-derived Code Organization Profile while explicitly keeping business/domain/system architecture outside that profile. The two tracks may share words such as ownership, cohesion, and lifecycle, but they own different facts:

- this ADR and the Host Architecture Map own topology, scoped architecture bindings, boundaries, contracts, and confirmed host architecture truth;
- `.lazy-harness/spec/platform/code-organization-profile.md` owns local source discoverability, chronological coherence, narrowing ownership paths, lifecycle vocabulary, and extraction timing;
- a code-organization observation cannot select a Layer 2 profile, infer a named architecture, or confirm a host map;
- Profile v1 is changed-source-only and observe/recommend level. Warnings, hard stops, AST rules, and bulk rewrites require later independent approval.

Goedamjip remains read-only supporting evidence, not a folder or implementation oracle. The profile preserves useful local organization principles without making its current tree, framework, or legacy choices canonical.

## Approved bounded pilot amendment

The original 2026-07-13 decision adopted only the three-layer model and deliberately
withheld schema, writer, adapter, and enforcement approval. On 2026-07-14 the user
separately approved a bounded **core + Pi/OMP skill pilot**.

The pilot approves:

- the framework-owned profile catalog and two architecture schemas;
- the host-owned `.lazy-harness/project/architecture-map.json` canonical path;
- stable value, scope, binding, alias, relation, and confirmation grammar;
- read-only `lazy architecture inspect|plan`;
- exact-digest, confirmation-referenced, validate-then-atomic `apply`;
- a candidate-only Project Profile V2 adapter and delegated promotion target;
- framework fixtures, self-tests, Category A distribution metadata, and graph links;
- the approval-gated `lazy-architecture-refactor` Pi/OMP package skill.

The pilot still does **not** approve:

- architecture inference or automatic candidate confirmation from source/folder evidence;
- application-source or host-folder refactoring under this framework work unit;
- portable evidence-adapter enforcement beyond the approved validation surfaces;
- new policies, capabilities, warning behavior, or hard stops;
- bulk graph migration or cleanup of the pending legacy rows;
- npm publication; source-path Pi/OMP validation remains the distribution path;
- downstream canary application-source edits or shared-host sync before its own safety gate.

Every Host Architecture Map apply still requires an exact plan digest and explicit
confirmation reference. Map confirmation does not authorize a source-refactor batch;
the skill requires a separate option gate for one independently reviewable seam.

## Remaining follow-up decision gates

1. Approve any real-host architecture candidate and map composition separately.
2. Select and approve one host source-refactor seam, if desired, after map confirmation.
3. Define additional portable evidence adapters only from pilot evidence.
4. Define profile retirement, supersession, and waiver review lifecycle.
5. Approve policy/capability enforcement, if ever warranted, as an independent slice.
6. Approve downstream canary sync only after source validation and host safety evidence.

## Implementation map

- Status: `core+skill pilot source-validated; rollout pending`
- Primary records:
  - `.lazy-harness/decisions/0054-three-layer-cross-stack-architecture-guidance.md`
  - `.lazy-harness/domain/architecture-guidance.md`
  - `.lazy-harness/spec/platform/architecture-guidance.md`
  - `.lazy-harness/spec/platform/code-organization-profile.md`
  - `.lazy-harness/behavior/architecture-refactor-flow.md`
  - `.lazy-harness/tests/architecture-guidance.md`
  - `.lazy-harness/tests/code-organization-profile.md`
  - `.lazy-harness/ssot/architecture-guidance-storage.md`
- Core implementation:
  - `.lazy-harness/ssot/architecture-profile-catalog.json`
  - `.lazy-harness/schemas/architecture-profile-catalog.schema.json`
  - `.lazy-harness/schemas/host-architecture-map.schema.json`
  - `.lazy-harness/scripts/architecture-profile-core.ts`
  - `.lazy-harness/scripts/architecture-profile.ts`
  - `.lazy-harness/scripts/project-profile-architecture.ts`
  - `.lazy-harness/scripts/project-profile.ts`
  - `.lazy-harness/bin/lazy`
- Skill and distribution:
  - `packages/lazy-harness-pi/skills/lazy-architecture-refactor/SKILL.md`
  - `packages/lazy-harness-pi/skills/lazy-project-profile/SKILL.md`
  - `.lazy-harness/manifests/init-categories.json`
  - `.lazy-harness/manifests/skills.xml`
- Protection:
  - `.lazy-harness/fixtures/architecture-guidance/**`
  - `.lazy-harness/scripts/self-test.py#check_architecture_guidance_cli`
  - `.lazy-harness/evidence/2026-07-14-cross-stack-architecture-pilot-validation.md`
  - `.lazy-harness/tests/project-profile-v2.md`
  - `.lazy-harness/tests/pi-agent-package.md`
- Runtime/host boundary: no canonical map exists in the source repository and no application source is refactored by this pilot.

## Rule placement

- Rule: guide architecture through inherited cross-stack principles, normalized
  scoped profiles, and confirmed host mappings with separated checks/policies.
- Scope: framework-global
- Primary record: `.lazy-harness/decisions/0054-three-layer-cross-stack-architecture-guidance.md`
- Why not AGENTS.md: this is an architecture decision; AGENTS should carry only a
  compact retrieval or execution pointer after an implementation is approved.
- Why not local notes: the decision is shared framework knowledge.
- Confirmation: the user selected the three-layer planning baseline and formal ADR on
  2026-07-13, then explicitly approved the bounded core+skill pilot, source-path
  Pi/OMP validation, and later safety-gated canary rollout on 2026-07-14.

## Discovery capture

- DDD: architecture vocabulary and identity invariants are owned by `.lazy-harness/domain/architecture-guidance.md`.
- SDD: architecture CLI/schema/adapter contract implemented in the linked SDD.
- BDD: separate map and source-refactor approval gates implemented in the skill flow.
- TDD: architecture, Project Profile, package, and sync-preservation coverage implemented.
- ADR: this amendment records the separately approved bounded pilot without approving enforcement.
- SSOT: catalog/schema ownership and the host-owned map path are confirmed.
- Planning: remaining real-host refactor, enforcement, canary, and legacy graph migration work stays deferred.
