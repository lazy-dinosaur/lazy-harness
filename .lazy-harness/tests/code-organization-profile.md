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
  - prove source-work guidance remains available through explicit canonical policy/capability resolution
  - prove pointer-only context does not inject source-adaptation guidance after reads
  - prove host-only source policy/capability entries remain resolvable from canonical registries without framework hardcoding
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
| `code_org_profile_explicit_resolution` | resolve the immediate source-work intent once before a coherent mutation batch | framework and host registry matches remain available as recommend/advisory-only guidance |
| `code_org_profile_pointer_context` | run `on-context.sh` after a read-only source touch | body stays pointer-only and contains no source profile, host ids, catalog, or resolver result |
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
  - `.lazy-harness/hooks/lifecycle/on-context.sh` — pointer-only mutation-boundary reminder that deliberately does not resolve or inject source guidance.
  - `.lazy-harness/hooks/lifecycle/helpers/operating_rule_catalog.py` — explicit canonical resolver rendering remains available to direct callers, not automatic context replay.
  - `.lazy-harness/ssot/policies.json` — recommend policy fixture.
  - `.lazy-harness/ssot/capabilities.json` — checklist capability fixture.
- Key symbols:
  - `check_code_organization_profile` (`.lazy-harness/scripts/self-test.py`) — validates the complete observe-only slice.
- Flow:
  1. Self-test verifies canonical records and manifest distribution.
  2. It resolves typed policy/capability entries explicitly.
  3. Pointer-only context is checked for absence of automatic profile/catalog replay.
  4. It rejects accidental warn/block or architecture-inference wording.
- Tests / protection:
  - `.lazy-harness/scripts/self-test.py#check_code_organization_profile` — verifies explicit recommend-only registry resolution and pointer-only context separation.
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
