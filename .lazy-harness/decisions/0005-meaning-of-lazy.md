# ADR 0005 — Meaning of "Lazy" in Lazy-Harness

**Date**: 2026-05-10
**Status**: Accepted
**Deciders**: Lazydino
**Trigger**: Conflict Resolution Protocol fired — AI used "lazy" as synonym for "minimal" in option D recommendation while user clarified that "lazy" refers to **developer** laziness, not framework laziness.

## Rule digest

- Status: needs-review
- Layer: ADR
- Scope: framework-global
- Applies when:
  - interpreting "lazy" during design or scope/size decisions
  - choosing between a minimal and a more complete framework option
- Must:
  - treat "lazy" as developer effort minimization, never framework minimalism
  - evaluate size choices by priority: completeness, consistency, user-laziness, automation, then initial cost
- Must not:
  - pick a minimal option on low initial cost alone
- Record completion:
  - changes to the lazy definition or size heuristic update this ADR and `.lazy-harness/framework/framework-contract.md`
- Related records:
  - `.lazy-harness/decisions/0001-core-philosophy.md`
  - `.lazy-harness/framework/framework-contract.md`

## Context

`lazy-harness` 라는 이름이 framework-contract 에 1 줄 정의 없이 박혀있었음. 이 세션에서 AI 가 옵션 D ("3 개 placeholder 만") 를 추천하며 "lazy 답게 시작하고 필요할 때 자라게" 라고 표현 → 사용자 (Lazydino) 즉시 정정:

> "내가 말하는 lazy 는 개발의 lazy 지 프레임워크는 당연히 완성도가 높고 탄탄해야해 이해하지??"

이 명시 없이 framework 가 진행되면, 미래에 또 다른 AI 세션에서 같은 잘못된 해석이 반복될 위험.

## Decision

framework-contract.md 의 `Section 0 Identity` 바로 아래에 두 개 sub-section 추가:

- **0.1 What "lazy" means (and does NOT mean)** — 의미 + 금지 해석 5 개
- **0.2 Decision-making heuristic for "size" choices** — 5 단계 priority

핵심:

```
lazy = developer effort minimization
NOT  = framework minimalism
```

옵션 평가 시:
1. 완성도 / 2. 일관성 / 3. 사용자 lazy / 4. 자동화 / 5. 초기 비용

→ "초기 비용 작음" 만 보고 minimal 선택은 #1, #2, #3 위반.

이 결정에 따라 직전 Conflict Resolution 의 "DDD/SDD/BDD/TDD 미러 map" 충돌 해소도 수정:

- AI 추천: ~~D (3 개 placeholder)~~ → **A (12 개 placeholder, full mirror)**
- 사용자 결정: A 채택 (이 ADR 직전)

## Consequences

### Positive

- 미래 AI 세션이 "lazy = minimal" 로 오독할 수 없음 (framework-contract 에 박혀있음)
- 옵션 평가 기준이 명시화 → Conflict Resolution Protocol 이 더 강력해짐
- DDD/SDD/BDD/TDD 균질성 보장 (lazy = full coverage of layers)

### Negative

- 초기 init script 가 더 무거워짐 (12 placeholder XML 추가) — 의도된 trade-off
- placeholder 가 진짜 데이터 들어올 때까지 빈 상태 → Empty-Container Tolerance (#10) 적용

### Cascade

| Document | 영향 |
|---|---|
| `framework/framework-contract.md` | Section 0.1 + 0.2 추가 (52 줄) |
| `decisions/0005-meaning-of-lazy.md` | 이 ADR |
| `logs/decisions.jsonl` | D-2026-05-10-002 (이 결정) + D-2026-05-10-001 (A 채택) |
| `scripts/init-lazy-harness.sh` | 12 placeholder XML 생성 추가 |
| `scripts/doctor.sh` | 12 placeholder 검증 추가 |
| `framework/framework-contract.md` Section 6.1 | DDD 패턴 SDD/BDD/TDD 로 미러 |

## References

- 직전 Conflict Resolution: 사용자 발언 "내가 말하는 lazy 는 개발의 lazy"
- Principle 0: 사람 + AI 한계 보완 (사람의 lazy = AI 의 무거운 자동화)
- Principle #6: Trigger-Based Growth (이 ADR 자체가 trigger 발동 결과)
- Principle #17: Conflict Resolution Protocol (이 ADR 의 motivating protocol)

## Implementation map

- Status: `needs-review`
- Primary files:
  - `.lazy-harness/framework/framework-contract.md` — current `What lazy means` contract section.
  - `.lazy-harness/AGENTS.md` — operational prompt reminders that records are single source of truth.
- Flow:
  1. The meaning of lazy is codified in framework-contract.
  2. Current harness behavior uses record-first/default-unknown rules rather than framework minimalism.
  3. This is a policy/definition ADR, not a standalone executable implementation.
- Tests / protection:
  - Prompt budget/self-test protects prompt surfaces, but no dedicated test asserts this definition text.
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0001-core-philosophy.md`
- Machine index:
  - graph ids: `kg_adr0005_lazy_meaning_contract`
  - generated index key: `pending`
