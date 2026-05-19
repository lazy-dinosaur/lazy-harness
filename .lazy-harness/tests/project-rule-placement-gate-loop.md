# Project rule placement gate loop regression

Status: verified
Layer: TDD
Date: 2026-05-18
Related SDD: `.lazy-harness/spec/platform/project-rule-router.md`
Related SSOT: `.lazy-harness/ssot/gate-fingerprint-state.md`

## Regression

A `Project rule placement gate` STOP reminder can loop visibly when production Jcode `response.completed` payloads omit `assistant_response`. The helper can derive the same missing-Rule-placement condition from stable fields such as `last_user_message` and `recent_tool_calls`, then inject the same A/B/C/D/E/F reminder again in the same turn.

Observed symptom: the assistant repeatedly answered the same Rule placement block for the Medivance named dev instance workflow, producing multiple near-identical `## Rule placement` sections.

Additional observed symptom on 2026-05-19: a different session answered the gate with repeated non-applicable/no-record judgement text (`Rule: 없음`, `Scope: non-applicable`, `Primary record: none`, `Confirmation: user-confirmed`, `기록하지 않음`). The helper treated Korean negative text containing `기록` as a new record action and kept re-triggering/being amplified visibly.

## Root cause

- Jcode production payload shape is a constraint: `response.completed` does not reliably include assistant response text.
- The lazy-harness `check-project-rule-placement.sh` helper was the component re-deriving and re-injecting the repeated STOP reminder.
- The agent then treated injected system-reminder text like a new user prompt and amplified the loop by restating the same confirmed placement.

Primary ownership: lazy-harness hook behavior. Jcode payload shape is an input constraint, not the main bug.

## Fix

`check-project-rule-placement.sh` now computes a deterministic fingerprint from stable project-rule-placement trigger inputs and records a `project-rule-placement:<fingerprint>` key in `.lazy-harness/state/open-gates.json`.

2026-05-19 addendum: the helper also recognizes completed no-op/non-applicable judgements and negative no-record dispositions as terminal non-actions. `기록하지 않음` and equivalent English/Korean no-record cues no longer count as an action cue when no write/Jcode/memory tool was touched.

Expected behavior:

1. First derived project-rule placement gate for a `(message_id, fingerprint)` emits STOP.
2. Repeated same-turn derivation exits silently.
3. A new `message_id` may re-fire if the issue is still unresolved.

## Layer completeness gate

- SDD: `.lazy-harness/spec/platform/project-rule-router.md` now documents same-turn fingerprint suppression for project rule placement gates.
- BDD: user-visible behavior is that the same Rule placement reminder appears at most once per turn instead of repeating until the assistant answers it.
- SSOT: `.lazy-harness/ssot/gate-fingerprint-state.md` now lists `project-rule-placement:<fingerprint>` as a known helper prefix.
- DDD: no domain terminology change.
- TDD: `check_project_rule_placement_helper` protects first fire, same-turn suppression, and new-turn re-fire without `assistant_response`.
- TDD: `check_project_rule_placement_helper` also protects non-applicable/no-record judgement and Korean `기록하지 않음` false-positive cases.
- ADR: no new ADR; existing option-gate discipline and project-rule router decisions cover the trade-off.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/hooks/lifecycle/helpers/check-project-rule-placement.sh` — computes and records same-turn project-rule placement fingerprints.
  - `.lazy-harness/hooks/lifecycle/helpers/check-project-rule-placement.sh` — recognizes no-op/non-applicable placement judgements and negative no-record dispositions.
  - `.lazy-harness/scripts/self-test.py` — regression test in `check_project_rule_placement_helper`.
  - `.lazy-harness/spec/platform/project-rule-router.md` — SDD contract for project-rule placement helper behavior.
  - `.lazy-harness/ssot/gate-fingerprint-state.md` — shared runtime state schema for option-gate helper fingerprints.
- Key symbols:
  - `gate_already_open_this_turn` (`check-project-rule-placement.sh`) — duplicate suppression function.
  - `has_rule_placement_judgement` (`check-project-rule-placement.sh`) — accepts full placement judgement and completed no-op judgement.
  - `check_project_rule_placement_helper` (`self-test.py`) — validates first fire, duplicate same-turn silence, and new-turn re-fire.
- Flow:
  1. Project rule placement cues are detected and no complete placement/canonical record update satisfies the gate.
  2. Helper computes fingerprint from `last_user_message`, relevant tool-call blobs, and derived cue booleans.
  3. Helper checks `.lazy-harness/state/open-gates.json` under `project-rule-placement:<fingerprint>` for the current `message_id`.
  4. First fire records state and emits STOP; same-turn duplicate exits silently.
- Tests / protection:
  - `bash -n .lazy-harness/hooks/lifecycle/helpers/check-project-rule-placement.sh`
  - focused self-test call for `check_project_rule_placement_helper`
  - `python3 .lazy-harness/scripts/self-test.py`
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/project-rule-router.md`
  - SSOT: `.lazy-harness/ssot/gate-fingerprint-state.md`
  - SDD: `.lazy-harness/spec/platform/option-gate-discipline.md`
- Machine index:
  - graph ids: `kg_tdd_project_rule_placement_gate_loop`, `kg_hook_project_rule_placement_fingerprint_suppression`, `kg_test_project_rule_placement_fingerprint_suppression`
