# lazy-harness ↔ timsquad (tsq) 비교 분석

Date: 2026-05-12
Author: lazydino
Source basis:
- 자체 framework 문서 (`framework/framework-contract.md`, `trails/01-long-term-roadmap.xml`)
- 기존 비교 메모: `trails/01-long-term-roadmap.xml` <comparisonToTsq>, ADR 0016, ADR 0001
- 공개 정보: tsq v3.8 (npm publish, 53 TS files, 330 templates, 23 tests, 37 skills) 시점 기준

> 본 문서는 north-star (정확도 + 회귀 제거) 관점에서 두 도구의 **포지셔닝과 격차** 를 솔직하게 기록한다.
> 추격이 목적이 아니라 **우리 차별점이 어디에 있는지 명확히 하기 위함**.

---

## 0. 한 줄 요약

| 항목 | timsquad (tsq) | lazy-harness |
|------|----------------|--------------|
| 본질 | **정적 SSOT 생성 + skill 모음** | **동적 라이프사이클 framework** |
| 강점 | 패키징, init, 템플릿 양, 시장 검증 | Principle 0, gate 깊이, 실패 9 종 차단 |
| 약점 | 라이프사이클 hook, conflict resolution 깊이 | 패키징, init, 실전 사용 부족 |
| 적합 사용자 | 도구를 빨리 적용하고 싶은 팀 | 실수/회귀를 구조적으로 막고 싶은 풀스택 / AI-first 개발자 |

→ **다른 차원의 제품**. 같은 카테고리 안에서 1:1 우열 비교 자체가 부분적으로만 의미 있음.

---

## 1. 정량 비교 (2026-05 시점)

| 지표 | tsq v3.8 | lazy-harness 현재 | 격차 평가 |
|------|----------|--------------------|-----------|
| 공개 상태 | npm publish ✅ | 비공개 실험 (medivance branch) | -42 (분명히 열세) |
| TS 파일 수 | 53 | ~5 (interview-loop, doctor 등) | -48 |
| 템플릿 수 | 330 | 0 (template 시스템 없음, ADR 0013 으로 의도적 폐기) | 의도된 차이 |
| 테스트 수 | 23 | 7 (D01~D07 doctor 프로파일 + lazy:test) | -16 |
| Skill 수 | 37 | 5 stable + 3 planned | -29 |
| Principle / Pattern 개수 | 공개 명시 적음 | 23 principle + 4 pattern + 5 trigger 강도 | **+ (개념 깊이 우위)** |
| ADR 수 | 공개 명시 적음 | 22 | + |
| 작성된 contract 라인 수 | n/a | 983 (`framework-contract.md`) | + |

→ 패키징 / 양 / 시장 검증은 tsq 압승, 개념 깊이 / contract / ADR 은 lazy 우위.

---

## 2. 철학 비교

### tsq 철학 (공개 정보 기반 요약)

- "AI 가 한 번에 끝내도록 SSOT 를 빠르게 깔자"
- init / template 기반 → 진입 장벽 낮춤
- skill 단위 작업 분해 (37 skill 로 인입점 풍부)
- /tsq-grill 같은 인터뷰 도구로 명세 보강

### lazy-harness 철학

- **Principle 0**: "사람도 AI 도 불완전하다, 상호 보완한다"
- 모든 작업은 trigger 기반 (force / recommend / auto+review / auto / human-author)
- 5 layer (DDD/SDD/BDD/TDD/ADR) 동등 대우
- 9 종 실패를 hook + gate 로 차단 (north-star)
- "looks fine" silent skip 절대 금지

### 결정적 차이

| 차원 | tsq | lazy-harness |
|------|-----|--------------|
| 시간축 | **단발적 SSOT 생성**: 작업 시점에 한 번 잘 만듦 | **연속적 라이프사이클**: 모든 변경마다 5 layer 재검증 |
| 책임 | AI 가 잘 만들면 끝 | AI 가 잘 만들어도 hook 이 다시 검증, 누락 block |
| 정답 | 빠른 init / 좋은 템플릿 | 누락 / drift / 회귀 / 정책위반 차단 |
| Conflict | 자유 답변 또는 grill 인터뷰 | **8-step Conflict Resolution Protocol** (Principle 17) |
| Recovery | 사람 수동 | **R1~R4 4 단계 fallback** (Principle 18) |

---

## 3. 기능 매핑

| tsq 기능 | lazy-harness 대응 | 비교 |
|----------|--------------------|------|
| `tsq init` (1 줄 init) | M1 Self-Bootstrap (계획) | tsq 가 이미 함, 우리는 M1 에서 따라잡을 예정 |
| 330 template | (의도적으로 없음) | ADR 0013 에서 template 폐기. 대신 trigger 기반 생성 |
| 37 skill | 5 + 3 planned (manifests/skills.xml) | M6 에서 10 skill 목표 (차별 영역 집중) |
| /tsq-grill 인터뷰 | lazy-interview (Phase 5d) + structured options | tsq 는 자유 질문, 우리는 **3~5 옵션 + Recommended** 강제 (Principle 21) |
| 결과 통합 | skill 별 출력 | **Unified Result Schema** (Principle 9) — 모든 hook 동일 JSON |
| daemon | 있음 (file watcher) | M7 (lite mode) 계획 |
| 자가 검증 | 부분 (lint / test) | doctor C01~C17 + lazy:test D01~D07 (framework 자기 검사) |
| Adapter funnel | n/a | Principle 3 (입력 6 종 → 단일 진입점) |
| 5-finding 분석 (gap/conflict/missing/drift/unclear) | n/a | 직접 명명한 분류 자체가 차별점 |
| Trigger 강도 5 단계 | n/a | **force/recommend/auto+review/auto/human-author** 명시 |
| Empty-container tolerance | n/a (template 으로 미리 채움) | Principle 10 (빈 게 valid) |
| Bidirectional traceability | n/a | Principle 14 (regression ↔ test ↔ BDD ↔ contract) |

---

## 4. 어디서 우리가 더 강한가 (north-star 관점)

north-star §1 의 9 종 실패 유형 기준 평가:

| 실패 유형 | tsq 차단력 | lazy-harness 차단력 | 비고 |
|-----------|------------|----------------------|------|
| 1. 도메인 지식 위반 | △ (template 가이드) | ◎ (Domain Invariant Gate N3) | gate 가 hook 으로 강제 |
| 2. 설계 흐름 누락 | △ | ◎ (Layer Impact Gate N1) | 누락 시 block |
| 3. 사용자 시나리오 깨짐 | △ (BDD 템플릿) | ○ (BDD layer + N3) | 비슷 |
| 4. 과거 버그 재발 | × (regression 추적 약) | ◎ (Regression Gate + 양방향 traceability) | **우위** |
| 5. 사이드이펙트 미탐지 | × | ◎ (Side-effect Gate N3) | **우위** |
| 6. 결정 망각 | △ (ADR 템플릿) | ◎ (22 ADR + decisions JSONL append-only) | **우위** |
| 7. 기록 불일치 / 중복 | × | ◎ (Drift Detector N6 + Conflict Resolution P17) | **우위** |
| 8. silent skip | × | ◎ (모든 gate force) | **우위** |
| 9. 테스트 없는 변경 | △ | ◎ (affected test runner + TDD layer) | 우위 |

→ **9 종 중 7 종에서 lazy-harness 가 구조적으로 더 강함**. 단 이건 "설계상" 우위이며 **실전 검증은 N1~N8 마일스톤 완수 후** 입증됨.

---

## 5. 어디서 tsq 가 더 강한가

| 차원 | 이유 |
|------|------|
| **시장 검증** | npm publish, 외부 사용자, v3.8 까지 진화. 우리는 비공개 실험. |
| **즉시성** | 1 줄 init → 바로 사용. 우리는 M1 미완. |
| **양** | 330 template / 37 skill / 53 TS file. 우리는 일부러 적게 시작. |
| **학습 자료** | 공개 문서 / 사용자 community. 우리는 0. |
| **portability** | 이미 다양한 환경에서 동작 검증. 우리는 jcode 의존. |
| **stability** | v3.8 의 안정성. 우리는 0.x 실험. |

---

## 6. 격차 좁히기 전략

우리가 tsq 와 같은 카테고리로 들어가려면:

| 격차 | 대응 마일스톤 | 우선순위 |
|------|---------------|----------|
| init 1 줄 | M1 Self-Bootstrap | critical |
| skill 10 개 | M6 Skill 생태계 | medium |
| daemon | M7 Daemon (lite) | medium |
| template (의도적 폐기) | 추격 안 함 — trigger 기반으로 차별화 | n/a |
| npm publish | M9 Public 0.1 | high |
| 학습 자료 | M9 와 함께 | high |

동시에 우리만의 차별점은 **north-star N1~N8 마일스톤** 으로 깊이 굳힌다 (`trails/02-north-star-milestones.xml`).

---

## 7. 결론

1. **추격 vs 차별화**: lazy-harness 의 목적은 tsq 추격이 아니다. **north-star 9 종 실패 차단**.
2. **단계별 전략**: M0~M5 에서 우리 차별점 (gate / Principle / Recovery) 을 굳히고, M6~M9 에서 tsq 가 가진 패키징/skill/publish 격차를 좁힌다.
3. **lessons from tsq**: init 1 줄, skill 단위 분해, daemon — 이 셋은 **컨셉을 차용** 하되 구현은 우리 라이프사이클에 맞게.
4. **우리만 가능한 것**: Principle 0 (사람-AI 상호 보완), 5-finding 분석, Trigger 강도 5 단계, 8-step Conflict Resolution, R1~R4 Recovery, Bidirectional Traceability, Unified Result Schema, Empty-Container Tolerance. **이 8 개는 학술/산업 어디에도 같은 명제 없음.**

> **방향**: tsq 와 같은 자리에 서지 않고, **그 위의 layer (라이프사이클 + 9 종 실패 차단)** 에 자리잡는다.

---

## 8. 후속 검증 항목 (open)

- tsq v3.8 의 실제 코드/skill 구조를 직접 확인 (현재 비교는 공개 메타데이터 기반)
- 우리 N1~N3 마일스톤 완료 후 동일 host-project 변경 1 회를 tsq vs lazy 로 각각 돌려 비교 evidence 수집
- M9 (public 0.1) 시점에 외부 1 개 프로젝트 적용으로 portability 검증

→ 위 항목은 진행 시 `questions/open.xml` 에 structured question 으로 등록.

---

## 9. 관련 문서

- `framework/framework-contract.md` — 23 principle / 4 pattern / 5 trigger
- `plans/north-star-accuracy-and-no-regression.md` — north-star 9 종 실패 + 7 gate
- `prd/framework-prd.md` — framework 자체 PRD
- `trails/01-long-term-roadmap.xml` — M0~M10 phase 축 (기존 tsq 비교 메타데이터 포함)
- `trails/02-north-star-milestones.xml` — N1~N8 north-star 실행 축
- `decisions/0013-*.md` — template 폐기 결정
- `decisions/0016-lifecycle-hook-strategy.md` — hook 전략
- `retrospective/metrics/completeness-scorecard.xml` — 자가 평가
