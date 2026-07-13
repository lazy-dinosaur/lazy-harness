# ADR 0046 — Policy Machinery Typed Policy Canonical

Status: accepted
Date: 2026-06-18
Layer: ADR
Related SDD: `.lazy-harness/spec/platform/policy-machinery-v2.md`
Related SSOT: `.lazy-harness/ssot/policy-registry.md`
Related SSOT: `.lazy-harness/ssot/capability-registry.md`
Related ADR: `.lazy-harness/decisions/0044-project-operating-rulebook.md`
Related TDD: `.lazy-harness/tests/policy-machinery-v2.md`

## Rule digest

- Status: active
- Layer: ADR
- Scope: framework-global
- Aliases:
  - 정책 기계
  - typed policy
  - 정책 canonical
  - policies.json
- Applies when:
  - adding or changing project/team behavior policy semantics
  - choosing the canonical store for operating policy vs rulebook markdown
- Must:
  - treat `.lazy-harness/ssot/policies.json` as the canonical typed policy registry; bind commands/actions via `capabilities.json`
  - add new policy semantics to typed policy records, using `lazy policy explain` for views
  - keep block enforcement gated on separate promotion evidence, TDD, and explicit confirmation
- Must not:
  - treat `.lazy-harness/rules/**` or generated/explain views as canonical policy source
- Record completion:
  - new policy semantics update `.lazy-harness/ssot/policies.json` and this ADR plus `.lazy-harness/spec/platform/policy-machinery-v2.md`
- Related records:
  - `.lazy-harness/spec/platform/policy-machinery-v2.md`
  - `.lazy-harness/ssot/policy-registry.md`
  - `.lazy-harness/decisions/0044-project-operating-rulebook.md`

## Context

ADR 0044 introduced the Phase 0-2 hybrid model:

```text
rules/*.md -> capabilities.json -> lazy rules/capability resolve
```

User review clarified that project/team operating rules are behavior policy, not general knowledge, and that humans do not need to maintain a markdown rulebook as the canonical source if the harness can explain typed policies on demand.

## Decision

Select Policy Machinery V2 option B:

```text
.lazy-harness/ssot/policies.json = canonical typed policy registry
.lazy-harness/ssot/capabilities.json = command/action/capability binding registry
.lazy-harness/rules/** = compatibility/generated/explain surface during migration, not canonical source for new policy semantics
lazy policy explain <id> = deterministic/LLM-ready explanation view over typed policy records
```

The typed policy registry becomes the canonical source for project/team behavior policy. Rulebook markdown may remain during migration for compatibility, documentation, or generated views, but it should not be the long-term source of truth for policy semantics.

## Consequences

- New policy semantics should be added to `policies.json`, not hand-maintained rulebook markdown.
- Capability entries may bind commands/actions to policy ids through `policyIds` or existing source links.
- `lazy rules` remains compatibility/audit tooling until a migration removes or redefines it.
- `lazy policy list/audit/explain` is read-only in the first Option B slice.
- User-confirmed next slice A adds `lazy policy resolve` as an advisory-only resolver for `discover`/`recommend`/`default` policies.
- User-confirmed next slice B adds explicit-context `warn-only` runtime for warn-level policies.
- User-confirmed next slice adds `lazy policy render-rulebook` and `.lazy-harness/generated/policy-rulebook.md` as a deterministic generated/explain view.
- User-requested validation gap fix adds `lazy policy upsert --from-json ... --confirm` and temp-host save round-trip tests before rulebook retire/deprecation.
- User-requested next-step execution adds a non-destructive `lazy policy retire-readiness` preflight before any hand-maintained rulebook canonical-semantics retirement.
- User-confirmed follow-up links `project-operating-rulebook` capability to new typed policy `project-operating-rulebook-policy`, closing the source-host retire-readiness blocker.
- User-confirmed follow-up retires rulebook canonical semantics non-destructively: `lazy rules` remains compatibility/advisory, but JSON outputs identify typed policies as semantic authority.
- User-confirmed 2026-07-13 follow-up adds `primary-canonical-record` at `recommend` level: candidate enumeration stays lossless, one primary narrative record is the default, additional layers require an independent semantic delta, and repeated validation detail uses one evidence capsule.
- User-confirmed follow-up adds block runtime readiness as preflight only; it validates promotion evidence and fixtures without installing lifecycle hard-stop hooks.
- User-confirmed follow-up adds first block-level policy `validation-evidence-block`; readiness passes, but lifecycle hard-stop hook installation is still deferred.
- User-confirmed follow-up adds dry-run block runtime helper for review-only STOP/ALLOW/BYPASS output.
- User-confirmed follow-up wires the dry-run block helper into `response.completed` / `lifecycle-check.py` as fail-open review output; blocking hook behavior is still deferred.
- Block enforcement still needs separate promotion evidence, TDD, bypass behavior, and explicit confirmation.
- Generated/explain views are derived output and must not become canonical truth.

## 2026-07-13 typed policy addition — primary canonical record

`primary-canonical-record` is a framework-global, turn-stage, recommend-level typed policy in `.lazy-harness/ssot/policies.json`. It has no hard-stop runtime and no capability binding requirement at this level. Its source/evidence paths are framework assets distributed to downstream hosts. The policy write/sync fixture audits the portable framework-seed + fixture-policy subset after sync; arbitrary host-local policies may cite host-owned records outside the framework manifest and are preserved but excluded from this portability audit.

Rollback remains demotion to `discover` if dogfood shows that the default hides independent layer changes or is misread as a hard one-file cap.

## Migration posture

This ADR does not delete `.lazy-harness/rules/**`. Migration should happen in slices:

1. Add typed policy registry, schema, read-only CLI, and tests.
2. Link capabilities to policy ids.
3. Add advisory-only resolver for `discover`/`recommend`/`default` policy levels.
4. Add explicit-context warn-only runtime for warn-level policy records.
5. Generate or explain rulebook views from typed policy records.
6. Validate policy write/save round-trip: upsert → audit → resolve → warn/render → sync merge.
7. Add retire-readiness preflight for active rulebook entries: rulebook entry → capability → typed policy coverage.
8. Retire hand-maintained rulebook canonical semantics after readiness proof by marking `lazy rules` as compatibility/advisory and keeping typed policies canonical.
9. Prepare block runtime only through readiness/preflight first; lifecycle hard-stop installation remains a later explicitly confirmed slice.
10. Add one narrow readiness-complete block policy before lifecycle integration: `validation-evidence-block`.
11. Add dry-run hard-stop runtime helper before blocking lifecycle integration.
12. Wire dry-run helper into lifecycle as fail-open review output; do not install blocking behavior yet.

## Implementation map

- Status: `option-b-active; primary-canonical-record recommend policy added`
- Primary records:
  - `.lazy-harness/decisions/0046-policy-machinery-typed-policy-canonical.md`
  - `.lazy-harness/spec/platform/policy-machinery-v2.md`
  - `.lazy-harness/ssot/policy-registry.md`
  - `.lazy-harness/tests/policy-machinery-v2.md`
- Primary files:
  - `.lazy-harness/ssot/policies.json` — canonical registry including `primary-canonical-record`.
  - `.lazy-harness/schemas/policies.schema.json`
  - `.lazy-harness/scripts/policy.ts`
  - `.lazy-harness/bin/lazy`
  - `.lazy-harness/scripts/self-test.py`
- Validation:
  - `lazy policy audit --format=json`
  - `lazy policy resolve --stage turn --applies-to making_validation_claims --format=json`
  - `lazy policy resolve --runtime warn --stage turn --applies-to making_validation_claims --format=json`
  - `lazy policy render-rulebook --write --format=json`
  - `lazy policy upsert --from-json <policy.json> --confirm --format=json`
  - `lazy policy retire-readiness --format=json`
  - `lazy policy retire-readiness --strict --format=json`
  - `lazy policy explain --id record-first-validation --format=md`
  - `lazy policy explain --id primary-canonical-record --format=md`
  - `lazy policy resolve --stage turn --applies-to writing_canonical_record --format=json`
  - `lazy rules list --format=json`
  - `lazy rules resolve --intent adding_project_operating_policy --format=json`
  - `lazy policy block-readiness --format=json`
  - `lazy policy block-readiness --strict --format=json`
  - `.lazy-harness/hooks/lifecycle/helpers/check-policy-block-runtime.py <payload-json>`
  - `python3 .lazy-harness/scripts/self-test.py --scope framework`
  - `.lazy-harness/bin/lazy test`

## Rule placement

- Rule: Policy Machinery V2 option B makes typed policy records the canonical source for project/team behavior policy; markdown rulebook becomes compatibility/generated/explain surface during migration.
- Scope: framework-global
- Primary record: `.lazy-harness/decisions/0046-policy-machinery-typed-policy-canonical.md`
- Why not AGENTS.md: this is a storage and architecture decision, not prompt grammar.
- Why not `.jcode`: shared framework/project policy must sync across hosts; `.jcode` is local/private wiring.
- Confirmation: user-confirmed
