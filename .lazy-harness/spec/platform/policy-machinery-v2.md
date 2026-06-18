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
  - prove rulebook retirement readiness through `lazy policy retire-readiness --format=json` before changing `.lazy-harness/rules/**` semantics
  - expose retired rulebook semantics through `lazy rules` compatibility boundary metadata
  - expose block runtime readiness only as a non-mutating preflight before any hard-stop hook work
  - keep hard-stop runtime integration in dry-run helper mode until explicit lifecycle hook installation is approved
  - represent policy creation/promotion/demotion as Project Map update-loop evidence, not as hidden hook state
  - keep new policies at `discover` or `recommend` unless user/team confirmation explicitly grants stronger levels
  - require source records and rollback/demotion criteria for `default`, `warn`, and `block` policies
- Must not:
  - add new canonical policy semantics only to `.lazy-harness/rules/**`
  - treat generated/explain rulebook text as canonical truth
  - turn advisory policies into blocking hooks from this contract-only slice
  - install lifecycle hard-stop hooks from block-readiness alone
  - connect dry-run block helper to `response.completed` before a later explicit lifecycle integration slice
  - infer warn/block decisions from raw user text or assistant text
  - treat warn-only output as a block
  - edit `.lazy-harness/generated/policy-rulebook.md` as canonical source
  - write policies without `--confirm`
  - delete or demote `.lazy-harness/rules/**` semantics without retire-readiness proof
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

## Block runtime readiness preflight slice

User confirmed the next step after rulebook semantic retirement: prepare block runtime, but do not install hard-stop hooks.

`lazy policy block-readiness` is the preflight slice:

- Reads `.lazy-harness/ssot/policies.json`.
- Reports `schemaVersion = policy-block-readiness/v1`.
- Reports `runtime = block-preflight-only`.
- Reports `hardStopHookInstalled = false` and `lifecycleMutation = false`.
- Returns `ready: false` on the source host until a promoted `level=block` policy exists.
- `--strict` exits nonzero while blockers exist.
- A block policy is ready only when it has:
  - `level = block`,
  - user-confirmation evidence,
  - validation-output evidence proving block and allow cases,
  - an active/proposed `## Hard-stop promotion` section in `sourceRecord`,
  - `runtime.blocks = true`,
  - `runtime.requiresExplicitContext = true`,
  - documented `runtime.bypass`,
  - an existing `runtime.fixture`,
  - rollback criteria.
- This slice does not call lifecycle helpers, emit STOP output, mutate hooks, or install a hard-stop.

Source-host status after the first block promotion readiness slice:

- `validation-evidence-block` is the first `level=block` policy.
- It is scoped to `claiming_validation_complete_without_evidence` and equivalent non-trivial completion claims without evidence.
- `lazy policy block-readiness --strict --format=json` passes.
- `hardStopHookInstalled=false` and `lifecycleMutation=false` remain required until a later lifecycle integration slice.

## Dry-run hard-stop runtime helper slice

User confirmed proceeding with dry-run hard-stop runtime integration and review, but not actual hook installation.

`check-policy-block-runtime.py` is the dry-run helper:

- Reads only explicit structured `policy_context` / `policyContext`.
- Requires `policy_context.blockRuntimeDryRun = true`; otherwise it stays silent.
- Never classifies raw user/assistant text.
- Emits review-only `DRY-RUN STOP`, `DRY-RUN ALLOW`, or `DRY-RUN BYPASS` output.
- Always exits zero and fails open.
- Does not install hooks, mutate lifecycle state, or connect itself to `response.completed`.
- Uses `validation-evidence-block` as the only current source-host block policy.

Allow/block/bypass semantics:

- `DRY-RUN STOP`: explicit block context matches `validation-evidence-block` and no validation evidence or bypass acknowledgement is attached.
- `DRY-RUN ALLOW`: explicit block context matches and validation evidence is attached.
- `DRY-RUN BYPASS`: explicit block context matches and `acknowledgedPolicyBlocks` plus `policyBlockBypassReason` are present.
- Silent: raw user/assistant text, no `policy_context`, no `blockRuntimeDryRun`, or no matching block policy.

## Hard-stop promotion

- Status: proposed
- Boundary: `validation-evidence-block` only covers explicit validation-complete claims without attached record/test evidence.
- Scope: framework-global
- User confirmation: user confirmed proceeding with the first `level=block` policy promotion readiness slice on 2026-06-18, after block-readiness preflight existed and before lifecycle hook installation.
- Evidence: repeated work-unit completion flows need concrete validation evidence before claiming completion; Policy Machinery TDD protects source-host readiness and negative missing-fixture cases.
- Existing softer coverage: `record-first-validation` discover policy and `validation-evidence-warning` warn-only runtime exist, but the block policy is prepared for the narrower boundary where a final validation-complete claim lacks evidence.
- Fixture: .lazy-harness/tests/policy-block-validation-evidence.md
- Narrowness: only `claiming_validation_complete_without_evidence` and equivalent non-trivial completion claims without evidence are in scope; generic user text, raw assistant text, and advisory/warn flows remain out of scope.
- Rollback: demote `validation-evidence-block` to `warn` or `recommend`, remove block runtime metadata, or retire the policy before any lifecycle hook integration.

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

## Rulebook retire-readiness preflight slice

Rulebook retirement is not a delete-first migration. Before `.lazy-harness/rules/**` can lose hand-maintained canonical semantics, a preflight must prove compatibility:

- `lazy policy retire-readiness --format=json` is read-only and non-destructive.
- It reads active `.lazy-harness/rules/**/*.md` entries, `.lazy-harness/ssot/capabilities.json`, and `.lazy-harness/ssot/policies.json`.
- An active rulebook entry is ready only when it has a capability binding and that capability is linked to an existing typed policy through `capability.policyIds` or `policy.capabilityIds`.
- `--strict` exits non-zero when blockers exist, so retire/deprecation work can be gated in CI/preflight.
- The current source host may report `ready: false`; that is expected until the active rulebook compatibility surface has typed policy coverage.
- After `project-operating-rulebook-policy`, the source host reports `ready: true` because `.lazy-harness/rules/README.md` is linked through capability `project-operating-rulebook` to a typed policy.
- The preflight does not delete `.lazy-harness/rules/**`, mutate `policies.json`, mutate `capabilities.json`, or change `lazy rules` compatibility behavior.

## Rulebook semantic retirement slice

After source-host retire-readiness became true, `lazy rules` was redefined as compatibility/explain tooling rather than canonical policy tooling:

- It still lists, audits, and resolves `.lazy-harness/rules/**` entries for compatibility and human review.
- JSON output includes `schemaVersion = rulebook-compatibility/v1`.
- JSON output includes `retiredCanonicalSemantics = true`.
- JSON output includes `canonicalPolicySource = .lazy-harness/ssot/policies.json` and `semanticAuthority = typed-policy-registry`.
- Resolve output uses `enforcement = compatibility-advisory`.
- This slice does not delete `.lazy-harness/rules/**`, remove host sync seeds, or introduce block runtime enforcement.

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
  - `.lazy-harness/scripts/policy.ts` — also exposes `retire-readiness` preflight for rulebook retirement gating.
  - `.lazy-harness/scripts/policy.ts` — exposes `block-readiness` preflight for block runtime preparation without lifecycle mutation.
  - `.lazy-harness/hooks/lifecycle/helpers/check-policy-block-runtime.py` — dry-run review helper for explicit structured block policy context, not installed in lifecycle hooks.
  - `.lazy-harness/ssot/policies.json` — contains `validation-evidence-block` as the first readiness-complete block policy.
  - `.lazy-harness/tests/policy-block-validation-evidence.md` — fixture record for allow/block cases and no-hook readiness.
  - `.lazy-harness/scripts/rulebook.ts` — exposes `rulebook-compatibility/v1` boundary metadata after semantic retirement.
  - `.lazy-harness/ssot/policies.json` — includes `project-operating-rulebook-policy` for active rulebook compatibility coverage.
  - `.lazy-harness/ssot/capabilities.json` — links `project-operating-rulebook.policyIds` to `project-operating-rulebook-policy`.
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
  - `lazy policy retire-readiness --format=json`
  - `lazy policy retire-readiness --strict --format=json`
  - `lazy rules list --format=json`
  - `lazy rules audit --strict --format=json`
  - `lazy rules resolve --intent adding_project_operating_policy --format=json`
  - `lazy policy block-readiness --format=json`
  - `lazy policy block-readiness --strict --format=json`
  - `.lazy-harness/hooks/lifecycle/helpers/check-policy-block-runtime.py <payload-json>`
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
