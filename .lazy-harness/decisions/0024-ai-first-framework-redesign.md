# ADR 0024 — AI-first Framework Redesign: SearchProvider, 3-Layer Defense, AGENTS.md as Grammar

- **Status**: Accepted
- **Date**: 2026-05-12
- **Supersedes (partially)**: ADR 0023 (N2 host-pilot validation) — N2 의 검증된 결과는 유지하되, 그 구현 70% (IDF/burst/stopwords/ADR-keyword/path-stem partial) 는 본 ADR 의 N2.5 작업으로 단순화·교체된다.
- **Related**: ADR 0007 (AGENTS.md injection), ADR 0017 (user-input trigger), ADR 0018 (cross-layer cascade), ADR 0019 (ambiguous detection force gate), ADR 0022 (framework-owned doctor)

## Rule digest

- Status: active
- Layer: ADR
- Scope: framework-global
- Aliases:
  - AI-first 재설계
  - SearchProvider
  - 시맨틱 검색 금지
  - no embeddings
  - LLM 직접 검색
  - 검색 위임
- Applies when:
  - deciding how the framework performs record/semantic search (AI-led vs algorithmic)
  - authoring AGENTS.md content or host-portable bootstrap behavior
  - tempted to add a keyword/IDF/stopword search algorithm to framework tooling
- Must:
  - let AI do semantic search in-context; keep the deterministic resolver to exact matches (cross-layer/test-stem/path-stem)
  - keep AGENTS.md a thin framework-common grammar; host rules live in records as vocabulary
  - enforce via 3 layers: pre-work search, tool.execute.before force-gate, response.completed verification
- Must not:
  - implement search algorithms (IDF/burst/stopwords/ADR-keyword) in framework tooling
  - embed host-specific rules in a thick AGENTS.md
- Record completion:
  - changes to search architecture or AGENTS.md grammar update this ADR and the SearchProvider/resolver self-test
- Related records:
  - `.lazy-harness/decisions/0023-n2-reference-resolver-host-pilot-validation.md`
  - `.lazy-harness/ssot/cli-tool-boundary.md`

## Context

N2 (Map-aware Reference Resolver) host-pilot 5-pass 검증이 precision/recall = 1.0 으로 통과했으나 (ADR 0023), 그 과정에서 다음 문제가 드러났다:

1. **검증 통과를 위해 5 번의 알고리즘 튜닝이 필요했다** — Pass 1 → 2 (manual + IDF stopwords) → 3 (IDF-weighted scoring) → 4 (burst suppression) → 5 (corpus-scaled threshold)
2. **모든 튜닝 결과가 medivance 코퍼스 크기 의존적이다** — IDF threshold `0.3`, burst threshold `max(3, N×0.18)`, score floor `0.5` 모두 매직 상수
3. **다른 host 로 옮기면 재튜닝 필수** — corpus 크기·도메인이 다르면 같은 튜닝값으로 작동 보장 불가

이는 framework portability 의 단일 진입점이 되어야 할 N2 가 실제로는 host-specific 튜닝의 누적 진입 비용을 야기한다는 의미다.

호스트 파일럿 종료 직후 사용자가 던진 질문이 정체성을 흔들었다:

> "이거 검색 알고리즘 아닌가? AI 가 검색하면 되지 않아?"
> "사용하면서 누적되는 게 framework 의 디자인이잖아."

세션 동안 합의된 결론: **N2 의 70% 는 잘못된 추상화**. AI 가 context window 안에서 의미론적 검색을 직접 수행하는 것이 더 정확하고, 더 portable 하고, framework 의 정체성에 부합한다.

## Decision

다음 5 가지를 본 ADR 의 결정 사항으로 박는다.

### 1. Framework 정체성 — AI-first lifecycle enforcement

lazy-harness 는:

- **AI-assisted tool 이 아님** — "사람이 주도, AI 가 보조" 모델 폐기
- **AI-first lifecycle enforcement framework** — AI 가 검색·판단·기록을 주도하고 hook 이 안전망 역할
- **ESLint-like 정적 분석 도구 아님** — 누적 효용 모델 (사용할수록 더 정확해짐)
- **methodology 다원주의** — DDD/SDD/BDD/TDD/ADR/SSOT 모두 동등 대우 (timsquad 가 TDD 일변도인 것과 대조)

이 정체성이 본 ADR 의 모든 후속 결정의 근거다.

### 2. SearchProvider abstraction (검색 알고리즘 제거)

검색 알고리즘 직접 구현 패턴 폐기. 다음 추상화로 교체:

```ts
interface SearchProvider {
  search(query: SearchQuery): Promise<SearchResult[]>
}

// default 구현
class DirectAISearch implements SearchProvider {
  // AI 가 context window 에서 직접 의미론적 매칭
  // "검색어: X, 후보 record 목록: [...]" 형태로 AI 에 위임
}

// optional 구현 (성능 / 비용 trade-off 시)
class SubagentSearch implements SearchProvider {
  // 전용 검색 에이전트에 위임 (Task tool)
}

// future 구현 (RAG)
class RAGSearch implements SearchProvider {
  // 벡터 DB 기반, report-and-knowledge-roadmap.md 의 미래
}
```

**폐기 대상** (N2 의 reference-resolver.ts 에서 제거):

| 항목 | 폐기 이유 |
|------|----------|
| `findAdrKeyword()` (ADR body 전체 토큰화 + 매칭) | 검색 알고리즘 직접 구현, AI 가 더 잘 함 |
| `findPathStem()` 의 partial substring match | 오탐 다수 |
| `computeIdfStopwords()` (런타임 IDF 계산) | O(ADRs × tokens) 비용, host-specific 튜닝 필요 |
| `MANUAL_STOPWORDS` (37개 하드코딩) | 도메인마다 재작성 필요 |
| `ADR_BURST_THRESHOLD = max(3, N × 0.18)` | corpus 크기 의존 매직 상수 |
| `MATCH_SCORE_FLOOR = 0.5` | 매직 상수 |
| `IDF_STOPWORD_THRESHOLD = 0.3` | 매직 상수 |

**유지 대상**:

| 항목 | 유지 이유 |
|------|----------|
| `findCrossLayerLink()` | 명시적 link 매칭, 알고리즘 없음 |
| `findTestStem()` (exact match) | 파일명 정확 매칭, 알고리즘 없음 |
| `findPathStem()` 의 exact stem match | exact match 만 유지, partial 제거 |

예상 단순화: `reference-resolver.ts` 459 줄 → ~80 줄.

### 3. 3-Layer Defense (방어 깊이)

AI 의 능동 준수만으로는 실수 방어 불충분. 다음 3 layer 로 구조화:

```
─────────────────────────────────────────────────────────────────
Layer 1 — AGENTS.md (작업 시작 전)
  AI 가 .lazy-harness/AGENTS.md 의 trigger 매핑을 보고
  → 요청 유형 판별
  → 해당 layer 능동 검색 (SearchProvider.search())
  → session-cache 에 검색 완료 기록
─────────────────────────────────────────────────────────────────
Layer 2 — tool.execute.before (도구 실행 직전)
  hook 이 session-cache 확인
  → 필수 layer 검색 안 했으면 force-gate
  → "DDD 검색 안 함, 진행 차단" 메시지 + AGENTS.md §섹션 인용
  → AI 가 메시지 보고 학습 (왜 막혔는지 알게 됨)
─────────────────────────────────────────────────────────────────
Layer 3 — response.completed (응답 완료 후)
  기존 helper 들 (check-layer-impact.sh 등)
  → 사후 검증 + 누락 force-gate
  → 이미 구현되어 있음 (ADR 0010~0014)
─────────────────────────────────────────────────────────────────
```

각 layer 의 역할:
- Layer 1: 자발적 준수 (AI 능동성)
- Layer 2: 사전 차단 (실수 방지)
- Layer 3: 사후 검증 (놓친 경우 잡기)

### 4. AGENTS.md = Grammar (얇음, framework 공통)

**가장 중요한 디자인 원칙.**

`.lazy-harness/AGENTS.md` 는 AI 의 작업 grammar 만 명시. host 특화 룰은 박지 않는다.

```
AGENTS.md (grammar, ~40~50 줄, 모든 host 동일)
  ↓
  "patient 단어 보면 ddd/ 검색해" (rule)
  ↓
AI 가 검색
  ↓
ddd/patient.md (의미·정의)
adr/0017-patient-risk-policy.md (결정·trade-off)
  ↓
거기서 host 특화 룰 학습 (vocabulary)
```

**원칙: AGENTS.md = grammar, record = vocabulary.**

| | Grammar (AGENTS.md) | Vocabulary (record) |
|---|---|---|
| 내용 | "어디서·언제·어떻게 검색" | "이 host 의 실제 룰" |
| 변동성 | 거의 안 변함 | 작업마다 자람 |
| 양 | ~50 줄 | 무한 |
| Host 차이 | 없음 | 있음 |
| 예 | "도메인 용어 등장 시 ddd/ 검색" | "patient 는 hospitalId 로 격리" |

**왜 이 분리가 우위 (7 차원 분석)**:

| 차원 | 두꺼운 AGENTS (host 룰 박음) | 얇은 AGENTS (grammar 만) |
|---|---|---|
| AI 룰 준수율 | ⚠️ long-context attention 약화 | ✅ 능동 학습 (검색 후 Read) |
| 정보 정확성 | ⚠️ drift 위험 | ✅ record 가 항상 최신 |
| 새 룰 발견 | ❌ AGENTS 갱신 의존 | ✅ adaptive |
| Cold-start | ✅ 즉시 (단, hook 으로 메꿔짐) | ⚠️ hook 의존 |
| Portability | ❌ host 별 변종 | ✅ 1 개로 충분 |
| Token 비용 | 매 session 200~500 줄 | 매 session ~50 줄 |
| 유지보수 | ❌ drift 잦음 | ✅ record 자연 갱신 |

종합: 7 차원 중 5 개에서 얇은 AGENTS.md 우위. 1 개 (cold-start) 약점은 Layer 2 hook 으로 해결.

**되돌릴 수 있는 선택**: 얇은 AGENTS.md 로 시작 → dogfooding 측정 → 약점 명확하면 핵심 룰 5 개 정도 점진 추가 (하이브리드). 두꺼운 AGENTS.md 로 시작하면 host 별 변종 누적 후 단순화 어려움.

### 5. Project Profile = AGENTS.md + config.json + rule pack 묶음

N4 의 `lazy init` 이 host 별로 생성하는 세 묶음:

```
.lazy-harness/
  AGENTS.md             ← framework 공통 grammar (모든 host 동일)
  config.json           ← host 프로파일 (stack, 폴더 구조, 아키텍처)
  rules/                ← rule pack (host 특화 룰 — optional)
    trpc-cache.json     ← 예: mutation invalidation 룰
    multi-tenancy.json  ← 예: hospitalId 필터 룰
```

- **AGENTS.md**: framework 공통, lazy init 이 1 종 템플릿 복사
- **config.json**: host 자동 감지 + interview 답변 반영
- **rule pack**: stack 기반 자동 생성, host 가 점진 추가

host 특화 룰의 진짜 자리는:
- 결정·trade-off → `.lazy-harness/decisions/00XX-*.md` (ADR)
- 도메인 용어 → `.lazy-harness/ddd/*.md` (DDD)
- API/contract → `.lazy-harness/sdd/*.md` (SDD)
- UI flow → `.lazy-harness/bdd/*.md` (BDD)
- 테스트 보호 → `.lazy-harness/tdd/*.md` (TDD)
- 단일 진실원 → `.lazy-harness/ssot/*.md` (SSOT)

자동 생성 가능한 stack 룰만 `rules/` 에 (예: tRPC mutation 누락 검출 패턴).

## Consequences

### 즉시 영향

- **ADR 0023 의 검증 결과는 유지**: precision/recall = 1.0 자체는 N2 가 "검색 가능"하다는 증명. 단, 그 구현 70% 는 본 ADR 의 N2.5 에서 교체.
- **N2 status = done** (ADR 0023 종결), **N2.5 신설** (본 ADR 의 작업)
- **N4 priority high → critical**, **estimatedHours 8h → 15.5h** (얇은 AGENTS.md 덕분에 LLM 보강 작업 제거로 8h 단축, 그러나 portability 단일 진입점 책임 추가로 24h → 15.5h 순감)
- **N9 (별도 portability milestone) 불신설** — 모든 portability 책임이 N4 에 흡수

### 장기 영향

- 새 host 옮길 때 `lazy init` 한 번이면 30 분 안에 동작 (검증은 dogfooding 후)
- 검색 알고리즘 직접 구현 패턴을 N3 (side-effect gate), N6 (drift detector) 에서도 반복하지 않음 (E2 원칙)
- methodology 다원주의 원칙이 N3, N5 의 모든 layer 동등 대우로 이어짐
- 효과 측정은 dogfooding 6 주 ~ 3 개월 후 (룰 위반율, drift, 검색 빈도, token 비용)

### Trade-off / 정직한 약점

- **Cold-start 약점**: 얇은 AGENTS.md 는 첫 작업에서 AI 가 검색 안 하면 host 룰 모름. Layer 2 hook 으로 해결하지만 hook 누락 시 약점 드러남.
- **검색 호출 빈도 증가**: 매 작업마다 grep + Read 발생. token/latency 비용 ↑. (반면 두꺼운 AGENTS.md 는 매 session 시작 시 prompt 비용 ↑.) 케이스 의존이라 측정 필요.
- **이론적 우위 = 실제 우위 보장 아님**: 7 차원 중 5 우위는 가설. dogfooding 측정 후 보정 가능.

## Implementation Plan

다음 4 가지 작업을 N2.5 milestone 으로 묶음 (5~7h 예상):

1. **SearchProvider abstraction**: `interface SearchProvider` + `DirectAISearch` 구현 (1.5h)
2. **N2 단순화**: `reference-resolver.ts` 의 IDF/burst/stopwords/keyword 제거, ~80 줄 (1.5h)
3. **`.lazy-harness/AGENTS.md` 작성**: grammar 만, ~50 줄 (1h)
4. **`tool.execute.before` hook + session-cache**: force-gate helper (1.5h)
5. **회귀 검증**: 기존 4 fixtures 모두 통과 (1h)

각 작업은 별도 commit. Implementation 끝나면 ADR 0023 의 host-pilot 을 N2.5 결과로 재실행해서 precision/recall 회귀 없음 확인.

## Alternatives considered

1. **N2 유지 + 매직 상수만 더 정교화**: 거부. host portability 가 해결 안 됨.
2. **두꺼운 AGENTS.md (host 룰 박음)**: 거부. 7 차원 중 5 차원에서 열위. 되돌릴 수 없는 선택.
3. **RAG 즉시 도입**: 거부. 인프라 (벡터 DB) 비용 + medivance 코퍼스 규모 (40 records) 에서 과잉. SearchProvider 추상화만 두고 future work.
4. **검색 알고리즘 자체 보존 (subagent 로만 위임)**: 거부. 알고리즘 직접 구현 패턴이 N3/N6 에서 반복될 위험.

## References

- ADR 0023 — N2 host-pilot validation (검증 결과 유지)
- ADR 0007 — AGENTS.md injection (`.jcode/AGENTS.md` 와 `.lazy-harness/AGENTS.md` 역할 분리 명시 필요)
- ADR 0022 — framework-owned doctor (N4 의 doctor 통합 근거)
- trails/02-north-star-milestones.xml — N2.5 신설, N4 격상
- plans/ai-first-redesign-roadmap.md — 본 ADR 의 후속 실행 계획
- `/tmp/jcode-bg-tasks/040210li73.output` — 본 ADR 작성 시 참조한 atlas subagent 정리
- `/tmp/lazy-harness-agents-md-correction.md` — 얇은 AGENTS.md 통찰 메모

## Implementation map

- Status: `needs-review`
- Primary files:
  - `.lazy-harness/AGENTS.md` — AI-first record-search grammar and default-unknown behavior.
  - `.lazy-harness/scripts/search-provider.ts` — SearchProvider interface and DirectAISearch prefilter.
  - `.lazy-harness/scripts/reference-resolver.ts` — simplified deterministic resolver that delegates semantic search to AI/SearchProvider rules.
  - `.lazy-harness/scripts/self-test.py` — SearchProvider canonical dirs and reference resolver checks.
- Key symbols:
  - `SearchProvider`, `DirectAISearch`, `SubagentSearch`, `RAGSearch` (`search-provider.ts`) — AI-first search abstraction and placeholders.
  - `findPathStem`, `findTestStem`, `findCrossLayer` (`reference-resolver.ts`) — exact deterministic resolver pieces retained after algorithm removal.
  - `check_search_provider_canonical_record_dirs`, `check_reference_resolver` (`self-test.py`) — executable coverage.
- Flow:
  1. AGENTS grammar requires record-first/default-unknown search by the AI.
  2. Deterministic resolver surfaces exact candidates only.
  3. Semantic interpretation remains with the AI/searcher rather than an IDF/burst keyword algorithm.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py` protects SearchProvider canonical record dirs and reference resolver fixtures.
  - Keep this map `needs-review` because the ADR also defines broad identity/governance and future Subagent/RAG paths that are intentionally not fully implemented.
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0023-n2-reference-resolver-host-pilot-validation.md`
  - SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`
- Machine index:
  - graph ids: `kg_adr0024_search_provider`, `kg_adr0024_reference_resolver_simplified`
  - generated index key: `pending`
