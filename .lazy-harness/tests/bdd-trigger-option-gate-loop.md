# BDD Trigger Option Gate Loop Regression

Status: accepted
Layer: TDD
Date: 2026-05-17
Related SDD: `.lazy-harness/spec/platform/option-gate-discipline.md`
Related helper: `.lazy-harness/hooks/lifecycle/helpers/check-bdd-trigger.sh`

## Regression

A BDD natural-language trigger can open a structured option gate from `last_user_message`. If the assistant then repeats the same BDD options while waiting for the user, `response.completed` still sees the unchanged `last_user_message` and can inject the same BDD gate again. The visible symptom is an infinite-looking loop of:

```text
BackgroundTask... BDD 후보 처리 선택 필요
A. BDD scenario 등록 (Recommended)
B. 기존 scenario의 alias / 확장
C. scenario 아님, 다른 layer 또는 skip
D. 직접 입력
```

## Required protection

- The BDD trigger may emit the first gate for a new natural-language scenario candidate.
- Once a BDD option gate has fired for a stable BDD trigger input, the helper must stay silent for the same `(helper, fingerprint)` during the same `message_id` turn.
- Suppression is based on turn-level fingerprint state, not assistant response content. Production jcode `response.completed` payload does not include `assistant_response`, so text-based suppression is invalid.
- The helper must not turn background task IDs such as `BackgroundTask...` into repeated scenario prompts while a gate is already open.
- The BDD `last_user_message` path must not require host projects to install `ts-morph`; BDD can run from natural language and should not silently fail because non-BDD trigger dependencies are absent.

## Layer completeness gate

- SDD: option-gate discipline contract updated with BDD turn-level fingerprint suppression.
- BDD: user-visible behavior is that the agent asks once per turn for the same BDD fingerprint, then waits for user choice instead of repeating the same A/B/C/D block.
- SSOT: `.lazy-harness/ssot/gate-fingerprint-state.md` defines `.lazy-harness/state/open-gates.json`.
- DDD: no domain terminology change.
- TDD: `check_bdd_trigger_loop_suppression` protects same-turn duplicate suppression and new-turn re-fire; `check_bdd_trigger_avoids_runtime_tsmorph` protects installed hosts without `ts-morph`.
- ADR: existing option-gate discipline decision covers waiting-state behavior; no new trade-off.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/hooks/lifecycle/helpers/check-bdd-trigger.sh` — computes BDD fingerprints and suppresses same-turn duplicates.
  - `.lazy-harness/hooks/lifecycle/helpers/gate-fingerprint.sh` — manages `.lazy-harness/state/open-gates.json` check/record behavior.
  - `.lazy-harness/ssot/gate-fingerprint-state.md` — SSOT for open gate runtime state.
  - `.lazy-harness/triggers/code-change.ts` — lazy-loads `ts-morph` only for non-BDD layers so BDD natural-language detection works in installed hosts.
  - `.lazy-harness/scripts/self-test.py` — adds `run_bdd_trigger_helper` and `check_bdd_trigger_loop_suppression`.
  - `.lazy-harness/spec/platform/option-gate-discipline.md` — documents BDD repeated-gate suppression.
- Key symbols:
  - `FINGERPRINT` / `MESSAGE_ID` (`check-bdd-trigger.sh`)
  - `gate_fingerprint_check` / `gate_fingerprint_record` (`gate-fingerprint.sh`)
  - `loadTsMorph` (`code-change.ts`)
  - `run_bdd_trigger_helper`
  - `check_bdd_trigger_loop_suppression`
  - `check_bdd_trigger_avoids_runtime_tsmorph`
- Flow:
  1. User message describes a user-visible flow.
  2. BDD helper emits the first structured gate.
  3. BDD helper records `(bdd, fingerprint)` for the current `message_id`.
  4. Subsequent invocations with the same `message_id` and fingerprint exit silently.
  5. A new `message_id` clears prior fingerprints and allows a fresh gate if still applicable.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - focused: `python3 - <<'PY' ... check_bdd_trigger_loop_suppression() ... PY`
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/option-gate-discipline.md`
  - SSOT: `.lazy-harness/ssot/gate-fingerprint-state.md`
  - TDD: `.lazy-harness/tests/bdd-trigger-option-gate-loop-bypass.md`
- Machine index:
  - graph ids: `kg_tdd_bdd_trigger_option_gate_loop`, `kg_hook_bdd_trigger_loop_suppression`, `kg_test_bdd_trigger_loop_suppression`
  - generated index key: `pending until implementation-index generator exists`
