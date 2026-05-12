# Lazy-Harness AI 행동 양식

너 (AI) 는 `lazy-harness` 가 활성된 host 에서 작업한다.
`.lazy-harness/` 는 이 프로젝트의 institutional memory 다.
이 파일은 framework 공통 grammar 만 정의한다. host 특화 룰은 record (DDD/SDD/BDD/TDD/ADR/SSOT) 에 있다.

## 1. Layer ↔ Trigger 매핑 (반드시 외울 것)

| Layer | 폴더 | 검색 트리거 |
|---|---|---|
| **DDD** | `.lazy-harness/domain/` | 도메인 용어 / 비즈니스 규칙 등장 |
| **SDD** | `.lazy-harness/spec/` | API / contract / component 만짐 |
| **BDD** | `.lazy-harness/behavior/` | UI flow / 사용자 행동 변경 |
| **TDD** | `.lazy-harness/tests/` | 버그 fix / regression / 보호 케이스 |
| **ADR** | `.lazy-harness/decisions/` | 설계 결정 / trade-off / "왜 이렇게" |
| **SSOT** | `.lazy-harness/ssot/` | config / schema / env / 단일 진실원 |

## 2. 4 단계 흐름 (작업 시작 ~ 종료)

### 2.1 요청 받자마자 검색 (필수)

구현 / 수정 / 추가 / 디버그 의도가 보이면 즉시:

```bash
grep -rli '<핵심 토큰>' .lazy-harness/{domain,spec,behavior,tests,decisions,ssot}/
```

또는 N2 resolver 활용:

```bash
bun .lazy-harness/scripts/reference-resolver.ts --file <path> --format ask
```

### 2.2 발견된 record 끝까지 Read

거기 있는 정의·제약·결정이 host 의 진짜 룰. AGENTS.md 가 아니라 **record 가 single source of truth**.

### 2.3 결정 분기 시 옵션 질문 (자유 문답 금지)

3~5 후보 + `(Recommended)` 표시 + type-your-own 마지막. ADR 0019 / Principle 21.

### 2.4 작업 후 누적

새 결정 / 시나리오 / 제약 / 도메인 용어 등장 → 해당 layer 에 record 추가·갱신. 누락은 hook 이 잡아낸다.

## 3. Silent Skip 금지

의식적으로 위 단계를 건너뛸 때는 사유를 `.lazy-harness/logs/skipped.jsonl` 에 한 줄 기록한다. "looks fine" 으로 통과하지 말 것.

## 4. Framework Contract

- 능동 검색하면 hook 은 silent
- 깜빡하면 `tool.execute.before` hook 이 force-gate 로 막고 본 파일의 §섹션 인용
- record 가 빈약하다? 누적해라. 1 주 동안 어느 layer 도 안 자라면 framework 활용 실패 신호
- 검색 알고리즘 직접 구현 금지 (ADR 0024 §2). semantic 검색이 필요하면 SearchProvider (`search-provider.ts`) 통해 위임

이게 전부. 세부 host 룰은 record 가 답한다.
