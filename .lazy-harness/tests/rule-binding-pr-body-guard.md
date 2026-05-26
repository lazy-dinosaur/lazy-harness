# Rule Binding PR Body Guard Regression

Status: accepted
Layer: TDD
Related SSOT: `.lazy-harness/ssot/rule-lifecycle.md`
Related SDD: `.lazy-harness/spec/platform/rule-binding-action-boundary.md`
Related ADR: `.lazy-harness/decisions/0039-rule-lifecycle-bindings.md`

## Regression

A stored PR body rule can be missed if the agent does not recall the host record before creating or editing a PR.

## Required protection

When a host has `.lazy-harness/ssot/pr-description-format.md`, a `gh pr create` or `gh pr edit` bash command with a missing/malformed body must be denied before execution if it lacks required headings:

- `## Why`
- `## What`
- `## Task`

Valid bodies with those headings must pass.

## Layer completeness gate

- DDD: no domain rule.
- SDD: protected by `.lazy-harness/spec/platform/rule-binding-action-boundary.md`.
- BDD: agent-visible behavior should feel like PR creation automatically applies the host PR policy.
- SSOT: `.lazy-harness/ssot/rule-lifecycle.md` owns lifecycle/binding metadata.
- ADR: `.lazy-harness/decisions/0039-rule-lifecycle-bindings.md` records the trade-off.

## Implementation map

- Status: `implemented-first-exemplar`
- Primary files:
  - `.lazy-harness/hooks/lifecycle/helpers/check-rule-action-boundary.py` — guard implementation.
  - `.lazy-harness/scripts/self-test.py` — fixture tests.
  - `.lazy-harness/scripts/jcode-wiring.ts` — generated `.jcode` hook wiring.
- Key symbols:
  - `check_rule_action_boundary_pr_body_guard` — self-test fixture.
  - `check_jcode_wiring_rule_action_boundary_hook` — template invariant fixture.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py`
