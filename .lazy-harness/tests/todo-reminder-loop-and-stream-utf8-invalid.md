# todo-reminder loop + Auto-poke + stream UTF-8 invalid → server reload

Status: open
Layer: TDD
Date: 2026-05-17
Related: `bdd-trigger-option-gate-loop-bypass.md`, jcode SIGHUP reload (별도 jcode issue), jcode auto-poke (별도 jcode 기능)

## Rule digest

- Status: needs-review
- Layer: TDD
- Scope: framework-global
- Applies when:
  - a todo system-reminder loop or jcode Auto-poke keeps pushing "continue" prompts against explicit user intent
  - diagnosing `stream did not contain valid UTF-8` server reload/reconnect symptoms
- Must:
  - treat Auto-poke / todo system-reminder text as system display, not user instruction; separate it from user intent
  - guide the user to clear todos or `/poke off` when `👉 Auto-poking` appears
- Must not:
  - let system-reminder or auto-poke pressure hijack the flow when the user states a different explicit intent
- Record completion:
  - auto-poke and UTF-8 transport fixes are jcode-side; an AI-behavior rule would land in AGENTS.md under a new ADR
- Related records:
  - `.lazy-harness/tests/bdd-trigger-option-gate-loop-bypass.md`

## Observation (medivance host, KST 2026-05-17 23:50 ~ 23:58 근방)

### Pattern A — system reminder loop

Turn 87 / 88 에 system reminder 가 연속 들어옴:
- `You have 5 incomplete todos. Continue working, or update the todo tool.`
- 다음 turn: `You have 6 incomplete todos. Continue working, or update the todo tool.`

AI 가 그에 대응해서 다시 옵션 게이트 출력 → 사용자가 의도하지 않은 흐름으로 흘러감.

### Pattern B — Auto-poke (jcode TUI feature)

Turn 94/95 에 jcode TUI 가 자동으로 prompt 를 큐에 push:
- `👉 Auto-poking: 6 incomplete todos. /poke off to stop.`
- 사용자가 "리로드 해줘" 라고 명시한 다음에도 auto-poke 가 계속 fire
- AI 가 이를 "hook 압박" 으로 잘못 해석

### Pattern C — stream UTF-8 invalid

- `[generation interrupted - server reloading]`
- `✓ Reconnected successfully. [×2]`
- `Waiting for handoff · 0s`
- `Detail: stream did not contain valid UTF-8`
- `Resume: jcode --resume gorilla`

## Three issues stacked

### Issue 1 — todo system reminder loop

`todo` tool 에 incomplete item 이 있으면 system reminder 가 매 turn 자동 inject 됨. 사용자가 "그냥 답해" 라고 했어도 reminder 가 계속 들어와서 AI 가 todo 처리 흐름을 자기 의도로 끌고 감.

### Issue 2 — Auto-poke (jcode TUI 기능, system reminder 와 별개)

확인된 소스: `/home/lazydino/dev/jcode/src/tui/app/input.rs:735` `schedule_auto_poke_followup_if_needed`

- default = ON (`tui_lifecycle.rs:345/713` 에서 `auto_poke_incomplete_todos: true`)
- 동작: turn 끝났는데 incomplete todo 있으면 jcode TUI 가 자동으로 "계속해" prompt 를 queued_messages 에 push → 다음 turn 자동 시작
- 표시: `👉 Auto-poking: N incomplete todo(s). /poke off to stop.` (system display message)
- 종료 조건:
  - todo 가 모두 완료 / 취소 / 삭제 → `✅ Todos complete. Auto-poke finished.`
  - 사용자가 `/poke off` 입력
  - `JCODE_RUN_AUTO_POKE=0` env (run 모드)
- **문제점**: 사용자가 명시적으로 다른 의도 ("리로드 해줘", "stop", "잠깐") 보냈을 때도 멈추지 않음

### Issue 3 — stream UTF-8 invalid + server reload

`Detail: stream did not contain valid UTF-8` 로 stream abort → server reload + reconnect. lazy-harness SIGHUP 케이스 (앞선 진단) 와 비슷한 증상이지만 원인은 UTF-8 stream payload 자체.

가능한 원인:
- 응답에 포함된 multi-byte 문자가 chunk 경계에서 잘림 (jcode side decoder 가 partial chunk 를 UTF-8 으로 파싱 시도)
- LLM provider 측 stream 이 binary 또는 truncated payload 보냄

이건 jcode harness 또는 provider transport 문제. lazy-harness 책임 X.

## Required protection (proposal)

### For Issue 1 (system reminder)

- lazy-harness 차원: 막을 수 없음 (jcode todo tool 동작은 jcode 측)
- AI 행동 차원: AGENTS.md 에 "system-reminder 와 user 의도 분리" 룰 명시 가능
- 효과: 모호. model 이 system-reminder 와 user message 를 구분하는 능력에 의존

### For Issue 2 (Auto-poke)

- lazy-harness 책임 X (jcode 기능). 단, 다음 개선이 jcode 측에 필요:
  1. user 의 다음 발화가 todo 와 무관한 명시적 새 의도 (`/poke off`, "리로드", "stop") 면 auto-poke 자동 비활성
  2. `/poke off` default 처리 방식 review (todo workflow 안 쓰는 host 에서 ON 디폴트가 적합한지)
- 임시 회피 (사용자): `/poke off` 또는 `JCODE_RUN_AUTO_POKE=0`
- AI 행동: auto-poke 메시지를 user instruction 으로 처리하지 말 것. 화면에 `👉 Auto-poking` 보이면 todo 정리 또는 `/poke off` 안내

### For Issue 3 (UTF-8 stream)

- lazy-harness 책임 X (jcode 또는 provider transport)
- UTF-8 chunk 경계 깨짐이 재현되면 jcode 에 report

## Layer completeness gate

- SDD: 변경 없음 (jcode protocol 영역, lazy-harness contract 영향 X)
- BDD: 사용자 가시 행동 — system reminder 와 auto-poke 가 흐름 점유 안 하도록 AGENTS.md 추가 룰 검토 필요
- SSOT: 변경 없음
- DDD: 변경 없음
- TDD: 이 record 가 regression recipe
- ADR: AGENTS.md 룰 추가 시 별도 ADR

## Implementation map

- Status: `open` (재현 어려움, jcode 측 책임)
- Primary files (jcode side):
  - `/home/lazydino/dev/jcode/src/tui/app/input.rs:735` `schedule_auto_poke_followup_if_needed`
  - `/home/lazydino/dev/jcode/src/tui/app/tui_lifecycle.rs:345/713` (default ON)
  - `/home/lazydino/dev/jcode/src/tui/app/commands.rs:87` (`/poke off` 처리)
  - `/home/lazydino/dev/jcode/src/cli/commands.rs:744+` (run mode auto-poke)
- lazy-harness side: 없음 (책임 외)
- References:
  - 관측: medivance KST 2026-05-17 23:50/23:58 screenshots
  - 연관: SIGHUP / server reload 진단 (jcode-2026-05-17.log)
  - jcode source rg: `Auto-poking|auto_poke_incomplete_todos`

## Next actions

1. medivance host 의 jcode session log 에서 23:50/23:58 시각대 stream error 확인
2. jcode 측에 auto-poke "user explicit new intent" detection 개선 제안
3. UTF-8 chunk 경계 깨짐 재현 케이스 모으면 jcode 에 report
4. AI 행동 룰 (auto-poke / system-reminder 와 user 의도 분리) 별도 ADR 검토
