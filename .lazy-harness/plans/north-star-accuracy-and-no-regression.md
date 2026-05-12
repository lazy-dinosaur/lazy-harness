# North-Star — AI 개발 정확도 + 실수/회귀 제거

이 문서는 지금까지 합의된 lazy-harness 의 **목표 그림 (north-star)** 을 한 곳에 정리한 단일 진입점이다.  
다른 plan (`5d-interview-loop-implementation-spec.md`, `project-init-interview-spec.md`,  
`report-and-knowledge-roadmap.md`, `post-mvp-gap-map.md`) 들은 이 문서의 하위 실행 계획.

> **이 문서 = 우리가 왜 lazy-harness 를 만드는가의 답.**  
> 구현 디테일이 흔들릴 때 항상 이 문서로 돌아온다.

---

## 0. 한 줄 요약

> **AI 에이전트를 활용한 실제 개발에서 정확도를 올리고, 실수와 회귀를 구조적으로 줄인다.**

- 단순 "AI 가 코드 잘 짜는 도구" 가 아니다.
- 프로젝트의 **도메인 / 설계 / 행동 / 테스트 / 결정** 을 매번 정확히 참조하면서 일하게 만드는 **시스템** 이다.
- 사람도 AI 도 불완전하다는 전제 위에서 **상호 보완** 한다 (framework-contract Principle 0).

---

## 1. 우리가 막으려는 실패 유형

| # | 실패 유형                          | 현실 사례                                                |
|---|------------------------------------|----------------------------------------------------------|
| 1 | 도메인 지식 위반                   | 환자 데이터에 hospitalId 누락, soft delete 정책 위반     |
| 2 | 설계 흐름 누락                     | 버튼은 만들었는데 연결된 상태/API/캐시 invalidation 빠짐 |
| 3 | 사용자 시나리오 깨짐               | 기능은 동작하지만 실제 사용 흐름이 막힘                  |
| 4 | 과거 버그 재발 (regression)        | 같은 자리에서 같은 버그가 다시 발생                      |
| 5 | 사이드이펙트 미탐지                | A 를 고쳤더니 B 가 깨짐                                  |
| 6 | 결정 망각 (decision drift)         | 왜 이렇게 했는지 잊고 반대로 구현                        |
| 7 | 기록 불일치 / 중복 / 충돌          | 같은 개념이 여러 곳에 다르게 정의됨                      |
| 8 | "looks fine" silent skip           | AI 가 검증 없이 통과시킴                                 |
| 9 | 테스트 없는 변경                   | 회귀 보호 안 됨                                          |

lazy-harness 의 모든 hook / script / skill / gate 는 위 9 개를 줄이기 위해 존재한다.

---

## 2. 5-Layer 역할 (DDD / SDD / BDD / TDD / ADR)

```text
DDD  → 도메인 지식, ubiquitous language, 비즈니스 불변조건
        → 잘못된 방향 / 용어 / 정책 위반 방지

SDD  → 구조, 화면, API, 컴포넌트, 흐름, 연결 관계
        → 버튼 / 상태 / 데이터 흐름 / cache invalidation 누락 방지

BDD  → 사용자 시나리오, 실제 사용 흐름
        → "기능은 됐는데 사용자 행동이 깨짐" 방지

TDD  → 구현 검증, 회귀 방지, affected test
        → 변경이 실제로 안전한지 확인

ADR  → 왜 이런 구조/정책을 택했는지
        → 장기 결정 흔들림, drift 방지
```

> 4 layer (DDD/SDD/BDD/TDD) **동등 대우** + ADR 은 결정 보존층.  
> framework-contract Principle 0.2 (완성도 > 일관성 > lazy > 자동화 > setup 비용) 와 일치.

---

## 3. 핵심 개발 루프 (모든 작업이 따라야 ���는 흐름)

```text
요청 / 코드 변경 발생
 │
 ▼
(1) project profile + map 읽기
 │   - 어떤 프로젝트인가, 어떤 layer/map 이 존재하는가
 │
 ▼
(2) Map-aware Reference Resolver
 │   - 이 변경이 어떤 DDD/SDD/BDD/TDD/ADR record 와 연결되는가
 │   - 단순 grep 아님 — cross-layer link 기반
 │
 ▼
(3) Gap / Conflict / Duplicate 판정
 │   - 빠진 흐름 / 버튼 / API / 시나리오 있는가
 │   - 같은 개념이 다르게 정의돼 있는가 (drift)
 │   - 기존 record 와 충돌하는가
 │
 ▼
(4) Side-effect / Regression / Domain-Invariant Gate
 │   - 인접 영향 영역은?
 │   - 과거 regression / 보호 BDD/TDD 가 있는가
 │   - DDD 불변조건 위반 가능성?
 │
 ▼
(5) 확신 vs 애매
 │   - 확신 → 자동 진행
 │   - 애매 → Structured Question (durable decision 저장)
 │
 ▼
(6) 테스트 먼저 / 동시에 작성 (TDD)
 │
 ▼
(7) 구현
 │
 ▼
(8) Validation
 │   - affected test / typecheck / lint
 │   - cache invalidation 점검 (renderer 변경 시)
 │
 ▼
(9) Record 자동 갱신
 │   - DDD/SDD/BDD/ADR 기록 update
 │   - drift / 중복 정정
 │
 ▼
(10) Layer Impact Completion Gate (hook)
      - 누락된 record / 미검증 항목 있으면 block
      - silent skip 금지
```

> 이 루프 중 어느 단계라도 silent 하게 skip 되면 framework 가 깨진 것이다.

---

## 4. 필수 게이트 (BLOCKING)

| Gate | 무엇을 검사? | 위반 시 |
|------|---------------|---------|
| **Map-aware Reference Resolver** | 변경 ↔ DDD/SDD/BDD/TDD/ADR record 매핑 | 매핑 못 찾으면 question or block |
| **Layer Impact Completion Gate** | 모든 관련 layer 가 갱신됐는가 | 누락이면 block |
| **Side-effect Gate** | 인접 영향 영역 / cache / cross-domain query | 모르면 question, 의심되면 block |
| **Regression Gate** | 과거 버그 / 보호 BDD/TDD 위반 여부 | 위반이면 block |
| **Domain Invariant Gate** | DDD ubiquitous-language / bounded-context / 정책 | 위반은 ADR 없이 진행 금지 |
| **Drift / Conflict Detector** | 같은 개념 다른 정의, record 중복 | 자동 정정 or question |
| **Auto Record Update Executor** | hook 지시 시 AI 가 직접 record 갱신 | 사람 수동에 의존 금지 |

모든 gate 는 framework-contract 의 **Principle 5 (Self-Loop Hard Limits)** 와  
**Principle 17 (Conflict Resolution)** 안에서 동작한다.

---

## 5. 왜 테스트를 붙이는가

테스트는 단순 커버리지 도구가 아니다.  
lazy-harness 에서 테스트는 **AI 정확도 강제 메커니즘** 이다.

- AI 가 놓친 요구사항을 잡기 위해
- 과거 버그 재발 (regression) 방지
- 도메인 정책 위반 검증
- 설계 / 사용자 흐름이 구현과 연결됐는지 확인
- "looks fine" silent pass 방지

→ TDD 는 4-layer 중 검증층이며, BDD / DDD / SDD 와 동등하게 first-class.

---

## 6. 우선순위 로드맵 (다음 작업 순서)

north-star 를 달성하기 위해 다음 순서로 구축한다.
**측정 가능한 산출물 / 완료 기준 / 의존성** 은 별도 마일스톤 문서로 정식화했다:

- 실행 마일스톤 (N1~N8): [`../trails/02-north-star-milestones.xml`](../trails/02-north-star-milestones.xml)
- 제품 PRD: [`../prd/framework-prd.md`](../prd/framework-prd.md)
- framework 전체 phase 축 (M0~M10): [`../trails/01-long-term-roadmap.xml`](../trails/01-long-term-roadmap.xml)

요약:

| 순위 | 작업                                              | 마일스톤 | 산출물                                     | 상태 |
|------|---------------------------------------------------|----------|--------------------------------------------|------|
| A    | **Layer Impact Completion Gate**                  | N1       | hook + schema + force-gate policy          | planned |
| B    | **Map-aware Reference Resolver**                  | N2       | resolver script + cross-layer link 규칙    | planned |
| C    | **Side-effect / Regression / Domain Invariant Gate** | N3   | gate script + 3 검사 통합 schema          | planned |
| D    | **Project Profile Skill (skill-first)**           | N4       | skill + 자동 진입 hook                     | planned |
| E    | **Auto Record Update Executor 강화**              | N5       | DDD/SDD/BDD/ADR auto-update + hook 재검증  | planned |
| F    | **Portable Report**                               | N7       | gate evidence 누적 → framework 자가 개선   | planned |
| aux  | Drift / Conflict Detector                         | N6       | 같은 개념 정의 불일치 자동 검출            | planned |
| aux  | Lifecycle Hook 통합                               | N8       | response.completed / pre-commit / pre-push 일관 | planned |

각 N* 마일스톤은 trails 문서에서 success criteria + 의존성 + 관련 FR 까지 정의되어 있다.

---

## 7. 성공 정의 (이게 되면 north-star 달성)

1. AI 가 새 작업을 받으면 **자동으로** 관련 DDD/SDD/BDD/TDD/ADR 을 검색·참조한다.
2. 변경 전 **side-effect / regression / domain invariant** 를 명시적으로 점검한다.
3. 애매하면 silent skip 없이 **structured question** 을 던지고, 답을 durable decision 으로 저장한다.
4. 작업 종료 전 **Layer Impact Completion Gate** 가 누락을 block 한다.
5. AI 가 hook 지시를 받으면 **직접 record 를 갱신** 한다 (사람 수동 의존 0).
6. 테스트가 **변경 안전성 / 회귀 / 도메인 정책** 위반을 자동 잡는다.
7. 모든 결정과 검증 evidence 가 **portable report** 로 누적되어 framework 자가 개선에 쓰인다.

---

## 8. 관련 문서

- `framework/framework-contract.md` — Principle 0~18, 모든 규칙의 SSOT
- `plans/project-init-interview-spec.md` — map-first 인터뷰 / project profile 규약
- `plans/5d-interview-loop-implementation-spec.md` — interview loop 구현 사양
- `plans/report-and-knowledge-roadmap.md` — knowledge / report 축적 로드맵
- `plans/post-mvp-gap-map.md` — 빠진 layer / gap 추적
- `plans/5c-remaining-implementation-plan.md` — 5c 잔여 작업
- `plans/post-5c-refactor-and-package-health.md` — 리팩터 / 패키지 건강

---

## 9. 변경 정책

- 이 문서는 north-star 가 **본질적으로** 바뀔 때만 수정 (목표 / gate 추가 / 우선순위 재조정).
- 구현 디테일은 각 plan 문서에서 진행.
- 다른 plan 들이 이 문서와 충돌하면 **이 문서가 우선** (목표 우선, 구현은 따라감).
