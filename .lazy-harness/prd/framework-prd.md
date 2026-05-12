# Framework PRD — lazy-harness

Date: 2026-05-12
Status: living document
Owner: lazydino

> **이 PRD 는 host-app PRD 가 아니라 lazy-harness framework 자체의 PRD.**
> framework 가 "어떤 사용자에게, 어떤 문제를, 어떻게 해결해 주는 제품인가" 를 정식화한다.
>
> 상위 목표: [`../plans/north-star-accuracy-and-no-regression.md`](../plans/north-star-accuracy-and-no-regression.md)
> 규칙층 SSOT: [`../framework/framework-contract.md`](../framework/framework-contract.md)
> 실행 마일스톤: [`../trails/02-north-star-milestones.xml`](../trails/02-north-star-milestones.xml)

---

## 1. Product summary

lazy-harness 는 **AI 에이전트 + 사람** 이 같은 코드베이스에서 일할 때
정확도를 올리고 실수/회귀를 구조적으로 막는 **개발 라이프사이클 framework** 다.

단순 prompt 또는 lint 도구가 아니라:

- 프로젝트의 **도메인(DDD) / 설계(SDD) / 행동(BDD) / 테스트(TDD) / 결정(ADR)** 기록을 SSOT 로 보유
- 매 작업마다 위 5 layer 를 **자동 참조 / 검증 / 갱신**
- 검증 누락을 **hook + gate** 로 block
- AI 가 직접 record 를 갱신하고 결정을 durable 하게 저장

---

## 2. Target users

| Persona | 누구인가 | 핵심 통증 |
|---------|----------|-----------|
| **Solo founder / lead dev** (1 차 대상) | 프론트 + 백 + 인프라 + 데이터 모두 책임지는 풀스택 | 컨텍스트 폭주, 결정 망각, 회귀 추적 불가 |
| **소규모 팀 lead** | 2~5 명 팀의 기술 결정권자 | AI 코드의 도메인 위반 / 흐름 누락 catch 불가 |
| **AI 에이전트** | jcode / claude-code / codex 등 | 매 응답마다 컨텍스트 잃음, hallucination, silent skip |

사람과 AI 가 같은 framework 위에서 협업해야 한다는 점이 핵심 (framework-contract Principle 0).

---

## 3. Problem statement (north-star §1 의 9 개 실패 유형)

| # | 실패 유형 | 비즈니스 임팩트 |
|---|-----------|-----------------|
| 1 | 도메인 지식 위반 (hospitalId 누락, soft-delete 정책 위반 등) | 데이터 사고, 멀티 테넌시 누수 |
| 2 | 설계 흐름 누락 (cache invalidation, API 연결 등) | 화면 stale, 사용자 신뢰 손상 |
| 3 | 사용자 시나리오 깨짐 | 출시 후 즉시 hotfix |
| 4 | 과거 버그 재발 (regression) | 같은 자리 반복 수정 비용 |
| 5 | 사이드이펙트 미탐지 | A 수정 → B 회귀 |
| 6 | 결정 망각 (decision drift) | 이전 ADR 반대로 구현 |
| 7 | 기록 불일치 / 중복 / 충돌 | 한 개념이 여러 곳에 다르게 존재 |
| 8 | "looks fine" silent skip | AI 가 검증 없이 통과 |
| 9 | 테스트 없는 변경 | 회귀 보호 0 |

> 이 9 개가 framework 의 **기능 우선순위를 정렬하는 절대 기준** 이다.

---

## 4. Goals & non-goals

### Goals

1. 모든 작업 시작 시 AI 가 자동으로 관련 DDD/SDD/BDD/TDD/ADR 을 검색·참조한다.
2. 변경 전 **side-effect / regression / domain invariant** 를 명시적으로 점검한다.
3. 애매하면 silent skip 없이 **structured question** 을 던지고 답을 durable decision 으로 저장한다.
4. 작업 종료 전 **Layer Impact Completion Gate** 가 누락을 block 한다.
5. AI 가 hook 지시를 받으면 **직접 record 를 갱신** 한다 (사람 수동 의존 0).
6. 테스트가 변경 안전성 / 회귀 / 도메인 정책 위반을 자동 잡는다.
7. 모든 결정과 검증 evidence 가 **portable report** 로 누적되어 framework 자가 개선에 쓰인다.

### Non-goals

- LLM 자체를 만들거나 fine-tune 하지 않는다.
- 프로젝트별 도메인 지식을 framework 가 미리 알지 않는다 (각 host-project 가 SSOT 로 채움).
- "AI 에게 완전 자율" 을 추구하지 않는다 — 항상 사람-AI 상호 보완 (Principle 0).
- 일반 lint / type checker 를 대체하지 않는다 (그건 도구이고, 우리는 그 위의 라이프사이클).
- 단일 IDE / 단일 AI 에 종속되지 않는다 (jcode 우선, 추후 claude-code / codex 동등).

---

## 5. Functional requirements (north-star §4 의 7 개 BLOCKING gate)

| FR | Gate | 검사 내용 | 위반 시 |
|----|------|-----------|---------|
| FR-1 | Map-aware Reference Resolver | 변경 ↔ DDD/SDD/BDD/TDD/ADR record 매핑 | 매핑 못 찾으면 structured question or block |
| FR-2 | Layer Impact Completion Gate | 관련 5 layer 모두 갱신됐는가 | 누락이면 block |
| FR-3 | Side-effect Gate | 인접 영향 영역 / cache / cross-domain query | 의심되면 block, 모르면 question |
| FR-4 | Regression Gate | 과거 버그 / 보호 BDD/TDD 위반 | 위반이면 block |
| FR-5 | Domain Invariant Gate | DDD 용어 / bounded-context / 정책 | 위반은 ADR 없이 진행 금지 |
| FR-6 | Drift / Conflict Detector | 같은 개념의 정의 불일치 / 중복 | 자동 정정 or question |
| FR-7 | Auto Record Update Executor | AI 가 직접 record 갱신 후 hook 재검증 | 사람 수동 의존 금지 |

추가 기능:

- FR-8 Project Profile Skill — 작업 시작 시 profile + map 자동 진입
- FR-9 Feature Navigation Map — "이 기능은 어느 map 에서 출발" 규칙
- FR-10 Lifecycle Hook 통합 — response.completed / pre-commit / pre-push 일관 동작
- FR-11 Portable Report — gate evidence 누적 → framework 자가 개선

---

## 6. Non-functional requirements

| NFR | 기준 |
|-----|------|
| 결정 영속성 | 모든 답변/결정 JSONL append-only, 사람도 AI 도 잃지 않음 |
| 자가 검증 | doctor / lazy:test 로 framework 자체가 framework 의 invariant 통과 |
| 빈 컨테이너 허용 | trigger 없이 빈 디렉토리/파일 valid (Principle 10) |
| Recovery | R1~R4 fallback path (Principle 18) |
| Trigger 강도 명시 | force / recommend / auto+review / auto / human-author 5 단계 |
| Conflict resolution | 8-step strict (Principle 17) |
| Portability | jcode 종속 X, claude-code / codex 도 동일 contract 적용 (M9+) |
| 변경 안전성 | 모든 hook 결과 Unified Result Schema (Principle 9) |

---

## 7. Success metrics

north-star §7 의 7 개 성공 정의를 측정 가능한 지표로:

| Metric | 측정 방법 | 목표 |
|--------|-----------|------|
| Map auto-reference rate | 작업 시작 시 resolver 호출 ÷ 전체 작업 | ≥ 95 % |
| Side-effect/regression/invariant check rate | gate 통과 작업 ÷ 전체 작업 | ≥ 99 % |
| Structured question 답변률 | 답변 완료 ÷ 발생 question | ≥ 90 % |
| Layer Impact Gate block 적중률 | true positive ÷ block 총수 | ≥ 80 % |
| Auto record update 비율 | AI 자동 갱신 record ÷ 전체 갱신 | ≥ 70 % |
| Regression 재발률 | 같은 root cause 재발 ÷ 전체 fix | ≤ 5 % |
| Portable report 활용 evidence 수 | report 기반 framework 개선 ADR | ≥ 4 / 분기 |

측정 기반: `.lazy-harness/logs/` JSONL + `retrospective/metrics/` + `reports/`.

---

## 8. Out of scope (현재 phase)

- 다국어 host-project 지원 (KR/EN UI 외)
- 클라우드 SaaS 형태의 framework hosting
- GUI / dashboard (CLI + 파일 SSOT 만)
- AI 모델 평가 / benchmark 자체 기능

---

## 9. Dependencies

| Dependency | 용도 | 대체 가능성 |
|------------|------|-------------|
| jcode harness | response.completed hook | claude-code / codex 어댑팅 (M9+) |
| TypeScript + bun | 스크립트 실행 환경 | node + tsx 로 fallback 가능 |
| ts-morph | AST diff | 다른 AST 도구 가능 (Principle 22 — 외부 SaaS 호출 금지) |
| git | trigger / log source | 필수 (변경 불가) |

외부 SaaS 호출은 framework 코드 안에서 금지 (Principle 22, Doctor C17 검사).

---

## 10. Release stages

| Stage | 대표 마일스톤 (trails) | 산출물 |
|-------|------------------------|--------|
| Alpha (현재) | M0 ~ M5 | 자기 사용 + medivance host pilot |
| Beta | M6 ~ M8 | 10 skill + daemon lite + template |
| 0.1 public | M9 | npm publish, standalone repo |
| 1.0 self-loop | M10 | 자가 학습 루프 완성 |

north-star A~F 작업은 M2~M5 안에서 병렬 진행 — 상세는
[`../trails/02-north-star-milestones.xml`](../trails/02-north-star-milestones.xml) 참조.

---

## 11. Open questions

- Layer Impact Gate 의 block / warn 임계값을 어떻게 정량화할 것인가? (FR-2)
- Domain Invariant 정의를 host-project 별로 어떻게 표현할 것인가? (FR-5)
- Portable Report 의 JSON 스키마와 외부 ingestion target 은? (FR-11)

→ 위 질문들은 발생 시 `questions/` 에 structured question 으로 등록한다.

---

## 12. Change policy

- 이 PRD 는 north-star 가 본질적으로 변할 때 갱신.
- FR 추가/제거는 ADR 동반 필수.
- success metric 의 목표 수치 조정은 retrospective 분기 회고에서만.
- 충돌 시 우선순위: north-star > framework-contract > 이 PRD > 개별 plan.
