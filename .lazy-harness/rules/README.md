# Project Operating Rulebook

Status: active
Layer: Rulebook
Scope: framework-global
Owner: lazy-harness
Level: discover
Related capability: project-operating-rulebook
Related policy: project-operating-rulebook-policy
Related records:
- `.lazy-harness/decisions/0044-project-operating-rulebook.md`
- `.lazy-harness/spec/platform/project-operating-rulebook.md`
- `.lazy-harness/ssot/capability-registry.md`

## Rule digest

- Applies when:
  - adding project/team development operating policy
  - documenting canonical commands, discouraged commands, validation workflows, or bypass rules
  - deciding whether something is a project fact or agent behavior rule
- Prefer:
  - store human-readable operating rules in `.lazy-harness/rules/**`
  - bind machine-readable action surfaces in `.lazy-harness/ssot/capabilities.json`
- Avoid:
  - storing shared project/team operating policy only in `.jcode/**` or Jcode memory
  - relying on fact records alone to steer commands
- Requires:
  - `Status`, `Layer`, `Scope`, `Owner`, `Level`, and `## Rule digest`
  - capability binding for active `default|warn|block` rules
  - bypass explanation for `warn|block` rules
- Bypass:
  - local/private Jcode-only preferences may use `.jcode/**` only with explicit `Scope: jcode-local`
- Record completion:
  - update related ADR/SDD/TDD/SSOT when rulebook schema or action level behavior changes

## Operating rule

This directory stores canonical project operating rules: how agents should work while developing in a host project.

Project fact records remain in DDD/SDD/BDD/TDD/ADR/SSOT layers. Rulebook entries are for behavioral policy such as canonical commands, discouraged commands, required checks, bypass conditions, and validation workflows.

## Examples

Good examples:

- A host says: use `bun run wt new` instead of raw `git worktree add`.
- A host says: use `bun run dev:instance` instead of raw `bun run dev`.
- A team says: run a specific validation command before touching generated schema files.

Bad examples:

- Putting shared team policy only in `.jcode/harness/20-project-rules.md`.
- Storing command policy as a vague note in memory without a capability binding.
- Jumping directly from a rulebook entry to a hard-stop hook without Guidance Ladder promotion evidence.

## Capability binding

Rulebook entries should link to `.lazy-harness/ssot/capabilities.json` entries by `Related capability`, `sourceRecord`, or `rulebookRecord`.

Capability fields for action guidance:

- `preferredActions`
- `discouragedActions`
- `requiresReasonForBypass`
- `rulebookRecord`

## Implementation map

- Source records:
  - `.lazy-harness/spec/platform/project-operating-rulebook.md`
  - `.lazy-harness/decisions/0044-project-operating-rulebook.md`
- Capabilities:
  - `project-operating-rulebook`
- Policies:
  - `project-operating-rulebook-policy`
- Validation:
  - `.lazy-harness/bin/lazy rules audit --strict`
  - `.lazy-harness/bin/lazy rules resolve --intent adding_project_operating_policy`
  - `.lazy-harness/bin/lazy policy retire-readiness --strict --format=json`
- Tests:
  - `.lazy-harness/tests/project-operating-rulebook.md`
  - `.lazy-harness/scripts/self-test.py`
