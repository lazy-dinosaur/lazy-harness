# Option Gate Discipline

Status: accepted
Layer: SDD
Related AGENTS: `.lazy-harness/AGENTS.md` §2.3
Related SSOT: `.lazy-harness/ssot/rule-sources.md`
Related SDD: `.lazy-harness/spec/platform/project-rule-router.md`

## Purpose

Prevent option gates from becoming loops or implicit approval.

A gate with `Confirmation: needs-option-gate` is a waiting state. It is not a completed judgement, not permission to choose the Recommended option, and not permission to continue with write/execute side effects.

## Trigger cues

The discipline applies when a response includes any of:

- `Confirmation: needs-option-gate`
- `needs-option-gate`
- `선택해주세요`
- `진행 선택 필요`
- `진행 선택:`

## Contract

When a gate is opened:

1. Ask once with 3-5 options plus a type-your-own option.
2. Stop the turn. Do not write records, run dispatch/release commands, mutate files, or execute follow-up plans in the same unresolved gate state.
3. Do not self-select `(Recommended)`.
4. If the user chooses an option, converge that choice to `Confirmation: user-confirmed` and do not ask the same gate again.
5. If existing records already decide the matter, use `Confirmation: inferred-from-record` and do not open the gate.

## Loop prevention

A repeated gate is a bug unless one of these changed since the previous gate:

- the user supplied a new choice or changed the scope,
- the candidate options materially changed,
- a record was found that converts the gate to `inferred-from-record`,
- a record/write happened after a user-confirmed selection.

Agents should summarize the already-open gate rather than reprinting the full option block multiple times. Trigger helpers that derive gates from stable context such as `last_user_message` must inspect the assistant response and suppress already-open repeated gates.

## Lifecycle helper behavior

`check-option-gate-discipline.sh` runs from `on-response-completed.sh` after project-rule placement.

It emits STOP text when an unresolved option gate appears together with either:

- mutating/executing tool calls in the same response payload, or
- self-selection/completion language such as `user-confirmed`, `inferred-from-record`, `기록 완료`, `dispatch 했`, `실행했습니다`, or `진행하겠습니다` without a user choice.

Plainly asking a gate once is allowed. BDD trigger gates are a special loop-prone case: if the assistant response already contains `BDD scenario 등록`, `5c-3 BDD`, or BDD selection-waiting text, `check-bdd-trigger.sh` must stay silent even when `last_user_message` still matches a scenario candidate.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/spec/platform/option-gate-discipline.md` — this SDD contract.
  - `.lazy-harness/AGENTS.md` — concise grammar rule.
  - `.lazy-harness/ssot/rule-sources.md` — option-gate waiting-state rule for project rule placement.
  - `.lazy-harness/spec/platform/project-rule-router.md` — project-rule-specific completion contract.
  - `.lazy-harness/hooks/lifecycle/helpers/check-option-gate-discipline.sh` — response-completed guard.
  - `.lazy-harness/hooks/lifecycle/helpers/check-bdd-trigger.sh` — suppresses already-open BDD option gate loops.
  - `.lazy-harness/triggers/code-change.ts` — lazy-loads non-BDD parser dependencies so BDD natural-language gates work in installed hosts without `ts-morph`.
  - `.lazy-harness/hooks/lifecycle/on-response-completed.sh` — invokes the helper.
  - `.lazy-harness/scripts/self-test.py` — regression fixtures.
- Key symbols:
  - `check_option_gate_discipline_helper` (`.lazy-harness/scripts/self-test.py`) — validates ask/pass/block cases.
  - `run_option_gate_discipline_helper` (`.lazy-harness/scripts/self-test.py`) — helper runner.
  - `check_bdd_trigger_loop_suppression` (`.lazy-harness/scripts/self-test.py`) — validates ask-once BDD behavior.
  - `check_bdd_trigger_avoids_runtime_tsmorph` (`.lazy-harness/scripts/self-test.py`) — validates BDD trigger dependency isolation for installed hosts.
- Flow:
  1. Assistant emits an option gate.
  2. Helper allows the turn only if no side-effect/self-selection is present.
  3. Any write/execute/self-selection after `needs-option-gate` is blocked.
  4. BDD trigger helper suppresses repeated injection when the assistant is already waiting on the BDD gate.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - `bash -n .lazy-harness/hooks/lifecycle/helpers/check-option-gate-discipline.sh`
  - `python3 .lazy-harness/scripts/doctor.py --profile smoke`
- Cross-layer links:
  - SSOT: `.lazy-harness/ssot/rule-sources.md`
  - SDD: `.lazy-harness/spec/platform/project-rule-router.md`
  - ADR: `.lazy-harness/decisions/0034-analysis-discovery-plan-capture-gate.md`
- Machine index:
  - graph ids: `kg_sdd_option_gate_discipline`
  - generated index key: `pending until implementation-index generator exists`
