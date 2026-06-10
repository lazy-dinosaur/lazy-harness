# Project Operating Rulebook Regression

Status: accepted
Layer: TDD
Related ADR: `.lazy-harness/decisions/0044-project-operating-rulebook.md`
Related SDD: `.lazy-harness/spec/platform/project-operating-rulebook.md`
Related SSOT: `.lazy-harness/ssot/capability-registry.md`

## Regression

Project-specific development operating rules must not be reduced to project fact records. A host must be able to store a rulebook entry and bind it to machine-readable preferred/discouraged actions so future agents can resolve the right behavior.

## Required protection

Self-test must prove:

- `.lazy-harness/rules/**` exists as the canonical human operating rulebook path.
- `lazy rules list --format=json` parses active entries.
- `lazy rules audit --strict --format=json` validates required metadata/sections and capability links.
- `lazy rules resolve --action 'git worktree add feature/x'` can match a discouraged action and return the preferred replacement.
- `lazy capability resolve --action 'git worktree add feature/x'` also matches `discouragedActions`.
- Missing rulebook/capability links fail audit deterministically.
- No blocking hook is installed by Phase 0-2.

## Layer completeness gate

- DDD: no domain/business rule impact.
- SDD: `.lazy-harness/spec/platform/project-operating-rulebook.md` and `.lazy-harness/spec/platform/capability-resolution.md`.
- BDD: agents should receive deterministic rulebook/capability guidance when resolving project operating actions.
- SSOT: `.lazy-harness/ssot/rule-sources.md` and `.lazy-harness/ssot/capability-registry.md`.
- ADR: `.lazy-harness/decisions/0044-project-operating-rulebook.md`.

## Implementation map

- Status: `phase-0-2-implemented`
- Primary files:
  - `.lazy-harness/scripts/rulebook.ts`
  - `.lazy-harness/scripts/capability.ts`
  - `.lazy-harness/bin/lazy`
  - `.lazy-harness/scripts/self-test.py`
- Key symbols:
  - `loadRulebook`
  - `auditRules`
  - `resolveRules`
  - `resolveCapabilities`
  - `check_project_operating_rulebook_cli`
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - `.lazy-harness/bin/lazy test`
