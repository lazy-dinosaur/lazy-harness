# ADR 0044 — Project Operating Rulebook

Status: superseded-by-0046
Date: 2026-06-10
Layer: ADR
Related planning: `.lazy-harness/planning/project-operating-rulebook-implementation-plan.md`
Related SDD: `.lazy-harness/spec/platform/project-operating-rulebook.md`
Related SSOT: `.lazy-harness/ssot/rule-sources.md`
Related SSOT: `.lazy-harness/ssot/capability-registry.md`
Related TDD: `.lazy-harness/tests/project-operating-rulebook.md`

## Rule digest

- Status: deprecated
- Layer: ADR
- Scope: framework-global
- Applies when:
  - storing project operating rules (how agents should act while developing in a host)
  - discussing `.lazy-harness/rules/**` rulebook vs typed policy as canonical source
- Must:
  - store project operating policies in `.lazy-harness/ssot/policies.json` plus capability bindings (per superseding ADR 0046)
  - treat `.lazy-harness/rules/**` as compatibility/explain surface, not canonical policy semantics
- Must not:
  - keep canonical project/team operating rules only in `.jcode`, memory, fact records, or rulebook markdown
- Record completion:
  - new operating-policy decisions update `.lazy-harness/ssot/policies.json` and ADR 0046 (this ADR superseded)
- Related records:
  - `.lazy-harness/decisions/0046-policy-machinery-typed-policy-canonical.md`
  - `.lazy-harness/spec/platform/project-operating-rulebook.md`
  - `.lazy-harness/ssot/rule-sources.md`

## Context

Lazy-harness already stores project facts and contracts in DDD/SDD/BDD/TDD/ADR/SSOT records. Dogfood showed that this is not enough for project-specific development behavior: agents also need a durable operating rulebook that says how to work inside a host project.

Project facts answer "what is true here?" Operating rules answer "how should agents act while developing here?"

## Decision

Introduce a first-class project operating rulebook category:

```text
.lazy-harness/rules/**
```

Rulebook entries were originally introduced as human-readable operating policies. ADR 0046 supersedes that semantic authority: typed policy records now carry canonical behavior policy semantics, while `.lazy-harness/rules/**` remains a compatibility/explain surface linked through `sourceRecord` or `rulebookRecord`.

The framework adopts the hybrid model:

```text
rules/*.md -> capabilities.json -> lazy rules/capability resolve -> advisory/default/warn/block ladder
```

Superseded note: ADR 0046 selects Policy Machinery V2 Option B. Typed policy records are the canonical source for behavior policy semantics; `.lazy-harness/rules/**` remains compatibility/generated/explain surface. `lazy rules` JSON output now advertises `rulebook-compatibility/v1` and `retiredCanonicalSemantics=true`.

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

- Rule: project operating policies belong in `.lazy-harness/ssot/policies.json` plus capability bindings, not only in fact records, `.jcode`, memory, or rulebook markdown.
- Scope: framework-global
- Primary record: `.lazy-harness/decisions/0044-project-operating-rulebook.md`
- Why not AGENTS.md: this is an architectural storage/routing decision; AGENTS grammar can later point to it but should not be the canonical rulebook store.
- Why not `.jcode`: `.jcode` is local/private generated wiring and cannot be the shared host/team rulebook.
- Confirmation: user-confirmed
