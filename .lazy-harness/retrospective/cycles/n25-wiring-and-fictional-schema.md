# Wiring 적용 + Fictional schema 회귀 관찰 (2026-05-13)

## 1. wiring 완료 상태

| 위치 | 내용 |
|---|---|
| `.jcode/config.toml` | hook 4 종 (bash/edit/write/multiedit) + log-tool + response.completed |
| `.jcode/harness/05-lazy-harness.md` | `.lazy-harness/AGENTS.md` 로 symlink |
| `.jcode/AGENTS.md` | jcode init 기본 (lazy-harness 무관) |
| `.jcode/hooks/check-bash.sh` | jcode init 기본 |

검증:
- toml parse OK (6 hooks 등록)
- hook 3 시나리오 (deny / cache write / cache hit) 모두 정상
- self-test 20/20 green

## 2. JCODE-INTEGRATION.md hallucination 발견

N2.5 commit 1 (`4d05e64f`) 에서 작성된 가이드가 **두 군데 fictional schema** 사용:

### 2.1 `[prompt] extra_instructions = [...]` 가 존재하지 않음

**실제 jcode (`config_file.rs:16-19`):**
```rust
struct PartialPromptConfig {
    ignore_project_agents: Option<bool>,
    ignore_global_agents: Option<bool>,
    load_jcode_agents: Option<bool>,
    load_harness_dir: Option<bool>,
}
```

`extra_instructions` 키는 jcode 가 모름. toml deserialize 시 unknown field 로 무시됨 (silent fail — 더 위험). 실제 inject 메커니즘은:
- `load_jcode_agents = true` → `.jcode/AGENTS.md` 자동 로드
- `load_harness_dir = true` → `.jcode/harness/*.md` 자동 로드
- project root `AGENTS.md` 도 기본 로드

→ **해결**: `.jcode/harness/05-lazy-harness.md` 를 `.lazy-harness/AGENTS.md` 로 symlink. `load_harness_dir = true` 가 자동 처리. single source 유지.

### 2.2 `[[hooks]]` 가 아닌 `[[hooks.commands]]`

**실제 jcode (`default_file.rs:368-373`):**
```toml
[[hooks.commands]]
event = "tool.execute.before"
tool = "bash"
command = ".jcode/hooks/check-bash.sh"
blocking = true
timeout_ms = 3000
```

가이드의 `[[hooks]]` 는 fictional. 또한:
- `tool` filter exact-match lowercase (`edit` / `write` / `multiedit`)
- `blocking` / `timeout_ms` 필수
- `[hooks] enabled = true` 가 parent section 에 있어야 함

## 3. 왜 이 hallucination 이 잡히지 않았는가

| 방어층 | 무엇이 잡았어야 했나 | 실제 |
|---|---|---|
| AI 자체 검증 | jcode source code 확인 | 안 함 — 추측으로 작성 |
| self-test | toml schema 검증 | 없음 — N2.5 에 추가 안 됨 |
| doctor | record 의 fictional reference 검출 | C17 forbidden tokens 만 — schema 검증 없음 |
| dogfooding | 실제 wiring 박아보기 | 본 작업이 첫 시도 — 그래서 발견 |

**핵심**: framework 자체가 dogfooding 되지 않은 상태로 docs 가 작성됨. wiring 박는 본 작업이 **사실상 첫 검증.**

## 4. N3 drift detector fixture 후보

본 사례는 N3 fixture 로 좋음:
- "record A 가 schema X 를 참조하는데 실제로는 schema Y" 패턴
- AI 가 다른 코드/docs 기반 추측으로 작성한 가상의 키
- toml/json schema 검증으로 binary 판정 가능

→ N3 spec 에 "external schema reference validation" 항목 추가 고려.

## 5. 가이드 수정 완료

`JCODE-INTEGRATION.md` 102 → 154 줄로 갱신:
- §2 AGENTS.md inject = symlink 방식 + `load_harness_dir` 설명
- §3 hook = `[[hooks.commands]]` 정정 + `tool` filter / `blocking` / `timeout_ms` 추가
- §4 response.completed = 동일 정정
- §5 옵션 B (global) = 동일 정정
- §6 검증 = 3 단위 hook 검증 case + 3 통합 jcode session 검증 분리

## 6. 다음 단계

- **dogfooding 시작** (본 wiring 으로 1~3 일)
- 새 jcode session 띄워서 통합 검증 (위 §6 의 3 case)
- AGENTS.md inject 가 실제로 AI 행동 바꾸는지 관찰
- false-deny 빈도 측정
- session-cache TTL 적정성 (현재 무제한 = session 종료까지)

## 7. 관련 commit

- 본 retrospective: 아직 commit 안 됨 (`.lazy-harness/retrospective/cycles/n25-wiring-and-fictional-schema.md`)
- 가이드 수정: 아직 commit 안 됨 (`.lazy-harness/JCODE-INTEGRATION.md` 154 lines)
- `.jcode/` 자체: gitignored, host 개인 wiring
