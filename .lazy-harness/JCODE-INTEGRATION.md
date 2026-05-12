# Jcode Integration Guide (optional, host-side)

본 문서는 **lazy-harness 가 jcode hosted 환경에서 최대 효과를 내려면 host 가 어떻게 wire 해야 하는지** 가이드. 이 wiring 은 framework 가 자동 적용하지 않는다 (ADR 0024 §6 portability 보장 — framework 는 host 환경에 침투하지 않음). host owner 가 본인 `.jcode/` 또는 jcode 글로벌 config 에서 직접 적용한다.

## 무엇을 얻는가

| Layer | 이 wiring 없을 때 | 적용 후 |
|---|---|---|
| Layer 1 (AGENTS.md grammar) | AI 가 우연히 읽음 | jcode 가 매 turn 시작에 자동 inject |
| Layer 2 (force gate hook) | 실행 안 됨 | Edit/Write tool 호출 시 자동 호출 |
| Layer 3 (response.completed) | 이미 작동 (별도 wiring) | — |

즉 **본 wiring 없으면 Layer 1+2 가 dormant**. self-test 는 통과하지만 실전 효과 0.

## 옵션 A — project-local (`<host>/.jcode/`)

본인 host 한 곳에만 적용. team 에 영향 없음.

### 1. project-local jcode init (없으면)

```bash
~/.claude/skills/jcode-init/scripts/init-jcode-project.sh "$(pwd)"
```

### 2. AGENTS.md inject 설정

`.jcode/config.toml` 에 추가:

```toml
[prompt]
extra_instructions = [
  ".lazy-harness/AGENTS.md",
]
```

→ 매 session 시작 시 jcode 가 본 파일 내용을 AI 의 system prompt 에 자동 첨부.

### 3. tool.execute.before hook 등록

`.jcode/config.toml` 에 추가:

```toml
[[hooks]]
event = "tool.execute.before"
command = ".lazy-harness/hooks/lifecycle/on-tool-execute-before.sh"
```

→ jcode 가 Edit/Write/MultiEdit tool 호출 직전 본 hook 으로 payload pipe.
→ hook 이 exit 1 + stdout 출력 시 jcode 가 tool 호출 차단 + 출력을 AI 에 전달.

### 4. response.completed hook 등록 (이미 있을 가능성)

```toml
[[hooks]]
event = "response.completed"
command = ".lazy-harness/hooks/lifecycle/on-response-completed.sh"
```

(기존 host 가 이미 박았으면 skip)

## 옵션 B — global `~/.jcode/`

본인 모든 lazy-harness host 에 동일 적용. wiring 은 같지만 path 를 절대로 박거나 `$REPO_ROOT` 환경변수 사용.

```toml
[[hooks]]
event = "tool.execute.before"
command = "bash -c '[ -x \"$PWD/.lazy-harness/hooks/lifecycle/on-tool-execute-before.sh\" ] && \"$PWD/.lazy-harness/hooks/lifecycle/on-tool-execute-before.sh\"'"
```

→ lazy-harness 가 활성된 cwd 에서만 발동. 다른 프로젝트는 silent.

## 검증 (wiring 적용 후)

1. **AGENTS.md inject 확인**: 새 jcode session 시작 → AI 에게 "AGENTS.md §1 의 6 layer 폴더 나열해라" 질문. 6 개 (domain/spec/behavior/tests/decisions/ssot) 정확히 나오면 OK.

2. **force gate 확인**: 새 session 에서 "src/main/foo.ts 파일에 한 줄 추가해줘" 같은 검색-bypass 요청. AI 가 Edit 호출 시 hook 이 deny + AGENTS.md §1 인용 메시지 출력 → AI 가 grep 부터 다시 시작하면 OK.

3. **session-cache 확인**: 같은 session 내 두 번째 Edit 부터는 deny 없이 통과. `.lazy-harness/.cache/session/<session_id>.json` 생성 확인.

## 비활성화 (긴급 / debug)

```bash
touch .lazy-harness/.hooks-disabled
```

→ 모든 lifecycle hook 이 즉시 no-op. config 변경 불필요.

## 다른 host AI (jcode 외) 사용 시

본 wiring 은 jcode 전용. 다른 agent (Cursor / Aider / native Claude Code 등) 사용 시:

- AGENTS.md inject 는 그 host 의 instruction 메커니즘으로 대체 가능
- tool.execute.before 같은 hook 메커니즘이 없으면 Layer 2 는 작동 안 함 (Layer 1 grammar 만 의존)
- 그래도 framework 자체 (record / triggers / N1 / N2) 는 정상 동작 — AI 가 자발적으로 AGENTS.md 따르기만 하면 됨

## 관련 문서

- `.lazy-harness/AGENTS.md` — framework grammar (본 wiring 의 inject 대상)
- `.lazy-harness/decisions/0024-ai-first-framework-redesign.md` — 3-Layer Defense 설계 근거
- `.lazy-harness/hooks/lifecycle/on-tool-execute-before.sh` — Layer 2 hook 본체
- `.lazy-harness/hooks/lifecycle/helpers/check-search-performed.sh` — 검색 흔적 검사 정책
