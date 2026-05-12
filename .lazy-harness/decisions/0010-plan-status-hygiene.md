# ADR 0010 — Plan Status Hygiene Principle (#20)

**Date**: 2026-05-10
**Status**: Accepted
**Deciders**: Lazydino
**Trigger**: 사용자 발언 "우리 모든 phase 나 이런것도 계획 다 기록하고 하나씩 진행하면서 체크하면서 가고있는거 맞지?? 그리고 프레임워크에도 그런식으로 설정된거 맞지??"

## Discovery

객관적 점검 결과 **부분 yes / 부분 no**:

✅ 박혀있는 것:
- `trails/01-long-term-roadmap.xml` 장기 vision
- `planning/phase-5-plan.xml` 5a~5e 정의
- `decisions/` ADR 9 개
- `logs/decisions.jsonl` 4 entries
- `logs/actions.jsonl` 79 entries
- `retrospective/cycles/` 5a-closing + 5b-progress

❌ 누락:
1. **5b criteria status 박지 않고 5b 끝났다고 선언** — 5a 는 `status="pass"` 다 박혔는데 5b 는 raw text
2. **emergent ADR (0006/0007/0008/0009) 가 phase plan 의 `<addedDuringPhase>` 에 반영 안 됨**
3. **`plans/`, `progress/`, `daily progress` 한 번도 안 박힘** — placeholder 텍스트도 0
4. **5b-2 → 5b-2a defer 가 plan 에 안 박힘** — ADR 0008 만 있고 plan 갱신 누락
5. **AI 가 5b 진행 중 phase plan 한 번도 cat 안 함** — 계획 파일이 진짜 가이드 역할 못 함

## Root cause

framework-contract 가 정의한 18 principle 중:
- Principle #6 (Trigger-Based Growth): 트리거 시 update
- Principle #1.2 (Drafting and Auditing): 감사 결과 반영
- Principle #11 (Lifecycle obligations): plan/progress 갱신

**모두 있으나** "phase 끝날 때 criteria status 박아라" 라는 **명시적 의무**가 없음. 추상적 "obligation" 만 있고 운영 절차 없음.

→ ADR 0005 의 패턴 ("암묵 → 명시") 또 적용. AI 는 명시 안 된 절차를 spontaneously 수행하지 않음.

## Decision

**Principle #20 — Plan Status Hygiene 추가 (framework-contract Section 20)**.

### Rule 1 — Status 박기 의무 (closed phase)

phase 가 closed 될 때:
- 모든 `<criterion>` 에 `status` 속성 박기 (pass / fail / deferred / passive)
- 각 status 에 verifiedAt 또는 reason 명시
- `<subPhase>` 에 `status="closed" closedAt="..."` 명시
- `<addedDuringPhase>` 섹션에 phase 도중 발생한 emergent ADR / 추가 산출물 기록
- `<closingNotes>` 에 phase 의미 / 교훈 기록

### Rule 2 — Plan-driven execution

phase 시작 시:
- `cat planning/phase-N-plan.xml` 으로 criteria 명시 출력 (verbalize)
- 각 criterion 마다 시작/완료 시 actions.jsonl 에 entry
- emergent task 는 즉시 plan 의 `<addedDuringPhase>` 에 append (ADR 작성 시점에)

### Rule 3 — Daily progress

`progress/YYYY-MM-DD.md` 에 매일 한 일 기록:
- 어떤 criterion 진행
- 어떤 ADR 발생
- 어떤 검증 통과/실패
- 1 일 = 1 파일 (없는 날 OK, 빈 파일 만들지 말 것 — Principle #10)

### Rule 4 — Doctor enforcement

새 check **C12 — Plan Status Hygiene**:
- `<subPhase status="closed">` 인데 `<criterion>` 에 status 속성 없으면 → fail
- closed phase 에 `<addedDuringPhase>` 섹션 없으면 → warn (어쩌면 emergent 가 진짜 없었을 수도)

### Rule 5 — Drafting handoff trigger

phase close 시 `handoff/00-current-state.md` 즉시 갱신 (이미 하고 있지만 명시화):
- phase 변경
- ADR count
- log count

## Why this matters

> Principle 0: 명시 안 된 의무는 누락된다. AI 는 spontaneously 절차를 만들지 않음.

이번 5b 가 lesson:
- 계획 파일이 있어도 진행 도중 안 봤음 → criteria 추적 누락
- ADR 4 개 발생했는데 phase plan 의 `<addedDuringPhase>` 비어있음
- "끝났다" 선언만 retrospective 에 적고 plan status 박지 않음

→ **명시적 5 rule 로 강제**.

## Cascade

| 파일 | 변경 |
|---|---|
| `framework/framework-contract.md` | Principle 20 (Plan Status Hygiene) 추가 |
| `phase-5-plan.xml` | 5b criteria status 박음 (이미 함) |
| `progress/2026-05-10.md` | 오늘 entry 작성 |
| `harness-doctor` C12 | closed phase 의 status 누락 검증 |
| `harness-init` | progress/ 첫 entry placeholder 안 만듦 (Principle #10 — empty 가 valid) |

## Consequences

### Positive

- "끝났다" 와 "진짜 끝났다" 사이의 gap 닫힘
- 다음 세션 AI 가 phase plan 만 봐도 어디까지 됐는지 즉시 파악
- emergent ADR cascade 추적 가능 (plan 이 진실)

### Negative

- phase close 의식 (5 rule) 매번 수행 필요
- 사람도 AI 도 잊을 수 있음 → doctor C12 가 compensate

### Risk

- C12 가 fail 출력하면 미완성 phase 라는 거짓 신호 가능 (실제론 phase 진행 중)
- → fix: status 미정의 시 doctor 가 "in-progress 면 OK / closed 면 fail" 분기

## References

- ADR 0005 (Lazy meaning): 명시 안 한 게 누락의 원인
- ADR 0006 (Directory Bridge): "암묵 → 명시" 패턴
- 사용자 발언: 직감으로 plan hygiene 누락 catch
- Principle 0: 사람도 AI 도 불완전 → 명시 + 자동 검증으로 보완
