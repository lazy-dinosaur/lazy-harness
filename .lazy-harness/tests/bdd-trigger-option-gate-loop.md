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
- Once the assistant response already contains a BDD option gate / BDD selection-waiting text, the helper must stay silent.
- Suppression is based on assistant response content, not only `last_user_message`, because `last_user_message` remains unchanged across repeated assistant replies.
- The helper must not turn background task IDs such as `BackgroundTask...` into repeated scenario prompts while a gate is already open.
- The BDD `last_user_message` path must not require host projects to install `ts-morph`; BDD can run from natural language and should not silently fail because non-BDD trigger dependencies are absent.

## Layer completeness gate

- DDD: no domain terminology change.
- SDD: option-gate discipline contract updated with BDD repeated-gate suppression.
- BDD: user-visible behavior is that the agent asks once, then waits for user choice instead of repeating the same A/B/C/D block.
- TDD: `check_bdd_trigger_loop_suppression` protects the repeated gate regression, and `check_bdd_trigger_avoids_runtime_tsmorph` protects installed hosts without `ts-morph`.
- ADR: existing option-gate discipline decision covers waiting-state behavior; no new trade-off.
- SSOT: no config/schema/source-of-truth change.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/hooks/lifecycle/helpers/check-bdd-trigger.sh` — suppresses already-open BDD option gates by inspecting assistant response text.
  - `.lazy-harness/triggers/code-change.ts` — lazy-loads `ts-morph` only for non-BDD layers so BDD natural-language detection works in installed hosts.
  - `.lazy-harness/scripts/self-test.py` — adds `run_bdd_trigger_helper` and `check_bdd_trigger_loop_suppression`.
  - `.lazy-harness/spec/platform/option-gate-discipline.md` — documents BDD repeated-gate suppression.
- Key symbols:
  - `ASSISTANT_RESPONSE` (`check-bdd-trigger.sh`)
  - `loadTsMorph` (`code-change.ts`)
  - `run_bdd_trigger_helper`
  - `check_bdd_trigger_loop_suppression`
  - `check_bdd_trigger_avoids_runtime_tsmorph`
- Flow:
  1. User message describes a user-visible flow.
  2. BDD helper emits the first structured gate.
  3. Assistant repeats/summarizes the open BDD gate while waiting.
  4. BDD helper detects the already-open gate in `assistant_response` and exits silently.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - focused: `python3 - <<'PY' ... check_bdd_trigger_loop_suppression() ... PY`
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/option-gate-discipline.md`
- Machine index:
  - graph ids: `kg_tdd_bdd_trigger_option_gate_loop`, `kg_hook_bdd_trigger_loop_suppression`, `kg_test_bdd_trigger_loop_suppression`
  - generated index key: `pending until implementation-index generator exists`
