# Rule Sources and Placement

Status: accepted
Layer: SSOT
Date: 2026-05-15
Related SSOT: `.lazy-harness/ssot/project-identity.md`
Related SDD: `.lazy-harness/spec/platform/project-rule-router.md`
Related ADR: `.lazy-harness/decisions/0024-ai-first-framework-redesign.md`
Related ADR: `.lazy-harness/decisions/0031-root-bound-record-convergence.md`

## Purpose

This record is the source of truth for deciding where newly discovered project-specific rules belong.

Agents must not default to `.jcode/harness/20-project-rules.md` for project/team policy. `.jcode` is only for generated/private Jcode wiring and pointer-only reminders unless a rule placement judgement explicitly says the rule is local-only.

`.jcode/harness/20-project-rules.md` must not accumulate host/team rule bodies as a mirror of `.lazy-harness` records. When a rule is discovered, corrected, or customized for a host, the durable content belongs in `.lazy-harness/{domain,spec,behavior,tests,decisions,ssot,planning}/**`; `.jcode` may only point to those canonical records or store truly local/private execution preferences.

## Priority order

When instructions conflict, use this order:

1. Current explicit user request.
2. Nearest nested/private `.jcode` instruction for local Jcode workflow.
3. `.lazy-harness/ssot/project-identity.md` for host role, ownership, and source-of-truth.
4. This `.lazy-harness/ssot/rule-sources.md` record for rule placement.
5. Layer records under `.lazy-harness/{domain,spec,behavior,tests,decisions,ssot}/`.
6. Shared `.lazy-harness/AGENTS.md` grammar.

## Rule placement matrix

| Rule type | Primary location |
|---|---|
| Framework-common agent behavior that applies to every host | `.lazy-harness/AGENTS.md` |
| Host identity, source-of-truth, ownership, forbidden mutation | `.lazy-harness/ssot/project-identity.md` or dedicated SSOT |
| Team/project operating policy shared by all agents | `.lazy-harness/ssot/rule-sources.md` or relevant ADR/SSOT |
| Domain/business language or invariant | `.lazy-harness/domain/**` |
| API/component/data/IPC contract | `.lazy-harness/spec/**` |
| User-visible workflow or expected behavior | `.lazy-harness/behavior/**` |
| Regression/protection expectation | `.lazy-harness/tests/**` |
| Trade-off or why decision | `.lazy-harness/decisions/**` |
| Local/private Jcode preference or workflow | `.jcode/harness/20-project-rules.md` as pointer-only or explicit `jcode-local` |
| Multi-step work plan/backlog | `.lazy-harness/planning/**` |

## Required judgement

When a new rule is discussed, corrected, or routed, use this compact judgement unless the placement is already explicit from existing records:

```md
## Rule placement

- Rule: ...
- Scope: framework-global | host-project | team-policy | layer-fact | jcode-local | transient-plan | ambiguous
- Primary record: ...
- Why not AGENTS.md: ...
- Why not `.jcode`: ...
- Confirmation: user-confirmed | inferred-from-record | needs-option-gate
```

## Ambiguous placement option gate

If the rule could belong to both `.lazy-harness` and `.jcode`, stop and ask exactly once:

A. `.lazy-harness/ssot/...` shared project rule (Recommended for team/project policy)
B. `.lazy-harness/decisions/...` trade-off/why decision
C. `.lazy-harness/planning/...` transient plan/backlog
D. `.jcode/harness/20-project-rules.md` local/private Jcode-only workflow
E. 직접 입력

`Confirmation: needs-option-gate` is a waiting state, not a completed judgement. The agent must not run tools, write records, dispatch releases, or self-select the Recommended option until the user chooses. Once the user chooses, record the result as `Confirmation: user-confirmed` and do not ask the same gate again.

## Examples

- PR/worktree tracker policy used by future agents: `.lazy-harness/planning/**` plus SSOT/ADR if enduring.
- “Always check local tracker first before PR work”: project operating policy, prefer `.lazy-harness/ssot/rule-sources.md` or dedicated SSOT, not `.jcode` by default.
- Personal shortcut, preferred shell alias, or Jcode-only UI workflow: `.jcode/harness/20-project-rules.md` with `Scope: jcode-local`.
- Host/team rule customization: record the rule body in `.lazy-harness/**`; `.jcode/harness/20-project-rules.md` may only link to that record.
- Host source ownership or downstream/upstream boundary: `.lazy-harness/ssot/project-identity.md` or dedicated ownership SSOT.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/ssot/rule-sources.md` — this SSOT placement registry.
  - `.lazy-harness/spec/platform/project-rule-router.md` — SDD operating standard.
  - `.lazy-harness/hooks/lifecycle/helpers/check-project-rule-placement.sh` — response-completed guard.
  - `.lazy-harness/scripts/self-test.py` — helper tests and AGENTS invariant.
  - `.lazy-harness/AGENTS.md` — concise grammar pointer.
- Key symbols:
  - `Rule placement` judgement — completion signal for routing.
  - `check_project_rule_placement_helper` (`.lazy-harness/scripts/self-test.py`) — fixture coverage.
- Flow:
  1. User or analysis introduces a rule/correction/workflow policy.
  2. Agent reads this registry and project identity.
  3. Agent writes the correct `.lazy-harness` record; `.jcode` receives only a pointer unless the rule is explicitly `jcode-local`.
  4. Ambiguity triggers the option gate.
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
