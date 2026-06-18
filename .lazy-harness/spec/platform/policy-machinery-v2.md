# SDD — Policy Machinery V2

Status: active-contract
Layer: SDD
Date: 2026-06-18
Related roadmap: `.lazy-harness/planning/lazy-harness-v2-implementation-roadmap.md#phase-3--unify-rulebook--capability-registry-into-policy-machinery`
Related audit: `.lazy-harness/planning/policy-machinery-v2-baseline-gap-audit.md`
Related ADR: `.lazy-harness/decisions/0046-policy-machinery-typed-policy-canonical.md`
Related SSOT: `.lazy-harness/ssot/policy-registry.md`
Related SSOT: `.lazy-harness/ssot/capability-registry.md`
Related SDD: `.lazy-harness/spec/platform/project-operating-rulebook.md`, `.lazy-harness/spec/platform/capability-resolution.md`, `.lazy-harness/spec/platform/project-map-update-loop-v2.md`
Related TDD: `.lazy-harness/tests/policy-machinery-v2.md`
Related fixture: `.lazy-harness/fixtures/policy-machinery-v2/example-policy.json`

## Rule digest

- Status: active-contract / Option B typed policy canonical slice
- Layer: SDD
- Scope: framework-global
- Applies when:
  - designing Policy Machinery V2
  - connecting project operating rules, capabilities, and Project Map update events
  - deciding whether policy evidence may promote/demote an operating rule or capability level
- Must:
  - keep policies stage-aware (`turn`, `edit`, `commit`, `push`, `release`, `high-risk-mutation`)
  - keep capability `kind` independent from enforcement `level`
  - treat `.lazy-harness/ssot/policies.json` as canonical typed behavior policy storage
  - keep `.lazy-harness/ssot/capabilities.json` as command/action/capability binding storage
  - keep `.lazy-harness/rules/**` as compatibility/generated/explain surface during migration, not canonical source for new policy semantics
  - expose `lazy policy resolve` as advisory-only guidance for `discover`, `recommend`, and `default` levels
  - expose warn-level policies only through explicit structured `policy_context` and `warn-only` output
  - render rulebook explanations from typed policy records through `lazy policy render-rulebook`
  - validate actual policy writes through `lazy policy upsert --from-json ... --confirm` before retiring rulebook semantics
  - represent policy creation/promotion/demotion as Project Map update-loop evidence, not as hidden hook state
  - keep new policies at `discover` or `recommend` unless user/team confirmation explicitly grants stronger levels
  - require source records and rollback/demotion criteria for `default`, `warn`, and `block` policies
- Must not:
  - add new canonical policy semantics only to `.lazy-harness/rules/**`
  - treat generated/explain rulebook text as canonical truth
  - turn advisory policies into blocking hooks from this contract-only slice
  - infer warn/block decisions from raw user text or assistant text
  - treat warn-only output as a block
  - edit `.lazy-harness/generated/policy-rulebook.md` as canonical source
  - write policies without `--confirm`
  - allow generated policy packets to become canonical truth without record-write policy or explicit confirmation
  - add semantic-authority fields such as confidence/intent/risk/requiredRead/nextAction/candidateMeaning
- Record completion:
  - Phase 3 runtime/schema work must update this SDD, TDD, fixture, baseline audit, manifest, graph rows, schema, registry, CLI, and validation evidence together.

## Purpose

Policy Machinery V2 is the unification layer that explains how a project/team operating policy moves between typed policy records, machine-readable capability bindings, generated/explain views, and Project Map update-loop evidence.

Option B is selected by user confirmation. The current stores are:

```text
.lazy-harness/ssot/policies.json       # canonical typed behavior policy registry
.lazy-harness/ssot/capabilities.json   # machine-readable capabilities and action bindings
.lazy-harness/rules/**                 # compatibility/generated/explain surface during migration
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

## Advisory resolver slice

User confirmed the next step after Option B: start with advisory resolution before warn/block behavior.

`lazy policy resolve` is the first resolver slice:

- Reads `.lazy-harness/ssot/policies.json`.
- Filters by `stage` and `appliesTo` when provided.
- Surfaces only `discover`, `recommend`, and `default` policy levels.
- Emits `enforcement = advisory-only` and `recommendedAction = surface-guidance`.
- Does not emit warn/block decisions, write state, mutate graph rows, or hook into lifecycle enforcement.

Block runtime remains a future promoted slice with separate TDD, bypass behavior, and explicit confirmation.

## Warn-only runtime slice

User confirmed the next step after advisory resolution: warn-only runtime.

Warn-only runtime is intentionally narrow:

- `lazy policy resolve --runtime warn` may surface `warn`, `default`, `recommend`, and `discover` levels.
- `check-policy-warn-runtime.py` runs in `response.completed` after existing blocking helpers.
- The helper only reads explicit structured `policy_context` / `policyContext` payload fields.
- The helper never classifies raw user text or raw assistant text.
- The helper emits `WARN. Policy Machinery warn-only runtime` and never emits `STOP`.
- Warnings are bypassable by adding `policy_context.acknowledgedPolicyWarnings` with the policy id.
- Block runtime remains out of scope.

## Generated rulebook view slice

User confirmed the next step after warn-only runtime: generate/explain rulebook views from typed policy records.

`lazy policy render-rulebook` is deterministic and derived:

- Reads canonical `.lazy-harness/ssot/policies.json`.
- Renders Markdown with a `GENERATED VIEW, NON-CANONICAL` disclaimer.
- Writes only to root-relative `.lazy-harness/generated/**` when `--write` is passed.
- Rejects output paths outside `.lazy-harness/generated/**`.
- Does not replace `policies.json` or create policy semantics.
- Host sync does not need to copy generated cache contents; each host can regenerate locally.

## Policy write round-trip slice

User identified a validation gap: seeded policies and read-only commands were tested, but adding a new policy had not been exercised.

`lazy policy upsert` closes that gap:

- Reads a policy object from `--from-json`.
- Validates the full next registry with the same audit rules as `lazy policy audit`.
- Defaults to dry-run and writes only with `--confirm`.
- Writes only the canonical `.lazy-harness/ssot/policies.json` registry.
- Replaces an existing policy with the same id deterministically.
- Keeps policies id-sorted for stable diffs.
- The regression suite validates save → audit → resolve → warn runtime → generated rulebook render → lazy-sync seed merge.

## Storage posture

Phase 3 selected Option B:

1. Policy entries under `.lazy-harness/ssot/policies.json` are canonical for behavior policy semantics.
2. Capability entries in `.lazy-harness/ssot/capabilities.json` bind actions, preferred actions, discouraged actions, and levels to those policies.
3. Rulebook markdown under `.lazy-harness/rules/**` is compatibility/generated/explain surface during migration.
4. Project Map update-loop events carry policy candidates/promotions/demotions as evidence and transition metadata.

The selected architecture is:

- Option B: absorb rulebook content into typed policy/capability records.
- Added compatibility detail: generated/explain views may be rendered from typed policy records for humans/LLMs.

This slice does not delete `.lazy-harness/rules/**`; it makes new canonical policy semantics land in typed policy records first.

## Update-loop integration

Policy candidate, promotion, and demotion events are Project Map update-loop events. They are not adapter-specific and do not become canonical truth without one of these paths:

- a user/team-confirmed record write,
- an accepted queue promotion that targets a canonical record,
- a future explicit policy migration that has its own ADR/TDD coverage.

## Implementation map

- Status: `phase-3-record-first-contract`
- Records:
  - `.lazy-harness/spec/platform/policy-machinery-v2.md` — this contract.
  - `.lazy-harness/decisions/0046-policy-machinery-typed-policy-canonical.md` — source canonical ADR for the user-confirmed Option B decision.
  - `.lazy-harness/framework/operational-adrs/0046-policy-machinery-typed-policy-canonical.md` — host sync target for the same framework ADR so host `.lazy-harness/decisions/` remains host-owned.
  - `.lazy-harness/ssot/policy-registry.md` — typed policy registry SSOT.
  - `.lazy-harness/tests/policy-machinery-v2.md` — regression expectations.
  - `.lazy-harness/planning/policy-machinery-v2-baseline-gap-audit.md` — baseline/gap audit.
  - `.lazy-harness/fixtures/policy-machinery-v2/example-policy.json` — static policy packet fixture.
  - `.lazy-harness/ssot/capability-registry.md` — current capability kind/level SSOT.
  - `.lazy-harness/spec/platform/project-operating-rulebook.md` — current rulebook contract.
  - `.lazy-harness/spec/platform/project-map-update-loop-v2.md` — update-loop evidence/transition model.
- Source files:
  - `.lazy-harness/scripts/capability.ts` — current capability CLI, unchanged by this slice.
  - `.lazy-harness/scripts/policy.ts` — typed policy list/audit/explain/resolve/render-rulebook/upsert CLI.
  - `.lazy-harness/hooks/lifecycle/helpers/check-policy-warn-runtime.py` — explicit-context warn-only response.completed helper.
  - `.lazy-harness/generated/policy-rulebook.md` — non-canonical generated/explain view rendered from typed policies.
  - `.lazy-harness/scripts/rulebook.ts` — current rulebook CLI, unchanged by this slice.
  - `.lazy-harness/ssot/policies.json` — canonical typed policy registry.
  - `.lazy-harness/schemas/policies.schema.json` — policy registry schema.
  - `.lazy-harness/scripts/self-test.py` — static fixture/manifest validation.
  - `.lazy-harness/manifests/init-categories.json` — host sync package, including the rulebook SDD dependency required by this static contract.
- Protected by:
  - `self-test.py#check_policy_machinery_v2`
  - `lazy policy audit --format=json`
  - `lazy policy resolve --stage turn --applies-to making_validation_claims --format=json`
  - `lazy policy resolve --runtime warn --stage turn --applies-to making_validation_claims --format=json`
  - `lazy policy render-rulebook --write --format=json`
  - `lazy policy upsert --from-json <policy.json> --confirm --format=json`
  - `lazy policy explain --id record-first-validation --format=md`
  - `python3 .lazy-harness/scripts/self-test.py --scope framework`
  - `.lazy-harness/bin/lazy test`

## Layer completeness impact

- DDD: no business-domain vocabulary impact.
- SDD: this record defines the Phase 3 policy contract and links to rulebook/capability/update-loop contracts.
- BDD: agent behavior may now surface explicit-context warn-only guidance; block behavior remains future work.
- TDD: `.lazy-harness/tests/policy-machinery-v2.md` and `self-test.py#check_policy_machinery_v2` protect this slice.
- ADR: `.lazy-harness/decisions/0046-policy-machinery-typed-policy-canonical.md` selects Option B.
- SSOT: `.lazy-harness/ssot/policy-registry.md` is canonical for behavior policy semantics; `.lazy-harness/ssot/capability-registry.md` remains kind/level binding source of truth.

## Rule placement

- Layer: SDD.
- Why: this is a platform contract for policy packet shape and boundaries.
- Why not ADR: ADR 0046 records the architectural choice; this SDD records the implementation contract.
- Why not SSOT: `.lazy-harness/ssot/policy-registry.md` records the canonical storage rule.
