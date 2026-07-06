# ADR 0022 — Framework-Owned Doctor and Lazy Test Boundary

- Status: Accepted
- Date: 2026-05-12
- Trigger: 사용자 결정 — "lazy:test 로 가야지 jcode 의 역할은 그냥 하네스 사용을 위한 툴인거고 나머지 모든건 우리 프레임워크가 흡수해야해"
- Related: ADR 0006 (Directory Bridge), ADR 0013 (External Dependency Invariant), ADR 0021 (Experimental Branch + Extract Strategy)

## Rule digest

- Status: active
- Layer: ADR
- Scope: framework-global
- Aliases:
  - doctor 소유권
  - lazy test 경계
- Applies when:
  - deciding where framework validation, doctor, or self-test logic should live
  - wiring a hook to a validation gate
  - a check depends on `.jcode` existing
- Must:
  - keep framework validation/doctor/self-test/registry logic owned by `.lazy-harness`, runnable without `.jcode`
  - make hooks call framework-owned validation (`lazy test` / self-test) as the primary gate
- Must not:
  - make framework operational validation depend on Jcode or `.jcode`
- Record completion:
  - doctor/self-test boundary changes update this ADR plus the CLI tool boundary SSOT
- Related records:
  - `.lazy-harness/decisions/0006-directory-bridge-architecture.md`
  - `.lazy-harness/decisions/0013-framework-external-dependency-invariant.md`
  - `.lazy-harness/decisions/0021-experimental-branch-and-extract-strategy.md`
  - `.lazy-harness/decisions/0026-doctor-self-test-scope-separation.md`
  - `.lazy-harness/ssot/cli-tool-boundary.md`

## Context

초기 lazy-harness 설계에서는 `.jcode/skills/harness-doctor/`가 framework 검증의 중심이었다.
그러나 Oracle audit에서 현재 worktree에 `.jcode/` 실체가 없고 doctor 실행이 재현되지 않는다는 문제가 확인되었다.

더 근본적으로, Jcode는 lazy-harness를 **사용하기 위한 도구**일 뿐이다. Framework의 운영 검증, self-test, doctor, registry consistency는 Jcode에 종속되면 안 된다.

ADR 0021의 future extract 목표까지 고려하면 검증 로직은 `.lazy-harness/` 안에 있어야 한다.

## Decision

Lazy-Harness의 검증/운영 로직은 framework가 소유한다.

### Boundary

| 영역 | 책임 |
|---|---|
| Jcode / `.jcode` | framework 사용 편의, slash command, adapter UI, local tool bridge |
| `.lazy-harness` | framework data, rules, hooks, doctor, self-test, trigger detectors, registry consistency |
| product code | host-project feature implementation |

### Immediate executable gate

현재 재현 가능한 gate는:

```bash
bun run lazy:test
```

`lazy:test`는 `.lazy-harness/scripts/self-test.py`를 실행하며 다음을 검증한다.

1. `.lazy-harness/**/*.xml` parse
2. permanent JSONL logs parse
3. DDD/SDD/BDD/SSOT trigger fixtures
4. SSOT registered utility suppression

### Doctor direction

`harness-doctor`라는 개념은 유지할 수 있지만 구현 위치는 `.jcode`가 아니라 framework 내부여야 한다.

권장 목표:

```text
.lazy-harness/scripts/doctor.ts 또는 .lazy-harness/scripts/doctor.py
```

`lazy:test`는 현재 최소 doctor 역할이며, 후속 작업에서 C1~C17 스타일 check를 이 framework-owned doctor로 흡수한다.

### Hook policy

Hooks should call framework-owned validation first.

- pre-push: `bun run lazy:test` 또는 `.lazy-harness/scripts/self-test.py`
- lifecycle helpers: `.lazy-harness/` scripts and triggers
- `.jcode/skills/harness-doctor` fallback은 더 이상 primary path가 아니다.

## Consequences

### Positive

- 재현 가능하다. `.jcode/`가 없어도 검증 가능.
- future extract에 적합하다.
- framework가 자기 일관성을 스스로 검증한다.
- (2026-07-05) self-test 는 `--scope` 외에 `--light` 모드를 갖는다: pre-commit gate 는 `lazy test --light`(measured-heavy check skip, ~16s), pre-push 는 full `lazy test`. 여전히 framework-owned validation(`lazy test`/self-test)이 primary gate — 경계 불변. 상세: ADR 0016 §0b (2026-07-05) + `.lazy-harness/ssot/cli-tool-boundary.md`.
- Jcode 외 다른 AI/tool 환경에서도 framework를 사용할 수 있다.

### Negative

- 기존 ADR/manifest에 남은 `.jcode` doctor 표현은 점진적으로 정리해야 한다.
- C1~C16 doctor 기능을 framework-owned doctor로 이전하는 후속 작업이 필요하다.
- Jcode slash command 편의성은 별도 wrapper로 다시 연결해야 한다.

## Verification

- L0: ADR 0022 문서 생성
- L1: README / handoff / manifests가 `lazy:test`를 primary gate로 설명
- L2: pre-push hook이 framework-owned `lazy:test`를 실행
- L3: `.jcode/`가 없는 worktree에서도 `bun run lazy:test` 통과
- L4: future extract 후에도 lazy-harness 자체 검증이 작동

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/scripts/doctor.py` — framework-owned doctor checks.
  - `.lazy-harness/scripts/self-test.py` — reproducible framework/host self-test gate.
  - `.lazy-harness/bin/lazy` — dispatches `lazy doctor` and `lazy test` to framework-owned scripts.
  - `.lazy-harness/hooks/pre-commit-guard.sh` — commit-time lazy test gate.
- Key symbols:
  - `detect_scope` (`doctor.py`) — ADR 0026-compatible scope detection used by the framework-owned doctor.
  - `check_doctor_smoke`, `check_doctor_c17_negative`, `check_doctor_package_health` (`self-test.py`) — executable doctor coverage.
  - `main` (`self-test.py`) — scope-aware self-test runner used by `lazy test`.
- Flow:
  1. User or hook calls `.lazy-harness/bin/lazy test` or `.lazy-harness/bin/lazy doctor`.
  2. The lazy CLI dispatches into `.lazy-harness/scripts/self-test.py` or `doctor.py`.
  3. Pre-commit/pre-push gates block on `lazy test`; Jcode may wrap but does not own operational validation.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py` validates doctor smoke/full negative/package-health behavior and pre-commit lazy test wiring.
  - `python3 .lazy-harness/scripts/doctor.py --profile smoke|full` is invoked directly by self-test.
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0026-doctor-self-test-scope-separation.md`
  - SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`
- Machine index:
  - graph ids: `kg_adr0022_doctor_lazy_test_cli`, `kg_adr0022_doctor_lazy_test_selftest`
  - generated index key: `pending`
