# ADR 0040 — Capability Registry Separates Kind From Enforcement Level

- Status: Accepted
- Date: 2026-05-26
- Trigger: User clarified that project customization can be scripts, skills, prompts, hooks, commands, or validations, and should not always become a hard rule.

## Rule digest

- Status: active
- Layer: ADR
- Scope: framework-global
- Applies when:
  - registering project customizations (scripts, skills, prompts, hooks, commands, validations)
  - deciding how strongly a capability should be steered or enforced
- Must:
  - model each capability with independent `kind` (what it is) and `level` (how strongly enforced)
  - keep most discovered capabilities advisory; reserve warn/block for explicit hard policies
- Must not:
  - silently escalate `recommend`/`default` capabilities to `block`
- Record completion:
  - changes to capability kind/level semantics update this ADR, `.lazy-harness/ssot/capability-registry.md`, and `.lazy-harness/spec/platform/capability-resolution.md`
- Related records:
  - `.lazy-harness/ssot/capability-registry.md`
  - `.lazy-harness/spec/platform/capability-resolution.md`
  - `.lazy-harness/tests/capability-registry.md`

## Context

ADR 0039 added Rule Lifecycle bindings for executable rules. Dogfooding then revealed a broader need: projects often define useful workflows or tools that agents should remember and use, but most should not be forced by default.

Examples include worktree scripts, lint commands, prompt templates, release skills, validation checklists, and audit reminders.

## Decision

Create a Capability Registry with two independent dimensions:

- `kind`: what the capability is.
- `level`: how strongly lazy-harness should steer/enforce it.

Phase 1/2 implements only add/discover/list/resolve/audit. No new blocking behavior is introduced by this ADR.

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

- Status: `phase-2-implemented`
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
