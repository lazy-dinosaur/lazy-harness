# Project rule placement gate loop regression

Status: verified
Layer: TDD
Date: 2026-05-18
Amended: 2026-07-20
Related SDD: `.lazy-harness/spec/platform/project-rule-router.md`
Related SSOT: `.lazy-harness/ssot/gate-fingerprint-state.md`

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Aliases:
  - 규칙 배치 루프 회귀
  - placement gate
- Applies when:
  - editing the project-rule-placement gate helper or its same-turn duplicate suppression
  - a `Project rule placement gate` STOP reminder repeats in a turn, re-triggers from echoed/Korean no-record text, or appears after an unrelated successful/failed tool because stale path evidence leaked across turns
- Must:
  - fire the placement gate at most once per `(message_id, fingerprint)` via `open-gates.json`; allow new-message re-fire
  - derive semantic gate cues from `last_user_message` plus optional `assistant_response`, never arbitrary tool arguments; use only successful current-turn tool calls as structural action evidence
  - treat completed no-op/non-applicable and `기록하지 않음` judgements as terminal non-actions
- Must not:
  - re-trigger on the helper's own echoed STOP reminder, or let inherited runtime env break fixture isolation
- Record completion:
  - changes to fingerprint suppression update this TDD plus project-rule-router SDD and gate-fingerprint-state SSOT
- Related records:
  - `.lazy-harness/spec/platform/project-rule-router.md`
  - `.lazy-harness/ssot/gate-fingerprint-state.md`
  - `.lazy-harness/spec/platform/option-gate-discipline.md`

## Regression

A `Project rule placement gate` STOP reminder can loop visibly when production Jcode `response.completed` payloads omit `assistant_response`. The helper can derive the same missing-Rule-placement condition from stable fields such as `last_user_message` and `recent_tool_calls`, then inject the same A/B/C/D/E/F reminder again in the same turn.

Observed symptom: the assistant repeatedly answered the same Rule placement block for the Medivance named dev instance workflow, producing multiple near-identical `## Rule placement` sections.

Additional observed symptom on 2026-05-19: a different session answered the gate with repeated non-applicable/no-record judgement text (`Rule: 없음`, `Scope: non-applicable`, `Primary record: none`, `Confirmation: user-confirmed`, `기록하지 않음`). The helper treated Korean negative text containing `기록` as a new record action and kept re-triggering/being amplified visibly.

Additional observed symptom on 2026-05-21: the helper's own `STOP. Project rule placement gate` reminder was surfaced back into a later turn as `last_user_message`. Because the message includes rule/action/placement cues, the helper interpreted its own reminder as a fresh user request and re-injected the same gate across turns. This fix is intentionally narrow: only recognizable helper-generated STOP reminder text is ignored; real user project-rule changes still gate.

Additional observed symptom on 2026-06-09: the self-test runner for `check-project-rule-placement.sh` can inherit an outer lazy/Jcode runtime session environment, while the test cleanup deletes only the deterministic default `open-gates.json`. That mismatch makes the duplicate same-turn fixture flaky because first and second fires may read/write a different runtime state file than the cleanup target.

Additional observed symptom on 2026-07-20: after a prior read of `.lazy-harness/spec/platform/project-rule-router.md`, ending a later fetch/tool turn could inject `STOP. Project rule placement gate`. The same false STOP reproduced after both successful and failed fetches; a fetch failure by itself stayed silent.

## Root cause

- Pi/OMP retained root-scoped `recent_tool_calls` across normal turns and forwarded the newest 40 calls at every `agent_end`; normal `before_agent_start` did not create a new evidence epoch.
- The placement helper walked every string in the response-completion payload. A stale read path such as `.lazy-harness/spec/platform/project-rule-router.md` supplied `rule`, `route`, and `.lazy-harness` substring cues even though no rule was discovered.
- Failed tool calls were present in history and could count as write/memory action evidence or successful capture.
- Jcode production payload shape remains a constraint: `response.completed` does not reliably include assistant response text, so `last_user_message` must remain a valid semantic source without promoting tool arguments into prose.
- Primary ownership: lazy-harness Pi/OMP turn projection plus project-rule helper evidence interpretation. Fetch success/failure is only the turn-ending event, not the trigger.

## Fix

`check-project-rule-placement.sh` computes a deterministic fingerprint from stable semantic project-rule-placement inputs and records a `project-rule-placement:<fingerprint>` key in `$LAZY_RUNTIME_ROOT/state/open-gates.json`.

2026-05-19 addendum: the helper also recognizes completed no-op/non-applicable judgements and negative no-record dispositions as terminal non-actions. `기록하지 않음` and equivalent English/Korean no-record cues no longer count as an action cue when no write/local-note/memory tool was touched.

2026-05-21 addendum: the helper exits silently when the input is its own STOP reminder echoed back by the harness UI. This prevents cross-turn self-triggering without weakening normal project-rule placement detection.

2026-06-09 addendum: `run_project_rule_placement_helper` uses `env_without_lazy_runtime()` when spawning the helper, so the fixture uses deterministic runtime state and duplicate-suppression cleanup is reliable.

2026-07-20 amendment: Pi/OMP advances the root evidence epoch at every normal `before_agent_start` and includes only matching-epoch tool results in `agent_end`. Late results from an older turn cannot repopulate the new epoch. The helper derives semantic cues only from user/assistant prose, removes file/path tokens from rule/action scanning, and treats tool calls only as structural evidence. Calls with `is_error`/`isError` true cannot satisfy capture or count as memory/local-note actions.

Expected behavior:

1. A tool/path-only fetch turn stays silent regardless of whether the fetch succeeds or fails.
2. Genuine project-rule prose still emits the first gate even when the only tool call failed.
3. Failed canonical writes and failed memory calls do not satisfy placement or count as successful misuse.
4. First derived gate for a `(message_id, fingerprint)` emits STOP; repeated same-turn derivation exits silently.
5. A new `message_id` may re-fire if the semantic placement issue is still unresolved.
6. Pi/OMP `agent_end` carries current-turn tool results only; a tool-free turn receives no prior-turn evidence.

## Layer completeness gate

- Primary canonical record: this TDD regression record.
- SDD: `.lazy-harness/spec/platform/project-rule-router.md` defines semantic-vs-structural evidence; `.lazy-harness/spec/platform/pi-agent-package.md` defines normal-turn evidence epochs and current-turn `agent_end` projection.
- BDD: no independent record delta; user-visible behavior returns to the intended flow where unrelated fetch/tool completion does not enqueue a false placement follow-up, while genuine placement gaps still do.
- SSOT: `.lazy-harness/ssot/gate-fingerprint-state.md` narrows the project-rule fingerprint input to semantic text plus successful relevant action kinds.
- DDD: no domain terminology or business invariant change.
- TDD: `check_project_rule_placement_helper` protects path-only/fetch/failed-call cases; `_check_pi_agent_end_current_turn_scope` protects active-turn projection.
- ADR: no new decision; existing lifecycle, option-gate, and Pi/OMP bridge decisions remain unchanged.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/hooks/lifecycle/helpers/check-project-rule-placement.sh` — separates semantic prose from successful structural action evidence and computes same-turn fingerprints.
  - `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — advances normal-turn evidence epochs and filters `agent_end` tool evidence to the active epoch.
  - `.lazy-harness/scripts/self-test.py` — helper and fake-runtime regressions.
  - `.lazy-harness/spec/platform/project-rule-router.md` — SDD contract for semantic cue and action-evidence boundaries.
  - `.lazy-harness/spec/platform/pi-agent-package.md` — SDD contract for current-turn Pi/OMP projection.
  - `.lazy-harness/ssot/gate-fingerprint-state.md` — runtime fingerprint input and shared option-gate state schema.
- Key symbols:
  - `call_succeeded` / `cue_lower` (`check-project-rule-placement.sh`) — ignore failed calls and prevent path tokens from self-triggering semantic cues.
  - `gate_already_open_this_turn` (`check-project-rule-placement.sh`) — fingerprints semantic text plus successful relevant action kinds.
  - `advanceEvidenceEpoch` / `toolResultBelongsToCurrentEvidenceEpoch` (`index.ts`) — create normal-turn boundaries and reject late old-turn results.
  - `_check_project_rule_placement_helper_cases` (`self-test.py`) — validates genuine gates, tool/path-only silence, and failed-call exclusion.
  - `_check_pi_agent_end_current_turn_scope` (`self-test.py`) — validates active-turn-only Pi/OMP projection.
- Flow:
  1. `before_agent_start` advances the Pi/OMP evidence epoch; tool results retain their completion epoch.
  2. `agent_end` projects only calls whose evidence epoch matches the active turn.
  3. Placement helper derives rule/action/workflow meaning from user/assistant prose and successful action facts from tool calls.
  4. If a genuine gap remains, helper fingerprints semantic text plus normalized successful relevant action kinds.
  5. First fire records state and emits STOP; same-turn duplicate exits silently.
- Tests / protection:
  - `bash -n .lazy-harness/hooks/lifecycle/helpers/check-project-rule-placement.sh`
  - `python3 -m py_compile .lazy-harness/scripts/self-test.py`
  - focused self-test call for `check_project_rule_placement_helper` (includes the Pi/OMP current-turn fake runtime)
  - `python3 .lazy-harness/scripts/self-test.py`
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/project-rule-router.md`
  - SSOT: `.lazy-harness/ssot/gate-fingerprint-state.md`
  - SDD: `.lazy-harness/spec/platform/option-gate-discipline.md`
- Machine index:
  - graph ids: `kg_tdd_project_rule_placement_gate_loop`, `kg_hook_project_rule_placement_fingerprint_suppression`, `kg_test_project_rule_placement_fingerprint_suppression`, `kg_test_project_rule_placement_env_isolation_20260609`
