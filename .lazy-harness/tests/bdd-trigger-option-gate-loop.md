# BDD Trigger Option Gate Loop Regression

Status: accepted
Layer: TDD
Date: 2026-05-17
Related SDD: `.lazy-harness/spec/platform/option-gate-discipline.md`
Related helper: `.lazy-harness/hooks/lifecycle/helpers/check-bdd-trigger.sh`

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Applies when:
  - a BDD natural-language trigger could repeat A-B-C-D option gates while waiting for the user
  - capturing scenario discoveries or running BDD detection in installed hosts
- Must:
  - capture raw BDD scenario discoveries as deduped candidates in candidates.jsonl, appending every distinct one
  - keep a pending BDD candidate silent across turns; require explicit user confirmation before canonical registration
- Must not:
  - emit STOP or A-B-C-D option prompts for raw BDD scenario discovery
  - require host projects to install `ts-morph` for BDD natural-language detection
- Record completion:
  - changes to BDD candidate capture or dedupe update this TDD plus option-gate-discipline SDD and self-test
- Related records:
  - `.lazy-harness/spec/platform/option-gate-discipline.md`
  - `.lazy-harness/ssot/gate-fingerprint-state.md`
  - `.lazy-harness/tests/bdd-trigger-option-gate-loop-bypass.md`

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

- The BDD trigger must not emit STOP / A-B-C-D option prompts for raw scenario discovery.
- Raw BDD scenario discoveries are automatically captured as deduped candidates in `.lazy-harness/knowledge/candidates.jsonl`.
- If the BDD detector returns multiple distinct BDD candidates, every distinct candidate must be appended/deduped; the helper must not stop after the first row.
- Canonical registration into `behavior/`, `domain/`, or `spec/` still requires explicit user confirmation later.
- The same pending BDD candidate must remain silent across turns, not only within the same `message_id`.
- Production jcode `response.completed` payload does not include `assistant_response`, so text-based suppression is invalid.
- The helper must not turn background task IDs such as `BackgroundTask...` into repeated scenario prompts while a candidate is pending.
- The BDD `last_user_message` path must not require host projects to install `ts-morph`; BDD can run from natural language and should not silently fail because non-BDD trigger dependencies are absent.

## Layer completeness gate

- SDD: option-gate discipline contract updated with BDD candidate-capture exception.
- BDD: user-visible behavior is no repeated BDD prompt; scenario candidates are accumulated silently for later promotion.
- SSOT: candidate intake uses `.lazy-harness/knowledge/candidates.jsonl`; project-rule STOP reminders still use `$LAZY_RUNTIME_ROOT/state/open-gates.json`.
- DDD: no domain terminology change.
- TDD: `check_bdd_trigger_loop_suppression` protects silent candidate capture and cross-turn dedupe; `check_bdd_trigger_avoids_runtime_tsmorph` protects installed hosts without `ts-morph`.
- ADR: existing option-gate discipline decision covers waiting-state behavior; no new trade-off.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/hooks/lifecycle/helpers/check-bdd-trigger.sh` — captures deduped BDD scenario candidates and emits no hook output.
  - `.lazy-harness/hooks/lifecycle/helpers/gate-fingerprint.sh` — still manages `$LAZY_RUNTIME_ROOT/state/open-gates.json` for true STOP reminders such as project-rule placement.
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
  2. BDD helper runs the BDD detector in JSON mode.
  3. BDD helper appends a stable `cand_bdd_*` row to `.lazy-harness/knowledge/candidates.jsonl` if it is not already pending.
  4. Subsequent invocations with the same candidate, including new turns, exit silently.
  5. Later canonical promotion happens only after explicit user confirmation.
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
