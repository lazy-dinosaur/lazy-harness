# ADR 0040 — Capability Registry Separates Kind From Enforcement Level

- Status: Accepted
- Date: 2026-05-26
- Trigger: User clarified that project customization can be scripts, skills, prompts, hooks, commands, or validations, and should not always become a hard rule.

## Context

ADR 0039 added Rule Lifecycle bindings for executable rules. Dogfooding then revealed a broader need: projects often define useful workflows or tools that agents should remember and use, but most should not be forced by default.

Examples include worktree scripts, lint commands, prompt templates, release skills, validation checklists, and audit reminders.

## Decision

Create a Capability Registry with two independent dimensions:

- `kind`: what the capability is.
- `level`: how strongly lazy-harness should steer/enforce it.

Phase 1 implements only discover/list/resolve/audit. No new blocking behavior is introduced by this ADR.

## Consequences

Positive:

- Avoids overfitting every project customization into a hook.
- Gives agents a structured way to find project-specific tools.
- Allows later warn/block integration only for explicit hard policies.

Risks:

- Registry can become stale if source records move.
- Too many low-quality discover entries can create noise.
- Later integration must avoid silently escalating `recommend` or `default` to `block`.

## Implementation map

- Status: `phase-1-implemented`
- Primary files:
  - `.lazy-harness/ssot/capability-registry.md`
  - `.lazy-harness/ssot/capabilities.json`
  - `.lazy-harness/spec/platform/capability-resolution.md`
  - `.lazy-harness/tests/capability-registry.md`
  - `.lazy-harness/scripts/capability.ts`
  - `.lazy-harness/bin/lazy`
  - `.lazy-harness/scripts/self-test.py`
- Validation:
  - `python3 .lazy-harness/scripts/self-test.py`
  - `python3 .lazy-harness/scripts/doctor.py --profile smoke`
