# ADR 0045 — Purpose-Scoped Retrieval

Status: accepted
Date: 2026-06-10
Layer: ADR
Related DDD: `.lazy-harness/domain/purpose-scoped-retrieval.md`
Related BDD: `.lazy-harness/behavior/purpose-scoped-retrieval.md`
Related SDD: `.lazy-harness/spec/platform/purpose-scoped-retrieval.md`
Related TDD: `.lazy-harness/tests/purpose-scoped-retrieval.md`
Related SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`
Related planning: `.lazy-harness/planning/purpose-scoped-retrieval-implementation-plan.md`

## Context

Lazy-harness previously optimized for record-first safety. Dogfood showed a cost: when the agent is choosing how to act, testing, or selecting a command, broad DDD/SDD/ADR/SSOT record sweeps waste tokens and can distract from the relevant operating-rule/test/capability surfaces.

## Decision

Adopt explicit purpose-scoped retrieval through:

```bash
lazy find --purpose <fact|rulebook|test|capability|source|architecture|full> <query>
```

The LLM/user chooses `--purpose`. The CLI does not infer purpose from raw user text and does not decide gates, risk, required reads, or next action. Output is cue-only.

## Why not `lazy route`

`lazy route` and route telemetry were superseded because route classifiers over raw user text became semantic authority. This ADR keeps the name `find` to emphasize deterministic candidate retrieval under explicit purpose.

## Consequences

- Fact/contract/implementation questions still use record/source/test evidence.
- Operating-rule/action questions start with rulebook/capability surfaces.
- Test/validation questions start with TDD/test/source-test/capability surfaces.
- Architecture/full purposes remain broad and safe.
- Lifecycle hooks may mention purpose-scoped retrieval later, but must not classify raw prompts into a purpose automatically.

## Implementation map

- Status: `phase-0-2-implemented`
- Primary records:
  - `.lazy-harness/domain/purpose-scoped-retrieval.md`
  - `.lazy-harness/behavior/purpose-scoped-retrieval.md`
  - `.lazy-harness/spec/platform/purpose-scoped-retrieval.md`
  - `.lazy-harness/tests/purpose-scoped-retrieval.md`
- Primary source:
  - `.lazy-harness/scripts/purpose-find.ts`
  - `.lazy-harness/bin/lazy`
  - `.lazy-harness/ssot/capabilities.json`
  - `.lazy-harness/project/feature-navigation.xml`
  - `.lazy-harness/scripts/self-test.py`
- Validation:
  - `.lazy-harness/bin/lazy find --purpose test <query>`
  - `.lazy-harness/bin/lazy find --purpose rulebook <query>`
  - `.lazy-harness/bin/lazy find --purpose fact <query>`
  - `.lazy-harness/bin/lazy test`

## Rule placement

- Rule: Retrieval must be purpose-scoped; use record search for facts, rulebook/capability search for behavior/action policy, and test surfaces for validation before widening only when needed.
- Scope: framework-global
- Primary record: `.lazy-harness/decisions/0045-purpose-scoped-retrieval.md`
- Why not AGENTS.md: this is an architecture/runtime retrieval decision with source/tests and implementation maps; AGENTS may later point to it.
- Why not `.jcode`: this changes shared lazy-harness framework behavior, not local/private Jcode wiring.
- Confirmation: user-confirmed
