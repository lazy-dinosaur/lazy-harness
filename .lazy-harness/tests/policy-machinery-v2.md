# TDD — Policy Machinery V2

Status: active-regression
Layer: TDD
Related SDD: `.lazy-harness/spec/platform/policy-machinery-v2.md`
Related fixture: `.lazy-harness/fixtures/policy-machinery-v2/example-policy.json`
Related roadmap: `.lazy-harness/planning/lazy-harness-v2-implementation-roadmap.md#phase-3--unify-rulebook--capability-registry-into-policy-machinery`

## Rule digest

- Status: active-regression / Phase 3 record-first slice
- Scope: framework-global
- Applies when:
  - editing Policy Machinery V2 records or fixture
  - changing rulebook/capability/update-loop integration
  - preparing Phase 3 runtime/schema work
- Must:
  - validate the Phase 3 policy packet fixture
  - prove Policy Machinery V2 stays contract/static-only in this slice
  - prove the hybrid rulebook + capability stores remain intact until an option gate changes them
  - prove policy packets use update-loop evidence without becoming canonical truth by themselves
- Must not:
  - add hook enforcement or schema rewrite as part of this static slice
  - allow forbidden semantic-authority fields in policy fixture output
  - let `block` appear in the fixture without explicit confirmation and bypass/rollback evidence
- Record completion:
  - Phase 3 runtime/schema work must add focused tests before changing implementation.

## Regression cases

| Case | Evidence | Expected |
|---|---|---|
| `policy_machinery_contract_files` | SDD/TDD/audit/fixture | All Phase 3 record-first files exist and are synced by manifest. |
| `policy_machinery_fixture_shape` | `example-policy.json` | Fixture schema is `policy-machinery-v2/v1`, stage/level are controlled vocabulary, sourceRecord is root-relative, and updateLoop cannot canonicalize by packet alone. |
| `policy_machinery_no_semantic_authority_fields` | recursive fixture scan | Fixture contains no confidence/intent/risk/requiredRead/nextAction/candidateMeaning fields. |
| `policy_machinery_hybrid_storage_preserved` | SDD + fixture | Rulebook and capability registry stay linked; storage replacement remains an option gate. |
| `policy_machinery_no_runtime_enforcement` | SDD/TDD text | Static slice does not add hook enforcement, warn/block runtime, or schema replacement. |

## Layer completeness gate

- DDD: no domain/business rule impact.
- SDD: `.lazy-harness/spec/platform/policy-machinery-v2.md`.
- BDD: agent guidance remains advisory unless a future confirmed policy level explicitly changes behavior.
- SSOT: `.lazy-harness/ssot/capability-registry.md` stays canonical for kind/level semantics.
- ADR: no new decision is made; rulebook storage options remain open.

## Implementation map

- Status: `phase-3-record-first-contract`
- Records:
  - `.lazy-harness/spec/platform/policy-machinery-v2.md`
  - `.lazy-harness/planning/policy-machinery-v2-baseline-gap-audit.md`
  - `.lazy-harness/tests/policy-machinery-v2.md`
- Fixture:
  - `.lazy-harness/fixtures/policy-machinery-v2/example-policy.json`
- Source/test:
  - `.lazy-harness/scripts/self-test.py#check_policy_machinery_v2`
  - `.lazy-harness/manifests/init-categories.json`
- Validation:
  - `python3 .lazy-harness/scripts/self-test.py --scope framework`
  - `.lazy-harness/bin/lazy test`

## Rule placement

- Layer: TDD.
- Why: this record defines regression protection for the Policy Machinery V2 static contract slice.
