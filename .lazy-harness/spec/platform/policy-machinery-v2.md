# SDD — Policy Machinery V2

Status: active-contract
Layer: SDD
Date: 2026-06-18
Related roadmap: `.lazy-harness/planning/lazy-harness-v2-implementation-roadmap.md#phase-3--unify-rulebook--capability-registry-into-policy-machinery`
Related audit: `.lazy-harness/planning/policy-machinery-v2-baseline-gap-audit.md`
Related SSOT: `.lazy-harness/ssot/capability-registry.md`
Related SDD: `.lazy-harness/spec/platform/project-operating-rulebook.md`, `.lazy-harness/spec/platform/capability-resolution.md`, `.lazy-harness/spec/platform/project-map-update-loop-v2.md`
Related TDD: `.lazy-harness/tests/policy-machinery-v2.md`
Related fixture: `.lazy-harness/fixtures/policy-machinery-v2/example-policy.json`

## Rule digest

- Status: active-contract / Phase 3 record-first slice
- Layer: SDD
- Scope: framework-global
- Applies when:
  - designing Policy Machinery V2
  - connecting project operating rules, capabilities, and Project Map update events
  - deciding whether policy evidence may promote/demote an operating rule or capability level
- Must:
  - keep policies stage-aware (`turn`, `edit`, `commit`, `push`, `release`, `high-risk-mutation`)
  - keep capability `kind` independent from enforcement `level`
  - preserve `.lazy-harness/rules/**` and `.lazy-harness/ssot/capabilities.json` as the implemented Phase 0-2 stores unless an explicit option gate changes that architecture
  - represent policy creation/promotion/demotion as Project Map update-loop evidence, not as hidden hook state
  - keep new policies at `discover` or `recommend` unless user/team confirmation explicitly grants stronger levels
  - require source records and rollback/demotion criteria for `default`, `warn`, and `block` policies
- Must not:
  - silently absorb the rulebook into `capabilities.json` or deprecate `.lazy-harness/rules/**`
  - turn advisory policies into blocking hooks from this contract-only slice
  - allow generated policy packets to become canonical truth without record-write policy or explicit confirmation
  - add semantic-authority fields such as confidence/intent/risk/requiredRead/nextAction/candidateMeaning
- Record completion:
  - Phase 3 runtime/schema work must update this SDD, TDD, fixture, baseline audit, manifest, graph rows, and validation evidence together.

## Purpose

Policy Machinery V2 is the unification layer that explains how a project/team operating policy moves between human-readable rulebook records, machine-readable capability bindings, and Project Map update-loop evidence.

It does not replace existing Phase 0-2 implementations. The current stores remain:

```text
.lazy-harness/rules/**                 # human-readable operating rulebook
.lazy-harness/ssot/capabilities.json   # machine-readable capabilities and action bindings
```

## Policy packet shape

A Policy Machinery V2 policy packet has this conceptual shape:

```ts
type PolicyMachineryV2Policy = {
  schemaVersion: 'policy-machinery-v2/v1'
  id: string
  title: string
  scope: 'framework-global' | 'host-project' | 'team-policy' | 'adapter'
  stage: 'turn' | 'edit' | 'commit' | 'push' | 'release' | 'high-risk-mutation'
  level: 'discover' | 'recommend' | 'default' | 'warn' | 'block'
  appliesTo: string[]
  sourceRecord: string
  rulebookRecord?: string
  capabilityIds: string[]
  evidence: Array<{ kind: 'record' | 'validation-output' | 'user-confirmation' | 'update-event'; path?: string; summary: string }>
  promotion: { requiresConfirmation: boolean; allowedTargetLevels: string[] }
  rollback: { criteria: string[]; demotionTarget: 'discover' | 'recommend' | 'retired' }
  updateLoop: { eventType: 'policy-candidate' | 'policy-promotion' | 'policy-demotion'; canonicalByPacketAlone: false }
}
```

The fixture uses JSON, not TypeScript, as the static contract sample.

## Stage and level rules

- `stage` says when the policy is relevant.
- `level` says how strongly lazy-harness may steer.
- `kind` remains a capability property, not a policy level.
- `block` requires explicit confirmation or a high-risk mutation boundary.
- `warn` and `block` require documented bypass behavior and tests before runtime enforcement.

## Storage posture

Phase 3 keeps the existing hybrid architecture:

1. Rulebook entries under `.lazy-harness/rules/**` explain human operating policy.
2. Capability entries in `.lazy-harness/ssot/capabilities.json` bind actions, preferred actions, discouraged actions, and levels.
3. Project Map update-loop events carry policy candidates/promotions/demotions as evidence and transition metadata.

The future storage decision is intentionally not resolved here:

- Option A: keep rulebook as lightweight human-readable policy docs.
- Option B: absorb rulebook content into typed policy/capability records.
- Option C: deprecate rulebook after migration.
- Option D: type your own architecture.

Until that option gate is answered, Phase 3 work must not remove the rulebook or rewrite the capability registry schema.

## Update-loop integration

Policy candidate, promotion, and demotion events are Project Map update-loop events. They are not adapter-specific and do not become canonical truth without one of these paths:

- a user/team-confirmed record write,
- an accepted queue promotion that targets a canonical record,
- a future explicit policy migration that has its own ADR/TDD coverage.

## Implementation map

- Status: `phase-3-record-first-contract`
- Records:
  - `.lazy-harness/spec/platform/policy-machinery-v2.md` — this contract.
  - `.lazy-harness/tests/policy-machinery-v2.md` — regression expectations.
  - `.lazy-harness/planning/policy-machinery-v2-baseline-gap-audit.md` — baseline/gap audit.
  - `.lazy-harness/fixtures/policy-machinery-v2/example-policy.json` — static policy packet fixture.
  - `.lazy-harness/ssot/capability-registry.md` — current capability kind/level SSOT.
  - `.lazy-harness/spec/platform/project-operating-rulebook.md` — current rulebook contract.
  - `.lazy-harness/spec/platform/project-map-update-loop-v2.md` — update-loop evidence/transition model.
- Source files:
  - `.lazy-harness/scripts/capability.ts` — current capability CLI, unchanged by this slice.
  - `.lazy-harness/scripts/rulebook.ts` — current rulebook CLI, unchanged by this slice.
  - `.lazy-harness/scripts/self-test.py` — static fixture/manifest validation.
  - `.lazy-harness/manifests/init-categories.json` — host sync package, including the rulebook SDD dependency required by this static contract.
- Protected by:
  - `self-test.py#check_policy_machinery_v2`
  - `python3 .lazy-harness/scripts/self-test.py --scope framework`
  - `.lazy-harness/bin/lazy test`

## Layer completeness impact

- DDD: no business-domain vocabulary impact.
- SDD: this record defines the Phase 3 policy contract and links to rulebook/capability/update-loop contracts.
- BDD: agent behavior remains advisory unless future confirmed policy levels introduce warn/block behavior.
- TDD: `.lazy-harness/tests/policy-machinery-v2.md` and `self-test.py#check_policy_machinery_v2` protect this slice.
- ADR: no new architecture decision is made; unresolved storage options remain gated.
- SSOT: `.lazy-harness/ssot/capability-registry.md` remains kind/level source of truth.

## Rule placement

- Layer: SDD.
- Why: this is a platform contract for policy packet shape and boundaries.
- Why not ADR: no storage option has been selected yet.
- Why not SSOT: current canonical stores remain the existing capability registry and rulebook records.
