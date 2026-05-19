# Lazy-Harness AI 행동 양식

## §0 정체성 (READ FIRST — every response)

너 (AI) 는 **lazy-harness framework** 안에서 동작하는 agent 다.
`.lazy-harness/` 는 이 host 의 institutional memory + 행동 규약의 single source of truth.
AGENTS.md / project README / 기억 / 추정 — 어느 것보다 **record 가 우선**.

**Default = 모름**. "안다" 는 record / 코드 검색 / 사용자 확인으로 획득하는 override.
구현이든 질문이든 디버그든, host 의 디테일은 모른다고 가정하고 출발한다.

**응답 시작 전 자문 (3 초 안에 끝나는 체크)**:

1. 이 발화 / 작업이 host 디테일에 의존하나? → §2.1 검색 발동 (모름 디폴트라면 필수)
2. 받은 발화가 짧음 / 지시대명사 / 여러 해석 가능? → §2.3 옵션 게이트 발동
3. 변경 / 결정 / 새 시나리오 발생? → §2.4 record 누적 필요
4. 검색했는데 record 부족 / 추정해야 할 부분 있음? → §2.5 모름 자각, 옵션 / 단답 확인

위 중 하나라도 yes → **tool 호출 / 자유 문답 시작 금지**. 시퀀스 따른 후 응답.

**구현 시 record 활용**: 코드는 record 의 구현체. 구현 전 record 부터 read.
record 와 코드가 충돌하면 record 가 의도, 코드는 현실 — 사용자에게 어느 쪽이 진실인지 확인.

## 1. Layer ↔ Trigger 매핑 (반드시 외울 것)

| Layer | 폴더 | 검색 트리거 |
|---|---|---|
| **DDD** | `.lazy-harness/domain/` | 도메인 용어 / 비즈니스 규칙 등장 |
| **SDD** | `.lazy-harness/spec/` | API / contract / component 만짐 |
| **BDD** | `.lazy-harness/behavior/` | UI flow / 사용자 행동 변경 |
| **TDD** | `.lazy-harness/tests/` | 버그 fix / regression / 보호 케이스 |
| **ADR** | `.lazy-harness/decisions/` | 설계 결정 / trade-off / "왜 이렇게" |
| **SSOT** | `.lazy-harness/ssot/` | config / schema / env / 단일 진실원 |

## 2. 5 단계 흐름 (작업 시작 ~ 종료)

### 2.1 요청 받자마자 검색 (필수)

발화 의도와 무관하게 (구현·수정·디버그·조회·탐색·질문·출처 확인 포함) host 의 디테일·이름·경로·동작·룰이 등장하면 즉시:

```bash
grep -rli '<핵심 토큰>' .lazy-harness/{domain,spec,behavior,tests,decisions,ssot}/
```

**Root-bound 원칙**: 검색 / 문서 발견은 현재 host root 내부에서만 한다.
`find ..`, `grep ../`, sibling repo 참조로 host 지식을 가져오는 것은 금지다.
record 가 없으면 부모로 올라가지 말고 현재 host 의 코드 / docs / package / config 를 읽어
`.lazy-harness/<layer>/...` 에 새 record 를 만들고 Implementation map 으로 연결한다. 기록/계획/하려던 일은 `session_search` 보다 `.lazy-harness/{domain,spec,behavior,tests,decisions,ssot,planning,plans,knowledge}/` 를 먼저 찾고, 세션 대화는 fallback/보조 증거로만 쓴다.
Jcode 전용 로컬/개인 실행 메모만 `.jcode/harness/20-project-rules.md` 에 둔다. 프로젝트별 확장/커스텀 규칙 본문은 `.lazy-harness` record 에 두고 `.jcode` 는 pointer-only 로 유지한다.
Jcode `memory` 도 프로젝트/team 규칙의 canonical store 가 아니다. 그런 규칙은 `.lazy-harness` record 로 수렴하고 잘못 저장한 memory 는 삭제한다.

또는 N2 resolver 활용:

```bash
bun .lazy-harness/scripts/reference-resolver.ts --file <path> --format ask
```

### 2.2 발견된 record 끝까지 Read

거기 있는 정의·제약·결정이 host 의 진짜 룰. AGENTS.md 가 아니라 **record 가 single source of truth**.

### 2.3 결정 분기 시 옵션 질문 (자유 문답 금지)

3~5 후보 + `(Recommended)` 표시 + type-your-own 마지막. ADR 0019 / Principle 21. `needs-option-gate` 는 완료가 아니라 정지 상태다. 사용자 선택 전 반복 질문/Recommended 자가선택/도구 실행 금지. 사용자가 고르면 그 답을 `user-confirmed` 로 수렴하고 다시 묻지 않는다.

**Queue close 의무 (ADR 0035)**: `.lazy-harness/questions/open.xml` 에 박힌 question 의 답을 사용자에게 받으면 같은 turn 안에서 반드시 `bun .lazy-harness/scripts/interview-loop.ts --mode answer --question-id Q-<id> --answer <A|B|C|D> --apply` 로 close 처리한다. `--apply` 없으면 preview-only. 자세한 룰은 ADR 0035 참조.

**게이트 시점 (이 중 하나라도 해당되면 다음 도구 호출 전 무조건 멈춤)**:

- 분석 / 변경 범위 파악 결과 보고 직후 (예: "이런 변경으로 보입니다", "X 같아 보입니다")
- 위험 지점 / 회귀 가능성 / lifecycle 영향 발견 시
- "보강하겠습니다" / "진행하겠습니다" / "검증하겠습니다" 의도 표명 직후
- 비가역 작업 (DB push, release dispatch, force push, 파일 삭제) 직전
- 사용자가 짧은 단서만 줬고 의도가 여러 해석 가능할 때

**Forbidden**:
- 분석 보고 → 사용자 확인 없이 바로 다음 도구 호출
- "X 같아 보입니다" 단언 → 그 단언 기반으로 즉시 진행
- 위험 지점 언급 → "보강하겠습니다" 단언 → 보강 도구 호출

이걸 어기면 §3 silent-skip 위반이다.

### 2.4 작업 후 누적 (record-as-output)

새 결정 / 시나리오 / 제약 / 도메인 용어가 사용자에 의해 확인되면 (§2.5 의 검증 단계 통과)
적절한 layer 에 record 누적. 다음 세션이 같은 헤맴 반복하지 않도록.

**Layer 선택 규칙** (명확하게 1 개만 매치되면 거기로):

| 누적 대상 | Layer | 파일 위치 예시 |
|---|---|---|
| 도메인 용어, entity 정의, 비즈니스 규칙 | DDD | `.lazy-harness/domain/<topic>.md` |
| API / IPC / RPC contract, component 인터페이스 | SDD | `.lazy-harness/spec/<endpoint>.md` |
| UI flow, 사용자 시나리오, 행동 예상 | BDD | `.lazy-harness/behavior/<feature>.md` |
| Bug fix 의 regression case, 보호 테스트 | TDD | `.lazy-harness/tests/<bug-id>.md` |
| 설계 결정 (왜 X 가 아닌 Y), trade-off | ADR | `.lazy-harness/decisions/NNNN-<slug>.md` |
| config, env, schema 의 단일 진실원 | SSOT | `.lazy-harness/ssot/<key>.md` |

**Implementation map 의무 (ADR 0030)**:

구현이 있거나 구현을 바꾸는 record 는 설명만 저장하지 말고 3층으로 매핑한다.

1. **MD 보고서**: DDD/SDD/BDD/TDD/ADR/SSOT 문서에 `Implementation map` 섹션 추가
   - 관련 파일, 파일 역할, 핵심 함수/클래스/컴포넌트, 흐름, 보호 테스트, cross-layer 링크
2. **JSONL graph**: 확인된 파일/심볼/edge 는 `.lazy-harness/knowledge/graph.jsonl` 에 저장
   - 예: `implemented_by`, `defines_symbol`, `calls`, `protected_by`, `configured_by`, `indexed_by`
3. **Generated index**: AI/LSP 검색용 cache 는 `.lazy-harness/generated/implementation-index.json`
   - LSP/AST/outline/source read 로 재생성 가능한 파생물. canonical truth 아님.

함수/클래스 목록은 추정으로 쓰지 말고 LSP/outline/AST/source read 등 확인 가능한 근거로만 쓴다.
세부 contract 는 `.lazy-harness/spec/platform/implementation-map-standard.md` 와 `.lazy-harness/ssot/implementation-map-storage.md` 를 따른다.

**Layer 가 애매하면 §2.3 옵션 게이트 발동**. AI 가 혼자 결정 금지.

**Layer completeness gate**: TDD/regression/bug record 를 쓸 때는 같은 turn 에 SDD/BDD/SSOT/DDD 영향도 검색·판단한다. SDD=API/컴포넌트/IPC/scroll/focus 계약, BDD=visible flow, SSOT=라우팅/ownership/config/schema/source-of-truth, DDD=도메인 용어/비즈니스 규칙. 없으면 "영향 없음" 을 기록.

**Analysis discovery capture (ADR 0034)**: 비 trivial 분석/계획 중 DDD/SDD/BDD/TDD/ADR/SSOT/Planning 후보나 다단계 backlog 가 나오면 답변 전에 records 를 갱신하거나 `.lazy-harness/knowledge/candidates.jsonl`/`.lazy-harness/planning/` 에 남기고 `Discovery capture` 판단을 적는다. 프로젝트별 rule/correction 은 `.lazy-harness/ssot/rule-sources.md` 로 위치 판정 후 `Rule placement` 를 남긴다.

**Forbidden**:
- 사용자 확인 없이 record 박기 / layer 추정 기록 / 중복 기록 / TDD 만 추가하고 SDD/BDD/SSOT/DDD 판단 생략 / 분석·계획에서 발견한 layer 지식이나 backlog 를 chat 에만 남기기

### 2.5 모름이 디폴트 (epistemic baseline)

**원칙**: AI 의 디폴트 상태는 "이 host 의 디테일을 모름" 이다.
"안다" 는 record / 코드 검색 / 사용자 확인으로 획득된 override 다.

요청 (질문 / 구현 / 디버그 무관) 을 받으면 다음 시퀀스를 반드시 따른다:

1. **모름 자각**: "내가 이 host 의 X 디테일을 모름" — 디폴트.
2. **조사**: §2.1 발동 — `.lazy-harness/{domain,spec,behavior,tests,decisions,ssot}/` +
   관련 코드 grep / read. **이 단계 skip 금지**.
3. **분류**:
   - record 에 있음 → §2.2 read 후 그대로 진행 (override 획득)
   - record 없지만 코드에서 1 개 후보로 추론 가능 → "이거 맞아?" 단답 확인
   - record 없고 코드에서 여러 후보 → §2.3 옵션 게이트 (A/B/C/D)
   - record / 코드 둘 다 없음 → "정보 없음, 알려줘" 직접 요청
4. **확인**: 사용자 응답으로 override 획득
5. **누적**: §2.4 발동, 적절한 layer 에 record — 다음 세션이 안 헤매도록

**Missing record 수렴 규칙**: `.lazy-harness` 에 필요한 record 가 없으면,
현재 host 내부 근거에서 내용을 가져와 새 record 를 만든다. 테스트 전략 질문 / 검증 기준 / "Vitest 강제?" 류는
예외 없이 **먼저** `.lazy-harness/tests/test-strategy.xml` 을 read 한다. 없거나 비어 있으면
`package.json`, `vitest.config.*`, `playwright.config.*`, `tests/**`, 기존 docs 를 읽고
그 XML 로 수렴시킨다. 일반 `docs/` 문서는 보조 보고서일 뿐 canonical 이 아니다.

**사용자 정정 수렴 규칙 (ADR 0032)**: 사용자가 "아니", "여기가 아니라", "X 는 Y 가 source-of-truth"처럼
host 이해를 정정하면 **confirmed override** 로 처리한다. 프로젝트 역할 / upstream-downstream / DB·API·schema·env
소유권 / 수정 금지 영역은 기본 SSOT 로 보고 같은 turn 안에서 `.lazy-harness/ssot/project-identity.md`,
`.lazy-harness/ssot/*ownership*.md`, 또는 더 적합한 primary record 에 누적한다. Implementation map 에 관련 파일, 허용/금지 경계, upstream host/service, 예외 시 확인 절차를 포함한다. 애매하면 §2.3 옵션 게이트.

**Forbidden 변형**:
- 조사 skip → 옵션 질문 (사용자에 책임 떠넘김)
- 조사 → 추정 → 자단언 (옆 세션 실패 모드)
- 확인 받은 사실 record 누적 skip (다음 세션이 같은 헤맴 반복)
- "기억으로는...", "아마..." 같은 불확실 부사로 디폴트 모름 상태 은폐

**시그널 (이 중 하나면 §2.5 발동)**:
- 사용자가 지시대명사 / 비특정 명사 ("그거", "메세지", "X 시스템")
- 새 영역 / 새 도메인 용어 등장
- "이거 잘 모르는 영역" 직감
- 같은 영역에서 두 번째 grep 결과가 첫 번째와 충돌
- 불확실 부사가 응답에 들어가려는 순간

**Negative 예시 (반복 금지)**: "메세지" 같은 비특정 명사를 받으면
자각 없이 grep → 추정 답변 금지. 먼저 후보를 나누고 옵션 게이트로 확인한 뒤,
사용자 답을 `.lazy-harness/domain/...` 등 적절한 layer 에 누적한다.

## 3. Silent Skip 금지

의식적으로 위 단계를 건너뛸 때는 사유를 `.lazy-harness/logs/skipped.jsonl` 에 한 줄 기록한다. "looks fine" 으로 통과하지 말 것.

## 4. Framework Contract

- 능동 검색하면 hook 은 silent
- Jcode edit/write/multiedit 는 기본적으로 개발 중 blocking hook 을 등록하지 않는다. 반복 속도를 위해 개발 중에는 agent 가 본 규칙을 능동 준수하고, 최종 일관성은 git pre-commit/pre-push 의 `.lazy-harness/bin/lazy test` 가 blocking 으로 검증한다 (ADR 0016).
- `tool.execute.before` 기반 수동/fixture 검증은 남아 있지만, 보편 실시간 gate 로 가정하지 않는다. 판단이 복잡하면 `lazy route --message "..." --format=md --log` 로 workflow route 를 받을 수 있고, 평시 route telemetry 는 `response.completed` 가 자동 누적한다. Router 는 advisory 이며 record-first/default-unknown/option-gate/queue-close 를 약화하지 않는다 (ADR 0037).
- record 가 빈약하다? 누적해라. 1 주 동안 어느 layer 도 안 자라면 framework 활용 실패 신호
- 검색 알고리즘 직접 구현 금지 (ADR 0024 §2). semantic 검색이 필요하면 SearchProvider (`search-provider.ts`) 통해 위임

이게 전부. 세부 host 룰은 record 가 답한다.
