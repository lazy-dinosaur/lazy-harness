# ADR 0036 — §2.1 record-search trigger: 의도 분류 (모든 host-dependent 발화) vs 키워드 매칭

- Status: Accepted
- Date: 2026-05-17
- Triggers: §2.1 silent-skip on "조회/탐색/질문/출처 확인" intents (observed in medivance GPT-5.5 session, 2026-05-17)

## Rule digest

- Status: active
- Layer: ADR
- Scope: framework-global
- Aliases:
  - 검색 트리거
  - search trigger
  - 의도 분류
  - 키워드 매칭 아님
- Applies when:
  - user mentions any host detail, name, path, behavior, or rule (implement, fix, debug, look up, locate, ask, verify source)
  - e.g. "where is X?", "where does AGENTS.md load from?", "find feature Y"
- Must:
  - trigger §2.1 record-search by utterance intent, not keyword match, on any host-detail-dependent request
  - treat the keyword list as examples, not an enumeration
- Must not:
  - skip record-search because an utterance is a question, lookup, or location request
- Record completion:
  - changes to the §2.1 trigger definition update this ADR and `.lazy-harness/AGENTS.md`
- Related records:
  - `.lazy-harness/decisions/0019-ambiguous-detection-force-gate.md`
  - `.lazy-harness/decisions/0035-interview-queue-close-mandate.md`

## Context

§2.1 "요청 받자마자 검색" 룰의 원래 트리거 정의는:

> 구현 / 수정 / 추가 / 디버그 / 기록·계획·하려던 일 조회 의도가 보이면 즉시

이 정의는 키워드 enumeration 방식이라 다음 케이스가 사각지대로 빠짐:

| 발화 | 키워드 매칭 결과 |
|---|---|
| "X 어디 있어?" (탐색 / location) | 매칭 안 됨 |
| "AGENTS.md 어디서 읽어와?" (출처 확인) | 매칭 안 됨 |
| "이 기능 동작 원리 알려줘" (조회 / explainer) | 부분 매칭 |
| "Y 기능 찾아봐" (탐색) | 매칭 안 됨 |

medivance 의 GPT-5.5 세션 (2026-05-17) 에서 다음이 관측됨:

1. 사용자: "어떤 기능 찾아봐"
2. AI: 추정 grep → 답변 (§2.1 skip)
3. 사용자: "너 하네스 본 거 맞지?"
4. AI: "맞아요, 제가 놓쳤습니다" (자각)

룰은 inject 되어 있었지만 트리거 enumeration 이 발화 의도를 못 잡음.

§2.5 "모름이 디폴트" 는 "요청 (질문 / 구현 / 디버그 무관)" 으로 모든 발화를 커버하지만,
§2.1 의 키워드 enumeration 와 위계가 애매해서 모델이 §2.1 만 보고 "질문은 해당 없음"으로 판단함.

## Decision

§2.1 트리거 정의를 **키워드 enumeration → 의도 분류** 로 reframe:

```
발화 의도와 무관하게 (구현·수정·디버그·조회·탐색·질문·출처 확인 포함)
host 의 디테일·이름·경로·동작·룰이 등장하면 즉시:
```

핵심 변화:

1. "의도와 무관하게" 명시 — §2.5 정신 ("default = 모름") 과 일치
2. 키워드 리스트는 enumeration 이 아니라 **예시** 로 격하 ("포함")
3. **새 기준**: "host 의 디테일·이름·경로·동작·룰이 등장" — 키워드가 아니라 의미적 트리거

이러면 "X 어디 있어 / 출처 / 동작 / 의미" 류 발화도 §2.1 발동 대상.

## Options considered

A. §2.1 트리거 리스트에 "조회 / 탐색 / 질문 / 출처 확인" 추가 (cheap, but list bloat)
B. **§2.1 룰 자체를 reframe — "모든 host-detail-dependent 발화" 로 일반화** ← chosen
C. §2.1 그대로 두고 §2.5 를 §2.1 위로 끌어올림 (구조 큰 변경)

B 가 §2.5 정신과 일치, line budget 1줄 substitution 으로 끝남.

## Consequences

### Positive

- "X 어디서 읽어와?" 같은 출처 확인 발화도 §2.1 발동 — record-search 강제
- "Y 기능 찾아봐" 같은 탐색 발화도 §2.1 발동 — 추측 답변 차단
- §2.5 "모름 디폴트" 와 §2.1 트리거가 일관됨
- AGENTS.md 179 lines 유지 (line cap 미접근)

### Risk

- 의미적 트리거이라 hook 으로 정확히 enforce 하기 어려움 (NLP 필요). hook 은 "agentgrep/grep 실행 후 `.lazy-harness/` read 가 같은 turn 에 없으면 force-gate" 같은 syntactic proxy 로 추가 필요. **별도 작업**.
- "host 의 디테일" 정의가 추상적이라 모델이 여전히 자의적으로 skip 할 수 있음. enforcement layer (hook) 추가 필수.

## Follow-up

- `tool.execute.before` hook 에 §2.1 enforcement proxy 추가 (별도 ADR / SDD)
- §2.3 silent-skip ("답하고 묻지도 않은 작업 진행") 도 동일하게 hook enforcement 검토

## Implementation map

- `.lazy-harness/AGENTS.md` §2.1 첫 번째 paragraph — 트리거 정의 본문
- `.lazy-harness/scripts/self-test.py` — N2.5 AGENTS.md invariants 검사 (line cap 179)
- 영향 layer: SDD/BDD/SSOT 없음 (룰 본문 reframe 만, contract 변경 없음). TDD 없음 (hook 추��는 follow-up).

## References

- §2.1 (record-search), §2.5 (모름 디폴트), §3 (silent-skip 금지)
- ADR 0019 (option gate), ADR 0035 (queue close mandate)
- 관측: medivance 2026-05-17 GPT-5.5 session screenshot
