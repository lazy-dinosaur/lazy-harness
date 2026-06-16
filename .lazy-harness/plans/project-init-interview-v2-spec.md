# Project Init Interview V2 Spec

Date: 2026-06-16
Status: draft design; no runtime implementation yet
Layer: Planning
Related SDD: `.lazy-harness/spec/platform/project-profile-v2.md`
Related V1: `.lazy-harness/plans/project-init-interview-spec.md`, `.lazy-harness/spec/platform/project-profile.md`
Related Project Map: `.lazy-harness/spec/platform/project-map-v2.md`, `.lazy-harness/ssot/project-map-taxonomy.md`
Related TDD: `.lazy-harness/tests/project-profile-v2.md`

## Purpose

Project Init Interview V2 is the structured entry point for building a project map and discovering project/team policies.

It should ask enough to seed the project atlas, but it must not turn into a one-time wizard that freezes decisions forever.

## Principles

1. **Project understanding first** — interview answers become Project Map cluster candidates.
2. **Policy discovery, not universal defaults** — project/team rules are discovered, confirmed, evolved, promoted, or demoted.
3. **No silent defaults** — unknown means unknown, not guessed.
4. **Stage-aware behavior** — policies may differ between turn, edit, commit, push, release, and high-risk mutation.
5. **Pi-primary adapter** — output should be consumable by Pi first, Jcode as compatibility.
6. **Candidate before canonical** — unconfirmed answers stay candidates or open questions.
7. **Not test-centric** — testing is one policy dimension among many.

## Interview flow

```text
inspect existing project/profile/doc evidence
→ present missing/uncertain areas
→ ask grouped questions
→ produce Project Map seed candidates
→ produce policy/capability candidates
→ record unresolved ambiguities
→ write only confirmed answers
→ leave reviewable plan for remaining gaps
```

## Question group details

### 1. Project purpose

Ask:

- What is this project for?
- Who uses it?
- What quality attributes matter most?
- What constraints must not be compromised?

Seed branches:

- `facts` / Project
- `expectations` / BDD
- `ownership` / SSOT when constraints imply source of truth

### 2. Stack and platform

Ask:

- Runtime/language/framework/package manager?
- Deployment/runtime target?
- External managed services?

Seed branches:

- `contracts` / SDD
- `ownership` / SSOT
- `source-links` / Source

### 3. Source ownership and filesystem

Ask:

- Where is source, test, config, generated, and runtime data?
- What areas are forbidden or high-risk for agents?
- Which upstream/downstream repos/services own truth?

Seed branches:

- `ownership` / SSOT
- `source-links` / Source
- `policies` / Policy for edit boundaries

### 4. System design

Ask:

- Architecture style?
- Module/boundary rules?
- Where should business logic live?
- What design changes require ADR?

Seed branches:

- `contracts` / SDD
- `decisions` / ADR
- `policies` / Policy

### 5. Domain vocabulary and invariants

Ask:

- What domain terms must be used consistently?
- What IDs/ownership rules matter?
- What invariants must not be violated?

Seed branches:

- `facts` / DDD
- `ownership` / SSOT
- `validation` / TDD when invariants need tests

### 6. Frontend/design system/accessibility

Ask:

- Existing design system or Figma source?
- Component organization policy?
- Accessibility baseline?
- Visual regression expectation?

Seed branches:

- `expectations` / BDD
- `contracts` / SDD
- `validation` / TDD
- `policies` / Policy

### 7. Backend/data/security

Ask:

- API style?
- Persistence boundary?
- Migration policy?
- Auth/authz/privacy/compliance boundaries?

Seed branches:

- `contracts` / SDD
- `ownership` / SSOT
- `validation` / TDD
- `policies` / Policy

### 8. Validation/testing policy

Ask:

- Focused tests during normal turn?
- Commit checks?
- Push checks?
- Release checks?
- Allowed deferrals?

Seed branches:

- `validation` / TDD
- `policies` / Policy

### 9. Workflow/review/release policy

Ask:

- Commit message style?
- Branch/PR/review expectations?
- Release/deploy confirmation boundary?

Seed branches:

- `policies` / Policy
- `decisions` / ADR when trade-offs are durable

### 10. Dependency and tool policy

Ask:

- Can agents add dependencies?
- What needs review?
- What package managers are authoritative?

Seed branches:

- `policies` / Policy
- `ownership` / SSOT
- `contracts` / SDD

### 11. Documentation/record policy

Ask:

- What changes require records/docs?
- Where do project rules live?
- What must be updated before commit/push?

Seed branches:

- `policies` / Policy
- `ownership` / SSOT

### 12. Human confirmation and autonomy

Ask:

- What can the agent do autonomously?
- What always needs confirmation?
- What actions are destructive or irreversible?

Seed branches:

- `policies` / Policy
- `ownership` / SSOT

## Output model

The dry-run output should match `.lazy-harness/fixtures/project-profile-v2/interview-output.json`.

It contains:

- adapter boundary
- question groups
- project-map seed candidates
- policy candidates
- unresolved ambiguities
- proposed writes
- no-silent-defaults declaration

## Review gate before implementation

This V2 spec is only the design draft. Before runtime changes:

1. User reviews question groups.
2. User reviews output packet shape.
3. User confirms whether Project Interview V2 should be added as a new mode or evolve existing `interview` mode.
4. User confirms whether initial policy candidates are written to `.lazy-harness/rules/**`, `capabilities.json`, or held as Project Map candidates until Phase 3.

## Rule placement

- Rule: Project Init Interview V2 should discover project-map cluster seeds and stage-aware project/team policy candidates across many dimensions, not only testing.
- Scope: framework-global
- Primary record: `.lazy-harness/plans/project-init-interview-v2-spec.md`
- Why not AGENTS.md: this is a design plan for interview behavior, not prompt grammar.
- Why not `.jcode`: Project Interview V2 is Pi-primary and agent-neutral.
- Confirmation: user-approved Phase 2 design draft; no runtime implementation approval yet.

## Discovery capture

- DDD: candidate domain vocabulary/invariants question groups.
- BDD: candidate project expectations/workflow behavior question groups.
- SDD: candidate Project Profile V2 output contract.
- TDD: candidate validation/testing and future fixture tests.
- ADR: future ADR needed for replacing V1 behavior.
- SSOT: candidate ownership/source-of-truth question groups.
- Planning: updated by this V2 interview plan.
