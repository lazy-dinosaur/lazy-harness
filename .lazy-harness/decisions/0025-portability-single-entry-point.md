# ADR 0025 — Portability Single Entry Point: N4 흡수, N9 불신설

- **Status**: Accepted
- **Date**: 2026-05-12
- **Related**: ADR 0024 (AI-first redesign), ADR 0022 (framework-owned doctor), ADR 0007 (AGENTS.md injection), trails/02-north-star-milestones.xml

## Context

Framework portability (다른 host 에 옮겨도 동작하는가) 를 별도 milestone N9 로 분리할지, 또는 N4 (Project Profile + Bootstrap) 에 흡수할지가 미결정 상태였다.

세션 토론에서 다음 5 가지 portability 의존성이 드러났다:

1. **IDF 튜닝** — corpus 크기 의존 매직 상수 (`0.18`, `0.3`, `0.5`)
2. **fixture path** — 절대경로 하드코딩 (`/home/lazydino/...`)
3. **cross-layer links** — host 구조 의존 (어떤 layer 가 어떤 layer 와 연결되는지)
4. **AGENTS.md 룰** — project 별 커스텀 행동 양식 (얇은 AGENTS.md 결정 후엔 framework 공통이지만 host 감지는 필요)
5. **doctor profile** — D01~D07 passes 가 host 마다 다름

ADR 0024 의 결정 (SearchProvider abstraction + 얇은 AGENTS.md) 이 이 의존성 일부를 자동 해소했다:
- IDF 튜닝 → SearchProvider 가 AI 직접 검색으로 교체, 튜닝 불필요
- AGENTS.md 룰 → grammar 만 박는 단일 템플릿, host 차이 없음

남은 의존성 (fixture path, cross-layer links, doctor profile) 은 여전히 host 별 설정이 필요하다.

## Decision

**별도 N9 milestone 을 만들지 않는다. 모든 portability 책임을 N4 (Project Profile + Bootstrap) 에 흡수한다.**

`lazy init` CLI 가 inspect → interview → apply 3 단계로 한 번에 해소:

### inspect (자동 감지)

```ts
inspect() {
  // 1. stack 자동 감지 (package.json, Cargo.toml, go.mod, ...)
  detectStack()
  
  // 2. 폴더 패턴 추출 (src/, app/, lib/, ...)
  detectFolderConvention()
  
  // 3. 기존 AGENTS.md / CLAUDE.md 가 있는지 (host 가 이미 있다면 참조만)
  detectExistingDocs()
  
  // 4. fixture path 자동 감지 (현재 working directory 기준 상대경로화)
  detectFixturePath()
}
```

산출: `inspect.json` (이전 매직 상수 → host 자동 감지 값)

### interview (구조화 옵션 질문 5~10개)

```
질문 ���시:
1. 이 프로젝트의 stack 은? (자동감지: Electron + React + Prisma) [확인/수정]
2. Force gate 모드는? [strict / observation / relaxed (Recommended for new host)]
3. BDD 시나리오는 어디에 보관? [.lazy-harness/bdd/ (default) / 다른 경로]
4. Multi-tenancy 룰 강제할까? [yes (Recommended if host 는 multi-tenant) / no]
5. Cross-layer link 자동 생성할까? [yes (inspect 기반) / no (수동 등록)]
...
```

원칙:
- **inspect 가 감지한 것은 묻지 않음** (확인만)
- **자유 문답 금지**, 옵션 3~5 개 + Recommended 표시 (ADR 0019, Principle 21)
- type-your-own 옵션은 마지막에 (탈출구)

산출: `answers.json` (사용자 결정 ledger)

### apply (산출물 생성)

```
.lazy-harness/
  AGENTS.md                ← framework 공통 grammar 템플릿 복사 (1 종, 변형 없음)
  config.json              ← inspect + answers 종합
  rules/                   ← stack 기반 자동 생성 룰 pack
    [stack 별 룰 파일들]
  cross-layer/
    links.json             ← 빈 시작 (사용 중 누적)
  decisions/
    0001-bootstrap.md      ← interview 결정 영구 기록 (decision ledger)
  ddd/                     ← 빈 폴더
  sdd/                     ← 빈 폴더
  bdd/                     ← 빈 폴더
  tdd/                     ← 빈 폴더
  ssot/                    ← 빈 폴더
  logs/                    ← 빈 폴더
  .session-cache/          ← 빈 폴더
```

산출: 위 디렉토리 트리. 이 시점부터 `lazy doctor` 가 통과해야 함.

### 마지막 단계 (검증)

```
$ lazy doctor
✓ D01 framework branch presence
✓ D02 AGENTS.md present
✓ D03 config.json valid
✓ D04 cross-layer/links.json present (empty allowed)
✓ D05 record folders all present (empty allowed)
✓ D06 hook scripts wired
✓ D07 SearchProvider configured

All 7 checks passed. lazy-harness is ready.
```

성공 기준: `lazy init` 시작부터 doctor 통과까지 **30분 이내** (cold-start budget).

## Consequences

### 즉시 영향

- **N9 (portability milestone) 신설 안 함** — milestones xml 에 추가 안 됨
- **N4 priority 격상**: high → critical (portability 의 단일 진입점이므로)
- **N4 estimatedHours 보정**: 원래 8h → 24h 까지 ballooned 됐다가, 얇은 AGENTS.md 결정 (ADR 0024) 으로 LLM 보강 작업 (8h) 제거되어 **최종 15.5h**
- **N4 successCriteria 보강**:
  - "새 host 에서 `lazy init` 한 번, 30분 이내 첫 작업 가능"
  - "2번째 host 에서 회귀 0 (medivance 외 다른 repo 에서 검증)"
  - "AGENTS.md 는 framework 공통 단일 템플릿, host 별 변종 0"

### N4 의 진짜 시간 분해 (24h → 15.5h)

| 작업 | 24h 추정 (이전) | 15.5h 추정 (보정) | 차이 |
|---|---|---|---|
| inspect (stack 감지 + AGENTS 파싱 + 폴더 패턴) | 4h | 2h | -2h (AGENTS 파싱 불필요, host 의 기존 AGENTS 안 건드림) |
| interview (옵션 질문 시스템) | 2h | 2h | 0 |
| apply (템플릿 + LLM 보강 하이브리드) | 4h | 2h | -2h (LLM 보강 제거, 단순 템플릿 복사) |
| AGENTS.md 템플릿 4~5 변종 | 2h | 0.5h | -1.5h (1 종만, framework 공통) |
| rule pack 자동 생성 | 3h | 3h | 0 |
| jcode 통합 (.lazy-harness/AGENTS.md 인식) | 2h | 2h | 0 |
| 2번째 host 검증 + 회귀 fix | 3h | 3h | 0 |
| 골격 (CLI entry, inspect/interview/apply 분기) | 4h | 1h | -3h (단순화 효과) |
| **합계** | **24h** | **15.5h** | **-8.5h** |

### 장기 영향

- 새 host 옮길 때 `lazy init` 한 번 → 30분 안에 동작 (검증은 dogfooding 후)
- N4 가 framework portability 의 단일 책임이 되어 다른 milestone (N3, N5, N6) 은 portability 고민 안 해도 됨
- "이 milestone 이 portable 한가?" 라는 질문이 모든 후속 작업에서 불필요 (N4 가 해결한다고 약속)

### Trade-off / 정직한 약점

- **N4 가 critical 단일 지점이 됨**: N4 가 실패하면 framework 전체가 portable 하지 않음. 단일 실패점.
- **30분 cold-start 약속이 검증 안 됨**: 이론적 추정. dogfooding 후 보정 필요.
- **inspect 가 완벽하지 않으면 interview 가 길어짐**: 자동 감지 실패 시 사용자에게 많은 질문 → cold-start 시간 ↑

이 약점들은 N4 작업 중 측정 + 보정으로 해소. 별도 milestone 분리는 디자인 복잡도만 늘림.

## Alternatives considered

1. **N9 별도 milestone**: 거부. portability 가 다른 milestone 들과 strongly coupled (특히 N4 의 bootstrap, N2.5 의 AGENTS.md 디자인) — 분리하면 책임 경계 불분명.
2. **portability 를 매 milestone 의 successCriteria 에 포함**: 거부. 책임 분산 → 어느 milestone 도 책임 안 짐 위험.
3. **N4 를 단순 "config 파일 생성" 으로 축소 + portability 는 사용자 매뉴얼로**: 거부. cold-start 30분 약속 깨짐. AI agent 가 framework 옮길 때 매뉴얼 못 읽음.

## References

- ADR 0024 — AI-first redesign (SearchProvider, 얇은 AGENTS.md 가 portability 의존성 일부 해소)
- ADR 0022 — framework-owned doctor (N4 의 doctor 통합 근거)
- ADR 0019 — ambiguous detection force gate (interview 의 옵션 강제 근거)
- ADR 0007 — AGENTS.md injection (jcode 와 `.lazy-harness/AGENTS.md` 의 역할 분리)
- trails/02-north-star-milestones.xml — N4 격상 반영
- plans/ai-first-redesign-roadmap.md — N4 작업 분해
