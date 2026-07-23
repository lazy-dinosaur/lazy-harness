# Project Rule Router

Status: accepted
Layer: SDD
Related SSOT: `.lazy-harness/ssot/rule-sources.md`
Related SSOT: `.lazy-harness/ssot/project-identity.md`
Related backlog: `.lazy-harness/planning/project-rule-discovery-router-backlog.md`
Related TDD: `.lazy-harness/tests/project-rule-placement-gate-loop.md`
Related ADR: `.lazy-harness/decisions/0050-pi-omp-only-runtime.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Aliases:
  - 규칙 배치
  - rule placement
  - 어느 record 에
  - 규칙 라우팅
  - 팀 규칙 저장
- Applies when:
  - user confirms or corrects a project rule, workflow rule, ownership, or source-of-truth fact
  - 사용자가 프로젝트 규칙, 룰, 기록 위치, AGENTS, Pi/OMP 로컬 노트(`.pi/`/`.omp/`), SSOT를 언급한다
  - deciding where to record AGENTS, Pi/OMP local notes (`.pi/`/`.omp/`), SSOT, ADR, layer facts, or planning knowledge
  - response.completed reports project rule placement or canonical record completion problems
- Must:
  - route durable project/team rules into canonical `.lazy-harness` records, not Pi/OMP local notes alone
  - include a complete Rule placement judgement when recording or reporting placement
  - derive semantic placement cues only from `last_user_message` and `assistant_response`; tool calls are structural action evidence, not prose
  - accept record/local-note/memory action evidence only from successful calls (`is_error` / `isError` is not true)
  - stop with an option gate when placement is ambiguous
- Must not:
  - treat `needs-option-gate` as approval to keep working
- Record completion:
  - confirmed rule placement changes update this SDD or the target SSOT/ADR/layer record
- Related records:
  - `.lazy-harness/ssot/rule-sources.md`
  - `.lazy-harness/spec/platform/record-write-update-policy.md`

## Purpose

Route newly discovered project-specific rules to the right durable source of truth.

This prevents agents from treating Pi/OMP local notes (`.pi/APPEND_SYSTEM.md`) as a catch-all when a rule should be visible through `.lazy-harness` records across sessions and hosts.

## Trigger cues

The router applies when a response or user correction mentions any of:

- `프로젝트 규칙`, `프로젝트마다 규칙`, `규칙 추가`, `룰 추가`
- `AGENTS.md 수정`, `AGENTS에 넣`, `agents.md`
- `.jcode`, `.lazy-harness`, `20-project-rules`, Jcode `memory.remember` / “프로젝트 메모리”
- `어디에 기록`, `어디에 저장`, `문서화`, `source of truth`, `SSOT`
- user correction about workflow, source-of-truth, ownership, forbidden mutation, or project-specific operating policy

## Completion contract

A triggered turn is complete only if one condition is true:

1. A `.lazy-harness` record/planning artifact is updated for the rule.
2. The response includes a complete `Rule placement` judgement with `Confirmation: user-confirmed` or `Confirmation: inferred-from-record`.
3. `.pi/APPEND_SYSTEM.md` is updated only as a pointer to canonical `.lazy-harness` records, or the response/file content includes a `local-only` judgement.
4. A mistaken Jcode `memory.remember` project-rule write is removed with `memory forget` and the rule is re-recorded in canonical `.lazy-harness` records.
5. The agent stops with an option gate because placement is ambiguous. `Confirmation: needs-option-gate` is not complete and must not be followed by tool calls or self-selected Recommended execution.

## Rule placement judgement

```md
## Rule placement

- Rule: ...
- Scope: framework-global | host-project | team-policy | layer-fact | local-only | transient-plan | ambiguous
- Primary record: ...
- Why not AGENTS.md: ...
- Why not local notes: ...
- Confirmation: user-confirmed | inferred-from-record | needs-option-gate
```

## Placement matrix

| Scope | Primary location |
|---|---|
| `framework-global` | `.lazy-harness/AGENTS.md` only if universal and thin |
| `host-project` | `.lazy-harness/ssot/project-identity.md` or dedicated SSOT |
| `team-policy` | `.lazy-harness/ssot/rule-sources.md` or dedicated SSOT/ADR |
| `layer-fact` | DDD/SDD/BDD/TDD/ADR/SSOT based on the fact type |
| `local-only` | `.pi/APPEND_SYSTEM.md` as a Pi/OMP local note |
| `transient-plan` | `.lazy-harness/planning/**` |
| `ambiguous` | option gate before writing |

## Lifecycle helper behavior

`check-project-rule-placement.sh` runs from `on-response-completed.sh`.

It emits STOP text when:

- high-confidence project-rule placement cues are detected,
- the response is creating, correcting, moving, or newly routing a rule rather than merely reporting that an existing record/policy is already applied,
- no `.lazy-harness` record/planning artifact was touched,
- and there is no complete `Rule placement` judgement,
- especially when the response chooses `.jcode` or Jcode memory for a project rule without canonical `.lazy-harness` placement.
- when a `memory.remember` call stores a project/team workflow, ownership, source-of-truth, or operating policy. The fix is `memory forget` plus canonical `.lazy-harness` record capture, not treating memory as the source of truth.

The helper must avoid false positives on casual mentions of AGENTS.md or `.jcode` without rule-placement language. Semantic rule/action/workflow cues come only from `last_user_message` and `assistant_response`; `recent_tool_calls` supplies structural evidence for successful writes or memory actions and must never contribute general prose. Failed tool calls cannot satisfy canonical capture, count as local-note writes, or count as memory misuse.

File/path tokens inside prose are retained as explicit placement context but removed from the rule/action/workflow cue scan. A path such as `.lazy-harness/spec/platform/project-rule-router.md` therefore cannot self-trigger merely because its filename contains `rule` and `route`.

The helper must also avoid same-turn repeated STOP reminders. Production Jcode `response.completed` payloads may not include `assistant_response`, so `last_user_message` remains a sufficient semantic source when assistant prose is absent. When the helper emits a derived gate, it records a deterministic `project-rule-placement:<fingerprint>` entry in `$LAZY_RUNTIME_ROOT/state/open-gates.json`; the fingerprint uses semantic user/assistant text plus normalized successful placement-relevant action kinds rather than arbitrary tool arguments. The same `(message_id, fingerprint)` exits silently, while a new `message_id` may re-fire.

Self-test runners for this helper must clear inherited lazy runtime/session environment before invoking `check-project-rule-placement.sh`, so fixture duplicate-suppression state is read from the deterministic default runtime path rather than an outer Jcode session path.

Generated `.pi/APPEND_SYSTEM.md` local notes must be pointer-only by default. They should tell agents to read `.lazy-harness/ssot/rule-sources.md` and layer records for custom host/team rules rather than inviting new project-specific rule bodies into local notes.

Existing user-owned Pi/OMP local notes (`.pi/APPEND_SYSTEM.md`) that predate pointer-only behavior are migrated so the active note becomes the generated pointer-only note, and the previous content is archived so it is not loaded as active harness instructions.

The placement helper's scope is `.jcode`/Jcode-memory over-routing only. Intra-`.lazy-harness` storage correctness — operating-rule semantics written to a non-canonical `.lazy-harness/ssot/*.md`, or a rule added without prior `lazy (policy|capability|rules) resolve` (duplication) — is covered by the sibling helper `.lazy-harness/hooks/lifecycle/helpers/check-operating-rule-storage.py` (advisory; see `.lazy-harness/spec/platform/response-rule-audit.md` and `.lazy-harness/planning/operating-rule-storage-apply-repair-20260624.md`).

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/spec/platform/project-rule-router.md` — this SDD contract.
  - `.lazy-harness/ssot/rule-sources.md` — canonical placement registry.
  - `.lazy-harness/hooks/lifecycle/helpers/check-project-rule-placement.sh` — enforcement helper, including Jcode memory misuse detection.
  - `.lazy-harness/ssot/gate-fingerprint-state.md` — runtime state schema shared by loop-prone option-gate helpers.
  - `.lazy-harness/tests/project-rule-placement-gate-loop.md` — regression record for repeated `Rule placement` STOP reminders.
  - `.lazy-harness/hooks/lifecycle/on-response-completed.sh` — invokes the helper.
  - `.lazy-harness/scripts/self-test.py` — fixture tests.
  - `.lazy-harness/AGENTS.md` — concise grammar pointer.
- Key symbols:
  - `check_project_rule_placement_helper` (`.lazy-harness/scripts/self-test.py`) — validates block/pass/no-false-positive cases.
  - `run_project_rule_placement_helper` (`.lazy-harness/scripts/self-test.py`) — helper runner.
  - `Rule placement` judgement — completion signal.
  - `MEMORY_TOOLS` / `MEMORY_RULE_CUES` (`check-project-rule-placement.sh`) — detects successful project-rule writes to Pi/OMP memory.
  - `call_succeeded` / `cue_lower` (`check-project-rule-placement.sh`) — exclude failed calls from action evidence and strip path tokens from semantic rule/action scanning.
  - `gate_already_open_this_turn` (`check-project-rule-placement.sh`) — records and suppresses same-turn project-rule placement gate fingerprints built from semantic text and successful relevant action kinds.
- Flow:
  1. User/assistant prose supplies semantic rule-placement cues; tool arguments do not.
  2. Helper checks only successful memory/write calls for memory misuse, canonical capture, or local-note action evidence.
  3. Helper accepts a successful `.lazy-harness` record/planning capture or complete explicit judgement.
  4. If placement remains missing, helper fingerprints semantic text plus successful placement-relevant action kinds and checks the `(message_id, project-rule-placement fingerprint)` state.
  5. First fire injects STOP with A/B/C/D/E/F options and records the fingerprint; repeated same-turn fire exits silently.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - `bash -n .lazy-harness/hooks/lifecycle/helpers/check-project-rule-placement.sh`
  - `python3 .lazy-harness/scripts/doctor.py --profile smoke`
  - focused: `.lazy-harness/scripts/self-test.py` `check_project_rule_placement_helper` validates first fire, same-turn suppression, new-turn re-fire, tool/path-only fetch silence, failed-call exclusion, and genuine semantic re-fire.
  - focused: `.lazy-harness/scripts/self-test.py` `_check_pi_agent_end_current_turn_scope` validates that Pi `agent_end` sends only the active turn's tool results while retaining current failed-tool structure.
  - focused: `.lazy-harness/scripts/self-test.py` `run_project_rule_placement_helper` invokes the helper with `env_without_lazy_runtime()` so duplicate-suppression fixtures do not inherit outer runtime/session state.
- Cross-layer links:
  - SSOT: `.lazy-harness/ssot/rule-sources.md`
  - SSOT: `.lazy-harness/ssot/gate-fingerprint-state.md`
  - SSOT: `.lazy-harness/ssot/project-identity.md`
  - TDD: `.lazy-harness/tests/project-rule-placement-gate-loop.md`
  - ADR: `.lazy-harness/decisions/0024-ai-first-framework-redesign.md`
  - ADR: `.lazy-harness/decisions/0031-root-bound-record-convergence.md`
- Machine index:
  - graph ids: `kg_sdd_project_rule_router`
  - generated index key: `pending until implementation-index generator exists`

## Discovery capture — current-turn placement evidence

- Primary canonical record: `.lazy-harness/tests/project-rule-placement-gate-loop.md`.
- SDD: this record has an independent contract delta for semantic cue sources and successful structural action evidence.
- BDD: no separate canonical record; the user-visible disappearance of the false follow-up is the regression correction protected by the primary TDD record.
- SSOT: `.lazy-harness/ssot/gate-fingerprint-state.md` is updated because the project-rule fingerprint input is narrowed.
- DDD: no domain vocabulary or business-rule delta.
- ADR: no new trade-off; this preserves the existing lifecycle and option-gate decisions while correcting evidence scope.
