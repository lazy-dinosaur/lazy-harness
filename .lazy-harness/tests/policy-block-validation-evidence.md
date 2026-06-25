# TDD — Validation Evidence Block Policy

Status: active-regression
Layer: TDD
Date: 2026-06-18
Related SDD: `.lazy-harness/spec/platform/policy-machinery-v2.md`
Related SSOT: `.lazy-harness/ssot/policy-registry.md`
Related policy: `validation-evidence-block`

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Applies when:
  - promoting the validation-evidence boundary to `level=block`
  - checking `lazy policy block-readiness --strict`
  - checking `check-policy-block-runtime.py` dry-run STOP/ALLOW/BYPASS behavior
  - ensuring no blocking lifecycle hook is installed by readiness or dry-run review alone
- Must:
  - prove the block policy has user confirmation, validation output, runtime fixture, bypass, and rollback evidence
  - prove the block policy is narrow: validation-complete claims without evidence only
  - prove `block-readiness` can become ready without lifecycle mutation
  - prove dry-run runtime review can distinguish missing evidence, attached evidence, bypass, and irrelevant raw text
- Must not:
  - install a lifecycle hard-stop hook
  - block generic assistant text or raw user text classification
  - replace the existing warn-only validation policy

## Fixture intent

This file is the concrete runtime fixture evidence for the first Policy Machinery `level=block` policy.

The intended block boundary is narrow:

```text
claiming_validation_complete_without_evidence
```

Allow cases:

```text
claiming_validation_complete_with_evidence
summarizing_work_without_validation_claim
reporting_block_readiness_preflight_only
```

Block cases:

```text
claiming_validation_complete_without_evidence
closing_non_trivial_work_unit_without_record_or_test_evidence
```

The readiness slice only proves readiness. The dry-run helper slice proves review output. The dry-run lifecycle integration slice connects review-only output to the helper chain, but it still does not install a blocking lifecycle hook.

## Regression assertions

- `lazy policy block-readiness --strict --format=json` passes when `validation-evidence-block` is present and complete.
- The result still reports `hardStopHookInstalled=false` and `lifecycleMutation=false`.
- `check-policy-block-runtime.py` emits `DRY-RUN STOP` for explicit structured block context without validation evidence.
- `check-policy-block-runtime.py` emits `DRY-RUN ALLOW` when validation evidence is attached.
- `check-policy-block-runtime.py` emits `DRY-RUN BYPASS` when acknowledged block id and bypass reason are present.
- `check-policy-block-runtime.py` stays silent for raw user/assistant text and for structured context without `blockRuntimeDryRun`.
- `response.completed` and `lifecycle-check.py` surface DRY-RUN STOP only for explicit structured dry-run payloads.
- Removing `runtime.fixture` or the hard-stop promotion section makes strict readiness fail.
- `lazy policy resolve` remains advisory/warn behavior only unless a later explicit lifecycle-integration slice is approved.

## Implementation map

- Primary source:
  - `.lazy-harness/ssot/policies.json` — contains `validation-evidence-block`.
  - `.lazy-harness/spec/platform/policy-machinery-v2.md` — contains the `## Hard-stop promotion` section for the validation-evidence boundary.
  - `.lazy-harness/scripts/policy.ts` — implements `lazy policy block-readiness`.
  - `.lazy-harness/hooks/lifecycle/helpers/check-policy-block-runtime.py` — implements dry-run block runtime review output only.
  - `.lazy-harness/hooks/lifecycle/on-response-completed.sh` — invokes the dry-run helper in response.completed helper order.
  - `.lazy-harness/scripts/lifecycle-check.py` — mirrors the dry-run helper in shadow/sandbox helper order.
  - `.lazy-harness/scripts/self-test.py` — protects the source-host ready case and negative fixture cases.
- Protection:
  - `.lazy-harness/bin/lazy policy block-readiness --strict --format=json`
  - `.lazy-harness/hooks/lifecycle/helpers/check-policy-block-runtime.py '{"policy_context":{"blockRuntimeDryRun":true,...}}'`
  - `python3 .lazy-harness/scripts/hard-stop-promotion-audit.py --strict --format json`
  - `.lazy-harness/bin/lazy test`
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/policy-machinery-v2.md`
  - SSOT: `.lazy-harness/ssot/policy-registry.md`
  - ADR: `.lazy-harness/decisions/0046-policy-machinery-typed-policy-canonical.md`

## Layer completeness

- DDD: no domain vocabulary change.
- SDD: Policy Machinery V2 hard-stop promotion boundary updated.
- BDD: no UI/user flow change; agent lifecycle integration is still future work.
- TDD: this record plus `self-test.py#check_policy_machinery_v2` protect readiness.
- ADR: ADR 0046 records block policy promotion readiness.
- SSOT: policy registry records block-readiness semantics.
