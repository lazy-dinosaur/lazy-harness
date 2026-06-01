# Jcode Integration Guide (generated host-side wiring)

본 문서는 **lazy-harness 가 jcode hosted 환경에서 최대 효과를 내기 위한 host-side wiring** 가이드다. 현재 public `install.sh`, `lazy-init`, `lazy-sync` 는 generic/secret-free `.jcode/` template 을 기본 생성/보수한다. `.jcode/` 는 `.git/info/exclude` 에 들어가므로 host-local/private 상태를 유지한다.

생성되는 기본 항목:

- `.jcode/config.toml` — prompt loading, private instruction globs, lifecycle hooks
- `.jcode/AGENTS.md` — host-local Jcode private entrypoint
- `.jcode/harness/05-lazy-harness.md` — `../../.lazy-harness/AGENTS.md` symlink
- `.jcode/harness/10-routing-policy.md`, `20-project-rules.md`
- `.jcode/hooks/check-bash.sh`, `log-tool.sh`
- `.jcode/skills/lazy-{init,sync,update,doctor,test,skill-create}/SKILL.md`

갱신 정책: `.lazy-harness/*` 는 `lazy update/sync` 로 framework source 를 따라 덮어쓴다. `.jcode/*` 는 generated marker 가 남아있는 파일만 template refresh 하고, marker 없는 user-owned 파일은 보존한다.

Custom project skill 생성은 `.lazy-harness/bin/lazy skill create <name>` 을 사용한다. 자세한 contract 는 `.lazy-harness/spec/platform/jcode-skill-creation.md` 가 source of truth 다.

## 무엇을 얻는가

| Layer | 이 wiring 없을 때 | 적용 후 |
|---|---|---|
| Layer 1 (AGENTS.md grammar) | AI 가 우연히 읽음 | jcode 가 매 turn 시작에 자동 inject |
| Layer 2 (development advisory) | AI 자율 준수만 존재 | `.lazy-harness/AGENTS.md` + response reminder, 비차단 |
| Layer 3 (commit-time gate) | commit/push 전 누락 가능 | pre-commit/pre-push 에서 `.lazy-harness/bin/lazy test` blocking |

즉 **본 wiring 없으면 Layer 1 이 dormant**. 개발 중 edit/write 는 빠르게 유지하고, 최종 일관성은 git hook gate 가 맡는다.

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

### 3. tool.execute.before hook 정책

`.jcode/config.toml` 은 destructive bash safety hook 만 blocking 으로 둔다. edit/write/multiedit record force-gate 는 개발 속도를 위해 Jcode blocking hook 으로 등록하지 않는다. jcode 의 hook schema 는 `[[hooks.commands]]` (NOT `[[hooks]]`) 이며 `tool` filter 는 lowercase exact match:

```toml
[hooks]
enabled = true

[[hooks.commands]]
event = "tool.execute.before"
tool = "bash"
command = ".jcode/hooks/check-bash.sh"
blocking = true
timeout_ms = 3000
```

→ jcode 가 위험 bash 명령과 action-boundary rule violation 을 차단한다.

### 3.5 edit/write/multiedit Layer 2 force-gate 등록

```toml
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

→ edit/write/multiedit 실행 직전 record-first force-gate 를 수행한다.
→ hook 자체는 scoped/fast path 를 유지하고, broad consistency 는 commit 전 `.lazy-harness/hooks/pre-commit-guard.sh` 가 blocking 으로 재검증한다.
→ 기존 user-owned `.jcode/config.toml` 도 덮어쓰지 않고 `BEGIN lazy-harness mandatory Layer 2 force-gates` block 을 append/repair 해서 mandatory wiring 이 빠지지 않게 한다.

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

전역 설정에서도 edit/write/multiedit record force-gate 를 등록할 수 있지만, command 는 host-local `.lazy-harness/hooks/lifecycle/on-tool-execute-before.sh` 를 현재 cwd 기준으로 resolve 해야 한다. 위험 bash safety hook 과 Layer 2 force-gate 모두 host-local record 를 기준으로 동작해야 하며, `.jcode` 나 Jcode memory 를 canonical policy store 로 쓰지 않는다.

## 검증 (wiring 적용 후)

### 단위 검증 (hook 직접 발동)

```bash
# Case 1: 검색 흔적 없음 → deny
echo '{"event":"tool.execute.before","session_id":"verify-1","tool":{"name":"edit","args":{"file_path":"src/main/foo.ts","old_string":"a","new_string":"b"}}}' \
  | bash .lazy-harness/hooks/lifecycle/on-tool-execute-before.sh
# 기대: exit 1 + AGENTS.md §1 인용 메시지. generated Jcode wiring 은 이 스크립트를 edit/write/multiedit blocking hook 으로 등록한다.

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

2. **개발 중 force-gate 확인**: `.jcode/config.toml` 에 edit/write/multiedit `on-tool-execute-before.sh` blocking hook 이 있어야 한다. hook 은 scoped/fast path 로 동작해야 하며, broad consistency 는 pre-commit/pre-push 가 다시 검증한다.

3. **commit-time gate 확인**: `.git/hooks/pre-commit` 또는 husky pre-commit delegate 가 `.lazy-harness/hooks/pre-commit-guard.sh` 를 호출하고, 이 hook 이 `.lazy-harness/bin/lazy test` 실패 시 commit 을 차단해야 한다.

## 비활성화 (긴급 / debug)

```bash
touch .lazy-harness/.hooks-disabled
```

→ 모든 lifecycle hook 이 즉시 no-op. config 변경 불필요.

## 다른 host AI (jcode 외) 사용 시

본 wiring 은 jcode 전용. 다른 agent (Cursor / Aider / native Claude Code 등) 사용 시:

- AGENTS.md inject 는 그 host 의 instruction 메커니즘으로 대체 가능
- tool.execute.before 같은 hook 메커니즘이 없더라도 개발 중 차단은 의도적으로 하지 않는다. commit-time git hook 과 manual `lazy test` 가 최종 gate 다.
- 그래도 framework 자체 (record / triggers / N1 / N2) 는 정상 동작 — AI 가 자발적으로 AGENTS.md 따르기만 하면 됨

## 관련 문서

- `.lazy-harness/AGENTS.md` — framework grammar (본 wiring 의 inject 대상)
- `.lazy-harness/decisions/0024-ai-first-framework-redesign.md` — 3-Layer Defense 설계 근거
- `.lazy-harness/hooks/lifecycle/on-tool-execute-before.sh` — Layer 2 hook 본체
- `.lazy-harness/hooks/lifecycle/helpers/check-search-performed.sh` — 검색 흔적 검사 정책
