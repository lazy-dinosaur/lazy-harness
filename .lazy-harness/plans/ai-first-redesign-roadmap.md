# AI-first Redesign Roadmap (N2.5 ~ N8 실행 계획)

**Status**: Active
**Date**: 2026-05-12
**Owner**: lazy-harness framework
**Driving ADRs**: 0024 (AI-first redesign), 0025 (portability single entry point)
**Supersedes**: 일부 — N2 의 70% 가 본 roadmap 의 N2.5 로 교체. N9 (별도 portability) 신설 안 함, N4 에 흡수.

---

## 배경 — 왜 이 roadmap 인가

N2 host-pilot (5 commit, 5 pass) 가 precision/recall = 1.0 으로 통과했지만, 그 과정에서 본질적 문제가 드러났다:

- N2 의 IDF/burst suppression / stopword / ADR-keyword 가 **검색 알고리즘을 TypeScript 로 수동 구현**한 패턴
- 모든 튜닝값이 medivance corpus 의존적 매직 상수 (`0.18`, `0.3`, `0.5`)
- 다른 host 로 옮기면 재튜닝 필수 → portability 깨짐
- 사용자 통찰: "AI 가 검색하면 되지 않아? 사용하면서 누적되는 게 framework 디자인이잖아."

→ N2 를 단순 검증된 baseline 으로 두고, **N2.5 에서 AI-first 로 재설계**. 그 후 N3~N8 이 같은 원리 일관 적용.

핵심 원칙 (ADR 0024):
- **Framework = AI-first lifecycle enforcement** (not AI-assisted, not ESLint-like)
- **AGENTS.md = grammar (얇음, framework 공통), record = vocabulary (host 특화)**
- **3-Layer Defense**: AGENTS.md (자발적 준수) / tool.execute.before (사전 차단) / response.completed (사후 검증)
- **SearchProvider 추상화**: default = AI direct, optional = subagent, future = RAG
- **검색 알고리즘 직접 구현 패턴 N3/N6 에서 반복 금지**

---

## 전체 timeline (총 ~85h)

```
2026-05-12 (오늘)
  ↓
N2.5 — AI-first Resolver + AGENTS.md + 3-Layer Defense (5~7h)
  ↓
N3 — Side-effect / Regression / Domain Invariant Gate (15h)
  ↓
N4 — Project Profile + Bootstrap (15.5h)  ← portability 단일 진입점
  ↓
N5 — Auto Record Update Executor (15h)
  ↓
N6 — Drift / Conflict Detector (8h)
  ↓
N7 — Portable Report (8h)
  ↓
N8 — Lifecycle Hook 통합 (8h)
```

각 milestone 끝나면 commit by commit + ADR 등록 + self-test 18/18 green 유지.

---

## N2.5 — AI-first Resolver + AGENTS.md + 3-Layer Defense (5~7h)

**목적**: N2 의 검색 알고리즘 제거 + AI 행동 grammar 박음 + 안전망 hook 신설.

### 작업 분해

| # | 작업 | 산출물 | 시간 |
|---|---|---|---|
| 1 | SearchProvider abstraction | `interface SearchProvider` + `DirectAISearch` 구현 | 1.5h |
| 2 | reference-resolver.ts 단순화 | IDF/burst/stopwords/ADR-keyword/path-stem partial 제거, ~459→~80 줄 | 1.5h |
| 3 | `.lazy-harness/AGENTS.md` 작성 | framework 공통 grammar, ~40~50 줄 | 1h |
| 4 | tool.execute.before hook | `on-tool-execute-before.sh` + session-cache | 1.5h |
| 5 | 회귀 검증 | 4 fixtures + host-pilot 5 commit, precision/recall ≥ 1.0 유지 | 1h |
| 6 | (선택) jcode 통합 | `.lazy-harness/AGENTS.md` 자동 인식 (jcode patch) | 0.5h |

### Commit 순서

1. `Refactor: N2 reference-resolver IDF/burst/stopwords 제거 + SearchProvider abstraction`
2. `Feat: .lazy-harness/AGENTS.md 신설 (framework grammar)`
3. `Feat: tool.execute.before hook + session-cache (3-Layer Defense Layer 2)`
4. `Test: N2.5 회귀 검증 (host-pilot 재실행)`
5. (선택) `Feat: jcode .lazy-harness/AGENTS.md 자동 인식`

### `.lazy-harness/AGENTS.md` 구조 초안

```markdown
# Lazy-Harness AI 행동 양식

너 (AI) 는 lazy-harness 가 활성된 host 에서 작업한다.
.lazy-harness/ 는 이 프로젝트의 institutional memory.

## Layer ↔ Trigger 매핑

| Layer | 폴더 | 검색 트리거 |
|---|---|---|
| DDD | .lazy-harness/ddd/ | 도메인 용어 등장 |
| SDD | .lazy-harness/sdd/ | API/contract/component 만짐 |
| BDD | .lazy-harness/bdd/ | UI flow / 사용자 행동 |
| TDD | .lazy-harness/tdd/ | 버그 fix, regression |
| ADR | .lazy-harness/decisions/ | 설계 결정 직면 |
| SSOT | .lazy-harness/ssot/ | config/schema/env |

## 4 단계 흐름

1. 요청 받자마자 검색 (반드시):
   `grep -rli '<핵심 토큰>' .lazy-harness/{ddd,sdd,bdd,tdd,decisions,ssot}/`
2. 발견된 record 끝까지 Read — host 룰의 single source of truth
3. 결정 분기 시 옵션 질문 (자유 문답 금지, 3~5 옵션 + Recommended)
4. 작업 후 누적 — 새 결정/시나리오/제약 → 해당 layer 갱신

## Framework Contract

- 능동 검색하면 hook silent
- 깜빡하면 tool.execute.before 가 force-gate (AGENTS.md §섹션 인용)
- record 가 빈약하면 누적해라 (1주 동안 안 자라면 framework 활용 실패)
```

→ 이 정도가 framework 공통. host 특화 룰은 절대 박지 않음.

### Success criteria

- [ ] `reference-resolver.ts` ≤ 100 줄
- [ ] `SearchProvider` interface + `DirectAISearch` 구현 ([테스트 포함])
- [ ] `.lazy-harness/AGENTS.md` ≤ 60 줄, host 특화 룰 0
- [ ] `on-tool-execute-before.sh` + session-cache 작동 (Edit/Write 시 검색 안 했으면 force-gate)
- [ ] 4 fixtures + 5 host-pilot commits 모두 precision/recall ≥ 1.0
- [ ] self-test 18/18 green 유지

### Risks

- **AGENTS.md 가 너무 추상적이라 AI 가 무시**: Layer 2 hook 으로 메꿈. dogfooding 측정 후 보정.
- **SearchProvider 의 AI 직접 검색이 느림**: 호출 빈도 측정, 너무 많으면 cache 추가.

---

## N3 — Side-effect / Regression / Domain Invariant Gate (15h)

**목적**: 인접 영향 / regression 보호 / 도메인 정책 위반 자동 catch.

### 핵심: N2.5 의 SearchProvider 소비

N3 의 3 스캐너 모두 SearchProvider 를 통해 record 검색. **검색 알고리즘 직접 구현 금지** (ADR 0024 E2).

### 작업 분해

| # | 작업 | 시간 |
|---|---|---|
| 1 | `scripts/side-effect-scan.ts` (cache invalidation, cross-domain query) | 4h |
| 2 | `scripts/regression-scan.ts` (regression log + 보호 BDD/TDD 위반) | 4h |
| 3 | `scripts/domain-invariant-scan.ts` (DDD term / bounded-context / 정책) | 4h |
| 4 | 통합 schema `gate-bundle-result.schema.json` | 1h |
| 5 | 옵션 질문 시스템 (자유 문답 금지) | 1h |
| 6 | host-pilot 검증 (medivance cache invalidation 1 건 catch) | 1h |

### 의존성

- N2.5 (SearchProvider, AGENTS.md, 3-Layer Defense)

### Success criteria

- 3 스캐너 모두 SearchProvider 사용 (직접 구현 0)
- medivance host-pilot 에서 실제 cache invalidation 누락 1 건 catch
- 위반 시 구조화 옵션 질문 (3~5 후보 + Recommended)

---

## N4 — Project Profile + Bootstrap (15.5h, portability 단일 진입점)

**목적**: `lazy init` 한 번으로 새 host 30 분 안에 동작. 모든 portability 책임 흡수.

### inspect → interview → apply 3 단계

상세는 ADR 0025 참조. 요점:

- **inspect**: stack 자동 감지, 폴더 패턴, fixture path. host AGENTS 안 건드림.
- **interview**: 5~10 구조화 옵션 질문. inspect 가 감지한 건 묻지 않음 (확인만).
- **apply**: AGENTS.md (1 종 템플릿) + config.json + rules/ + 빈 record 폴더 + bootstrap ADR.

### 작업 분해 (15.5h)

| # | 작업 | 시간 |
|---|---|---|
| 1 | inspect: stack/폴더/path 자동 감지 | 2h |
| 2 | interview: 옵션 질문 시스템 | 2h |
| 3 | apply: 템플릿 복사 + config + rules + 빈 폴더 | 2h |
| 4 | AGENTS.md 템플릿 (1 종, framework 공통) | 0.5h |
| 5 | rule pack 자동 생성 (stack 기반) | 3h |
| 6 | jcode 통합 (.lazy-harness/AGENTS.md 인식) | 2h |
| 7 | 2번째 host 검증 + 회귀 fix | 3h |
| 8 | CLI 골격 + 분기 + doctor 통합 | 1h |

### 의존성

- N2.5 (AGENTS.md 템플릿, SearchProvider)

### Success criteria

- 새 host 에서 `lazy init` → 30 분 안에 첫 commit (cold-start budget)
- AGENTS.md 모든 host 동일 (host 별 변종 0)
- `lazy doctor` D01~D07 통과 (init 직후)

### Risks

- **30 분 budget 미달성**: dogfooding 후 보정. interview 질문 줄이기 + inspect 강화.
- **jcode 통합 막힘**: jcode patch 안 되면 `.jcode/AGENTS.md` 에 `@include` 우회.

---

## N5 — Auto Record Update Executor (15h)

**목적**: hook 이 누락 layer 지적 → AI 가 직접 record 갱신. 사람 입력 비용 0.

### 작업 분해

| # | 작업 | 시간 |
|---|---|---|
| 1 | `scripts/record-update-executor.ts` 골격 | 3h |
| 2 | DDD writer 클래스 | 2h |
| 3 | SDD writer 클래스 | 2h |
| 4 | BDD writer 클래스 | 2h |
| 5 | ADR writer 클래스 | 2h |
| 6 | Loop safety (max 3회) + diff cap | 2h |
| 7 | host-pilot 검증 (5 commit 평균 70% auto-update) | 2h |

### 의존성

- N1, N3 (gate finding 을 input 으로 받음)
- N2.5 (SearchProvider 로 갱신 대상 record 검색)

### Success criteria

- host-project 변경 5 회에서 평균 ≥ 70% auto-update 비율
- 갱신 후 N1 Layer Impact Gate 자동 재실행 (loop safety: max 3 회)
- diff cap 준수 (Principle 5)

---

## N6 — Drift / Conflict Detector (8h)

**목적**: 같은 개념이 여��� 곳 다르게 정의 → 자동 검출 + 8-step Conflict Resolution 진입.

### 작업 분해

| # | 작업 | 시간 |
|---|---|---|
| 1 | `scripts/drift-detector.ts` (term/contract/scenario 중복) | 3h |
| 2 | 8-step Conflict Resolution flow 진입 | 2h |
| 3 | 자동 정정 + 사람 ask 분리 | 1.5h |
| 4 | host-pilot 검증 | 1.5h |

### 의존성

- N2.5 (SearchProvider)

---

## N7 — Portable Report (8h)

**목적**: gate / question / record-update 결과를 외부로 export. Framework 자가 개선 evidence.

### 작업 분해

| # | 작업 | 시간 |
|---|---|---|
| 1 | `scripts/report-export.ts` (markdown + JSON) | 3h |
| 2 | `schemas/portable-report.schema.json` | 1h |
| 3 | 분기당 1회 자동 생성 hook | 2h |
| 4 | 첫 framework 개선 ADR 작성 (report 근거) | 2h |

### 의존성

- N1, N3, N5

---

## N8 — Lifecycle Hook 통합 (8h)

**목적**: response.completed / pre-commit / pre-push 단일 entry. Silent skip 0.

### 작업 분해

| # | 작업 | 시간 |
|---|---|---|
| 1 | hooks/response-completed.ts 통합 entry | 2h |
| 2 | pre-commit chain 통합 | 2h |
| 3 | pre-push chain 통합 | 1h |
| 4 | Unified Result Schema 강제 | 1h |
| 5 | 사람-친화 메시지 + R1~R4 회복 후보 | 1h |
| 6 | host-pilot 1 주일 silent skip 0 검증 | 1h |

### 의존성

- N1, N3, N5

---

## 측정 기준 (dogfooding metrics)

ADR 0024 의 "이론적 우위 = 실제 우위 보장 아님" 약점 보완. N5 완료 후 측정:

### M1 — AI 룰 준수율

- 같은 commit (예: 새 mutation 추가) 을 AI 에게 시키고 cache invalidate 호출 누락 빈도 측정
- 얇은 AGENTS.md + record 검색 vs 두꺼운 AGENTS.md (가설 검증)
- 목표: ≥ 95% 룰 준수 (즉 5% 미만 위반)

### M2 — AGENTS.md drift

- 3 개월 후 AGENTS.md 의 룰과 실제 코드 일치도
- 얇은 AGENTS.md 가설: drift ≤ 1 건 (거의 안 변하니까)

### M3 — 검색 호출 빈도 / token 비용

- AI 의 grep + Read 호출 빈도 vs token 비용
- 두꺼운 AGENTS.md prompt 비용과 비교
- 목표: token 비용 ≤ 두꺼운 AGENTS.md 의 80%

### M4 — Cold-start 30 분

- 새 host 에서 `lazy init` ~ 첫 commit 까지 wall clock 시간
- 목표: ≤ 30 분 (2 번째 host 에서 검증)

### M5 — Auto-update 비율

- N5 의 success criteria: 5 commit 평균 ≥ 70% auto-update
- 누적 진입 비용 0 약속 검증

### 측정 시점

- M1, M3: N5 완료 후 (record 가 자라야 의미 있음)
- M2: 3 개월 사용 후
- M4: N4 완료 직후 + 1 개월 후
- M5: N5 완료 직후

각 metric 결과는 `metrics/dogfooding-MMYY.md` 에 기록.

---

## 결정 ledger

- ADR 0023 — N2 host-pilot validation (검증 결과 유지)
- ADR 0024 — AI-first framework redesign (본 roadmap 의 N2.5/N3/N6 설계 근거)
- ADR 0025 — Portability single entry point (본 roadmap 의 N4 설계 근거)

---

## 다음 단계

1. **본 roadmap commit** (`Docs: ai-first redesign roadmap`)
2. **N2.5 작업 시작** (5~7h)
3. **N2.5 commit by commit** (Refactor → Feat 4개 → Test)
4. **N2.5 완료 후 N3 진행**

사용자가 OK 하면 N2.5 시작.
