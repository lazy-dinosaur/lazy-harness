# Generated Policy Rulebook

> GENERATED VIEW, NON-CANONICAL.
> Canonical behavior policy source: `.lazy-harness/ssot/policies.json`.
> Regenerate with: `.lazy-harness/bin/lazy policy render-rulebook --write`.

This file explains typed behavior policies for humans/LLMs. Do not edit it as source of truth.

## Summary

- Policy count: 5
- Canonical source: `.lazy-harness/ssot/policies.json`
- Generated/explain view only: yes

| Policy | Level | Stage | Runtime | Summary |
|---|---|---|---|---|
| `framework-co-change-completeness` | discover | turn | advisory-only | Before closing a framework change, enumerate referencing skills/prompts/extension/help/parser surfaces (grep the changed command/flag/contract name under packages/ and bin/) and update them in the same change. |
| `project-operating-rulebook-policy` | discover | turn | advisory-only | When adding or resolving project/team operating behavior policy, keep human-readable rulebook compatibility surfaces and machine-readable capability bindings linked to typed policy records. |
| `record-first-validation` | discover | turn | advisory-only | Before claiming validation is complete, attach or summarize concrete validation evidence from canonical records/tests. |
| `validation-evidence-block` | block | turn | block (not implemented by current runtime) | Prepare a narrow block boundary for validation-complete claims made without record/test evidence. This policy is ready for block runtime, but no lifecycle hook is installed in this slice. |
| `validation-evidence-warning` | warn | turn | warn-only (explicit policy_context required) | When structured policy context says the agent is making validation claims, warn if concrete validation evidence should be attached or summarized. |

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
- Runtime: block (not implemented by current runtime)
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
