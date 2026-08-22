# Rule Sources and Placement

Status: accepted
Layer: SSOT
Date: 2026-05-15
Related SSOT: `.lazy-harness/ssot/project-identity.md`
Related SDD: `.lazy-harness/spec/platform/project-rule-router.md`
Related ADR: `.lazy-harness/decisions/0024-ai-first-framework-redesign.md`
Related ADR: `.lazy-harness/decisions/0031-root-bound-record-convergence.md`
Related ADR: `.lazy-harness/decisions/0050-pi-omp-only-runtime.md`

## Rule digest

- Status: active
- Layer: SSOT
- Scope: framework-global
- Aliases:
  - 규칙 출처
  - rule sources
  - 어느 규칙이 어디
  - 규칙 위치 판정
- Applies when:
  - deciding where a newly discovered or corrected project/team rule belongs
  - routing a rule among `.lazy-harness` records or Pi/OMP local notes (`.pi/`/`.omp/`)
  - resolving conflicting instructions by priority, or adding/applying an operating rule
- Must:
  - put durable host/team rule bodies in `.lazy-harness/{domain,spec,behavior,tests,decisions,ssot,planning}/**`, not Pi/OMP local notes
  - store operating-rule semantics in `ssot/policies.json` (+`capabilities.json` to steer actions); `rules/**` is compatibility/explain only
  - resolve existing rules (`lazy policy/capability/rules resolve`) before adding a new operating rule
  - fix lifecycle/hook loops at the structural payload/source boundary with a regression test, not broad string filters
- Must not:
  - store host/team policy only in Pi/OMP local notes, or self-select the Recommended placement while an option gate is pending
- Record completion:
  - rule-placement or operating-rule storage/resolve changes update this SSOT plus `spec/platform/project-rule-router.md`
- Related records:
  - `.lazy-harness/ssot/project-identity.md`
  - `.lazy-harness/spec/platform/project-rule-router.md`
  - `.lazy-harness/decisions/0024-ai-first-framework-redesign.md`
  - `.lazy-harness/decisions/0031-root-bound-record-convergence.md`

## Purpose

This record is the source of truth for deciding where newly discovered project-specific rules belong.

Agents must not default to `.pi/APPEND_SYSTEM.md` (Pi/OMP local notes) for project/team policy. Pi/OMP local notes (`.pi/` or `.omp/`) are only for generated/private local wiring and pointer-only reminders unless a rule placement judgement explicitly says the rule is `local-only`; local notes are not a canonical store for host/team rules. See `.lazy-harness/decisions/0050-pi-omp-only-runtime.md`.

`.pi/APPEND_SYSTEM.md` and other Pi/OMP local notes must not accumulate host/team rule bodies as a mirror of `.lazy-harness` records. When a rule is discovered, corrected, or customized for a host, the durable content belongs in `.lazy-harness/{domain,spec,behavior,tests,decisions,ssot,planning}/**`; Pi/OMP local notes (`.pi/` or `.omp/`) may only point to those canonical records or store truly local/private execution preferences. If an agent mistakenly writes a project rule into a local note, it must remove it and write/update the canonical record in the same turn.

## Priority order

When instructions conflict, use this order:

1. Current explicit user request.
2. Nearest nested/private Pi/OMP local note (`.pi/`/`.omp/`) for local workflow.
3. `.lazy-harness/ssot/project-identity.md` for host role, ownership, and source-of-truth.
4. This `.lazy-harness/ssot/rule-sources.md` record for rule placement.
5. Layer records under `.lazy-harness/{domain,spec,behavior,tests,decisions,ssot}/`.
6. Shared `.lazy-harness/AGENTS.md` grammar.

## Rule placement matrix

| Rule type | Primary location |
|---|---|
| Framework-common agent behavior that applies to every host | `.lazy-harness/AGENTS.md` |
| Host identity, source-of-truth, ownership, forbidden mutation | `.lazy-harness/ssot/project-identity.md` or dedicated SSOT |
| Team/project operating policy shared by all agents | `.lazy-harness/ssot/policies.json` plus `.lazy-harness/ssot/capabilities.json` when it should steer actions; `.lazy-harness/rules/**` is a compatibility/explain surface |
| Domain/business language or invariant | `.lazy-harness/domain/**` |
| API/component/data/IPC contract | `.lazy-harness/spec/**` |
| User-visible workflow or expected behavior | `.lazy-harness/behavior/**` |
| Regression/protection expectation | `.lazy-harness/tests/**` |
| Trade-off or why decision | `.lazy-harness/decisions/**` |
| Local/private Pi/OMP preference or workflow | `.pi/APPEND_SYSTEM.md` as pointer-only or explicit `local-only`; Pi/OMP local notes only for personal/user preferences, never project/team policy |
| Multi-step work plan/backlog | `.lazy-harness/planning/**` |

## Required judgement

When a new rule is discussed, corrected, or routed, use this compact judgement unless the placement is already explicit from existing records:

```md
## Rule placement

- Rule: ...
- Scope: framework-global | host-project | team-policy | layer-fact | local-only | transient-plan | ambiguous
- Primary record: ...
- Why not AGENTS.md: ...
- Why not local notes: ...
- Confirmation: user-confirmed | inferred-from-record | needs-option-gate
```

## Ambiguous placement option gate

If the rule could belong to both `.lazy-harness` and a Pi/OMP local note, stop and ask exactly once:

A. `.lazy-harness/ssot/...` shared project rule (Recommended for team/project policy)
B. `.lazy-harness/decisions/...` trade-off/why decision
C. `.lazy-harness/planning/...` transient plan/backlog
D. `.pi/APPEND_SYSTEM.md` local/private Pi/OMP-only workflow
E. Remove a mistaken local-note rule, then record the canonical `.lazy-harness` source
F. 직접 입력

`Confirmation: needs-option-gate` is a waiting state, not a completed judgement. The agent must not run tools, write records, dispatch releases, or self-select the Recommended option until the user chooses. Once the user chooses, record the result as `Confirmation: user-confirmed` and do not ask the same gate again.

## Examples

- PR/worktree tracker policy used by future agents: `.lazy-harness/ssot/policies.json` plus capability binding when it should steer commands; `.lazy-harness/rules/**` may explain the policy for compatibility; planning may track rollout/backlog.
- “Always check local tracker first before PR work”: project operating policy, prefer `.lazy-harness/ssot/policies.json` plus `.lazy-harness/ssot/capabilities.json`, not Pi/OMP local notes by default.
- Personal shortcut, preferred shell alias, or Pi/OMP-only local workflow: `.pi/APPEND_SYSTEM.md` with `Scope: local-only`.
- Host/team rule customization: record the rule body in `.lazy-harness/**`; `.pi/APPEND_SYSTEM.md` may only link to that record; Pi/OMP local notes must not be used as durable policy storage.
- Host source ownership or downstream/upstream boundary: `.lazy-harness/ssot/project-identity.md` or dedicated ownership SSOT.

## Harness fix quality rule

User-confirmed correction on 2026-05-21: do not patch lazy-harness gates with broad string filters or temporary workaround-style suppressions. When a lifecycle/hook loop appears, identify the structural payload/source boundary first, then fix the narrow structural cause and protect it with a regression test.

Required standard:

- Prefer payload structure, source field, message role, tool-call shape, fingerprint state, or other explicit contract signals over broad text matching.
- If text matching is unavoidable, constrain it to the exact structural field that carries the helper output, not the entire payload/blob.
- Do not weaken normal rule detection to hide noisy gates.
- Record the root cause and regression case in the appropriate TDD/SDD/SSOT record.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/ssot/rule-sources.md` — this SSOT placement registry.
  - `.lazy-harness/spec/platform/project-rule-router.md` — SDD operating standard.
  - `.lazy-harness/hooks/lifecycle/helpers/check-project-rule-placement.sh` — response-completed guard, including runtime-local memory/transport misuse detection.
  - `.lazy-harness/scripts/self-test.py` — helper tests and AGENTS invariant.
  - `.lazy-harness/AGENTS.md` — concise grammar pointer.
- Key symbols:
  - `Rule placement` judgement — completion signal for routing.
  - runtime memory cleanup — required when a project/team rule is mistakenly stored in non-canonical personal/runtime memory.
  - `check_project_rule_placement_helper` (`.lazy-harness/scripts/self-test.py`) — fixture coverage.
- Flow:
  1. User or analysis introduces a rule/correction/workflow policy.
  2. Agent reads this registry and project identity.
  3. Agent writes the correct `.lazy-harness` record; the Pi/OMP local note receives only a pointer unless the rule is explicitly `local-only`.
  4. If the rule was placed in runtime-local memory, agent removes it there and records the canonical `.lazy-harness` source.
  5. Ambiguity triggers the option gate.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - `python3 .lazy-harness/scripts/doctor.py --profile smoke`
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/project-rule-router.md`
  - SSOT: `.lazy-harness/ssot/project-identity.md`
  - ADR: `.lazy-harness/decisions/0024-ai-first-framework-redesign.md`
  - ADR: `.lazy-harness/decisions/0031-root-bound-record-convergence.md`
- Machine index:
  - graph ids: `kg_ssot_rule_sources_project_rule_router`
  - generated index key: `pending until implementation-index generator exists`

## Project operating rulebook

Project facts and project operating rules are distinct. Facts, contracts, regressions, and decisions remain in DDD/SDD/BDD/TDD/ADR/SSOT. Development behavior rules that tell agents how to work inside a host belong canonically in `.lazy-harness/ssot/policies.json` and, when they should influence command/tool choice, in `.lazy-harness/ssot/capabilities.json`. `.lazy-harness/rules/**` remains a compatibility/explain surface for human review and host sync.

Examples include canonical worktree commands, discouraged raw dev-server commands, validation workflows, bypass rules, and team operating policy.

Rulebook entries still need `## Rule placement` when created as compatibility/explain surfaces from a user correction or new project policy, but the policy semantics must also be represented in `.lazy-harness/ssot/policies.json`.

## Operating rule resolve-before-add and storage guard (2026-06-24)

Adding or applying an operating rule must start by resolving existing rules, so a new rule does not duplicate one already stored:

- Before adding: run `lazy policy resolve` / `lazy capability resolve` / `lazy rules resolve` for the same intent/action.
- Canonical store: behavior semantics in `.lazy-harness/ssot/policies.json`, action binding in `.lazy-harness/ssot/capabilities.json`; `.lazy-harness/rules/**` is the compatibility/explain surface. Do not author operating-rule semantics as prose in an unrelated `.lazy-harness/ssot/*.md`.

Two advisory backstops run at `response.completed` (no hard gate, ADR 0041):

- `check-operating-rule-storage.py` — flags rule-store writes without prior resolve evidence (duplication) and operating-rule prose written to a non-canonical `.lazy-harness/ssot/*.md`.
- `check-response-rule-audit.py` — at apply time, flags a discouraged action of a `default`/`warn`/`block` capability used without prior resolve evidence (`discover`/`recommend` stay silent).

See `.lazy-harness/planning/operating-rule-storage-apply-repair-20260624.md` and `.lazy-harness/decisions/0048-operating-rule-storage-apply-repair.md`.
