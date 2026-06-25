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
  - store canonical behavior policy semantics in `.lazy-harness/ssot/policies.json`
  - keep `.lazy-harness/rules/**` as a compatibility/explain surface for human review and host sync
  - bind machine-readable action surfaces in `.lazy-harness/ssot/capabilities.json`
- Avoid:
  - storing shared project/team operating policy only in Pi/OMP local notes
  - relying on fact records alone to steer commands
- Requires:
  - typed policy coverage in `.lazy-harness/ssot/policies.json` before treating a rulebook entry as behavior policy authority
  - `Status`, `Layer`, `Scope`, `Owner`, `Level`, and `## Rule digest`
  - capability binding for active `default|warn|block` rules
  - bypass explanation for `warn|block` rules
- Bypass:
  - local/private Pi/OMP-only preferences may use Pi/OMP local notes (`.pi/`/`.omp/`) only with explicit `Scope: local-only`
- Record completion:
  - update related ADR/SDD/TDD/SSOT when rulebook schema or action level behavior changes

## Operating rule

This directory is a compatibility/explain surface for project operating rules: how agents should work while developing in a host project.

Canonical behavior policy semantics live in `.lazy-harness/ssot/policies.json`. Rulebook markdown remains for human review, host compatibility, and generated/explain surfaces; it is no longer the canonical source for new policy semantics.

Project fact records remain in DDD/SDD/BDD/TDD/ADR/SSOT layers. Rulebook entries are for behavioral policy such as canonical commands, discouraged commands, required checks, bypass conditions, and validation workflows.

## Examples

Good examples:

- A host says: use `bun run wt new` instead of raw `git worktree add`.
- A host says: use `bun run dev:instance` instead of raw `bun run dev`.
- A team says: run a specific validation command before touching generated schema files.

Bad examples:

- Putting shared team policy only in `.pi/APPEND_SYSTEM.md`.
- Storing command policy as a vague note in memory without typed policy and capability bindings.
- Jumping directly from a rulebook entry to a hard-stop hook without Guidance Ladder promotion evidence.

## Capability binding

Rulebook entries should link to `.lazy-harness/ssot/capabilities.json` entries by `Related capability`, `sourceRecord`, or `rulebookRecord`, and to typed policies by `Related policy` / capability `policyIds`.

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
  - `.lazy-harness/bin/lazy rules list --format=json` exposes `rulebook-compatibility/v1` and `retiredCanonicalSemantics=true`
- Tests:
  - `.lazy-harness/tests/project-operating-rulebook.md`
  - `.lazy-harness/scripts/self-test.py`
