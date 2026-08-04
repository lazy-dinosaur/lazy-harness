# TDD — Jcode Typed Review Routing

Status: accepted
Date: 2026-08-04
Layer: TDD
Related SDD: `.lazy-harness/spec/platform/jcode-typed-review-routing.md`

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Confidence: high
- Aliases:
  - typed reviewer route regression
  - Oracle max route fixture
- Surface terms:
  - `[reviewer]` GPT-5.6 Sol high
  - `[oracle]` GPT-5.6 Sol max
  - reject GPT-5.5
- Applies when:
  - changing typed Jcode review routing or policy portability
- Must:
  - prove approved reviewer and Oracle routes are allowed
  - prove GPT-5.5 and incorrect effort are denied
  - prove untyped roles remain outside the guard
  - prove demoting the typed routing policy stops the runtime block
- Must not:
  - require network access for the static fixture
- Record completion:
  - update with routing helper or policy changes
- Related records:
  - `.lazy-harness/spec/platform/jcode-typed-review-routing.md`

## Regression contract

`.lazy-harness/scripts/self-test.py#check_jcode_agent_adapter` exercises the structured helper directly:

- allow `[reviewer]` + GPT-5.6 Sol + high
- allow `[oracle]` + GPT-5.6 Sol + max
- deny GPT-5.5 for either typed role
- deny reviewer medium and Oracle high
- allow untyped worker labels to pass without routing enforcement
- demote the policy to `recommend` and prove the helper becomes silent without adapter/hook changes

The policy source and fixture paths are synced framework assets so `lazy policy audit` and `lazy policy block-readiness --strict` remain valid on downstream hosts.

## Layer completeness matrix

| Layer | Independent semantic delta? | Judgement |
|---|---:|---|
| DDD | No | No domain vocabulary changed. |
| SDD | Yes | Portable typed routing contract added. |
| BDD | No | No product behavior changed. |
| SSOT | Yes | Existing typed policy/capability records now reference portable dependencies. |

## Implementation map

- Status: `implemented-policy-rollback-covered`
- Test implementation: `.lazy-harness/scripts/self-test.py#check_jcode_agent_adapter`
- Protected implementation: `.lazy-harness/hooks/lifecycle/helpers/check-agent-model-routing.py`
- Cross-layer link: `.lazy-harness/spec/platform/jcode-typed-review-routing.md`
- Machine index: `kg_jcode_typed_review_routing_test_20260803`

## Discovery capture

- Primary canonical record: this TDD owns routing regression portability.
- DDD/BDD: no independent delta.
- SDD/SSOT: independent portable contract and registry dependency repair.
- ADR/Planning: no additional delta.
