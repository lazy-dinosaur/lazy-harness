# TDD — Code Organization Profile

Status: active-pilot
Date: 2026-07-20
Layer: TDD
Related SDD: `.lazy-harness/spec/platform/code-organization-profile.md`
Related ADR: `.lazy-harness/decisions/0054-three-layer-cross-stack-architecture-guidance.md`

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Aliases:
  - code organization regression
  - changed-source profile test
  - 코드 정돈 회귀
- Applies when:
  - changing Profile v1 semantics, policy/capability bindings, or source-touch reminders
  - promoting any mechanical code-organization observation toward warn or block
- Must:
  - prove source touches surface observe-only guidance
  - prove non-source touches do not add source-adaptation guidance
  - prove a host-only source policy/capability is resolved and surfaced from canonical registries
  - prove policy/capability resolution remains recommend/advisory-only
  - prove system architecture inference and bulk rewrite stay forbidden
- Must not:
  - accept line-count splitting, automatic profile inference, or hard-stop promotion
- Record completion:
  - profile implementation changes update this TDD and the four-layer judgement
- Related records:
  - `.lazy-harness/spec/platform/code-organization-profile.md`
  - `.lazy-harness/spec/platform/guidance-ladder.md`
  - `.lazy-harness/spec/platform/pi-agent-package.md`

## Regression matrix

| Case | Trigger | Expected |
|---|---|---|
| `code_org_profile_contract_files` | inspect SDD/TDD/ADR/AGENTS/runtime files | all canonical pointers and observe-only boundaries exist |
| `code_org_profile_policy_resolve` | resolve `reviewing_code_organization` at edit stage | `code-organization-profile` resolves as `recommend` and `advisory-only` |
| `code_org_profile_capability_resolve` | resolve `reviewing_code_organization` intent | `code-organization-review` is available as a recommend checklist |
| `code_org_profile_source_touch` | run `on-context.sh` with a touched source path and mechanical edit tool label | reminder resolves framework source guidance through canonical policy/capability surfaces |
| `code_org_profile_host_adaptation` | run the hook in a minimal temp host with a host-only `modifying_source_file` policy/capability | injected guidance includes the host ids, source record, summary, and action without framework hardcoding |
| `code_org_profile_non_source_touch` | run `on-context.sh` with only a `.md` record path | generic catalog remains available but no source-adaptation block is injected |
| `code_org_profile_manifest_distribution` | inspect Category A manifest | SDD and TDD records are distributed to hosts |
| `code_org_profile_no_enforcement` | inspect policy, runtime reminder, and SDD | no warn/block level, AST/lint gate, line threshold, or bulk rewrite |
| `code_org_profile_architecture_separation` | inspect SDD and ADR 0054 amendment | local organization cannot confirm a Host Architecture Map or named architecture |

## Protection boundary

The fixture protects guidance delivery and policy level, not a universal source-code style. It deliberately does not grade current repository files, require an existing host to conform, or treat Goedamjip's folder tree as an oracle. The temp-host case proves the adaptation bridge with host-owned registry entries rather than asserting that the framework baseline is the only valid profile.

A future mechanical rule needs its own positive/negative fixture and observe-stage false-positive evidence before this matrix may mention warn behavior.

## Layer completeness

| Layer | Independent delta | Judgement |
|---|---|---|
| SDD | yes | `.lazy-harness/spec/platform/code-organization-profile.md` defines Profile v1 and observe-stage runtime behavior. |
| BDD | no | No product-visible user flow changes; agent review behavior is covered by the platform contract. |
| SSOT | yes | Typed policy/capability registry entries bind the recommend-only review behavior; no prose SSOT is needed. |
| DDD | no | No business term, entity, or invariant is introduced. |

ADR impact: ADR 0054 is amended because separating local code organization from system architecture is an independent design boundary.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/tests/code-organization-profile.md` — regression contract.
  - `.lazy-harness/scripts/self-test.py` — executable focused assertions.
  - `.lazy-harness/hooks/lifecycle/on-context.sh` — tool-label-to-source-intent context transport.
  - `.lazy-harness/hooks/lifecycle/helpers/operating_rule_catalog.py` — canonical resolver output rendering for framework and host-project matches.
  - `.lazy-harness/ssot/policies.json` — recommend policy fixture.
  - `.lazy-harness/ssot/capabilities.json` — checklist capability fixture.
- Key symbols:
  - `check_code_organization_profile` (`.lazy-harness/scripts/self-test.py`) — validates the complete observe-only slice.
- Flow:
  1. Self-test verifies canonical records and manifest distribution.
  2. It resolves typed policy/capability entries.
  3. It runs source, host-only source-policy, and non-source context payloads.
  4. It rejects any accidental warn/block or architecture-inference wording.
- Tests / protection:
  - `.lazy-harness/scripts/self-test.py#check_code_organization_profile` — includes a minimal temp-host registry canary.
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/code-organization-profile.md`
  - ADR: `.lazy-harness/decisions/0054-three-layer-cross-stack-architecture-guidance.md`, `.lazy-harness/decisions/0048-operating-rule-storage-apply-repair.md`
  - SSOT: `.lazy-harness/ssot/policies.json`, `.lazy-harness/ssot/capabilities.json`
- Machine index:
  - graph id: `kg_code_organization_profile_test_20260720`

## Rule placement

- Rule: Profile v1 changes require source/non-source context fixtures and recommend-only policy/capability resolution.
- Scope: framework-global.
- Primary record: `.lazy-harness/tests/code-organization-profile.md`.
- Confirmation: user selected the Code Organization Profile track and then the recommended host adaptation bridge on 2026-07-20.

## Discovery capture

- DDD: no independent delta.
- SDD: protected by the primary Profile v1 contract, including host-resolved source guidance.
- BDD: no independent delta.
- TDD: this record owns the regression matrix.
- ADR: two-track separation is linked to ADR 0054.
- SSOT: registry entries are covered without a duplicate prose record.
- Planning: warn/block and mechanical-rule promotion remain deferred.
