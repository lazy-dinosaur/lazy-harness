# Jcode Integration Guide (generated host-side wiring)

본 문서는 **lazy-harness 가 jcode hosted 환경에서 최대 효과를 내기 위한 host-side wiring** 가이드다. 현재 public `install.sh`, `lazy-init`, `lazy-sync` 는 generic/secret-free `.jcode/` template 을 기본 생성/보수한다. `.jcode/` 는 `.git/info/exclude` 에 들어가므로 host-local/private 상태를 유지한다.

생성되는 기본 항목:

- `.jcode/config.toml` — prompt loading, private instruction globs, lifecycle hooks
- `.jcode/AGENTS.md` — host-local Jcode private entrypoint
- `.jcode/harness/05-lazy-harness.md` — `../../.lazy-harness/AGENTS.md` symlink
- `.jcode/harness/10-routing-policy.md`, `20-project-rules.md`
- `.jcode/hooks/check-bash.sh`, `log-tool.sh`
- `.jcode/skills/lazy-{init,sync,update,doctor,test}/SKILL.md`

갱신 정책: `.lazy-harness/*` 는 `lazy update/sync` 로 framework source 를 따라 덮어쓴다. `.jcode/*` 는 generated marker 가 남아있는 파일만 template refresh 하고, marker 없는 user-owned 파일은 보존한다.

## 무엇을 얻는가

| Layer | 이 wiring 없을 때 | 적용 후 |
|---|---|---|
| Layer 1 (AGENTS.md grammar) | AI 가 우연히 읽음 | jcode 가 매 turn 시작에 자동 inject |
| Layer 2 (force gate hook) | 실행 안 됨 | Edit/Write tool 호출 시 자동 호출 |
| Layer 3 (response.completed) | 이미 작동 (별도 wiring) | — |

즉 **본 wiring 없으면 Layer 1+2 가 dormant**. self-test 는 통과하지만 실전 효과가 줄어든다.

## 기본 옵션 — project-local (`<host>/.jcode/`)

본인 host 한 곳에만 적용. team 에 영향 없음. 일반적으로 별도 수동 작업 없이 설치/업데이트가 생성한다.

```bash
.lazy-harness/bin/lazy update --force
```

수동 repair 가 필요하면 source checkout 에서:

```bash
bun /path/to/lazy-harness/.lazy-harness/scripts/lazy-init.ts --target "$PWD" --from /path/to/lazy-harness --force
```

### 1. project-local jcode init (없으면)

```bash
~/.claude/skills/jcode-init/scripts/init-jcode-project.sh "$(pwd)"
```

### 2. AGENTS.md inject 설정 (symlink 방식)

jcode 는 별도 `extra_instructions` schema 가 없다. 대신 `.jcode/harness/*.md` 를 자동으로 로드 (`load_harness_dir = true` 기본값) 한다. lazy-harness AGENTS.md 를 그 디렉토리에 symlink:

```bash
ln -s ../../.lazy-harness/AGENTS.md .jcode/harness/05-lazy-harness.md
```

`.jcode/config.toml` 의 `[prompt]` 섹션에서 `load_harness_dir = true` 만 확인 (jcode init 의 기본값):

```toml
[prompt]
load_harness_dir = true   # .jcode/harness/*.md 자동 로드 (jcode init 기본값)
load_jcode_agents = true  # .jcode/AGENTS.md 자동 로드
```

→ 매 session 시작 시 jcode 가 symlink 를 따라가 `.lazy-harness/AGENTS.md` 내용을 AI system prompt 에 자동 첨부. single source of truth 유지 (편집은 `.lazy-harness/AGENTS.md` 한 곳).

### 3. tool.execute.before hook 등록

`.jcode/config.toml` 에 추가. jcode 의 hook schema 는 `[[hooks.commands]]` (NOT `[[hooks]]`) 이며 `tool` filter 는 lowercase exact match:

```toml
[hooks]
enabled = true

[[hooks.commands]]
event = "tool.execute.before"
tool = "edit"
command = ".lazy-harness/hooks/lifecycle/on-tool-execute-before.sh"
blocking = true
timeout_ms = 3000

[[hooks.commands]]
event = "tool.execute.before"
tool = "write"
command = ".lazy-harness/hooks/lifecycle/on-tool-execute-before.sh"
blocking = true
timeout_ms = 3000

[[hooks.commands]]
event = "tool.execute.before"
tool = "multiedit"
command = ".lazy-harness/hooks/lifecycle/on-tool-execute-before.sh"
blocking = true
timeout_ms = 3000
```

→ jcode 가 edit/write/multiedit tool 호출 직전 본 hook 으로 payload pipe.
→ hook 이 exit 1 + stdout 출력 시 jcode 가 tool 호출 차단 + 출력을 AI 에 전달.

### 4. response.completed hook 등록 (이미 있을 가능성)

```toml
[[hooks.commands]]
event = "response.completed"
tool = "*"
command = ".lazy-harness/hooks/lifecycle/on-response-completed.sh"
blocking = false
timeout_ms = 5000
```

(기존 host 가 이미 박았으면 skip)

## 옵션 B — global `~/.jcode/`

본인 모든 lazy-harness host 에 동일 적용. wiring 은 같지만 path 를 절대로 박거나 `$PWD` 사용:

```toml
[[hooks.commands]]
event = "tool.execute.before"
tool = "edit"
command = "bash -c '[ -x \"$PWD/.lazy-harness/hooks/lifecycle/on-tool-execute-before.sh\" ] && \"$PWD/.lazy-harness/hooks/lifecycle/on-tool-execute-before.sh\"'"
blocking = true
timeout_ms = 3000
```

→ lazy-harness 가 활성된 cwd 에서만 발동. 다른 프로젝트는 silent.

## 검증 (wiring 적용 후)

### 단위 검증 (hook 직접 발동)

```bash
# Case 1: 검색 흔적 없음 → deny
echo '{"event":"tool.execute.before","session_id":"verify-1","tool":{"name":"edit","args":{"file_path":"src/main/foo.ts","old_string":"a","new_string":"b"}}}' \
  | bash .lazy-harness/hooks/lifecycle/on-tool-execute-before.sh
# 기대: exit 1 + AGENTS.md §1 인용 메시지

# Case 2: 검색 흔적 있음 → cache 기록 + 통과
echo '{"event":"tool.execute.before","session_id":"verify-2","tool":{"name":"edit","args":{"file_path":"src/main/foo.ts","old_string":"a","new_string":"b"}},"recent_tool_calls":[{"name":"grep","args_preview":".lazy-harness/decisions/0024"}]}' \
  | bash .lazy-harness/hooks/lifecycle/on-tool-execute-before.sh
# 기대: exit 0 + .lazy-harness/.cache/session/verify-2.json 생성

# Case 3: cache hit → 통과
echo '{"event":"tool.execute.before","session_id":"verify-2","tool":{"name":"edit","args":{"file_path":"src/main/bar.ts","old_string":"x","new_string":"y"}}}' \
  | bash .lazy-harness/hooks/lifecycle/on-tool-execute-before.sh
# 기대: exit 0 (즉시 통과)
```

### 통합 검증 (jcode session)

1. **AGENTS.md inject 확인**: 새 jcode session 시작 → AI 에게 "AGENTS.md §1 의 6 layer 폴더 나열해라" 질문. 6 개 (domain/spec/behavior/tests/decisions/ssot) 정확히 나오면 OK.

2. **force gate 확인**: 새 session 에서 "src/main/foo.ts 파일에 한 줄 추가해줘" 같은 검색-bypass 요청. AI 가 edit 호출 시 hook 이 deny + AGENTS.md §1 인용 메시지 출력 → AI 가 grep 부터 다시 시작하면 OK.

3. **session-cache 확인**: 같은 session 내 두 번째 edit 부터는 deny 없이 통과. `.lazy-harness/.cache/session/<session_id>.json` 생성 확인.

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
