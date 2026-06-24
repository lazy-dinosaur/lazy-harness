# Project Rule Router

Status: accepted
Layer: SDD
Related SSOT: `.lazy-harness/ssot/rule-sources.md`
Related SSOT: `.lazy-harness/ssot/project-identity.md`
Related backlog: `.lazy-harness/planning/project-rule-discovery-router-backlog.md`
Related TDD: `.lazy-harness/tests/project-rule-placement-gate-loop.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Applies when:
  - user confirms or corrects a project rule, workflow rule, ownership, or source-of-truth fact
  - 사용자가 프로젝트 규칙, 룰, 기록 위치, AGENTS, `.jcode`, memory, SSOT를 언급한다
  - deciding where to record AGENTS, `.jcode`, memory, SSOT, ADR, layer facts, or planning knowledge
  - response.completed reports project rule placement or canonical record completion problems
- Must:
  - route durable project/team rules into canonical `.lazy-harness` records, not `.jcode` or memory alone
  - include a complete Rule placement judgement when recording or reporting placement
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

This prevents agents from treating `.jcode/harness/20-project-rules.md` or Jcode `memory.remember` as a catch-all when a rule should be visible through `.lazy-harness` records across sessions and hosts.

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
3. `.jcode/harness/20-project-rules.md` is updated only as a pointer to canonical `.lazy-harness` records, or the response/file content includes `jcode-local` or `local-only` judgement.
4. A mistaken Jcode `memory.remember` project-rule write is removed with `memory forget` and the rule is re-recorded in canonical `.lazy-harness` records.
5. The agent stops with an option gate because placement is ambiguous. `Confirmation: needs-option-gate` is not complete and must not be followed by tool calls or self-selected Recommended execution.

## Rule placement judgement

```md
## Rule placement

- Rule: ...
- Scope: framework-global | host-project | team-policy | layer-fact | jcode-local | transient-plan | ambiguous
- Primary record: ...
- Why not AGENTS.md: ...
- Why not `.jcode`: ...
- Confirmation: user-confirmed | inferred-from-record | needs-option-gate
```

## Placement matrix

| Scope | Primary location |
|---|---|
| `framework-global` | `.lazy-harness/AGENTS.md` only if universal and thin |
| `host-project` | `.lazy-harness/ssot/project-identity.md` or dedicated SSOT |
| `team-policy` | `.lazy-harness/ssot/rule-sources.md` or dedicated SSOT/ADR |
| `layer-fact` | DDD/SDD/BDD/TDD/ADR/SSOT based on the fact type |
| `jcode-local` | `.jcode/harness/20-project-rules.md` as local-only note |
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

The helper must avoid false positives on casual mentions of AGENTS.md or `.jcode` without rule-placement language.

The helper must also avoid same-turn repeated STOP reminders. Production Jcode `response.completed` payloads may not include `assistant_response`, so the helper can repeatedly derive the same project-rule placement gate from stable fields such as `last_user_message` and `recent_tool_calls`. When it emits a derived gate, it records a deterministic `project-rule-placement:<fingerprint>` entry in `$LAZY_RUNTIME_ROOT/state/open-gates.json`; the same `(message_id, fingerprint)` exits silently, while a new `message_id` may re-fire.

Self-test runners for this helper must clear inherited lazy runtime/session environment before invoking `check-project-rule-placement.sh`, so fixture duplicate-suppression state is read from the deterministic default runtime path rather than an outer Jcode session path.

Generated `.jcode/harness/20-project-rules.md` templates must be pointer-only by default. They should tell agents to read `.lazy-harness/ssot/rule-sources.md` and layer records for custom host/team rules rather than inviting new project-specific rule bodies into `.jcode`.

Existing user-owned `.jcode/harness/20-project-rules.md` files that predate pointer-only behavior are migrated by Jcode wiring: the active file becomes the generated pointer-only note, and the previous content is archived under `.jcode/archive/20-project-rules.pre-pointer-only-migration.md` so it is not loaded as active harness instructions.

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
  - `MEMORY_TOOLS` / `MEMORY_RULE_CUES` (`check-project-rule-placement.sh`) — detects project rules written to Jcode memory.
  - `gate_already_open_this_turn` (`check-project-rule-placement.sh`) — records and suppresses same-turn project-rule placement gate fingerprints.
- Flow:
  1. Rule placement cues appear in a response.
  2. Helper checks for Jcode memory misuse before accepting `.lazy-harness` record/planning capture.
  3. Helper checks for `.lazy-harness` record/planning capture or explicit judgement.
  4. If missing placement or memory misuse would inject STOP, helper first checks the `(message_id, project-rule-placement fingerprint)` state.
  5. First fire injects STOP with A/B/C/D/E/F options and records the fingerprint; repeated same-turn fire exits silently.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - `bash -n .lazy-harness/hooks/lifecycle/helpers/check-project-rule-placement.sh`
  - `python3 .lazy-harness/scripts/doctor.py --profile smoke`
  - focused: `.lazy-harness/scripts/self-test.py` `check_project_rule_placement_helper` validates first fire, same-turn suppression, and new-turn re-fire without `assistant_response`.
  - focused: `.lazy-harness/scripts/self-test.py` `run_project_rule_placement_helper` invokes the helper with `env_without_lazy_runtime()` so duplicate-suppression fixtures do not inherit outer Jcode runtime/session state.
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
