# ADR 0026 — Doctor / Self-Test Scope Separation (Framework vs Host)

- **Status**: Accepted
- **Date**: 2026-05-13
- **Related**: ADR 0022 (framework-owned doctor and lazy-test), ADR 0025 (portability single entry point), ADR 0024 (AI-first redesign)
- **Author**: framework dev session (lazy-init MVP dogfooding 직전 발견)

## Rule digest

- Status: active
- Layer: ADR
- Scope: framework-global
- Applies when:
  - running or modifying doctor / self-test checks
  - adding a validation check and deciding framework-only, host-only, or both
  - debugging host validation failures caused by framework-only files
- Must:
  - separate validation into framework vs host scope; auto-detect via framework-only markers
  - classify every check as BOTH, FRAMEWORK_ONLY, or HOST_ONLY; skip framework-only checks on host scope
  - propagate the chosen scope into nested doctor subprocesses
- Must not:
  - make host validation depend on framework-only files (handoff/phase plans, source-only fixtures/registries)
- Record completion:
  - new or moved checks update this ADR with an explicit scope classification and self-test coverage
- Related records:
  - `.lazy-harness/decisions/0022-framework-owned-doctor-and-lazy-test.md`
  - `.lazy-harness/decisions/0025-portability-single-entry-point.md`

## Context

ADR 0022 가 `doctor.py` 와 `self-test.py` 를 framework-owned 검증 도구로 정의했다. ADR 0025 가 `lazy-init` 으로 framework 를 host 에 복사하는 단일 진입점을 정했다. 두 ADR 사이의 가정이 충돌하는 지점이 lazy-init MVP 검증 중에 노출됐다:

`doctor.py` 와 `self-test.py` 는 **framework dev 컨텍스트에서만** self-aware 하게 짜여있다. host 에 복사된 후 같은 코드가 돌면 다음 hard-coded 의존성들이 깨진다:

- `handoff/00-current-state.md` — framework own dev cycle state (host 에 안 박힘)
- `planning/phase-5-plan.xml` — framework own phase plan (Category C, host 에 안 박힘)
- ADR 0021 의 존재 확인 — framework own 결정 (host 의 decisions/ 와 무관)
- `experimental/lazy-harness` 브랜치 정책 — framework dev 만 적용
- fixture set 일부 (lint-output, tdd-cross-verify, aftershock, e2e 디렉터리) — manifest `glob: ["fixtures/**/*.json"]` 가 .txt/.ts 파일을 제외해서 host 에 안 박힘

결과: `lazy-init` 직후 host 에서 `bun run lazy:doctor` 또는 `bun run lazy:test` 를 호출하면 `FileNotFoundError` 로 폭사한다. ADR 0025 의 "framework 가 자족적으로 자기를 검증한다" 약속이 host 에서 거짓이 된다.

검증 (2026-05-13, `/tmp/lazy-init-test/`):
- doctor.py D03 `check_adr_sequence` 가 `handoff/00-current-state.md` 못 찾아 폭사
- self-test 도 `check_doctor_smoke` 호출 단계에서 같은 이유로 중단

## Decision

**Doctor 와 self-test 에 명시적 scope 분리를 도입한다. scope 는 두 값 중 하나: `framework` (framework dev repo 검증) 또는 `host` (host project 검증).**

### Scope 감지

```python
def detect_scope() -> Literal["framework", "host"]:
    # framework dev repo 만 가지는 2 개 marker 의 동시 존재로 판정
    return "framework" if (
        (LAZY / "framework" / "framework-contract.md").exists()
        and (LAZY / "planning" / "phase-5-plan.xml").exists()
    ) else "host"
```

CLI 플래그로 명시적 override 가능:
- `--scope framework` / `--scope host` / `--scope auto` (default)

### Check 분류

각 check 함수는 3 그룹 중 하나에 속한다:

| 그룹 | 의미 | 예 |
|---|---|---|
| **BOTH** | host 와 framework 둘 다 가치 있음 | XML parse, JSONL parse, AGENTS.md invariants, C17 external dependency |
| **FRAMEWORK_ONLY** | framework dev cycle 검증 (host 에 무의미) | ADR 0021 존재, phase-5 criterion, fixture 기반 walkthrough |
| **HOST_ONLY** | host 환경 자체 검증 (framework 에 무의미) | (현재 비어있음. 향후 host-specific marker 검증 추가 가능) |

`run_checks(profile, scope)` 가 `BOTH ∪ (FRAMEWORK_ONLY if scope == framework else HOST_ONLY)` 를 실행한다.

### D03 분할

기존 `check_adr_sequence` 는 2 책임을 섞고 있었다:
1. ADR 번호 0001~N 의 연속성 (host 도 ADR 쌓을 거라 BOTH)
2. README/handoff 의 ADR count 마커 freshness (framework own 문서 동기화, FRAMEWORK_ONLY)

→ 분할:
- `check_adr_sequence` (BOTH) — 순수 연속성만
- `check_framework_adr_freshness` (FRAMEWORK_ONLY) — README/handoff 마커 일치

### self-test 적용

`self-test.py` 의 21 check 도 같은 분류:
- BOTH: doctor_smoke, doctor_c17_negative, doctor_package_health, xml, jsonl, schemas, tool_execute_before_hook, agents_md_invariants
- FRAMEWORK_ONLY: lint_output, interview_loop_collect/answer, tdd_cross_verify, affected_test_runner, aftershock_reanalysis, lifecycle_hook_integration, real_feature_walkthrough, e2e_demo, triggers, layer_impact_gate, reference_resolver

scope=host 일 때 framework-only check 들은 silently skip 하고 `[skipped: framework-only check, scope=host]` 로 출력에 표시.

### CLI

```
python3 .lazy-harness/scripts/doctor.py [--profile smoke|full] [--scope auto|framework|host]
python3 .lazy-harness/scripts/self-test.py [--scope auto|framework|host]
```

기본 `--scope auto` 가 환경 감지. CI / debugging 시 명시 override.

## Consequences

### 긍정

- `lazy-init` 직후 `bun run lazy:doctor` 가 host 에서 깨끗하게 통과 (HOST + BOTH check 만 실행)
- Framework dev 의 doctor 도 그대로 동작 (auto-detect 로 framework scope 잡음)
- ADR 0025 의 "framework 가 자족적으로 자기를 검증" 약속이 host 에서도 진실
- 향후 host-specific check 추가 시 HOST_ONLY 그룹에 박을 자리 마련됨

### 부정

- doctor.py / self-test.py 코드 분기 추가로 복잡도 증가 (~50 줄)
- check 추가/이동 시 scope 분류를 의식적으로 정해야 함 (manifest 처럼)
- 두 마커 (`framework/framework-contract.md`, `planning/phase-5-plan.xml`) 의 존재로 framework 를 판정 — 이 마커가 사라지면 detect 가 깨짐 (방어: 둘 다 framework own 으로 영구 유지)

### 대안 (기각)

- **A. Host 에 framework own dummy 파일 박기**: manifest postInit 에서 빈 `handoff/00-current-state.md` 박기. 거짓 검증 결과 만들 위험.
- **B. doctor/self-test 를 host 에 안 박기**: ADR 0025 의 "자족 검증" 약속 어김. host 에서 framework 건강 확인 불가.
- **C. Framework own check 를 graceful skip (파일 없으면 자동 통과)**: silent skip 으로 detection 실수 마스킹. scope 명시가 더 정직.

## Rollout

1. doctor.py 에 scope 분기 + check 분류 추가
2. self-test.py 에 scope 분기 + check 분류 추가
3. `result.schema.json` 에 `scope` 필드 (string enum) 추가
4. `manifests/init-categories.json` 의 doctor/self-test 설명에 scope 언급
5. `.jcode/skills/lazy-doctor/SKILL.md` 와 `lazy-test/SKILL.md` 에 scope 동작 명시
6. host 검증 (`/tmp/lazy-init-test/` + dev-ian) — 양쪽 scope 모두 통과 확인

## Scope override propagation update (2026-05-17)

`self-test.py --scope host|framework` must pass the chosen scope into every nested `doctor.py` subprocess. Without propagation, a host or legacy installed copy that still contains framework marker files can force `doctor.py` back into auto-detected framework scope, making host validation fail on framework-only freshness checks.

Implementation map addendum:

- `.lazy-harness/scripts/self-test.py` — `ACTIVE_SCOPE` and `doctor_scope_args()` propagate the resolved self-test scope to doctor smoke/full/json subprocesses.
- Protection: run `.lazy-harness/bin/lazy test --scope host` in installed hosts that may retain framework markers.

## Host package-source fixture skip update (2026-06-22)

Host-scope self-test must not require framework source-only package fixtures such as `packages/lazy-harness-pi/skills/lazy-impl-map-migrate/SKILL.md`, framework source registry parity such as source capability `policyIds`, source-only feature ids from `project/feature-navigation.xml`, or framework source readiness outcomes for host-owned policy/rulebook registries. It may validate generated host-local Jcode wrappers, synced concrete record traversal, framework seed policy availability, and read-only policy CLI schema/boundaries, but source package/registry/feature/readiness parity remains `framework` scope only. This preserves ADR 0026's rule that host validation does not depend on framework-own files that are not synced into hosts.

## Notes

이 ADR 은 lazy-init MVP dogfooding 의 *0 번째* finding 이다. 실제로 host 박기 직전에 발견됐기 때문에 lazy-init MVP 의 일부로 통합된다. 정상적인 dogfooding finding 이라면 host 박은 후에 발견되어 다음 cycle 로 미뤄질 수도 있었지만, 이 issue 는 lazy-init 의 첫 사용자 경험을 직접 깨뜨리므로 MVP 안에서 해결한다.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/scripts/doctor.py` — scope-aware doctor checks.
  - `.lazy-harness/scripts/self-test.py` — scope-aware self-test runner and scope fixtures.
  - `.lazy-harness/bin/lazy` — passes through `lazy doctor` and `lazy test` to framework-owned scripts.
- Key symbols:
  - `detect_scope` (`doctor.py`) — uses framework markers to distinguish framework vs host.
  - `_detect_scope`, `main`, `ACTIVE_SCOPE`, `doctor_scope_args` (`self-test.py`) — self-test scope selection and doctor forwarding.
  - `check_standalone_source_detection_uses_markers`, `check_lazy_host_root_resolution` (`self-test.py`) — regression coverage for scope/root behavior.
- Flow:
  1. Doctor/self-test resolve `ROOT` from `LAZY_HOST_ROOT` or script location.
  2. Scope auto-detect uses framework-only markers.
  3. BOTH checks run everywhere, FRAMEWORK_ONLY checks skip on host scope.
  4. `lazy test --scope host|framework` and `lazy doctor --scope ...` reuse the same scripts.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py` covers doctor smoke/full behavior, source marker detection, LAZY_HOST_ROOT resolution, and scope-aware self-test execution.
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0022-framework-owned-doctor-and-lazy-test.md`, `.lazy-harness/decisions/0025-portability-single-entry-point.md`
- Machine index:
  - graph ids: `kg_adr0026_doctor_scope`, `kg_adr0026_selftest_scope`
  - generated index key: `pending`
