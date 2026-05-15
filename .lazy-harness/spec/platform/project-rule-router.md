# Project Rule Router

Status: accepted
Layer: SDD
Related SSOT: `.lazy-harness/ssot/rule-sources.md`
Related SSOT: `.lazy-harness/ssot/project-identity.md`
Related backlog: `.lazy-harness/planning/project-rule-discovery-router-backlog.md`

## Purpose

Route newly discovered project-specific rules to the right durable source of truth.

This prevents agents from treating `.jcode/harness/20-project-rules.md` as a catch-all when a rule should be visible through `.lazy-harness` records across sessions and hosts.

## Trigger cues

The router applies when a response or user correction mentions any of:

- `프로젝트 규칙`, `프로젝트마다 규칙`, `규칙 추가`, `룰 추가`
- `AGENTS.md 수정`, `AGENTS에 넣`, `agents.md`
- `.jcode`, `.lazy-harness`, `20-project-rules`
- `어디에 기록`, `어디에 저장`, `문서화`, `source of truth`, `SSOT`
- user correction about workflow, source-of-truth, ownership, forbidden mutation, or project-specific operating policy

## Completion contract

A triggered turn is complete only if one condition is true:

1. A `.lazy-harness` record/planning artifact is updated for the rule.
2. The response includes a complete `Rule placement` judgement.
3. `.jcode/harness/20-project-rules.md` is updated only as a pointer to canonical `.lazy-harness` records, or the response/file content includes `jcode-local` or `local-only` judgement.
4. The agent stops with an option gate because placement is ambiguous.

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
- especially when the response chooses `.jcode` for a project rule without `jcode-local` or `local-only` scope.

The helper must avoid false positives on casual mentions of AGENTS.md or `.jcode` without rule-placement language.

Generated `.jcode/harness/20-project-rules.md` templates must be pointer-only by default. They should tell agents to read `.lazy-harness/ssot/rule-sources.md` and layer records for custom host/team rules rather than inviting new project-specific rule bodies into `.jcode`.

Existing user-owned `.jcode/harness/20-project-rules.md` files that predate pointer-only behavior are migrated by Jcode wiring: the active file becomes the generated pointer-only note, and the previous content is archived under `.jcode/archive/20-project-rules.pre-pointer-only-migration.md` so it is not loaded as active harness instructions.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/spec/platform/project-rule-router.md` — this SDD contract.
  - `.lazy-harness/ssot/rule-sources.md` — canonical placement registry.
  - `.lazy-harness/hooks/lifecycle/helpers/check-project-rule-placement.sh` — enforcement helper.
  - `.lazy-harness/hooks/lifecycle/on-response-completed.sh` — invokes the helper.
  - `.lazy-harness/scripts/self-test.py` — fixture tests.
  - `.lazy-harness/AGENTS.md` — concise grammar pointer.
- Key symbols:
  - `check_project_rule_placement_helper` (`.lazy-harness/scripts/self-test.py`) — validates block/pass/no-false-positive cases.
  - `run_project_rule_placement_helper` (`.lazy-harness/scripts/self-test.py`) — helper runner.
  - `Rule placement` judgement — completion signal.
- Flow:
  1. Rule placement cues appear in a response.
  2. Helper checks for `.lazy-harness` record/planning capture or explicit judgement.
  3. Missing placement injects STOP with A/B/C/D/E options.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - `bash -n .lazy-harness/hooks/lifecycle/helpers/check-project-rule-placement.sh`
  - `python3 .lazy-harness/scripts/doctor.py --profile smoke`
- Cross-layer links:
  - SSOT: `.lazy-harness/ssot/rule-sources.md`
  - SSOT: `.lazy-harness/ssot/project-identity.md`
  - ADR: `.lazy-harness/decisions/0024-ai-first-framework-redesign.md`
  - ADR: `.lazy-harness/decisions/0031-root-bound-record-convergence.md`
- Machine index:
  - graph ids: `kg_sdd_project_rule_router`
  - generated index key: `pending until implementation-index generator exists`
