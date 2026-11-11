# ADR 0063 — lazy-harness as module composition layer; module-owned connection contracts

Status: accepted (user-confirmed native options, 2026-11-07 ~ 2026-11-10)
Layer: ADR
Date: 2026-11-10
Related SDD: `.lazy-harness/spec/platform/module-composition.md`
Related SSOT: `.lazy-harness/ssot/project-identity.md` (section "lazy-harness role and module composition")
Related ADR: `.lazy-harness/decisions/0013-framework-external-dependency-invariant.md`, `.lazy-harness/decisions/0061-monitoring-core-fabric-optional.md`, `.lazy-harness/decisions/0062-monitoring-core-own-repository.md`
Related planning: `.lazy-harness/planning/module-composition-rollout.md`

## Rule digest

- Status: active
- Layer: ADR
- Scope: host-project
- Aliases:
  - module composition contract
  - 모듈 연결 규약
  - 모듈 조립층
- Applies when:
  - attaching a module repository (monitoring, knowledge, later ones) to lazy-harness
  - deciding where a connection contract, Fabric adapter or module manifest lives
- Must:
  - keep lazy-harness as the record/rule framework plus the module composition layer
  - let each module repository define and export its own connection contract (port types, fakes, conformance tests, and for other-language modules an RPC server plus a TypeScript client)
  - keep only the short common rules in the SDD: no pi-fabric dependency in modules, one root `lazy-harness.module.json`, JSON-RPC 2.0 stdio for process modules, the shared status/certainty result, integer major versions
  - keep pi-fabric use inside `packages/lazy-harness-pi` only; `.lazy-harness` core works without Fabric (ADR 0013)
- Must not:
  - create a separate contract repository while modules are few and no real duplication exists
  - let a module repository depend on pi-fabric
- Record completion:
  - update this ADR when the contract ownership, the common rules or the Fabric position changes

## Context

The monitoring and knowledge modules moved into their own repositories (ADR 0062 for monitoring) and started their own connection work before lazy-harness had a written connection contract. lazy-harness had to state its own role and how modules attach, through Pi Fabric, without pulling module internals back into this repository.

## Decision

- Role: lazy-harness is the record/rule framework and the module composition layer. Module design, decision and measurement records stay in this repository.
- Contract ownership: each module repository defines and exports its connection contract; lazy-harness installs the module as a git submodule pinned to a commit, imports it and implements its ports with Fabric. The same-day option of a separate contract repository (working name `lazy-harness-contract`) was replaced by this choice.
- Common rules (SDD §6): root manifest `lazy-harness-module/v1` with required `schema`, `id`, `version`, `runtime`, `entry`, `requires`, `test`, `conformance` and optional `provides`, `records`; JSON-RPC 2.0 over stdio for process modules; shared result `status` + `certainty`, `uncertain` never auto-retried; a deliberate hold is `completed`/`terminal` with `value.held: true`; integer major versions, unsupported majors refused at start.
- Fabric position: only `packages/lazy-harness-pi` uses Fabric. The documented connection is the public host event `pi-fabric:program:run:v1` without importing Fabric internals (SDD §6.7); implementation and final confirmation happen in the later attach PR.
- Work split (user instruction 2026-11-10): module sessions align their own repositories to this contract; this contract work does not take over module work.

## Consequences

- A module changes its contract next to its code and tests; lazy-harness follows by moving the submodule commit and passing the module's conformance tests.
- Two places to read when building a module (module contract plus this SDD's common rules), reduced by module documents linking the SDD.
- Revisit a shared contract package only when the same code really repeats across modules.
- Attaching monitoring stays a later user decision (monitoring session order: contract alignment, submodule inclusion, then attach PR).

## Alternatives

- Separate contract repository with schemas and a conformance kit: rejected for now; adds a third versioned repository at 2–3 modules.
- Monitoring repository as the canonical common contract: rejected; other modules would follow a monitoring-specific repository.
- All contracts inside lazy-harness: rejected; module internals would drift away from their code.

## Implementation map

- Status: `planned` (documentation only; no adapter or module code in this decision)
- Primary files: `.lazy-harness/spec/platform/module-composition.md`, `.lazy-harness/ssot/project-identity.md`, this ADR.
- Key symbols: none yet.
- Tests / protection: none yet; module conformance tests and the Fabric adapter tests come with the attach work.
