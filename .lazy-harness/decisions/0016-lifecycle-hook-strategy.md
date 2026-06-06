# ADR 0016 — Lifecycle Hook Strategy (M11 활용)

- Status: Accepted
- Date: 2026-05-11
- Trigger: 사용자가 jcode 코어에 M11 lifecycle hook decision parsing patch 완료 → framework 의 응답 종료 시점 강제 게이트 처음 가능
- Related: ADR 0010 (Plan Status Hygiene), ADR 0011 (Verification Discipline), ADR 0013 (External Dep Invariant + Code-First), ADR 0015 (Doctor C16 확장)

## Context

이번 세션 6시간 동안 발견된 framework 한계:

> 사용자 catch 9/15 ADR 패턴. AI 가 ADR 작성 후 plan/handoff/progress 갱신 누락 → 사용자가 catch → 추가 ADR. 자기 self-correcting 못 함.

원인: **AI 가 "응답 끝" 선언한 후 검증할 게이트 없음**. 우리 framework 은 git hook (commit/push 시점) 만 가졌고, agent hook (응답 시점) 0.

timsquad 분석 결과 그들의 강점 = claude-code `Stop` event 활용. AI 응답마다 검증 → deny 시 reason 자동 inject → AI 가 추가 작업 강제.

jcode 에는 처음에 hook event `tool.execute.before` / `after` 만 있었음. 사용자 직접 jcode 코어에 M11 patch 5 stage 추가:

| Stage | 내용 | Commit |
|---|---|---|
| 1 | lifecycle decision parsing | `e345d632` |
| 2 | reason → next-turn system reminder inject | `e345d632` |
| 3 | loop guard (3회 deny → suppress) | `b78e2bf5` |
| 4 | client.disconnect vs session.stop 분리 | `f382011c` |
| 5 | payload context 보강 (last_user_message, recent_tool_calls, turn_count, session_age_seconds) | `dc26f1e8` |

→ 이제 framework 의 응답 종료 시점 강제 가능.

## Decision

5 lifecycle event 활용 strategy:

### 0. 2026-05-19 amendment — development hooks advisory, commit hooks blocking

사용자 확인: "좋아 이방향으로 가자". 개발 중 `edit/write/multiedit` 직전 blocking force-gate 는 제거하고, framework consistency 는 git pre-commit/pre-push 시점에 blocking 으로 검증한다. 이유는 매 코드 수정마다 gate 가 개입하면 개발 시간이 과도하게 늘어나기 때문이다.

정책:
- Jcode `tool.execute.before` 는 destructive bash safety 만 blocking 으로 유지한다.
- `on-tool-execute-before.sh` 는 직접 검증/수동 audit 용으로 남기되 기본 generated `.jcode/config.toml` 에 edit/write/multiedit hook 으로 등록하지 않는다.
- `.lazy-harness/hooks/pre-commit-guard.sh` 는 host private leak guard 후 `.lazy-harness/bin/lazy test` 를 실행해 commit 을 차단한다.
- pre-push 는 기존처럼 `.lazy-harness/bin/lazy test` 를 blocking 으로 유지한다.

### 1. `response.completed` — 매 응답 검증 게이트 (PRIMARY)

**Fire 시점**: turn loop 끝 + tool calls 없음 (AI 가 더 이상 도구 사용 안 함)
**Frequency**: 응답 1회당 1번
**Blocking**: Yes (deny → next turn 에 reminder inject)
**Loop guard**: 3회 연속 deny → suppress

**Hook script**: `.lazy-harness/hooks/lifecycle/on-response-completed.sh`
**책임**:
- ADR 작성 detect (recent_tool_calls 안 .lazy-harness/decisions/00XX-*.md Write) → plan addedDuringPhase 갱신 검증
- handoff 안 stale 표기 ("pending ADR XXXX") detect → ADR closed 면 갱신 강제
- Fix commit 후 regression 엔트리 미생성 detect
- doctor/lazy-harness consistency checks and current 5c/5d/affected-test gates

**deny 패턴**:
```json
{"action":"deny","reason":"ADR 0011 작성됨, plan addedDuringPhase 미갱신. plan-5-plan.xml 의 5b addedDuringPhase 에 'ADR 0011 — Verification Discipline' 추가 필요."}
```

### 2. `client.disconnect` — 세션 종료 cleanup (Stage 4)

**Fire 시점**: client (TUI) tearing down (창 닫기 / ctrl-c / crash)
**Frequency**: 세션당 1번 (정상 종료 시)
**Blocking**: 의미 없음 (이미 disconnect)

**Hook script**: `.lazy-harness/hooks/lifecycle/on-client-disconnect.sh`
**책임**:
- progress/<today>.md 에 세션 summary append
- handoff/00-current-state.md 자동 갱신 (ADR count, framework version)
- validations.jsonl 에 final snapshot
- .lazy-harness/state/last-session.json 기록 (다음 SessionStart 가 읽음)

### 3. `session.stop` — DEPRECATED (Stage 4 가 client.disconnect 로 분리)

기존 hook 호환성을 위해 fire 됨. **새 hook 은 `client.disconnect` 등록**.
우리 framework 은 새 코드 작성이므로 `client.disconnect` 사용.

### 4. `tool.execute.before` — 위험 명령 차단 (기존 유지)

이미 `.jcode/hooks/check-bash.sh` 가 등록. edit/write/multiedit record force-gate 는 2026-05-19 amendment 이후 기본 Jcode config 에 등록하지 않는다.

### 5. `tool.execute.after` — 로깅 (기존 유지)

이미 `.jcode/hooks/log-tool.sh` 가 등록. 변경 없음.

## 구현 위치

```
.lazy-harness/hooks/lifecycle/
  on-response-completed.sh      # PRIMARY 검증 게이트
  on-client-disconnect.sh       # 세션 종료 cleanup
  helpers/
    check-handoff-stale.sh          # handoff 안 stale 표기 detect
    check-ddd-trigger.sh            # DDD trigger force gate
    check-sdd-trigger.sh            # SDD trigger force gate
    check-bdd-trigger.sh            # BDD trigger force gate
    check-ssot-trigger.sh           # SSOT trigger force gate
    check-tdd-cross-verify.sh       # missing test / TDD strategy gate
    check-affected-tests.sh         # matching project-routed test run or test-strategy gate
    check-aftershock-reanalysis.sh  # aftershock recursion gate
    check-fix-regression.sh         # Fix commit 후 regression 엔트리 검증
    check-adr-sync.sh               # ADR 작성 후 plan/handoff sync 검증
```

`.jcode/config.toml` 에 등록:
```toml
[[hooks.commands]]
event = "response.completed"
command = ".lazy-harness/hooks/lifecycle/on-response-completed.sh"
blocking = true
timeout_ms = 5000

[[hooks.commands]]
event = "client.disconnect"
command = ".lazy-harness/hooks/lifecycle/on-client-disconnect.sh"
blocking = false
timeout_ms = 5000
```

## Defense-in-depth

| Layer | 메커니즘 | 위치 |
|---|---|---|
| L0 record | tool.execute.after logging | 기존 |
| L1 warn | response.completed deny → reminder inject | M11 Stage 1+2 |
| L2 hard-stop | jcode loop guard (3회 deny) | M11 Stage 3 |
| L3 hard-stop | git pre-commit / pre-push (commit/push 시점) | 기존 |
| L4 manual | doctor 16 check + 사용자 catch | 기존 |

→ 5 layer 가 cascade. response.completed 가 catch 못 하면 git hook 이 catch. git hook 도 빠지면 doctor / 사용자.

## 무한루프 방지 (Defense)

jcode M11 Stage 3 (loop guard 3회) 외 우리 추가 안전망:

1. **Idempotent check** — sync-guard 가 "이미 reminder 주입했나" 검증 (.lazy-harness/state/pending-reminders.jsonl)
2. **Same-deny detection** — 같은 reason 2회 연속이면 자동 allow + warn 로그
3. **Hook script 자체 dry-run mode** — `LAZY_HARNESS_HOOK_DRY_RUN=1` 시 deny 안 함

## Code-First Trigger 정신 (ADR 0013) 일관

이 ADR 의 모든 결정은 외부 SaaS 의존 0:
- jcode 코어 (Principle 22 허용)
- bash + python3 (코어 허용)
- ADR 0013 의 Code-First Trigger 가 lifecycle hook 으로 자연스럽게 확장

## Verification

- L0: 파일 작성됨
- L2 marker: 다음 응답 끝나면 `event-trace.log` 에 `response.completed` fire 기록 확인
- L3 negative: 일부러 ADR 작성 후 plan 미갱신 → on-response-completed.sh 가 deny → 다음 turn 에 reminder 주입 검증
- L4 사람 review: 5c 진입 전 사용자에게 hook strategy 동의 ask

## Consequences

### Positive

- ADR 0010 (Plan Status Hygiene) 의 진정한 자동화. 사용자 catch 의존도 최소화.
- ADR 0011 (Verification Discipline) 의 L1 warn 단계가 자동 주입으로 실효성 가짐.
- ADR 0015 (Doctor C16 확장) 가 자동 발동.
- timsquad equivalent + jcode 추가 안전망 (loop guard + payload context).

### Negative

- response.completed 가 매 응답마다 fire → 검증 비용 (현재 doctor ~400ms, 허용 가능)
- false positive 시 AI 가 불필요한 작업 수행 (loop guard 가 3회 후 catch)
- hook script 자체 버그 시 framework 자기마비 가능성 (loop guard + dry-run flag 가 mitigate)

### Risk

- 우리 sync-guard 가 정확히 작동하는지 검증 필수 (5c-9 doctor C17 추가)
- payload context 활용 미숙으로 인한 misjudgment (예: 사용자가 "test 만 해" 했는데 commit deny) → conservative deny only

## Related Future Work

- ADR 0017 (예정) — sync-guard 의 정확도 측정 + tuning
- ADR 0018 (예정) — `session.end` event (logical session end) 가 jcode 코어에 추가되면 framework 활용


## Addendum — 2026-05-12 current helper chain

ADR 0016 originally described the first 3 response helpers. The live chain has grown to 10 helpers as 5c/5d matured. The current source of truth is `.lazy-harness/hooks/README.md` and `.lazy-harness/hooks/lifecycle/on-response-completed.sh`.

Read-only audits should disable hooks with `.lazy-harness/.hooks-disabled` or equivalent dry-run mode to avoid lifecycle continuation edits during audit collection.

## Implementation map

- Status: `needs-review`
- Primary files:
  - `.lazy-harness/hooks/lifecycle/on-response-completed.sh` — primary response.completed lifecycle hook and helper timing loop.
  - `.lazy-harness/hooks/lifecycle/on-client-disconnect.sh` — client disconnect cleanup hook surface.
  - `.lazy-harness/hooks/pre-commit-guard.sh` — commit-time blocking lazy test gate.
  - `.lazy-harness/scripts/self-test.py` — lifecycle, Jcode hook, pre-commit, and response.completed regression coverage.
  - `.lazy-harness/scripts/jcode-wiring.ts` — generated Jcode hook policy, including non-blocking edit/write behavior and bash safety-only hook.
- Key symbols:
  - `check_response_completed_no_auto_route_telemetry` (`self-test.py`) — verifies response.completed stays best-effort, does not run route classifiers, and still logs hook timings.
  - `check_jcode_dev_hooks_are_nonblocking` (`self-test.py`) — protects the 2026-05-19 amendment that edit/write/multiedit development hooks stay non-blocking.
  - `check_pre_commit_runs_lazy_test` (`self-test.py`) — protects commit-time `.lazy-harness/bin/lazy test` blocking gate.
- Flow:
  1. Jcode/tool lifecycle invokes generated hook surfaces.
  2. response.completed runs lifecycle helpers and timing logging.
  3. edit/write/multiedit blocking is intentionally absent during development.
  4. pre-commit/pre-push retain blocking `lazy test` consistency checks.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py` covers response.completed route telemetry removal, lifecycle parity/intake, pre-commit lazy test, Jcode non-blocking dev hooks, and bash safety-only policy.
  - This ADR remains `needs-review` because it records historical M11 event semantics and several hook-stage intentions; not every historic stage is executable in this repo.
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/hook-performance-measurement.md`
  - TDD: `.lazy-harness/tests/response-completed-route-telemetry-large-payload.md`
  - SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`
- Machine index:
  - graph ids: `kg_adr0016_lifecycle_hooks`, `kg_adr0016_lifecycle_tests`
  - generated index key: `pending`
