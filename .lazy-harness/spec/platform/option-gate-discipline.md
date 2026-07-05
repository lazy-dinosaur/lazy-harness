# Option Gate Discipline

Status: accepted
Layer: SDD
Related AGENTS: `.lazy-harness/AGENTS.md` §2.3
Related SSOT: `.lazy-harness/ssot/rule-sources.md`
Related SDD: `.lazy-harness/spec/platform/project-rule-router.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Aliases:
  - 게이트 규율
  - 반복 질문 금지
  - gate discipline
- Applies when:
  - a response opens an option gate (`needs-option-gate`, `선택해주세요`, `진행 선택 필요`)
  - deciding whether to proceed, write, or execute while a choice is still pending
- Must:
  - ask once with 3-5 options plus a type-your-own, then stop the turn
  - render the gate through the runtime's interactive ask/select tool (OMP `ask`: `{questions:[{question, options:[{label,description}], recommended}]}`, type-your-own automatic) when available — native selectable choices, not plain A/B/C text
  - converge a user's choice to `user-confirmed`; use `inferred-from-record` when records already decide
  - summarize an already-open gate instead of reprinting or repeating it
- Must not:
  - write records, run dispatch/release, mutate files, or self-select `(Recommended)` while the gate is unresolved
  - re-ask the same gate unless scope, options, or a record/confirmation changed
- Record completion:
  - changes to gate-discipline triggers or loop suppression update this SDD, rule-sources, and self-test
- Related records:
  - `.lazy-harness/ssot/rule-sources.md`
  - `.lazy-harness/ssot/gate-fingerprint-state.md`
  - `.lazy-harness/spec/platform/project-rule-router.md`
  - `.lazy-harness/decisions/0034-analysis-discovery-plan-capture-gate.md`

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

1. Ask once with 3-5 options plus a type-your-own option, rendered via the runtime's interactive `ask` tool (native selectable choices) when the runtime exposes one; fall back to plain text only when no such tool is available (e.g. non-interactive/subagent sessions).
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

Agents should summarize the already-open gate rather than reprinting the full option block multiple times. Gate detection keys on the agent's own current response (`assistant_response`) only — never on tool-call args or other quoted/discussed payload strings, which previously made the helper fire on turns that merely mention gate markers. The runtime `ask`/`select` tool is the sanctioned, self-enforcing gate mechanism (it blocks the turn for the user), so its use is never a discipline violation and its args are not gate markers. Under jcode (no assistant text in the production payload) the text-gate path is inert; under Pi/OMP the `agent_end` bridge projects `assistant_response` (pi-agent-package payload parity).

BDD scenario detection is a special case: raw BDD discoveries are institutional-memory intake, not execution approval for product code or canonical record mutation. Therefore the BDD lifecycle helper must not emit repeated STOP/option-gate prompts. It silently appends a deduped `bdd-scenario` candidate to `.lazy-harness/knowledge/candidates.jsonl`; promotion into `behavior/`, `domain/`, or `spec/` still requires explicit user-confirmed action later.

## Lifecycle helper behavior

`check-option-gate-discipline.sh` runs from `on-response-completed.sh` after project-rule placement.

It first exits silently when the agent used the runtime `ask`/`select` tool (the sanctioned gate that blocks the turn for the user — never a violation). Otherwise it detects a text gate from `assistant_response` only and emits STOP when that gate appears together with either:

- a same-payload mutating/executing tool call (excluding the `ask`/`select` gate tools), or
- self-selection/completion language such as `user-confirmed`, `inferred-from-record`, `기록 완료`, `dispatch 했`, `실행했습니다`, or `진행하겠습니다` without a user choice.

Plainly asking a gate once is allowed for true decision/execution gates. Helpers that derive gates from stable payload fields are loop-prone and must suppress repeats. BDD trigger candidates use candidate-id dedupe in `.lazy-harness/knowledge/candidates.jsonl` and produce no hook output. Project rule placement gates use compatible `project-rule-placement:<fingerprint>` entries via `gate-fingerprint.sh`; if the same helper-prefixed fingerprint is already open for the current `message_id`, the helper exits silently even when stable payload fields still match the candidate.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/spec/platform/option-gate-discipline.md` — this SDD contract.
  - `.lazy-harness/AGENTS.md` — concise grammar rule.
  - `.lazy-harness/ssot/rule-sources.md` — option-gate waiting-state rule for project rule placement.
  - `.lazy-harness/spec/platform/project-rule-router.md` — project-rule-specific completion contract.
  - `.lazy-harness/hooks/lifecycle/helpers/check-option-gate-discipline.sh` — response-completed guard.
  - `.lazy-harness/hooks/lifecycle/helpers/check-bdd-trigger.sh` — silently captures deduped BDD scenario candidates instead of injecting repeated option gates.
  - `.lazy-harness/hooks/lifecycle/helpers/check-project-rule-placement.sh` — suppresses already-open project-rule placement STOP reminders using turn-level fingerprints.
  - `.lazy-harness/hooks/lifecycle/helpers/gate-fingerprint.sh` — owns `$LAZY_RUNTIME_ROOT/state/open-gates.json` check/record behavior.
  - `.lazy-harness/ssot/gate-fingerprint-state.md` — runtime state SSOT for `open-gates.json`.
  - `.lazy-harness/tests/project-rule-placement-gate-loop.md` — regression record for repeated project rule placement reminders.
  - `.lazy-harness/triggers/code-change.ts` — lazy-loads non-BDD parser dependencies so BDD natural-language gates work in installed hosts without `ts-morph`.
  - `.lazy-harness/hooks/lifecycle/on-response-completed.sh` — invokes the helper.
  - `packages/lazy-harness-pi/extensions/lazy-harness/index.ts#ensureAskToolActive` — keeps OMP's native `ask` selector active under tool discovery mode so option gates render as selectable choices.
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh` / `on-context.sh` — reminder grammar instructing agents to render option gates via the `ask` tool.
  - `.lazy-harness/scripts/self-test.py` — regression fixtures.
- Key symbols:
  - `check_option_gate_discipline_helper` (`.lazy-harness/scripts/self-test.py`) — validates ask/pass/block cases.
  - `run_option_gate_discipline_helper` (`.lazy-harness/scripts/self-test.py`) — helper runner.
  - `check_bdd_trigger_loop_suppression` (`.lazy-harness/scripts/self-test.py`) — validates silent BDD candidate capture and cross-turn dedupe.
  - `gate_fingerprint_check` / `gate_fingerprint_record` (`.lazy-harness/hooks/lifecycle/helpers/gate-fingerprint.sh`) — manage turn-level fingerprint state.
  - `check_bdd_trigger_avoids_runtime_tsmorph` (`.lazy-harness/scripts/self-test.py`) — validates BDD trigger dependency isolation for installed hosts.
- Flow:
  1. Assistant emits an option gate.
  2. Helper allows the turn only if no side-effect/self-selection is present.
  3. Any write/execute/self-selection after `needs-option-gate` is blocked.
  4. BDD trigger helper captures raw scenario candidates silently and does not block the conversation with A/B/C/D prompts.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - `bash -n .lazy-harness/hooks/lifecycle/helpers/check-option-gate-discipline.sh`
  - `python3 .lazy-harness/scripts/doctor.py --profile smoke`
- Cross-layer links:
  - SSOT: `.lazy-harness/ssot/rule-sources.md`
  - SSOT: `.lazy-harness/ssot/gate-fingerprint-state.md`
  - SDD: `.lazy-harness/spec/platform/project-rule-router.md`
  - ADR: `.lazy-harness/decisions/0034-analysis-discovery-plan-capture-gate.md`
- Machine index:
  - graph ids: `kg_sdd_option_gate_discipline`
  - generated index key: `pending until implementation-index generator exists`
