# BDD trigger option-gate suppression bypass (regression)

Status: verified (root cause confirmed, A+C fix implemented)
Layer: TDD
Date: 2026-05-17
Related: `.lazy-harness/tests/bdd-trigger-option-gate-loop.md`, `.lazy-harness/hooks/lifecycle/helpers/check-bdd-trigger.sh`

## Observation (medivance host, KST 2026-05-17 23:02)

같은 BDD trigger 가 같은 turn 안에서 **3번 연속** system-reminder 로 들어옴.
사용자: "야 왜 무한반복해도"

AI 본인의 자각 메시지:
> "system-reminder가 같은 BDD trigger 3번 연속 들어와서 멈춰있었습니다. 무한 ask 안 합니다."

기존 fix (`bdd-trigger-option-gate-loop.md`) 의 suppression 키워드는:
- `"5c-3 BDD"`
- `"BDD scenario 등록"` ← 이미지 응답에 있음
- `"BDD 후"*"선택"`
- `"BackgroundTask"*"BDD"*"선택"`

이미지의 assistant 응답이 `"BDD scenario 등록 (Recommended)"` 을 포함하고 있어서 suppression 이 fire 되어야 했음. 그런데도 3번 reminder 가 들어옴 → **suppression 우회**.

## Root cause (confirmed)

medivance host debug payload dumps confirmed that production jcode `response.completed` payload does **not** include `assistant_response`. Payload keys were limited to fields such as `event`, `session_id`, `message_id`, `working_dir`, `stop_reason`, `tool_calls_count`, `output_chars`, `last_user_message`, `recent_tool_calls`, `turn_count`, and `session_age_seconds`.

Therefore the previous suppression strategy was a false-green test: self-test supplied synthetic `assistant_response`, but production hooks never received it. Any suppression based on assistant text was a no-op in real hosts.

## Reproduction recipe

1. medivance host 에서 BDD 후보 발생하는 자연어 발화 (예: "취소된 예약 모달 등록")
2. 첫 응답에 BDD 옵션 게이트 표시됨 (정상)
3. 옵션 답 안 하고 다른 발화 / system event 발생 시 동일 게이트 반복

The key production mismatch is reproducible by invoking `check-bdd-trigger.sh` with a jcode-like payload that has `message_id`, `last_user_message`, and `recent_tool_calls`, but no `assistant_response`.

## Required protection (implemented)

- `assistant_response` 의존 제거.
- BDD helper computes a deterministic fingerprint from BDD trigger inputs (`files + last_user_message`).
- Same `(helper, fingerprint)` may fire at most once per `message_id` turn.
- Runtime state lives at `.lazy-harness/state/open-gates.json` and is defined by `.lazy-harness/ssot/gate-fingerprint-state.md`.
- New `message_id` clears prior fingerprints, so a fresh turn can re-fire if the candidate still exists.

## Layer completeness gate

- SDD: `.lazy-harness/spec/platform/option-gate-discipline.md` updated with production payload and turn-level fingerprint contract.
- BDD: user-visible behavior — same BDD gate appears at most once per turn for a stable fingerprint.
- SSOT: `.lazy-harness/ssot/gate-fingerprint-state.md` defines `.lazy-harness/state/open-gates.json`.
- DDD: 변경 없음.
- TDD: this record plus `check_bdd_trigger_loop_suppression` protect same-turn duplicate suppression and new-turn re-fire.
- ADR: no new ADR; existing option-gate discipline covers the waiting-state trade-off.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/hooks/lifecycle/helpers/check-bdd-trigger.sh` — computes BDD fingerprint and calls fingerprint gate.
  - `.lazy-harness/hooks/lifecycle/helpers/gate-fingerprint.sh` — stores and checks open gate fingerprints by `message_id`.
  - `.lazy-harness/ssot/gate-fingerprint-state.md` — state SSOT.
  - `.lazy-harness/spec/platform/option-gate-discipline.md` — SDD contract.
  - `.lazy-harness/scripts/self-test.py` — production-schema regression test.
- Tests / protection:
  - `check_bdd_trigger_loop_suppression` validates first fire, same-turn suppression, and new-turn re-fire.
- References:
  - 관측: 사용자 screenshot 2026-05-17 23:02 (KST)
  - 기존 fix: `bdd-trigger-option-gate-loop.md`

## Validation

- `python3 .lazy-harness/scripts/self-test.py` → 34/0 green after A+C implementation.
- medivance temporary debug dumps confirmed `assistant_response` absent in production payload. Debug hook was removed after diagnosis.
