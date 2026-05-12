# D-2026-05-10-001 — Core Philosophy: 사람과 AI 상호 보완

## Status

Accepted (2026-05-10)

## Context

lazy-harness 의 존재 이유를 명확히 박아두지 않으면 framework 가 시간 갈수록
방향을 잃거나, 다른 framework (tsq 등) 를 단순 모방하는 길로 빠질 위험.

이번 세션에서 사용자(Lazydino) 가 명시적으로 표현:

> "사람도 AI 도 불완전하기 때문에 상호 보완하면서 진행하게 되는 게
>  이 프레임워크의 핵심이야"

이 한 문장이 16 principle 위에 서 있는 메타 원칙임을 확인.

## Decision

**Principle 0** 으로 framework-contract 에 박는다:

> **사람도 AI 도 불완전하다. 그래서 상호 보완하며 진행한다.**

이 원칙에서 모든 18 principle (16 기존 + 17 Conflict Resolution + 18 Recovery) 이 파생됨을 명시.

각 principle 은 사람의 한계 또는 AI 의 한계를 보완하는 안전망으로 정렬:

| 사람의 한계 | AI 의 한계 | 보완 principle |
|---|---|---|
| 기억력 부족 | 환각 | #1 Living Document |
| 모순 인식 어려움 | 모순 무시 | #2 Audit + #17 Conflict Resolution |
| 영향 추적 불가 | 영향 추측 | #14 Bidirectional Traceability |
| 일관성 어려움 | 매번 다름 | #6 Trigger Growth + Schema |
| 자율 부담 | 자율 폭주 | #5 Self-Loop Limits + #1.6 5 강도 |
| 빠짐 인지 불가 | hallucinated knowledge | #10 Empty Tolerance + Audit |
| 회복 즉흥적 | 깨짐 모름 | #18 Recovery Path |
| 도구 비일관 | 호출 누락 | #9 Unified Result + #3 Adapter Funnel |

## Consequences

### Positive
- framework 의 모든 결정이 Principle 0 으로 검증 가능
- "왜 이 principle 이 있나?" 질문에 즉답 가능
- 다른 framework 와의 차별점 명확화 (tsq 는 "Structure leads to better results", 우리는 "사람과 AI 상호 보완")
- 미래 18+ principle 추가 시 Principle 0 정렬 검증 필수

### Negative / Trade-offs
- "AI 자율 폭주" 와 "사람 부담 경감" 둘 다 막아야 하므로 균형점 찾기 어려울 수 있음
- 새 principle 추가 시 Principle 0 으로 정당화 의무 → 추가 비용

### Neutral
- 기존 16 principle 의 의미 변화 없음 (해석 frame 만 추가)

## Related

- framework-contract.md (Principle 0 섹션)
- handoff/00-current-state.md (Principle 0 표)
- D-2026-05-10-002 (Principle 17 Conflict Resolution Protocol)
- D-2026-05-10-003 (Principle 18 Recovery Path)
