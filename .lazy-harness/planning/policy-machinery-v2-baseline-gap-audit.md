# Planning — Policy Machinery V2 Baseline / Gap Audit

Status: active-audit
Date: 2026-06-18
Layer: Planning
Related roadmap: `.lazy-harness/planning/lazy-harness-v2-implementation-roadmap.md#phase-3--unify-rulebook--capability-registry-into-policy-machinery`
Related SDD: `.lazy-harness/spec/platform/policy-machinery-v2.md`
Related TDD: `.lazy-harness/tests/policy-machinery-v2.md`
Related fixture: `.lazy-harness/fixtures/policy-machinery-v2/example-policy.json`
Related SSOT: `.lazy-harness/ssot/capability-registry.md`

## Rule digest

- Status: active Phase 3 baseline/gap audit
- Scope: framework-global
- Applies when:
  - starting Policy Machinery V2 implementation
  - deciding whether to change rulebook or capability registry storage
  - promoting project operating policies beyond discover/recommend
- Must:
- preserve existing Phase 0-2 rulebook/capability CLIs during migration
- implement user-confirmed Option B: typed policy registry is canonical
  - align policy candidate/promotion/demotion with Project Map update-loop semantics
  - keep runtime enforcement out of the first Phase 3 slice
- Must not:
- keep adding new canonical policy semantics only to `.lazy-harness/rules/**`
  - silently rewrite `.lazy-harness/ssot/capabilities.json` schema
  - promote warn/block policies without confirmation and regression tests
- Record completion:
  - Phase 3 runtime/schema work should update this audit, SDD, TDD, fixture, self-test, manifest, graph rows, and validation logs together.

## Evidence read

Records inspected for this slice:

- `.lazy-harness/planning/lazy-harness-v2-implementation-roadmap.md`
- `.lazy-harness/planning/project-operating-rulebook-implementation-plan.md`
- `.lazy-harness/planning/capability-registry-implementation-plan.md`
- `.lazy-harness/spec/platform/project-operating-rulebook.md`
- `.lazy-harness/ssot/capability-registry.md`
- `.lazy-harness/decisions/0040-capability-registry-kind-level-separation.md`
- `.lazy-harness/spec/platform/project-map-update-loop-v2.md`
- `.lazy-harness/ssot/capabilities.json`

## Current baseline

Current implementation already has:

- `.lazy-harness/rules/**` as the human operating rulebook path.
- `lazy rules list/audit/resolve` via `.lazy-harness/scripts/rulebook.ts`.
- `.lazy-harness/ssot/capabilities.json` as the machine-readable registry.
- `lazy capability list/add/resolve/candidates/audit` via `.lazy-harness/scripts/capability.ts`.
- Capability `kind` and `level` separated by ADR 0040 and capability registry SSOT.
- Project Map update-loop events and non-canonical candidate/canonical transition semantics.

## Gap matrix

| Area | Current baseline | Phase 3 target | Gap | Safe next action |
|---|---|---|---|---|
| Policy packet | Rulebook + capability entries exist separately | Explicit policy packet connects stage, level, evidence, rollback, source records | No shared contract | Add SDD/TDD/fixture static contract. |
| Stage awareness | `appliesWhen` strings exist | Formal `stage` vocabulary for turn/edit/commit/push/release/high-risk | Not typed as policy stage | Keep contract-only until schema decision. |
| Promotion/demotion | Capability levels exist | Update-loop evidence models policy candidate/promotion/demotion | No Phase 3 event-specific fixture yet | Reuse update-loop semantics, do not add writer. |
| Storage decision | Hybrid rulebook + capability is implemented | Future may keep, absorb, or deprecate rulebook | Requires user/team option gate | Preserve hybrid storage and record options. |
| Enforcement | Existing guidance ladder/advisory paths | Warn/block policy enforcement could be future | Needs tests and confirmation | Do not add enforcement in this slice. |

## Phase 3 slice decision

This slice implements only:

1. SDD contract for Policy Machinery V2.
2. TDD regression record.
3. Static fixture for a discover-level policy packet.
4. Self-test/manifest/graph coverage.

It intentionally did not implement:

- new runtime writer,
- new hook enforcement,
- capability schema rewrite,
- rulebook deprecation,
- automatic warn/block promotion.

## User-confirmed storage decision

User selected Option B on 2026-06-18:

1. Typed policy records are canonical.
2. Capability registry remains machine binding for commands/actions/tools.
3. Rulebook markdown becomes compatibility/generated/explain surface during migration.
4. Runtime warn/block enforcement remains a later promoted slice.

First implementation slice adds `.lazy-harness/ssot/policies.json`, `.lazy-harness/schemas/policies.schema.json`, and read-only `lazy policy list/audit/explain`.

User confirmed the recommended next step (A) on 2026-06-18: add advisory-only `lazy policy resolve` for `discover`/`recommend`/`default` levels and keep warn/block runtime enforcement deferred.

User confirmed the follow-up next step (B) on 2026-06-18: add explicit-context warn-only runtime. The slice must stay non-blocking, must not classify raw user/assistant text, and must keep block runtime deferred.

User confirmed the follow-up next step on 2026-06-18: add a deterministic generated/explain rulebook view from typed policy records. The slice must keep `.lazy-harness/ssot/policies.json` canonical and keep generated Markdown non-canonical.

## Implementation map

- Status: `phase-3-baseline-audit-static-slice`
- Records:
  - `.lazy-harness/planning/policy-machinery-v2-baseline-gap-audit.md`
  - `.lazy-harness/spec/platform/policy-machinery-v2.md`
  - `.lazy-harness/tests/policy-machinery-v2.md`
  - `.lazy-harness/decisions/0046-policy-machinery-typed-policy-canonical.md`
  - `.lazy-harness/ssot/policy-registry.md`
- Fixture:
  - `.lazy-harness/fixtures/policy-machinery-v2/example-policy.json`
- Source/test:
  - `.lazy-harness/scripts/policy.ts`
  - `.lazy-harness/generated/policy-rulebook.md`
  - `.lazy-harness/ssot/policies.json`
  - `.lazy-harness/schemas/policies.schema.json`
  - `.lazy-harness/scripts/self-test.py#check_policy_machinery_v2`
  - `.lazy-harness/manifests/init-categories.json`
- Cross-layer links:
  - `.lazy-harness/ssot/capability-registry.md`
  - `.lazy-harness/spec/platform/project-operating-rulebook.md`
  - `.lazy-harness/spec/platform/project-map-update-loop-v2.md`

## Discovery capture

- Captured because Phase 3 introduced a storage architecture decision and a future runtime/enforcement backlog.
- User-confirmed Option B closes the storage option gate; runtime warn/block enforcement remains future backlog.

## Rule placement

- Layer: Planning.
- Why: this is a baseline/gap audit and next-slice plan, not canonical runtime contract by itself.
