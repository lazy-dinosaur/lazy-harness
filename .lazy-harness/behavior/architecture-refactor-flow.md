# BDD — Approval-Batched Architecture Refactor Flow

Status: active-pilot
Date: 2026-07-14
Layer: BDD
Related ADR: `.lazy-harness/decisions/0054-three-layer-cross-stack-architecture-guidance.md`
Related SDD: `.lazy-harness/spec/platform/architecture-guidance.md`
Related TDD: `.lazy-harness/tests/architecture-guidance.md`

## Rule digest

- Status: active
- Layer: BDD
- Scope: framework-global
- Confidence: high
- Aliases:
  - guided architecture refactor
  - approval-batched refactoring
  - 승인형 아키텍처 리팩토링
  - 구조 개선 배치
- Surface terms:
  - inspect candidate option gate plan digest apply refactor batch checkpoint
  - 구조 감사 후보 승인 계획 적용 검증 중단
- Applies when:
  - using `lazy-architecture-refactor` on a host project
  - converting observed architecture evidence into a confirmed host mapping
  - refactoring source toward confirmed architecture constraints
- Must:
  - inspect records and source before proposing a binding or refactor batch
  - keep observations as candidates until an option gate confirms them
  - preview and confirm the exact architecture plan before map writes
  - ask separately before each source refactor batch
  - validate and checkpoint each approved batch
- Must not:
  - infer a named architecture from folders or frameworks
  - edit source while architecture meaning or ownership is unresolved
  - combine unrelated cleanup, graph migration, or enforcement with a batch
  - continue after validation failure or stale approval
- Record completion:
  - flow changes update the skill, SDD, TDD, fixtures, and package contract
- Related records:
  - `.lazy-harness/planning/cross-stack-architecture-guidance.md`
  - `.lazy-harness/planning/cross-stack-architecture-profiles.md`
  - `.lazy-harness/planning/cross-stack-architecture-host-mapping.md`
  - `.lazy-harness/decisions/0038-requirements-first-change-gate.md`

## Scenario 1 — Missing host map remains unclassified

Given a host has no `.lazy-harness/project/architecture-map.json`
When the agent runs `lazy architecture inspect`
Then the result reports a missing confirmed map without error
And it does not select `simple-direct`, FSD, Hexagonal, or another profile
And it offers candidate discovery rather than mutation.

## Scenario 2 — Source evidence creates candidates only

Given records and source show units, entrypoints, dependencies, effects, or ownership
When the skill compares them with the Layer 1 and Layer 2 catalog
Then it may propose scoped architecture candidates with evidence references
But every candidate remains non-authoritative
And conflicting evidence is presented through a 3–5 option gate.

## Scenario 3 — Exact plan confirmation writes host truth

Given the user selected explicit project-base descriptors, scopes, and bindings
When the skill runs `lazy architecture plan --proposal <file>`
Then it shows normalized bindings, alias expansion, findings, baseline digest, and plan
digest without writing files
And only an exact digest plus confirmation reference may authorize apply
And apply writes only the host-owned architecture map atomically.

## Scenario 4 — Project Profile delegates instead of pretending to write

Given an evidence-backed architecture candidate is supplied to Project Profile V2
When queue-v2 routes it and an accepted item is promoted
Then the queue records a host-architecture-map delegation
And Project Profile does not write the host map or semantic-owner records
And the skill must still preview and confirm the architecture plan.

## Scenario 5 — Refactor approval is separate from map confirmation

Given a host map contains confirmed constraints
When the skill finds source drift or a structure improvement
Then it decomposes work into independently reviewable batches
And each batch states files, owner, contract impact, tests, records, rollback, and size
And no source edit occurs until the user selects a batch.

## Scenario 6 — One approved batch is applied and checked

Given the user approved one candidate batch
When the skill edits source and tests with structured edit tools
Then it touches only declared files and required records
And runs focused project validation before broader harness validation
And reports changed files, validation evidence, remaining candidates, and stop reason.

## Scenario 7 — Safety stop preserves state

Given any of these occurs:

- record and code conflict;
- missing profile, scope, ownership, contract, or protecting test;
- new requirement after approval;
- unrelated dirty target overlap;
- failed or unexplained validation;
- CLI/schema/package co-change is incomplete;
- graph or record migration pressure;

When the skill reaches that condition
Then it stops without applying the next batch
And presents a new option gate or explicit blocker
And it never self-selects the previous recommendation.

## Scenario 8 — Canary does not refactor product source

Given the source implementation and package skill pass framework validation
When a downstream canary receives Category A and loads the package
Then the canary verifies catalog/schema/CLI/skill availability and host-map preservation
And it does not refactor application source without separate host approval.

## Scenario 9 — Enforcement remains separate

Given a confirmed binding has validation evidence
When the skill reports conformance or drift
Then it may link checks and evidence
But it does not create `default`, `warn`, or `block` policy/capability behavior
And enforcement requires a separate approved work unit.

## Project Map branch

- Anchor: `cross-stack-architecture-guidance`
- Branch: `expectations`
- Node: `approval-batched-architecture-refactor`
- Primary: `expectations`
- Facets: `BDD`, `Project`
- Edges:
  - `cross-stack-architecture-guidance --has-expectation--> approval-batched-architecture-refactor`
- Related records:
  - `.lazy-harness/spec/platform/architecture-guidance.md`
  - `.lazy-harness/tests/architecture-guidance.md`
  - `.lazy-harness/ssot/architecture-guidance-storage.md`

## Implementation map

- Status: `implemented; source validation passed; rollout pending`
- Primary files:
  - `packages/lazy-harness-pi/skills/lazy-architecture-refactor/SKILL.md`
  - `.lazy-harness/scripts/architecture-profile.ts`
  - `.lazy-harness/scripts/project-profile-architecture.ts`
  - `.lazy-harness/scripts/project-profile.ts`
- Protection:
  - `.lazy-harness/tests/architecture-guidance.md`
  - `.lazy-harness/scripts/self-test.py#check_architecture_guidance_cli`
  - `.lazy-harness/scripts/self-test.py#check_project_profile_v2_runtime`

## Layer completeness impact

- DDD: architecture vocabulary has an independent domain record.
- BDD: this record owns visible agent/user approval and stop behavior.
- SDD: the CLI and adapter interfaces are independently specified.
- TDD: runtime and no-mutation regressions are independently protected.
- ADR: ADR 0054 records the pilot approval and non-enforcement boundary.
- SSOT: artifact ownership and writer paths are independently canonical.
- Planning: existing Layer 1/2/3 design remains linked evidence.

## Rule placement

- Rule: architecture mapping and source refactoring are separate, approval-batched
  flows with a new option gate before every independently reviewable source batch.
- Scope: framework-global
- Primary record: `.lazy-harness/behavior/architecture-refactor-flow.md`
- Why not AGENTS.md: this is a specialized skill workflow, not every-turn grammar.
- Confirmation: user-selected approval-batched skill behavior on 2026-07-14.

## Discovery capture

- DDD: no new terms beyond the dedicated architecture vocabulary record.
- BDD: this record owns the approved interaction flow.
- SDD: runtime and delegation contracts are linked, not mirrored.
- TDD: each scenario has corresponding fixture or self-test coverage.
- ADR: ADR 0054 remains primary.
- SSOT: host-map and catalog ownership remain in the storage SSOT.
- Planning: no additional backlog was created.
