# D-2026-05-10-002 — Principle 17: Conflict Resolution Protocol

## Status

Accepted (2026-05-10)

## Context

framework-contract 의 Principle #2 (Drafting and Auditing) 에 5-finding 분류
(gap / conflict / missing / drift / unclear) 는 명세돼 있으나, **conflict 가
발견됐을 때 사용자에게 어떻게 보여주고 결정받는지 정확한 흐름**이 흐릿했음.

사용자(Lazydino) 가 명시적으로 표현:

> "사용자가 그게 아니고 이렇다고 했을 때 실제 ddd 에 있는 내용 sdd 에 있는 내용
>  bdd 에 있는 내용을 예시로 보여주며 뭐가 맞는 거냐고 물어보는 거지.
>  사용자가 실수한 거라면 명확하게 의사결정을 하고 넘어가는 거야"

이게 framework 가 "유기적으로 동적으로 완성되어 가는 지식 저장소" 가 되기 위한
핵심 동작. 명세화 필수.

## Decision

**Principle 17 — Conflict Resolution Protocol** 을 framework-contract 에 추가.

8 단계 strict protocol:

1. **Search Existing Knowledge** — DDD/SDD/BDD/TDD/SSOT 전체 검색
2. **Detect Conflict** — 5-finding 분류
3. **Cite Sources Explicitly** — file:line + 직접 인용 (paraphrase 금지)
4. **Present Structured Choices** — A/B/C/D/E 객관식 + recommended
5. **Compute Impact Range** — 선택 전 영향 범위 미리 보여줌
6. **Persist Decision** — decisions/decisions-log.jsonl + 영향 문서 atomic 갱신
7. **Aftershock Check** — 갱신 후 재 5-finding (max depth 3)
8. **Log Full Chain** — input → conflict → choice → impact → persist 체인 기록

Hard rules:
- 새 정보 persist 전 conflict scan 강제
- paraphrase 금지 (직접 인용만)
- auto-resolve 금지 (항상 human gate)
- silent update 금지 (impact range 먼저 보여줌)
- aftershock check skip 금지

## Consequences

### Positive
- framework 가 사용할수록 견고해짐 (Principle 0 핵심 실현)
- 사용자/AI 가 새 정보 줄 때마다 자동으로 모순 검사
- silent drift 방지 (가장 위험한 실패 모드)
- 결정이 자산화 → 6 개월 후에도 추적 가능
- AI hallucination 차단 (paraphrase 금지 + 직접 인용 강제)

### Negative / Trade-offs
- 모든 새 정보 입력에 latency 추가 (최소 +30s, conflict 있으면 +수분)
- 사용자에��� 의사결정 요구 횟수 증가 (단, 자산화로 보상)
- aftershock recursion 으로 복잡한 변경 시 다단계 결정 필요

### Mitigations
- recommended 옵션 제시로 의사결정 부담 경감
- 아주 작은 변경 (typo, comment) 은 conflict scan 가능 자동 skip 휴리스틱 추가 (TBD)
- aftershock max depth 3 으로 무한 재귀 방지

## Example

```
사용자: "환자 등록 시 보호자 정보 필수"

AI 가 자동 실행:
  Step 1~3: DDD/aggregates.xml line 47, SDD/frontend/patient-register.xml line 23,
            BDD/scenarios/patient-001.xml line 12 발견 — 모두 보호자 옵셔널

  Step 4: 어느 쪽이 맞나요?
    (A) 새 정보 맞음 → DDD/SDD/BDD 3 곳 갱신
    (B) 기존 맞음 → 사용자가 잘못 안 것
    (C) 상황 따라 다름
    (D) 정책 변경
    (E) 다른 답

  Step 5: 각 선택의 영향 범위 미리 보여줌

  사용자 선택 후 Step 6~8 자동 실행
```

## Related

- framework-contract.md Principle 17
- D-2026-05-10-001 (Principle 0 — 이 protocol 의 동기)
- D-2026-05-10-003 (Principle 18 Recovery Path)
- M3 (Adapter Funnel 실작동) - 이 protocol 의 첫 실전
- M4 (Interview Loop) - 이 protocol 의 양방향 흐름 시나리오
