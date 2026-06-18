# ADR 0044 — Project Operating Rulebook

Status: superseded-by-0046
Date: 2026-06-10
Layer: ADR
Related planning: `.lazy-harness/planning/project-operating-rulebook-implementation-plan.md`
Related SDD: `.lazy-harness/spec/platform/project-operating-rulebook.md`
Related SSOT: `.lazy-harness/ssot/rule-sources.md`
Related SSOT: `.lazy-harness/ssot/capability-registry.md`
Related TDD: `.lazy-harness/tests/project-operating-rulebook.md`

## Context

Lazy-harness already stores project facts and contracts in DDD/SDD/BDD/TDD/ADR/SSOT records. Dogfood showed that this is not enough for project-specific development behavior: agents also need a durable operating rulebook that says how to work inside a host project.

Project facts answer "what is true here?" Operating rules answer "how should agents act while developing here?"

## Decision

Introduce a first-class project operating rulebook category:

```text
.lazy-harness/rules/**
```

Rulebook entries are human-readable canonical operating policies. Machine-readable command/action/default/warn/block steering stays in `.lazy-harness/ssot/capabilities.json` and links back to rulebook entries through `sourceRecord` or `rulebookRecord`.

The framework adopts the hybrid model:

```text
rules/*.md -> capabilities.json -> lazy rules/capability resolve -> advisory/default/warn/block ladder
```

Superseded note: ADR 0046 selects Policy Machinery V2 Option B. Typed policy records are the canonical source for new behavior policy semantics; `.lazy-harness/rules/**` remains compatibility/generated/explain surface during migration.

## Consequences

- `.jcode/**` remains local/private pointer-only wiring, not canonical project rule storage.
- Project fact records remain in existing layers.
- Rulebook entries can be discovered and audited separately from fact records.
- Rulebook-backed capabilities can steer agents without adding broad tool-specific hard gates.
- `block` behavior still requires Guidance Ladder hard-stop promotion evidence.

## Implementation map

- Status: `phase-0-2-implemented`
- Primary records:
  - `.lazy-harness/spec/platform/project-operating-rulebook.md`
  - `.lazy-harness/tests/project-operating-rulebook.md`
  - `.lazy-harness/ssot/rule-sources.md`
  - `.lazy-harness/ssot/capability-registry.md`
- Primary files:
  - `.lazy-harness/rules/README.md`
  - `.lazy-harness/scripts/rulebook.ts`
  - `.lazy-harness/scripts/capability.ts`
  - `.lazy-harness/schemas/capabilities.schema.json`
  - `.lazy-harness/bin/lazy`
  - `.lazy-harness/scripts/self-test.py`
- Validation:
  - `.lazy-harness/bin/lazy rules audit --strict`
  - `.lazy-harness/bin/lazy rules resolve --action <action>`
  - `.lazy-harness/bin/lazy capability resolve --action <action>`
  - `.lazy-harness/bin/lazy test`

## Rule placement

- Rule: project operating policies belong in `.lazy-harness/rules/**` plus capability bindings, not only in fact records, `.jcode`, or memory.
- Scope: framework-global
- Primary record: `.lazy-harness/decisions/0044-project-operating-rulebook.md`
- Why not AGENTS.md: this is an architectural storage/routing decision; AGENTS grammar can later point to it but should not be the canonical rulebook store.
- Why not `.jcode`: `.jcode` is local/private generated wiring and cannot be the shared host/team rulebook.
- Confirmation: user-confirmed
