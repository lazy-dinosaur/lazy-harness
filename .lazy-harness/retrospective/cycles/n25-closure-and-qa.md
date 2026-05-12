# N2.5 종결 + Q&A 정리 (2026-05-13)

본 문서는 N2.5 milestone 종결 직후 사용자와의 Q&A 세션에서 결정·확정된 내용을 record 로 보존. 다음 session 인계 + dogfooding 가이드 + N3/N4 의사결정 근거 모두 포함.

## 1. N2.5 완료 commit 5종

```
4d05e64f  Docs:     jcode integration wiring 가이드 (JCODE-INTEGRATION.md)
304f0bd4  Test:     N2.5 self-test 편입 (hook 5 case + AGENTS.md invariants)
ac70b765  Feat:     tool.execute.before hook + session-cache (Layer 2 force gate)
03cb2502  Feat:     .lazy-harness/AGENTS.md 신설 (framework grammar, 57 줄)
10a8aac9  Refactor: SearchProvider 추상화 + IDF/burst/stopwords 제거
```

검증: `bun run lazy:test` = **20/20 green** (기존 18 + N2.5 신규 2).

## 2. 결정된 사항 (확정)

### 2.1 가중치 layer-aware 안 박음 (옵션 C 채택)

resolver 의 deterministic 가중치:
- `1.0` cross-layer link
- `0.95` test-stem (sibling test 파일)
- `0.85` path-stem exact (record 파일명 일치)

세 점수에 **layer (DDD/SDD/BDD/TDD/ADR/SSOT) 가중치 곱하지 않음**. 이유:

1. ADR 0024 원칙 일관 — framework 는 deterministic 만, 의미적 판단은 AI 위임
2. AGENTS.md §1 표가 이미 변경 종류 → 우선 layer 가이드 제공
3. host 무관 (portability 안전)
4. 추가 코드 0
5. 나중에 dogfooding 으로 AI 가 헤매는 게 보이면 추가 가능 — 역방향 (박은 거 빼기) 어려움

→ **현 상태 유지.**

### 2.2 deterministic 가중치 vs 매직 상수 구분

| 종류 | 예시 | 처리 |
|---|---|---|
| deterministic (있다/없다 binary 매칭의 신뢰도 라벨) | 1.0 / 0.95 / 0.85 | **유지** |
| 매직 상수 (host-corpus 의존 임계값) | 0.3 / 0.18 / 0.5 | **폐기** (N2.5 에서 제거) |

기준: "정당화 가능한 숫자" vs "왜 이 값?" 답 못 함.

### 2.3 6 layer 모두 항상 검색

AGENTS.md §1 표는 "어느 layer 부터 깊게 읽을지" 가이드. 검색 자체는 **6 폴더 동시**:

```bash
grep -rli '<token>' .lazy-harness/{domain,spec,behavior,tests,decisions,ssot}/
```

ADR (`decisions/`) 도 항상 포함. ADR 은 다른 5 layer 의 "근거" 라 cross-check 필수.

## 3. 다음 작업 결정

**옵션 A 채택: wiring + dogfooding** (vs C = N4 lazy init 바로 진행)

### 3.1 wiring 이 무엇인가

`.jcode/config.toml` 에 두 가지 등록:
1. **AGENTS.md inject** → 매 session 시작 시 AI 한테 자동 첨부
2. **tool.execute.before hook** → Edit/Write 직전 hook 으로 payload pipe

**박힌 부품 (.lazy-harness/) 과 사용 측 (jcode) 사이 전선.** 현재 본 host 는 `.jcode/` 자체가 없음 = wiring 0 = 모든 hook + AGENTS.md dormant.

### 3.2 wiring 은 본래 N4 의 일부

정상 흐름:
```
bunx lazy-harness init  (= N4, 미구현)
  ├── inspect: stack 자동 감지
  ├── interview: 5~10 옵션 질문
  └── apply:
      ├── .lazy-harness/ (framework 부품)
      └── .jcode/config.toml (wiring) ← 자동
```

본 host 는 framework 가 **만들어진** 특수 case — N4 가 없는 채 부품만 누적. install 한 게 아님. 그래서 수동 wiring 필요.

### 3.3 수동 wiring vs N4 대기

| | 수동 (지금) | N4 대기 (~2주) |
|---|---|---|
| 비용 | 5~10분 | 0 (지금) + 15.5h (N4 구현) |
| dogfooding 시작 | 즉시 | 2주 후 |
| eat own dog food | ✅ | ❌ 2주 dormant |
| N3 의 input 데이터 | 모음 | 추측 기반 |

→ **수동 wiring 채택.** 5~10분 비용 vs 2주 검증 공백.

### 3.4 wiring 영향 범위

`.jcode/config.toml` (project-local) = 본 host 만 영향. 글로벌 `~/.jcode/` 영향 0. 다른 host 영향 0.

### 3.5 git 처리

본 host 는 experimental repo 라 `.jcode/` 도 commit 해서 contributor 와 공유 가능. 또는 `.git/info/exclude` 로 개인 한정. 사용자가 commit 선호 시 그대로.

## 4. 로드맵 위치

```
N2    ✅ host pilot (~2 주 전)
N2.5  ✅ 3-Layer Defense (방금 종결)
N3    ⏳ Drift / Conflict Detector (8h)
N4    ⏳ Lazy init / portability (15.5h)
N5    ⏳ Onboarding telemetry (~10h)
N6    ⏳ SearchProvider 확장 (RAG/subagent) (~12h)
N7    ⏳ Reporting / canonical view / metrics (~10h)
N8    ⏳ Public 0.1 (npm publish, docs, skill) (~22h)
```

**N4 는 마지막 아님. N8 이 진짜 마지막** (public release).

### 4.1 N3 = Drift / Conflict Detector

- 같은 개념이 record 여러 곳에서 다르게 정의됐을 때 검출
- 8-step Conflict Resolution 흐름 진입 (구조화 옵션 질문)
- 함정: dogfooding 없이 짜면 또 매직 상수 (예: "정의 sim < 0.7" 같은 임계값)
- → dogfooding 1~3 일로 실제 conflict 사례 3+ 수집 후 시작 권장

### 4.2 다른 host 로 빼기 = N4 (portability)

- N4 ≠ N8. N4 는 "2번째 host 에 박기", N8 은 "독립 repo + npm publish"
- 둘 다 의미상 분리
- N4 적기: framework **1 주 변경 없이 안정** + dogfooding 으로 핵심 함정 정리 후
- 후보 host: `~/dev/jcode` (1순위) > medivance production > 새 작은 프로젝트 > 외부 사람 host
- **현재 기준 ~2 주 후, jcode 본체가 첫 후보**

### 4.3 권장 순서

```
오늘    : wiring 박음 + dogfooding 시작
~3 일후 : false-deny / 가중치 / drift 사례 수집
~1 주후 : (필요 시) N3 + 가중치 layer 보강
~2 주후 : framework 안정 → N4 (jcode 에 init)
~1 달후 : 2 host 양쪽 안정 → N5/N6 (telemetry, RAG)
~2 달후 : N7/N8 (reporting, public 0.1)
```

너무 일찍 N4: 매주 sync 비용 + 함정 두 번 고침
너무 늦게 N4: portability 검증 안 된 채 N5~N7 쌓아 N8 직전 폭발

## 5. SSOT / 통합 요구의 분류

사용자 질문 "ssot 니까 다 검색하고 최신정보로 통합?" 을 3 요구로 분리:

| 요구 | 처리 milestone |
|---|---|
| A. 작업 시 6 layer 다 읽기 | ✅ N2.5 hook (강제 중) |
| B. record 간 모순 자동 검출 | ⏳ N3 (drift detector) |
| C. 통합 canonical view 자동 생성 | ⏳ N7 (또는 N3 확장) |

C 는 roadmap 명시 안 됨. dogfooding 으로 가치 확인되면 N7 에 추가.

## 6. 인코딩 손상 회귀

이전 ledger commit `759ddbb0` 에서 Edit 도구가 일부 한글 음절을 `\ufffd` 로 손상시켜 commit. N2.5 commit 4 (`304f0bd4`) 에서 6 군데 복구. doctor D08 가 향후 같은 손상 즉시 감지 (`scripts/doctor.py:282`).

본 retrospective 자체도 같은 위험 — 작성 후 grep 검증 필요.

## 7. 잔재 todo 정리

이전 session (`session_koala_*`) 의 "reporting facilities" 작업 5 todos 가 본 세션 reminder 로 새어나옴. scope 가 N7 reporting 으로 흡수되었다고 판단 → 모두 cancelled + audit-trail 노트 추가 + `.pre-cancel-bak` 백업. 향후 N7 진행 시 재open 검토.

## 8. 다음 session 으로의 인계

### 8.1 즉시 할 일

1. **수동 wiring 박기** — `.jcode/config.toml` 생성, hook + AGENTS inject 등록 (5~10분)
2. 새 jcode session 띄워서 발동 확인 (Q3 검증 절차: AGENTS inject / force gate / session cache)
3. 1~3 일 dogfooding 시작

### 8.2 dogfooding 동안 수집할 데이터

- false-deny 빈도 (hook 이 정당한 작업도 막는 경우)
- AGENTS.md inject 가 AI 행동 실제로 바꾸는지
- 6 layer 동률 출력 시 AI 가 헤매는지 (→ 가중치 layer-aware 재검토)
- record 간 conflict 사례 (→ N3 의 fixture)
- session-cache TTL 적정성

### 8.3 데이터 수집 위치

`.lazy-harness/logs/skipped.jsonl` (AGENTS.md §3) — silent skip 사유 기록 위치 활용. 추가로:
- `.lazy-harness/.cache/session/` 의 cache hit/miss 패턴 분석
- `.lazy-harness/logs/actions.jsonl` 의 hook deny 빈도

## 9. 핵심 원칙 재확인

- **AGENTS.md = grammar** (얇음, 모든 host 동일, ≤100 줄)
- **record = vocabulary** (host 특화)
- **framework = deterministic only**, 의미적 매칭은 AI 위임
- **portability = AGENTS.md 가 host-agnostic 한 한 보장**
- **eat own dog food = wiring 박고 dogfooding** (본 결정의 의미)

## 10. 관련 문서

- `.lazy-harness/AGENTS.md` — framework grammar 본체
- `.lazy-harness/JCODE-INTEGRATION.md` — wiring 가이드 (옵션 A/B + 검증)
- `.lazy-harness/decisions/0024-ai-first-framework-redesign.md` — 3-Layer Defense 근거
- `.lazy-harness/decisions/0025-portability-single-entry-point.md` — N4 lazy init 설계
- `.lazy-harness/plans/ai-first-redesign-roadmap.md` — N2.5~N8 전체 plan
- `.lazy-harness/scripts/reference-resolver.ts` — deterministic 매칭 본체
- `.lazy-harness/scripts/search-provider.ts` — semantic 검색 추상화
- `.lazy-harness/hooks/lifecycle/on-tool-execute-before.sh` — Layer 2 hook
- `.lazy-harness/hooks/lifecycle/helpers/check-search-performed.sh` — 검색 흔적 검사 정책
