# Generated Policy Rulebook

> GENERATED VIEW, NON-CANONICAL.
> Canonical behavior policy source: `.lazy-harness/ssot/policies.json`.
> Regenerate with: `.lazy-harness/bin/lazy policy render-rulebook --write`.

This file explains typed behavior policies for humans/LLMs. Do not edit it as source of truth.

## Summary

- Policy count: 9
- Canonical source: `.lazy-harness/ssot/policies.json`
- Generated/explain view only: yes

| Policy | Level | Stage | Runtime | Summary |
|---|---|---|---|---|
| `bounded-validation-orchestration` | recommend | turn | advisory-only | Do not validate after each micro-edit. Batch a coherent mutation set, run lazy check at a deliberate checkpoint, run focused or affected validation once per changed-behavior batch when needed, then run one lazy validate --plan standard after the final mutation. Direct lazy test remains explicit fresh full regression or commit/push/release only. |
| `code-organization-profile` | recommend | edit | advisory-only | Review only new or modified source for local coherence, narrowing ownership, lifecycle clarity, and duplicate authority. Do not infer system architecture, split by line count, or rewrite untouched code. |
| `framework-co-change-completeness` | discover | turn | advisory-only | Before closing a framework change, enumerate referencing skills/prompts/extension/help/parser surfaces (grep the changed command/flag/contract name under packages/ and bin/) and update them in the same change. |
| `jcode-typed-review-model-routing` | block | turn | block (typed-agent-routing configured; verify installation with block-readiness) | Use [reviewer] with GPT-5.6 Sol high and [oracle] with GPT-5.6 Sol max. GPT-5.5 is rejected for both typed review roles. |
| `primary-canonical-record` | recommend | turn | advisory-only | Choose one primary canonical narrative record by default. Promote another layer only for an independent semantic delta; otherwise link it or record no independent delta. Consolidate durable repeated validation detail into one evidence capsule. |
| `project-operating-rulebook-policy` | discover | turn | advisory-only | When adding or resolving project/team operating behavior policy, keep human-readable rulebook compatibility surfaces and machine-readable capability bindings linked to typed policy records. |
| `record-first-validation` | discover | turn | advisory-only | Before claiming validation is complete, attach or summarize concrete validation evidence from canonical records/tests. |
| `validation-evidence-block` | block | turn | block (readiness/preflight only; no lifecycle runtime declared) | Prepare a narrow block boundary for validation-complete claims made without record/test evidence. This policy is ready for block runtime, but no lifecycle hook is installed in this slice. |
| `validation-evidence-warning` | warn | turn | warn-only (explicit policy_context required) | When structured policy context says the agent is making validation claims, warn if concrete validation evidence should be attached or summarized. |

## bounded-validation-orchestration

- Title: Prefer bounded validation and one final full-regression boundary
- Scope: framework-global
- Stage: turn
- Level: recommend
- Runtime: advisory-only
- Source record: `.lazy-harness/spec/platform/bounded-validation-governor.md`
- Capabilities: bounded-validation-orchestration
- Summary: Do not validate after each micro-edit. Batch a coherent mutation set, run lazy check at a deliberate checkpoint, run focused or affected validation once per changed-behavior batch when needed, then run one lazy validate --plan standard after the final mutation. Direct lazy test remains explicit fresh full regression or commit/push/release only.

### Applies to
- choosing_validation_scope
- making_validation_claims
- closing_non_trivial_work_unit
- before_commit_or_sync

### Evidence
- user-confirmation: User approved the full validation-churn improvement on 2026-07-23 after repeated host lazy test runs consumed roughly 147 seconds each.
- record `.lazy-harness/spec/platform/bounded-validation-governor.md`: The bounded governor defines fast edit-loop checks, one standard full-regression boundary, release opt-in, and conservative evidence reuse.

### Promotion / rollback
- Requires confirmation: true
- Allowed target levels: discover, recommend, warn
- Rollback target: discover
  - Agents under-validate source, test, hook, schema, or contract changes.
  - The recommendation obscures an explicit user request for fresh full regression.

## code-organization-profile

- Title: Review changed source with the Code Organization Profile
- Scope: framework-global
- Stage: edit
- Level: recommend
- Runtime: advisory-only
- Source record: `.lazy-harness/spec/platform/code-organization-profile.md`
- Capabilities: code-organization-review
- Summary: Review only new or modified source for local coherence, narrowing ownership, lifecycle clarity, and duplicate authority. Do not infer system architecture, split by line count, or rewrite untouched code.

### Applies to
- creating_source_file
- modifying_source_file
- reviewing_code_organization
- extracting_shared_code

### Evidence
- user-confirmation: User selected the Code Organization Profile track and requested implementation on 2026-07-20, with system architecture kept separate and no bulk rewrite.
- record `.lazy-harness/spec/platform/code-organization-profile.md`: Profile v1 defines domain-shape continuity, local chronological coherence, narrowing ownership, explicit lifecycle vocabulary, delayed extraction, and changed-surface-only review.
- validation-output `.lazy-harness/tests/code-organization-profile.md`: Regression contract protects recommend-only resolution, source-touch context, architecture separation, and no enforcement.

### Promotion / rollback
- Requires confirmation: true
- Allowed target levels: discover, recommend, warn
- Rollback target: discover
  - Changed-source review produces noisy or generic advice.
  - The profile starts inferring system architecture or prescribing folder taxonomies.

## framework-co-change-completeness

- Title: Framework surface changes co-update all referencing distributed artifacts
- Scope: framework-global
- Stage: turn
- Level: discover
- Runtime: advisory-only
- Source record: `.lazy-harness/spec/platform/pi-agent-package.md`
- Summary: Before closing a framework change, enumerate referencing skills/prompts/extension/help/parser surfaces (grep the changed command/flag/contract name under packages/ and bin/) and update them in the same change.

### Applies to
- changing_framework_cli_surface
- renaming_or_removing_cli_flags_or_formats
- changing_shared_contract_or_schema
- closing_framework_change_with_dependent_artifacts

### Evidence
- user-confirmation: User-confirmed operating rule 2026-07-05: when the framework changes, all related skills/prompts/help/parsers must be updated in the same change so downstream updates land consistent.
- validation-output `.lazy-harness/spec/platform/pi-agent-package.md`: Record completion CO-CHANGE COMPLETENESS clause lists the artifact classes; precedent defects jcode-prompt rename and init --target= help/parser drift fixed in 5d88a31.

### Promotion / rollback
- Requires confirmation: true
- Allowed target levels: discover, recommend, warn
- Rollback target: discover
  - Co-change checklist proves noisy for changes with no distributed references.

## jcode-typed-review-model-routing

- Title: Route typed Jcode review roles through GPT-5.6 Sol
- Scope: framework-global
- Stage: turn
- Level: block
- Runtime: block (typed-agent-routing configured; verify installation with block-readiness)
- Source record: `.lazy-harness/spec/platform/jcode-typed-review-routing.md`
- Capabilities: jcode-typed-review-model-routing
- Summary: Use [reviewer] with GPT-5.6 Sol high and [oracle] with GPT-5.6 Sol max. GPT-5.5 is rejected for both typed review roles.

### Applies to
- spawning_typed_jcode_reviewer
- spawning_typed_jcode_oracle
- delegating_high_risk_code_review

### Evidence
- user-confirmation: User confirmed GPT-5.6 Sol high for normal reviewers and max for Oracle on 2026-08-03.
- record `.lazy-harness/spec/platform/jcode-typed-review-routing.md`: Portable SDD defines exact typed labels, GPT-5.6 Sol routes, and the promoted structured spawn boundary.
- validation-output `.lazy-harness/tests/jcode-typed-review-routing.md`: Portable TDD records approved and rejected typed reviewer and Oracle routes.

### Promotion / rollback
- Requires confirmation: true
- Allowed target levels: block
- Rollback target: recommend
  - Typed label routing blocks valid GPT-5.6 Sol reviewer or Oracle workers.
  - The structured role convention creates material review-routing ambiguity.

## primary-canonical-record

- Title: Prefer one primary canonical record per logical work unit
- Scope: framework-global
- Stage: turn
- Level: recommend
- Runtime: advisory-only
- Source record: `.lazy-harness/spec/platform/record-write-update-policy.md`
- Summary: Choose one primary canonical narrative record by default. Promote another layer only for an independent semantic delta; otherwise link it or record no independent delta. Consolidate durable repeated validation detail into one evidence capsule.

### Applies to
- writing_canonical_record
- updating_cross_layer_records
- closing_logical_work_unit
- recording_repeated_validation_evidence

### Evidence
- user-confirmation: User selected the guard → sample-cleanup rollout on 2026-07-13 after reviewing Medivance record write amplification.
- record `.lazy-harness/spec/platform/record-write-update-policy.md`: The synced write/update contract defines one primary narrative record, independent-delta exceptions, and one durable evidence location.
- record `.lazy-harness/spec/platform/layer-completeness-gate.md`: The synced completeness contract defines impact judgement rather than layer mirroring and keeps semantic-delta judgement LLM-owned.
- record `.lazy-harness/tests/record-decision-broker.md`: The synced TDD contract protects lossless candidate review without automatic multi-record promotion.

### Promotion / rollback
- Requires confirmation: true
- Allowed target levels: discover, recommend
- Rollback target: discover
  - Dogfood shows the primary-record default hides an independently changed layer.
  - Agents treat the recommendation as a hard one-file cap instead of an independent-delta test.

## project-operating-rulebook-policy

- Title: Project operating rulebook policy
- Scope: framework-global
- Stage: turn
- Level: discover
- Runtime: advisory-only
- Source record: `.lazy-harness/spec/platform/project-operating-rulebook.md`
- Capabilities: project-operating-rulebook
- Summary: When adding or resolving project/team operating behavior policy, keep human-readable rulebook compatibility surfaces and machine-readable capability bindings linked to typed policy records.

### Applies to
- adding_project_operating_policy
- resolving_project_operating_rule
- inspecting_project_rules
- distinguishing_project_facts_from_operating_rules

### Evidence
- record `.lazy-harness/rules/README.md`: Active rulebook compatibility surface defines project operating rule storage and capability binding.
- record `.lazy-harness/spec/platform/project-operating-rulebook.md`: SDD defines lazy rules contract, rulebook entry shape, capability binding, and audit behavior.
- record `.lazy-harness/tests/project-operating-rulebook.md`: TDD protects rulebook list/audit/resolve behavior and sync compatibility.
- record `.lazy-harness/ssot/policy-registry.md`: Policy registry SSOT requires rulebook retire-readiness coverage through typed policy links before changing rulebook semantics.

### Promotion / rollback
- Requires confirmation: true
- Allowed target levels: discover, recommend
- Rollback target: discover
  - Rulebook compatibility surface no longer represents project/team operating policy storage.
  - Capability-policy link causes noisy or incorrect retire-readiness coverage.

## record-first-validation

- Title: Record-first validation evidence
- Scope: framework-global
- Stage: turn
- Level: discover
- Runtime: advisory-only
- Source record: `.lazy-harness/spec/platform/policy-machinery-v2.md`
- Capabilities: lazy-evidence-capsule
- Summary: Before claiming validation is complete, attach or summarize concrete validation evidence from canonical records/tests.

### Applies to
- closing_non_trivial_work_unit
- making_validation_claims

### Evidence
- record `.lazy-harness/spec/platform/evidence-capsule-standard.md`: Existing evidence capsule capability is recommend-level and manual.
- update-event `.lazy-harness/spec/platform/project-map-update-loop-v2.md`: Policy changes must use update-loop candidate/canonical transition semantics.

### Promotion / rollback
- Requires confirmation: true
- Allowed target levels: discover, recommend
- Rollback target: discover
  - Evidence capsule recommendation becomes noisy or not useful in dogfood validation.
  - A stronger level is requested without user/team confirmation.

## validation-evidence-block

- Title: Block validation-complete claims without evidence
- Scope: framework-global
- Stage: turn
- Level: block
- Runtime: block (readiness/preflight only; no lifecycle runtime declared)
- Source record: `.lazy-harness/spec/platform/policy-machinery-v2.md`
- Capabilities: lazy-evidence-capsule
- Summary: Prepare a narrow block boundary for validation-complete claims made without record/test evidence. This policy is ready for block runtime, but no lifecycle hook is installed in this slice.

### Applies to
- claiming_validation_complete_without_evidence
- closing_non_trivial_work_unit_without_record_or_test_evidence

### Evidence
- user-confirmation: User confirmed proceeding with the first level=block policy promotion readiness slice on 2026-06-18.
- validation-output `.lazy-harness/tests/policy-block-validation-evidence.md`: TDD fixture documents allow/block cases and protects block-readiness without lifecycle hook installation.
- record `.lazy-harness/spec/platform/guidance-ladder.md`: Guidance Ladder requires hard stops to be narrow, reversible, fixture-protected, and user-confirmed.
- record `.lazy-harness/ssot/policy-registry.md`: Policy Registry SSOT requires block-readiness before lifecycle hard-stop integration.

### Promotion / rollback
- Requires confirmation: true
- Allowed target levels: block
- Rollback target: recommend
  - The block boundary is too broad or noisy in dogfood use.
  - The runtime fixture fails to cover both allow and block cases.
  - A lifecycle integration slice cannot preserve explicit-context and bypass behavior.

## validation-evidence-warning

- Title: Warn when validation evidence is missing
- Scope: framework-global
- Stage: turn
- Level: warn
- Runtime: warn-only (explicit policy_context required)
- Source record: `.lazy-harness/spec/platform/policy-machinery-v2.md`
- Capabilities: lazy-evidence-capsule
- Summary: When structured policy context says the agent is making validation claims, warn if concrete validation evidence should be attached or summarized.

### Applies to
- making_validation_claims

### Evidence
- record `.lazy-harness/ssot/policy-registry.md`: Warn-only runtime requires explicit structured policy context and never blocks.
- record `.lazy-harness/tests/policy-machinery-v2.md`: TDD protects warn-only runtime output, bypass guidance, and no block behavior.

### Promotion / rollback
- Requires confirmation: true
- Allowed target levels: warn
- Rollback target: recommend
  - Warn-only runtime emits noisy warnings for explicit structured policy context.
  - A warning output suppresses a more important blocking helper in response.completed.
